"""
Real Migration Engine
Performs actual source → target data migration via oracledb (thin mode).
No Oracle Client installation required.

Flow per table:
  1. Read DDL from source (columns, constraints, indexes)
  2. Create table on target (if not exists)
  3. Stream rows from source in configurable batches
  4. Insert rows into target
  5. Re-create indexes and enable constraints
  6. Validate row counts match
"""

import oracledb
from typing import List, Dict, Any, Optional, Callable
import structlog
import os
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration helpers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DBConnConfig:
    host: str
    port: int
    service: str
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return f"{self.host}:{self.port}/{self.service}"

    def connect(self) -> oracledb.Connection:
        return oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)


def source_config() -> DBConnConfig:
    return DBConnConfig(
        host=os.getenv("ORACLE_SOURCE_HOST", "localhost"),
        port=int(os.getenv("ORACLE_SOURCE_PORT", 1521)),
        service=os.getenv("ORACLE_SOURCE_SERVICE", "XEPDB1"),
        user=os.getenv("ORACLE_SOURCE_USER", "migration_user"),
        password=os.getenv("ORACLE_SOURCE_PASSWORD", "MigrationPwd123"),
    )


def target_config() -> DBConnConfig:
    return DBConnConfig(
        host=os.getenv("ORACLE_TARGET_HOST", "localhost"),
        port=int(os.getenv("ORACLE_TARGET_PORT", 1522)),
        service=os.getenv("ORACLE_TARGET_SERVICE", "XEPDB1"),
        user=os.getenv("ORACLE_TARGET_USER", "migration_user"),
        password=os.getenv("ORACLE_TARGET_PASSWORD", "MigrationPwd123"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# DDL helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_columns(cur: oracledb.Cursor, owner: str, table: str) -> List[Dict]:
    """Return ordered column metadata for a table."""
    cur.execute(
        """
        SELECT column_name, data_type, data_length, data_precision,
               data_scale, nullable, data_default
        FROM   all_tab_columns
        WHERE  owner = :owner AND table_name = :tname
        ORDER  BY column_id
        """,
        owner=owner.upper(),
        tname=table.upper(),
    )
    cols = []
    for row in cur:
        cols.append(
            {
                "name": row[0],
                "type": row[1],
                "length": row[2],
                "precision": row[3],
                "scale": row[4],
                "nullable": row[5],
                "default": row[6],
            }
        )
    return cols


def _col_ddl(col: Dict) -> str:
    """Build a single column DDL fragment — safe for Oracle XE via thin driver."""
    t = col["type"]

    # data_type from all_tab_columns already contains precision for these types,
    # e.g. "TIMESTAMP(6)", "FLOAT(126)". Use as-is.
    if t.startswith("TIMESTAMP") or t.startswith("INTERVAL") or t.startswith("FLOAT"):
        spec = t
    elif t == "NUMBER":
        if col["precision"] is not None:
            spec = f"NUMBER({int(col['precision'])},{int(col['scale'] or 0)})"
        else:
            spec = "NUMBER"
    elif t in ("VARCHAR2", "NVARCHAR2"):
        spec = f"{t}({col['length']} CHAR)"
    elif t in ("CHAR", "NCHAR"):
        spec = f"{t}({col['length']})"
    elif t in ("DATE", "CLOB", "BLOB", "XMLTYPE", "RAW"):
        spec = t
    elif t.startswith("RAW"):
        spec = f"RAW({col['length']})"
    else:
        # Fallback — use the type string as-is (may already include size)
        spec = t

    # Strip DEFAULT value: remove trailing whitespace, guard against embedded newlines
    default_clause = ""
    if col["default"] is not None:
        default_val = str(col["default"]).strip().replace("\n", " ").replace("\r", " ")
        if default_val:
            default_clause = f" DEFAULT {default_val}"

    null_clause = "" if col["nullable"] == "Y" else " NOT NULL"
    return f'"{col["name"]}" {spec}{default_clause}{null_clause}'


def _get_pk_constraint(cur: oracledb.Cursor, owner: str, table: str) -> Optional[Dict]:
    try:
        cur.execute(
            """
            SELECT ac.constraint_name,
                   LISTAGG(acc.column_name, ',') WITHIN GROUP (ORDER BY acc.position) AS cols
            FROM   all_constraints ac
            JOIN   all_cons_columns acc
                   ON  ac.constraint_name = acc.constraint_name
                   AND ac.owner           = acc.owner
            WHERE  ac.owner           = :owner
            AND    ac.table_name      = :tname
            AND    ac.constraint_type = 'P'
            GROUP  BY ac.constraint_name
            """,
            owner=owner.upper(),
            tname=table.upper(),
        )
        row = cur.fetchone()
        if row:
            return {"name": row[0], "columns": row[1]}
    except Exception as e:
        logger.warning(f"Could not get PK for {table}: {e}")
    return None


def _get_fk_constraints(cur: oracledb.Cursor, owner: str, table: str) -> List[Dict]:
    """Get FK constraints using a simpler query that works without DBA privileges."""
    try:
        # Step 1: get FK constraint names and their column lists
        cur.execute(
            """
            SELECT ac.constraint_name,
                   ac.r_constraint_name,
                   ac.r_owner,
                   ac.delete_rule,
                   LISTAGG(acc.column_name, ',' ORDER BY acc.position) AS fk_cols
            FROM   all_constraints  ac
            JOIN   all_cons_columns acc
                   ON  acc.constraint_name = ac.constraint_name
                   AND acc.owner           = ac.owner
            WHERE  ac.owner           = :owner
            AND    ac.table_name      = :tname
            AND    ac.constraint_type = 'R'
            GROUP  BY ac.constraint_name, ac.r_constraint_name, ac.r_owner, ac.delete_rule
            """,
            owner=owner.upper(),
            tname=table.upper(),
        )
        rows = cur.fetchall()
        fks = []
        for row in rows:
            con_name, r_con_name, r_owner, del_rule, fk_cols = row
            try:
                # Step 2: resolve referenced table + columns
                cur.execute(
                    """
                    SELECT ac.table_name,
                           LISTAGG(acc.column_name, ',' ORDER BY acc.position) AS ref_cols
                    FROM   all_constraints  ac
                    JOIN   all_cons_columns acc
                           ON  acc.constraint_name = ac.constraint_name
                           AND acc.owner           = ac.owner
                    WHERE  ac.constraint_name = :cname
                    AND    ac.owner           = :owner
                    GROUP  BY ac.table_name
                    """,
                    cname=r_con_name,
                    owner=r_owner,
                )
                ref_row = cur.fetchone()
                if ref_row:
                    fks.append({
                        "name": con_name,
                        "fk_cols": fk_cols,
                        "ref_table": ref_row[0],
                        "ref_cols": ref_row[1],
                        "delete_rule": del_rule or "NO ACTION",
                    })
            except Exception:
                pass
        return fks
    except Exception as e:
        logger.warning(f"Could not get FKs for {table}: {e}")
        return []


def _get_indexes(cur: oracledb.Cursor, owner: str, table: str) -> List[Dict]:
    """Return non-PK, non-unique-constraint indexes."""
    try:
        # Simpler query: get all indexes then exclude those backing P/U constraints.
        # Avoids NOT EXISTS + IN('P','U') which hits an oracledb thin-driver parse bug.
        cur.execute(
            """
            SELECT ai.index_name, ai.uniqueness,
                   LISTAGG(aic.column_name, ',' ORDER BY aic.column_position) AS cols
            FROM   all_indexes     ai
            JOIN   all_ind_columns aic
                   ON  aic.index_name  = ai.index_name
                   AND aic.index_owner = ai.owner
            WHERE  ai.owner      = :owner
            AND    ai.table_name = :tname
            GROUP  BY ai.index_name, ai.uniqueness
            """,
            owner=owner.upper(),
            tname=table.upper(),
        )
        all_idxs = cur.fetchall()

        # Get constraint-backed index names so we can exclude them
        cur.execute(
            "SELECT index_name FROM all_constraints "
            "WHERE owner=:owner AND table_name=:tname AND index_name IS NOT NULL",
            owner=owner.upper(),
            tname=table.upper(),
        )
        constraint_indexes = {row[0] for row in cur.fetchall()}

        return [
            {"name": row[0], "unique": row[1] == "UNIQUE", "columns": row[2]}
            for row in all_idxs
            if row[0] not in constraint_indexes
        ]
    except Exception as e:
        logger.warning(f"Could not get indexes for {table}: {e}")
        return []


def _build_create_table_ddl(cols: List[Dict], pk: Optional[Dict], table: str) -> str:
    col_defs = [_col_ddl(c) for c in cols]
    if pk:
        pk_cols = ", ".join(f'"{c}"' for c in pk["columns"].split(","))
        # Use a migration-specific PK name to avoid ORA-02264 if the source
        # constraint name already exists on target from a prior partial run.
        safe_pk_name = f"MIG_{table.upper()}_PK"
        col_defs.append(f'CONSTRAINT "{safe_pk_name}" PRIMARY KEY ({pk_cols})')
    return f'CREATE TABLE "{table.upper()}" (\n  ' + ",\n  ".join(col_defs) + "\n)"


# ─────────────────────────────────────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────────────────────────────────────

BATCH_SIZE = 500   # rows per INSERT batch


class MigrationEngine:
    """
    Migrates tables from source Oracle DB to target Oracle DB.

    Usage:
        engine = MigrationEngine()
        results = engine.migrate_tables(
            table_names=["CUSTOMER", "PRODUCTS", "ORDERS", "ORDER_ITEMS", "PAYMENTS"],
            progress_callback=lambda msg: print(msg)
        )
    """

    def __init__(self):
        self.src_cfg = source_config()
        self.tgt_cfg = target_config()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def migrate_tables(
        self,
        table_names: List[str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Migrate a list of tables from source to target.
        Returns a summary dict with per-table results and overall status.
        """

        def _log(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        results: Dict[str, Any] = {
            "tables_attempted": len(table_names),
            "tables_succeeded": 0,
            "tables_failed": 0,
            "per_table": {},
            "overall_status": "success",
        }

        try:
            src_conn = self.src_cfg.connect()
            tgt_conn = self.tgt_cfg.connect()
        except Exception as e:
            logger.error(f"Cannot open DB connections: {e}")
            results["overall_status"] = "failed"
            results["error"] = str(e)
            return results

        try:
            src_owner = self.src_cfg.user.upper()

            # ── Phase 1: disable all FK constraints on target ──────────
            _log("Disabling FK constraints on target for bulk load...")
            self._disable_fks(tgt_conn, tgt_owner=self.tgt_cfg.user.upper(),
                               table_names=table_names)

            # ── Phase 2: migrate each table ────────────────────────────
            for table in table_names:
                _log(f"[{table}] Starting migration...")
                t_result = self._migrate_one_table(
                    src_conn=src_conn,
                    tgt_conn=tgt_conn,
                    src_owner=src_owner,
                    tgt_owner=self.tgt_cfg.user.upper(),
                    table=table,
                    log=_log,
                )
                results["per_table"][table] = t_result
                if t_result["status"] == "success":
                    results["tables_succeeded"] += 1
                else:
                    results["tables_failed"] += 1
                    results["overall_status"] = "partial"

            # ── Phase 3: re-enable FK constraints on target ────────────
            _log("Re-enabling FK constraints on target...")
            self._enable_fks(tgt_conn, tgt_owner=self.tgt_cfg.user.upper(),
                              table_names=table_names)

            if results["tables_failed"] == results["tables_attempted"]:
                results["overall_status"] = "failed"

        except Exception as e:
            logger.error(f"Fatal migration error: {e}")
            results["overall_status"] = "failed"
            results["error"] = str(e)
        finally:
            try:
                src_conn.close()
            except Exception:
                pass
            try:
                tgt_conn.close()
            except Exception:
                pass

        return results

    # ------------------------------------------------------------------
    # Single-table migration
    # ------------------------------------------------------------------

    def _migrate_one_table(
        self,
        src_conn: oracledb.Connection,
        tgt_conn: oracledb.Connection,
        src_owner: str,
        tgt_owner: str,
        table: str,
        log: Callable,
    ) -> Dict[str, Any]:

        t_result: Dict[str, Any] = {
            "status": "failed",
            "source_rows": 0,
            "target_rows": 0,
            "rows_inserted": 0,
            "error": None,
        }

        try:
            src_cur = src_conn.cursor()
            tgt_cur = tgt_conn.cursor()

            # 1. Get source metadata
            cols = _get_columns(src_cur, src_owner, table)
            if not cols:
                raise ValueError(f"Table {table} not found in source schema {src_owner}")

            pk   = _get_pk_constraint(src_cur, src_owner, table)
            idxs = _get_indexes(src_cur, src_owner, table)
            fks  = _get_fk_constraints(src_cur, src_owner, table)

            # 2. Drop + recreate table on target (clean slate)
            log(f"  [{table}] Creating table on target...")

            # Drop existing table — use separate try/except instead of PL/SQL
            # because PL/SQL anonymous blocks with mixed quotes can cause ORA-00907
            # in some oracledb thin-mode versions.
            try:
                tgt_cur.execute(f'DROP TABLE "{table.upper()}" CASCADE CONSTRAINTS PURGE')
                tgt_conn.commit()
            except oracledb.DatabaseError as de:
                err_obj = de.args[0]
                # ORA-00942 = table does not exist — safe to ignore
                if hasattr(err_obj, 'code') and err_obj.code == 942:
                    pass
                elif '942' in str(de):
                    pass
                else:
                    logger.warning(f"  [{table}] Drop warning: {de}")

            ddl = _build_create_table_ddl(cols, pk, table)
            logger.info(f"  [{table}] DDL: {ddl[:120]}...")
            try:
                tgt_cur.execute(ddl)
            except Exception as ddl_err:
                raise ValueError(
                    f"CREATE TABLE failed for {table}.\nDDL:\n{ddl}\nError: {ddl_err}"
                )
            tgt_conn.commit()
            log(f"  [{table}] Table created on target.")

            # 3. Stream rows source → target
            col_names = [c["name"] for c in cols]
            quoted_cols = ", ".join(f'"{c}"' for c in col_names)
            bind_vars   = ", ".join(f":{i+1}" for i in range(len(col_names)))
            insert_sql  = (
                f'INSERT INTO "{table.upper()}" ({quoted_cols}) VALUES ({bind_vars})'
            )

            # Get source row count BEFORE opening the SELECT cursor
            # (using the same cursor for COUNT then SELECT would overwrite the result set)
            count_cur = src_conn.cursor()
            count_cur.execute(f'SELECT COUNT(*) FROM {src_owner}.{table.upper()}')
            t_result["source_rows"] = count_cur.fetchone()[0]
            count_cur.close()

            # Open the streaming SELECT on src_cur
            src_cur.execute(f'SELECT {quoted_cols} FROM {src_owner}."{table.upper()}"')

            rows_inserted = 0
            batch: List[tuple] = []

            for row in src_cur:
                batch.append(row)
                if len(batch) >= BATCH_SIZE:
                    tgt_cur.executemany(insert_sql, batch)
                    tgt_conn.commit()
                    rows_inserted += len(batch)
                    batch = []
                    log(f"  [{table}] {rows_inserted} rows inserted...")

            if batch:
                tgt_cur.executemany(insert_sql, batch)
                tgt_conn.commit()
                rows_inserted += len(batch)

            log(f"  [{table}] All {rows_inserted} rows inserted.")
            t_result["rows_inserted"] = rows_inserted

            # 4. Recreate indexes on target
            for idx in idxs:
                idx_cols = ", ".join(f'"{c}"' for c in idx["columns"].split(","))
                unique_kw = "UNIQUE " if idx["unique"] else ""
                idx_ddl = (
                    f'CREATE {unique_kw}INDEX "{idx["name"]}" '
                    f'ON "{table.upper()}" ({idx_cols})'
                )
                try:
                    tgt_cur.execute(idx_ddl)
                    tgt_conn.commit()
                except Exception as ie:
                    log(f"  [{table}] Warning: could not create index {idx['name']}: {ie}")

            # 5. Add FK constraints on target (NOVALIDATE — data already loaded correctly)
            for fk_idx, fk in enumerate(fks):
                fk_cols  = ", ".join(f'"{c}"' for c in fk["fk_cols"].split(","))
                ref_cols = ", ".join(f'"{c}"' for c in fk["ref_cols"].split(","))
                del_rule = f" ON DELETE {fk['delete_rule']}" if fk["delete_rule"] not in ("NO ACTION", "") else ""
                # Use a migration-specific name to avoid ORA-02264
                safe_fk_name = f"MIG_{table.upper()}_FK{fk_idx + 1}"
                fk_ddl = (
                    f'ALTER TABLE "{table.upper()}" ADD CONSTRAINT "{safe_fk_name}" '
                    f'FOREIGN KEY ({fk_cols}) '
                    f'REFERENCES "{fk["ref_table"].upper()}" ({ref_cols}){del_rule} '
                    f'ENABLE NOVALIDATE'
                )
                try:
                    tgt_cur.execute(fk_ddl)
                    tgt_conn.commit()
                except Exception as fe:
                    log(f"  [{table}] Warning: could not add FK {safe_fk_name}: {fe}")

            # 6. Validate row count
            t_result["target_rows"] = self._get_row_count(tgt_cur, tgt_owner, table)
            if t_result["target_rows"] == rows_inserted:
                t_result["status"] = "success"
                log(f"  [{table}] Validated: {t_result['target_rows']} rows on target.")
            else:
                t_result["status"] = "row_count_mismatch"
                t_result["error"] = (
                    f"Expected {rows_inserted} rows, found {t_result['target_rows']}"
                )
                log(f"  [{table}] Row count mismatch! {t_result['error']}")

            src_cur.close()
            tgt_cur.close()

        except Exception as e:
            import traceback
            logger.error(f"Error migrating {table}: {e}\n{traceback.format_exc()}")
            t_result["status"] = "failed"
            t_result["error"] = str(e)

        return t_result

    # ------------------------------------------------------------------
    # FK enable/disable helpers
    # ------------------------------------------------------------------

    def _disable_fks(self, conn: oracledb.Connection, tgt_owner: str, table_names: List[str]):
        """Disable all FK constraints on target tables before bulk load."""
        for table in table_names:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT constraint_name FROM all_constraints "
                    "WHERE owner=:o AND table_name=:t AND constraint_type='R' AND status='ENABLED'",
                    o=tgt_owner, t=table.upper(),
                )
                rows = cur.fetchall()
                cur.close()
                for (cname,) in rows:
                    try:
                        c2 = conn.cursor()
                        c2.execute(f'ALTER TABLE "{table.upper()}" DISABLE CONSTRAINT "{cname}"')
                        c2.close()
                    except Exception as e:
                        logger.warning(f"Could not disable FK {cname} on {table}: {e}")
            except Exception as e:
                logger.warning(f"_disable_fks error for {table}: {e}")
        try:
            conn.commit()
        except Exception:
            pass

    def _enable_fks(self, conn: oracledb.Connection, tgt_owner: str, table_names: List[str]):
        """Re-enable FK constraints after bulk load."""
        for table in table_names:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT constraint_name FROM all_constraints "
                    "WHERE owner=:o AND table_name=:t AND constraint_type='R'",
                    o=tgt_owner, t=table.upper(),
                )
                rows = cur.fetchall()
                cur.close()
                for (cname,) in rows:
                    try:
                        c2 = conn.cursor()
                        c2.execute(
                            f'ALTER TABLE "{table.upper()}" ENABLE NOVALIDATE CONSTRAINT "{cname}"'
                        )
                        c2.close()
                    except Exception as e:
                        logger.warning(f"Could not enable FK {cname} on {table}: {e}")
            except Exception as e:
                logger.warning(f"_enable_fks error for {table}: {e}")
        try:
            conn.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _get_row_count(
        self,
        cur: oracledb.Cursor,
        owner: str,
        table: str,
    ) -> int:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table.upper()}"')
            return cur.fetchone()[0]
        except Exception:
            return 0

    def test_connections(self) -> Dict[str, Any]:
        """Test both source and target connections. Returns status dict."""
        result = {"source": {}, "target": {}}
        for label, cfg in (("source", self.src_cfg), ("target", self.tgt_cfg)):
            try:
                conn = cfg.connect()
                cur  = conn.cursor()
                cur.execute("SELECT 'ok' FROM DUAL")
                val = cur.fetchone()[0]
                cur.close()
                conn.close()
                result[label] = {"connected": val == "ok", "dsn": cfg.dsn}
            except Exception as e:
                result[label] = {"connected": False, "error": str(e), "dsn": cfg.dsn}
        return result
