"""
Lexer implementation for Informix 4GL.

This module provides the Lexer class that performs lexical analysis
(tokenization) of 4GL source code.
"""

from typing import List, Optional

from .exceptions import (
    InvalidCharacterError,
    InvalidNumberError,
    UnterminatedStringError,
)
from .tokens import KEYWORDS, Token, TokenType


class Lexer:
    """
    Lexical analyzer for Informix 4GL source code.

    The lexer converts raw source code into a stream of tokens,
    preserving position information and handling errors gracefully.
    """

    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        """
        Initialize the lexer with source code.

        Args:
            source: The 4GL source code to tokenize
            filename: Name of the source file (for error messages)
        """
        self.source = source
        self.filename = filename
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

        # Split source into lines for error reporting
        self.lines = source.split("\n")

    def current_char(self) -> Optional[str]:
        """Get the current character without advancing position."""
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        """
        Look ahead at a character without advancing position.

        Args:
            offset: How many characters to look ahead (default 1)

        Returns:
            The character at position + offset, or None if out of bounds
        """
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self) -> Optional[str]:
        """
        Move to the next character and return it.

        Returns:
            The character that was at the current position before advancing
        """
        if self.position >= len(self.source):
            return None

        char = self.source[self.position]
        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def skip_whitespace(self) -> None:
        """Skip whitespace characters (spaces, tabs, but not newlines)."""
        while self.current_char() and self.current_char() in " \t\r":
            self.advance()

    def skip_comment(self) -> None:
        """Skip single-line comments (starting with # or --)."""
        char = self.current_char()

        if char == "#":
            # Skip until end of line
            while self.current_char() and self.current_char() != "\n":
                self.advance()

        elif char == "-" and self.peek_char() == "-":
            # Skip -- style comments
            self.advance()  # First -
            self.advance()  # Second -
            while self.current_char() and self.current_char() != "\n":
                self.advance()

    def read_string(self, quote_char: str) -> str:
        """
        Read a string literal enclosed in quotes.

        Args:
            quote_char: The opening quote character (' or ")

        Returns:
            The string content (without quotes)

        Raises:
            UnterminatedStringError: If the string is not properly closed
        """
        start_line = self.line
        start_column = self.column - 1
        result = []

        # Skip opening quote
        self.advance()

        while True:
            char = self.current_char()

            if char is None or char == "\n":
                # Unterminated string
                source_line = self.lines[start_line - 1] if start_line <= len(self.lines) else ""
                raise UnterminatedStringError(start_line, start_column, source_line)

            if char == quote_char:
                # Check for escaped quote (double quote)
                if self.peek_char() == quote_char:
                    result.append(quote_char)
                    self.advance()  # First quote
                    self.advance()  # Second quote
                else:
                    # End of string
                    self.advance()  # Closing quote
                    break

            elif char == "\\":
                # Handle escape sequences
                self.advance()
                next_char = self.current_char()

                if next_char is None:
                    source_line = (
                        self.lines[start_line - 1] if start_line <= len(self.lines) else ""
                    )
                    raise UnterminatedStringError(start_line, start_column, source_line)

                # Common escape sequences
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }

                result.append(escape_map.get(next_char, next_char))
                self.advance()

            else:
                result.append(char)
                self.advance()

        return "".join(result)

    def read_number(self) -> Token:
        """
        Read a numeric literal (integer or float).

        Returns:
            Token with type INTEGER_LITERAL or FLOAT_LITERAL

        Raises:
            InvalidNumberError: If the number format is invalid
        """
        start_line = self.line
        start_column = self.column
        num_str = []
        is_float = False

        # Read digits before decimal point
        while self.current_char() and self.current_char().isdigit():
            num_str.append(self.current_char())
            self.advance()

        # Check for decimal point
        if self.current_char() == "." and self.peek_char() and self.peek_char().isdigit():
            is_float = True
            num_str.append(self.current_char())
            self.advance()

            # Read digits after decimal point
            while self.current_char() and self.current_char().isdigit():
                num_str.append(self.current_char())
                self.advance()

        # Check for scientific notation (e or E)
        if self.current_char() and self.current_char() in "eE":
            is_float = True
            num_str.append(self.current_char())
            self.advance()

            # Optional sign
            if self.current_char() and self.current_char() in "+-":
                num_str.append(self.current_char())
                self.advance()

            # Exponent digits
            if not self.current_char() or not self.current_char().isdigit():
                source_line = self.lines[start_line - 1] if start_line <= len(self.lines) else ""
                raise InvalidNumberError(
                    "Invalid exponent in number", start_line, start_column, source_line
                )

            while self.current_char() and self.current_char().isdigit():
                num_str.append(self.current_char())
                self.advance()

        value_str = "".join(num_str)

        try:
            if is_float:
                literal_value = float(value_str)
                return Token(
                    TokenType.FLOAT_LITERAL, value_str, start_line, start_column, literal_value
                )
            else:
                literal_value = int(value_str)
                return Token(
                    TokenType.INTEGER_LITERAL, value_str, start_line, start_column, literal_value
                )
        except ValueError as e:
            source_line = self.lines[start_line - 1] if start_line <= len(self.lines) else ""
            raise InvalidNumberError(str(e), start_line, start_column, source_line)

    def read_identifier(self) -> Token:
        """
        Read an identifier or keyword.

        Returns:
            Token with type IDENTIFIER or a keyword TokenType
        """
        start_line = self.line
        start_column = self.column
        chars = []

        # First character (letter or underscore)
        chars.append(self.current_char())
        self.advance()

        # Remaining characters (letters, digits, underscores)
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == "_"):
            chars.append(self.current_char())
            self.advance()

        value = "".join(chars)
        value_upper = value.upper()

        # Check if it's a keyword
        if value_upper in KEYWORDS:
            token_type = KEYWORDS[value_upper]
            # Special handling for boolean literals
            if token_type == TokenType.BOOLEAN_LITERAL:
                literal_value = value_upper == "TRUE"
                return Token(token_type, value, start_line, start_column, literal_value)
            return Token(token_type, value, start_line, start_column)

        # It's an identifier
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)

    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire source code.

        Returns:
            List of tokens including an EOF token at the end

        Raises:
            LexerError: If any lexical errors are encountered
        """
        self.tokens = []

        while self.position < len(self.source):
            self.skip_whitespace()

            char = self.current_char()

            if char is None:
                break

            # Skip newlines and track them
            if char == "\n":
                self.advance()
                continue

            # Comments
            if char == "#" or (char == "-" and self.peek_char() == "-"):
                self.skip_comment()
                continue

            # String literals
            if char in "\"'":
                start_line = self.line
                start_column = self.column
                quote_char = char
                string_value = self.read_string(quote_char)
                token = Token(
                    TokenType.STRING_LITERAL, string_value, start_line, start_column, string_value
                )
                self.tokens.append(token)
                continue

            # Numbers
            if char.isdigit():
                token = self.read_number()
                self.tokens.append(token)
                continue

            # Identifiers and keywords
            if char.isalpha() or char == "_":
                token = self.read_identifier()
                self.tokens.append(token)
                continue

            # Operators and delimiters
            start_line = self.line
            start_column = self.column

            # Two-character operators
            two_char = char + (self.peek_char() or "")

            if two_char == "<=":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LESS_EQUAL, "<=", start_line, start_column))
                continue

            if two_char == ">=":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GREATER_EQUAL, ">=", start_line, start_column))
                continue

            if two_char == "<>" or two_char == "!=":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NOT_EQUAL, two_char, start_line, start_column))
                continue

            if two_char == "**":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.POWER, "**", start_line, start_column))
                continue

            if two_char == "||":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.CONCAT, "||", start_line, start_column))
                continue

            # Single-character operators and delimiters
            single_char_tokens = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.MULTIPLY,
                "/": TokenType.DIVIDE,
                "%": TokenType.MODULO,
                "=": TokenType.EQUAL,
                "<": TokenType.LESS_THAN,
                ">": TokenType.GREATER_THAN,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ",": TokenType.COMMA,
                ";": TokenType.SEMICOLON,
                ":": TokenType.COLON,
                ".": TokenType.DOT,
                "@": TokenType.AT,
                "?": TokenType.QUESTION_MARK,
            }

            if char in single_char_tokens:
                token_type = single_char_tokens[char]
                self.advance()
                self.tokens.append(Token(token_type, char, start_line, start_column))
                continue

            # Unknown character
            source_line = self.lines[start_line - 1] if start_line <= len(self.lines) else ""
            raise InvalidCharacterError(char, start_line, start_column, source_line)

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))

        return self.tokens

    def get_tokens(self) -> List[Token]:
        """
        Get the list of tokens (tokenize if not already done).

        Returns:
            List of tokens
        """
        if not self.tokens:
            self.tokenize()
        return self.tokens
