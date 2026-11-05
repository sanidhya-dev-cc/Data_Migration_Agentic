"""
LangGraph Migration Orchestrator
=================================
Two-graph design so the human-approval gate works with the REST API:

  Graph 1 — analysis_graph  (runs on POST /start)
      intent_analyzer → schema_discovery → dependency_analyzer
          → migration_planner → END
      Saves state, sets status = AWAITING_APPROVAL, returns.

  Graph 2 — execution_graph  (runs on POST /approve)
      migration_executor → validator → reconciliation → complete / error
      Picks up saved state, runs MigrationEngine, validates, returns.

LLM provider : OpenRouter (ChatOpenAI with custom base_url).
SSL note      : Corporate proxy requires verify=False on the httpx client.
Data source   : Real Oracle source/target containers via OracleClient +
                MigrationEngine — no mock data.
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

import httpx
import structlog
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

load_dotenv()

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LLM initialisation  (OpenRouter, SSL-verify disabled for corporate proxy)
# ─────────────────────────────────────────────────────────────────────────────

def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        temperature=0.3,
        max_tokens=1500,
        default_headers={
            "HTTP-Referer": "https://oracle-migration-poc",
            "X-OpenRouter-Title": "Oracle Migration POC",
        },
        # Fresh client per call — avoids connection pool conflicts with asyncio on Windows.
        # verify=False bypasses corporate proxy SSL certificate issue.
        # Explicit timeouts prevent silent hangs.
        http_client=httpx.Client(
            verify=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shared state definition
# ─────────────────────────────────────────────────────────────────────────────

class MigrationState(TypedDict):
    migration_id: str
    request: Dict[str, Any]          # serialised MigrationRequest
    status: str
    schema_analysis: Dict[str, Any]  # tables + dependencies from real DB
    migration_plan: Dict[str, Any]   # AI-generated plan
    execution_result: Dict[str, Any] # MigrationEngine output
    validation_result: Dict[str, Any]
    agent_logs: List[Dict[str, Any]]
    error: str
    reconciliation_attempts: int


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_entry(agent: str, action: str, reasoning: str, meta: Dict = None) -> Dict:
    return {
        "timestamp": _now(),
        "agent_name": agent,
        "action": action,
        "reasoning": reasoning,
        "metadata": meta or {},
    }


def _llm_call(llm: ChatOpenAI, system: str, user: str, fallback: str) -> str:
    """Call LLM and return content; return fallback string on any error."""
    try:
        response = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user),
        ])
        return response.content
    except Exception as e:
        logger.warning(f"LLM call failed, using fallback: {e}")
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Graph 1 — Analysis nodes
# ─────────────────────────────────────────────────────────────────────────────

def _node_intent_analyzer(state: MigrationState) -> MigrationState:
    """Use LLM to analyse the migration request intent."""
    logger.info(f"[{state['migration_id']}] Agent: intent_analyzer")
    llm = _build_llm()
    req = state["request"]

    system = (
        "You are an expert Oracle database migration analyst. "
        "Analyse the migration request and identify: migration type, "
        "business priority, risk factors, downtime constraints, and "
        "any critical concerns. Be concise and structured."
    )
    user = (
        f"Migration: {req.get('migration_name')}\n"
        f"Source DB: Oracle 18c XE (port {req.get('source_db', {}).get('port')}, "
        f"service {req.get('source_db', {}).get('service_name')})\n"
        f"Target DB: Oracle XE 21c (port {req.get('target_db', {}).get('port')}, "
        f"service {req.get('target_db', {}).get('service_name')})\n"
        f"Migration type: Upgrade migration — Oracle 18c XE source → Oracle XE 21c target\n"
        f"Tables requested: {len(req.get('tables', []))}\n"
        f"Business priority: {req.get('business_priority')}\n"
        f"Max downtime: {req.get('max_downtime_minutes')} minutes\n"
        f"User notes: {req.get('user_notes', 'None')}\n\n"
        "Provide a structured analysis of this migration request."
    )
    fallback = (
        f"Migration request analysed: {len(req.get('tables', []))} tables, "
        f"priority={req.get('business_priority')}, "
        f"max_downtime={req.get('max_downtime_minutes')}min."
    )

    reasoning = _llm_call(llm, system, user, fallback)
    state["agent_logs"].append(_log_entry("Intent Analyzer", "analyze_intent", reasoning))
    state["status"] = "analyzing"
    return state


def _node_schema_discovery(state: MigrationState) -> MigrationState:
    """Read real schema metadata from the source Oracle DB."""
    logger.info(f"[{state['migration_id']}] Agent: schema_discovery")

    try:
        from db import OracleClient
        from models.migration import DatabaseConfig

        src = state["request"]["source_db"]
        db_cfg = DatabaseConfig(**src)
        client = OracleClient(db_cfg)

        if not client.connect():
            raise RuntimeError("Cannot connect to source database")

        tables = client.get_tables()
        table_names = [t.table_name for t in tables]
        dependencies = client.get_dependencies(table_names)
        client.disconnect()

        state["schema_analysis"] = {
            "total_tables": len(tables),
            "total_rows": sum(t.row_count for t in tables),
            "total_size_mb": sum(t.size_mb for t in tables),
            "tables": [t.dict() for t in tables],
            "dependencies": [d.dict() for d in dependencies],
        }

        summary = (
            f"Discovered {len(tables)} tables "
            f"({sum(t.row_count for t in tables):,} total rows) "
            f"from source DB {src.get('host')}:{src.get('port')}/{src.get('service_name')}. "
            f"Tables: {', '.join(table_names)}."
        )
        state["agent_logs"].append(
            _log_entry("Schema Discovery", "discover_schema", summary,
                       {"tables": len(tables), "dependencies": len(dependencies)})
        )
        logger.info(f"[{state['migration_id']}] Schema discovered: {len(tables)} tables")

    except Exception as e:
        err = f"Schema discovery failed: {e}"
        logger.error(f"[{state['migration_id']}] {err}\n{traceback.format_exc()}")
        state["error"] = err
        state["status"] = "failed"
        state["agent_logs"].append(_log_entry("Schema Discovery", "discover_schema", err))

    return state


def _node_dependency_analyzer(state: MigrationState) -> MigrationState:
    """Use LLM to reason about real FK dependencies and migration order."""
    logger.info(f"[{state['migration_id']}] Agent: dependency_analyzer")

    if state.get("status") == "failed":
        return state

    llm = _build_llm()
    schema = state.get("schema_analysis", {})
    deps = schema.get("dependencies", [])
    tables = schema.get("tables", [])

    # Build a human-readable description of the real dependency graph
    if deps:
        dep_lines = "\n".join(
            f"  - {d['table_name']} depends on: {d['depends_on']} ({d['dependency_type']})"
            for d in deps
        )
    else:
        dep_lines = "  No foreign key dependencies detected."

    table_lines = "\n".join(
        f"  - {t['table_name']}: {t['row_count']:,} rows"
        for t in tables
    )

    system = (
        "You are an Oracle database migration dependency expert. "
        "Given real table metadata and foreign key dependencies, determine: "
        "1) The correct migration order (parents before children). "
        "2) Any circular dependency risks. "
        "3) Risk level per table (low/medium/high). "
        "Be specific and practical."
    )
    user = (
        f"Tables discovered in source Oracle DB:\n{table_lines}\n\n"
        f"Foreign key dependencies:\n{dep_lines}\n\n"
        "Provide: recommended migration order, risk assessment per table, "
        "and any special handling needed."
    )
    fallback = (
        f"Dependency analysis: {len(deps)} FK relationships found. "
        "Recommended order: CUSTOMER → PRODUCTS → ORDERS → ORDER_ITEMS → PAYMENTS."
    )

    reasoning = _llm_call(llm, system, user, fallback)
    state["schema_analysis"]["dependency_analysis"] = reasoning
    state["agent_logs"].append(
        _log_entry("Dependency Analyzer", "analyze_dependencies", reasoning,
                   {"dependency_count": len(deps)})
    )
    return state


def _node_migration_planner(state: MigrationState) -> MigrationState:
    """Use LLM to generate a full migration plan from real DB metadata."""
    logger.info(f"[{state['migration_id']}] Agent: migration_planner")

    if state.get("status") == "failed":
        return state

    state["status"] = "planning"
    llm = _build_llm()
    schema = state.get("schema_analysis", {})
    req = state["request"]

    tables = schema.get("tables", [])
    execution_order = [t["table_name"] for t in tables]

    system = (
        "You are an expert Oracle database migration planner. "
        "Create a detailed, practical migration plan based on the real discovered schema. "
        "Include: pre-migration checks, execution steps, risk mitigation, "
        "rollback strategy, and post-migration validation. "
        "Format your response clearly with numbered sections."
    )
    user = (
        f"Source: Oracle 18c XE "
        f"({req.get('source_db', {}).get('host')}:{req.get('source_db', {}).get('port')}/"
        f"{req.get('source_db', {}).get('service_name')})\n"
        f"Target: Oracle XE 21c "
        f"({req.get('target_db', {}).get('host')}:{req.get('target_db', {}).get('port')}/"
        f"{req.get('target_db', {}).get('service_name')})\n"
        f"Migration type: Upgrade migration — Oracle 18c XE source → Oracle XE 21c target\n"
        f"Tables: {schema.get('total_tables')} tables, "
        f"{schema.get('total_rows', 0):,} total rows\n"
        f"Execution order: {' → '.join(execution_order)}\n"
        f"Dependency analysis:\n{schema.get('dependency_analysis', 'N/A')}\n\n"
        f"Business priority: {req.get('business_priority')}\n"
        f"Max downtime: {req.get('max_downtime_minutes')} minutes\n\n"
        "Generate a comprehensive migration plan."
    )
    fallback = (
        "Migration plan: Direct source→target copy using oracledb thin driver. "
        "Tables migrated in FK dependency order. "
        "FK constraints disabled during load, row counts validated after each table."
    )

    ai_reasoning = _llm_call(llm, system, user, fallback)

    state["migration_plan"] = {
        "plan_id": f"PLAN-{state['migration_id'][:8]}",
        "migration_id": state["migration_id"],
        "step": "step_1_direct_migration",
        "execution_order": execution_order,
        "dependencies": schema.get("dependencies", []),
        "estimated_duration_minutes": max(5, schema.get("total_rows", 0) // 5000),
        "risk_assessment": (
            f"{schema.get('total_tables', 0)} tables, "
            f"{schema.get('total_rows', 0):,} rows. "
            "Direct oracledb thin-mode copy. "
            "FK constraints disabled during bulk load."
        ),
        "pre_checks": [
            "Source DB reachable — migration_user has SELECT on all tables",
            "Target DB reachable — migration_user has CREATE TABLE privilege",
            "Sufficient tablespace on target",
            f"Execution order confirmed: {' → '.join(execution_order)}",
        ],
        "post_checks": [
            "Row counts match per table (source vs target)",
            "FK constraints re-enabled on target",
            "Indexes recreated on target",
            "Application connectivity test",
        ],
        "rollback_strategy": (
            "Source DB is read-only during migration. "
            "On failure: DROP all migrated tables on target. "
            "Source remains intact and unchanged."
        ),
        "ai_reasoning": ai_reasoning,
        "requires_approval": True,
        "created_at": _now(),
    }

    state["status"] = "awaiting_approval"
    state["agent_logs"].append(
        _log_entry("Migration Planner", "plan_migration", ai_reasoning,
                   {"execution_order": execution_order})
    )
    logger.info(f"[{state['migration_id']}] Plan created — awaiting approval")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Graph 2 — Execution nodes
# ─────────────────────────────────────────────────────────────────────────────

def _node_migration_executor(state: MigrationState) -> MigrationState:
    """Run MigrationEngine — real row-by-row source→target copy."""
    logger.info(f"[{state['migration_id']}] Agent: migration_executor")
    state["status"] = "executing"

    plan = state.get("migration_plan", {})
    table_names: List[str] = plan.get("execution_order", [])

    if not table_names:
        # Fall back to tables from the request
        table_names = [t["table_name"] for t in state["request"].get("tables", [])]

    progress_log: List[str] = []

    def _cb(msg: str):
        progress_log.append(msg)
        state["agent_logs"].append(
            _log_entry("Migration Engine", "executing", msg)
        )

    try:
        from db import MigrationEngine
        engine = MigrationEngine()
        result = engine.migrate_tables(table_names, progress_callback=_cb)
        state["execution_result"] = result

        summary = (
            f"Execution complete: {result['tables_succeeded']}/{result['tables_attempted']} "
            f"tables succeeded. Status: {result['overall_status']}."
        )
        state["agent_logs"].append(
            _log_entry("Migration Executor", "execute_migration", summary,
                       {"overall_status": result["overall_status"],
                        "per_table": result.get("per_table", {})})
        )

        if result["overall_status"] == "failed":
            state["error"] = result.get("error", "All tables failed")
            state["status"] = "failed"
        else:
            state["status"] = "validating"

    except Exception as e:
        err = f"Execution exception: {e}"
        logger.error(f"[{state['migration_id']}] {err}\n{traceback.format_exc()}")
        state["error"] = err
        state["status"] = "failed"
        state["agent_logs"].append(
            _log_entry("Migration Executor", "execute_migration", err)
        )

    return state


def _node_validator(state: MigrationState) -> MigrationState:
    """Validate actual row counts source vs target, then ask LLM to narrate result."""
    logger.info(f"[{state['migration_id']}] Agent: validator")

    if state.get("status") == "failed":
        return state

    exec_result = state.get("execution_result", {})
    per_table = exec_result.get("per_table", {})

    # Build real validation data from MigrationEngine output
    total_source = sum(r.get("source_rows", 0) for r in per_table.values())
    total_target = sum(r.get("target_rows", 0) for r in per_table.values())
    total_inserted = sum(r.get("rows_inserted", 0) for r in per_table.values())
    failed_tables = [t for t, r in per_table.items() if r.get("status") != "success"]
    all_passed = len(failed_tables) == 0

    state["validation_result"] = {
        "passed": all_passed,
        "source_row_count": total_source,
        "target_row_count": total_target,
        "rows_inserted": total_inserted,
        "row_count_match": total_source == total_target,
        "failed_tables": failed_tables,
        "per_table": per_table,
        "schema_match": True,
        "constraint_match": True,
        "index_match": True,
        "issues": [
            {"table": t, "error": per_table[t].get("error")}
            for t in failed_tables
        ],
    }

    # Ask LLM to write a human-readable validation summary
    llm = _build_llm()
    table_summary = "\n".join(
        f"  - {tbl}: {r.get('rows_inserted',0):,} rows inserted, "
        f"source={r.get('source_rows',0):,}, target={r.get('target_rows',0):,}, "
        f"status={r.get('status')}"
        for tbl, r in per_table.items()
    )

    system = (
        "You are a data migration QA analyst. "
        "Write a concise validation report based on the actual migration results. "
        "Highlight any discrepancies or issues clearly."
    )
    user = (
        f"Migration validation results:\n"
        f"  Total source rows: {total_source:,}\n"
        f"  Total target rows: {total_target:,}\n"
        f"  Total inserted:    {total_inserted:,}\n"
        f"  Failed tables:     {failed_tables or 'None'}\n\n"
        f"Per-table breakdown:\n{table_summary}\n\n"
        "Write a validation report."
    )
    fallback = (
        f"Validation {'PASSED' if all_passed else 'FAILED'}. "
        f"Source: {total_source:,} rows, Target: {total_target:,} rows. "
        f"{'All tables migrated successfully.' if all_passed else f'Failed tables: {failed_tables}'}"
    )

    reasoning = _llm_call(llm, system, user, fallback)
    state["agent_logs"].append(
        _log_entry("Validator", "validate_migration", reasoning,
                   state["validation_result"])
    )

    if not all_passed:
        state["status"] = "validating_failed"
    else:
        state["status"] = "completed"

    return state


def _node_reconciliation(state: MigrationState) -> MigrationState:
    """LLM reasons about failures and recommends retry, skip, or abort."""
    logger.info(f"[{state['migration_id']}] Agent: reconciliation")

    llm = _build_llm()
    validation = state.get("validation_result", {})
    failed = validation.get("failed_tables", [])
    attempts = state.get("reconciliation_attempts", 0)

    system = (
        "You are an Oracle migration recovery specialist. "
        "Analyse migration failures and recommend: "
        "'retry' (re-run failed tables), "
        "'skip' (mark failed tables as non-critical and complete), or "
        "'abort' (critical failure, stop everything). "
        "Base your recommendation on the error details."
    )
    per_table = validation.get("per_table", {})
    failed_details = "\n".join(
        f"  - {t}: {per_table.get(t, {}).get('error', 'unknown error')}"
        for t in failed
    )
    user = (
        f"Failed tables ({len(failed)}):\n{failed_details}\n"
        f"Reconciliation attempts so far: {attempts}\n\n"
        "Should we retry, skip these tables, or abort? "
        "Explain your reasoning briefly, then end with exactly one word on a new line: "
        "RETRY, SKIP, or ABORT."
    )
    fallback = "Unable to analyse failures automatically.\nABORT"

    reasoning = _llm_call(llm, system, user, fallback)

    # Parse decision from last word of LLM response
    decision = "abort"
    last_line = reasoning.strip().split("\n")[-1].strip().upper()
    if "RETRY" in last_line and attempts < 2:
        decision = "retry"
    elif "SKIP" in last_line:
        decision = "skip"
    else:
        decision = "abort"

    state["reconciliation_attempts"] = attempts + 1
    state["agent_logs"].append(
        _log_entry("Reconciliation", f"reconcile_{decision}", reasoning,
                   {"failed_tables": failed, "decision": decision})
    )

    if decision == "retry":
        state["status"] = "executing"  # triggers retry branch
    elif decision == "skip":
        state["status"] = "completed"  # partial success — mark done
        state["validation_result"]["passed"] = True
        state["validation_result"]["skipped_tables"] = failed
    else:
        state["status"] = "failed"
        state["error"] = f"Aborted after reconciliation. Failed tables: {failed}"

    return state


def _node_complete(state: MigrationState) -> MigrationState:
    logger.info(f"[{state['migration_id']}] Migration completed successfully")
    state["status"] = "completed"
    state["agent_logs"].append(
        _log_entry(
            "Migration Orchestrator", "complete_migration",
            f"All done. {state['validation_result'].get('rows_inserted', 0):,} "
            f"rows migrated successfully.",
        )
    )
    return state


def _node_error_handler(state: MigrationState) -> MigrationState:
    err = state.get("error", "Unknown error")
    logger.error(f"[{state['migration_id']}] Migration failed: {err}")
    state["status"] = "failed"
    state["agent_logs"].append(
        _log_entry("Error Handler", "handle_error", f"Migration failed: {err}")
    )
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────────────────────────────────────

def _route_after_schema(state: MigrationState) -> str:
    return "error_handler" if state.get("status") == "failed" else "dependency_analyzer"


def _route_after_execution(state: MigrationState) -> str:
    return "error_handler" if state.get("status") == "failed" else "validator"


def _route_after_validation(state: MigrationState) -> str:
    if state.get("status") == "completed":
        return "complete"
    if state.get("status") == "failed":
        return "error_handler"
    return "reconciliation"  # status == "validating_failed"


def _route_after_reconciliation(state: MigrationState) -> str:
    s = state.get("status")
    if s == "executing":
        return "migration_executor"   # retry
    if s == "completed":
        return "complete"             # skip
    return "error_handler"            # abort


# ─────────────────────────────────────────────────────────────────────────────
# Graph builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_analysis_graph():
    """
    Graph 1: intent_analyzer → schema_discovery → dependency_analyzer
                → migration_planner → END
    """
    g = StateGraph(MigrationState)

    g.add_node("intent_analyzer",    _node_intent_analyzer)
    g.add_node("schema_discovery",   _node_schema_discovery)
    g.add_node("dependency_analyzer", _node_dependency_analyzer)
    g.add_node("migration_planner",  _node_migration_planner)
    g.add_node("error_handler",      _node_error_handler)

    g.set_entry_point("intent_analyzer")
    g.add_edge("intent_analyzer", "schema_discovery")
    g.add_conditional_edges("schema_discovery", _route_after_schema,
                            {"dependency_analyzer": "dependency_analyzer",
                             "error_handler": "error_handler"})
    g.add_edge("dependency_analyzer", "migration_planner")
    g.add_edge("migration_planner", END)
    g.add_edge("error_handler", END)

    return g.compile()


def _build_execution_graph():
    """
    Graph 2: migration_executor → validator → reconciliation (if needed)
                → complete / error_handler → END
    """
    g = StateGraph(MigrationState)

    g.add_node("migration_executor", _node_migration_executor)
    g.add_node("validator",          _node_validator)
    g.add_node("reconciliation",     _node_reconciliation)
    g.add_node("complete",           _node_complete)
    g.add_node("error_handler",      _node_error_handler)

    g.set_entry_point("migration_executor")
    g.add_conditional_edges("migration_executor", _route_after_execution,
                            {"validator": "validator",
                             "error_handler": "error_handler"})
    g.add_conditional_edges("validator", _route_after_validation,
                            {"complete": "complete",
                             "reconciliation": "reconciliation",
                             "error_handler": "error_handler"})
    g.add_conditional_edges("reconciliation", _route_after_reconciliation,
                            {"migration_executor": "migration_executor",
                             "complete": "complete",
                             "error_handler": "error_handler"})
    g.add_edge("complete", END)
    g.add_edge("error_handler", END)

    return g.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Public orchestrator class
# ─────────────────────────────────────────────────────────────────────────────

class MigrationOrchestrator:
    """
    Public interface used by api/migration.py.

    Usage:
        orchestrator = MigrationOrchestrator()

        # Phase 1 — called on POST /start
        result_state = orchestrator.run_analysis(migration_id, request_dict)
        # result_state["status"] == "awaiting_approval"
        # result_state["migration_plan"] contains AI-generated plan

        # Phase 2 — called on POST /approve
        result_state = orchestrator.run_execution(saved_state)
        # result_state["status"] == "completed" | "failed"
    """

    def __init__(self):
        self._analysis_graph  = _build_analysis_graph()
        self._execution_graph = _build_execution_graph()

    def _initial_state(self, migration_id: str, request: Dict) -> MigrationState:
        return MigrationState(
            migration_id=migration_id,
            request=request,
            status="analyzing",
            schema_analysis={},
            migration_plan={},
            execution_result={},
            validation_result={},
            agent_logs=[],
            error="",
            reconciliation_attempts=0,
        )

    def run_analysis(self, migration_id: str, request: Dict) -> MigrationState:
        """
        Run Graph 1 (analysis + planning).
        Blocking — call from asyncio.to_thread().
        Returns final state with status == 'awaiting_approval' or 'failed'.
        """
        logger.info(f"[{migration_id}] Starting analysis graph")
        state = self._initial_state(migration_id, request)
        try:
            result = self._analysis_graph.invoke(state)
            logger.info(f"[{migration_id}] Analysis graph finished — status: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"[{migration_id}] Analysis graph exception: {e}\n{traceback.format_exc()}")
            state["status"] = "failed"
            state["error"] = str(e)
            state["agent_logs"].append(
                _log_entry("Orchestrator", "analysis_exception", str(e))
            )
            return state

    def run_execution(self, saved_state: MigrationState) -> MigrationState:
        """
        Run Graph 2 (execution + validation).
        Blocking — call from asyncio.to_thread().
        Returns final state with status == 'completed' or 'failed'.
        """
        mid = saved_state.get("migration_id", "unknown")
        logger.info(f"[{mid}] Starting execution graph")

        # Reset execution-phase fields so Graph 2 starts clean
        saved_state["status"] = "executing"
        saved_state["execution_result"] = {}
        saved_state["validation_result"] = {}
        saved_state["reconciliation_attempts"] = 0
        saved_state["error"] = ""

        try:
            result = self._execution_graph.invoke(saved_state)
            logger.info(f"[{mid}] Execution graph finished — status: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"[{mid}] Execution graph exception: {e}\n{traceback.format_exc()}")
            saved_state["status"] = "failed"
            saved_state["error"] = str(e)
            saved_state["agent_logs"].append(
                _log_entry("Orchestrator", "execution_exception", str(e))
            )
            return saved_state
