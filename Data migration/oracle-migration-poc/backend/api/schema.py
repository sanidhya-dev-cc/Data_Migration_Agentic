"""
Schema API routes
"""

from fastapi import APIRouter, HTTPException
import structlog
from typing import List
import os

from models.migration import SchemaAnalysis, TableInfo, DependencyInfo, DatabaseConfig
from db import get_mock_tables, get_mock_dependencies, OracleClient, source_config, target_config

router = APIRouter()
logger = structlog.get_logger(__name__)

MOCK_MODE = os.getenv("ENABLE_MOCK_MODE", "false").lower() == "true"


@router.post("/analyze")
async def analyze_schema(db_config: DatabaseConfig) -> SchemaAnalysis:
    """Analyze database schema."""
    try:
        logger.info(f"Analyzing schema for: {db_config.db_id}")

        if MOCK_MODE:
            tables = get_mock_tables()
            dependencies = get_mock_dependencies()
        else:
            client = OracleClient(db_config)
            if not client.connect():
                raise HTTPException(status_code=500, detail="Failed to connect to database")
            tables = client.get_tables()
            table_names = [t.table_name for t in tables]
            dependencies = client.get_dependencies(table_names)
            client.disconnect()

        readiness_score = _calculate_readiness_score(tables, dependencies)

        return SchemaAnalysis(
            db_id=db_config.db_id,
            total_tables=len(tables),
            total_size_mb=sum(t.size_mb for t in tables),
            tables=tables,
            dependencies=dependencies,
            compatibility_issues=[],
            readiness_score=readiness_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source")
async def get_source_schema():
    """Get source database schema using env-configured connection."""
    try:
        if MOCK_MODE:
            tables = get_mock_tables()
            dependencies = get_mock_dependencies()
        else:
            cfg = source_config()
            db_cfg = DatabaseConfig(
                db_id="source_oracle",
                db_type="oracle_19c_standalone",
                host=cfg.host,
                port=cfg.port,
                service_name=cfg.service,
                username=cfg.user,
                password=cfg.password,
            )
            client = OracleClient(db_cfg)
            if not client.connect():
                raise HTTPException(status_code=500, detail="Cannot connect to source DB")
            tables = client.get_tables()
            dependencies = client.get_dependencies([t.table_name for t in tables])
            client.disconnect()

        return {
            "db_id": "source_oracle",
            "tables": [t.dict() for t in tables],
            "dependencies": [d.dict() for d in dependencies],
            "total_tables": len(tables),
            "total_size_mb": sum(t.size_mb for t in tables),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_source_schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/target")
async def get_target_schema():
    """Get target database schema using env-configured connection."""
    try:
        if MOCK_MODE:
            return {"db_id": "target_oracle", "tables": [], "dependencies": [],
                    "total_tables": 0, "total_size_mb": 0}

        cfg = target_config()
        db_cfg = DatabaseConfig(
            db_id="target_oracle",
            db_type="oracle_23c_cdb_pdb",
            host=cfg.host,
            port=cfg.port,
            service_name=cfg.service,
            username=cfg.user,
            password=cfg.password,
        )
        client = OracleClient(db_cfg)
        if not client.connect():
            # Target may be empty – return empty schema instead of error
            return {"db_id": "target_oracle", "tables": [], "dependencies": [],
                    "total_tables": 0, "total_size_mb": 0}
        tables = client.get_tables()
        dependencies = client.get_dependencies([t.table_name for t in tables])
        client.disconnect()

        return {
            "db_id": "target_oracle",
            "tables": [t.dict() for t in tables],
            "dependencies": [d.dict() for d in dependencies],
            "total_tables": len(tables),
            "total_size_mb": sum(t.size_mb for t in tables),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_target_schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_schemas(source_config_body: DatabaseConfig, target_config_body: DatabaseConfig):
    """Compare source and target schemas."""
    try:
        if MOCK_MODE:
            source_tables = get_mock_tables()
            target_tables: List[TableInfo] = []
        else:
            src_client = OracleClient(source_config_body)
            src_client.connect()
            source_tables = src_client.get_tables()
            src_client.disconnect()

            tgt_client = OracleClient(target_config_body)
            tgt_client.connect()
            target_tables = tgt_client.get_tables()
            tgt_client.disconnect()

        src_names = {t.table_name for t in source_tables}
        tgt_names = {t.table_name for t in target_tables}

        return {
            "source_db": source_config_body.db_id,
            "target_db": target_config_body.db_id,
            "source_tables": len(source_tables),
            "target_tables": len(target_tables),
            "missing_in_target": sorted(src_names - tgt_names),
            "extra_in_target": sorted(tgt_names - src_names),
            "common_tables": sorted(src_names & tgt_names),
            "schema_match": src_names == tgt_names,
        }

    except Exception as e:
        logger.error(f"Schema comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Legacy URL aliases kept for frontend compatibility
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/source/{db_id}")
async def get_source_schema_by_id(db_id: str):
    return await get_source_schema()


@router.get("/target/{db_id}")
async def get_target_schema_by_id(db_id: str):
    return await get_target_schema()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _calculate_readiness_score(
    tables: List[TableInfo], dependencies: List[DependencyInfo]
) -> float:
    score = 100.0
    score -= len([t for t in tables if t.size_mb > 100]) * 5
    score -= len([d for d in dependencies if d.risk_level == "high"]) * 10
    score -= len([d for d in dependencies if d.risk_level == "medium"]) * 5
    return max(0.0, min(100.0, score))
