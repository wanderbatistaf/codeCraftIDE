"""
Database integration for Informix via wbjdbc and wborm.

This module provides:
- Database connector interface (DatabaseConnector)
- wbjdbc integration (WBJDBCConnector)
- wborm ORM layer (WBORMConnector)
- Connection pooling (ConnectionPool, create_connection_pool)
- Transaction management
- Database exception hierarchy
- Structured logging for database operations

Story 2.1: Database Connector Interface - COMPLETE
Story 2.3: Error Handling & Logging Layer - IN PROGRESS
"""

from .connector import ConnectionConfig, ConnectionPool, DatabaseConnector
from .exceptions import (
    ConfigurationError,
    ConnectionError,
    CursorError,
    DatabaseError,
    DataError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    QueryError,
    RetryableError,
    TimeoutError,
    TransactionError,
)
from .logging import DatabaseLogger, configure_logging, db_logger

# Try to import database adapters (may fail if database drivers not available)
try:
    from .wbjdbc_adapter import WBJDBCConnector
except Exception:
    WBJDBCConnector = None

try:
    from .wborm_adapter import WBORMConnector
except Exception:
    WBORMConnector = None

try:
    from .pool import SimpleConnectionPool, create_connection_pool
except Exception:
    SimpleConnectionPool = None
    create_connection_pool = None

__all__ = [
    # Core interfaces
    "DatabaseConnector",
    "ConnectionConfig",
    "ConnectionPool",
    # Connector implementations
    "WBJDBCConnector",
    "WBORMConnector",
    # Connection pooling
    "SimpleConnectionPool",
    "create_connection_pool",
    # Logging
    "DatabaseLogger",
    "configure_logging",
    "db_logger",
    # Exceptions
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    "QueryError",
    "DataError",
    "IntegrityError",
    "OperationalError",
    "ProgrammingError",
    "ConfigurationError",
    "CursorError",
    "TimeoutError",
    "RetryableError",
]


def create_connector(config: ConnectionConfig) -> DatabaseConnector:
    """Factory function to create a database connector.

    Args:
        config: Database connection configuration

    Returns:
        A database connector instance (WBJDBCConnector or WBORMConnector)

    Raises:
        ConfigurationError: If driver is not supported
    """
    if config.driver == "wbjdbc":
        return WBJDBCConnector(config)
    elif config.driver == "wborm":
        return WBORMConnector(config)
    else:
        raise ConfigurationError(
            f"Unknown driver: {config.driver}. Supported drivers: wbjdbc, wborm"
        )


__all__.append("create_connector")
