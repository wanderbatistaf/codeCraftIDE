"""
Exception classes for lexical analysis errors.

This module defines custom exceptions that can be raised during tokenization
to provide clear error messages with context.
"""


class LexerError(Exception):
    """Base exception for all lexer-related errors."""

    def __init__(self, message: str, line: int, column: int, source_line: str = "") -> None:
        """
        Initialize a lexer error.

        Args:
            message: Description of the error
            line: Line number where the error occurred (1-indexed)
            column: Column number where the error occurred (1-indexed)
            source_line: The actual source code line (optional, for better error messages)
        """
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format the error message with context."""
        error_msg = f"Lexical error at line {self.line}, column {self.column}: {self.message}"

        if self.source_line:
            # Add the source line and a pointer to the error location
            error_msg += f"\n\n  {self.source_line}"
            error_msg += f"\n  {' ' * (self.column - 1)}^"

        return error_msg


class UnterminatedStringError(LexerError):
    """Raised when a string literal is not properly closed."""

    def __init__(self, line: int, column: int, source_line: str = "") -> None:
        super().__init__("Unterminated string literal", line, column, source_line)


class InvalidCharacterError(LexerError):
    """Raised when an invalid character is encountered."""

    def __init__(self, char: str, line: int, column: int, source_line: str = "") -> None:
        super().__init__(f"Invalid character: {char!r}", line, column, source_line)


class InvalidNumberError(LexerError):
    """Raised when a number literal is malformed."""

    def __init__(self, message: str, line: int, column: int, source_line: str = "") -> None:
        super().__init__(f"Invalid number: {message}", line, column, source_line)
