"""
Connection pooling for database connectors.

This module provides connection pool implementations for efficient
connection reuse and resource management.
"""

import threading
from queue import Empty, Queue
from typing import Dict, Type

from .connector import ConnectionConfig, ConnectionPool, DatabaseConnector
from .exceptions import ConnectionError
from .wbjdbc_adapter import WBJDBCConnector
from .wborm_adapter import WBORMConnector


class SimpleConnectionPool(ConnectionPool):
    """
    Simple connection pool implementation.

    Manages a pool of database connections with basic resource management.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize connection pool.

        Args:
            config: Database connection configuration
        """
        super().__init__(config)
        self._available: Queue = Queue(maxsize=config.pool_size)
        self._all_connections: Dict[int, DatabaseConnector] = {}
        self._lock = threading.Lock()
        self._closed = False

        # Map driver names to connector classes
        self._connector_classes: Dict[str, Type[DatabaseConnector]] = {
            "wbjdbc": WBJDBCConnector,
            "wborm": WBORMConnector,
        }

        # Create initial connections
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Create initial pool connections."""
        connector_class = self._connector_classes.get(self.config.driver)
        if not connector_class:
            raise ConnectionError(
                f"Unknown driver: {self.config.driver}. "
                f"Supported drivers: {list(self._connector_classes.keys())}"
            )

        for _ in range(self.config.pool_size):
            try:
                conn = connector_class(self.config)
                conn.connect()
                conn_id = id(conn)
                self._all_connections[conn_id] = conn
                self._available.put(conn)
            except Exception as e:
                # Log error but continue creating other connections
                print(f"Warning: Failed to create pool connection: {e}")

    def get_connection(self) -> DatabaseConnector:
        """Get a connection from the pool.

        Returns:
            A database connector instance

        Raises:
            ConnectionError: If no connections available within timeout
        """
        if self._closed:
            raise ConnectionError("Connection pool is closed")

        try:
            # Try to get a connection from the pool
            conn = self._available.get(timeout=self.config.pool_timeout)

            # Check if connection is still valid
            if not conn.is_connected():
                # Reconnect if necessary
                try:
                    conn.connect()
                except Exception:
                    # Remove invalid connection and create a new one
                    self._all_connections.pop(id(conn), None)
                    conn = self._create_new_connection()

            return conn

        except Empty:
            raise ConnectionError(
                f"No connections available within {self.config.pool_timeout} seconds"
            )

    def _create_new_connection(self) -> DatabaseConnector:
        """Create a new connection when existing one fails.

        Returns:
            A new database connector instance

        Raises:
            ConnectionError: If connection creation fails
        """
        connector_class = self._connector_classes.get(self.config.driver)
        if not connector_class:
            raise ConnectionError(f"Unknown driver: {self.config.driver}")

        conn = connector_class(self.config)
        conn.connect()
        conn_id = id(conn)

        with self._lock:
            self._all_connections[conn_id] = conn

        return conn

    def release_connection(self, connector: DatabaseConnector) -> None:
        """Release a connection back to the pool.

        Args:
            connector: The connector to release

        Raises:
            ValueError: If connector not from this pool
        """
        if self._closed:
            # If pool is closed, just disconnect
            try:
                connector.disconnect()
            except Exception:
                pass
            return

        conn_id = id(connector)
        if conn_id not in self._all_connections:
            raise ValueError("Connector not from this pool")

        # Check if connection is still valid
        if connector.is_connected():
            self._available.put(connector)
        else:
            # Remove invalid connection
            with self._lock:
                self._all_connections.pop(conn_id, None)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            if self._closed:
                return

            self._closed = True

            # Close all connections
            for conn in self._all_connections.values():
                try:
                    if conn.is_connected():
                        conn.disconnect()
                except Exception as e:
                    print(f"Warning: Failed to close connection: {e}")

            self._all_connections.clear()

            # Clear the queue
            while not self._available.empty():
                try:
                    self._available.get_nowait()
                except Empty:
                    break

    def __del__(self):
        """Destructor - close all connections."""
        self.close_all()


def create_connection_pool(config: ConnectionConfig) -> ConnectionPool:
    """Factory function to create a connection pool.

    Args:
        config: Database connection configuration

    Returns:
        A connection pool instance

    Raises:
        ConnectionError: If pool creation fails
    """
    return SimpleConnectionPool(config)
