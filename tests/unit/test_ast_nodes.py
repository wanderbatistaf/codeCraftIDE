"""
Unit tests for AST node definitions.
"""

import pytest

from fglinterpreter.lexer import TokenType
from fglinterpreter.parser import (
    BinaryOp,
    DefineStatement,
    DisplayStatement,
    ForStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    LetStatement,
    Literal,
    MainBlock,
    Parameter,
    Program,
    WhileStatement,
)


@pytest.mark.unit
class TestLiteralNode:
    """Tests for Literal AST node."""

    def test_integer_literal(self) -> None:
        """Test integer literal node."""
        node = Literal(value=42, token_type=TokenType.INTEGER_LITERAL, line=1, column=5)
        assert node.value == 42
        assert node.token_type == TokenType.INTEGER_LITERAL
        assert node.line == 1
        assert node.column == 5

    def test_string_literal(self) -> None:
        """Test string literal node."""
        node = Literal(value="hello", token_type=TokenType.STRING_LITERAL, line=2, column=10)
        assert node.value == "hello"
        assert node.token_type == TokenType.STRING_LITERAL

    def test_boolean_literal(self) -> None:
        """Test boolean literal node."""
        node = Literal(value=True, token_type=TokenType.BOOLEAN_LITERAL, line=1, column=1)
        assert node.value is True

    def test_literal_to_dict(self) -> None:
        """Test converting literal to dictionary."""
        node = Literal(value=42, token_type=TokenType.INTEGER_LITERAL, line=1, column=5)
        d = node.to_dict()
        assert d["type"] == "Literal"
        assert d["value"] == 42
        assert d["line"] == 1
        assert d["column"] == 5


@pytest.mark.unit
class TestIdentifierNode:
    """Tests for Identifier AST node."""

    def test_identifier(self) -> None:
        """Test identifier node."""
        node = Identifier(name="myvar", line=1, column=5)
        assert node.name == "myvar"
        assert node.line == 1
        assert node.column == 5

    def test_identifier_to_dict(self) -> None:
        """Test converting identifier to dictionary."""
        node = Identifier(name="myvar", line=1, column=5)
        d = node.to_dict()
        assert d["type"] == "Identifier"
        assert d["name"] == "myvar"


@pytest.mark.unit
class TestBinaryOpNode:
    """Tests for BinaryOp AST node."""

    def test_binary_op(self) -> None:
        """Test binary operation node."""
        left = Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=1)
        right = Literal(value=20, token_type=TokenType.INTEGER_LITERAL, line=1, column=5)
        node = BinaryOp(
            left=left, operator="+", operator_type=TokenType.PLUS, right=right, line=1, column=3
        )

        assert node.operator == "+"
        assert node.operator_type == TokenType.PLUS
        assert node.left == left
        assert node.right == right

    def test_binary_op_to_dict(self) -> None:
        """Test converting binary op to dictionary."""
        left = Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=1)
        right = Literal(value=20, token_type=TokenType.INTEGER_LITERAL, line=1, column=5)
        node = BinaryOp(
            left=left, operator="+", operator_type=TokenType.PLUS, right=right, line=1, column=3
        )

        d = node.to_dict()
        assert d["type"] == "BinaryOp"
        assert d["operator"] == "+"
        assert d["left"]["type"] == "Literal"
        assert d["right"]["type"] == "Literal"


@pytest.mark.unit
class TestStatementNodes:
    """Tests for statement AST nodes."""

    def test_define_statement(self) -> None:
        """Test DEFINE statement node."""
        node = DefineStatement(
            variables=["x", "y"], data_type="INTEGER", type_params=None, line=1, column=1
        )

        assert node.variables == ["x", "y"]
        assert node.data_type == "INTEGER"
        assert node.type_params is None

    def test_define_statement_with_params(self) -> None:
        """Test DEFINE with type parameters."""
        node = DefineStatement(
            variables=["name"], data_type="CHAR", type_params=[50], line=1, column=1
        )

        assert node.data_type == "CHAR"
        assert node.type_params == [50]

    def test_let_statement(self) -> None:
        """Test LET statement node."""
        value = Literal(value=42, token_type=TokenType.INTEGER_LITERAL, line=1, column=10)
        node = LetStatement(variable="x", value=value, line=1, column=1)

        assert node.variable == "x"
        assert node.value == value

    def test_display_statement(self) -> None:
        """Test DISPLAY statement node."""
        expr = Literal(value="Hello", token_type=TokenType.STRING_LITERAL, line=1, column=10)
        node = DisplayStatement(expressions=[expr], line=1, column=1)

        assert len(node.expressions) == 1
        assert node.expressions[0] == expr


@pytest.mark.unit
class TestControlFlowNodes:
    """Tests for control flow AST nodes."""

    def test_if_statement(self) -> None:
        """Test IF statement node."""
        condition = Literal(value=True, token_type=TokenType.BOOLEAN_LITERAL, line=1, column=5)
        then_stmt = LetStatement(
            variable="x",
            value=Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=2, column=10),
            line=2,
            column=5,
        )

        node = IfStatement(
            condition=condition,
            then_block=[then_stmt],
            elif_blocks=[],
            else_block=None,
            line=1,
            column=1,
        )

        assert node.condition == condition
        assert len(node.then_block) == 1
        assert node.then_block[0] == then_stmt
        assert node.else_block is None

    def test_for_statement(self) -> None:
        """Test FOR statement node."""
        start = Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=10)
        end = Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=15)

        node = ForStatement(
            variable="i",
            start_value=start,
            end_value=end,
            step_value=None,
            body=[],
            line=1,
            column=1,
        )

        assert node.variable == "i"
        assert node.start_value == start
        assert node.end_value == end
        assert node.step_value is None

    def test_while_statement(self) -> None:
        """Test WHILE statement node."""
        condition = BinaryOp(
            left=Identifier(name="x", line=1, column=7),
            operator="<",
            operator_type=TokenType.LESS_THAN,
            right=Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=11),
            line=1,
            column=9,
        )

        node = WhileStatement(condition=condition, body=[], line=1, column=1)

        assert node.condition == condition
        assert len(node.body) == 0


@pytest.mark.unit
class TestFunctionNodes:
    """Tests for function and program AST nodes."""

    def test_parameter(self) -> None:
        """Test Parameter object."""
        param = Parameter(name="x", data_type="INTEGER", line=1, column=15)
        assert param.name == "x"
        assert param.data_type == "INTEGER"

    def test_function_def(self) -> None:
        """Test FunctionDef node."""
        params = [Parameter(name="a", line=1, column=15)]
        body = [
            LetStatement(
                variable="result", value=Identifier(name="a", line=2, column=15), line=2, column=5
            )
        ]

        node = FunctionDef(
            name="test_func", parameters=params, body=body, return_type=None, line=1, column=1
        )

        assert node.name == "test_func"
        assert len(node.parameters) == 1
        assert node.parameters[0].name == "a"
        assert len(node.body) == 1

    def test_main_block(self) -> None:
        """Test MainBlock node."""
        stmt = DisplayStatement(
            expressions=[
                Literal(value="Hello", token_type=TokenType.STRING_LITERAL, line=2, column=13)
            ],
            line=2,
            column=5,
        )

        node = MainBlock(body=[stmt], line=1, column=1)

        assert len(node.body) == 1
        assert node.body[0] == stmt

    def test_program(self) -> None:
        """Test Program node."""
        func = FunctionDef(name="test", parameters=[], body=[], line=1, column=1)

        main = MainBlock(body=[], line=10, column=1)

        node = Program(functions=[func], main_block=main, line=1, column=1)

        assert len(node.functions) == 1
        assert node.functions[0] == func
        assert node.main_block == main


@pytest.mark.unit
class TestFunctionCallNode:
    """Tests for FunctionCall AST node."""

    def test_function_call_no_args(self) -> None:
        """Test function call with no arguments."""
        node = FunctionCall(function_name="test", arguments=[], line=1, column=5)

        assert node.function_name == "test"
        assert len(node.arguments) == 0

    def test_function_call_with_args(self) -> None:
        """Test function call with arguments."""
        arg1 = Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=10)
        arg2 = Identifier(name="x", line=1, column=14)

        node = FunctionCall(function_name="add", arguments=[arg1, arg2], line=1, column=5)

        assert node.function_name == "add"
        assert len(node.arguments) == 2
        assert node.arguments[0] == arg1
        assert node.arguments[1] == arg2
