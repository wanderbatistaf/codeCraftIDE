"""
Unit tests for SQL statement translator.

Tests the conversion of 4GL SQL statements to Python database calls
using both wbjdbc and wborm backends.

Epic 4, Story 4.4: Enhanced SQL Statement Translator
"""

import pytest

from src.fglinterpreter.converter.sql_translator import (
    SQLTranslator,
    WBJDBCTranslator,
    WBORMTranslator,
    create_sql_translator,
)
from src.fglinterpreter.lexer.tokens import TokenType
from src.fglinterpreter.parser.ast_nodes import (
    BinaryOp,
    DeleteStatement,
    Identifier,
    InsertStatement,
    Literal,
    SelectStatement,
    UpdateStatement,
)


class TestSQLTranslatorFactory:
    """Tests for SQL translator factory function."""

    def test_create_wbjdbc_translator(self):
        """Test creating wbjdbc translator."""
        translator = create_sql_translator(backend="wbjdbc")
        assert isinstance(translator, WBJDBCTranslator)

    def test_create_wborm_translator(self):
        """Test creating wborm translator."""
        translator = create_sql_translator(backend="wborm")
        assert isinstance(translator, WBORMTranslator)

    def test_create_translator_with_invalid_backend(self):
        """Test that invalid backend raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported SQL backend"):
            create_sql_translator(backend="invalid")

    def test_create_translator_with_indent_params(self):
        """Test creating translator with custom indent parameters."""
        translator = create_sql_translator(backend="wbjdbc", indent_level=2, indent_str="  ")
        assert translator.indent_level == 2
        assert translator.indent_str == "  "


class TestWBJDBCTranslator:
    """Tests for wbjdbc SQL translator."""

    def test_simple_select_statement(self):
        """Test converting simple SELECT statement."""
        translator = WBJDBCTranslator()

        node = SelectStatement(
            columns=["customer_name", "balance"],
            from_table="customers",
            into_variables=["v_name", "v_balance"],
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert '_sql = "SELECT customer_name, balance FROM customers"' in result
        assert "_cursor = db.execute_query(_sql)" in result
        assert "_row = _cursor.fetchone()" in result
        assert "if _row:" in result
        assert "v_name, v_balance = _row" in result

    def test_select_with_where_clause(self):
        """Test SELECT with WHERE clause."""
        translator = WBJDBCTranslator()

        # WHERE customer_id = v_id
        where_clause = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        node = SelectStatement(
            columns=["customer_name"],
            from_table="customers",
            into_variables=["v_name"],
            where_clause=where_clause,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert "WHERE customer_id = ?" in result
        assert "_params = [v_id]" in result
        assert "_cursor = db.execute_query(_sql, _params)" in result

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY clause."""
        translator = WBJDBCTranslator()

        node = SelectStatement(
            columns=["customer_name", "balance"],
            from_table="customers",
            into_variables=None,
            where_clause=None,
            order_by=[("customer_name", "ASC"), ("balance", "DESC")],
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert "ORDER BY customer_name ASC, balance DESC" in result

    def test_select_with_group_by(self):
        """Test SELECT with GROUP BY clause."""
        translator = WBJDBCTranslator()

        node = SelectStatement(
            columns=["region", "COUNT(*)"],
            from_table="customers",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=["region"],
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert "GROUP BY region" in result

    def test_select_all_columns(self):
        """Test SELECT * (no columns specified)."""
        translator = WBJDBCTranslator()

        node = SelectStatement(
            columns=[],
            from_table="customers",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert "SELECT *" in result

    def test_insert_with_values(self):
        """Test INSERT statement with VALUES."""
        translator = WBJDBCTranslator()

        node = InsertStatement(
            table_name="customers",
            columns=["customer_name", "balance"],
            values=[
                Identifier(name="v_name", line=1, column=1),
                Identifier(name="v_balance", line=1, column=1),
            ],
            line=1,
            column=1,
        )

        result = translator.translate_insert(node)

        assert "INSERT INTO customers (customer_name, balance) VALUES (?, ?)" in result
        assert "_params = [v_name, v_balance]" in result
        assert "db.execute_query(_sql, _params)" in result

    def test_insert_without_column_list(self):
        """Test INSERT without explicit column list."""
        translator = WBJDBCTranslator()

        node = InsertStatement(
            table_name="customers",
            columns=None,
            values=[
                Identifier(name="v_name", line=1, column=1),
                Identifier(name="v_balance", line=1, column=1),
            ],
            line=1,
            column=1,
        )

        result = translator.translate_insert(node)

        assert "INSERT INTO customers VALUES (?, ?)" in result

    def test_update_statement(self):
        """Test UPDATE statement."""
        translator = WBJDBCTranslator()

        # SET balance = v_new_balance
        assignments = [
            ("balance", Identifier(name="v_new_balance", line=1, column=1)),
        ]

        # WHERE customer_id = v_id
        where_clause = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        node = UpdateStatement(
            table_name="customers",
            assignments=assignments,
            where_clause=where_clause,
            line=1,
            column=1,
        )

        result = translator.translate_update(node)

        assert "UPDATE customers SET balance = ?" in result
        assert "WHERE customer_id = ?" in result
        assert "_params = [v_new_balance, v_id]" in result

    def test_update_multiple_columns(self):
        """Test UPDATE with multiple column assignments."""
        translator = WBJDBCTranslator()

        assignments = [
            ("customer_name", Identifier(name="v_name", line=1, column=1)),
            ("balance", Identifier(name="v_balance", line=1, column=1)),
        ]

        node = UpdateStatement(
            table_name="customers",
            assignments=assignments,
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_update(node)

        assert "UPDATE customers SET customer_name = ?, balance = ?" in result
        assert "_params = [v_name, v_balance]" in result

    def test_update_with_expression(self):
        """Test UPDATE with arithmetic expression (balance = balance + amount)."""
        translator = WBJDBCTranslator()

        # balance = balance + v_amount
        value_expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator="+",
            operator_type=TokenType.PLUS,
            right=Identifier(name="v_amount", line=1, column=1),
            line=1,
            column=1,
        )

        assignments = [("balance", value_expr)]

        node = UpdateStatement(
            table_name="customers",
            assignments=assignments,
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_update(node)

        assert "UPDATE customers SET balance = balance + ?" in result
        assert "_params = [v_amount]" in result

    def test_delete_statement(self):
        """Test DELETE statement with WHERE clause."""
        translator = WBJDBCTranslator()

        # WHERE customer_id = v_id
        where_clause = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        node = DeleteStatement(
            table_name="customers",
            where_clause=where_clause,
            line=1,
            column=1,
        )

        result = translator.translate_delete(node)

        assert "DELETE FROM customers WHERE customer_id = ?" in result
        assert "_params = [v_id]" in result
        assert "db.execute_query(_sql, _params)" in result

    def test_delete_without_where(self):
        """Test DELETE without WHERE clause."""
        translator = WBJDBCTranslator()

        node = DeleteStatement(
            table_name="customers",
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_delete(node)

        assert 'DELETE FROM customers"' in result
        assert "_params" not in result
        assert "db.execute_query(_sql)" in result


class TestWBORMTranslator:
    """Tests for wborm SQL translator."""

    def test_simple_select_statement(self):
        """Test converting simple SELECT statement with wborm."""
        translator = WBORMTranslator()

        node = SelectStatement(
            columns=["customer_name", "balance"],
            from_table="customers",
            into_variables=["v_name", "v_balance"],
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert '_sql = "SELECT customer_name, balance FROM customers"' in result
        assert "_result = db.query_one(_sql)" in result
        assert "if _result:" in result
        assert "v_name = _result['customer_name']" in result
        assert "v_balance = _result['balance']" in result

    def test_select_with_where_clause(self):
        """Test SELECT with WHERE clause using wborm."""
        translator = WBORMTranslator()

        where_clause = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        node = SelectStatement(
            columns=["customer_name"],
            from_table="customers",
            into_variables=["v_name"],
            where_clause=where_clause,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        assert "WHERE customer_id = ?" in result
        assert "_params = [v_id]" in result
        assert "_result = db.query_one(_sql, _params)" in result
        assert "v_name = _result['customer_name']" in result

    def test_insert_statement_same_as_wbjdbc(self):
        """Test that INSERT uses same implementation as wbjdbc."""
        wborm_translator = WBORMTranslator()
        wbjdbc_translator = WBJDBCTranslator()

        node = InsertStatement(
            table_name="customers",
            columns=["customer_name"],
            values=[Identifier(name="v_name", line=1, column=1)],
            line=1,
            column=1,
        )

        wborm_result = wborm_translator.translate_insert(node)
        wbjdbc_result = wbjdbc_translator.translate_insert(node)

        # Both should generate similar code (just different indentation objects)
        assert "INSERT INTO customers" in wborm_result
        assert "INSERT INTO customers" in wbjdbc_result


class TestWhereClauseBuilder:
    """Tests for WHERE clause and expression building."""

    def test_simple_equality(self):
        """Test simple equality: WHERE id = value."""
        translator = WBJDBCTranslator()

        expr = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        where_sql, params = translator.build_where_clause(expr)

        assert where_sql == " WHERE customer_id = ?"
        assert params == ["v_id"]

    def test_not_equal_operator(self):
        """Test NOT EQUAL operator: WHERE status <> value."""
        translator = WBJDBCTranslator()

        expr = BinaryOp(
            left=Identifier(name="status", line=1, column=1),
            operator="<>",
            operator_type=TokenType.NOT_EQUAL,
            right=Identifier(name="v_status", line=1, column=1),
            line=1,
            column=1,
        )

        where_sql, params = translator.build_where_clause(expr)

        assert " WHERE status <> ?" in where_sql
        assert params == ["v_status"]

    def test_comparison_operators(self):
        """Test comparison operators (>, <, >=, <=)."""
        translator = WBJDBCTranslator()

        # Test >
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator=">",
            operator_type=TokenType.GREATER_THAN,
            right=Identifier(name="v_min", line=1, column=1),
            line=1,
            column=1,
        )
        where_sql, _ = translator.build_where_clause(expr)
        assert "balance > ?" in where_sql

        # Test <
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator="<",
            operator_type=TokenType.LESS_THAN,
            right=Identifier(name="v_max", line=1, column=1),
            line=1,
            column=1,
        )
        where_sql, _ = translator.build_where_clause(expr)
        assert "balance < ?" in where_sql

        # Test >=
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator=">=",
            operator_type=TokenType.GREATER_EQUAL,
            right=Identifier(name="v_min", line=1, column=1),
            line=1,
            column=1,
        )
        where_sql, _ = translator.build_where_clause(expr)
        assert "balance >= ?" in where_sql

        # Test <=
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator="<=",
            operator_type=TokenType.LESS_EQUAL,
            right=Identifier(name="v_max", line=1, column=1),
            line=1,
            column=1,
        )
        where_sql, _ = translator.build_where_clause(expr)
        assert "balance <= ?" in where_sql

    def test_complex_where_with_and(self):
        """Test complex WHERE with AND: WHERE id = v_id AND status = v_status."""
        translator = WBJDBCTranslator()

        # id = v_id
        left_expr = BinaryOp(
            left=Identifier(name="customer_id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_id", line=1, column=1),
            line=1,
            column=1,
        )

        # status = v_status
        right_expr = BinaryOp(
            left=Identifier(name="status", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Identifier(name="v_status", line=1, column=1),
            line=1,
            column=1,
        )

        # Combined with AND
        expr = BinaryOp(
            left=left_expr,
            operator="AND",
            operator_type=TokenType.AND,
            right=right_expr,
            line=1,
            column=1,
        )

        where_sql, params = translator.build_where_clause(expr)

        assert "WHERE" in where_sql
        assert "AND" in where_sql
        assert "customer_id = ?" in where_sql
        assert "status = ?" in where_sql
        assert len(params) == 2
        assert "v_id" in params
        assert "v_status" in params

    def test_complex_where_with_or(self):
        """Test complex WHERE with OR."""
        translator = WBJDBCTranslator()

        # status = 'ACTIVE'
        left_expr = BinaryOp(
            left=Identifier(name="status", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value="ACTIVE", token_type=TokenType.STRING_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        # status = 'PENDING'
        right_expr = BinaryOp(
            left=Identifier(name="status", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value="PENDING", token_type=TokenType.STRING_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        # Combined with OR
        expr = BinaryOp(
            left=left_expr,
            operator="OR",
            operator_type=TokenType.OR,
            right=right_expr,
            line=1,
            column=1,
        )

        where_sql, params = translator.build_where_clause(expr)

        assert "OR" in where_sql
        assert len(params) == 2

    def test_where_with_literal_values(self):
        """Test WHERE clause with literal values."""
        translator = WBJDBCTranslator()

        # balance > 1000
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator=">",
            operator_type=TokenType.GREATER_THAN,
            right=Literal(value=1000, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        where_sql, params = translator.build_where_clause(expr)

        assert "balance > ?" in where_sql
        assert "1000" in params

    def test_empty_where_clause(self):
        """Test that None WHERE clause returns empty string."""
        translator = WBJDBCTranslator()

        where_sql, params = translator.build_where_clause(None)

        assert where_sql == ""
        assert params == []


class TestParameterBinding:
    """Tests for parameter binding and expression conversion."""

    def test_identifier_becomes_parameter(self):
        """Test that identifiers become parameters."""
        translator = WBJDBCTranslator()

        expr = Identifier(name="v_customer_id", line=1, column=1)
        sql, params = translator._build_expression_sql(expr)

        assert sql == "?"
        assert params == ["v_customer_id"]

    def test_literal_becomes_parameter(self):
        """Test that literals become parameters."""
        translator = WBJDBCTranslator()

        # String literal
        expr = Literal(value="ACTIVE", token_type=TokenType.STRING_LITERAL, line=1, column=1)
        sql, params = translator._build_expression_sql(expr)
        assert sql == "?"
        assert "'ACTIVE'" in params

        # Integer literal
        expr = Literal(value=100, token_type=TokenType.INTEGER_LITERAL, line=1, column=1)
        sql, params = translator._build_expression_sql(expr)
        assert sql == "?"
        assert "100" in params

    def test_column_arithmetic_in_where(self):
        """Test column arithmetic in WHERE clause (balance + 100)."""
        translator = WBJDBCTranslator()

        # balance + v_amount
        expr = BinaryOp(
            left=Identifier(name="balance", line=1, column=1),
            operator="+",
            operator_type=TokenType.PLUS,
            right=Identifier(name="v_amount", line=1, column=1),
            line=1,
            column=1,
        )

        sql, params = translator._build_expression_sql(expr)

        assert "balance + ?" in sql
        assert "v_amount" in params


class TestIndentation:
    """Tests for indentation handling."""

    def test_translator_respects_indent_level(self):
        """Test that translator respects indent level."""
        translator = WBJDBCTranslator(indent_level=2, indent_str="  ")

        node = DeleteStatement(
            table_name="customers",
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_delete(node)

        # Result should have indented lines
        lines = result.split("\n")
        for line in lines:
            if line.strip():  # Non-empty lines
                assert line.startswith("  " * 2)

    def test_custom_indent_string(self):
        """Test using custom indent string (tabs instead of spaces)."""
        translator = WBJDBCTranslator(indent_level=1, indent_str="\t")

        node = DeleteStatement(
            table_name="customers",
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_delete(node)

        lines = result.split("\n")
        for line in lines:
            if line.strip():
                assert line.startswith("\t")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_select_without_into_clause(self):
        """Test SELECT without INTO (for cursor scenarios)."""
        translator = WBJDBCTranslator()

        node = SelectStatement(
            columns=["customer_name"],
            from_table="customers",
            into_variables=None,  # No INTO
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        result = translator.translate_select(node)

        # Should still generate query, just no variable assignment
        assert "SELECT customer_name FROM customers" in result
        assert "_cursor = db.execute_query(_sql)" in result
        # But no INTO variable assignment
        assert "= _row" not in result

    def test_update_without_where_is_valid(self):
        """Test that UPDATE without WHERE is allowed (updates all rows)."""
        translator = WBJDBCTranslator()

        assignments = [("status", Identifier(name="v_new_status", line=1, column=1))]

        node = UpdateStatement(
            table_name="customers",
            assignments=assignments,
            where_clause=None,
            line=1,
            column=1,
        )

        result = translator.translate_update(node)

        assert "UPDATE customers SET status = ?" in result
        assert "WHERE" not in result  # No WHERE clause

    def test_insert_with_no_values(self):
        """Test INSERT with no values (edge case)."""
        translator = WBJDBCTranslator()

        node = InsertStatement(
            table_name="customers",
            columns=["customer_name"],
            values=None,  # No values
            line=1,
            column=1,
        )

        result = translator.translate_insert(node)

        # Should still generate INSERT statement
        assert "INSERT INTO customers" in result
