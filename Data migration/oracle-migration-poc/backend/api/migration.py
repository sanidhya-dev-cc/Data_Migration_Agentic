"""
Migration API routes
====================
Wires the LangGraph MigrationOrchestrator into the FastAPI lifecycle.

Flow:
  POST /api/migration/start
      → stores migration record
      → background: MigrationOrchestrator.run_analysis()  [Graph 1]
      → state written back to migrations dict
      → status becomes "awaiting_approval"

  POST /api/migration/{id}/approve
      → background: MigrationOrchestrator.run_execution()  [Graph 2]
      → state written back to migrations dict
      → status becomes "completed" or "failed"

All orchestrator calls are run in asyncio.to_thread() so FastAPI's
event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException

# Dedicated thread pool for orchestrator — keeps LLM calls isolated
# from the event loop's default thread pool
_ORCHESTRATOR_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="orchestrator")

from models.migration import (
    ApprovalRequest,
    DependencyInfo,
    MigrationPlan,
    MigrationProgress,
    MigrationRequest,
    MigrationResponse,
    MigrationStatus,
    MigrationStep,
)

router = APIRouter()
logger = structlog.get_logger(__name__)

# ── In-memory store (sufficient for POC) ─────────────────────────────────────
# Structure per entry:
#   {
#     "migration_id": str,
#     "request":      dict,        # MigrationRequest.dict()
#     "status":       str,         # mirrors MigrationStatus values
#     "agent_state":  dict | None, # full MigrationState from orchestrator
#     "created_at":   str,
#   }
migrations: Dict[str, Dict[str, Any]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _progress_from_state(migration_id: str, agent_state: Optional[Dict]) -> MigrationProgress:
    """Convert orchestrator MigrationState → MigrationProgress Pydantic model."""
    if not agent_state:
        return MigrationProgress(
            migration_id=migration_id,
            status=MigrationStatus.ANALYZING,
            current_step=None,
            current_table=None,
            tables_completed=0,
            tables_total=0,
            progress_percentage=0.0,
            started_at=None,
            completed_at=None,
            agent_logs=[],
            error_message=None,
        )

    raw_status = agent_state.get("status", "analyzing")

    # Map orchestrator status strings → MigrationStatus enum
    _status_map = {
        "analyzing":          MigrationStatus.ANALYZING,
        "planning":           MigrationStatus.PLANNING,
        "awaiting_approval":  MigrationStatus.AWAITING_APPROVAL,
        "approved":           MigrationStatus.APPROVED,
        "executing":          MigrationStatus.EXECUTING,
        "validating":         MigrationStatus.VALIDATING,
        "validating_failed":  MigrationStatus.VALIDATING,
        "completed":          MigrationStatus.COMPLETED,
        "failed":             MigrationStatus.FAILED,
        "cancelled":          MigrationStatus.CANCELLED,
    }
    status = _status_map.get(raw_status, MigrationStatus.ANALYZING)

    # Progress percentage by phase
    _pct_map = {
        "analyzing":         10.0,
        "planning":          30.0,
        "awaiting_approval": 50.0,
        "approved":          55.0,
        "executing":         65.0,
        "validating":        88.0,
        "validating_failed": 88.0,
        "completed":        100.0,
        "failed":            60.0,
        "cancelled":         50.0,
    }
    pct = _pct_map.get(raw_status, 0.0)

    # Count tables completed from execution result
    per_table = agent_state.get("execution_result", {}).get("per_table", {})
    tables_completed = sum(1 for r in per_table.values() if r.get("status") == "success")
    tables_total = len(agent_state.get("request", {}).get("tables", []))

    # Determine current_table (last "executing" log entry mentioning a table)
    current_table = None
    for log in reversed(agent_state.get("agent_logs", [])):
        reasoning = log.get("reasoning", "")
        if "Starting migration" in reasoning or "rows inserted" in reasoning:
            # Extract table name from messages like "[CUSTOMER] Starting migration..."
            import re
            m = re.search(r"\[([A-Z_]+)\]", reasoning)
            if m:
                current_table = m.group(1)
                break

    return MigrationProgress(
        migration_id=migration_id,
        status=status,
        current_step=MigrationStep.STEP_1_DIRECT_MIGRATION,
        current_table=current_table,
        tables_completed=tables_completed,
        tables_total=tables_total,
        progress_percentage=pct,
        started_at=migrations.get(migration_id, {}).get("created_at"),
        completed_at=(
            _utcnow()
            if raw_status in ("completed", "failed", "cancelled")
            else None
        ),
        agent_logs=agent_state.get("agent_logs", []),
        error_message=agent_state.get("error") or None,
    )


def _plan_from_state(migration_id: str, agent_state: Optional[Dict]) -> Optional[MigrationPlan]:
    """Extract MigrationPlan from agent state if available."""
    if not agent_state:
        return None
    plan_raw = agent_state.get("migration_plan")
    if not plan_raw or not plan_raw.get("plan_id"):
        return None
    try:
        deps = [
            DependencyInfo(**d)
            for d in plan_raw.get("dependencies", [])
            if isinstance(d, dict)
               and "table_name" in d
               and "depends_on" in d
               and isinstance(d["depends_on"], list)
        ]
        return MigrationPlan(
            plan_id=plan_raw["plan_id"],
            migration_id=migration_id,
            step=MigrationStep.STEP_1_DIRECT_MIGRATION,
            execution_order=plan_raw.get("execution_order", []),
            dependencies=deps,
            estimated_duration_minutes=plan_raw.get("estimated_duration_minutes", 5),
            risk_assessment=plan_raw.get("risk_assessment", ""),
            pre_checks=plan_raw.get("pre_checks", []),
            post_checks=plan_raw.get("post_checks", []),
            rollback_strategy=plan_raw.get("rollback_strategy", ""),
            ai_reasoning=plan_raw.get("ai_reasoning", ""),
            requires_approval=plan_raw.get("requires_approval", True),
        )
    except Exception as e:
        logger.warning(f"Could not parse plan from state: {e}")
        return None


def _sync_status(migration_id: str, agent_state: Dict) -> None:
    """Write orchestrator state back into the migrations dict."""
    m = migrations.get(migration_id)
    if not m:
        return
    m["agent_state"] = agent_state
    m["status"] = agent_state.get("status", "analyzing")


# ─────────────────────────────────────────────────────────────────────────────
# Background tasks
# ─────────────────────────────────────────────────────────────────────────────

async def _bg_run_analysis(migration_id: str, request_dict: Dict) -> None:
    """Background: run Graph 1 via orchestrator and sync state."""
    from agents import MigrationOrchestrator
    import functools

    logger.info(f"[{migration_id}] Background analysis started")
    try:
        orchestrator = MigrationOrchestrator()
        loop = asyncio.get_event_loop()
        fn = functools.partial(orchestrator.run_analysis, migration_id, request_dict)
        result_state = await asyncio.wait_for(
            loop.run_in_executor(_ORCHESTRATOR_POOL, fn),
            timeout=300,
        )
        _sync_status(migration_id, result_state)
        logger.info(f"[{migration_id}] Background analysis done — status: {result_state['status']}")
    except asyncio.TimeoutError:
        logger.error(f"[{migration_id}] Analysis timed out after 300s")
        m = migrations.get(migration_id)
        if m:
            m["status"] = "failed"
            m.setdefault("agent_state", {})["status"] = "failed"
            m["agent_state"]["error"] = "Analysis timed out after 5 minutes"
            m["agent_state"].setdefault("agent_logs", []).append({
                "timestamp": _utcnow(), "agent_name": "Orchestrator",
                "action": "timeout", "reasoning": "Analysis timed out after 5 minutes", "metadata": {},
            })
    except Exception as e:
        logger.error(f"[{migration_id}] Background analysis exception: {e}")
        m = migrations.get(migration_id)
        if m:
            m["status"] = "failed"
            m.setdefault("agent_state", {})
            m["agent_state"]["status"] = "failed"
            m["agent_state"]["error"] = str(e)
            m["agent_state"].setdefault("agent_logs", []).append({
                "timestamp": _utcnow(), "agent_name": "Orchestrator",
                "action": "analysis_exception", "reasoning": str(e), "metadata": {},
            })


async def _bg_run_execution(migration_id: str) -> None:
    """Background: run Graph 2 via orchestrator and sync state."""
    from agents import MigrationOrchestrator

    m = migrations.get(migration_id)
    if not m:
        logger.error(f"[{migration_id}] Cannot run execution — migration not found")
        return

    saved_state = m.get("agent_state")
    if not saved_state:
        logger.error(f"[{migration_id}] Cannot run execution — no saved agent state")
        return

    logger.info(f"[{migration_id}] Background execution started")
    try:
        orchestrator = MigrationOrchestrator()
        import functools
        loop = asyncio.get_event_loop()
        fn = functools.partial(orchestrator.run_execution, saved_state)
        result_state = await asyncio.wait_for(
            loop.run_in_executor(_ORCHESTRATOR_POOL, fn),
            timeout=600,
        )
        _sync_status(migration_id, result_state)
        logger.info(f"[{migration_id}] Background execution done — status: {result_state['status']}")
    except asyncio.TimeoutError:
        logger.error(f"[{migration_id}] Execution timed out after 600s")
        m["status"] = "failed"
        m.setdefault("agent_state", {})["status"] = "failed"
        m["agent_state"]["error"] = "Execution timed out after 10 minutes"
        m["agent_state"].setdefault("agent_logs", []).append({
            "timestamp": _utcnow(), "agent_name": "Orchestrator",
            "action": "timeout", "reasoning": "Execution timed out after 10 minutes", "metadata": {},
        })
    except Exception as e:
        logger.error(f"[{migration_id}] Background execution exception: {e}")
        if m.get("agent_state"):
            m["agent_state"]["status"] = "failed"
            m["agent_state"]["error"] = str(e)
            m["agent_state"].setdefault("agent_logs", []).append({
                "timestamp": _utcnow(), "agent_name": "Orchestrator",
                "action": "execution_exception", "reasoning": str(e), "metadata": {},
            })
        m["status"] = "failed"


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=MigrationResponse)
async def start_migration(
    request: MigrationRequest,
) -> MigrationResponse:
    """
    Start a new migration.
    Returns immediately; Graph 1 (analysis) runs as an asyncio task.
    Poll /status to track progress.
    """
    migration_id = str(uuid.uuid4())
    logger.info(f"Starting migration: {migration_id}")

    migrations[migration_id] = {
        "migration_id": migration_id,
        "request": request.dict(),
        "status": "analyzing",
        "agent_state": None,
        "created_at": _utcnow(),
    }

    # Use asyncio.create_task — more reliable than BackgroundTasks on Windows
    asyncio.create_task(_bg_run_analysis(migration_id, request.dict()))

    initial_progress = _progress_from_state(migration_id, None)
    return MigrationResponse(
        migration_id=migration_id,
        status=MigrationStatus.ANALYZING,
        message="Migration started. AI agents are analysing your schema...",
        progress=initial_progress,
    )


@router.get("/{migration_id}/status", response_model=MigrationResponse)
async def get_migration_status(migration_id: str) -> MigrationResponse:
    """Poll migration status. Frontend calls this every 3 s."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    agent_state = m.get("agent_state")

    progress = _progress_from_state(migration_id, agent_state)
    plan     = _plan_from_state(migration_id, agent_state)

    raw_status = m["status"]
    _status_map = {
        "analyzing":         MigrationStatus.ANALYZING,
        "planning":          MigrationStatus.PLANNING,
        "awaiting_approval": MigrationStatus.AWAITING_APPROVAL,
        "approved":          MigrationStatus.APPROVED,
        "executing":         MigrationStatus.EXECUTING,
        "validating":        MigrationStatus.VALIDATING,
        "validating_failed": MigrationStatus.VALIDATING,
        "completed":         MigrationStatus.COMPLETED,
        "failed":            MigrationStatus.FAILED,
        "cancelled":         MigrationStatus.CANCELLED,
    }
    status_enum = _status_map.get(raw_status, MigrationStatus.ANALYZING)

    return MigrationResponse(
        migration_id=migration_id,
        status=status_enum,
        message=f"Migration status: {raw_status}",
        progress=progress,
        plan=plan,
    )


@router.post("/{migration_id}/approve", response_model=MigrationResponse)
async def approve_migration(
    migration_id: str,
    approval: ApprovalRequest,
) -> MigrationResponse:
    """
    Approve or reject a migration that is awaiting approval.
    On approval, Graph 2 (execution) runs in the background.
    """
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]

    if m["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Migration is not awaiting approval (current: {m['status']})",
        )

    # ── Rejected ──────────────────────────────────────────────────────────────
    if not approval.approved:
        m["status"] = "cancelled"
        if m.get("agent_state"):
            m["agent_state"]["status"] = "cancelled"
            m["agent_state"].setdefault("agent_logs", []).append({
                "timestamp": _utcnow(),
                "agent_name": "Human Approver",
                "action": "reject_migration",
                "reasoning": f"Cancelled by {approval.approver}: {approval.comments or 'No reason given'}",
                "metadata": {},
            })
        progress = _progress_from_state(migration_id, m.get("agent_state"))
        return MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.CANCELLED,
            message="Migration cancelled by approver.",
            progress=progress,
        )

    # ── Approved ──────────────────────────────────────────────────────────────
    logger.info(f"Migration {migration_id} approved by {approval.approver}")
    m["status"] = "executing"
    if m.get("agent_state"):
        m["agent_state"].setdefault("agent_logs", []).append({
            "timestamp": _utcnow(),
            "agent_name": "Human Approver",
            "action": "approve_migration",
            "reasoning": (
                f"Migration approved by {approval.approver}. "
                f"{('Comment: ' + approval.comments) if approval.comments else ''}"
            ),
            "metadata": {"approver": approval.approver},
        })

    # Use asyncio.create_task — more reliable than BackgroundTasks on Windows
    asyncio.create_task(_bg_run_execution(migration_id))

    progress = _progress_from_state(migration_id, m.get("agent_state"))
    return MigrationResponse(
        migration_id=migration_id,
        status=MigrationStatus.EXECUTING,
        message="Migration approved. Execution agents running...",
        progress=progress,
    )


@router.post("/{migration_id}/cancel")
async def cancel_migration(migration_id: str):
    """Cancel a migration that is not yet executing."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    terminal = {"completed", "failed", "cancelled"}
    if m["status"] in terminal:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a migration in terminal state: {m['status']}",
        )

    m["status"] = "cancelled"
    if m.get("agent_state"):
        m["agent_state"]["status"] = "cancelled"
    logger.info(f"Migration {migration_id} cancelled via API")
    return {"message": "Migration cancelled."}


@router.get("/{migration_id}/result")
async def get_migration_result(migration_id: str):
    """Return the detailed per-table execution result."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    agent_state = m.get("agent_state") or {}

    return {
        "migration_id": migration_id,
        "status": m["status"],
        "execution_result": agent_state.get("execution_result"),
        "validation_result": agent_state.get("validation_result"),
    }


@router.get("/{migration_id}/logs")
async def get_agent_logs(migration_id: str):
    """Return all agent reasoning logs for a migration."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    agent_state = migrations[migration_id].get("agent_state") or {}
    return {
        "migration_id": migration_id,
        "logs": agent_state.get("agent_logs", []),
    }
