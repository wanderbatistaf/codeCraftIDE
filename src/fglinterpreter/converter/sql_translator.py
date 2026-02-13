"""
SQL statement translator for converting 4GL SQL to Python database calls.

This module provides translation of 4GL SQL statements to Python code using
either wbjdbc (direct SQL) or wborm (ORM-style) database connectors.

Epic 4, Story 4.4: Enhanced SQL Statement Translator
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..lexer.tokens import TokenType
from ..parser.ast_nodes import (
    BinaryOp,
    DeleteStatement,
    Expression,
    Identifier,
    InsertStatement,
    Literal,
    SelectStatement,
    UnaryOp,
    UpdateStatement,
)


class SQLTranslator(ABC):
    """Abstract base class for SQL statement translators."""

    def __init__(self, indent_level: int = 0, indent_str: str = "    "):
        """Initialize the SQL translator.

        Args:
            indent_level: Current indentation level
            indent_str: String to use for indentation
        """
        self.indent_level = indent_level
        self.indent_str = indent_str
        self.lines: List[str] = []

    def emit(self, line: str) -> None:
        """Emit a line of Python code with proper indentation.

        Args:
            line: Line of code to emit
        """
        if line.strip():
            self.lines.append(self.indent_str * self.indent_level + line)
        else:
            self.lines.append("")

    def indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def dedent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)

    def get_code(self) -> str:
        """Get the generated Python code.

        Returns:
            Generated Python code as a string
        """
        return "\n".join(self.lines)

    def clear(self) -> None:
        """Clear all generated code."""
        self.lines = []

    @abstractmethod
    def translate_select(self, node: SelectStatement) -> str:
        """Translate SELECT statement to Python code.

        Args:
            node: SELECT statement AST node

        Returns:
            Generated Python code
        """
        pass

    @abstractmethod
    def translate_insert(self, node: InsertStatement) -> str:
        """Translate INSERT statement to Python code.

        Args:
            node: INSERT statement AST node

        Returns:
            Generated Python code
        """
        pass

    @abstractmethod
    def translate_update(self, node: UpdateStatement) -> str:
        """Translate UPDATE statement to Python code.

        Args:
            node: UPDATE statement AST node

        Returns:
            Generated Python code
        """
        pass

    @abstractmethod
    def translate_delete(self, node: DeleteStatement) -> str:
        """Translate DELETE statement to Python code.

        Args:
            node: DELETE statement AST node

        Returns:
            Generated Python code
        """
        pass

    def build_where_clause(self, where_expr: Optional[Expression]) -> Tuple[str, List[str]]:
        """Build WHERE clause SQL string and parameter list.

        Args:
            where_expr: WHERE clause expression AST node

        Returns:
            Tuple of (WHERE SQL string, list of parameter variable names)
        """
        if not where_expr:
            return "", []

        sql, params = self._build_expression_sql(where_expr)
        return f" WHERE {sql}", params

    def _build_expression_sql(self, expr: Expression) -> Tuple[str, List[str]]:
        """Build SQL expression string and extract parameters.

        Args:
            expr: Expression AST node

        Returns:
            Tuple of (SQL expression string, list of parameter variables)
        """
        if isinstance(expr, Literal):
            # Literal values become parameters
            return "?", [self._convert_literal_to_param(expr)]

        elif isinstance(expr, Identifier):
            # Variable references become parameters
            return "?", [expr.name]

        elif isinstance(expr, BinaryOp):
            return self._build_binary_op_sql(expr)

        elif isinstance(expr, UnaryOp):
            return self._build_unary_op_sql(expr)

        else:
            # Fallback for unsupported expression types
            return "?", ["unknown_expr"]

    def _build_binary_op_sql(self, expr: BinaryOp) -> Tuple[str, List[str]]:
        """Build SQL for binary operation.

        Args:
            expr: Binary operation AST node

        Returns:
            Tuple of (SQL string, parameter list)
        """
        left_sql, left_params = self._build_expression_sql(expr.left)
        right_sql, right_params = self._build_expression_sql(expr.right)

        # Map 4GL operators to SQL operators
        operator_map = {
            TokenType.EQUAL: "=",
            TokenType.NOT_EQUAL: "<>",
            TokenType.LESS_THAN: "<",
            TokenType.GREATER_THAN: ">",
            TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_EQUAL: ">=",
            TokenType.AND: "AND",
            TokenType.OR: "OR",
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.MULTIPLY: "*",
            TokenType.DIVIDE: "/",
        }

        sql_op = operator_map.get(expr.operator, str(expr.operator))

        # Handle special case: column arithmetic in SQL (e.g., "balance + ?")
        if self._is_column_reference(expr.left):
            left_column = self._get_column_name(expr.left)
            sql = f"{left_column} {sql_op} {right_sql}"
            params = right_params
        elif self._is_column_reference(expr.right):
            right_column = self._get_column_name(expr.right)
            sql = f"{left_sql} {sql_op} {right_column}"
            params = left_params
        else:
            sql = f"{left_sql} {sql_op} {right_sql}"
            params = left_params + right_params

        # Add parentheses for complex expressions
        if expr.operator in (TokenType.AND, TokenType.OR):
            sql = f"({sql})"

        return sql, params

    def _build_unary_op_sql(self, expr: UnaryOp) -> Tuple[str, List[str]]:
        """Build SQL for unary operation.

        Args:
            expr: Unary operation AST node

        Returns:
            Tuple of (SQL string, parameter list)
        """
        operand_sql, params = self._build_expression_sql(expr.operand)

        if expr.operator == TokenType.NOT:
            return f"NOT {operand_sql}", params
        elif expr.operator == TokenType.MINUS:
            return f"-{operand_sql}", params
        else:
            return operand_sql, params

    def _is_column_reference(self, expr: Expression) -> bool:
        """Check if expression is a direct column reference.

        This is a heuristic to distinguish column names from variable names.
        In SQL context, if an identifier appears in a WHERE clause without
        being in a parameter position, it's likely a column reference.

        Args:
            expr: Expression to check

        Returns:
            True if expression appears to be a column reference
        """
        # For now, treat simple identifiers as potential column references
        # This will need refinement based on context analysis
        return isinstance(expr, Identifier)

    def _get_column_name(self, expr: Expression) -> str:
        """Extract column name from expression.

        Args:
            expr: Expression node

        Returns:
            Column name string
        """
        if isinstance(expr, Identifier):
            return expr.name
        return "unknown_column"

    def _convert_literal_to_param(self, literal: Literal) -> str:
        """Convert a literal value to a parameter reference.

        Args:
            literal: Literal AST node

        Returns:
            String representing how to reference this literal in Python
        """
        if literal.token_type == TokenType.STRING_LITERAL:
            return f"'{literal.value}'"
        elif literal.token_type == TokenType.INTEGER_LITERAL:
            return str(literal.value)
        elif literal.token_type == TokenType.FLOAT_LITERAL:
            return str(literal.value)
        elif literal.token_type in (TokenType.TRUE, TokenType.FALSE):
            return str(literal.value)
        else:
            return str(literal.value)

    def build_column_list(self, columns: List[str]) -> str:
        """Build comma-separated column list for SQL.

        Args:
            columns: List of column names

        Returns:
            Comma-separated column list
        """
        if not columns:
            return "*"
        return ", ".join(columns)


class WBJDBCTranslator(SQLTranslator):
    """SQL translator for wbjdbc (direct SQL) backend."""

    def translate_select(self, node: SelectStatement) -> str:
        """Translate SELECT statement to wbjdbc Python code.

        Args:
            node: SELECT statement AST node

        Returns:
            Generated Python code
        """
        self.clear()

        # Build the SQL query
        sql_parts = ["SELECT"]

        # Add FIRST N modifier if present
        if node.first_n is not None:
            sql_parts.append(f"FIRST {node.first_n}")

        columns_str = self.build_column_list(node.columns)
        sql_parts.append(columns_str)
        sql = " ".join(sql_parts)

        if node.from_table:
            sql += f" FROM {node.from_table}"

        # Build WHERE clause
        where_sql, params = self.build_where_clause(node.where_clause)
        sql += where_sql

        # Build ORDER BY
        if node.order_by:
            order_parts = []
            for col, direction in node.order_by:
                if direction:
                    order_parts.append(f"{col} {direction}")
                else:
                    order_parts.append(col)
            sql += f" ORDER BY {', '.join(order_parts)}"

        # Build GROUP BY
        if node.group_by:
            sql += f" GROUP BY {', '.join(node.group_by)}"

        # Generate Python code
        self.emit(f'_sql = "{sql}"')

        if params:
            params_list = ", ".join(params)
            self.emit(f"_params = [{params_list}]")
            self.emit("_cursor = db.execute_query(_sql, _params)")
        else:
            self.emit("_cursor = db.execute_query(_sql)")

        # Handle INTO clause
        if node.into_variables:
            self.emit("_row = _cursor.fetchone()")
            self.emit("if _row:")
            self.indent()
            vars_str = ", ".join(node.into_variables)
            self.emit(f"{vars_str} = _row")
            self.dedent()

        return self.get_code()

    def translate_insert(self, node: InsertStatement) -> str:
        """Translate INSERT statement to wbjdbc Python code.

        Args:
            node: INSERT statement AST node

        Returns:
            Generated Python code
        """
        self.clear()

        # Build the SQL query
        sql = f"INSERT INTO {node.table_name}"

        if node.columns:
            columns_str = ", ".join(node.columns)
            sql += f" ({columns_str})"

        # Build VALUES clause
        if node.values:
            placeholders = ", ".join(["?" for _ in node.values])
            sql += f" VALUES ({placeholders})"

            # Extract parameters from value expressions
            params = []
            for value_expr in node.values:
                _, expr_params = self._build_expression_sql(value_expr)
                params.extend(expr_params)

            # Generate Python code
            self.emit(f'_sql = "{sql}"')
            params_list = ", ".join(params)
            self.emit(f"_params = [{params_list}]")
            self.emit("db.execute_query(_sql, _params)")
        else:
            self.emit(f'db.execute_query("{sql}")')

        return self.get_code()

    def translate_update(self, node: UpdateStatement) -> str:
        """Translate UPDATE statement to wbjdbc Python code.

        Args:
            node: UPDATE statement AST node

        Returns:
            Generated Python code
        """
        self.clear()

        # Build SET clause
        set_parts = []
        set_params = []

        for column, value_expr in node.assignments:
            # Check if value is a column expression (e.g., balance = balance + 100)
            if isinstance(value_expr, BinaryOp) and self._is_column_reference(value_expr.left):
                set_sql, params = self._build_expression_sql(value_expr)
                set_parts.append(f"{column} = {set_sql}")
                set_params.extend(params)
            else:
                set_sql, params = self._build_expression_sql(value_expr)
                set_parts.append(f"{column} = {set_sql}")
                set_params.extend(params)

        sql = f"UPDATE {node.table_name} SET {', '.join(set_parts)}"

        # Build WHERE clause
        where_sql, where_params = self.build_where_clause(node.where_clause)
        sql += where_sql

        # Generate Python code
        self.emit(f'_sql = "{sql}"')

        all_params = set_params + where_params
        if all_params:
            params_list = ", ".join(all_params)
            self.emit(f"_params = [{params_list}]")
            self.emit("db.execute_query(_sql, _params)")
        else:
            self.emit("db.execute_query(_sql)")

        return self.get_code()

    def translate_delete(self, node: DeleteStatement) -> str:
        """Translate DELETE statement to wbjdbc Python code.

        Args:
            node: DELETE statement AST node

        Returns:
            Generated Python code
        """
        self.clear()

        # Build the SQL query
        sql = f"DELETE FROM {node.table_name}"

        # Build WHERE clause
        where_sql, params = self.build_where_clause(node.where_clause)
        sql += where_sql

        # Generate Python code
        self.emit(f'_sql = "{sql}"')

        if params:
            params_list = ", ".join(params)
            self.emit(f"_params = [{params_list}]")
            self.emit("db.execute_query(_sql, _params)")
        else:
            self.emit("db.execute_query(_sql)")

        return self.get_code()


class WBORMTranslator(SQLTranslator):
    """SQL translator for wborm (ORM-style) backend."""

    def translate_select(self, node: SelectStatement) -> str:
        """Translate SELECT statement to wborm Python code.

        Args:
            node: SELECT statement AST node

        Returns:
            Generated Python code
        """
        self.clear()

        # Build the SQL query (same as wbjdbc)
        columns_str = self.build_column_list(node.columns)
        sql = f"SELECT {columns_str}"

        if node.from_table:
            sql += f" FROM {node.from_table}"

        # Build WHERE clause
        where_sql, params = self.build_where_clause(node.where_clause)
        sql += where_sql

        # Build ORDER BY
        if node.order_by:
            order_parts = [f"{col} {direction}" for col, direction in node.order_by]
            sql += f" ORDER BY {', '.join(order_parts)}"

        # Build GROUP BY
        if node.group_by:
            sql += f" GROUP BY {', '.join(node.group_by)}"

        # Generate Python code using query_one for single row
        self.emit(f'_sql = "{sql}"')

        if params:
            params_list = ", ".join(params)
            self.emit(f"_params = [{params_list}]")
            self.emit("_result = db.query_one(_sql, _params)")
        else:
            self.emit("_result = db.query_one(_sql)")

        # Handle INTO clause with dictionary access
        if node.into_variables:
            self.emit("if _result:")
            self.indent()
            for i, var_name in enumerate(node.into_variables):
                if i < len(node.columns):
                    col_name = node.columns[i]
                    self.emit(f"{var_name} = _result['{col_name}']")
                else:
                    self.emit(f"{var_name} = None")
            self.dedent()

        return self.get_code()

    def translate_insert(self, node: InsertStatement) -> str:
        """Translate INSERT statement to wborm Python code.

        Args:
            node: INSERT statement AST node

        Returns:
            Generated Python code
        """
        # wborm uses the same direct SQL approach for INSERT
        return WBJDBCTranslator(self.indent_level, self.indent_str).translate_insert(node)

    def translate_update(self, node: UpdateStatement) -> str:
        """Translate UPDATE statement to wborm Python code.

        Args:
            node: UPDATE statement AST node

        Returns:
            Generated Python code
        """
        # wborm uses the same direct SQL approach for UPDATE
        return WBJDBCTranslator(self.indent_level, self.indent_str).translate_update(node)

    def translate_delete(self, node: DeleteStatement) -> str:
        """Translate DELETE statement to wborm Python code.

        Args:
            node: DELETE statement AST node

        Returns:
            Generated Python code
        """
        # wborm uses the same direct SQL approach for DELETE
        return WBJDBCTranslator(self.indent_level, self.indent_str).translate_delete(node)


def create_sql_translator(backend: str = "wbjdbc", **kwargs) -> SQLTranslator:
    """Factory function to create appropriate SQL translator.

    Args:
        backend: Backend type ("wbjdbc" or "wborm")
        **kwargs: Additional arguments to pass to translator constructor

    Returns:
        SQL translator instance

    Raises:
        ValueError: If backend is not supported
    """
    if backend == "wbjdbc":
        return WBJDBCTranslator(**kwargs)
    elif backend == "wborm":
        return WBORMTranslator(**kwargs)
    else:
        raise ValueError(f"Unsupported SQL backend: {backend}. Use 'wbjdbc' or 'wborm'.")
