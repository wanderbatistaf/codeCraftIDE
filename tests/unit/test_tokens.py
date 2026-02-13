"""
Unit tests for token definitions and Token dataclass.
"""

import pytest

from fglinterpreter.lexer import KEYWORDS, Token, TokenType


@pytest.mark.unit
class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_types_exist(self) -> None:
        """Test that essential token types are defined."""
        assert TokenType.MAIN
        assert TokenType.END
        assert TokenType.IF
        assert TokenType.THEN
        assert TokenType.ELSE
        assert TokenType.FOR
        assert TokenType.WHILE
        assert TokenType.FUNCTION
        assert TokenType.RETURN
        assert TokenType.DISPLAY
        assert TokenType.SELECT
        assert TokenType.INSERT
        assert TokenType.UPDATE
        assert TokenType.DELETE

    def test_operator_token_types(self) -> None:
        """Test that operator token types are defined."""
        assert TokenType.PLUS
        assert TokenType.MINUS
        assert TokenType.MULTIPLY
        assert TokenType.DIVIDE
        assert TokenType.EQUAL
        assert TokenType.NOT_EQUAL
        assert TokenType.LESS_THAN
        assert TokenType.GREATER_THAN

    def test_literal_token_types(self) -> None:
        """Test that literal token types are defined."""
        assert TokenType.INTEGER_LITERAL
        assert TokenType.FLOAT_LITERAL
        assert TokenType.STRING_LITERAL
        assert TokenType.BOOLEAN_LITERAL

    def test_delimiter_token_types(self) -> None:
        """Test that delimiter token types are defined."""
        assert TokenType.LPAREN
        assert TokenType.RPAREN
        assert TokenType.COMMA
        assert TokenType.SEMICOLON


@pytest.mark.unit
class TestKeywordMapping:
    """Tests for the KEYWORDS dictionary."""

    def test_main_keywords_mapped(self) -> None:
        """Test that essential keywords are mapped correctly."""
        assert KEYWORDS["MAIN"] == TokenType.MAIN
        assert KEYWORDS["END"] == TokenType.END
        assert KEYWORDS["IF"] == TokenType.IF
        assert KEYWORDS["THEN"] == TokenType.THEN
        assert KEYWORDS["ELSE"] == TokenType.ELSE

    def test_function_keywords_mapped(self) -> None:
        """Test that function keywords are mapped correctly."""
        assert KEYWORDS["FUNCTION"] == TokenType.FUNCTION
        assert KEYWORDS["RETURN"] == TokenType.RETURN
        assert KEYWORDS["CALL"] == TokenType.CALL

    def test_database_keywords_mapped(self) -> None:
        """Test that database keywords are mapped correctly."""
        assert KEYWORDS["SELECT"] == TokenType.SELECT
        assert KEYWORDS["INSERT"] == TokenType.INSERT
        assert KEYWORDS["UPDATE"] == TokenType.UPDATE
        assert KEYWORDS["DELETE"] == TokenType.DELETE
        assert KEYWORDS["FROM"] == TokenType.FROM
        assert KEYWORDS["WHERE"] == TokenType.WHERE

    def test_data_type_keywords_mapped(self) -> None:
        """Test that data type keywords are mapped correctly."""
        assert KEYWORDS["INTEGER"] == TokenType.INTEGER
        assert KEYWORDS["CHAR"] == TokenType.CHAR
        assert KEYWORDS["DECIMAL"] == TokenType.DECIMAL
        assert KEYWORDS["DATE"] == TokenType.DATE

    def test_keyword_aliases(self) -> None:
        """Test that keyword aliases work correctly."""
        assert KEYWORDS["INT"] == TokenType.INTEGER
        assert KEYWORDS["DEC"] == TokenType.DECIMAL
        assert KEYWORDS["CHARACTER"] == TokenType.CHAR

    def test_boolean_literals_mapped(self) -> None:
        """Test that boolean literals are mapped correctly."""
        assert KEYWORDS["TRUE"] == TokenType.BOOLEAN_LITERAL
        assert KEYWORDS["FALSE"] == TokenType.BOOLEAN_LITERAL


@pytest.mark.unit
class TestTokenDataclass:
    """Tests for the Token dataclass."""

    def test_token_creation(self) -> None:
        """Test creating a basic token."""
        token = Token(TokenType.IDENTIFIER, "myvar", 1, 5)
        assert token.type == TokenType.IDENTIFIER
        assert token.value == "myvar"
        assert token.line == 1
        assert token.column == 5
        assert token.literal is None

    def test_token_with_literal(self) -> None:
        """Test creating a token with a literal value."""
        token = Token(TokenType.INTEGER_LITERAL, "42", 1, 1, 42)
        assert token.type == TokenType.INTEGER_LITERAL
        assert token.value == "42"
        assert token.literal == 42

    def test_token_repr(self) -> None:
        """Test token string representation."""
        token = Token(TokenType.IDENTIFIER, "myvar", 1, 5)
        repr_str = repr(token)
        assert "IDENTIFIER" in repr_str
        assert "myvar" in repr_str
        assert "1:5" in repr_str

    def test_token_repr_with_literal(self) -> None:
        """Test token string representation with literal."""
        token = Token(TokenType.INTEGER_LITERAL, "42", 1, 1, 42)
        repr_str = repr(token)
        assert "literal=42" in repr_str

    def test_token_str(self) -> None:
        """Test token human-readable string."""
        token = Token(TokenType.IDENTIFIER, "myvar", 1, 5)
        str_repr = str(token)
        assert "IDENTIFIER(myvar)" == str_repr

    def test_is_keyword(self) -> None:
        """Test is_keyword method."""
        keyword_token = Token(TokenType.MAIN, "MAIN", 1, 1)
        assert keyword_token.is_keyword()

        identifier_token = Token(TokenType.IDENTIFIER, "myvar", 1, 1)
        assert not identifier_token.is_keyword()

    def test_is_operator(self) -> None:
        """Test is_operator method."""
        plus_token = Token(TokenType.PLUS, "+", 1, 1)
        assert plus_token.is_operator()

        identifier_token = Token(TokenType.IDENTIFIER, "myvar", 1, 1)
        assert not identifier_token.is_operator()

    def test_is_literal(self) -> None:
        """Test is_literal method."""
        int_token = Token(TokenType.INTEGER_LITERAL, "42", 1, 1, 42)
        assert int_token.is_literal()

        string_token = Token(TokenType.STRING_LITERAL, "hello", 1, 1, "hello")
        assert string_token.is_literal()

        identifier_token = Token(TokenType.IDENTIFIER, "myvar", 1, 1)
        assert not identifier_token.is_literal()

    def test_is_delimiter(self) -> None:
        """Test is_delimiter method."""
        lparen_token = Token(TokenType.LPAREN, "(", 1, 1)
        assert lparen_token.is_delimiter()

        comma_token = Token(TokenType.COMMA, ",", 1, 1)
        assert comma_token.is_delimiter()

        identifier_token = Token(TokenType.IDENTIFIER, "myvar", 1, 1)
        assert not identifier_token.is_delimiter()
