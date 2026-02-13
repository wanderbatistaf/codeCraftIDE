"""
Abstract database connector interface for fglInterpreter.

This module defines the base interface that all database connectors must implement,
providing a unified API for database operations regardless of the underlying driver.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ConnectionConfig:
    """Database connection configuration."""

    host: str
    port: int
    database: str
    username: str
    password: str
    driver: str = "wbjdbc"  # or "wborm"
    pool_size: int = 5
    pool_timeout: int = 30
    autocommit: bool = False
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class DatabaseConnector(ABC):
    """
    Abstract base class for database connectors.

    This defines the interface that all database connectors (wbjdbc, wborm, etc.)
    must implement to provide consistent database access.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize connector with configuration.

        Args:
            config: Database connection configuration
        """
        self.config = config
        self._connection = None
        self._in_transaction = False

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection.

        Raises:
            ConnectionError: If disconnect fails
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to database.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        """Execute a SQL statement (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query to execute
            params: Query parameters (optional)

        Returns:
            Number of affected rows

        Raises:
            QueryError: If query execution fails
            ConnectionError: If not connected
        """
        pass

    @abstractmethod
    def query(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters (optional)

        Returns:
            List of result rows as dictionaries

        Raises:
            QueryError: If query execution fails
            ConnectionError: If not connected
        """
        pass

    @abstractmethod
    def query_one(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return first result.

        Args:
            query: SQL query to execute
            params: Query parameters (optional)

        Returns:
            First result row as dictionary, or None if no results

        Raises:
            QueryError: If query execution fails
            ConnectionError: If not connected
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction.

        Raises:
            TransactionError: If transaction cannot be started
            ConnectionError: If not connected
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction.

        Raises:
            TransactionError: If commit fails
            ConnectionError: If not connected
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction.

        Raises:
            TransactionError: If rollback fails
            ConnectionError: If not connected
        """
        pass

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for transaction handling.

        Automatically commits on success, rolls back on exception.

        Example:
            with connector.transaction():
                connector.execute("INSERT INTO table VALUES (?)", (value,))
                connector.execute("UPDATE other_table SET x = ?", (new_value,))

        Yields:
            None

        Raises:
            TransactionError: If transaction operations fail
        """
        try:
            self.begin_transaction()
            yield
            self.commit()
        except Exception:
            self.rollback()
            raise

    def __enter__(self):
        """Context manager entry - connect to database."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from database."""
        if exc_type is not None and self._in_transaction:
            # Exception occurred, rollback
            try:
                self.rollback()
            except Exception:
                pass  # Ignore rollback errors during exception handling
        self.disconnect()
        return False  # Don't suppress exceptions


class ConnectionPool(ABC):
    """
    Abstract base class for connection pooling.

    Manages a pool of database connections for efficient reuse.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize connection pool.

        Args:
            config: Database connection configuration
        """
        self.config = config
        self._pool: List[DatabaseConnector] = []
        self._in_use: set = set()

    @abstractmethod
    def get_connection(self) -> DatabaseConnector:
        """Get a connection from the pool.

        Returns:
            A database connector instance

        Raises:
            ConnectionError: If no connections available
        """
        pass

    @abstractmethod
    def release_connection(self, connector: DatabaseConnector) -> None:
        """Release a connection back to the pool.

        Args:
            connector: The connector to release

        Raises:
            ValueError: If connector not from this pool
        """
        pass

    @abstractmethod
    def close_all(self) -> None:
        """Close all connections in the pool."""
        pass

    @contextmanager
    def connection(self) -> Generator[DatabaseConnector, None, None]:
        """Context manager to get and release a connection.

        Example:
            with pool.connection() as conn:
                conn.execute("SELECT * FROM table")

        Yields:
            A database connector instance
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.release_connection(conn)
