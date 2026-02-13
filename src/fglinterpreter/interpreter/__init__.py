"""
Interpreter and execution engine for Informix 4GL.

This module provides:
- Execution engine (Interpreter class)
- Variable scope management (ExecutionContext, Scope)
- Runtime error handling
- Control flow execution
"""

from .context import ExecutionContext, Scope
from .exceptions import (
    ContinueLoopException,
    DivisionByZeroError,
    ExitLoopException,
    FunctionNotFoundError,
    InvalidOperationError,
    ReturnException,
    RuntimeError,
    TypeMismatchError,
    UndefinedVariableError,
)
from .interpreter import Interpreter, interpret_source

__all__ = [
    # Main classes
    "Interpreter",
    "interpret_source",
    "ExecutionContext",
    "Scope",
    # Exceptions
    "RuntimeError",
    "UndefinedVariableError",
    "TypeMismatchError",
    "DivisionByZeroError",
    "InvalidOperationError",
    "FunctionNotFoundError",
    "ReturnException",
    "ExitLoopException",
    "ContinueLoopException",
]
