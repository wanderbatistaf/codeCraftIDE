"""
Unit tests for the Interpreter class.
"""

import pytest

from fglinterpreter.interpreter import (
    DivisionByZeroError,
    ExecutionContext,
    FunctionNotFoundError,
    RuntimeError,
    Scope,
    UndefinedVariableError,
    interpret_source,
)


def run_code(code: str) -> str:
    """Helper to run 4GL code and return output."""
    return interpret_source(code)


@pytest.mark.unit
class TestScope:
    """Tests for Scope class."""

    def test_define_and_get_variable(self) -> None:
        """Test defining and getting variables."""
        scope = Scope()
        scope.define("x", 42)
        assert scope.get("x") == 42

    def test_set_variable(self) -> None:
        """Test setting variable value."""
        scope = Scope()
        scope.define("x", 10)
        scope.set("x", 20)
        assert scope.get("x") == 20

    def test_undefined_variable_error(self) -> None:
        """Test error when accessing undefined variable."""
        scope = Scope()
        with pytest.raises(UndefinedVariableError):
            scope.get("undefined")

    def test_nested_scopes(self) -> None:
        """Test nested scopes."""
        parent = Scope()
        parent.define("x", 10)

        child = Scope(parent)
        child.define("y", 20)

        # Child can see parent's variables
        assert child.get("x") == 10
        assert child.get("y") == 20

        # Parent cannot see child's variables
        assert parent.get("x") == 10
        with pytest.raises(UndefinedVariableError):
            parent.get("y")

    def test_variable_shadowing(self) -> None:
        """Test variable shadowing in nested scopes."""
        parent = Scope()
        parent.define("x", 10)

        child = Scope(parent)
        child.define("x", 20)

        # Child sees its own version
        assert child.get("x") == 20
        # Parent sees its version
        assert parent.get("x") == 10


@pytest.mark.unit
class TestExecutionContext:
    """Tests for ExecutionContext class."""

    def test_push_pop_scope(self) -> None:
        """Test pushing and popping scopes."""
        ctx = ExecutionContext()
        ctx.define_variable("global_var", 100)

        ctx.push_scope()
        ctx.define_variable("local_var", 200)

        assert ctx.get_variable("global_var") == 100
        assert ctx.get_variable("local_var") == 200

        ctx.pop_scope()

        assert ctx.get_variable("global_var") == 100
        with pytest.raises(UndefinedVariableError):
            ctx.get_variable("local_var")

    def test_output_buffer(self) -> None:
        """Test output buffer management."""
        ctx = ExecutionContext()
        ctx.add_output("Hello ")
        ctx.add_output("World\n")

        assert ctx.get_output() == "Hello World\n"

        ctx.clear_output()
        assert ctx.get_output() == ""


@pytest.mark.unit
class TestExpressionEvaluation:
    """Tests for expression evaluation."""

    def test_literal_evaluation(self) -> None:
        """Test evaluating literal expressions."""
        code = """
        MAIN
            DISPLAY 42
            DISPLAY "Hello"
            DISPLAY 3.14
        END MAIN
        """
        output = run_code(code)
        assert "42" in output
        assert "Hello" in output
        assert "3.14" in output

    def test_variable_evaluation(self) -> None:
        """Test evaluating variables."""
        code = """
        MAIN
            DEFINE x INTEGER
            LET x = 100
            DISPLAY x
        END MAIN
        """
        output = run_code(code)
        assert "100" in output

    def test_arithmetic_operations(self) -> None:
        """Test arithmetic operations."""
        code = """
        MAIN
            LET result = 10 + 5
            DISPLAY result
            LET result = 20 - 8
            DISPLAY result
            LET result = 3 * 4
            DISPLAY result
            LET result = 15 / 3
            DISPLAY result
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert "15" in lines[0]
        assert "12" in lines[1]
        assert "12" in lines[2]
        assert "5" in lines[3]

    def test_comparison_operations(self) -> None:
        """Test comparison operations."""
        code = """
        MAIN
            DISPLAY 10 < 20
            DISPLAY 10 > 20
            DISPLAY 10 = 10
            DISPLAY 10 <> 20
        END MAIN
        """
        output = run_code(code)
        assert "TRUE" in output
        assert "FALSE" in output

    def test_logical_operations(self) -> None:
        """Test logical operations."""
        code = """
        MAIN
            LET result = 1 AND 1
            DISPLAY result
            LET result = 1 AND 0
            DISPLAY result
            LET result = 0 OR 1
            DISPLAY result
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert "TRUE" in lines[0]
        assert "FALSE" in lines[1]
        assert "TRUE" in lines[2]

    def test_operator_precedence(self) -> None:
        """Test operator precedence."""
        code = """
        MAIN
            LET result = 2 + 3 * 4
            DISPLAY result
        END MAIN
        """
        output = run_code(code)
        assert "14" in output  # Should be 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20

    def test_division_by_zero(self) -> None:
        """Test division by zero error."""
        code = """
        MAIN
            LET result = 10 / 0
        END MAIN
        """
        with pytest.raises(DivisionByZeroError):
            run_code(code)


@pytest.mark.unit
class TestStatementExecution:
    """Tests for statement execution."""

    def test_define_statement(self) -> None:
        """Test DEFINE statement."""
        code = """
        MAIN
            DEFINE x, y, z INTEGER
            LET x = 1
            LET y = 2
            LET z = 3
            DISPLAY x, y, z
        END MAIN
        """
        output = run_code(code)
        assert "123" in output

    def test_let_statement(self) -> None:
        """Test LET statement."""
        code = """
        MAIN
            LET x = 42
            DISPLAY x
            LET x = 100
            DISPLAY x
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert "42" in lines[0]
        assert "100" in lines[1]

    def test_display_multiple_values(self) -> None:
        """Test DISPLAY with multiple values."""
        code = """
        MAIN
            DISPLAY "The answer is ", 42
        END MAIN
        """
        output = run_code(code)
        assert "The answer is 42" in output


@pytest.mark.unit
class TestControlFlow:
    """Tests for control flow execution."""

    def test_if_statement(self) -> None:
        """Test IF statement."""
        code = """
        MAIN
            LET x = 10
            IF x < 20 THEN
                DISPLAY "Less than 20"
            END IF
        END MAIN
        """
        output = run_code(code)
        assert "Less than 20" in output

    def test_if_else_statement(self) -> None:
        """Test IF-ELSE statement."""
        code = """
        MAIN
            LET x = 30
            IF x < 20 THEN
                DISPLAY "Less"
            ELSE
                DISPLAY "Greater or equal"
            END IF
        END MAIN
        """
        output = run_code(code)
        assert "Greater or equal" in output

    def test_if_elif_else_statement(self) -> None:
        """Test IF-ELIF-ELSE statement."""
        code = """
        MAIN
            LET x = 20
            IF x < 20 THEN
                DISPLAY "Less"
            ELIF x = 20 THEN
                DISPLAY "Equal"
            ELSE
                DISPLAY "Greater"
            END IF
        END MAIN
        """
        output = run_code(code)
        assert "Equal" in output

    def test_for_loop(self) -> None:
        """Test FOR loop."""
        code = """
        MAIN
            FOR i = 1 TO 3
                DISPLAY i
            END FOR
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert "1" in lines[0]
        assert "2" in lines[1]
        assert "3" in lines[2]

    def test_for_loop_with_step(self) -> None:
        """Test FOR loop with STEP."""
        code = """
        MAIN
            FOR i = 0 TO 10 STEP 2
                DISPLAY i
            END FOR
        END MAIN
        """
        output = run_code(code)
        assert "0" in output
        assert "2" in output
        assert "4" in output
        assert "6" in output
        assert "8" in output
        assert "10" in output

    def test_while_loop(self) -> None:
        """Test WHILE loop."""
        code = """
        MAIN
            LET x = 3
            WHILE x > 0
                DISPLAY x
                LET x = x - 1
            END WHILE
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert "3" in lines[0]
        assert "2" in lines[1]
        assert "1" in lines[2]

    def test_nested_loops(self) -> None:
        """Test nested loops."""
        code = """
        MAIN
            FOR i = 1 TO 2
                FOR j = 1 TO 2
                    DISPLAY i, " ", j
                END FOR
            END FOR
        END MAIN
        """
        output = run_code(code)
        assert "1 1" in output
        assert "1 2" in output
        assert "2 1" in output
        assert "2 2" in output

    def test_exit_loop(self) -> None:
        """Test EXIT statement."""
        code = """
        MAIN
            FOR i = 1 TO 10
                DISPLAY i
                IF i = 3 THEN
                    EXIT FOR
                END IF
            END FOR
        END MAIN
        """
        output = run_code(code)
        lines = output.strip().split("\n")
        assert len(lines) == 3  # Should stop at 3
        assert "1" in lines[0]
        assert "2" in lines[1]
        assert "3" in lines[2]

    def test_continue_loop(self) -> None:
        """Test CONTINUE statement."""
        code = """
        MAIN
            FOR i = 1 TO 5
                IF i = 3 THEN
                    CONTINUE FOR
                END IF
                DISPLAY i
            END FOR
        END MAIN
        """
        output = run_code(code)
        assert "1" in output
        assert "2" in output
        assert "3" not in output.replace("15", "")  # Skip 3
        assert "4" in output
        assert "5" in output

    def test_case_statement(self) -> None:
        """Test CASE statement."""
        code = """
        MAIN
            LET x = 2
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
        output = run_code(code)
        assert "Two" in output


@pytest.mark.unit
class TestFunctions:
    """Tests for function execution."""

    def test_function_definition_and_call(self) -> None:
        """Test function definition and calling."""
        code = """
        FUNCTION add(a, b)
            RETURN a + b
        END FUNCTION

        MAIN
            LET result = add(10, 20)
            DISPLAY result
        END MAIN
        """
        output = run_code(code)
        assert "30" in output

    def test_function_with_multiple_statements(self) -> None:
        """Test function with multiple statements."""
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
            DISPLAY factorial(5)
        END MAIN
        """
        output = run_code(code)
        assert "120" in output  # 5! = 120

    def test_function_scope(self) -> None:
        """Test that function parameters are scoped."""
        code = """
        FUNCTION test(x)
            LET x = 999
            RETURN x
        END FUNCTION

        MAIN
            LET x = 1
            LET result = test(100)
            DISPLAY x, " ", result
        END MAIN
        """
        output = run_code(code)
        assert "1 999" in output

    def test_recursive_function(self) -> None:
        """Test recursive function."""
        code = """
        FUNCTION fib(n)
            IF n <= 1 THEN
                RETURN n
            ELSE
                RETURN fib(n - 1) + fib(n - 2)
            END IF
        END FUNCTION

        MAIN
            DISPLAY fib(7)
        END MAIN
        """
        output = run_code(code)
        assert "13" in output  # fib(7) = 13

    def test_function_not_found_error(self) -> None:
        """Test error when calling undefined function."""
        code = """
        MAIN
            LET result = undefined_function(10)
        END MAIN
        """
        with pytest.raises(FunctionNotFoundError):
            run_code(code)

    def test_call_statement(self) -> None:
        """Test CALL statement (procedure call)."""
        code = """
        FUNCTION print_message(msg)
            DISPLAY msg
        END FUNCTION

        MAIN
            CALL print_message("Hello from procedure")
        END MAIN
        """
        output = run_code(code)
        assert "Hello from procedure" in output


@pytest.mark.unit
class TestCompletePrograms:
    """Tests for complete program execution."""

    def test_simple_program(self, sample_4gl_code: str) -> None:
        """Test running a simple complete program."""
        output = run_code(sample_4gl_code)
        assert len(output) > 0

    def test_variables_and_conditionals_example(self) -> None:
        """Test variables and conditionals example."""
        code = """
        MAIN
            DEFINE x, y INTEGER

            LET x = 10
            LET y = 20

            IF x < y THEN
                DISPLAY "x is less than y"
            ELSE
                DISPLAY "x is greater than or equal to y"
            END IF
        END MAIN
        """
        output = run_code(code)
        assert "x is less than y" in output

    def test_loops_example(self) -> None:
        """Test loops example."""
        code = """
        MAIN
            DEFINE i INTEGER

            FOR i = 1 TO 3
                DISPLAY "Count: ", i
            END FOR
        END MAIN
        """
        output = run_code(code)
        assert "Count: 1" in output
        assert "Count: 2" in output
        assert "Count: 3" in output

    def test_function_example(self) -> None:
        """Test function example."""
        code = """
        FUNCTION multiply(a, b)
            RETURN a * b
        END FUNCTION

        MAIN
            DEFINE result INTEGER
            LET result = multiply(6, 7)
            DISPLAY "6 * 7 = ", result
        END MAIN
        """
        output = run_code(code)
        assert "6 * 7 = 42" in output


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling."""

    def test_undefined_variable(self) -> None:
        """Test undefined variable error."""
        code = """
        MAIN
            DISPLAY undefined_var
        END MAIN
        """
        with pytest.raises(UndefinedVariableError):
            run_code(code)

    def test_runtime_error_includes_location(self) -> None:
        """Test that runtime errors include location information."""
        code = """
        MAIN
            DISPLAY undefined_var
        END MAIN
        """
        try:
            run_code(code)
            pytest.fail("Should have raised UndefinedVariableError")
        except UndefinedVariableError as e:
            error_msg = str(e)
            assert "line" in error_msg.lower()


@pytest.mark.unit
class TestInterpretSourceFunction:
    """Tests for the interpret_source convenience function."""

    def test_interpret_source_success(self) -> None:
        """Test interpret_source function."""
        code = """
        MAIN
            DISPLAY "test"
        END MAIN
        """
        output = interpret_source(code, "test.4gl")
        assert "test" in output

    def test_interpret_source_with_error(self) -> None:
        """Test interpret_source with runtime error."""
        code = """
        MAIN
            DISPLAY undefined
        END MAIN
        """
        with pytest.raises(RuntimeError):
            interpret_source(code, "test.4gl")
