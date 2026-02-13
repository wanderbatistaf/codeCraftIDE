"""
Lexer for Querix .per form files.
"""

from typing import List

from .tokens import KEYWORDS, Token, TokenType


class PerLexer:
    """
    Lexer for .per form files.
    Tokenizes the input text into a sequence of tokens.
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[0] if text else None
        self.in_screen_section = False

    def error(self, message: str):
        raise Exception(f"Lexer error at line {self.line}, column {self.column}: {message}")

    def advance(self):
        """Move to the next character in the input."""
        if self.current_char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def peek(self, offset: int = 1) -> str:
        """Look ahead at the next character without consuming it."""
        peek_pos = self.pos + offset
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        """Skip whitespace characters except newlines."""
        while self.current_char is not None and self.current_char in " \t\r":
            self.advance()

    def skip_comment(self):
        """Skip comments (# or -- to end of line)."""
        if self.current_char in "#":
            while self.current_char is not None and self.current_char != "\n":
                self.advance()
        elif self.current_char == "-" and self.peek() == "-":
            while self.current_char is not None and self.current_char != "\n":
                self.advance()

    def skip_block_comment(self):
        """Skip block comments {...} that appear before keywords."""
        if self.current_char != "{":
            return False

        # Look ahead to see if this is a comment block (contains * or comment text)
        # Save position to restore if not a comment
        saved_pos = self.pos
        saved_line = self.line
        saved_col = self.column

        self.advance()  # Skip {

        # Skip whitespace and check for comment indicators
        while self.current_char in " \t\r\n":
            self.advance()

        # If next char is * or letter (comment text), treat as block comment
        if self.current_char == "*" or (self.current_char and self.current_char.isalpha()):
            # It's a comment block, skip until closing }
            brace_count = 1
            while self.current_char is not None and brace_count > 0:
                if self.current_char == "{":
                    brace_count += 1
                elif self.current_char == "}":
                    brace_count -= 1
                self.advance()
            return True
        else:
            # Not a comment, restore position
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_col
            self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
            return False

    def read_string(self) -> str:
        """Read a string literal enclosed in double quotes."""
        result = ""
        quote_char = self.current_char
        self.advance()  # Skip opening quote

        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == "\\":
                self.advance()
                if self.current_char is not None:
                    result += self.current_char
                    self.advance()
            else:
                result += self.current_char
                self.advance()

        if self.current_char != quote_char:
            self.error("Unterminated string literal")

        self.advance()  # Skip closing quote
        return result

    def read_identifier(self) -> str:
        """Read an identifier or keyword."""
        result = ""
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char in "_"
        ):
            result += self.current_char
            self.advance()
        return result

    def read_number(self) -> str:
        """Read a numeric literal."""
        result = ""
        has_dot = False

        while self.current_char is not None and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            if self.current_char == ".":
                if has_dot:
                    break
                has_dot = True
            result += self.current_char
            self.advance()

        return result

    def read_screen_line(self) -> str:
        """
        Read a line of screen layout text in the SCREEN section.
        This preserves all characters including spaces for layout.
        """
        result = ""
        while self.current_char is not None and self.current_char != "\n":
            result += self.current_char
            self.advance()
        return result

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input and return a list of tokens."""
        tokens = []

        while self.current_char is not None:
            # Skip whitespace
            if self.current_char in " \t\r":
                self.skip_whitespace()
                continue

            # Handle newlines
            if self.current_char == "\n":
                tokens.append(Token(TokenType.NEWLINE, "\\n", self.line, self.column))
                self.advance()
                continue

            # Skip comments
            if self.current_char in "#" or (self.current_char == "-" and self.peek() == "-"):
                self.skip_comment()
                continue

            line = self.line
            column = self.column

            # String literals
            if self.current_char in "\"'":
                value = self.read_string()
                tokens.append(Token(TokenType.STRING, value, line, column))
                continue

            # Numbers
            if self.current_char.isdigit():
                value = self.read_number()
                tokens.append(Token(TokenType.NUMBER, value, line, column))
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                value = self.read_identifier()
                token_type = KEYWORDS.get(value.upper(), TokenType.IDENTIFIER)

                # Track when we enter/exit SCREEN section
                if token_type == TokenType.SCREEN:
                    self.in_screen_section = True
                elif token_type == TokenType.END and self.in_screen_section:
                    self.in_screen_section = False

                tokens.append(Token(token_type, value, line, column))
                continue

            # Check for block comments {...} before treating { as LBRACE
            if self.current_char == "{" and not self.in_screen_section:
                if self.skip_block_comment():
                    continue

            # Single-character tokens
            single_char_tokens = {
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "=": TokenType.EQUALS,
                ",": TokenType.COMMA,
                ";": TokenType.SEMICOLON,
                ".": TokenType.DOT,
                ":": TokenType.COLON,
            }

            if self.current_char in single_char_tokens:
                # Special handling for RBRACE - it might end SCREEN section
                if self.current_char == "}" and self.in_screen_section:
                    # Check if next non-whitespace is END
                    saved_pos = self.pos
                    saved_line = self.line
                    saved_col = self.column
                    saved_char = self.current_char

                    self.advance()
                    self.skip_whitespace()
                    if self.current_char == "\n":
                        self.advance()
                        self.skip_whitespace()

                    # Look ahead for END keyword
                    if self.current_char and self.current_char.isalpha():
                        peek_word = self.read_identifier()
                        if peek_word.upper() == "END":
                            # Don't consume, let normal parsing handle it
                            self.pos = saved_pos
                            self.line = saved_line
                            self.column = saved_col
                            self.current_char = saved_char
                        else:
                            # Reset
                            self.pos = saved_pos
                            self.line = saved_line
                            self.column = saved_col
                            self.current_char = saved_char
                    else:
                        # Reset
                        self.pos = saved_pos
                        self.line = saved_line
                        self.column = saved_col
                        self.current_char = saved_char

                token_type = single_char_tokens[self.current_char]
                tokens.append(Token(token_type, self.current_char, line, column))
                self.advance()
                continue

            # Layout text with special characters (like \g)
            if self.current_char == "\\" and self.peek() == "g":
                tokens.append(Token(TokenType.LAYOUT_TEXT, "\\g", line, column))
                self.advance()
                self.advance()
                continue

            # If we're in the SCREEN section, treat unknown characters as layout text
            if self.in_screen_section:
                # Read characters that are part of layout (not field markers or braces)
                layout_chars = ""
                while (
                    self.current_char is not None
                    and self.current_char not in "{}[]\n"
                    and not (self.current_char == "\\" and self.peek() == "g")
                ):
                    layout_chars += self.current_char
                    self.advance()

                if layout_chars:
                    tokens.append(Token(TokenType.LAYOUT_TEXT, layout_chars, line, column))
                    continue

            # If we get here, it's an unexpected character
            self.error(f"Unexpected character: {self.current_char!r}")

        # Add EOF token
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens


def tokenize_per_file(text: str) -> List[Token]:
    """Convenience function to tokenize a .per file."""
    lexer = PerLexer(text)
    return lexer.tokenize()
