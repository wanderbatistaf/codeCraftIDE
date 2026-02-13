"""
Execution context and scope management for the interpreter.

This module provides the ExecutionContext class for managing variables,
functions, and scopes during program execution.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..parser.ast_nodes import FunctionDef
from .exceptions import UndefinedVariableError

if TYPE_CHECKING:
    from ..database.connector import DatabaseConnector
    from ..profiler import ExecutionProfiler


class Scope:
    """
    Represents a single scope (e.g., function scope, block scope).

    Scopes are organized in a stack, with inner scopes able to access
    variables from outer scopes.
    """

    def __init__(self, parent: Optional["Scope"] = None) -> None:
        """
        Initialize a scope.

        Args:
            parent: The parent scope (None for global scope)
        """
        self.parent = parent
        self.variables: Dict[str, Any] = {}

    def define(self, name: str, value: Any = None) -> None:
        """
        Define a new variable in this scope.

        Args:
            name: Variable name
            value: Initial value (default None)
        """
        self.variables[name] = value

    def get(self, name: str) -> Any:
        """
        Get a variable's value from this scope or parent scopes.

        Args:
            name: Variable name

        Returns:
            Variable value

        Raises:
            UndefinedVariableError: If variable not found in any scope
        """
        if name in self.variables:
            return self.variables[name]

        if self.parent:
            return self.parent.get(name)

        raise UndefinedVariableError(name)

    def set(self, name: str, value: Any) -> None:
        """
        Set a variable's value in the scope where it's defined.

        Args:
            name: Variable name
            value: New value

        Raises:
            UndefinedVariableError: If variable not found in any scope
        """
        if name in self.variables:
            self.variables[name] = value
            return

        if self.parent:
            self.parent.set(name, value)
            return

        # If variable doesn't exist, create it in current scope
        # (4GL behavior - variables can be implicitly created)
        self.variables[name] = value

    def exists(self, name: str) -> bool:
        """
        Check if a variable exists in this scope or parent scopes.

        Args:
            name: Variable name

        Returns:
            True if variable exists
        """
        if name in self.variables:
            return True

        if self.parent:
            return self.parent.exists(name)

        return False


class ExecutionContext:
    """
    Manages the execution environment for the interpreter.

    Maintains variable scopes, function definitions, output, and database state.
    """

    def __init__(self) -> None:
        """Initialize the execution context."""
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.functions: Dict[str, FunctionDef] = {}
        self.output: List[str] = []
        self.database_connector: Optional[DatabaseConnector] = None
        self.cursors: Dict[str, Any] = {}  # cursor_name -> cursor object
        self.profiler: Optional[ExecutionProfiler] = None

        # SQLCA (SQL Communication Area) structure
        self.sqlca: Dict[str, Any] = {
            "sqlcode": 0,  # SQL return code (0=success, negative=error, 100=not found)
            "sqlerrd": [0, 0, 0, 0, 0, 0],  # Error/diagnostic data (sqlerrd[1] = row count)
            "sqlerrm": "",  # Error message
            "sqlerrp": "",  # Error procedure
            "sqlwarn": [" "] * 8,  # Warning flags
        }

    def push_scope(self) -> None:
        """Push a new scope onto the scope stack."""
        self.current_scope = Scope(parent=self.current_scope)

    def pop_scope(self) -> None:
        """Pop the current scope from the scope stack."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define_variable(self, name: str, value: Any = None) -> None:
        """
        Define a variable in the current scope.

        Args:
            name: Variable name
            value: Initial value
        """
        self.current_scope.define(name, value)

    def get_variable(self, name: str) -> Any:
        """
        Get a variable's value.

        Args:
            name: Variable name

        Returns:
            Variable value

        Raises:
            UndefinedVariableError: If variable not defined
        """
        return self.current_scope.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable's value.

        Args:
            name: Variable name
            value: New value
        """
        self.current_scope.set(name, value)

    def variable_exists(self, name: str) -> bool:
        """
        Check if a variable exists.

        Args:
            name: Variable name

        Returns:
            True if variable exists
        """
        return self.current_scope.exists(name)

    def define_function(self, name: str, func_def: FunctionDef) -> None:
        """
        Define a function.

        Args:
            name: Function name
            func_def: Function definition AST node
        """
        self.functions[name] = func_def

    def get_function(self, name: str) -> Optional[FunctionDef]:
        """
        Get a function definition.

        Args:
            name: Function name

        Returns:
            Function definition or None if not found
        """
        return self.functions.get(name)

    def add_output(self, text: str) -> None:
        """
        Add text to the output buffer.

        Args:
            text: Text to add
        """
        self.output.append(text)

    def get_output(self) -> str:
        """
        Get all accumulated output as a single string.

        Returns:
            Complete output text
        """
        return "".join(self.output)

    def clear_output(self) -> None:
        """Clear the output buffer."""
        self.output.clear()

    # ========================================================================
    # Database Methods
    # ========================================================================

    def set_database_connector(self, connector: "DatabaseConnector") -> None:
        """
        Set the database connector for SQL execution.

        Args:
            connector: Database connector instance
        """
        self.database_connector = connector

    def get_database_connector(self) -> Optional["DatabaseConnector"]:
        """
        Get the database connector.

        Returns:
            Database connector or None if not set
        """
        return self.database_connector

    def has_database_connector(self) -> bool:
        """
        Check if a database connector is configured.

        Returns:
            True if database connector is available
        """
        return self.database_connector is not None

    def declare_cursor(self, name: str, cursor: Any) -> None:
        """
        Declare a database cursor.

        Args:
            name: Cursor name
            cursor: Cursor object
        """
        self.cursors[name] = cursor

    def get_cursor(self, name: str) -> Optional[Any]:
        """
        Get a declared cursor.

        Args:
            name: Cursor name

        Returns:
            Cursor object or None if not found
        """
        return self.cursors.get(name)

    def has_cursor(self, name: str) -> bool:
        """
        Check if a cursor is declared.

        Args:
            name: Cursor name

        Returns:
            True if cursor exists
        """
        return name in self.cursors

    def remove_cursor(self, name: str) -> None:
        """
        Remove a cursor from the context.

        Args:
            name: Cursor name
        """
        if name in self.cursors:
            del self.cursors[name]

    # ========================================================================
    # Profiling Methods
    # ========================================================================

    def set_profiler(self, profiler: "ExecutionProfiler") -> None:
        """
        Set the execution profiler.

        Args:
            profiler: Execution profiler instance
        """
        self.profiler = profiler

    def get_profiler(self) -> Optional["ExecutionProfiler"]:
        """
        Get the execution profiler.

        Returns:
            Execution profiler or None if not set
        """
        return self.profiler

    def has_profiler(self) -> bool:
        """
        Check if profiling is enabled.

        Returns:
            True if profiler is configured and enabled
        """
        return self.profiler is not None and self.profiler.enabled

    # ========================================================================
    # SQLCA Methods
    # ========================================================================

    def get_sqlca(self) -> Dict[str, Any]:
        """
        Get the SQLCA (SQL Communication Area) structure.

        Returns:
            SQLCA dictionary with SQL operation status
        """
        return self.sqlca

    def reset_sqlca(self) -> None:
        """Reset SQLCA to initial state."""
        self.sqlca["sqlcode"] = 0
        self.sqlca["sqlerrd"] = [0, 0, 0, 0, 0, 0]
        self.sqlca["sqlerrm"] = ""
        self.sqlca["sqlerrp"] = ""
        self.sqlca["sqlwarn"] = [" "] * 8
