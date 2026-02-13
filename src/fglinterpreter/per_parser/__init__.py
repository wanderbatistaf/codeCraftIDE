"""
Parser for Querix .per form files.

This module provides:
- Lexer for tokenizing .per files
- Parser for building AST from tokens
- AST node definitions for form structure
- Utilities for form rendering and validation
"""

from .ast_nodes import (
    AttributesSection,
    DatabaseDirective,
    FieldAttribute,
    FormASTNode,
    FormDefinition,
    InstructionsSection,
    ScreenField,
    ScreenLine,
    ScreenSection,
)
from .lexer import PerLexer, tokenize_per_file
from .parser import PerParser, parse_per_file
from .serializer import serialize_form_definition
from .tokens import KEYWORDS, Token, TokenType

__all__ = [
    # Main functions
    "parse_per_file",
    "tokenize_per_file",
    "serialize_form_definition",
    # Classes
    "PerLexer",
    "PerParser",
    # AST Nodes
    "FormASTNode",
    "ScreenField",
    "ScreenLine",
    "ScreenSection",
    "FieldAttribute",
    "AttributesSection",
    "InstructionsSection",
    "DatabaseDirective",
    "FormDefinition",
    # Tokens
    "Token",
    "TokenType",
    "KEYWORDS",
]
