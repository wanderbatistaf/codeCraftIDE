"""
WBORM adapter for fglInterpreter.

This module provides a concrete implementation of DatabaseConnector using wborm,
an ORM layer for Informix databases in Python.

wborm is built on top of wbjdbc and provides automatic schema introspection
and model generation for JDBC databases.
"""

from typing import Any, Dict, List, Optional, Tuple

from .connector import ConnectionConfig, DatabaseConnector
from .exceptions import (
    ConfigurationError,
    ConnectionError,
    QueryError,
    TransactionError,
)

# Check if wborm is available
try:
    import wborm
    from wborm import generate_model, get_model

    WBORM_AVAILABLE = True
except ImportError:
    WBORM_AVAILABLE = False


class WBORMConnector(DatabaseConnector):
    """
    Database connector implementation using wborm.

    Provides ORM-style access to Informix databases with automatic
    schema introspection and model generation.

    wborm is built on top of wbjdbc, so it inherits JDBC capabilities
    while adding ORM features like query builders and model introspection.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize WBORM connector.

        Args:
            config: Database connection configuration

        Raises:
            ConfigurationError: If wborm is not installed
        """
        super().__init__(config)
        if not WBORM_AVAILABLE:
            raise ConfigurationError("wborm is not installed. Install it with: pip install wborm")

        self._db = None  # wborm connection object

    def connect(self) -> None:
        """Establish database connection.

        Raises:
            ConnectionError: If connection fails
        """
        if self.is_connected():
            return

        try:
            # wborm uses similar connection parameters as wbjdbc
            # It automatically initializes the underlying JDBC connection
            import wbjdbc

            # Create underlying JDBC connection
            # wborm typically wraps wbjdbc connections
            db_type = self.config.extra_params.get("db_type", "informix")
            db_type_code = 1 if db_type == "informix" else 1  # Default to Informix

            jdbc_conn = wbjdbc.connect_to_db(
                db_type=db_type_code,
                host=self.config.host,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                port=self.config.port,
                server=self.config.extra_params.get("server", None),
                debug=self.config.extra_params.get("debug", 0),
            )

            if jdbc_conn is None:
                raise Exception("Failed to create JDBC connection for wborm")

            # Store the connection
            self._connection = jdbc_conn
            self._db = jdbc_conn  # wborm uses this for queries

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to database: {self.config.host}:{self.config.port}",
                driver_error=e,
            )

    def disconnect(self) -> None:
        """Close database connection.

        Raises:
            ConnectionError: If disconnect fails
        """
        try:
            if self._connection:
                self._connection.close()
                self._connection = None
                self._db = None

        except Exception as e:
            raise ConnectionError("Failed to disconnect from database", driver_error=e)

    def is_connected(self) -> bool:
        """Check if currently connected to database.

        Returns:
            True if connected, False otherwise
        """
        return self._connection is not None and self._db is not None

    def _check_connection(self) -> None:
        """Check connection and raise if not connected."""
        if not self.is_connected():
            raise ConnectionError("Not connected to database. Call connect() first.")

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

        try:
            # Use the underlying JDBC connection
            cursor = self._connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rowcount = getattr(cursor, "rowcount", 0)
            cursor.close()

            return rowcount if rowcount >= 0 else 0

        except Exception as e:
            raise QueryError(str(e), query=query, driver_error=e)

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

        try:
            cursor = self._connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Use fetchdh() if available (wbjdbc feature)
            if hasattr(cursor, "fetchdh"):
                results = cursor.fetchdh()
                cursor.close()
                return results

            # Fallback to manual dict conversion
            rows = cursor.fetchall()

            if hasattr(cursor, "description") and cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]
                cursor.close()
                return results

            cursor.close()
            return []

        except Exception as e:
            raise QueryError(str(e), query=query, driver_error=e)

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
            cursor = self._connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            row = cursor.fetchone()

            if row is None:
                cursor.close()
                return None

            if hasattr(cursor, "description") and cursor.description:
                columns = [desc[0] for desc in cursor.description]
                result = dict(zip(columns, row))
                cursor.close()
                return result

            cursor.close()
            return None

        except Exception as e:
            raise QueryError(str(e), query=query, driver_error=e)

    def begin_transaction(self) -> None:
        """Begin a database transaction.

        Note: wborm uses underlying JDBC transaction behavior.

        Raises:
            TransactionError: If transaction cannot be started
            ConnectionError: If not connected
        """
        self._check_connection()

        if self._in_transaction:
            raise TransactionError("Transaction already in progress")

        # Mark transaction state
        # wborm/wbjdbc uses JDBC auto-commit
        self._in_transaction = True

    def commit(self) -> None:
        """Commit the current transaction.

        Note: wborm uses underlying JDBC transaction behavior.

        Raises:
            TransactionError: If commit fails
            ConnectionError: If not connected
        """
        self._check_connection()

        if not self._in_transaction:
            raise TransactionError("No transaction in progress")

        # wborm/wbjdbc auto-commits by default
        self._in_transaction = False

    def rollback(self) -> None:
        """Rollback the current transaction.

        Note: wborm uses underlying JDBC transaction behavior.

        Raises:
            TransactionError: If rollback fails
            ConnectionError: If not connected
        """
        self._check_connection()

        if not self._in_transaction:
            raise TransactionError("No transaction in progress")

        # wborm/wbjdbc auto-commits by default
        self._in_transaction = False

    # ORM-specific methods (optional, can be added in future)

    def generate_model(self, table_name: str) -> Any:
        """Generate ORM model from database table.

        This uses wborm's automatic introspection feature.

        Args:
            table_name: Name of the database table

        Returns:
            Generated model class

        Raises:
            QueryError: If model generation fails
            ConnectionError: If not connected
        """
        self._check_connection()

        if not WBORM_AVAILABLE:
            raise ConfigurationError("wborm is required for model generation")

        try:
            # Use wborm's generate_model function
            model = generate_model(connection=self._connection, table_name=table_name)
            return model

        except Exception as e:
            raise QueryError(f"Failed to generate model for table {table_name}", driver_error=e)

    def get_model(self, table_name: str) -> Any:
        """Get cached ORM model for table.

        Args:
            table_name: Name of the database table

        Returns:
            Cached model class or None

        Raises:
            QueryError: If model retrieval fails
        """
        if not WBORM_AVAILABLE:
            raise ConfigurationError("wborm is required for model access")

        try:
            return get_model(table_name)
        except Exception as e:
            raise QueryError(f"Failed to get model for table {table_name}", driver_error=e)
