"""
Runtime exceptions for the 4GL interpreter.

This module defines exceptions that can be raised during program execution.
"""

from typing import Optional

from ..error_hints import enhance_error_message
from ..parser.ast_nodes import ASTNode


class RuntimeError(Exception):
    """Base exception for all runtime errors."""

    def __init__(self, message: str, node: Optional[ASTNode] = None) -> None:
        """
        Initialize a runtime error.

        Args:
            message: Description of the error
            node: The AST node where the error occurred (optional)
        """
        self.message = message
        self.node = node
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format the error message with context."""
        if self.node:
            error_msg = (
                f"Runtime error at line {self.node.line}, column {self.node.column}: {self.message}"
            )
        else:
            error_msg = f"Runtime error: {self.message}"

        # Enhance error message with context-aware hints
        context = {}
        if self.node:
            context["line"] = self.node.line
            context["column"] = self.node.column

        return enhance_error_message(Exception(error_msg), context)


class UndefinedVariableError(RuntimeError):
    """Raised when accessing an undefined variable."""

    def __init__(self, variable_name: str, node: Optional[ASTNode] = None) -> None:
        message = f"Undefined variable: {variable_name}"
        self.variable_name = variable_name  # Store for context
        super().__init__(message, node)

    def format_error(self) -> str:
        """Override to provide variable-specific context."""
        if self.node:
            error_msg = (
                f"Runtime error at line {self.node.line}, column {self.node.column}: {self.message}"
            )
        else:
            error_msg = f"Runtime error: {self.message}"

        # Enhance with variable-specific context
        context = {
            "variable": self.variable_name,
            "available_variables": [],  # Could be populated from execution context in future
        }
        if self.node:
            context["line"] = self.node.line
            context["column"] = self.node.column

        return enhance_error_message(Exception(error_msg), context)


class TypeMismatchError(RuntimeError):
    """Raised when there's a type mismatch in an operation."""

    def __init__(self, message: str, node: Optional[ASTNode] = None) -> None:
        super().__init__(f"Type mismatch: {message}", node)


class DivisionByZeroError(RuntimeError):
    """Raised when dividing by zero."""

    def __init__(self, node: Optional[ASTNode] = None) -> None:
        super().__init__("Division by zero", node)


class InvalidOperationError(RuntimeError):
    """Raised when an invalid operation is performed."""

    def __init__(self, message: str, node: Optional[ASTNode] = None) -> None:
        super().__init__(f"Invalid operation: {message}", node)


class FunctionNotFoundError(RuntimeError):
    """Raised when calling an undefined function."""

    def __init__(self, function_name: str, node: Optional[ASTNode] = None) -> None:
        message = f"Function not found: {function_name}"
        super().__init__(message, node)


class ReturnException(Exception):
    """
    Exception used for RETURN statement control flow.

    Not a real error - used internally to implement return statements.
    """

    def __init__(self, value: any = None) -> None:
        self.value = value
        super().__init__()


class ExitLoopException(Exception):
    """
    Exception used for EXIT statement control flow.

    Not a real error - used internally to implement loop exits.
    """

    pass


class ContinueLoopException(Exception):
    """
    Exception used for CONTINUE statement control flow.

    Not a real error - used internally to implement loop continues.
    """

    pass
