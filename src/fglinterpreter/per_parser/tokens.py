"""
Token definitions for Querix .per form file lexer.
"""

from enum import Enum, auto


class TokenType(Enum):
    """Token types for .per form files."""

    # Keywords
    DATABASE = auto()
    SCREEN = auto()
    TABLES = auto()
    ATTRIBUTES = auto()
    INSTRUCTIONS = auto()
    END = auto()
    FORMONLY = auto()

    # Common keywords in DATABASE directive
    WITHOUT = auto()
    NULL = auto()
    INPUT = auto()

    # Common keywords in INSTRUCTIONS
    DELIMITERS = auto()
    SCREEN_RECORD = auto()

    # Common attribute properties
    UPSHIFT = auto()
    DOWNSHIFT = auto()
    NOENTRY = auto()
    TYPE = auto()
    WIDGET = auto()
    WORDWRAP = auto()
    REQUIRED = auto()

    # Data types (for TYPE property)
    CHAR = auto()
    INTEGER = auto()
    SMALLINT = auto()
    DECIMAL = auto()
    DATE = auto()
    DATETIME = auto()
    MONEY = auto()

    # Symbols
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    EQUALS = auto()  # =
    COMMA = auto()  # ,
    SEMICOLON = auto()  # ;
    DOT = auto()  # .
    COLON = auto()  # :

    # Literals
    IDENTIFIER = auto()  # Variable/field names
    STRING = auto()  # String literals "..."
    NUMBER = auto()  # Numeric literals

    # Layout
    LAYOUT_TEXT = auto()  # Text in SCREEN section (labels, decorations)

    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()  # Comments


class Token:
    """Represents a single token in a .per file."""

    def __init__(
        self,
        type_: TokenType,
        value: str,
        line: int = 0,
        column: int = 0,
    ):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}, {self.column})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value


# Keyword mapping
KEYWORDS = {
    "DATABASE": TokenType.DATABASE,
    "SCREEN": TokenType.SCREEN,
    "TABLES": TokenType.TABLES,
    "ATTRIBUTES": TokenType.ATTRIBUTES,
    "INSTRUCTIONS": TokenType.INSTRUCTIONS,
    "END": TokenType.END,
    "FORMONLY": TokenType.FORMONLY,
    "WITHOUT": TokenType.WITHOUT,
    "NULL": TokenType.NULL,
    "INPUT": TokenType.INPUT,
    "DELIMITERS": TokenType.DELIMITERS,
    "UPSHIFT": TokenType.UPSHIFT,
    "DOWNSHIFT": TokenType.DOWNSHIFT,
    "NOENTRY": TokenType.NOENTRY,
    "TYPE": TokenType.TYPE,
    "WIDGET": TokenType.WIDGET,
    "WORDWRAP": TokenType.WORDWRAP,
    "REQUIRED": TokenType.REQUIRED,
    "CHAR": TokenType.CHAR,
    "INTEGER": TokenType.INTEGER,
    "SMALLINT": TokenType.SMALLINT,
    "DECIMAL": TokenType.DECIMAL,
    "DATE": TokenType.DATE,
    "DATETIME": TokenType.DATETIME,
    "MONEY": TokenType.MONEY,
}
