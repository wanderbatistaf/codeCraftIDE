"""
High-level API for 4GL to Python conversion.

This module provides convenience functions for converting 4GL code to Python.
"""

from ..parser import parse_source
from .converter import convert_to_python
from .formatter import format_python_code


def convert_source(
    source_code: str,
    filename: str = "<string>",
    indent_size: int = 4,
    format_code: bool = True,
    line_length: int = 88,
    sql_backend: str = "wbjdbc",
) -> str:
    """Convert 4GL source code to Python.

    This is a high-level convenience function that:
    1. Parses the 4GL source code
    2. Converts the AST to Python code
    3. Optionally formats the code with black

    Args:
        source_code: The 4GL source code to convert
        filename: The filename for error reporting
        indent_size: Number of spaces per indentation level
        format_code: Whether to format the output with black
        line_length: Maximum line length for formatting (default: 88)
        sql_backend: SQL backend to use ("wbjdbc" or "wborm") (default: "wbjdbc")

    Returns:
        Generated Python code as a string

    Raises:
        LexerError: If there are lexical errors in the source
        ParserError: If there are syntax errors in the source
    """
    # Parse the 4GL source code
    ast = parse_source(source_code, filename=filename)

    # Convert AST to Python code
    python_code = convert_to_python(ast, indent_size=indent_size, sql_backend=sql_backend)

    # Format if requested
    if format_code:
        python_code = format_python_code(python_code, line_length=line_length)

    return python_code
