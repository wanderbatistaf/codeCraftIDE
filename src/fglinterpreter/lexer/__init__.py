"""
Lexer and tokenizer for Informix 4GL.

This module provides:
- Token definitions (TokenType enum, Token dataclass)
- Lexer implementation for tokenizing 4GL source code
- Exception classes for lexical errors
"""

from .exceptions import (
    InvalidCharacterError,
    InvalidNumberError,
    LexerError,
    UnterminatedStringError,
)
from .lexer import Lexer
from .tokens import KEYWORDS, Token, TokenType

__all__ = [
    # Main classes
    "Lexer",
    "Token",
    "TokenType",
    "KEYWORDS",
    # Exceptions
    "LexerError",
    "InvalidCharacterError",
    "InvalidNumberError",
    "UnterminatedStringError",
]
