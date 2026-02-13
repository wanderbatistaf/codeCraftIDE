"""
4GL to Python code converter.

This module converts parsed 4GL AST into equivalent Python code.
"""

from typing import Any, List

from ..lexer.tokens import TokenType
from ..parser.ast_nodes import (
    ASTVisitor,
    BinaryOp,
    CallStatement,
    CaseStatement,
    ContinueStatement,
    DefineStatement,
    DeleteStatement,
    DisplayStatement,
    ExitStatement,
    ForStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    InsertStatement,
    LetStatement,
    Literal,
    MainBlock,
    Program,
    ReturnStatement,
    SelectStatement,
    UnaryOp,
    UpdateStatement,
    WhileStatement,
)
from .sql_translator import create_sql_translator


class PythonCodeGenerator(ASTVisitor):
    """Generates Python code from 4GL AST."""

    def __init__(self, indent_size: int = 4, sql_backend: str = "wbjdbc"):
        """Initialize the code generator.

        Args:
            indent_size: Number of spaces per indentation level
            sql_backend: SQL backend to use ("wbjdbc" or "wborm")
        """
        self.indent_size = indent_size
        self.indent_level = 0
        self.output: List[str] = []
        self.sql_backend = sql_backend
        self.has_sql_statements = False  # Track if SQL statements are present

    def indent(self) -> str:
        """Get current indentation string."""
        return " " * (self.indent_level * self.indent_size)

    def increase_indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def decrease_indent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)

    def emit(self, code: str) -> None:
        """Emit a line of code with current indentation."""
        self.output.append(self.indent() + code)

    def emit_blank(self) -> None:
        """Emit a blank line."""
        self.output.append("")

    def get_code(self) -> str:
        """Get the generated Python code."""
        return "\n".join(self.output)

    # Type mapping
    TYPE_MAP = {
        "INTEGER": "int",
        "SMALLINT": "int",
        "INT": "int",
        "BIGINT": "int",
        "INT8": "int",
        "SERIAL": "int",
        "SERIAL8": "int",
        "BIGSERIAL": "int",
        "DECIMAL": "float",
        "FLOAT": "float",
        "SMALLFLOAT": "float",
        "MONEY": "float",
        "REAL": "float",
        "DOUBLE": "float",
        "CHAR": "str",
        "VARCHAR": "str",
        "NCHAR": "str",
        "NVARCHAR": "str",
        "STRING": "str",
        "TEXT": "str",
        "DATE": "datetime.date",
        "DATETIME": "datetime.datetime",
        "INTERVAL": "datetime.timedelta",
        "BOOLEAN": "bool",
        "BYTE": "bytes",
    }

    def map_type(self, fgl_type: str) -> str:
        """Map 4GL type to Python type."""
        return self.TYPE_MAP.get(fgl_type.upper(), "Any")

    # Visitor methods

    def visit_program(self, node: Program) -> str:
        """Convert Program node to Python code."""
        # Add header
        self.emit("#!/usr/bin/env python3")
        self.emit('"""')
        self.emit("Generated from 4GL source by fglInterpreter.")
        self.emit('"""')
        self.emit_blank()

        # Placeholder for imports (will be filled after AST traversal)
        import_placeholder_index = len(self.output)

        # Convert functions
        for func in node.functions:
            func.accept(self)
            self.emit_blank()

        # Convert main block
        if node.main_block:
            node.main_block.accept(self)

        # Add necessary imports after determining what's needed
        imports = []

        # Check if we need datetime imports
        # TODO: Scan for datetime types

        # Add database imports if SQL statements were found
        if self.has_sql_statements:
            if self.sql_backend == "wbjdbc":
                imports.append(
                    "from fglinterpreter.database.wbjdbc_connector import WBJDBCConnector"
                )
            else:  # wborm
                imports.append("from fglinterpreter.database.wborm_connector import WBORMConnector")
            imports.append("from datetime import datetime")
            imports.append("")
            imports.append("# Initialize database connection")
            imports.append("# TODO: Configure connection parameters")
            imports.append("db = WBJDBCConnector() if True else WBORMConnector()  # Set backend")
            imports.append(
                '# db.connect("jdbc:informix-sqli://localhost:9088/database", "user", "password")'
            )
            imports.append("")

        # Insert imports at the placeholder position
        if imports:
            for _i, imp in enumerate(reversed(imports)):
                self.output.insert(import_placeholder_index, imp)

        return self.get_code()

    def visit_function_def(self, node: FunctionDef) -> None:
        """Convert FunctionDef node to Python function."""
        # Build parameter list
        params = []
        for param in node.parameters:
            if param.data_type:
                # Type-hinted parameter
                py_type = self.map_type(param.data_type)
                params.append(f"{param.name}: {py_type}")
            else:
                params.append(param.name)

        param_str = ", ".join(params) if params else ""

        # Function signature
        return_type = ""
        if node.return_type:
            py_return_type = self.map_type(node.return_type)
            return_type = f" -> {py_return_type}"

        self.emit(f"def {node.name}({param_str}){return_type}:")

        # Function body
        if node.body:
            self.increase_indent()
            for stmt in node.body:
                stmt.accept(self)
            self.decrease_indent()
        else:
            # Empty function needs pass
            self.increase_indent()
            self.emit("pass")
            self.decrease_indent()

    def visit_main_block(self, node: MainBlock) -> None:
        """Convert MainBlock node to Python main function."""
        self.emit("def main() -> None:")
        self.emit('    """Main program entry point."""')

        if node.body:
            self.increase_indent()
            for stmt in node.body:
                stmt.accept(self)
            self.decrease_indent()
        else:
            self.increase_indent()
            self.emit("pass")
            self.decrease_indent()

        self.emit_blank()
        self.emit_blank()
        self.emit('if __name__ == "__main__":')
        self.emit("    main()")

    def visit_define_statement(self, node: DefineStatement) -> None:
        """Convert DEFINE statement to Python variable declarations."""
        # In Python, we can use type annotations
        py_type = self.map_type(node.data_type)

        for var in node.variables:
            # Initialize with default value based on type
            if py_type == "int":
                self.emit(f"{var}: {py_type} = 0")
            elif py_type == "float":
                self.emit(f"{var}: {py_type} = 0.0")
            elif py_type == "str":
                self.emit(f'{var}: {py_type} = ""')
            elif py_type == "bool":
                self.emit(f"{var}: {py_type} = False")
            else:
                self.emit(f"{var}: {py_type} = None")

    def visit_let_statement(self, node: LetStatement) -> None:
        """Convert LET statement to Python assignment."""
        value = node.value.accept(self)
        self.emit(f"{node.variable} = {value}")

    def visit_display_statement(self, node: DisplayStatement) -> None:
        """Convert DISPLAY statement to Python print."""
        if not node.expressions:
            self.emit("print()")
            return

        # Convert each expression
        values = [expr.accept(self) for expr in node.expressions]

        # Join with spaces and use print
        values_str = ", ".join(values)
        self.emit(f"print({values_str})")

    def visit_return_statement(self, node: ReturnStatement) -> None:
        """Convert RETURN statement to Python return."""
        if node.value:
            value = node.value.accept(self)
            self.emit(f"return {value}")
        else:
            self.emit("return")

    def visit_call_statement(self, node: CallStatement) -> None:
        """Convert CALL statement to Python function call."""
        args = [arg.accept(self) for arg in node.arguments]
        args_str = ", ".join(args)
        self.emit(f"{node.function_name}({args_str})")

    def visit_if_statement(self, node: IfStatement) -> None:
        """Convert IF statement to Python if/elif/else."""
        # Main IF condition
        condition = node.condition.accept(self)
        self.emit(f"if {condition}:")

        # Then block
        if node.then_block:
            self.increase_indent()
            for stmt in node.then_block:
                stmt.accept(self)
            self.decrease_indent()
        else:
            self.increase_indent()
            self.emit("pass")
            self.decrease_indent()

        # ELIF blocks
        for elif_condition, elif_block in node.elif_blocks:
            elif_cond = elif_condition.accept(self)
            self.emit(f"elif {elif_cond}:")
            if elif_block:
                self.increase_indent()
                for stmt in elif_block:
                    stmt.accept(self)
                self.decrease_indent()
            else:
                self.increase_indent()
                self.emit("pass")
                self.decrease_indent()

        # ELSE block
        if node.else_block is not None:
            self.emit("else:")
            if node.else_block:
                self.increase_indent()
                for stmt in node.else_block:
                    stmt.accept(self)
                self.decrease_indent()
            else:
                self.increase_indent()
                self.emit("pass")
                self.decrease_indent()

    def visit_for_statement(self, node: ForStatement) -> None:
        """Convert FOR statement to Python for loop."""
        start = node.start_value.accept(self)
        end = node.end_value.accept(self)

        if node.step_value:
            step = node.step_value.accept(self)
            # range is exclusive on the end, so we need to add 1
            self.emit(f"for {node.variable} in range({start}, {end} + 1, {step}):")
        else:
            # range is exclusive on the end, so we need to add 1
            self.emit(f"for {node.variable} in range({start}, {end} + 1):")

        # Loop body
        if node.body:
            self.increase_indent()
            for stmt in node.body:
                stmt.accept(self)
            self.decrease_indent()
        else:
            self.increase_indent()
            self.emit("pass")
            self.decrease_indent()

    def visit_while_statement(self, node: WhileStatement) -> None:
        """Convert WHILE statement to Python while loop."""
        condition = node.condition.accept(self)
        self.emit(f"while {condition}:")

        # Loop body
        if node.body:
            self.increase_indent()
            for stmt in node.body:
                stmt.accept(self)
            self.decrease_indent()
        else:
            self.increase_indent()
            self.emit("pass")
            self.decrease_indent()

    def visit_case_statement(self, node: CaseStatement) -> None:
        """Convert CASE statement to Python if/elif chain."""
        first = True

        for when_clause in node.when_clauses:
            condition = when_clause.condition.accept(self)

            if first:
                self.emit(f"if {condition}:")
                first = False
            else:
                self.emit(f"elif {condition}:")

            if when_clause.statements:
                self.increase_indent()
                for stmt in when_clause.statements:
                    stmt.accept(self)
                self.decrease_indent()
            else:
                self.increase_indent()
                self.emit("pass")
                self.decrease_indent()

        # OTHERWISE block
        if node.otherwise_block is not None:
            self.emit("else:")
            if node.otherwise_block:
                self.increase_indent()
                for stmt in node.otherwise_block:
                    stmt.accept(self)
                self.decrease_indent()
            else:
                self.increase_indent()
                self.emit("pass")
                self.decrease_indent()

    def visit_exit_statement(self, node: ExitStatement) -> None:
        """Convert EXIT statement to Python break."""
        self.emit("break")

    def visit_continue_statement(self, node: ContinueStatement) -> None:
        """Convert CONTINUE statement to Python continue."""
        self.emit("continue")

    # Expression visitors (return string representations)

    def visit_literal(self, node: Literal) -> str:
        """Convert Literal to Python literal."""
        if node.token_type == TokenType.STRING_LITERAL:
            # Escape the string properly
            escaped = str(node.value).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif node.token_type == TokenType.INTEGER_LITERAL:
            return str(node.value)
        elif node.token_type == TokenType.FLOAT_LITERAL:
            return str(node.value)
        elif node.token_type == TokenType.BOOLEAN_LITERAL:
            return "True" if node.value else "False"
        else:
            return str(node.value)

    def visit_identifier(self, node: Identifier) -> str:
        """Convert Identifier to Python identifier."""
        return node.name

    def visit_binary_op(self, node: BinaryOp) -> str:
        """Convert BinaryOp to Python expression."""
        left = node.left.accept(self)
        right = node.right.accept(self)

        # Map operators
        operator_map = {
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.MULTIPLY: "*",
            TokenType.DIVIDE: "/",
            TokenType.POWER: "**",
            TokenType.MODULO: "%",
            TokenType.EQUAL: "==",
            TokenType.NOT_EQUAL: "!=",
            TokenType.LESS_THAN: "<",
            TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_THAN: ">",
            TokenType.GREATER_EQUAL: ">=",
            TokenType.AND: "and",
            TokenType.OR: "or",
        }

        py_operator = operator_map.get(node.operator_type, node.operator)

        return f"({left} {py_operator} {right})"

    def visit_unary_op(self, node: UnaryOp) -> str:
        """Convert UnaryOp to Python expression."""
        operand = node.operand.accept(self)

        operator_map = {
            TokenType.MINUS: "-",
            TokenType.PLUS: "+",
            TokenType.NOT: "not ",
        }

        py_operator = operator_map.get(node.operator_type, node.operator)

        return f"({py_operator}{operand})"

    def visit_function_call(self, node: FunctionCall) -> str:
        """Convert FunctionCall to Python function call."""
        args = [arg.accept(self) for arg in node.arguments]
        args_str = ", ".join(args)
        return f"{node.function_name}({args_str})"

    # Database and advanced features (not yet implemented in Epic 1)
    # These will be fully implemented in Epic 2: Database Integration

    def visit_array_access(self, node: Any) -> str:
        """Convert ArrayAccess to Python array access."""
        # TODO: Implement in Epic 2
        self.emit("# TODO: Array access not yet implemented")
        return "None  # Array access not yet implemented"

    def visit_foreach_statement(self, node: Any) -> None:
        """Convert FOREACH statement."""
        # TODO: Implement in Epic 2
        self.emit("# TODO: FOREACH not yet implemented")
        self.emit("pass")

    def visit_select_statement(self, node: SelectStatement) -> None:
        """Convert SELECT statement using SQL translator.

        Args:
            node: SELECT statement AST node
        """
        self.has_sql_statements = True
        translator = create_sql_translator(
            backend=self.sql_backend,
            indent_level=self.indent_level,
            indent_str=" " * self.indent_size,
        )
        sql_code = translator.translate_select(node)
        for line in sql_code.split("\n"):
            if line.strip():
                self.output.append(line)

    def visit_insert_statement(self, node: InsertStatement) -> None:
        """Convert INSERT statement using SQL translator.

        Args:
            node: INSERT statement AST node
        """
        self.has_sql_statements = True
        translator = create_sql_translator(
            backend=self.sql_backend,
            indent_level=self.indent_level,
            indent_str=" " * self.indent_size,
        )
        sql_code = translator.translate_insert(node)
        for line in sql_code.split("\n"):
            if line.strip():
                self.output.append(line)

    def visit_update_statement(self, node: UpdateStatement) -> None:
        """Convert UPDATE statement using SQL translator.

        Args:
            node: UPDATE statement AST node
        """
        self.has_sql_statements = True
        translator = create_sql_translator(
            backend=self.sql_backend,
            indent_level=self.indent_level,
            indent_str=" " * self.indent_size,
        )
        sql_code = translator.translate_update(node)
        for line in sql_code.split("\n"):
            if line.strip():
                self.output.append(line)

    def visit_delete_statement(self, node: DeleteStatement) -> None:
        """Convert DELETE statement using SQL translator.

        Args:
            node: DELETE statement AST node
        """
        self.has_sql_statements = True
        translator = create_sql_translator(
            backend=self.sql_backend,
            indent_level=self.indent_level,
            indent_str=" " * self.indent_size,
        )
        sql_code = translator.translate_delete(node)
        for line in sql_code.split("\n"):
            if line.strip():
                self.output.append(line)

    def visit_declare_statement(self, node: Any) -> None:
        """Convert DECLARE statement (cursor declaration)."""
        # TODO: Implement in Epic 2 (Database Integration)
        self.emit("# TODO: DECLARE cursor not yet implemented")
        self.emit("pass")

    def visit_open_statement(self, node: Any) -> None:
        """Convert OPEN statement (cursor open)."""
        # TODO: Implement in Epic 2 (Database Integration)
        self.emit("# TODO: OPEN cursor not yet implemented")
        self.emit("pass")

    def visit_close_statement(self, node: Any) -> None:
        """Convert CLOSE statement (cursor close)."""
        # TODO: Implement in Epic 2 (Database Integration)
        self.emit("# TODO: CLOSE cursor not yet implemented")
        self.emit("pass")

    def visit_free_statement(self, node: Any) -> None:
        """Convert FREE statement (cursor free)."""
        # TODO: Implement in Epic 2 (Database Integration)
        self.emit("# TODO: FREE cursor not yet implemented")
        self.emit("pass")

    def visit_database_statement(self, node: Any) -> None:
        """Convert DATABASE statement."""
        self.emit("# TODO: DATABASE statement not yet implemented")
        self.emit("pass")

    def visit_begin_work_statement(self, node: Any) -> None:
        """Convert BEGIN WORK statement."""
        self.emit("# TODO: BEGIN WORK statement not yet implemented")
        self.emit("pass")

    def visit_commit_work_statement(self, node: Any) -> None:
        """Convert COMMIT WORK statement."""
        self.emit("# TODO: COMMIT WORK statement not yet implemented")
        self.emit("pass")

    def visit_rollback_work_statement(self, node: Any) -> None:
        """Convert ROLLBACK WORK statement."""
        self.emit("# TODO: ROLLBACK WORK statement not yet implemented")
        self.emit("pass")


def convert_to_python(ast: Program, indent_size: int = 4, sql_backend: str = "wbjdbc") -> str:
    """Convert 4GL AST to Python code.

    Args:
        ast: The parsed 4GL program AST
        indent_size: Number of spaces per indentation level
        sql_backend: SQL backend to use ("wbjdbc" or "wborm")

    Returns:
        Generated Python code as a string
    """
    generator = PythonCodeGenerator(indent_size=indent_size, sql_backend=sql_backend)
    return ast.accept(generator)
