"""
FastAPI router for executing SQL queries.

This module provides endpoints for executing ad-hoc SQL queries against configured databases.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# Auth imports
from .auth.config import auth_config
from .auth.core.permissions import Permission, require_permission
from .auth.dependencies.auth_deps import get_current_user_optional
from .auth.models import CurrentUser
from .database import _load_configs
from .database_schema import _execute_sql_via_wbjdbc

router = APIRouter(prefix="/api/sql", tags=["sql-query"])


class ExecuteSQLRequest(BaseModel):
    """Request model for executing SQL query."""

    config_name: str
    query: str


class ExecuteSQLResponse(BaseModel):
    """Response model for SQL query execution."""

    status: str
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    execution_time: Optional[float] = None
    error: Optional[str] = None


@router.post("/execute", response_model=ExecuteSQLResponse)
async def execute_sql_query(
    request: ExecuteSQLRequest,
    current_user: CurrentUser = Depends(
        require_permission(Permission.QUERY_DATABASE)
        if auth_config.enabled
        else get_current_user_optional
    ),
):
    """
    Execute an SQL query against a configured database.

    Requires QUERY_DATABASE permission (Developer or Admin role).

    Args:
        request: SQL query execution request with config name and query
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Query results with columns, rows, and metadata
    """
    import time

    try:
        # Load configuration
        configs = _load_configs()
        if request.config_name not in configs:
            raise HTTPException(
                status_code=404, detail=f"Configuration '{request.config_name}' not found"
            )

        config = configs[request.config_name]

        # Validate query (basic validation)
        query = request.query.strip()
        if not query:
            return ExecuteSQLResponse(status="error", error="Query cannot be empty")

        # Start timing
        start_time = time.time()

        # Execute query
        rows = _execute_sql_via_wbjdbc(config, query)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Extract column names from first row
        columns = []
        if rows and len(rows) > 0:
            columns = list(rows[0].keys())

        return ExecuteSQLResponse(
            status="success",
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time=execution_time,
        )

    except Exception as e:
        return ExecuteSQLResponse(status="error", error=str(e))


@router.get("/history")
async def get_query_history(
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Get SQL query history.

    Args:
        current_user: Current authenticated user (optional)

    Returns:
        List of previously executed queries
    """
    # TODO: Implement query history storage and retrieval
    # For now, return empty list
    return {"status": "success", "queries": []}
