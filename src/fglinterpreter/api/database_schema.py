"""
FastAPI router for database schema exploration.

This module provides endpoints for exploring database structure (tables, columns, etc.)
"""

import re
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import DatabaseConfigModel, _load_configs

# Try to import wbjdbc (may not be available in all environments)
try:
    import wbjdbc

    WBJDBC_AVAILABLE = True
except ImportError:
    WBJDBC_AVAILABLE = False
    wbjdbc = None

router = APIRouter(prefix="/api/database", tags=["database-schema"])


class TableColumn(BaseModel):
    """Model for a database table column."""

    name: str
    type: str
    nullable: bool
    primary_key: bool = False
    default_value: Optional[str] = None
    description: Optional[str] = None


class TableInfo(BaseModel):
    """Model for a database table."""

    name: str
    type: str  # "table" or "view"
    columns: List[TableColumn] = []
    row_count: Optional[int] = None


class GetTablesResponse(BaseModel):
    """Response model for listing tables."""

    status: str
    tables: List[TableInfo]
    error: Optional[str] = None


class GetTableSchemaResponse(BaseModel):
    """Response model for getting table schema."""

    status: str
    table: Optional[TableInfo] = None
    error: Optional[str] = None


def _parse_informix_type(coltype: int, collength: int) -> str:
    """
    Parse Informix column type code to readable type name.

    Based on Informix syscolumns.coltype values:
    0 = CHAR, 1 = SMALLINT, 2 = INTEGER, 3 = FLOAT, 4 = SMALLFLOAT,
    5 = DECIMAL, 6 = SERIAL, 7 = DATE, 8 = MONEY, 9 = NULL,
    10 = DATETIME, 11 = BYTE, 12 = TEXT, 13 = VARCHAR, 14 = INTERVAL,
    15 = NCHAR, 16 = NVARCHAR, 17 = INT8, 18 = SERIAL8, 19 = SET,
    20 = MULTISET, 21 = LIST, 22 = ROW, 40 = LVARCHAR, etc.

    If coltype > 256, it means NOT NULL (subtract 256)
    """
    # Check if NOT NULL
    nullable = coltype < 256
    if coltype >= 256:
        coltype = coltype - 256

    # Type mapping
    type_map = {
        0: f"CHAR({collength})",
        1: "SMALLINT",
        2: "INTEGER",
        3: "FLOAT",
        4: "SMALLFLOAT",
        5: f"DECIMAL({collength})",  # Simplified
        6: "SERIAL",
        7: "DATE",
        8: f"MONEY({collength})",  # Simplified
        10: "DATETIME",
        11: "BYTE",
        12: "TEXT",
        13: f"VARCHAR({collength})",
        14: "INTERVAL",
        15: f"NCHAR({collength})",
        16: f"NVARCHAR({collength})",
        17: "INT8",
        18: "SERIAL8",
        40: f"LVARCHAR({collength})",
    }

    type_name = type_map.get(coltype, f"UNKNOWN({coltype})")

    return type_name, nullable


def _execute_sql_via_wbjdbc(config: DatabaseConfigModel, sql: str) -> List[Dict]:
    """
    Execute SQL query via WBJDBC and return results.

    Args:
        config: Database configuration
        sql: SQL query to execute

    Returns:
        List of dictionaries with query results

    Raises:
        Exception: If query execution fails
    """
    conn = None
    try:
        # Connect to database using WBJDBC
        conn = wbjdbc.connect_to_db(
            db_type="informix-sqli",
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password,
            server=config.server,
            debug=0,
        )

        if conn is None:
            raise Exception("Failed to connect to database")

        # Execute query
        cursor = conn.cursor()
        cursor.execute(sql)

        # Check if this is a query that returns results (SELECT, SHOW, DESCRIBE, etc.)
        # vs a statement that modifies data (INSERT, UPDATE, DELETE, CREATE, etc.)
        sql_upper = sql.strip().upper()
        is_select_query = sql_upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN"))

        results = []

        if is_select_query:
            # Fetch results for SELECT queries
            rows = cursor.fetchall()

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Convert to list of dicts with Python native types
            for row in rows:
                # Convert Java objects to Python native types
                python_row = {}
                for col, val in zip(columns, row):
                    # Convert Java objects to Python native types
                    if val is None:
                        python_row[str(col)] = None
                    elif hasattr(val, "toString"):
                        # Java object - convert to string
                        python_row[str(col)] = str(val)
                    elif isinstance(val, (str, int, float, bool)):
                        # Already a Python primitive
                        python_row[str(col)] = val
                    else:
                        # Unknown type - convert to string as fallback
                        python_row[str(col)] = str(val)
                results.append(python_row)
        else:
            # For DDL/DML statements (CREATE, INSERT, UPDATE, DELETE, etc.)
            # Don't try to fetch results - just commit the transaction
            # Return empty result set (the statement executed successfully)
            pass

        cursor.close()
        return results

    except Exception as e:
        raise Exception(f"SQL execution failed: {str(e)}")

    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _parse_dbaccess_output(output: List[str]) -> List[Dict]:
    """
    Parse dbaccess output into structured data.

    dbaccess output format:

    column1  column2  column3
    -------  -------  -------
    value1   value2   value3
    value1   value2   value3

    Args:
        output: Lines from dbaccess output

    Returns:
        List of dictionaries with column data
    """
    results = []

    # Find the header line and separator
    header_idx = -1
    separator_idx = -1

    for i, line in enumerate(output):
        # Skip empty lines and database selection messages
        if not line.strip() or "Database selected" in line:
            continue

        # Look for separator line (dashes)
        if re.match(r"^[\s-]+$", line):
            separator_idx = i
            if header_idx == -1:
                header_idx = i - 1
            continue

        # If we found header and separator, parse data rows
        if header_idx != -1 and separator_idx != -1 and i > separator_idx:
            if line.strip():
                # Parse header to get column names and positions
                if not results:  # First time, parse header
                    header_line = output[header_idx]
                    columns = header_line.split()

                # Parse data row
                values = line.split()
                if len(values) > 0:
                    row = {}
                    for j, col in enumerate(columns):
                        row[col] = values[j] if j < len(values) else None
                    results.append(row)

    return results


@router.get("/{config_name}/tables", response_model=GetTablesResponse)
async def get_database_tables(config_name: str):
    """
    Get list of tables in the database.

    Args:
        config_name: Name of the database configuration to use

    Returns:
        List of tables with basic information
    """
    try:
        # Load configuration
        configs = _load_configs()
        if config_name not in configs:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")

        config = configs[config_name]

        # Query to get all user tables
        sql = """
        SELECT tabname, tabtype
        FROM systables
        WHERE tabid >= 100
        AND tabtype IN ('T', 'V')
        ORDER BY tabname
        """

        rows = _execute_sql_via_wbjdbc(config, sql)

        # Convert to TableInfo objects
        tables = []
        for row in rows:
            table_type = "table" if row.get("tabtype") == "T" else "view"
            tables.append(
                TableInfo(
                    name=row.get("tabname", ""),
                    type=table_type,
                    columns=[],  # Will be loaded on demand
                )
            )

        return GetTablesResponse(status="success", tables=tables)

    except Exception as e:
        return GetTablesResponse(status="error", tables=[], error=str(e))


@router.get("/{config_name}/table/{table_name}/schema", response_model=GetTableSchemaResponse)
async def get_table_schema(config_name: str, table_name: str):
    """
    Get detailed schema for a specific table.

    Args:
        config_name: Name of the database configuration
        table_name: Name of the table

    Returns:
        Detailed table schema with columns
    """
    try:
        # Load configuration
        configs = _load_configs()
        if config_name not in configs:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")

        config = configs[config_name]

        # Query to get table columns
        sql = f"""
        SELECT
            c.colname,
            c.coltype,
            c.collength,
            c.colno
        FROM syscolumns c
        JOIN systables t ON c.tabid = t.tabid
        WHERE t.tabname = '{table_name}'
        ORDER BY c.colno
        """

        rows = _execute_sql_via_wbjdbc(config, sql)

        # Get primary key information
        # Note: PK detection via sysindexes is simplified and not yet used

        # Convert to TableColumn objects
        columns = []
        for row in rows:
            coltype = int(row.get("coltype", 0))
            collength = int(row.get("collength", 0))

            type_name, nullable = _parse_informix_type(coltype, collength)

            columns.append(
                TableColumn(
                    name=row.get("colname", ""),
                    type=type_name,
                    nullable=nullable,
                    primary_key=False,  # Would need to check constraints
                )
            )

        # Get table type
        type_sql = f"SELECT tabtype FROM systables WHERE tabname = '{table_name}'"
        type_rows = _execute_sql_via_wbjdbc(config, type_sql)
        table_type = "table" if type_rows and type_rows[0].get("tabtype") == "T" else "view"

        table_info = TableInfo(name=table_name, type=table_type, columns=columns)

        return GetTableSchemaResponse(status="success", table=table_info)

    except Exception as e:
        return GetTableSchemaResponse(status="error", table=None, error=str(e))


@router.get("/{config_name}/table/{table_name}/data")
async def get_table_sample_data(config_name: str, table_name: str, limit: int = 100):
    """
    Get sample data from a table.

    Args:
        config_name: Name of the database configuration
        table_name: Name of the table
        limit: Maximum number of rows to return (default 100)

    Returns:
        Sample data from the table
    """
    try:
        # Load configuration
        configs = _load_configs()
        if config_name not in configs:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")

        config = configs[config_name]

        # Query to get sample data
        sql = f"SELECT * FROM {table_name} WHERE 1=1 LIMIT {min(limit, 1000)}"

        rows = _execute_sql_via_wbjdbc(config, sql)

        return {"status": "success", "table": table_name, "rows": rows, "count": len(rows)}

    except Exception as e:
        return {"status": "error", "table": table_name, "rows": [], "count": 0, "error": str(e)}


@router.get("/{config_name}/refresh")
async def refresh_database_cache(config_name: str):
    """
    Refresh cached database schema information.

    Args:
        config_name: Name of the database configuration

    Returns:
        Status of refresh operation
    """
    # For now, we don't cache anything, so just return success
    # In the future, we could implement caching here
    return {"status": "success", "message": f"Schema cache refreshed for '{config_name}'"}
