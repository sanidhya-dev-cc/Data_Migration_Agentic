"""
Oracle Database Client
Handles Oracle connectivity and operations
"""

import oracledb
from typing import List, Dict, Any, Optional
import structlog
from models.migration import DatabaseConfig, TableInfo, DependencyInfo
import os

logger = structlog.get_logger(__name__)


class OracleClient:
    """Oracle database client for migration operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            # For POC, using thin mode (no Oracle Client required)
            connection_string = (
                f"{self.config.username}/{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.service_name}"
            )
            
            self.connection = oracledb.connect(connection_string)
            logger.info(f"Connected to Oracle database: {self.config.db_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Oracle: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info(f"Disconnected from Oracle database: {self.config.db_id}")
    
    def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get list of tables with live row counts for the given schema."""
        if not self.connection:
            self.connect()

        schema_name = (schema or self.config.username).upper()
        tables: List[TableInfo] = []

        try:
            # ALL_TABLES is accessible; ALL_SEGMENTS requires DBA privilege on XE – skip it.
            cur = self.connection.cursor()
            cur.execute(
                "SELECT TABLE_NAME, OWNER FROM ALL_TABLES WHERE OWNER = :schema ORDER BY TABLE_NAME",
                schema=schema_name,
            )
            rows = cur.fetchall()
            cur.close()

            # Live COUNT(*) per table using owner-qualified name
            for tname, owner in rows:
                try:
                    cnt_cur = self.connection.cursor()
                    cnt_cur.execute(f"SELECT COUNT(*) FROM {owner}.{tname}")
                    live_count = cnt_cur.fetchone()[0]
                    cnt_cur.close()
                except Exception:
                    live_count = 0

                tables.append(TableInfo(
                    table_name=tname,
                    schema_name=owner,
                    row_count=live_count,
                    size_mb=0.0,   # segment size not available without DBA_SEGMENTS
                    selected=True,
                ))

            logger.info(f"Retrieved {len(tables)} tables from {self.config.db_id}")

        except Exception as e:
            logger.error(f"Error retrieving tables: {str(e)}")

        return tables
    
    def get_dependencies(self, table_names: List[str]) -> List[DependencyInfo]:
        """Discover table dependencies (foreign keys)."""
        if not self.connection:
            self.connect()

        if not table_names:
            return []

        cursor = self.connection.cursor()
        dependencies = []

        try:
            placeholders = ",".join([f"'{t}'" for t in table_names])
            fk_query = f"""
                SELECT
                    a.TABLE_NAME,
                    c_pk.TABLE_NAME AS REFERENCED_TABLE,
                    a.CONSTRAINT_NAME
                FROM
                    ALL_CONSTRAINTS a
                JOIN ALL_CONSTRAINTS c_pk
                    ON  a.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
                    AND a.R_OWNER           = c_pk.OWNER
                WHERE
                    a.CONSTRAINT_TYPE = 'R'
                    AND a.OWNER = :owner
                    AND a.TABLE_NAME IN ({placeholders})
            """
            cursor.execute(fk_query, owner=self.config.username.upper())
            
            dep_map: Dict[str, List[str]] = {}
            for row in cursor:
                table = row[0]
                referenced = row[1]
                if table not in dep_map:
                    dep_map[table] = []
                if referenced not in dep_map[table]:
                    dep_map[table].append(referenced)
            
            for table, depends_on in dep_map.items():
                dependencies.append(DependencyInfo(
                    table_name=table,
                    depends_on=depends_on,
                    dependency_type="foreign_key",
                    risk_level="medium" if len(depends_on) > 2 else "low"
                ))
            
            logger.info(f"Discovered {len(dependencies)} dependencies")
            return dependencies
            
        except Exception as e:
            logger.error(f"Error discovering dependencies: {str(e)}")
            return []
        finally:
            cursor.close()
    
    def validate_schema(self, expected_tables: List[str]) -> Dict[str, Any]:
        """Validate schema against expected tables"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            query = """
                SELECT TABLE_NAME 
                FROM ALL_TABLES 
                WHERE OWNER = :schema
            """
            
            cursor.execute(query, schema=self.config.username.upper())
            existing_tables = [row[0] for row in cursor]
            
            missing = [t for t in expected_tables if t not in existing_tables]
            extra = [t for t in existing_tables if t not in expected_tables and not t.startswith('SYS')]
            
            return {
                "valid": len(missing) == 0,
                "existing_tables": existing_tables,
                "missing_tables": missing,
                "extra_tables": extra
            }
            
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}")
            return {"valid": False, "error": str(e)}
        finally:
            cursor.close()
    
    def get_row_count(self, table_name: str) -> int:
        """Get accurate row count for a table"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return int(count)
        except Exception as e:
            logger.error(f"Error getting row count for {table_name}: {str(e)}")
            return 0
        finally:
            cursor.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return metadata"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Get Oracle version
            cursor.execute("SELECT * FROM v$version WHERE ROWNUM = 1")
            version = cursor.fetchone()[0]
            
            # Check if CDB
            cursor.execute("""
                SELECT 
                    DECODE(CDB, 'YES', 'CDB', 'NO', 'Non-CDB', 'Unknown') as DB_TYPE
                FROM 
                    v$database
            """)
            db_type = cursor.fetchone()[0]
            
            # If CDB, get PDB info
            pdb_info = None
            if db_type == 'CDB':
                cursor.execute("""
                    SELECT NAME, OPEN_MODE 
                    FROM v$pdbs 
                    WHERE NAME != 'PDB$SEED'
                """)
                pdbs = cursor.fetchall()
                pdb_info = [{"name": row[0], "open_mode": row[1]} for row in pdbs]
            
            cursor.close()
            
            return {
                "connected": True,
                "version": version,
                "db_type": db_type,
                "pdb_info": pdb_info,
                "host": self.config.host,
                "port": self.config.port,
                "service": self.config.service_name
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e)
            }


def get_mock_tables() -> List[TableInfo]:
    """Generate mock tables for testing"""
    return [
        TableInfo(
            table_name="CUSTOMER",
            schema_name="MIGRATION_USER",
            row_count=100000,
            size_mb=25.5,
            selected=True
        ),
        TableInfo(
            table_name="ORDERS",
            schema_name="MIGRATION_USER",
            row_count=250000,
            size_mb=75.2,
            selected=True
        ),
        TableInfo(
            table_name="PAYMENTS",
            schema_name="MIGRATION_USER",
            row_count=500000,
            size_mb=150.8,
            selected=True
        ),
        TableInfo(
            table_name="PRODUCTS",
            schema_name="MIGRATION_USER",
            row_count=50000,
            size_mb=12.3,
            selected=True
        ),
        TableInfo(
            table_name="ORDER_ITEMS",
            schema_name="MIGRATION_USER",
            row_count=750000,
            size_mb=200.5,
            selected=True
        )
    ]


def get_mock_dependencies() -> List[DependencyInfo]:
    """Generate mock dependencies for testing"""
    return [
        DependencyInfo(
            table_name="ORDERS",
            depends_on=["CUSTOMER"],
            dependency_type="foreign_key",
            risk_level="medium"
        ),
        DependencyInfo(
            table_name="ORDER_ITEMS",
            depends_on=["ORDERS", "PRODUCTS"],
            dependency_type="foreign_key",
            risk_level="high"
        ),
        DependencyInfo(
            table_name="PAYMENTS",
            depends_on=["ORDERS"],
            dependency_type="foreign_key",
            risk_level="medium"
        )
    ]
