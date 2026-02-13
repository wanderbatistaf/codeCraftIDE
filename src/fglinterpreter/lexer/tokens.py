"""
Token definitions for the Informix 4GL lexer.

This module defines all token types and the Token dataclass used throughout
the lexical analysis phase.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    """Enumeration of all token types in Informix 4GL."""

    # Keywords - Control Flow
    MAIN = auto()
    END = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    ELIF = auto()
    FOR = auto()
    TO = auto()
    STEP = auto()
    WHILE = auto()
    CASE = auto()
    WHEN = auto()
    OTHERWISE = auto()
    EXIT = auto()
    CONTINUE = auto()

    # Keywords - Functions and Procedures
    FUNCTION = auto()
    RETURN = auto()
    CALL = auto()

    # Keywords - Variables and Types
    DEFINE = auto()
    LET = auto()
    CONSTANT = auto()
    GLOBALS = auto()
    RECORD = auto()

    # Data Types
    INTEGER = auto()
    SMALLINT = auto()
    DECIMAL = auto()
    MONEY = auto()
    FLOAT = auto()
    SMALLFLOAT = auto()
    DATE = auto()
    DATETIME = auto()
    INTERVAL = auto()
    CHAR = auto()
    VARCHAR = auto()
    NCHAR = auto()
    NVARCHAR = auto()
    TEXT = auto()
    BYTE = auto()
    SERIAL = auto()
    SERIAL8 = auto()
    BIGSERIAL = auto()
    BIGINT = auto()
    INT8 = auto()
    BOOLEAN = auto()

    # Keywords - Database Operations
    DATABASE = auto()
    SELECT = auto()
    INSERT = auto()
    UPDATE = auto()
    DELETE = auto()
    FROM = auto()
    WHERE = auto()
    INTO = auto()
    VALUES = auto()
    SET = auto()
    ORDER = auto()
    BY = auto()
    GROUP = auto()
    HAVING = auto()
    UNION = auto()
    INTERSECT = auto()
    EXCEPT = auto()
    FIRST = auto()
    ASC = auto()
    DESC = auto()
    DISTINCT = auto()

    # Keywords - Cursor Operations
    DECLARE = auto()
    CURSOR = auto()
    OPEN = auto()
    CLOSE = auto()
    FETCH = auto()
    FOREACH = auto()
    FREE = auto()
    USING = auto()  # For parametric cursors: OPEN cursor USING var

    # Keywords - Transaction Control
    BEGIN = auto()
    COMMIT = auto()
    ROLLBACK = auto()
    WORK = auto()

    # Keywords - Display and I/O
    DISPLAY = auto()
    INPUT = auto()
    PROMPT = auto()
    PRINT = auto()

    # Keywords - Other
    AS = auto()
    IS = auto()
    NULL = auto()
    NOT = auto()
    LIKE = auto()
    IN = auto()
    BETWEEN = auto()
    EXISTS = auto()
    ALL = auto()
    ANY = auto()
    SOME = auto()

    # Logical Operators
    AND = auto()
    OR = auto()

    # Operators
    PLUS = auto()  # +
    MINUS = auto()  # -
    MULTIPLY = auto()  # *
    DIVIDE = auto()  # /
    MODULO = auto()  # %
    POWER = auto()  # **
    CONCAT = auto()  # || (string concatenation)

    # Comparison Operators
    EQUAL = auto()  # =
    NOT_EQUAL = auto()  # != or <>
    LESS_THAN = auto()  # <
    GREATER_THAN = auto()  # >
    LESS_EQUAL = auto()  # <=
    GREATER_EQUAL = auto()  # >=

    # Assignment
    ASSIGN = auto()  # LET x = ...

    # Delimiters
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    COMMA = auto()  # ,
    SEMICOLON = auto()  # ;
    COLON = auto()  # :
    DOT = auto()  # .
    AT = auto()  # @
    QUESTION_MARK = auto()  # ? (for parametric queries)

    # Literals
    INTEGER_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOLEAN_LITERAL = auto()

    # Identifiers
    IDENTIFIER = auto()

    # Comments
    COMMENT = auto()

    # Special
    NEWLINE = auto()
    EOF = auto()

    # Error token
    UNKNOWN = auto()


# Mapping of keyword strings to TokenType
KEYWORDS = {
    # Control Flow
    "MAIN": TokenType.MAIN,
    "END": TokenType.END,
    "IF": TokenType.IF,
    "THEN": TokenType.THEN,
    "ELSE": TokenType.ELSE,
    "ELIF": TokenType.ELIF,
    "ELSEIF": TokenType.ELIF,  # Alternative spelling
    "FOR": TokenType.FOR,
    "TO": TokenType.TO,
    "STEP": TokenType.STEP,
    "WHILE": TokenType.WHILE,
    "CASE": TokenType.CASE,
    "WHEN": TokenType.WHEN,
    "OTHERWISE": TokenType.OTHERWISE,
    "EXIT": TokenType.EXIT,
    "CONTINUE": TokenType.CONTINUE,
    # Functions
    "FUNCTION": TokenType.FUNCTION,
    "RETURN": TokenType.RETURN,
    "CALL": TokenType.CALL,
    # Variables
    "DEFINE": TokenType.DEFINE,
    "LET": TokenType.LET,
    "CONSTANT": TokenType.CONSTANT,
    "GLOBALS": TokenType.GLOBALS,
    "RECORD": TokenType.RECORD,
    # Data Types
    "INTEGER": TokenType.INTEGER,
    "INT": TokenType.INTEGER,  # Alias
    "SMALLINT": TokenType.SMALLINT,
    "DECIMAL": TokenType.DECIMAL,
    "DEC": TokenType.DECIMAL,  # Alias
    "MONEY": TokenType.MONEY,
    "FLOAT": TokenType.FLOAT,
    "SMALLFLOAT": TokenType.SMALLFLOAT,
    "REAL": TokenType.SMALLFLOAT,  # Alias
    "DATE": TokenType.DATE,
    "DATETIME": TokenType.DATETIME,
    "INTERVAL": TokenType.INTERVAL,
    "CHAR": TokenType.CHAR,
    "CHARACTER": TokenType.CHAR,  # Alias
    "VARCHAR": TokenType.VARCHAR,
    "NCHAR": TokenType.NCHAR,
    "NVARCHAR": TokenType.NVARCHAR,
    "TEXT": TokenType.TEXT,
    "BYTE": TokenType.BYTE,
    "SERIAL": TokenType.SERIAL,
    "SERIAL8": TokenType.SERIAL8,
    "BIGSERIAL": TokenType.BIGSERIAL,
    "BIGINT": TokenType.BIGINT,
    "INT8": TokenType.INT8,
    "BOOLEAN": TokenType.BOOLEAN,
    "BOOL": TokenType.BOOLEAN,  # Alias
    # Database Operations
    "DATABASE": TokenType.DATABASE,
    "SELECT": TokenType.SELECT,
    "INSERT": TokenType.INSERT,
    "UPDATE": TokenType.UPDATE,
    "DELETE": TokenType.DELETE,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "INTO": TokenType.INTO,
    "VALUES": TokenType.VALUES,
    "SET": TokenType.SET,
    "ORDER": TokenType.ORDER,
    "BY": TokenType.BY,
    "GROUP": TokenType.GROUP,
    "HAVING": TokenType.HAVING,
    "UNION": TokenType.UNION,
    "INTERSECT": TokenType.INTERSECT,
    "EXCEPT": TokenType.EXCEPT,
    "FIRST": TokenType.FIRST,
    "ASC": TokenType.ASC,
    "DESC": TokenType.DESC,
    "DISTINCT": TokenType.DISTINCT,
    # Cursor Operations
    "DECLARE": TokenType.DECLARE,
    "CURSOR": TokenType.CURSOR,
    "OPEN": TokenType.OPEN,
    "CLOSE": TokenType.CLOSE,
    "FETCH": TokenType.FETCH,
    "FOREACH": TokenType.FOREACH,
    "FREE": TokenType.FREE,
    "USING": TokenType.USING,
    # Transaction Control
    "BEGIN": TokenType.BEGIN,
    "COMMIT": TokenType.COMMIT,
    "ROLLBACK": TokenType.ROLLBACK,
    "WORK": TokenType.WORK,
    # Display and I/O
    "DISPLAY": TokenType.DISPLAY,
    "INPUT": TokenType.INPUT,
    "PROMPT": TokenType.PROMPT,
    "PRINT": TokenType.PRINT,
    # Other Keywords
    "AS": TokenType.AS,
    "IS": TokenType.IS,
    "NULL": TokenType.NULL,
    "NOT": TokenType.NOT,
    "LIKE": TokenType.LIKE,
    "IN": TokenType.IN,
    "BETWEEN": TokenType.BETWEEN,
    "EXISTS": TokenType.EXISTS,
    "ALL": TokenType.ALL,
    "ANY": TokenType.ANY,
    "SOME": TokenType.SOME,
    # Logical Operators
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    # Boolean literals
    "TRUE": TokenType.BOOLEAN_LITERAL,
    "FALSE": TokenType.BOOLEAN_LITERAL,
}


@dataclass
class Token:
    """
    Represents a single token in the 4GL source code.

    Attributes:
        type: The type of token (from TokenType enum)
        value: The actual string value from the source code
        line: Line number where the token appears (1-indexed)
        column: Column number where the token starts (1-indexed)
        literal: Optional parsed literal value (e.g., int for INTEGER_LITERAL)
    """

    type: TokenType
    value: str
    line: int
    column: int
    literal: Optional[Any] = None

    def __repr__(self) -> str:
        """String representation for debugging."""
        if self.literal is not None:
            return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column}, literal={self.literal!r})"
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.type.name}({self.value})"

    def is_keyword(self) -> bool:
        """Check if this token is a keyword."""
        return self.value.upper() in KEYWORDS

    def is_operator(self) -> bool:
        """Check if this token is an operator."""
        operator_types = {
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.MODULO,
            TokenType.POWER,
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.AND,
            TokenType.OR,
            TokenType.NOT,
        }
        return self.type in operator_types

    def is_literal(self) -> bool:
        """Check if this token is a literal value."""
        literal_types = {
            TokenType.INTEGER_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.STRING_LITERAL,
            TokenType.BOOLEAN_LITERAL,
        }
        return self.type in literal_types

    def is_delimiter(self) -> bool:
        """Check if this token is a delimiter."""
        delimiter_types = {
            TokenType.LPAREN,
            TokenType.RPAREN,
            TokenType.LBRACKET,
            TokenType.RBRACKET,
            TokenType.LBRACE,
            TokenType.RBRACE,
            TokenType.COMMA,
            TokenType.SEMICOLON,
            TokenType.COLON,
            TokenType.DOT,
        }
        return self.type in delimiter_types
