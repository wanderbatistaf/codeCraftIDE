"""
Exception classes for parsing errors.

This module defines custom exceptions for syntax errors encountered
during parsing of 4GL source code.
"""

from typing import List, Optional

from ..error_hints import enhance_error_message
from ..lexer import Token, TokenType


class ParserError(Exception):
    """Base exception for all parser-related errors."""

    def __init__(
        self,
        message: str,
        token: Optional[Token] = None,
        expected: Optional[List[TokenType]] = None,
    ) -> None:
        """
        Initialize a parser error.

        Args:
            message: Description of the error
            token: The token where the error occurred (optional)
            expected: List of expected token types (optional)
        """
        self.message = message
        self.token = token
        self.expected = expected
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format the error message with context."""
        if self.token:
            error_msg = f"Syntax error at line {self.token.line}, column {self.token.column}: "
            error_msg += self.message

            if self.expected:
                expected_str = ", ".join(t.name for t in self.expected)
                error_msg += f"\nExpected: {expected_str}"
                error_msg += f"\nGot: {self.token.type.name} ({self.token.value!r})"
        else:
            error_msg = f"Syntax error: {self.message}"

        # Enhance error message with context-aware hints
        context = {}
        if self.token:
            context["line"] = self.token.line
            context["column"] = self.token.column
            context["token"] = self.token.value
        if self.expected:
            context["expected"] = ", ".join(t.name for t in self.expected)

        return enhance_error_message(Exception(error_msg), context)


class UnexpectedTokenError(ParserError):
    """Raised when an unexpected token is encountered."""

    def __init__(
        self, token: Token, expected: Optional[List[TokenType]] = None, context: str = ""
    ) -> None:
        message = f"Unexpected token: {token.type.name}"
        if context:
            message += f" (in {context})"
        super().__init__(message, token, expected)


class UnexpectedEOFError(ParserError):
    """Raised when EOF is reached unexpectedly."""

    def __init__(self, expected: Optional[List[TokenType]] = None, context: str = "") -> None:
        message = "Unexpected end of file"
        if context:
            message += f" while parsing {context}"
        super().__init__(message, expected=expected)


class MissingTokenError(ParserError):
    """Raised when a required token is missing."""

    def __init__(self, expected: TokenType, token: Optional[Token] = None) -> None:
        message = f"Missing required token: {expected.name}"
        super().__init__(message, token, [expected])


class InvalidSyntaxError(ParserError):
    """Raised for invalid syntax constructs."""

    def __init__(self, message: str, token: Optional[Token] = None) -> None:
        super().__init__(message, token)
