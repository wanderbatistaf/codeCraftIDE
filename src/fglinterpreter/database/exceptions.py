"""
Database-related exceptions for fglInterpreter.

This module defines exceptions that can occur during database operations,
mapping driver-specific errors to interpreter-level exceptions.
"""

from typing import Any, Dict, Optional


class DatabaseError(Exception):
    """Base class for all database-related errors."""

    def __init__(
        self,
        message: str,
        driver_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize database error.

        Args:
            message: Human-readable error message
            driver_error: Original exception from the database driver
            context: Additional context information (host, database, etc.)
        """
        super().__init__(message)
        self.message = message
        self.driver_error = driver_error
        self.context = context or {}

    def __str__(self) -> str:
        parts = [self.message]

        if self.driver_error:
            parts.append(f"Driver error: {type(self.driver_error).__name__}: {self.driver_error}")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "driver_error": str(self.driver_error) if self.driver_error else None,
            "driver_error_type": type(self.driver_error).__name__ if self.driver_error else None,
            "context": self.context,
        }


class ConnectionError(DatabaseError):
    """Error establishing or maintaining database connection."""

    pass


class TransactionError(DatabaseError):
    """Error during transaction management (begin, commit, rollback)."""

    pass


class QueryError(DatabaseError):
    """Error executing a database query."""

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        params: Optional[tuple] = None,
        driver_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize query error.

        Args:
            message: Human-readable error message
            query: The SQL query that caused the error
            params: Query parameters
            driver_error: Original exception from the database driver
            context: Additional context information
        """
        super().__init__(message, driver_error, context)
        self.query = query
        self.params = params

    def __str__(self) -> str:
        base_msg = super().__str__()
        parts = [base_msg]

        if self.query:
            # Truncate long queries
            display_query = self.query if len(self.query) <= 200 else self.query[:197] + "..."
            parts.append(f"Query: {display_query}")

        if self.params:
            # Don't expose sensitive parameter values, just indicate presence
            parts.append(f"Parameters: {len(self.params)} parameter(s) provided")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        data = super().to_dict()
        data["query"] = self.query
        data["param_count"] = len(self.params) if self.params else 0
        return data


class DataError(DatabaseError):
    """Error related to data format or type conversion."""

    pass


class IntegrityError(DatabaseError):
    """Database integrity constraint violation."""

    pass


class OperationalError(DatabaseError):
    """Database operational error (e.g., server down, connection lost)."""

    pass


class ProgrammingError(DatabaseError):
    """Programming error (e.g., table not found, syntax error)."""

    pass


class ConfigurationError(DatabaseError):
    """Database configuration error."""

    pass


class CursorError(DatabaseError):
    """Error related to cursor operations."""

    def __init__(
        self,
        message: str,
        cursor_name: Optional[str] = None,
        driver_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize cursor error.

        Args:
            message: Human-readable error message
            cursor_name: Name of the cursor
            driver_error: Original exception from the database driver
            context: Additional context information
        """
        super().__init__(message, driver_error, context)
        self.cursor_name = cursor_name

    def __str__(self) -> str:
        if self.cursor_name:
            return f"Cursor '{self.cursor_name}': {super().__str__()}"
        return super().__str__()


class TimeoutError(DatabaseError):
    """Database operation timeout."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        driver_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize timeout error.

        Args:
            message: Human-readable error message
            timeout_seconds: Timeout duration in seconds
            driver_error: Original exception from the database driver
            context: Additional context information
        """
        super().__init__(message, driver_error, context)
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        if self.timeout_seconds:
            return f"{super().__str__()} (timeout: {self.timeout_seconds}s)"
        return super().__str__()


class RetryableError(DatabaseError):
    """
    Error that can be retried.

    This is used to indicate transient failures that may succeed on retry.
    """

    def __init__(
        self,
        message: str,
        original_error: Exception,
        retry_count: int = 0,
        max_retries: int = 3,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize retryable error.

        Args:
            message: Human-readable error message
            original_error: The original exception
            retry_count: Number of retries attempted
            max_retries: Maximum number of retries allowed
            context: Additional context information
        """
        super().__init__(message, original_error, context)
        self.original_error = original_error
        self.retry_count = retry_count
        self.max_retries = max_retries

    def __str__(self) -> str:
        return f"{super().__str__()} " f"(retry {self.retry_count}/{self.max_retries})"

    def can_retry(self) -> bool:
        """Check if another retry is allowed."""
        return self.retry_count < self.max_retries
