"""
Data Verification API
Lets you inspect actual rows in source and target DBs to manually
verify migration results without needing DBeaver or sqlplus.

Endpoints:
  GET /api/data/source/tables                 — list all tables + live row counts
  GET /api/data/target/tables                 — same for target
  GET /api/data/source/{table}?limit=20&offset=0  — actual rows from source table
  GET /api/data/target/{table}?limit=20&offset=0  — actual rows from target table
  GET /api/data/compare/{table}               — side-by-side row count + sample diff
  GET /api/data/source/{table}/count          — exact COUNT(*) for source table
  GET /api/data/target/{table}/count          — exact COUNT(*) for target table
"""

import oracledb
import os
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DB connection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _src_conn() -> oracledb.Connection:
    return oracledb.connect(
        user=os.getenv("ORACLE_SOURCE_USER", "migration_user"),
        password=os.getenv("ORACLE_SOURCE_PASSWORD", "MigrationPwd123"),
        dsn=f"{os.getenv('ORACLE_SOURCE_HOST','localhost')}:"
            f"{os.getenv('ORACLE_SOURCE_PORT','1521')}/"
            f"{os.getenv('ORACLE_SOURCE_SERVICE','XEPDB1')}",
    )


def _tgt_conn() -> oracledb.Connection:
    return oracledb.connect(
        user=os.getenv("ORACLE_TARGET_USER", "migration_user"),
        password=os.getenv("ORACLE_TARGET_PASSWORD", "MigrationPwd123"),
        dsn=f"{os.getenv('ORACLE_TARGET_HOST','localhost')}:"
            f"{os.getenv('ORACLE_TARGET_PORT','1522')}/"
            f"{os.getenv('ORACLE_TARGET_SERVICE','XEPDB1')}",
    )


def _get_tables(conn: oracledb.Connection) -> List[Dict]:
    """Return all user tables with live row counts."""
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    tables = [row[0] for row in cur.fetchall()]
    cur.close()

    result = []
    for tbl in tables:
        try:
            c = conn.cursor()
            c.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = c.fetchone()[0]
            c.close()
        except Exception:
            count = -1
        result.append({"table_name": tbl, "row_count": count})
    return result


def _get_rows(
    conn: oracledb.Connection,
    table: str,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return paginated rows from a table as a list of dicts."""
    table = table.upper()
    try:
        cur = conn.cursor()

        # Get column names first
        cur.execute(
            "SELECT column_name FROM all_tab_columns "
            "WHERE owner = USER AND table_name = :t ORDER BY column_id",
            t=table,
        )
        columns = [row[0] for row in cur.fetchall()]
        if not columns:
            raise HTTPException(status_code=404, detail=f"Table {table} not found")

        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]

        # Get paginated rows
        cur.execute(
            f"SELECT * FROM (SELECT a.*, ROWNUM rn FROM {table} a WHERE ROWNUM <= :end_row) "
            f"WHERE rn > :start_row",
            end_row=offset + limit,
            start_row=offset,
        )
        rows = []
        for row in cur.fetchall():
            # Skip the ROWNUM column we added
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert Oracle types to JSON-serialisable
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                elif isinstance(val, oracledb.LOB):
                    val = str(val)
                row_dict[col] = val
            rows.append(row_dict)

        cur.close()
        return {
            "table": table,
            "total_rows": total,
            "limit": limit,
            "offset": offset,
            "returned": len(rows),
            "columns": columns,
            "rows": rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/source/tables")
def source_tables():
    """List all tables and live row counts in the SOURCE database."""
    try:
        conn = _src_conn()
        tables = _get_tables(conn)
        conn.close()
        total = sum(t["row_count"] for t in tables if t["row_count"] >= 0)
        return {
            "database": "source",
            "host": f"{os.getenv('ORACLE_SOURCE_HOST')}:{os.getenv('ORACLE_SOURCE_PORT')}",
            "service": os.getenv("ORACLE_SOURCE_SERVICE"),
            "total_tables": len(tables),
            "total_rows": total,
            "tables": tables,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/target/tables")
def target_tables():
    """List all tables and live row counts in the TARGET database."""
    try:
        conn = _tgt_conn()
        tables = _get_tables(conn)
        conn.close()
        total = sum(t["row_count"] for t in tables if t["row_count"] >= 0)
        return {
            "database": "target",
            "host": f"{os.getenv('ORACLE_TARGET_HOST')}:{os.getenv('ORACLE_TARGET_PORT')}",
            "service": os.getenv("ORACLE_TARGET_SERVICE"),
            "total_tables": len(tables),
            "total_rows": total,
            "tables": tables,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source/{table}/count")
def source_count(table: str):
    """Exact row count for a specific source table."""
    try:
        conn = _src_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table.upper()}")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"database": "source", "table": table.upper(), "row_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/target/{table}/count")
def target_count(table: str):
    """Exact row count for a specific target table."""
    try:
        conn = _tgt_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table.upper()}")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"database": "target", "table": table.upper(), "row_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source/{table}")
def source_rows(
    table: str,
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Browse actual rows in a SOURCE table.
    - limit: rows per page (max 500)
    - offset: skip N rows (for pagination)
    """
    try:
        conn = _src_conn()
        result = _get_rows(conn, table, limit, offset)
        result["database"] = "source"
        conn.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/target/{table}")
def target_rows(
    table: str,
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Browse actual rows in a TARGET table.
    - limit: rows per page (max 500)
    - offset: skip N rows (for pagination)
    """
    try:
        conn = _tgt_conn()
        result = _get_rows(conn, table, limit, offset)
        result["database"] = "target"
        conn.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{table}")
def compare_table(table: str):
    """
    Side-by-side comparison of source vs target for a table.
    Shows: row counts, first 5 rows from each, and whether they match.
    """
    table = table.upper()
    result: Dict[str, Any] = {
        "table": table,
        "source": {},
        "target": {},
        "match": False,
        "row_count_match": False,
        "verdict": "",
    }

    try:
        src_conn = _src_conn()
        result["source"] = _get_rows(src_conn, table, limit=5, offset=0)
        result["source"]["database"] = "source"
        src_conn.close()
    except Exception as e:
        result["source"] = {"error": str(e)}

    try:
        tgt_conn = _tgt_conn()
        result["target"] = _get_rows(tgt_conn, table, limit=5, offset=0)
        result["target"]["database"] = "target"
        tgt_conn.close()
    except Exception as e:
        result["target"] = {"error": str(e)}

    # Verdict
    src_count = result["source"].get("total_rows", -1)
    tgt_count = result["target"].get("total_rows", -1)
    result["row_count_match"] = (src_count == tgt_count and src_count >= 0)

    if result["row_count_match"]:
        result["match"] = True
        result["verdict"] = (
            f"✓ MATCH — both source and target have {src_count:,} rows"
        )
    elif tgt_count == 0:
        result["verdict"] = (
            f"✗ NOT MIGRATED — source has {src_count:,} rows, target has 0"
        )
    else:
        result["verdict"] = (
            f"✗ MISMATCH — source has {src_count:,} rows, target has {tgt_count:,} rows"
        )

    return result
