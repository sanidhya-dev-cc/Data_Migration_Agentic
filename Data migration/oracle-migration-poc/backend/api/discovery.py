"""
Discovery API routes
"""

from fastapi import APIRouter, HTTPException
import structlog
from typing import Dict, Any
import os

from models.migration import DatabaseConfig, DatabaseType
from db import OracleClient, source_config, target_config

router = APIRouter()
logger = structlog.get_logger(__name__)

MOCK_MODE = os.getenv("ENABLE_MOCK_MODE", "false").lower() == "true"


@router.post("/test-connection")
async def test_connection(db_config: DatabaseConfig) -> Dict[str, Any]:
    """Test database connection."""
    try:
        logger.info(f"Testing connection to: {db_config.db_id}")

        if MOCK_MODE:
            return {
                "connected": True,
                "db_id": db_config.db_id,
                "db_type": db_config.db_type.value,
                "version": "Oracle Database 21c Express Edition (mock)",
                "host": db_config.host,
                "port": db_config.port,
                "service": db_config.service_name,
            }

        client = OracleClient(db_config)
        result = client.test_connection()
        result["db_id"] = db_config.db_id
        result["db_type"] = db_config.db_type.value
        client.disconnect()
        return result

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases")
async def list_databases():
    """List configured source and target databases."""
    try:
        src = source_config()
        tgt = target_config()

        databases = [
            {
                "db_id": "source_oracle",
                "db_type": DatabaseType.ORACLE_19C_STANDALONE.value,
                "host": src.host,
                "port": src.port,
                "service_name": src.service,
                "description": "Oracle XE 21c – Source database (pre-populated with test data)",
            },
            {
                "db_id": "target_oracle",
                "db_type": DatabaseType.ORACLE_23C_CDB_PDB.value,
                "host": tgt.host,
                "port": tgt.port,
                "service_name": tgt.service,
                "description": "Oracle XE 21c – Target database (empty, ready for migration)",
            },
        ]
        return databases

    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-check")
async def db_health_check():
    """Check connectivity to both source and target databases."""
    from db import MigrationEngine
    try:
        if MOCK_MODE:
            return {
                "source": {"connected": True, "mode": "mock"},
                "target": {"connected": True, "mode": "mock"},
            }
        engine = MigrationEngine()
        return engine.test_connections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
