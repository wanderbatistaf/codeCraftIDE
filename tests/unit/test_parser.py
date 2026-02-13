"""
Unit tests for the Parser class.
"""

import pytest

from fglinterpreter.lexer import Lexer, TokenType
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
    Parser,
    ParserError,
    Program,
    UnexpectedTokenError,
    WhileStatement,
    parse_source,
)


def parse_code(code: str) -> Program:
    """Helper to parse 4GL code."""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


@pytest.mark.unit
class TestParserBasics:
    """Tests for basic parser functionality."""

    def test_empty_main_block(self) -> None:
        """Test parsing empty MAIN block."""
        code = """
        MAIN
        END MAIN
        """
        program = parse_code(code)

        assert program.main_block is not None
        assert len(program.main_block.body) == 0
        assert len(program.functions) == 0

    def test_main_with_display(self) -> None:
        """Test parsing MAIN with DISPLAY statement."""
        code = """
        MAIN
            DISPLAY "Hello, World!"
        END MAIN
        """
        program = parse_code(code)

        assert program.main_block is not None
        assert len(program.main_block.body) == 1

        stmt = program.main_block.body[0]
        assert isinstance(stmt, DisplayStatement)
        assert len(stmt.expressions) == 1
        assert isinstance(stmt.expressions[0], Literal)
        assert stmt.expressions[0].value == "Hello, World!"


@pytest.mark.unit
class TestExpressionParsing:
    """Tests for expression parsing."""

    def test_literal_expression(self) -> None:
        """Test parsing literal expressions."""
        code = """
        MAIN
            LET x = 42
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, Literal)
        assert stmt.value.value == 42

    def test_identifier_expression(self) -> None:
        """Test parsing identifier expressions."""
        code = """
        MAIN
            LET y = x
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, Identifier)
        assert stmt.value.name == "x"

    def test_binary_op_expression(self) -> None:
        """Test parsing binary operation expressions."""
        code = """
        MAIN
            LET result = 10 + 20
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, BinaryOp)
        assert stmt.value.operator == "+"
        assert isinstance(stmt.value.left, Literal)
        assert stmt.value.left.value == 10
        assert isinstance(stmt.value.right, Literal)
        assert stmt.value.right.value == 20

    def test_complex_expression(self) -> None:
        """Test parsing complex expression with operator precedence."""
        code = """
        MAIN
            LET result = 10 + 20 * 30
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, BinaryOp)

        # Should parse as: 10 + (20 * 30) due to precedence
        assert stmt.value.operator == "+"
        assert isinstance(stmt.value.left, Literal)
        assert stmt.value.left.value == 10

        # Right side should be 20 * 30
        right = stmt.value.right
        assert isinstance(right, BinaryOp)
        assert right.operator == "*"

    def test_comparison_expression(self) -> None:
        """Test parsing comparison expressions."""
        code = """
        MAIN
            LET check = x < 10
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, BinaryOp)
        assert stmt.value.operator_type == TokenType.LESS_THAN

    def test_logical_expression(self) -> None:
        """Test parsing logical AND/OR expressions."""
        code = """
        MAIN
            LET check = x < 10 AND y > 5
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, BinaryOp)
        assert stmt.value.operator_type == TokenType.AND

    def test_function_call_expression(self) -> None:
        """Test parsing function call expressions."""
        code = """
        MAIN
            LET result = add(10, 20)
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, FunctionCall)
        assert stmt.value.function_name == "add"
        assert len(stmt.value.arguments) == 2


@pytest.mark.unit
class TestStatementParsing:
    """Tests for statement parsing."""

    def test_define_statement(self) -> None:
        """Test parsing DEFINE statement."""
        code = """
        MAIN
            DEFINE x, y INTEGER
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.variables == ["x", "y"]
        assert stmt.data_type == "INTEGER"

    def test_define_with_params(self) -> None:
        """Test parsing DEFINE with type parameters."""
        code = """
        MAIN
            DEFINE name CHAR(50)
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.data_type == "CHAR"
        assert stmt.type_params == [50]

    def test_let_statement(self) -> None:
        """Test parsing LET statement."""
        code = """
        MAIN
            LET x = 42
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)
        assert stmt.variable == "x"

    def test_display_multiple_expressions(self) -> None:
        """Test parsing DISPLAY with multiple expressions."""
        code = """
        MAIN
            DISPLAY "Value: ", x, " Result: ", y
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, DisplayStatement)
        assert len(stmt.expressions) == 4


@pytest.mark.unit
class TestControlFlowParsing:
    """Tests for control flow statement parsing."""

    def test_if_statement(self) -> None:
        """Test parsing IF statement."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "Less than 10"
            END IF
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, IfStatement)
        assert isinstance(stmt.condition, BinaryOp)
        assert len(stmt.then_block) == 1
        assert stmt.else_block is None

    def test_if_else_statement(self) -> None:
        """Test parsing IF-ELSE statement."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "Less"
            ELSE
                DISPLAY "Greater or equal"
            END IF
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, IfStatement)
        assert len(stmt.then_block) == 1
        assert stmt.else_block is not None
        assert len(stmt.else_block) == 1

    def test_if_elif_else_statement(self) -> None:
        """Test parsing IF-ELIF-ELSE statement."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "Less"
            ELIF x = 10 THEN
                DISPLAY "Equal"
            ELSE
                DISPLAY "Greater"
            END IF
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, IfStatement)
        assert len(stmt.elif_blocks) == 1
        assert stmt.else_block is not None

    def test_for_statement(self) -> None:
        """Test parsing FOR statement."""
        code = """
        MAIN
            FOR i = 1 TO 10
                DISPLAY i
            END FOR
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, ForStatement)
        assert stmt.variable == "i"
        assert isinstance(stmt.start_value, Literal)
        assert stmt.start_value.value == 1
        assert isinstance(stmt.end_value, Literal)
        assert stmt.end_value.value == 10
        assert stmt.step_value is None

    def test_for_statement_with_step(self) -> None:
        """Test parsing FOR statement with STEP."""
        code = """
        MAIN
            FOR i = 0 TO 20 STEP 2
                DISPLAY i
            END FOR
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, ForStatement)
        assert stmt.step_value is not None
        assert isinstance(stmt.step_value, Literal)
        assert stmt.step_value.value == 2

    def test_while_statement(self) -> None:
        """Test parsing WHILE statement."""
        code = """
        MAIN
            WHILE x > 0
                LET x = x - 1
            END WHILE
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, WhileStatement)
        assert isinstance(stmt.condition, BinaryOp)
        assert len(stmt.body) == 1

    def test_nested_control_flow(self) -> None:
        """Test parsing nested control flow."""
        code = """
        MAIN
            FOR i = 1 TO 10
                IF i > 5 THEN
                    DISPLAY "Greater than 5"
                END IF
            END FOR
        END MAIN
        """
        program = parse_code(code)

        for_stmt = program.main_block.body[0]
        assert isinstance(for_stmt, ForStatement)
        assert len(for_stmt.body) == 1

        if_stmt = for_stmt.body[0]
        assert isinstance(if_stmt, IfStatement)


@pytest.mark.unit
class TestFunctionParsing:
    """Tests for function parsing."""

    def test_function_definition(self) -> None:
        """Test parsing function definition."""
        code = """
        FUNCTION add_numbers(a, b)
            RETURN a + b
        END FUNCTION

        MAIN
        END MAIN
        """
        program = parse_code(code)

        assert len(program.functions) == 1

        func = program.functions[0]
        assert isinstance(func, FunctionDef)
        assert func.name == "add_numbers"
        assert len(func.parameters) == 2
        assert func.parameters[0].name == "a"
        assert func.parameters[1].name == "b"

    def test_function_with_body(self) -> None:
        """Test parsing function with body."""
        code = """
        FUNCTION test()
            DEFINE x INTEGER
            LET x = 10
            RETURN x
        END FUNCTION

        MAIN
        END MAIN
        """
        program = parse_code(code)

        func = program.functions[0]
        assert len(func.body) == 3
        assert isinstance(func.body[0], DefineStatement)
        assert isinstance(func.body[1], LetStatement)

    def test_empty_function(self) -> None:
        """Test parsing empty function."""
        code = """
        FUNCTION empty()
        END FUNCTION

        MAIN
        END MAIN
        """
        program = parse_code(code)

        func = program.functions[0]
        assert func.name == "empty"
        assert len(func.parameters) == 0
        assert len(func.body) == 0


@pytest.mark.unit
class TestCompletePrograms:
    """Tests for complete program parsing."""

    def test_simple_complete_program(self, sample_4gl_code: str) -> None:
        """Test parsing a complete simple program."""
        program = parse_code(sample_4gl_code)

        assert program.main_block is not None
        assert len(program.main_block.body) > 0

    def test_program_with_function_and_main(self) -> None:
        """Test parsing program with function and main."""
        code = """
        FUNCTION multiply(a, b)
            RETURN a * b
        END FUNCTION

        MAIN
            DEFINE result INTEGER
            LET result = multiply(5, 10)
            DISPLAY "Result: ", result
        END MAIN
        """
        program = parse_code(code)

        assert len(program.functions) == 1
        assert program.main_block is not None
        assert len(program.main_block.body) == 3

    def test_multiple_functions(self) -> None:
        """Test parsing multiple functions."""
        code = """
        FUNCTION func1()
            RETURN 1
        END FUNCTION

        FUNCTION func2()
            RETURN 2
        END FUNCTION

        MAIN
        END MAIN
        """
        program = parse_code(code)

        assert len(program.functions) == 2
        assert program.functions[0].name == "func1"
        assert program.functions[1].name == "func2"


@pytest.mark.unit
class TestParserErrors:
    """Tests for parser error handling."""

    def test_unexpected_token_error(self) -> None:
        """Test unexpected token error."""
        code = "INVALID TOKEN"

        with pytest.raises(UnexpectedTokenError):
            parse_code(code)

    def test_missing_end_main(self) -> None:
        """Test missing END MAIN error."""
        code = """
        MAIN
            DISPLAY "test"
        """

        with pytest.raises(ParserError):
            parse_code(code)

    def test_missing_then_in_if(self) -> None:
        """Test missing THEN in IF statement."""
        code = """
        MAIN
            IF x < 10
                DISPLAY "test"
            END IF
        END MAIN
        """

        with pytest.raises(ParserError):
            parse_code(code)

    def test_missing_end_if(self) -> None:
        """Test missing END IF error."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "test"
        END MAIN
        """

        with pytest.raises(ParserError):
            parse_code(code)


@pytest.mark.unit
class TestParseSourceFunction:
    """Tests for the parse_source convenience function."""

    def test_parse_source_success(self) -> None:
        """Test parse_source function."""
        code = """
        MAIN
            DISPLAY "test"
        END MAIN
        """

        program = parse_source(code, "test.4gl")

        assert isinstance(program, Program)
        assert program.main_block is not None

    def test_parse_source_with_error(self) -> None:
        """Test parse_source with syntax error."""
        code = "INVALID"

        with pytest.raises(ParserError):
            parse_source(code, "test.4gl")


@pytest.mark.unit
class TestOperatorPrecedence:
    """Tests for operator precedence."""

    def test_addition_multiplication_precedence(self) -> None:
        """Test that multiplication binds tighter than addition."""
        code = """
        MAIN
            LET x = 2 + 3 * 4
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        assert isinstance(stmt, LetStatement)

        # Should parse as: 2 + (3 * 4)
        expr = stmt.value
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.left, Literal)
        assert expr.left.value == 2

        # Right side should be 3 * 4
        right = expr.right
        assert isinstance(right, BinaryOp)
        assert right.operator == "*"
        assert right.left.value == 3
        assert right.right.value == 4

    def test_comparison_arithmetic_precedence(self) -> None:
        """Test that arithmetic binds tighter than comparison."""
        code = """
        MAIN
            LET x = 10 + 5 < 20
        END MAIN
        """
        program = parse_code(code)

        stmt = program.main_block.body[0]
        expr = stmt.value

        # Should parse as: (10 + 5) < 20
        assert isinstance(expr, BinaryOp)
        assert expr.operator_type == TokenType.LESS_THAN

        left = expr.left
        assert isinstance(left, BinaryOp)
        assert left.operator == "+"
