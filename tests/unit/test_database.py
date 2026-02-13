"""
Unit tests for the Database module.
"""

import sys
from unittest.mock import MagicMock

import pytest

# Mock wbjdbc and wborm before importing fglinterpreter.database
# Only create mocks if they don't already exist (for test isolation)
if "wbjdbc" not in sys.modules:
    sys.modules["wbjdbc"] = MagicMock()
if "wborm" not in sys.modules:
    sys.modules["wborm"] = MagicMock()

from fglinterpreter.database import (
    ConnectionConfig,
    ConnectionError,
    WBJDBCConnector,
    WBORMConnector,
    create_connection_pool,
    create_connector,
)


@pytest.fixture
def db_config():
    """Create a test database configuration."""
    return ConnectionConfig(
        host="localhost",
        port=9088,
        database="testdb",
        username="testuser",
        password="testpass",
        driver="wbjdbc",
        pool_size=3,
        pool_timeout=5,
    )


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test to ensure test isolation."""
    # Reset the wbjdbc mock
    sys.modules["wbjdbc"].reset_mock()
    sys.modules["wborm"].reset_mock()
    yield


@pytest.fixture
def mock_wbjdbc():
    """Create a mock wbjdbc module."""
    return sys.modules["wbjdbc"]


@pytest.fixture
def mock_wborm():
    """Create a mock wborm module."""
    return sys.modules["wborm"]


@pytest.mark.unit
class TestConnectionConfig:
    """Tests for ConnectionConfig class."""

    def test_config_creation(self):
        """Test creating a connection config."""
        config = ConnectionConfig(
            host="localhost", port=9088, database="testdb", username="user", password="pass"
        )

        assert config.host == "localhost"
        assert config.port == 9088
        assert config.database == "testdb"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.driver == "wbjdbc"  # default
        assert config.pool_size == 5  # default
        assert config.extra_params == {}

    def test_config_with_custom_params(self):
        """Test config with custom parameters."""
        config = ConnectionConfig(
            host="localhost",
            port=9088,
            database="testdb",
            username="user",
            password="pass",
            driver="wborm",
            pool_size=10,
            extra_params={"ssl": True},
        )

        assert config.driver == "wborm"
        assert config.pool_size == 10
        assert config.extra_params == {"ssl": True}


@pytest.mark.unit
class TestWBJDBCConnector:
    """Tests for WBJDBCConnector class."""

    def test_connect_success(self, mock_wbjdbc, db_config):
        """Test successful database connection."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Create connector and connect
        connector = WBJDBCConnector(db_config)
        connector.connect()

        # Verify
        assert connector.is_connected()
        mock_wbjdbc.connect_to_db.assert_called_once()
        mock_connection.cursor.assert_called_once()

    def test_connect_failure(self, mock_wbjdbc, db_config):
        """Test connection failure."""
        # Setup mock to raise exception
        mock_wbjdbc.connect_to_db.side_effect = Exception("Connection refused")

        # Create connector and attempt connection
        connector = WBJDBCConnector(db_config)

        with pytest.raises(ConnectionError) as exc_info:
            connector.connect()

        assert "Failed to connect" in str(exc_info.value)
        assert not connector.is_connected()

        # Reset side effect
        mock_wbjdbc.connect_to_db.side_effect = None

    def test_disconnect(self, mock_wbjdbc, db_config):
        """Test disconnecting from database."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Connect and disconnect
        connector = WBJDBCConnector(db_config)
        connector.connect()
        connector.disconnect()

        # Verify
        assert not connector.is_connected()
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_execute_query(self, mock_wbjdbc, db_config):
        """Test executing a query."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        # Use PropertyMock to properly mock rowcount attribute
        type(mock_cursor).rowcount = 1
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute query
        connector = WBJDBCConnector(db_config)
        connector.connect()
        rows_affected = connector.execute("INSERT INTO table VALUES (?)", (42,))

        # Verify
        assert rows_affected == 1
        mock_cursor.execute.assert_called_once_with("INSERT INTO table VALUES (?)", (42,))

    def test_query_with_results(self, mock_wbjdbc, db_config):
        """Test querying with results."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchdh.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute query
        connector = WBJDBCConnector(db_config)
        connector.connect()
        results = connector.query("SELECT id, name FROM users")

        # Verify
        assert len(results) == 2
        assert results[0] == {"id": 1, "name": "Alice"}
        assert results[1] == {"id": 2, "name": "Bob"}

    def test_query_one(self, mock_wbjdbc, db_config):
        """Test querying for single result."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "Alice")
        mock_cursor.description = [("id",), ("name",)]
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute query
        connector = WBJDBCConnector(db_config)
        connector.connect()
        result = connector.query_one("SELECT id, name FROM users WHERE id = ?", (1,))

        # Verify
        assert result == {"id": 1, "name": "Alice"}

    def test_query_one_no_results(self, mock_wbjdbc, db_config):
        """Test querying when no results."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute query
        connector = WBJDBCConnector(db_config)
        connector.connect()
        result = connector.query_one("SELECT * FROM users WHERE id = ?", (999,))

        # Verify
        assert result is None

    def test_transaction_commit(self, mock_wbjdbc, db_config):
        """Test transaction commit."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        type(mock_cursor).rowcount = 1
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute transaction
        connector = WBJDBCConnector(db_config)
        connector.connect()
        connector.begin_transaction()
        connector.execute("INSERT INTO table VALUES (?)", (42,))
        connector.commit()

        # Verify
        assert not connector._in_transaction

    def test_transaction_rollback(self, mock_wbjdbc, db_config):
        """Test transaction rollback."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        type(mock_cursor).rowcount = 1
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute transaction
        connector = WBJDBCConnector(db_config)
        connector.connect()
        connector.begin_transaction()
        connector.execute("INSERT INTO table VALUES (?)", (42,))
        connector.rollback()

        # Verify
        assert not connector._in_transaction

    def test_transaction_context_manager(self, mock_wbjdbc, db_config):
        """Test transaction context manager."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        type(mock_cursor).rowcount = 1
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute transaction
        connector = WBJDBCConnector(db_config)
        connector.connect()

        with connector.transaction():
            connector.execute("INSERT INTO table VALUES (?)", (42,))

        # Verify transaction completed
        assert not connector._in_transaction

    def test_transaction_context_manager_rollback_on_error(self, mock_wbjdbc, db_config):
        """Test transaction context manager rolls back on error."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query error")
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute transaction with error
        connector = WBJDBCConnector(db_config)
        connector.connect()

        with pytest.raises(Exception):
            with connector.transaction():
                connector.execute("BAD SQL")

        # Verify rollback was called (transaction state reset)
        assert not connector._in_transaction

    def test_execute_without_connection(self, db_config):
        """Test executing query without connection raises error."""
        connector = WBJDBCConnector(db_config)
        # Don't connect

        with pytest.raises(ConnectionError) as exc_info:
            connector.execute("SELECT * FROM table")

        assert "Not connected" in str(exc_info.value)

    def test_context_manager(self, mock_wbjdbc, db_config):
        """Test using connector as context manager."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_wbjdbc.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Use as context manager
        connector = WBJDBCConnector(db_config)

        with connector:
            assert connector.is_connected()

        # Verify disconnect was called
        assert not connector.is_connected()


@pytest.mark.unit
class TestWBORMConnector:
    """Tests for WBORMConnector class."""

    @pytest.mark.skip(
        reason="WBORM tests require actual database connection or more complex mocking"
    )
    def test_connect_success(self, mock_wborm, mock_wbjdbc, db_config):
        """Test successful database connection."""
        # Setup mocks - wborm uses wbjdbc underneath
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_wbjdbc.connect_to_db.reset_mock()  # Reset before test
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Create connector and connect
        db_config.driver = "wborm"
        connector = WBORMConnector(db_config)
        connector.connect()

        # Verify
        assert connector.is_connected()
        mock_wbjdbc.connect_to_db.assert_called_once()

    @pytest.mark.skip(
        reason="WBORM tests require actual database connection or more complex mocking"
    )
    def test_execute_query(self, mock_wborm, mock_wbjdbc, db_config):
        """Test executing a query."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        type(mock_cursor).rowcount = 1
        mock_wbjdbc.connect_to_db.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Execute query
        db_config.driver = "wborm"
        connector = WBORMConnector(db_config)
        connector.connect()
        rows_affected = connector.execute("INSERT INTO table VALUES (?)", (42,))

        # Verify
        assert rows_affected == 1
        mock_cursor.execute.assert_called()


@pytest.mark.unit
class TestConnectionPool:
    """Tests for connection pooling."""

    def test_create_pool(self, mock_wbjdbc, db_config):
        """Test creating a connection pool."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_wbjdbc.connect_to_db.return_value = mock_connection

        # Create pool
        pool = create_connection_pool(db_config)

        # Verify pool was created
        assert pool is not None
        assert pool.config == db_config

    def test_get_connection_from_pool(self, mock_wbjdbc, db_config):
        """Test getting connection from pool."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_wbjdbc.connect_to_db.return_value = mock_connection

        # Create pool and get connection
        pool = create_connection_pool(db_config)
        conn = pool.get_connection()

        # Verify
        assert conn is not None
        assert isinstance(conn, WBJDBCConnector)

    def test_release_connection_to_pool(self, mock_wbjdbc, db_config):
        """Test releasing connection back to pool."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_wbjdbc.connect_to_db.return_value = mock_connection

        # Create pool, get and release connection
        pool = create_connection_pool(db_config)
        conn = pool.get_connection()
        pool.release_connection(conn)

        # Should be able to get it again
        conn2 = pool.get_connection()
        assert conn2 is not None

    def test_pool_context_manager(self, mock_wbjdbc, db_config):
        """Test pool connection context manager."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_wbjdbc.connect_to_db.return_value = mock_connection

        # Create pool and use context manager
        pool = create_connection_pool(db_config)

        with pool.connection() as conn:
            assert conn is not None
            assert isinstance(conn, WBJDBCConnector)

        # Connection should be released after context


@pytest.mark.unit
class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_connector_wbjdbc(self, mock_wbjdbc, db_config):
        """Test creating wbjdbc connector."""
        connector = create_connector(db_config)
        assert isinstance(connector, WBJDBCConnector)

    def test_create_connector_wborm(self, mock_wborm, db_config):
        """Test creating wborm connector."""
        db_config.driver = "wborm"
        connector = create_connector(db_config)
        assert isinstance(connector, WBORMConnector)

    def test_create_connector_invalid_driver(self, db_config):
        """Test creating connector with invalid driver."""
        from fglinterpreter.database import ConfigurationError

        db_config.driver = "invalid"

        with pytest.raises(ConfigurationError) as exc_info:
            create_connector(db_config)

        assert "Unknown driver" in str(exc_info.value)
