"""
Unit tests for the Converter module.
"""

import pytest

from fglinterpreter.converter import convert_source, convert_to_python
from fglinterpreter.parser import parse_source


def convert_code(code: str) -> str:
    """Helper to convert 4GL code to Python."""
    return convert_source(code, format_code=False)


@pytest.mark.unit
class TestBasicConversion:
    """Tests for basic conversion functionality."""

    def test_empty_main_block(self) -> None:
        """Test converting empty MAIN block."""
        code = """
        MAIN
        END MAIN
        """
        python_code = convert_code(code)

        assert "def main()" in python_code
        assert "pass" in python_code
        assert 'if __name__ == "__main__":' in python_code
        assert "main()" in python_code

    def test_simple_display(self) -> None:
        """Test converting simple DISPLAY statement."""
        code = """
        MAIN
            DISPLAY "Hello, World!"
        END MAIN
        """
        python_code = convert_code(code)

        assert "def main()" in python_code
        assert 'print("Hello, World!")' in python_code

    def test_multiple_displays(self) -> None:
        """Test converting multiple DISPLAY statements."""
        code = """
        MAIN
            DISPLAY "Line 1"
            DISPLAY "Line 2"
        END MAIN
        """
        python_code = convert_code(code)

        assert 'print("Line 1")' in python_code
        assert 'print("Line 2")' in python_code


@pytest.mark.unit
class TestVariableConversion:
    """Tests for variable-related conversion."""

    def test_define_integer(self) -> None:
        """Test converting DEFINE statement with INTEGER."""
        code = """
        MAIN
            DEFINE x INTEGER
        END MAIN
        """
        python_code = convert_code(code)

        assert "x: int = 0" in python_code

    def test_define_multiple_variables(self) -> None:
        """Test converting DEFINE with multiple variables."""
        code = """
        MAIN
            DEFINE x, y, z INTEGER
        END MAIN
        """
        python_code = convert_code(code)

        assert "x: int = 0" in python_code
        assert "y: int = 0" in python_code
        assert "z: int = 0" in python_code

    def test_define_string(self) -> None:
        """Test converting DEFINE statement with CHAR."""
        code = """
        MAIN
            DEFINE name CHAR(50)
        END MAIN
        """
        python_code = convert_code(code)

        assert 'name: str = ""' in python_code

    def test_define_float(self) -> None:
        """Test converting DEFINE statement with FLOAT."""
        code = """
        MAIN
            DEFINE price FLOAT
        END MAIN
        """
        python_code = convert_code(code)

        assert "price: float = 0.0" in python_code

    def test_let_statement(self) -> None:
        """Test converting LET statement."""
        code = """
        MAIN
            LET x = 42
        END MAIN
        """
        python_code = convert_code(code)

        assert "x = 42" in python_code

    def test_let_with_expression(self) -> None:
        """Test converting LET with expression."""
        code = """
        MAIN
            LET result = 10 + 20
        END MAIN
        """
        python_code = convert_code(code)

        assert "result = (10 + 20)" in python_code


@pytest.mark.unit
class TestExpressionConversion:
    """Tests for expression conversion."""

    def test_integer_literal(self) -> None:
        """Test converting integer literals."""
        code = """
        MAIN
            LET x = 42
        END MAIN
        """
        python_code = convert_code(code)

        assert "x = 42" in python_code

    def test_string_literal(self) -> None:
        """Test converting string literals."""
        code = """
        MAIN
            LET msg = "Hello"
        END MAIN
        """
        python_code = convert_code(code)

        assert 'msg = "Hello"' in python_code

    def test_float_literal(self) -> None:
        """Test converting float literals."""
        code = """
        MAIN
            LET pi = 3.14
        END MAIN
        """
        python_code = convert_code(code)

        assert "pi = 3.14" in python_code

    def test_arithmetic_operations(self) -> None:
        """Test converting arithmetic operations."""
        code = """
        MAIN
            LET a = 10 + 5
            LET b = 10 - 5
            LET c = 10 * 5
            LET d = 10 / 5
        END MAIN
        """
        python_code = convert_code(code)

        assert "a = (10 + 5)" in python_code
        assert "b = (10 - 5)" in python_code
        assert "c = (10 * 5)" in python_code
        assert "d = (10 / 5)" in python_code

    def test_comparison_operations(self) -> None:
        """Test converting comparison operations."""
        code = """
        MAIN
            LET a = 10 < 20
            LET b = 10 > 20
            LET c = 10 = 20
            LET d = 10 <> 20
        END MAIN
        """
        python_code = convert_code(code)

        assert "a = (10 < 20)" in python_code
        assert "b = (10 > 20)" in python_code
        assert "c = (10 == 20)" in python_code
        assert "d = (10 != 20)" in python_code

    def test_logical_operations(self) -> None:
        """Test converting logical operations."""
        code = """
        MAIN
            LET a = 1 AND 1
            LET b = 0 OR 1
        END MAIN
        """
        python_code = convert_code(code)

        assert "a = (1 and 1)" in python_code
        assert "b = (0 or 1)" in python_code

    def test_identifier_expression(self) -> None:
        """Test converting identifier expressions."""
        code = """
        MAIN
            LET y = x
        END MAIN
        """
        python_code = convert_code(code)

        assert "y = x" in python_code


@pytest.mark.unit
class TestControlFlowConversion:
    """Tests for control flow conversion."""

    def test_if_statement(self) -> None:
        """Test converting IF statement."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "Less than 10"
            END IF
        END MAIN
        """
        python_code = convert_code(code)

        assert "if (x < 10):" in python_code
        assert 'print("Less than 10")' in python_code

    def test_if_else_statement(self) -> None:
        """Test converting IF-ELSE statement."""
        code = """
        MAIN
            IF x < 10 THEN
                DISPLAY "Less"
            ELSE
                DISPLAY "Greater or equal"
            END IF
        END MAIN
        """
        python_code = convert_code(code)

        assert "if (x < 10):" in python_code
        assert 'print("Less")' in python_code
        assert "else:" in python_code
        assert 'print("Greater or equal")' in python_code

    def test_if_elif_else_statement(self) -> None:
        """Test converting IF-ELIF-ELSE statement."""
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
        python_code = convert_code(code)

        assert "if (x < 10):" in python_code
        assert "elif (x == 10):" in python_code
        assert "else:" in python_code

    def test_for_loop(self) -> None:
        """Test converting FOR loop."""
        code = """
        MAIN
            FOR i = 1 TO 10
                DISPLAY i
            END FOR
        END MAIN
        """
        python_code = convert_code(code)

        assert "for i in range(1, 10 + 1):" in python_code
        assert "print(i)" in python_code

    def test_for_loop_with_step(self) -> None:
        """Test converting FOR loop with STEP."""
        code = """
        MAIN
            FOR i = 0 TO 10 STEP 2
                DISPLAY i
            END FOR
        END MAIN
        """
        python_code = convert_code(code)

        assert "for i in range(0, 10 + 1, 2):" in python_code

    def test_while_loop(self) -> None:
        """Test converting WHILE loop."""
        code = """
        MAIN
            WHILE x > 0
                LET x = x - 1
            END WHILE
        END MAIN
        """
        python_code = convert_code(code)

        assert "while (x > 0):" in python_code
        assert "x = (x - 1)" in python_code

    def test_case_statement(self) -> None:
        """Test converting CASE statement."""
        code = """
        MAIN
            CASE
                WHEN x = 1
                    DISPLAY "One"
                WHEN x = 2
                    DISPLAY "Two"
                OTHERWISE
                    DISPLAY "Other"
            END CASE
        END MAIN
        """
        python_code = convert_code(code)

        assert "if (x == 1):" in python_code
        assert 'print("One")' in python_code
        assert "elif (x == 2):" in python_code
        assert 'print("Two")' in python_code
        assert "else:" in python_code
        assert 'print("Other")' in python_code

    def test_exit_statement(self) -> None:
        """Test converting EXIT statement."""
        code = """
        MAIN
            FOR i = 1 TO 10
                IF i = 5 THEN
                    EXIT FOR
                END IF
            END FOR
        END MAIN
        """
        python_code = convert_code(code)

        assert "break" in python_code

    def test_continue_statement(self) -> None:
        """Test converting CONTINUE statement."""
        code = """
        MAIN
            FOR i = 1 TO 10
                IF i = 5 THEN
                    CONTINUE FOR
                END IF
            END FOR
        END MAIN
        """
        python_code = convert_code(code)

        assert "continue" in python_code


@pytest.mark.unit
class TestFunctionConversion:
    """Tests for function conversion."""

    def test_function_definition(self) -> None:
        """Test converting function definition."""
        code = """
        FUNCTION add(a, b)
            RETURN a + b
        END FUNCTION

        MAIN
        END MAIN
        """
        python_code = convert_code(code)

        assert "def add(a, b):" in python_code
        assert "return (a + b)" in python_code

    def test_function_with_body(self) -> None:
        """Test converting function with body."""
        code = """
        FUNCTION test()
            DEFINE x INTEGER
            LET x = 10
            RETURN x
        END FUNCTION

        MAIN
        END MAIN
        """
        python_code = convert_code(code)

        assert "def test():" in python_code
        assert "x: int = 0" in python_code
        assert "x = 10" in python_code
        assert "return x" in python_code

    def test_empty_function(self) -> None:
        """Test converting empty function."""
        code = """
        FUNCTION empty()
        END FUNCTION

        MAIN
        END MAIN
        """
        python_code = convert_code(code)

        assert "def empty():" in python_code
        assert "pass" in python_code

    def test_function_call(self) -> None:
        """Test converting function call."""
        code = """
        MAIN
            LET result = add(10, 20)
        END MAIN
        """
        python_code = convert_code(code)

        assert "result = add(10, 20)" in python_code

    def test_call_statement(self) -> None:
        """Test converting CALL statement."""
        code = """
        MAIN
            CALL print_message("Hello")
        END MAIN
        """
        python_code = convert_code(code)

        assert 'print_message("Hello")' in python_code

    def test_return_without_value(self) -> None:
        """Test converting RETURN without value."""
        code = """
        FUNCTION test()
            RETURN
        END FUNCTION

        MAIN
        END MAIN
        """
        python_code = convert_code(code)

        assert "return" in python_code


@pytest.mark.unit
class TestCompletePrograms:
    """Tests for complete program conversion."""

    def test_simple_complete_program(self, sample_4gl_code: str) -> None:
        """Test converting a complete simple program."""
        python_code = convert_code(sample_4gl_code)

        # Should have valid Python structure
        assert "def main()" in python_code
        assert 'if __name__ == "__main__":' in python_code

    def test_program_with_function_and_main(self) -> None:
        """Test converting program with function and main."""
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
        python_code = convert_code(code)

        assert "def multiply(a, b):" in python_code
        assert "return (a * b)" in python_code
        assert "def main()" in python_code
        assert "result: int = 0" in python_code
        assert "result = multiply(5, 10)" in python_code
        assert 'print("Result: ", result)' in python_code

    def test_complex_program(self) -> None:
        """Test converting complex program with multiple features."""
        code = """
        FUNCTION factorial(n)
            DEFINE result, i INTEGER
            LET result = 1
            FOR i = 1 TO n
                LET result = result * i
            END FOR
            RETURN result
        END FUNCTION

        MAIN
            DEFINE x, fact INTEGER
            LET x = 5
            LET fact = factorial(x)
            DISPLAY "Factorial of ", x, " is ", fact
        END MAIN
        """
        python_code = convert_code(code)

        # Function definition
        assert "def factorial(n):" in python_code
        assert "result: int = 0" in python_code
        assert "i: int = 0" in python_code
        assert "for i in range(1, n + 1):" in python_code

        # Main block
        assert "def main()" in python_code
        assert "x: int = 0" in python_code
        assert "fact: int = 0" in python_code
        assert "fact = factorial(x)" in python_code


@pytest.mark.unit
class TestCodeFormatting:
    """Tests for code formatting."""

    def test_format_with_black(self) -> None:
        """Test formatting code with black."""
        code = """
        MAIN
            DISPLAY "Test"
        END MAIN
        """
        # Try with formatting enabled
        python_code = convert_source(code, format_code=True)

        # Should contain valid Python
        assert "def main()" in python_code
        assert 'if __name__ == "__main__":' in python_code

    def test_no_format_option(self) -> None:
        """Test disabling code formatting."""
        code = """
        MAIN
            DISPLAY "Test"
        END MAIN
        """
        # Format disabled
        python_code = convert_source(code, format_code=False)

        # Should still be valid Python
        assert "def main()" in python_code


@pytest.mark.unit
class TestTypeMapping:
    """Tests for type mapping."""

    def test_integer_types(self) -> None:
        """Test mapping integer types."""
        code = """
        MAIN
            DEFINE x INTEGER
            DEFINE y SMALLINT
            DEFINE z INT
        END MAIN
        """
        python_code = convert_code(code)

        assert "x: int = 0" in python_code
        assert "y: int = 0" in python_code
        assert "z: int = 0" in python_code

    def test_float_types(self) -> None:
        """Test mapping float types."""
        code = """
        MAIN
            DEFINE a FLOAT
            DEFINE b DECIMAL
            DEFINE c SMALLFLOAT
            DEFINE d MONEY
        END MAIN
        """
        python_code = convert_code(code)

        assert "a: float = 0.0" in python_code
        assert "b: float = 0.0" in python_code
        assert "c: float = 0.0" in python_code
        assert "d: float = 0.0" in python_code

    def test_string_types(self) -> None:
        """Test mapping string types."""
        code = """
        MAIN
            DEFINE a CHAR(10)
            DEFINE b VARCHAR(100)
        END MAIN
        """
        python_code = convert_code(code)

        assert 'a: str = ""' in python_code
        assert 'b: str = ""' in python_code


@pytest.mark.unit
class TestConvertToApiFunction:
    """Tests for convert_to_python and convert_source API."""

    def test_convert_to_python_function(self) -> None:
        """Test convert_to_python function."""
        code = """
        MAIN
            DISPLAY "Test"
        END MAIN
        """
        ast = parse_source(code)
        python_code = convert_to_python(ast)

        assert "def main()" in python_code
        assert 'print("Test")' in python_code

    def test_convert_source_function(self) -> None:
        """Test convert_source function."""
        code = """
        MAIN
            DISPLAY "Test"
        END MAIN
        """
        python_code = convert_source(code, filename="test.4gl")

        assert "def main()" in python_code
        assert 'print("Test")' in python_code
