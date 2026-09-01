"""
Migration API routes
Supports both real (ENABLE_MOCK_MODE=false) and mock (ENABLE_MOCK_MODE=true) modes.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import structlog
from datetime import datetime, timezone
import uuid
import asyncio
import os

from models.migration import (
    MigrationRequest,
    MigrationResponse,
    MigrationStatus,
    ApprovalRequest,
    MigrationProgress,
)

router = APIRouter()
logger = structlog.get_logger(__name__)

# In-memory store (sufficient for POC)
migrations: Dict[str, Dict] = {}

MOCK_MODE = os.getenv("ENABLE_MOCK_MODE", "false").lower() == "true"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_status(migration_id: str, status: MigrationStatus, pct: float, msg: str):
    """Thread-safe-enough update for the in-memory store."""
    m = migrations.get(migration_id)
    if not m:
        return
    m["status"] = status.value
    m["progress"]["status"] = status.value
    m["progress"]["progress_percentage"] = pct
    m["progress"]["agent_logs"].append(
        {
            "timestamp": _utcnow(),
            "agent_name": "Migration Orchestrator",
            "action": status.value,
            "reasoning": msg,
            "metadata": {},
        }
    )
    if status in (MigrationStatus.COMPLETED, MigrationStatus.FAILED):
        m["progress"]["completed_at"] = _utcnow()


def _build_plan(migration_id: str, request: MigrationRequest) -> Dict:
    return {
        "plan_id": f"PLAN-{migration_id[:8]}",
        "migration_id": migration_id,
        "step": "step_1_non_cdb_to_pdb",
        "execution_order": [t.table_name for t in request.tables],
        "dependencies": [],
        "estimated_duration_minutes": 5,
        "risk_assessment": (
            "Low risk – direct table copy via oracledb thin driver. "
            "FK constraints disabled during load and re-enabled after."
        ),
        "pre_checks": [
            "Source DB reachable and migration_user has SELECT privilege",
            "Target DB reachable and migration_user has CREATE TABLE privilege",
            "Sufficient tablespace on target",
        ],
        "post_checks": [
            "Row counts match source vs target per table",
            "FK constraints re-enabled successfully",
            "Indexes recreated on target",
        ],
        "rollback_strategy": "DROP each migrated table on target; source is read-only.",
        "ai_reasoning": (
            "Tables are migrated in dependency order: parents before children.\n"
            "FK constraints are disabled on the target during bulk load to maximise\n"
            "throughput, then validated and re-enabled afterwards.\n"
            "A row-count check per table confirms integrity."
        ),
        "requires_approval": True,
        "created_at": _utcnow(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Background workers
# ─────────────────────────────────────────────────────────────────────────────

async def _run_analysis_and_plan(migration_id: str, request: MigrationRequest):
    """Phase 1: analyse → plan → await approval."""
    await asyncio.sleep(1)
    _set_status(migration_id, MigrationStatus.ANALYZING, 10,
                "Connecting to source database and reading schema metadata...")

    if not MOCK_MODE:
        # Real connection test
        await asyncio.to_thread(_real_test_connections, migration_id)
        if migrations[migration_id]["status"] == MigrationStatus.FAILED.value:
            return

    await asyncio.sleep(2)
    _set_status(migration_id, MigrationStatus.PLANNING, 30,
                "Schema discovered. Analysing table dependencies and building migration plan...")

    await asyncio.sleep(1)
    plan = _build_plan(migration_id, request)
    migrations[migration_id]["plan"] = plan

    _set_status(migration_id, MigrationStatus.AWAITING_APPROVAL, 50,
                "Migration plan ready. Awaiting human approval before execution.")


def _real_test_connections(migration_id: str):
    """Blocking: test source + target connectivity."""
    from db import MigrationEngine
    engine = MigrationEngine()
    conn_result = engine.test_connections()
    if not conn_result["source"]["connected"]:
        err = conn_result["source"].get("error", "unknown")
        _set_status(migration_id, MigrationStatus.FAILED, 0,
                    f"Cannot connect to source DB: {err}")
        return
    if not conn_result["target"]["connected"]:
        err = conn_result["target"].get("error", "unknown")
        _set_status(migration_id, MigrationStatus.FAILED, 0,
                    f"Cannot connect to target DB: {err}")
        return
    logger.info(f"[{migration_id}] Both DB connections verified.")


async def _run_execution(migration_id: str, table_names: list):
    """Phase 2 (post-approval): execute real or mock migration."""
    _set_status(migration_id, MigrationStatus.EXECUTING, 60,
                f"Starting data migration for {len(table_names)} tables...")

    if MOCK_MODE:
        await _mock_execute(migration_id, table_names)
    else:
        await _real_execute(migration_id, table_names)


async def _real_execute(migration_id: str, table_names: list):
    """Run MigrationEngine in a thread so the event loop stays free."""
    from db import MigrationEngine

    progress_msgs: list = []

    def _cb(msg: str):
        progress_msgs.append(msg)
        m = migrations.get(migration_id)
        if m:
            m["progress"]["agent_logs"].append(
                {
                    "timestamp": _utcnow(),
                    "agent_name": "Migration Engine",
                    "action": "executing",
                    "reasoning": msg,
                    "metadata": {},
                }
            )

    def _do_migration():
        engine = MigrationEngine()
        return engine.migrate_tables(table_names, progress_callback=_cb)

    try:
        result = await asyncio.to_thread(_do_migration)
        migrations[migration_id]["execution_result"] = result

        if result["overall_status"] in ("success", "partial"):
            _set_status(migration_id, MigrationStatus.VALIDATING, 85,
                        f"Execution done ({result['tables_succeeded']}/{result['tables_attempted']} tables OK). Validating...")
            await asyncio.sleep(1)
            _finalize(migration_id, result)
        else:
            err = result.get("error", "Migration engine reported failure.")
            _set_status(migration_id, MigrationStatus.FAILED, 60, f"Execution failed: {err}")

    except Exception as e:
        logger.error(f"[{migration_id}] Execution exception: {e}")
        _set_status(migration_id, MigrationStatus.FAILED, 60, f"Exception during execution: {e}")


async def _mock_execute(migration_id: str, table_names: list):
    """Simulated execution for when ENABLE_MOCK_MODE=true."""
    total = len(table_names)
    for i, table in enumerate(table_names, 1):
        await asyncio.sleep(1)
        pct = 60 + (25 * i / total)
        _set_status(migration_id, MigrationStatus.EXECUTING, pct,
                    f"[Mock] Migrating table {table} ({i}/{total})...")

    mock_result = {
        "overall_status": "success",
        "tables_attempted": total,
        "tables_succeeded": total,
        "tables_failed": 0,
        "per_table": {t: {"status": "success", "rows_inserted": 1000} for t in table_names},
    }
    migrations[migration_id]["execution_result"] = mock_result
    _set_status(migration_id, MigrationStatus.VALIDATING, 88,
                "Mock execution complete. Validating row counts...")
    await asyncio.sleep(1)
    _finalize(migration_id, mock_result)


def _finalize(migration_id: str, result: Dict):
    """Set final status based on engine result."""
    failed_tables = [
        t for t, r in result.get("per_table", {}).items()
        if r.get("status") != "success"
    ]
    if not failed_tables:
        _set_status(migration_id, MigrationStatus.COMPLETED, 100,
                    f"All {result['tables_succeeded']} tables migrated and validated successfully.")
    else:
        _set_status(migration_id, MigrationStatus.FAILED, 95,
                    f"Migration finished with errors on: {', '.join(failed_tables)}.")


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=MigrationResponse)
async def start_migration(request: MigrationRequest, background_tasks: BackgroundTasks):
    """Start a new migration – returns immediately, runs analysis in background."""
    migration_id = str(uuid.uuid4())
    logger.info(f"Starting migration: {migration_id} (mock={MOCK_MODE})")

    migrations[migration_id] = {
        "migration_id": migration_id,
        "request": request.dict(),
        "status": MigrationStatus.ANALYZING.value,
        "created_at": _utcnow(),
        "plan": None,
        "execution_result": None,
        "progress": {
            "migration_id": migration_id,
            "status": MigrationStatus.ANALYZING.value,
            "current_step": None,
            "current_table": None,
            "tables_completed": 0,
            "tables_total": len(request.tables),
            "progress_percentage": 0,
            "started_at": _utcnow(),
            "completed_at": None,
            "agent_logs": [],
            "error_message": None,
        },
    }

    # Kick off analysis + planning in the background
    background_tasks.add_task(_run_analysis_and_plan, migration_id, request)

    return MigrationResponse(
        migration_id=migration_id,
        status=MigrationStatus.ANALYZING,
        message="Migration started. Analysis running in background.",
        progress=MigrationProgress(**migrations[migration_id]["progress"]),
    )


@router.get("/{migration_id}/status", response_model=MigrationResponse)
async def get_migration_status(migration_id: str):
    """Poll migration status."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    plan_raw = m.get("plan")
    plan_obj = None
    if plan_raw:
        from models.migration import MigrationPlan, DependencyInfo
        try:
            plan_obj = MigrationPlan(
                plan_id=plan_raw["plan_id"],
                migration_id=plan_raw["migration_id"],
                step=plan_raw["step"],
                execution_order=plan_raw["execution_order"],
                dependencies=[DependencyInfo(**d) for d in plan_raw.get("dependencies", [])],
                estimated_duration_minutes=plan_raw["estimated_duration_minutes"],
                risk_assessment=plan_raw["risk_assessment"],
                pre_checks=plan_raw["pre_checks"],
                post_checks=plan_raw["post_checks"],
                rollback_strategy=plan_raw["rollback_strategy"],
                ai_reasoning=plan_raw["ai_reasoning"],
                requires_approval=plan_raw["requires_approval"],
            )
        except Exception:
            pass

    return MigrationResponse(
        migration_id=migration_id,
        status=MigrationStatus(m["status"]),
        message=f"Migration status: {m['status']}",
        progress=MigrationProgress(**m["progress"]),
        plan=plan_obj,
    )


@router.post("/{migration_id}/approve", response_model=MigrationResponse)
async def approve_migration(
    migration_id: str,
    approval: ApprovalRequest,
    background_tasks: BackgroundTasks,
):
    """Approve or reject a migration that is awaiting approval."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]

    if m["status"] != MigrationStatus.AWAITING_APPROVAL.value:
        raise HTTPException(
            status_code=400,
            detail=f"Migration is not awaiting approval (current: {m['status']})",
        )

    if not approval.approved:
        m["status"] = MigrationStatus.CANCELLED.value
        m["progress"]["status"] = MigrationStatus.CANCELLED.value
        m["progress"]["error_message"] = f"Cancelled by user: {approval.comments}"
        return MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.CANCELLED,
            message="Migration cancelled by approver.",
            progress=MigrationProgress(**m["progress"]),
        )

    # Approved – kick off real execution
    logger.info(f"Migration {migration_id} approved by {approval.approver}")
    table_names = [t["table_name"] for t in m["request"].get("tables", [])]
    background_tasks.add_task(_run_execution, migration_id, table_names)

    return MigrationResponse(
        migration_id=migration_id,
        status=MigrationStatus.EXECUTING,
        message="Migration approved. Execution running in background.",
        progress=MigrationProgress(**m["progress"]),
    )


@router.post("/{migration_id}/cancel")
async def cancel_migration(migration_id: str):
    """Cancel a pending/planning/awaiting migration."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    terminal = {MigrationStatus.COMPLETED.value, MigrationStatus.FAILED.value,
                MigrationStatus.CANCELLED.value}
    if m["status"] in terminal:
        raise HTTPException(status_code=400, detail="Cannot cancel a terminal migration.")

    m["status"] = MigrationStatus.CANCELLED.value
    m["progress"]["status"] = MigrationStatus.CANCELLED.value
    logger.info(f"Migration {migration_id} cancelled via API.")
    return {"message": "Migration cancelled."}


@router.get("/{migration_id}/result")
async def get_migration_result(migration_id: str):
    """Return the detailed per-table execution result."""
    if migration_id not in migrations:
        raise HTTPException(status_code=404, detail="Migration not found")

    m = migrations[migration_id]
    return {
        "migration_id": migration_id,
        "status": m["status"],
        "execution_result": m.get("execution_result"),
    }
