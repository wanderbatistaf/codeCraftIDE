"""
Interpreter for executing 4GL AST.

This module implements the visitor pattern to traverse and execute the AST.
"""

from typing import Any, List, Optional

from ..lexer import TokenType
from ..parser.ast_nodes import *
from .builtins import get_builtin_function
from .context import ExecutionContext
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


class Interpreter(ASTVisitor):
    """
    Interpreter for executing 4GL programs.

    Uses the visitor pattern to traverse the AST and execute each node.
    """

    def __init__(self, context: Optional[ExecutionContext] = None) -> None:
        """
        Initialize the interpreter.

        Args:
            context: Execution context (creates new one if not provided)
        """
        self.context = context or ExecutionContext()

    def execute(self, program: Program) -> str:
        """
        Execute a complete program.

        Args:
            program: Program AST node

        Returns:
            Output from the program execution
        """
        try:
            program.accept(self)
            return self.context.get_output()
        except RuntimeError:
            # Re-raise runtime errors with context
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise RuntimeError(f"Unexpected error during execution: {e}")

    # ========================================================================
    # Expression Visitors
    # ========================================================================

    def visit_literal(self, node: Literal) -> Any:
        """Evaluate a literal expression."""
        return node.value

    def visit_identifier(self, node: Identifier) -> Any:
        """Evaluate an identifier (variable reference)."""
        # Check for system variables first
        if node.name.upper() == "SQLCODE":
            return self.context.sqlca.get("SQLCODE", 0)
        elif node.name.upper() == "SQLCA":
            # Return SQLCA as a dict-like object
            return self.context.sqlca

        try:
            return self.context.get_variable(node.name)
        except UndefinedVariableError:
            raise UndefinedVariableError(node.name, node)

    def visit_binary_op(self, node: BinaryOp) -> Any:
        """Evaluate a binary operation."""
        left = node.left.accept(self)
        right = node.right.accept(self)

        try:
            # Arithmetic operators
            if node.operator_type == TokenType.PLUS:
                return left + right
            elif node.operator_type == TokenType.MINUS:
                return left - right
            elif node.operator_type == TokenType.MULTIPLY:
                return left * right
            elif node.operator_type == TokenType.DIVIDE:
                if right == 0:
                    raise DivisionByZeroError(node)
                return left / right
            elif node.operator_type == TokenType.MODULO:
                if right == 0:
                    raise DivisionByZeroError(node)
                return left % right
            elif node.operator_type == TokenType.POWER:
                return left**right

            # String concatenation
            elif node.operator_type == TokenType.CONCAT:
                return str(left if left is not None else "") + str(
                    right if right is not None else ""
                )

            # Comparison operators
            elif node.operator_type == TokenType.EQUAL:
                return left == right
            elif node.operator_type == TokenType.NOT_EQUAL:
                return left != right
            elif node.operator_type == TokenType.LESS_THAN:
                return left < right
            elif node.operator_type == TokenType.GREATER_THAN:
                return left > right
            elif node.operator_type == TokenType.LESS_EQUAL:
                return left <= right
            elif node.operator_type == TokenType.GREATER_EQUAL:
                return left >= right

            # Pattern matching operators
            elif node.operator_type == TokenType.LIKE:
                # Convert SQL LIKE pattern to Python regex
                # % -> .* (any characters)
                # _ -> . (any single character)
                import re

                pattern = str(right)
                # Escape special regex characters except % and _
                pattern = re.escape(pattern)
                # Now replace escaped % and _ with regex equivalents
                pattern = pattern.replace(r"\%", ".*").replace(r"\_", ".")
                pattern = "^" + pattern + "$"  # Match entire string
                return bool(re.match(pattern, str(left)))

            # IN operator
            elif node.operator_type == TokenType.IN:
                # right should be a list of expressions (already evaluated in parser)
                # We need to evaluate them
                if isinstance(right, list):
                    values = [expr.accept(self) for expr in right]
                else:
                    # right is a Literal containing a list
                    values = right
                return left in values

            # BETWEEN operator
            elif node.operator_type == TokenType.BETWEEN:
                # right contains [low, high] expressions
                if isinstance(right, list) and len(right) == 2:
                    low_expr, high_expr = right
                    low_val = low_expr.accept(self)
                    high_val = high_expr.accept(self)
                    return low_val <= left <= high_val
                else:
                    raise InvalidOperationError("BETWEEN requires two values", node)

            # Logical operators
            elif node.operator_type == TokenType.AND:
                return self._to_bool(left) and self._to_bool(right)
            elif node.operator_type == TokenType.OR:
                return self._to_bool(left) or self._to_bool(right)

            else:
                raise InvalidOperationError(f"Unknown operator: {node.operator}", node)

        except (TypeError, ValueError):
            raise TypeMismatchError(
                f"Cannot apply {node.operator} to {type(left).__name__} and {type(right).__name__}",
                node,
            )

    def visit_unary_op(self, node: UnaryOp) -> Any:
        """Evaluate a unary operation."""
        operand = node.operand.accept(self)

        if node.operator_type == TokenType.MINUS:
            return -operand
        elif node.operator_type == TokenType.NOT:
            return not self._to_bool(operand)
        else:
            raise InvalidOperationError(f"Unknown unary operator: {node.operator}", node)

    def visit_function_call(self, node: FunctionCall) -> Any:
        """Evaluate a function call expression."""
        # Check for built-in functions first
        builtin_func = get_builtin_function(node.function_name)
        if builtin_func:
            # Evaluate arguments
            args = [arg.accept(self) for arg in node.arguments]
            try:
                return builtin_func(*args)
            except Exception as e:
                raise RuntimeError(
                    f"Error calling built-in function {node.function_name}: {e}", node
                )

        # Check for user-defined functions
        func_def = self.context.get_function(node.function_name)

        if not func_def:
            raise FunctionNotFoundError(node.function_name, node)

        # Evaluate arguments
        args = [arg.accept(self) for arg in node.arguments]

        # Execute function
        return self._execute_function(func_def, args, node)

    def visit_array_access(self, node: ArrayAccess) -> Any:
        """Evaluate array element access."""
        # For now, treat arrays as lists
        array = self.context.get_variable(node.array_name)
        index = node.index.accept(self)

        try:
            # 4GL arrays are 1-indexed, Python is 0-indexed
            return array[int(index) - 1]
        except (IndexError, TypeError) as e:
            raise RuntimeError(f"Array access error: {e}", node)

    # ========================================================================
    # Statement Visitors
    # ========================================================================

    def visit_define_statement(self, node: DefineStatement) -> None:
        """Execute a DEFINE statement."""
        # Define each variable with None as initial value
        for var_name in node.variables:
            self.context.define_variable(var_name, None)

        # Note: DATETIME/INTERVAL qualifiers (e.g., YEAR TO SECOND) are parsed
        # and stored in node.qualifier_start and node.qualifier_end.
        # These qualifiers define the precision and range of datetime/interval values.
        # In a full implementation, qualifiers would be used for:
        # - Type validation on assignment
        # - Formatting output with correct precision
        # - Handling FRACTION precision for sub-second values

    def visit_let_statement(self, node: LetStatement) -> None:
        """Execute a LET statement (assignment)."""
        value = node.value.accept(self)
        self.context.set_variable(node.variable, value)

    def visit_display_statement(self, node: DisplayStatement) -> None:
        """Execute a DISPLAY statement."""
        output_parts = []

        for expr in node.expressions:
            value = expr.accept(self)
            output_parts.append(self._to_string(value))

        output_text = "".join(output_parts)
        self.context.add_output(output_text + "\n")

        # Also print to console for immediate feedback
        print(output_text)

    def visit_return_statement(self, node: ReturnStatement) -> None:
        """Execute a RETURN statement."""
        value = None
        if node.value:
            value = node.value.accept(self)

        raise ReturnException(value)

    def visit_call_statement(self, node: CallStatement) -> None:
        """Execute a CALL statement."""
        func_def = self.context.get_function(node.function_name)

        if not func_def:
            raise FunctionNotFoundError(node.function_name, node)

        # Evaluate arguments
        args = [arg.accept(self) for arg in node.arguments]

        # Execute function (discard return value for CALL)
        self._execute_function(func_def, args, node)

    def visit_exit_statement(self, node: ExitStatement) -> None:
        """Execute an EXIT statement."""
        raise ExitLoopException()

    def visit_continue_statement(self, node: ContinueStatement) -> None:
        """Execute a CONTINUE statement."""
        raise ContinueLoopException()

    # ========================================================================
    # Control Flow Visitors
    # ========================================================================

    def visit_if_statement(self, node: IfStatement) -> None:
        """Execute an IF statement."""
        condition = node.condition.accept(self)

        if self._to_bool(condition):
            # Execute THEN block
            self._execute_block(node.then_block)
        else:
            # Check ELIF blocks
            executed = False
            for elif_condition, elif_block in node.elif_blocks:
                if self._to_bool(elif_condition.accept(self)):
                    self._execute_block(elif_block)
                    executed = True
                    break

            # Execute ELSE block if no ELIF matched
            if not executed and node.else_block:
                self._execute_block(node.else_block)

    def visit_for_statement(self, node: ForStatement) -> None:
        """Execute a FOR loop."""
        start_value = node.start_value.accept(self)
        end_value = node.end_value.accept(self)
        step_value = 1

        if node.step_value:
            step_value = node.step_value.accept(self)

        # Ensure numeric values
        try:
            start = int(start_value)
            end = int(end_value)
            step = int(step_value)
        except (TypeError, ValueError):
            raise TypeMismatchError("FOR loop requires integer values", node)

        # Determine range direction
        if step > 0:
            current = start
            while current <= end:
                self.context.set_variable(node.variable, current)

                try:
                    self._execute_block(node.body)
                except ExitLoopException:
                    break
                except ContinueLoopException:
                    pass  # Continue to next iteration

                current += step
        else:
            current = start
            while current >= end:
                self.context.set_variable(node.variable, current)

                try:
                    self._execute_block(node.body)
                except ExitLoopException:
                    break
                except ContinueLoopException:
                    pass  # Continue to next iteration

                current += step

    def visit_while_statement(self, node: WhileStatement) -> None:
        """Execute a WHILE loop."""
        while self._to_bool(node.condition.accept(self)):
            try:
                self._execute_block(node.body)
            except ExitLoopException:
                break
            except ContinueLoopException:
                continue

    def visit_case_statement(self, node: CaseStatement) -> None:
        """Execute a CASE statement."""
        # Evaluate the case expression (if present)
        case_value = None
        if node.expression:
            case_value = node.expression.accept(self)

        # Check each WHEN clause
        executed = False
        for when_clause in node.when_clauses:
            when_value = when_clause.condition.accept(self)

            # If no case expression, treat WHEN as boolean condition
            # Otherwise, compare with case value
            matches = False
            if case_value is None:
                matches = self._to_bool(when_value)
            else:
                matches = case_value == when_value

            if matches:
                self._execute_block(when_clause.statements)
                executed = True
                break  # Execute first matching WHEN only

        # Execute OTHERWISE block if no WHEN matched
        if not executed and node.otherwise_block:
            self._execute_block(node.otherwise_block)

    def visit_foreach_statement(self, node: ForeachStatement) -> None:
        """Execute a FOREACH loop for cursor iteration."""
        # Get cursor info
        cursor_info = self.context.get_cursor(node.cursor_name)
        if not cursor_info:
            raise RuntimeError(f"Cursor '{node.cursor_name}' not declared", node)

        results = cursor_info.get("results")
        if results is None:
            raise RuntimeError(f"Cursor '{node.cursor_name}' not opened", node)

        # Get column names from cursor (set in OPEN statement)
        column_names = cursor_info.get("columns", [])

        # Iterate through results
        try:
            for row in results:
                # Assign row values to INTO variables
                if isinstance(row, dict):
                    # Results from fetchdh() - map by position using column names
                    # Convert dict to list of values in column order
                    if column_names:
                        # Map values by column order from SELECT
                        row_values = [row.get(col, None) for col in column_names]
                    else:
                        # Fallback: use dict values in iteration order (Python 3.7+)
                        row_values = list(row.values())

                    # Assign to INTO variables by position
                    for var_name, value in zip(node.into_variables, row_values):
                        self.context.set_variable(var_name, value)
                elif isinstance(row, (tuple, list)):
                    # Results from fetchall() - map by position
                    for var_name, value in zip(node.into_variables, row):
                        self.context.set_variable(var_name, value)

                # Execute loop body
                try:
                    self._execute_block(node.body)
                except ExitLoopException:
                    break
                except ContinueLoopException:
                    continue

        except Exception as e:
            if not isinstance(e, (ExitLoopException, ContinueLoopException, ReturnException)):
                raise RuntimeError(f"Error in FOREACH loop: {e}", node)
            raise

    # ========================================================================
    # Function and Program Visitors
    # ========================================================================

    def visit_function_def(self, node: FunctionDef) -> None:
        """Process a function definition (register it)."""
        self.context.define_function(node.name, node)

    def visit_main_block(self, node: MainBlock) -> None:
        """Execute the MAIN block."""
        self._execute_block(node.body)

    def visit_program(self, node: Program) -> None:
        """Execute a complete program."""
        # First, register all functions
        for func in node.functions:
            func.accept(self)

        # Then execute MAIN block if present
        if node.main_block:
            node.main_block.accept(self)

    # ========================================================================
    # SQL Statement Visitors (Placeholders for Epic 2)
    # ========================================================================

    def visit_select_statement(self, node: SelectStatement) -> None:
        """Execute SELECT statement."""
        # Check database connector
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        # Build SELECT query
        query_parts = ["SELECT"]

        # Add DISTINCT if present
        if node.distinct:
            query_parts.append("DISTINCT")

        # Add FIRST N modifier if present
        if node.first_n is not None:
            query_parts.extend(["FIRST", str(node.first_n)])

        query_parts.append(", ".join(node.columns))

        if node.from_table:
            query_parts.extend(["FROM", node.from_table])

        # Build WHERE clause with parameters
        params = []
        if node.where_clause:
            where_sql, where_params = self._build_expression_sql(node.where_clause)
            query_parts.extend(["WHERE", where_sql])
            params.extend(where_params)

        # Build GROUP BY clause
        if node.group_by:
            query_parts.extend(["GROUP BY", ", ".join(node.group_by)])

        # Build HAVING clause (must come after GROUP BY)
        if node.having_clause:
            having_sql, having_params = self._build_expression_sql(node.having_clause)
            query_parts.extend(["HAVING", having_sql])
            params.extend(having_params)

        # Build ORDER BY clause
        if node.order_by:
            order_items = []
            for col, direction in node.order_by:
                if direction:
                    order_items.append(f"{col} {direction}")
                else:
                    order_items.append(col)
            query_parts.extend(["ORDER BY", ", ".join(order_items)])

        query = " ".join(query_parts)

        # Execute query
        try:
            results = connector.query(query, tuple(params) if params else None)

            # If INTO clause, assign first row to variables
            if node.into_variables and results:
                row = results[0]
                if isinstance(row, dict):
                    # Results from fetchdh() - map by column name
                    for var_name, col_name in zip(node.into_variables, node.columns):
                        value = row.get(col_name, None)
                        self.context.set_variable(var_name, value)
                elif isinstance(row, (tuple, list)):
                    # Results from fetchall() - map by position
                    for var_name, value in zip(node.into_variables, row):
                        self.context.set_variable(var_name, value)

        except Exception as e:
            raise RuntimeError(f"Error executing SELECT: {e}", node)

    def visit_insert_statement(self, node: InsertStatement) -> None:
        """Execute INSERT statement."""
        # Check database connector
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        # Build INSERT query
        query_parts = ["INSERT INTO", node.table_name]

        # Add column list if specified
        if node.columns:
            query_parts.append(f"({', '.join(node.columns)})")

        # Build VALUES clause with parameters
        params = []
        if node.values:
            value_placeholders = []
            for value_expr in node.values:
                value = value_expr.accept(self)
                value_placeholders.append("?")
                params.append(value)

            query_parts.extend(["VALUES", f"({', '.join(value_placeholders)})"])

        query = " ".join(query_parts)

        # Execute query
        try:
            connector.execute(query, tuple(params) if params else None)
        except Exception as e:
            raise RuntimeError(f"Error executing INSERT: {e}", node)

    def visit_update_statement(self, node: UpdateStatement) -> None:
        """Execute UPDATE statement."""
        # Check database connector
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        # Build UPDATE query
        query_parts = ["UPDATE", node.table_name, "SET"]

        # Build SET clause with parameters
        params = []
        set_items = []
        for column, value_expr in node.assignments:
            value = value_expr.accept(self)
            set_items.append(f"{column} = ?")
            params.append(value)

        query_parts.append(", ".join(set_items))

        # Build WHERE clause with parameters
        if node.where_clause:
            where_sql, where_params = self._build_expression_sql(node.where_clause)
            query_parts.extend(["WHERE", where_sql])
            params.extend(where_params)

        query = " ".join(query_parts)

        # Execute query
        try:
            connector.execute(query, tuple(params) if params else None)
        except Exception as e:
            raise RuntimeError(f"Error executing UPDATE: {e}", node)

    def visit_delete_statement(self, node: DeleteStatement) -> None:
        """Execute DELETE statement."""
        # Check database connector
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        # Build DELETE query
        query_parts = ["DELETE FROM", node.table_name]

        # Build WHERE clause with parameters
        params = []
        if node.where_clause:
            where_sql, where_params = self._build_expression_sql(node.where_clause)
            query_parts.extend(["WHERE", where_sql])
            params.extend(where_params)

        query = " ".join(query_parts)

        # Execute query
        try:
            connector.execute(query, tuple(params) if params else None)
        except Exception as e:
            raise RuntimeError(f"Error executing DELETE: {e}", node)

    def visit_declare_statement(self, node: DeclareStatement) -> None:
        """Execute DECLARE cursor statement."""
        # Store cursor definition in context for later OPEN
        # We'll store the SELECT statement AST node
        cursor_info = {
            "select_statement": node.select_statement,
            "cursor": None,  # Will be populated on OPEN
            "results": None,  # Will be populated on OPEN
        }
        self.context.declare_cursor(node.cursor_name, cursor_info)

    def visit_open_statement(self, node: OpenStatement) -> None:
        """Execute OPEN cursor statement with optional USING parameters."""
        # Check database connector
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        # Get cursor info
        cursor_info = self.context.get_cursor(node.cursor_name)
        if not cursor_info:
            raise RuntimeError(f"Cursor '{node.cursor_name}' not declared", node)

        connector = self.context.get_database_connector()

        # Execute the SELECT statement from DECLARE
        select_node = cursor_info["select_statement"]
        if not select_node:
            raise RuntimeError(f"Cursor '{node.cursor_name}' has no SELECT statement", node)

        # Build and execute query
        query_parts = ["SELECT", ", ".join(select_node.columns)]

        if select_node.from_table:
            query_parts.extend(["FROM", select_node.from_table])

        params = []
        if select_node.where_clause:
            where_sql, where_params = self._build_expression_sql(select_node.where_clause)
            query_parts.extend(["WHERE", where_sql])
            params.extend(where_params)

        # If USING variables specified, get their values and use instead of params
        if node.using_variables:
            using_values = []
            for var_name in node.using_variables:
                try:
                    value = self.context.get_variable(var_name)
                    using_values.append(value)
                except Exception as e:
                    raise RuntimeError(f"Error getting USING variable '{var_name}': {e}", node)
            params = using_values

        query = " ".join(query_parts)

        try:
            results = connector.query(query, tuple(params) if params else None)
            cursor_info["results"] = results
            cursor_info["current_index"] = 0
            # Store column names for proper mapping in FOREACH
            cursor_info["columns"] = select_node.columns
        except Exception as e:
            raise RuntimeError(f"Error opening cursor '{node.cursor_name}': {e}", node)

    def visit_close_statement(self, node: CloseStatement) -> None:
        """Execute CLOSE cursor statement."""
        cursor_info = self.context.get_cursor(node.cursor_name)
        if not cursor_info:
            raise RuntimeError(f"Cursor '{node.cursor_name}' not declared", node)

        # Clear results
        cursor_info["results"] = None
        cursor_info["current_index"] = 0

    def visit_free_statement(self, node: FreeStatement) -> None:
        """Execute FREE cursor statement."""
        if not self.context.has_cursor(node.cursor_name):
            raise RuntimeError(f"Cursor '{node.cursor_name}' not declared", node)

        # Remove cursor from context
        self.context.remove_cursor(node.cursor_name)

    def visit_begin_work_statement(self, node: BeginWorkStatement) -> None:
        """Execute BEGIN WORK statement to start a transaction."""
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        try:
            connector.begin_transaction()
            # Update SQLCA
            self._update_sqlca(0, 0)  # Success
        except Exception as e:
            self._update_sqlca(-1, 0)  # Error
            raise RuntimeError(f"Error beginning transaction: {e}", node)

    def visit_commit_work_statement(self, node: CommitWorkStatement) -> None:
        """Execute COMMIT WORK statement to commit a transaction."""
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        try:
            connector.commit()
            # Update SQLCA
            self._update_sqlca(0, 0)  # Success
        except Exception as e:
            self._update_sqlca(-1, 0)  # Error
            raise RuntimeError(f"Error committing transaction: {e}", node)

    def visit_rollback_work_statement(self, node: RollbackWorkStatement) -> None:
        """Execute ROLLBACK WORK statement to rollback a transaction."""
        if not self.context.has_database_connector():
            raise RuntimeError("No database connector configured", node)

        connector = self.context.get_database_connector()

        try:
            connector.rollback()
            # Update SQLCA
            self._update_sqlca(0, 0)  # Success
        except Exception as e:
            self._update_sqlca(-1, 0)  # Error
            raise RuntimeError(f"Error rolling back transaction: {e}", node)

    def visit_database_statement(self, node: DatabaseStatement) -> None:
        """Execute DATABASE statement to connect to a database."""
        # For now, we assume the database connector is already configured
        # In a full implementation, this would parse the database name and
        # create/configure the connector
        #
        # Format: DATABASE dbname@host:port
        # Example: DATABASE testdb@localhost:9088

        if not self.context.has_database_connector():
            raise RuntimeError(
                "Database connector not configured. Please set up the connector before using DATABASE statement.",
                node,
            )

        # If connector exists, it's already connected during setup
        # This statement would typically trigger a connection switch or verification
        # For now, we just verify the connector is available
        connector = self.context.get_database_connector()

        try:
            # Verify connection is active
            if not connector.is_connected():
                connector.connect()

            # Update SQLCA
            self._update_sqlca(0, 0)  # Success
        except Exception as e:
            self._update_sqlca(-1, 0)  # Error
            raise RuntimeError(f"Error connecting to database '{node.database_name}': {e}", node)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _execute_block(self, statements: List[Statement]) -> None:
        """Execute a block of statements."""
        for stmt in statements:
            stmt.accept(self)

    def _execute_function(self, func_def: FunctionDef, args: List[Any], call_node: ASTNode) -> Any:
        """
        Execute a function with given arguments.

        Args:
            func_def: Function definition
            args: Argument values
            call_node: The call site node (for error reporting)

        Returns:
            Return value from the function
        """
        # Check argument count
        if len(args) != len(func_def.parameters):
            raise RuntimeError(
                f"Function {func_def.name} expects {len(func_def.parameters)} arguments, got {len(args)}",
                call_node,
            )

        # Push new scope for function
        self.context.push_scope()

        try:
            # Bind parameters
            for param, arg_value in zip(func_def.parameters, args):
                self.context.define_variable(param.name, arg_value)

            # Execute function body
            try:
                self._execute_block(func_def.body)
                return None  # No explicit return
            except ReturnException as e:
                return e.value

        finally:
            # Pop function scope
            self.context.pop_scope()

    def _to_bool(self, value: Any) -> bool:
        """Convert a value to boolean (4GL semantics)."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return bool(value)

    def _to_string(self, value: Any) -> str:
        """Convert a value to string for output."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, float):
            # Format floats nicely
            if value == int(value):
                return str(int(value))
            return str(value)
        return str(value)

    def _build_expression_sql(self, expr: Expression) -> tuple[str, List[Any]]:
        """
        Build SQL string and parameter list from an expression AST node.

        Args:
            expr: Expression AST node

        Returns:
            Tuple of (sql_string, parameters)
        """
        if isinstance(expr, Literal):
            # Special case: if value is already "?" (from parametric cursor), keep it as placeholder
            if expr.value == "?":
                return ("?", [])
            # Use parameter placeholder for literals
            return ("?", [expr.value])

        elif isinstance(expr, Identifier):
            # Check if this identifier is a variable in the context with a non-None value
            # This distinguishes between:
            # 1. Columns (or uninitialized variables): state = "CA" where state is a column
            # 2. Variables: customer_num = cust_num where cust_num has a value
            if self.context.variable_exists(expr.name):
                value = self.context.get_variable(expr.name)
                # Only substitute if the variable has been assigned a non-None value
                # If it's None, treat it as a column reference
                if value is not None:
                    return ("?", [value])
            # It's a column reference (or uninitialized variable)
            return (expr.name, [])

        elif isinstance(expr, BinaryOp):
            # Binary operation - recursively build left and right
            left_sql, left_params = self._build_expression_sql(expr.left)

            # Special handling for IS NULL and IS NOT NULL
            if (
                expr.operator in ("IS", "IS NOT")
                and isinstance(expr.right, Literal)
                and expr.right.value is None
            ):
                sql = f"({left_sql} {expr.operator} NULL)"
                return (sql, left_params)

            right_sql, right_params = self._build_expression_sql(expr.right)

            # Map operator to SQL
            op_map = {
                TokenType.PLUS: "+",
                TokenType.MINUS: "-",
                TokenType.MULTIPLY: "*",
                TokenType.DIVIDE: "/",
                TokenType.MODULO: "%",
                TokenType.EQUAL: "=",
                TokenType.NOT_EQUAL: "!=",
                TokenType.LESS_THAN: "<",
                TokenType.LESS_EQUAL: "<=",
                TokenType.GREATER_THAN: ">",
                TokenType.GREATER_EQUAL: ">=",
                TokenType.AND: "AND",
                TokenType.OR: "OR",
            }

            op_str = op_map.get(expr.operator_type, expr.operator)
            sql = f"({left_sql} {op_str} {right_sql})"
            params = left_params + right_params

            return (sql, params)

        elif isinstance(expr, UnaryOp):
            # Unary operation
            operand_sql, operand_params = self._build_expression_sql(expr.operand)

            op_map = {
                TokenType.NOT: "NOT",
                TokenType.MINUS: "-",
            }

            op_str = op_map.get(expr.operator, str(expr.operator))
            sql = f"{op_str} ({operand_sql})"

            return (sql, operand_params)

        else:
            # For other expression types, evaluate and use as parameter
            value = expr.accept(self)
            return ("?", [value])

    def _update_sqlca(self, sqlcode: int, rowcount: int = 0, sqlerrm: str = "") -> None:
        """
        Update SQLCA (SQL Communication Area) with operation results.

        Args:
            sqlcode: SQL return code (0 = success, negative = error, 100 = not found)
            rowcount: Number of rows affected
            sqlerrm: Error message (if any)
        """
        sqlca = self.context.get_sqlca()
        sqlca["sqlcode"] = sqlcode
        sqlca["sqlerrd"] = [rowcount, 0, 0, 0, 0, 0]  # Only sqlerrd[1] used for row count
        sqlca["sqlerrm"] = sqlerrm


# ============================================================================
# Convenience Function
# ============================================================================


def interpret_source(source: str, filename: str = "<stdin>") -> str:
    """
    Parse and execute 4GL source code.

    Args:
        source: The 4GL source code
        filename: Name of the source file (for error messages)

    Returns:
        Output from program execution

    Raises:
        RuntimeError: If execution fails
    """
    from ..parser import parse_source

    # Parse the source
    ast = parse_source(source, filename)

    # Execute it
    interpreter = Interpreter()
    return interpreter.execute(ast)
