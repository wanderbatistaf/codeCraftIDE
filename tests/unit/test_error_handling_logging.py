"""
Unit tests for database error handling and logging.

Tests the logging infrastructure and enhanced exception handling.
"""

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock database modules before importing
# Only create mocks if they don't already exist (for test isolation)
if "wbjdbc" not in sys.modules:
    sys.modules["wbjdbc"] = MagicMock()
if "wborm" not in sys.modules:
    sys.modules["wborm"] = MagicMock()

from src.fglinterpreter.database.exceptions import (
    ConnectionError,
    CursorError,
    DatabaseError,
    QueryError,
    RetryableError,
    TimeoutError,
)
from src.fglinterpreter.database.logging import DatabaseLogger, configure_logging


@pytest.mark.unit
class TestDatabaseExceptions:
    """Tests for enhanced database exceptions."""

    def test_database_error_basic(self):
        """Test basic database error."""
        error = DatabaseError("Test error")
        assert error.message == "Test error"
        assert error.driver_error is None
        assert error.context == {}
        assert str(error) == "Test error"

    def test_database_error_with_driver_error(self):
        """Test database error with driver exception."""
        driver_error = Exception("Original error")
        error = DatabaseError("Test error", driver_error=driver_error)

        assert error.driver_error is driver_error
        assert "Driver error" in str(error)
        assert "Original error" in str(error)

    def test_database_error_with_context(self):
        """Test database error with context information."""
        context = {"host": "localhost", "database": "testdb", "port": 9088}
        error = DatabaseError("Test error", context=context)

        assert error.context == context
        assert "host=localhost" in str(error)
        assert "database=testdb" in str(error)

    def test_database_error_to_dict(self):
        """Test database error serialization to dictionary."""
        driver_error = ValueError("Invalid value")
        context = {"operation": "connect"}

        error = DatabaseError("Test error", driver_error=driver_error, context=context)
        error_dict = error.to_dict()

        assert error_dict["error_type"] == "DatabaseError"
        assert error_dict["message"] == "Test error"
        assert error_dict["driver_error_type"] == "ValueError"
        assert error_dict["context"] == context

    def test_query_error_with_query(self):
        """Test query error with SQL query."""
        error = QueryError("Query failed", query="SELECT * FROM users WHERE id = ?")

        assert error.query is not None
        assert "SELECT * FROM users" in str(error)

    def test_query_error_with_params(self):
        """Test query error with parameters."""
        error = QueryError("Query failed", query="SELECT * FROM users WHERE id = ?", params=(42,))

        assert error.params == (42,)
        # Params should not be exposed in string, just count
        error_str = str(error)
        assert "1 parameter(s)" in error_str
        assert "42" not in error_str  # Actual value should not be exposed

    def test_query_error_truncates_long_query(self):
        """Test that long queries are truncated in error messages."""
        long_query = "SELECT " + ", ".join([f"col{i}" for i in range(100)]) + " FROM table"
        error = QueryError("Query failed", query=long_query)

        error_str = str(error)
        assert len(error_str) < len(long_query) + 100  # Should be truncated
        assert "..." in error_str

    def test_cursor_error_with_cursor_name(self):
        """Test cursor error with cursor name."""
        error = CursorError("Cursor operation failed", cursor_name="my_cursor")

        assert error.cursor_name == "my_cursor"
        assert "Cursor 'my_cursor'" in str(error)

    def test_timeout_error_with_timeout(self):
        """Test timeout error with timeout duration."""
        error = TimeoutError("Operation timed out", timeout_seconds=30.0)

        assert error.timeout_seconds == 30.0
        assert "timeout: 30.0s" in str(error)

    def test_retryable_error_can_retry(self):
        """Test retryable error retry logic."""
        original = Exception("Transient failure")
        error = RetryableError(
            "Operation failed", original_error=original, retry_count=1, max_retries=3
        )

        assert error.can_retry() is True
        assert "retry 1/3" in str(error)

    def test_retryable_error_max_retries_exceeded(self):
        """Test retryable error when max retries reached."""
        original = Exception("Transient failure")
        error = RetryableError(
            "Operation failed", original_error=original, retry_count=3, max_retries=3
        )

        assert error.can_retry() is False


@pytest.mark.unit
class TestDatabaseLogger:
    """Tests for database logging infrastructure."""

    @pytest.fixture
    def logger(self):
        """Create a database logger for testing."""
        return DatabaseLogger("test")

    def test_logger_initialization(self, logger):
        """Test logger initialization."""
        assert logger.query_count == 0
        assert logger.error_count == 0
        assert logger.logger.name == "fglinterpreter.test"

    def test_connection_opened_logging(self, logger):
        """Test connection opened log."""
        with patch.object(logger.logger, "info") as mock_info:
            logger.connection_opened(
                driver="wbjdbc", host="localhost", database="testdb", port=9088
            )

            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "connection established" in call_args[0][0].lower()
            assert call_args[1]["extra"]["driver"] == "wbjdbc"
            assert call_args[1]["extra"]["host"] == "localhost"

    def test_connection_failed_logging(self, logger):
        """Test connection failure log."""
        error = Exception("Connection refused")

        with patch.object(logger.logger, "error") as mock_error:
            logger.connection_failed(
                driver="wbjdbc", host="localhost", database="testdb", error=error
            )

            mock_error.assert_called_once()
            assert logger.error_count == 1

    def test_query_executed_logging(self, logger):
        """Test successful query logging."""
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.query_executed(
                query="SELECT * FROM users", params=(42,), duration=0.05, row_count=10
            )

            mock_debug.assert_called_once()
            assert logger.query_count == 1

            call_args = mock_debug.call_args
            extra = call_args[1]["extra"]
            assert extra["duration_ms"] == 50.0  # 0.05s = 50ms
            assert extra["row_count"] == 10
            assert extra["param_count"] == 1

    def test_query_failed_logging(self, logger):
        """Test failed query logging."""
        error = Exception("Syntax error")

        with patch.object(logger.logger, "error") as mock_error:
            logger.query_failed(
                query="SELECT * FROM invalid_table", params=None, error=error, duration=0.01
            )

            mock_error.assert_called_once()
            assert logger.error_count == 1
            assert logger.query_count == 1

    def test_query_logging_truncates_long_queries(self, logger):
        """Test that long queries are truncated in logs."""
        long_query = "SELECT " + ", ".join([f"column_{i}" for i in range(100)]) + " FROM table"

        with patch.object(logger.logger, "debug") as mock_debug:
            logger.query_executed(query=long_query, params=None, duration=0.01, row_count=0)

            call_args = mock_debug.call_args
            logged_query = call_args[1]["extra"]["query"]
            assert len(logged_query) <= 200
            if len(long_query) > 200:
                assert "..." in logged_query

    def test_transaction_started_logging(self, logger):
        """Test transaction start logging."""
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.transaction_started()

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert call_args[1]["extra"]["event"] == "transaction_started"

    def test_transaction_committed_logging(self, logger):
        """Test transaction commit logging."""
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.transaction_committed(duration=0.5)

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert call_args[1]["extra"]["duration_ms"] == 500.0

    def test_transaction_rolled_back_logging(self, logger):
        """Test transaction rollback logging."""
        with patch.object(logger.logger, "warning") as mock_warning:
            logger.transaction_rolled_back(reason="Data validation failed")

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "Data validation failed" in call_args[0][0]
            assert call_args[1]["extra"]["reason"] == "Data validation failed"

    def test_cursor_declared_logging(self, logger):
        """Test cursor declaration logging."""
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.cursor_declared(cursor_name="user_cursor", query="SELECT id, name FROM users")

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "user_cursor" in call_args[0][0]
            assert call_args[1]["extra"]["cursor_name"] == "user_cursor"

    def test_cursor_opened_logging(self, logger):
        """Test cursor opened logging."""
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.cursor_opened(cursor_name="user_cursor", row_count=100)

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "100 rows" in call_args[0][0]

    def test_retry_attempt_logging(self, logger):
        """Test retry attempt logging."""
        error = Exception("Temporary failure")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.retry_attempt(operation="connect", attempt=2, max_attempts=5, error=error)

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "Retry 2/5" in call_args[0][0]
            assert call_args[1]["extra"]["attempt"] == 2
            assert call_args[1]["extra"]["max_attempts"] == 5

    def test_get_stats(self, logger):
        """Test getting logger statistics."""
        # Simulate some operations
        logger.query_count = 10
        logger.error_count = 2

        stats = logger.get_stats()

        assert stats["query_count"] == 10
        assert stats["error_count"] == 2
        assert stats["error_rate"] == 0.2  # 2/10

    def test_get_stats_no_queries(self, logger):
        """Test getting stats with no queries."""
        stats = logger.get_stats()

        assert stats["query_count"] == 0
        assert stats["error_count"] == 0
        assert stats["error_rate"] == 0.0

    def test_time_operation_context_manager(self, logger):
        """Test operation timing context manager."""
        with patch.object(logger.logger, "debug") as mock_debug:
            import time

            with logger.time_operation("test_operation") as result:
                time.sleep(0.01)  # Simulate some work

            assert result["duration"] >= 0.01
            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "test_operation" in call_args[0][0]


@pytest.mark.unit
class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_default(self):
        """Test default logging configuration."""
        configure_logging()

        logger = logging.getLogger("fglinterpreter.database")
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_configure_logging_debug_level(self):
        """Test configuring logging at DEBUG level."""
        configure_logging(level=logging.DEBUG)

        logger = logging.getLogger("fglinterpreter.database")
        assert logger.level == logging.DEBUG

    def test_configure_logging_custom_format(self):
        """Test configuring logging with custom format."""
        custom_format = "%(levelname)s - %(message)s"

        configure_logging(format_string=custom_format)

        logger = logging.getLogger("fglinterpreter.database")
        # Logger should be configured without errors
        assert logger is not None

    def test_configure_logging_custom_handlers(self):
        """Test configuring logging with custom handlers."""
        handler = logging.StreamHandler()
        configure_logging(handlers=[handler])

        logger = logging.getLogger("fglinterpreter.database")
        assert handler in logger.handlers


@pytest.mark.unit
class TestExceptionMapping:
    """Tests for exception mapping and error context."""

    def test_connection_error_context(self):
        """Test connection error with context."""
        error = ConnectionError(
            "Failed to connect", context={"host": "localhost", "port": 9088, "database": "testdb"}
        )

        error_dict = error.to_dict()
        assert error_dict["context"]["host"] == "localhost"
        assert error_dict["context"]["port"] == 9088

    def test_query_error_context(self):
        """Test query error with full context."""
        error = QueryError(
            "Query execution failed",
            query="SELECT * FROM users",
            params=(1, "test"),
            context={"table": "users", "operation": "select"},
        )

        error_dict = error.to_dict()
        assert error_dict["query"] == "SELECT * FROM users"
        assert error_dict["param_count"] == 2
        assert error_dict["context"]["table"] == "users"
