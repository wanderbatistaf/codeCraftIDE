"""
Logging infrastructure for database operations.

This module provides structured logging for database connections, queries,
transactions, and error conditions.
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

# Configure logger for database operations
logger = logging.getLogger("fglinterpreter.database")


class DatabaseLogger:
    """
    Structured logger for database operations.

    Provides context-aware logging with query timing, parameter tracking,
    and structured log messages.
    """

    def __init__(self, name: str = "database"):
        """
        Initialize database logger.

        Args:
            name: Logger name (used for hierarchical logging)
        """
        self.logger = logging.getLogger(f"fglinterpreter.{name}")
        self.query_count = 0
        self.error_count = 0

    def connection_opened(
        self, driver: str, host: str, database: str, port: Optional[int] = None
    ) -> None:
        """
        Log successful database connection.

        Args:
            driver: Database driver name
            host: Database host
            database: Database name
            port: Database port
        """
        self.logger.info(
            "Database connection established",
            extra={
                "driver": driver,
                "host": host,
                "database": database,
                "port": port,
                "event": "connection_opened",
            },
        )

    def connection_closed(self, driver: str, database: str) -> None:
        """
        Log database connection closure.

        Args:
            driver: Database driver name
            database: Database name
        """
        self.logger.info(
            "Database connection closed",
            extra={"driver": driver, "database": database, "event": "connection_closed"},
        )

    def connection_failed(self, driver: str, host: str, database: str, error: Exception) -> None:
        """
        Log connection failure.

        Args:
            driver: Database driver name
            host: Database host
            database: Database name
            error: The exception that occurred
        """
        self.error_count += 1
        self.logger.error(
            f"Failed to connect to database: {error}",
            extra={
                "driver": driver,
                "host": host,
                "database": database,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "event": "connection_failed",
            },
            exc_info=True,
        )

    def query_executed(
        self, query: str, params: Optional[tuple] = None, duration: float = 0.0, row_count: int = 0
    ) -> None:
        """
        Log successful query execution.

        Args:
            query: SQL query string
            params: Query parameters
            duration: Execution time in seconds
            row_count: Number of rows affected/returned
        """
        self.query_count += 1

        # Truncate long queries for logging
        display_query = query if len(query) <= 200 else query[:197] + "..."

        log_data = {
            "query": display_query,
            "duration_ms": round(duration * 1000, 2),
            "row_count": row_count,
            "event": "query_executed",
            "query_number": self.query_count,
        }

        if params:
            # Don't log sensitive data in params, just count
            log_data["param_count"] = len(params)

        self.logger.debug(
            f"Query executed in {log_data['duration_ms']}ms: {display_query}", extra=log_data
        )

    def query_failed(
        self, query: str, params: Optional[tuple], error: Exception, duration: float = 0.0
    ) -> None:
        """
        Log query execution failure.

        Args:
            query: SQL query string
            params: Query parameters
            error: The exception that occurred
            duration: Time before failure in seconds
        """
        self.error_count += 1
        self.query_count += 1

        # Truncate long queries
        display_query = query if len(query) <= 200 else query[:197] + "..."

        log_data = {
            "query": display_query,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "duration_ms": round(duration * 1000, 2),
            "event": "query_failed",
            "query_number": self.query_count,
        }

        if params:
            log_data["param_count"] = len(params)

        self.logger.error(
            f"Query failed after {log_data['duration_ms']}ms: {error}",
            extra=log_data,
            exc_info=True,
        )

    def transaction_started(self) -> None:
        """Log transaction start."""
        self.logger.debug("Transaction started", extra={"event": "transaction_started"})

    def transaction_committed(self, duration: float = 0.0) -> None:
        """
        Log transaction commit.

        Args:
            duration: Transaction duration in seconds
        """
        self.logger.debug(
            f"Transaction committed (duration: {round(duration * 1000, 2)}ms)",
            extra={"event": "transaction_committed", "duration_ms": round(duration * 1000, 2)},
        )

    def transaction_rolled_back(self, reason: Optional[str] = None) -> None:
        """
        Log transaction rollback.

        Args:
            reason: Reason for rollback
        """
        log_data = {"event": "transaction_rolled_back"}
        if reason:
            log_data["reason"] = reason

        message = f"Transaction rolled back: {reason}" if reason else "Transaction rolled back"
        self.logger.warning(message, extra=log_data)

    def cursor_declared(self, cursor_name: str, query: str) -> None:
        """
        Log cursor declaration.

        Args:
            cursor_name: Name of the cursor
            query: SELECT query for the cursor
        """
        display_query = query if len(query) <= 200 else query[:197] + "..."
        self.logger.debug(
            f"Cursor '{cursor_name}' declared",
            extra={"cursor_name": cursor_name, "query": display_query, "event": "cursor_declared"},
        )

    def cursor_opened(self, cursor_name: str, row_count: int) -> None:
        """
        Log cursor opening.

        Args:
            cursor_name: Name of the cursor
            row_count: Number of rows in result set
        """
        self.logger.debug(
            f"Cursor '{cursor_name}' opened ({row_count} rows)",
            extra={"cursor_name": cursor_name, "row_count": row_count, "event": "cursor_opened"},
        )

    def cursor_closed(self, cursor_name: str) -> None:
        """
        Log cursor closing.

        Args:
            cursor_name: Name of the cursor
        """
        self.logger.debug(
            f"Cursor '{cursor_name}' closed",
            extra={"cursor_name": cursor_name, "event": "cursor_closed"},
        )

    def retry_attempt(
        self, operation: str, attempt: int, max_attempts: int, error: Exception
    ) -> None:
        """
        Log retry attempt for failed operation.

        Args:
            operation: Name of the operation being retried
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            error: The error that triggered the retry
        """
        self.logger.warning(
            f"Retry {attempt}/{max_attempts} for {operation}: {error}",
            extra={
                "operation": operation,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "event": "retry_attempt",
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Dictionary with query count, error count, etc.
        """
        return {
            "query_count": self.query_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.query_count, 1),
        }

    @contextmanager
    def time_operation(self, operation_name: str):
        """
        Context manager to time an operation.

        Args:
            operation_name: Name of the operation

        Yields:
            Dictionary to store operation results
        """
        start_time = time.time()
        result = {"duration": 0.0}

        try:
            yield result
        finally:
            result["duration"] = time.time() - start_time
            self.logger.debug(
                f"{operation_name} completed in {round(result['duration'] * 1000, 2)}ms",
                extra={
                    "operation": operation_name,
                    "duration_ms": round(result["duration"] * 1000, 2),
                    "event": "operation_timed",
                },
            )


def log_database_operation(operation_name: str):
    """
    Decorator to log database operations with timing.

    Args:
        operation_name: Name of the operation for logging

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            db_logger = DatabaseLogger()
            start_time = time.time()

            try:
                result = func(self, *args, **kwargs)
                duration = time.time() - start_time

                db_logger.logger.debug(
                    f"{operation_name} completed successfully",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration * 1000, 2),
                        "event": "operation_success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                db_logger.logger.error(
                    f"{operation_name} failed: {e}",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration * 1000, 2),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "event": "operation_failed",
                    },
                    exc_info=True,
                )

                raise

        return wrapper

    return decorator


# Global database logger instance
db_logger = DatabaseLogger()


def configure_logging(
    level: int = logging.INFO, format_string: Optional[str] = None, handlers: Optional[list] = None
) -> None:
    """
    Configure database logging.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_string: Custom format string for log messages
        handlers: List of logging handlers to add
    """
    logger = logging.getLogger("fglinterpreter.database")
    logger.setLevel(level)

    # Default format with structured data
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - " "%(message)s [%(filename)s:%(lineno)d]"
        )

    # Add console handler if no handlers specified
    if handlers is None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(format_string)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        for handler in handlers:
            logger.addHandler(handler)

    logger.info("Database logging configured")
