"""
Code formatting utilities for generated Python code.

This module provides formatting capabilities using black.
"""

import sys
from typing import Optional

try:
    from black import FileMode, format_str

    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False
    FileMode = None  # type: ignore
    format_str = None  # type: ignore


def format_python_code(
    code: str, line_length: int = 88, target_version: Optional[str] = None
) -> str:
    """Format Python code using black.

    Args:
        code: The Python code to format
        line_length: Maximum line length (default: 88, black's default)
        target_version: Python version target (e.g., "py39", "py310")

    Returns:
        Formatted Python code

    Raises:
        ImportError: If black is not installed
        ValueError: If the code cannot be formatted
    """
    if not BLACK_AVAILABLE:
        # Black not available, return code as-is with warning
        print(
            "Warning: black is not installed. Code will not be formatted.",
            file=sys.stderr,
        )
        return code

    try:
        # Configure black mode
        mode = FileMode(line_length=line_length)

        # Format the code
        formatted = format_str(code, mode=mode)

        return formatted

    except Exception as e:
        # If formatting fails, return original code with warning
        print(
            f"Warning: Failed to format code with black: {e}",
            file=sys.stderr,
        )
        return code


def is_black_available() -> bool:
    """Check if black is available for formatting.

    Returns:
        True if black is installed, False otherwise
    """
    return BLACK_AVAILABLE
