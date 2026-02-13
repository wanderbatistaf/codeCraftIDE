"""
Unit tests for the Lexer class.
"""

import pytest

from fglinterpreter.lexer import (
    InvalidCharacterError,
    Lexer,
    TokenType,
    UnterminatedStringError,
)


@pytest.mark.unit
class TestLexerBasics:
    """Tests for basic lexer functionality."""

    def test_empty_source(self) -> None:
        """Test lexing empty source code."""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self) -> None:
        """Test lexing whitespace-only source."""
        lexer = Lexer("   \t  \n  ")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_single_keyword(self) -> None:
        """Test lexing a single keyword."""
        lexer = Lexer("MAIN")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # MAIN + EOF
        assert tokens[0].type == TokenType.MAIN
        assert tokens[0].value == "MAIN"
        assert tokens[1].type == TokenType.EOF

    def test_multiple_keywords(self) -> None:
        """Test lexing multiple keywords."""
        lexer = Lexer("MAIN END IF THEN ELSE")
        tokens = lexer.tokenize()
        assert len(tokens) == 6  # 5 keywords + EOF
        assert tokens[0].type == TokenType.MAIN
        assert tokens[1].type == TokenType.END
        assert tokens[2].type == TokenType.IF
        assert tokens[3].type == TokenType.THEN
        assert tokens[4].type == TokenType.ELSE

    def test_case_insensitive_keywords(self) -> None:
        """Test that keywords are case-insensitive."""
        lexer = Lexer("main Main MAIN MaIn")
        tokens = lexer.tokenize()
        for i in range(4):
            assert tokens[i].type == TokenType.MAIN


@pytest.mark.unit
class TestLexerIdentifiers:
    """Tests for identifier tokenization."""

    def test_simple_identifier(self) -> None:
        """Test lexing a simple identifier."""
        lexer = Lexer("myvar")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # identifier + EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "myvar"

    def test_identifier_with_underscores(self) -> None:
        """Test identifier with underscores."""
        lexer = Lexer("my_var_name")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "my_var_name"

    def test_identifier_with_numbers(self) -> None:
        """Test identifier with numbers."""
        lexer = Lexer("var123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "var123"

    def test_identifier_starting_with_underscore(self) -> None:
        """Test identifier starting with underscore."""
        lexer = Lexer("_private")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "_private"


@pytest.mark.unit
class TestLexerNumbers:
    """Tests for number literal tokenization."""

    def test_integer_literal(self) -> None:
        """Test lexing integer literals."""
        lexer = Lexer("42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.INTEGER_LITERAL
        assert tokens[0].value == "42"
        assert tokens[0].literal == 42

    def test_multiple_integers(self) -> None:
        """Test lexing multiple integers."""
        lexer = Lexer("10 20 30")
        tokens = lexer.tokenize()
        assert tokens[0].literal == 10
        assert tokens[1].literal == 20
        assert tokens[2].literal == 30

    def test_float_literal(self) -> None:
        """Test lexing float literals."""
        lexer = Lexer("3.14")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.FLOAT_LITERAL
        assert tokens[0].value == "3.14"
        assert tokens[0].literal == 3.14

    def test_float_with_leading_zero(self) -> None:
        """Test float with leading zero."""
        lexer = Lexer("0.5")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.FLOAT_LITERAL
        assert tokens[0].literal == 0.5

    def test_scientific_notation(self) -> None:
        """Test scientific notation."""
        lexer = Lexer("1.5e10")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.FLOAT_LITERAL
        assert tokens[0].literal == 1.5e10

    def test_scientific_notation_with_sign(self) -> None:
        """Test scientific notation with positive/negative exponent."""
        lexer = Lexer("2.5e+3 1.5e-2")
        tokens = lexer.tokenize()
        assert tokens[0].literal == 2.5e3
        assert tokens[1].literal == 1.5e-2

    def test_large_integer(self) -> None:
        """Test large integer literal."""
        lexer = Lexer("1234567890")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.INTEGER_LITERAL
        assert tokens[0].literal == 1234567890


@pytest.mark.unit
class TestLexerStrings:
    """Tests for string literal tokenization."""

    def test_double_quoted_string(self) -> None:
        """Test double-quoted string."""
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].literal == "hello world"

    def test_single_quoted_string(self) -> None:
        """Test single-quoted string."""
        lexer = Lexer("'hello world'")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].literal == "hello world"

    def test_empty_string(self) -> None:
        """Test empty string literal."""
        lexer = Lexer('""')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].literal == ""

    def test_string_with_escaped_quotes(self) -> None:
        """Test string with escaped quotes."""
        lexer = Lexer(r'"He said \"hello\""')
        tokens = lexer.tokenize()
        assert tokens[0].literal == 'He said "hello"'

    def test_string_with_escape_sequences(self) -> None:
        """Test string with escape sequences."""
        lexer = Lexer(r'"line1\nline2\ttabbed"')
        tokens = lexer.tokenize()
        assert tokens[0].literal == "line1\nline2\ttabbed"

    def test_string_with_double_quotes_escaped(self) -> None:
        """Test 4GL-style double quote escaping."""
        lexer = Lexer("'It''s a test'")
        tokens = lexer.tokenize()
        assert tokens[0].literal == "It's a test"

    def test_unterminated_string_error(self) -> None:
        """Test that unterminated strings raise an error."""
        lexer = Lexer('"unterminated')
        with pytest.raises(UnterminatedStringError) as exc_info:
            lexer.tokenize()
        assert "Unterminated string" in str(exc_info.value)
        assert exc_info.value.line == 1


@pytest.mark.unit
class TestLexerOperators:
    """Tests for operator tokenization."""

    def test_arithmetic_operators(self) -> None:
        """Test arithmetic operators."""
        lexer = Lexer("+ - * / %")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PLUS
        assert tokens[1].type == TokenType.MINUS
        assert tokens[2].type == TokenType.MULTIPLY
        assert tokens[3].type == TokenType.DIVIDE
        assert tokens[4].type == TokenType.MODULO

    def test_comparison_operators(self) -> None:
        """Test comparison operators."""
        lexer = Lexer("< > <= >= = <>")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LESS_THAN
        assert tokens[1].type == TokenType.GREATER_THAN
        assert tokens[2].type == TokenType.LESS_EQUAL
        assert tokens[3].type == TokenType.GREATER_EQUAL
        assert tokens[4].type == TokenType.EQUAL
        assert tokens[5].type == TokenType.NOT_EQUAL

    def test_not_equal_variants(self) -> None:
        """Test different not-equal operators."""
        lexer = Lexer("!= <>")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NOT_EQUAL
        assert tokens[1].type == TokenType.NOT_EQUAL

    def test_power_operator(self) -> None:
        """Test power operator."""
        lexer = Lexer("**")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.POWER
        assert tokens[0].value == "**"


@pytest.mark.unit
class TestLexerDelimiters:
    """Tests for delimiter tokenization."""

    def test_parentheses(self) -> None:
        """Test parentheses."""
        lexer = Lexer("()")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_brackets(self) -> None:
        """Test brackets."""
        lexer = Lexer("[]")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LBRACKET
        assert tokens[1].type == TokenType.RBRACKET

    def test_braces(self) -> None:
        """Test braces."""
        lexer = Lexer("{}")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LBRACE
        assert tokens[1].type == TokenType.RBRACE

    def test_comma_semicolon_colon(self) -> None:
        """Test comma, semicolon, and colon."""
        lexer = Lexer(", ; :")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.COMMA
        assert tokens[1].type == TokenType.SEMICOLON
        assert tokens[2].type == TokenType.COLON

    def test_dot(self) -> None:
        """Test dot delimiter."""
        lexer = Lexer(".")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DOT


@pytest.mark.unit
class TestLexerComments:
    """Tests for comment handling."""

    def test_hash_comment(self) -> None:
        """Test # style comments."""
        lexer = Lexer("# This is a comment\nMAIN")
        tokens = lexer.tokenize()
        # Comments should be skipped
        assert len(tokens) == 2  # MAIN + EOF
        assert tokens[0].type == TokenType.MAIN

    def test_double_dash_comment(self) -> None:
        """Test -- style comments."""
        lexer = Lexer("-- This is a comment\nMAIN")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # MAIN + EOF
        assert tokens[0].type == TokenType.MAIN

    def test_inline_comment(self) -> None:
        """Test inline comments."""
        lexer = Lexer("MAIN # comment here\nEND")
        tokens = lexer.tokenize()
        assert len(tokens) == 3  # MAIN + END + EOF
        assert tokens[0].type == TokenType.MAIN
        assert tokens[1].type == TokenType.END

    def test_comment_at_end(self) -> None:
        """Test comment at end of file."""
        lexer = Lexer("MAIN\n# Final comment")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # MAIN + EOF


@pytest.mark.unit
class TestLexerPositions:
    """Tests for line and column tracking."""

    def test_single_line_positions(self) -> None:
        """Test column positions on a single line."""
        lexer = Lexer("MAIN END")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].line == 1
        assert tokens[1].column == 6  # "MAIN " is 5 chars, END starts at 6

    def test_multi_line_positions(self) -> None:
        """Test line and column positions across multiple lines."""
        source = "MAIN\n  IF x THEN\n    DISPLAY\n  END IF\nEND MAIN"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # MAIN on line 1
        assert tokens[0].type == TokenType.MAIN
        assert tokens[0].line == 1

        # IF on line 2
        if_token = next(t for t in tokens if t.type == TokenType.IF)
        assert if_token.line == 2

        # DISPLAY on line 3
        display_token = next(t for t in tokens if t.type == TokenType.DISPLAY)
        assert display_token.line == 3


@pytest.mark.unit
class TestLexerErrors:
    """Tests for error handling."""

    def test_invalid_character_error(self) -> None:
        """Test invalid character error."""
        lexer = Lexer("MAIN \\ END")
        with pytest.raises(InvalidCharacterError) as exc_info:
            lexer.tokenize()
        assert "Invalid character" in str(exc_info.value)
        assert "\\" in str(exc_info.value)

    def test_error_includes_line_number(self) -> None:
        """Test that errors include line numbers."""
        lexer = Lexer("MAIN\nEND\n\\")
        with pytest.raises(InvalidCharacterError) as exc_info:
            lexer.tokenize()
        assert exc_info.value.line == 3

    def test_error_includes_column_number(self) -> None:
        """Test that errors include column numbers."""
        lexer = Lexer("MAIN  \\")
        with pytest.raises(InvalidCharacterError) as exc_info:
            lexer.tokenize()
        assert exc_info.value.column == 7

    def test_unterminated_string_multiline(self) -> None:
        """Test unterminated string error with newline."""
        lexer = Lexer('"unterminated\nMAIN')
        with pytest.raises(UnterminatedStringError):
            lexer.tokenize()


@pytest.mark.unit
class TestLexerComplexCode:
    """Tests for complex code tokenization."""

    def test_simple_4gl_program(self, sample_4gl_code: str) -> None:
        """Test lexing a complete simple 4GL program."""
        lexer = Lexer(sample_4gl_code)
        tokens = lexer.tokenize()

        # Check for key tokens
        token_types = [t.type for t in tokens]
        assert TokenType.MAIN in token_types
        assert TokenType.DEFINE in token_types
        assert TokenType.LET in token_types
        assert TokenType.IF in token_types
        assert TokenType.DISPLAY in token_types
        assert TokenType.END in token_types
        assert TokenType.EOF in token_types

    def test_variable_assignment(self) -> None:
        """Test lexing variable assignment."""
        source = "LET x = 10"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.LET
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "x"
        assert tokens[2].type == TokenType.EQUAL
        assert tokens[3].type == TokenType.INTEGER_LITERAL
        assert tokens[3].literal == 10

    def test_arithmetic_expression(self) -> None:
        """Test lexing arithmetic expressions."""
        source = "x = 10 + 20 * 30 / 5 - 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[1].type == TokenType.EQUAL
        assert tokens[2].type == TokenType.INTEGER_LITERAL
        assert tokens[3].type == TokenType.PLUS
        assert tokens[4].type == TokenType.INTEGER_LITERAL
        assert tokens[5].type == TokenType.MULTIPLY

    def test_function_declaration(self) -> None:
        """Test lexing function declaration."""
        source = "FUNCTION add_numbers(a, b)\n  RETURN a + b\nEND FUNCTION"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        token_types = [t.type for t in tokens]
        assert TokenType.FUNCTION in token_types
        assert TokenType.IDENTIFIER in token_types
        assert TokenType.LPAREN in token_types
        assert TokenType.COMMA in token_types
        assert TokenType.RPAREN in token_types
        assert TokenType.RETURN in token_types

    def test_sql_statement(self) -> None:
        """Test lexing SQL statement."""
        source = "SELECT name FROM customers WHERE id = 1"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.SELECT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[2].type == TokenType.FROM
        assert tokens[3].type == TokenType.IDENTIFIER
        assert tokens[4].type == TokenType.WHERE

    def test_display_with_string(self) -> None:
        """Test lexing DISPLAY statement with string."""
        source = 'DISPLAY "Hello, World!"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.DISPLAY
        assert tokens[1].type == TokenType.STRING_LITERAL
        assert tokens[1].literal == "Hello, World!"


@pytest.mark.unit
class TestLexerEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_adjacent_operators(self) -> None:
        """Test adjacent operators without spaces."""
        lexer = Lexer("x<=y")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[1].type == TokenType.LESS_EQUAL
        assert tokens[2].type == TokenType.IDENTIFIER

    def test_number_followed_by_identifier(self) -> None:
        """Test that numbers and identifiers are properly separated."""
        lexer = Lexer("123abc")
        tokens = lexer.tokenize()
        # Should be tokenized as: 123, abc
        assert tokens[0].type == TokenType.INTEGER_LITERAL
        assert tokens[0].literal == 123
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "abc"

    def test_get_tokens_method(self) -> None:
        """Test get_tokens method."""
        lexer = Lexer("MAIN")
        tokens1 = lexer.get_tokens()
        tokens2 = lexer.get_tokens()
        # Should return the same tokens (cached)
        assert tokens1 is tokens2

    def test_boolean_literals(self) -> None:
        """Test TRUE and FALSE boolean literals."""
        lexer = Lexer("TRUE FALSE")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.BOOLEAN_LITERAL
        assert tokens[0].literal is True
        assert tokens[1].type == TokenType.BOOLEAN_LITERAL
        assert tokens[1].literal is False
