"""
Enhanced error messages with context-aware suggestions for Informix 4GL.
"""

from typing import Dict, List, Optional


class ErrorHint:
    """Container for enhanced error messages with suggestions."""

    def __init__(
        self,
        original_error: str,
        suggestion: Optional[str] = None,
        examples: Optional[List[str]] = None,
        valid_options: Optional[List[str]] = None,
        tip: Optional[str] = None,
    ):
        self.original_error = original_error
        self.suggestion = suggestion
        self.examples = examples or []
        self.valid_options = valid_options or []
        self.tip = tip

    def format(self) -> str:
        """Format the error with hints for display."""
        lines = [f"❌ {self.original_error}", ""]

        if self.suggestion:
            lines.append(f"💡 {self.suggestion}")
            lines.append("")

        if self.valid_options:
            lines.append("Valid options:")
            for option in self.valid_options:
                lines.append(f"   • {option}")
            lines.append("")

        if self.examples:
            lines.append("Example:")
            for example in self.examples:
                lines.append(f"   {example}")
            lines.append("")

        if self.tip:
            lines.append(f"💭 Tip: {self.tip}")

        return "\n".join(lines)


# Informix 4GL data types reference
VALID_DATA_TYPES = {
    "CHAR": "Fixed-length character string - CHAR(n)",
    "VARCHAR": "Variable-length character string - VARCHAR(n, reserve)",
    "SMALLINT": "Small integer (-32,768 to 32,767)",
    "INTEGER": "Integer (-2,147,483,648 to 2,147,483,647)",
    "DECIMAL": "Decimal number - DECIMAL(p, s)",
    "MONEY": "Money value - MONEY(p, s)",
    "FLOAT": "Double-precision floating point",
    "SMALLFLOAT": "Single-precision floating point",
    "DATE": "Date value (year, month, day)",
    "DATETIME": "Date and time - DATETIME qualifier TO qualifier",
    "INTERVAL": "Time interval - INTERVAL qualifier TO qualifier",
    "BYTE": "Binary large object",
    "TEXT": "Text large object",
    "SERIAL": "Auto-incrementing integer (database only)",
}


# Common mistakes and their corrections
COMMON_TYPE_MISTAKES = {
    "STRING": ("CHAR", ["CHAR(50)", "VARCHAR(255)"]),
    "STR": ("CHAR", ["CHAR(100)", "VARCHAR(100)"]),
    "TEXT": ("CHAR", ["CHAR(255)", "VARCHAR(4096)", "TEXT (for large text)"]),
    "BOOL": ("SMALLINT", ["SMALLINT  -- Use 0 for FALSE, 1 for TRUE"]),
    "BOOLEAN": ("SMALLINT", ["SMALLINT  -- Use 0 for FALSE, 1 for TRUE"]),
    "DOUBLE": ("FLOAT", ["FLOAT", "DECIMAL(10,2)"]),
    "REAL": ("SMALLFLOAT", ["SMALLFLOAT", "FLOAT"]),
    "INT": ("INTEGER", ["INTEGER", "SMALLINT"]),
    "TIMESTAMP": ("DATETIME", ["DATETIME YEAR TO SECOND"]),
}


def get_data_type_hint(invalid_type: str, line: int, column: int) -> ErrorHint:
    """Generate helpful hint for invalid data type."""

    invalid_upper = invalid_type.upper()

    # Check for common mistakes
    if invalid_upper in COMMON_TYPE_MISTAKES:
        correct_type, examples = COMMON_TYPE_MISTAKES[invalid_upper]

        return ErrorHint(
            original_error=f"Invalid data type '{invalid_type}' at line {line}, column {column}",
            suggestion=f"Did you mean '{correct_type}'? In Informix 4GL, '{invalid_type}' is not a valid type.",
            examples=examples,
            valid_options=None,
            tip=f"{correct_type} is the standard Informix 4GL type for this use case.",
        )

    # General invalid type
    return ErrorHint(
        original_error=f"Invalid data type '{invalid_type}' at line {line}, column {column}",
        suggestion="Informix 4GL supports the following data types:",
        valid_options=[f"{k} - {v}" for k, v in VALID_DATA_TYPES.items()],
        examples=["DEFINE name CHAR(50)", "DEFINE age INTEGER", "DEFINE salary DECIMAL(10,2)"],
        tip="Most text data uses CHAR(n) or VARCHAR(n,r). Numbers use INTEGER or DECIMAL.",
    )


def get_missing_main_hint() -> ErrorHint:
    """Hint for missing MAIN block."""
    return ErrorHint(
        original_error="No MAIN block found",
        suggestion="Every 4GL program needs a MAIN block as the entry point.",
        examples=[
            "MAIN",
            "    DEFINE name CHAR(20)",
            "    LET name = 'John'",
            "    DISPLAY 'Hello, ', name",
            "END MAIN",
        ],
        tip="MAIN is like the 'main()' function in C - it's where your program starts.",
    )


def get_missing_end_hint(block_type: str, line: int) -> ErrorHint:
    """Hint for missing END statement."""

    block_examples = {
        "MAIN": ["MAIN", "    -- your code here", "END MAIN"],
        "FUNCTION": ["FUNCTION calculate(x INT) RETURNS INT", "    RETURN x * 2", "END FUNCTION"],
        "IF": ["IF age >= 18 THEN", "    DISPLAY 'Adult'", "END IF"],
        "WHILE": ["WHILE counter < 10", "    LET counter = counter + 1", "END WHILE"],
        "FOR": ["FOR i = 1 TO 10", "    DISPLAY i", "END FOR"],
        "CASE": [
            "CASE",
            "    WHEN age < 18 THEN DISPLAY 'Minor'",
            "    WHEN age >= 18 THEN DISPLAY 'Adult'",
            "END CASE",
        ],
    }

    examples = block_examples.get(
        block_type.upper(), [f"{block_type}", "    -- code", f"END {block_type}"]
    )

    return ErrorHint(
        original_error=f"Missing 'END {block_type}' statement (started at line {line})",
        suggestion=f"Every {block_type} block must be closed with 'END {block_type}'",
        examples=examples,
        tip="In 4GL, blocks are always explicitly closed. Don't forget the END!",
    )


def get_syntax_error_hint(token: str, expected: str, line: int, column: int) -> ErrorHint:
    """Generate contextual hint for syntax errors."""

    # Assignment operator confusion
    if token == "=" and "comparison" in expected.lower():
        return ErrorHint(
            original_error=f"Unexpected '=' at line {line}, column {column}",
            suggestion="For comparisons, use '==' (double equals). Single '=' is only for assignment (LET).",
            examples=[
                "IF age == 18 THEN     -- Comparison (double =)",
                "LET age = 18          -- Assignment (single =)",
            ],
            tip="This is different from SQL where you use single = for both!",
        )

    # Missing LET keyword
    if token in ["IDENTIFIER"] and "LET" in expected:
        return ErrorHint(
            original_error=f"Syntax error at line {line}, column {column}",
            suggestion="To assign a value to a variable, use the LET keyword.",
            examples=["LET name = 'John'", "LET total = price * quantity", "LET found = FALSE"],
            tip="Unlike SQL, 4GL requires LET for assignments (except in INPUT, etc.)",
        )

    # Missing THEN after IF
    if "THEN" in expected.upper():
        return ErrorHint(
            original_error=f"Missing THEN at line {line}, column {column}",
            suggestion="IF statements require THEN after the condition.",
            examples=["IF x > 10 THEN", "    DISPLAY 'Greater'", "END IF"],
            tip="In 4GL, THEN is mandatory - different from some other languages!",
        )

    # Generic syntax error
    return ErrorHint(
        original_error=f"Syntax error at line {line}, column {column}: unexpected '{token}'",
        suggestion=f"Expected: {expected}",
        examples=None,
        valid_options=None,
        tip="Check for missing semicolons, keywords, or incorrect statement order.",
    )


def get_undefined_variable_hint(var_name: str, line: int, available_vars: List[str]) -> ErrorHint:
    """Hint for undefined variable with suggestions."""

    # Find similar variable names (simple Levenshtein-like)
    suggestions = []
    for var in available_vars:
        if var.lower().startswith(var_name[0].lower()):
            suggestions.append(var)
        elif var_name.lower() in var.lower() or var.lower() in var_name.lower():
            suggestions.append(var)

    if suggestions:
        return ErrorHint(
            original_error=f"Undefined variable '{var_name}' at line {line}",
            suggestion="Did you mean one of these?",
            valid_options=suggestions,
            examples=[f"DEFINE {var_name} CHAR(20)  -- If it's a new variable"],
            tip="All variables must be DEFINEd before use in 4GL.",
        )

    return ErrorHint(
        original_error=f"Undefined variable '{var_name}' at line {line}",
        suggestion="This variable has not been declared.",
        examples=[f"DEFINE {var_name} INTEGER", f"LET {var_name} = 100"],
        tip="Variables must be DEFINEd at the start of the block (MAIN/FUNCTION).",
    )


def get_function_error_hint(func_name: str, issue: str) -> ErrorHint:
    """Hint for function-related errors."""

    if issue == "missing_returns":
        return ErrorHint(
            original_error=f"Function '{func_name}' missing RETURNS clause",
            suggestion="Functions that return values must declare their return type.",
            examples=[
                f"FUNCTION {func_name}(x INTEGER) RETURNS INTEGER",
                "    RETURN x * 2",
                "END FUNCTION",
            ],
            tip="Use RETURNS type for functions that return values, omit for procedures.",
        )

    if issue == "missing_return":
        return ErrorHint(
            original_error=f"Function '{func_name}' missing RETURN statement",
            suggestion="Functions with RETURNS must have at least one RETURN statement.",
            examples=[
                f"FUNCTION {func_name}() RETURNS CHAR(10)",
                "    RETURN 'Success'",
                "END FUNCTION",
            ],
            tip="Every code path should return a value of the declared type.",
        )

    return ErrorHint(
        original_error=f"Error in function '{func_name}': {issue}",
        suggestion="Check function syntax and structure.",
        examples=[
            "FUNCTION name(param TYPE) RETURNS TYPE",
            "    -- function body",
            "    RETURN value",
            "END FUNCTION",
        ],
    )


def enhance_error_message(error: Exception, context: Optional[Dict] = None) -> str:
    """
    Enhance any error with contextual hints.

    Args:
        error: The original exception
        context: Optional context dict with keys like 'line', 'column', 'token', etc.

    Returns:
        Formatted error message with hints
    """
    error_msg = str(error)
    context = context or {}

    # Try to extract line/column from error message if not in context
    import re

    if "line" not in context:
        match = re.search(r"line (\d+)", error_msg, re.IGNORECASE)
        if match:
            context["line"] = int(match.group(1))

    if "column" not in context:
        match = re.search(r"column (\d+)", error_msg, re.IGNORECASE)
        if match:
            context["column"] = int(match.group(1))

    # Detect error type and generate appropriate hint
    line = context.get("line", 0)
    column = context.get("column", 0)

    # Invalid data type
    if (
        "data type" in error_msg.lower()
        or "unexpected token: identifier (in expected data type)" in error_msg.lower()
    ):
        # Try to extract the invalid type from error or context
        token = context.get("token", "")
        if not token:
            match = re.search(r"'(\w+)'", error_msg)
            if match:
                token = match.group(1)

        if token:
            hint = get_data_type_hint(token, line, column)
            return hint.format()

    # Missing MAIN
    if "no main" in error_msg.lower() or "main block" in error_msg.lower():
        hint = get_missing_main_hint()
        return hint.format()

    # Missing END
    match = re.search(r"missing.*end\s+(\w+)", error_msg, re.IGNORECASE)
    if match:
        block_type = match.group(1)
        hint = get_missing_end_hint(block_type, line)
        return hint.format()

    # Generic syntax error
    if "syntax error" in error_msg.lower():
        token = context.get("token", "unknown")
        expected = context.get("expected", "valid syntax")
        hint = get_syntax_error_hint(token, expected, line, column)
        return hint.format()

    # Undefined variable
    if "undefined" in error_msg.lower() and "variable" in error_msg.lower():
        var_name = context.get("variable", "")
        available = context.get("available_variables", [])
        if var_name:
            hint = get_undefined_variable_hint(var_name, line, available)
            return hint.format()

    # Return original error if no hint applies
    return f"❌ {error_msg}"
