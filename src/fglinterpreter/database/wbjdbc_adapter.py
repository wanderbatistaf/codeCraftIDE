"""
WBJDBC adapter for fglInterpreter.

This module provides a concrete implementation of DatabaseConnector using wbjdbc,
a JDBC-style driver for Informix databases in Python.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from .connector import ConnectionConfig, DatabaseConnector
from .exceptions import (
    ConnectionError,
    DataError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    QueryError,
    TransactionError,
)
from .logging import DatabaseLogger

# Check if wbjdbc is available
try:
    import wbjdbc

    WBJDBC_AVAILABLE = True
except ImportError:
    WBJDBC_AVAILABLE = False


class WBJDBCConnector(DatabaseConnector):
    """
    Database connector implementation using wbjdbc.

    Provides direct JDBC-style access to Informix and other databases.

    wbjdbc handles JVM initialization and JDBC driver management automatically.
    """

    # Map driver names to wbjdbc db_type strings
    DB_TYPE_MAP = {
        "informix": "informix-sqli",
        "mysql": "mysql",
        "postgresql": "postgresql",
    }

    def __init__(self, config: ConnectionConfig):
        """Initialize WBJDBC connector.

        Args:
            config: Database connection configuration

        Raises:
            ConfigurationError: If wbjdbc is not installed
        """
        super().__init__(config)
        if not WBJDBC_AVAILABLE:
            from .exceptions import ConfigurationError

            raise ConfigurationError("wbjdbc is not installed. Install it with: pip install wbjdbc")

        self._cursor = None
        self._logger = DatabaseLogger("wbjdbc")

        # Extract database type from config (default to informix)
        self._db_type_name = self.config.extra_params.get("db_type", "informix")
        self._db_type = self.DB_TYPE_MAP.get(self._db_type_name, "informix-sqli")

        # Extract server for Informix
        self._server = self.config.extra_params.get("server", None)

    def connect(self) -> None:
        """Establish database connection.

        Raises:
            ConnectionError: If connection fails
        """
        if self.is_connected():
            return

        try:
            # Use wbjdbc.connect_to_db with proper parameters
            # Signature: (db_type, host, database, user, password, port, server, ...)
            self._connection = wbjdbc.connect_to_db(
                db_type=self._db_type,
                host=self.config.host,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                port=self.config.port,
                server=self._server,
                debug=self.config.extra_params.get("debug", 0),
            )

            if self._connection is None:
                raise Exception("connect_to_db returned None")

            # Create cursor
            self._cursor = self._connection.cursor()

            # Log successful connection
            self._logger.connection_opened(
                driver="wbjdbc",
                host=self.config.host,
                database=self.config.database,
                port=self.config.port,
            )

        except Exception as e:
            # Log connection failure
            self._logger.connection_failed(
                driver="wbjdbc", host=self.config.host, database=self.config.database, error=e
            )

            raise ConnectionError(
                f"Failed to connect to database: {self.config.host}:{self.config.port}",
                driver_error=e,
                context={
                    "driver": "wbjdbc",
                    "host": self.config.host,
                    "database": self.config.database,
                    "port": self.config.port,
                    "db_type": self._db_type_name,
                },
            )

    def disconnect(self) -> None:
        """Close database connection.

        Raises:
            ConnectionError: If disconnect fails
        """
        try:
            if self._cursor:
                self._cursor.close()
                self._cursor = None

            if self._connection:
                self._connection.close()
                self._connection = None

            # Log successful disconnection
            self._logger.connection_closed(driver="wbjdbc", database=self.config.database)

        except Exception as e:
            raise ConnectionError("Failed to disconnect from database", driver_error=e)

    def is_connected(self) -> bool:
        """Check if currently connected to database.

        Returns:
            True if connected, False otherwise
        """
        return self._connection is not None and self._cursor is not None

    def _check_connection(self) -> None:
        """Check connection and raise if not connected."""
        if not self.is_connected():
            raise ConnectionError("Not connected to database. Call connect() first.")

    def _map_exception(self, e: Exception, query: Optional[str] = None) -> Exception:
        """Map driver exception to appropriate database exception.

        Args:
            e: Original exception
            query: SQL query that caused the error (optional)

        Returns:
            Mapped exception
        """
        error_msg = str(e).lower()

        # Map based on error message patterns
        if "integrity" in error_msg or "constraint" in error_msg:
            return IntegrityError(str(e), driver_error=e)
        elif "type" in error_msg or "conversion" in error_msg:
            return DataError(str(e), driver_error=e)
        elif "syntax" in error_msg or "not found" in error_msg:
            return ProgrammingError(str(e), driver_error=e)
        elif "connection" in error_msg or "network" in error_msg:
            return OperationalError(str(e), driver_error=e)
        else:
            return QueryError(str(e), query=query, driver_error=e)

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
        self._check_connection()

        start_time = time.time()

        try:
            if params:
                self._cursor.execute(query, params)
            else:
                self._cursor.execute(query)

            # Get row count - wbjdbc cursor should have rowcount attribute
            rowcount = getattr(self._cursor, "rowcount", 0)

            # Note: wbjdbc connections don't have explicit commit/rollback
            # They use JDBC's auto-commit behavior

            duration = time.time() - start_time
            actual_rowcount = rowcount if rowcount >= 0 else 0

            # Log successful execution
            self._logger.query_executed(
                query=query, params=params, duration=duration, row_count=actual_rowcount
            )

            return actual_rowcount

        except Exception as e:
            duration = time.time() - start_time

            # Log query failure
            self._logger.query_failed(query=query, params=params, error=e, duration=duration)

            mapped_error = self._map_exception(e, query)
            raise mapped_error

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
        self._check_connection()

        start_time = time.time()

        try:
            if params:
                self._cursor.execute(query, params)
            else:
                self._cursor.execute(query)

            # Use fetchdh() to get results as dictionaries
            # This is wbjdbc's special method for dict/hash results
            if hasattr(self._cursor, "fetchdh"):
                results = self._cursor.fetchdh()
            else:
                # Fallback to fetchall() and manual dict conversion
                rows = self._cursor.fetchall()

                # Get column names from description
                if hasattr(self._cursor, "description") and self._cursor.description:
                    columns = [desc[0] for desc in self._cursor.description]
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    results = []

            duration = time.time() - start_time
            row_count = len(results) if results else 0

            # Log successful query
            self._logger.query_executed(
                query=query, params=params, duration=duration, row_count=row_count
            )

            return results

        except Exception as e:
            duration = time.time() - start_time

            # Log query failure
            self._logger.query_failed(query=query, params=params, error=e, duration=duration)

            mapped_error = self._map_exception(e, query)
            raise mapped_error

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
        self._check_connection()

        try:
            if params:
                self._cursor.execute(query, params)
            else:
                self._cursor.execute(query)

            # Fetch one result
            row = self._cursor.fetchone()

            if row is None:
                return None

            # Get column names from description
            if hasattr(self._cursor, "description") and self._cursor.description:
                columns = [desc[0] for desc in self._cursor.description]
                return dict(zip(columns, row))

            return None

        except Exception as e:
            mapped_error = self._map_exception(e, query)
            raise mapped_error

    def begin_transaction(self) -> None:
        """Begin a database transaction.

        Note: wbjdbc uses JDBC's auto-commit behavior.
        Transaction support may be limited.

        Raises:
            TransactionError: If transaction cannot be started
            ConnectionError: If not connected
        """
        self._check_connection()

        if self._in_transaction:
            raise TransactionError("Transaction already in progress")

        # Mark that we're in a transaction
        # wbjdbc doesn't have explicit transaction begin
        self._in_transaction = True

    def commit(self) -> None:
        """Commit the current transaction.

        Note: wbjdbc uses JDBC's auto-commit behavior.
        This is a no-op for compatibility.

        Raises:
            TransactionError: If commit fails
            ConnectionError: If not connected
        """
        self._check_connection()

        if not self._in_transaction:
            raise TransactionError("No transaction in progress")

        # wbjdbc doesn't have explicit commit
        # JDBC auto-commits by default
        self._in_transaction = False

    def rollback(self) -> None:
        """Rollback the current transaction.

        Note: wbjdbc uses JDBC's auto-commit behavior.
        This is a no-op for compatibility.

        Raises:
            TransactionError: If rollback fails
            ConnectionError: If not connected
        """
        self._check_connection()

        if not self._in_transaction:
            raise TransactionError("No transaction in progress")

        # wbjdbc doesn't have explicit rollback
        # JDBC auto-commits by default
        self._in_transaction = False
