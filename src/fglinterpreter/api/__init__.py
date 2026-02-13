"""
FastAPI backend for fglInterpreter IDE.

This module provides HTTP API endpoints for code execution, parsing,
and validation.
"""

from .main import app
from .models import (
    DatabaseConfig,
    ErrorResponse,
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    ParseRequest,
    ParseResponse,
)

__all__ = [
    "app",
    "ExecuteRequest",
    "ExecuteResponse",
    "ErrorResponse",
    "ParseRequest",
    "ParseResponse",
    "HealthResponse",
    "DatabaseConfig",
]
