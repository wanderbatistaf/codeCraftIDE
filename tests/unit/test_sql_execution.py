"""
Unit tests for SQL statement execution in the interpreter.

Tests SQL parsing and execution with mocked database connectors.
"""

import sys
from unittest.mock import MagicMock, Mock

import pytest

# Mock the database modules before importing fglinterpreter
# Only create mocks if they don't already exist (for test isolation)
if "wbjdbc" not in sys.modules:
    sys.modules["wbjdbc"] = MagicMock()
if "wborm" not in sys.modules:
    sys.modules["wborm"] = MagicMock()

from src.fglinterpreter.database import WBJDBCConnector
from src.fglinterpreter.interpreter import ExecutionContext, Interpreter
from src.fglinterpreter.lexer.tokens import TokenType
from src.fglinterpreter.parser.ast_nodes import (
    BinaryOp,
    CloseStatement,
    DeclareStatement,
    DeleteStatement,
    ForeachStatement,
    FreeStatement,
    Identifier,
    InsertStatement,
    Literal,
    OpenStatement,
    SelectStatement,
    UpdateStatement,
)


class TestSQLExecution:
    """Tests for SQL statement execution."""

    @pytest.fixture
    def mock_connector(self):
        """Create a mock database connector."""
        connector = Mock(spec=WBJDBCConnector)
        connector.query = Mock(return_value=[])
        connector.execute = Mock(return_value=0)
        connector.is_connected = Mock(return_value=True)
        return connector

    @pytest.fixture
    def context_with_db(self, mock_connector):
        """Create execution context with database connector."""
        context = ExecutionContext()
        context.set_database_connector(mock_connector)
        return context

    @pytest.fixture
    def interpreter_with_db(self, context_with_db):
        """Create interpreter with database connector."""
        return Interpreter(context_with_db)

    # ========================================================================
    # SELECT Statement Tests
    # ========================================================================

    def test_select_simple(self, interpreter_with_db, mock_connector):
        """Test simple SELECT statement."""
        # Setup
        mock_connector.query.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        # Create SELECT statement: SELECT id, name FROM users
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        # Execute
        select_node.accept(interpreter_with_db)

        # Verify
        mock_connector.query.assert_called_once_with("SELECT id, name FROM users", None)

    def test_select_with_where(self, interpreter_with_db, mock_connector):
        """Test SELECT with WHERE clause."""
        # Setup
        mock_connector.query.return_value = [{"id": 1, "name": "Alice"}]

        # Create WHERE clause: id = 1
        where_clause = BinaryOp(
            left=Identifier(name="id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        # Create SELECT statement: SELECT id, name FROM users WHERE id = 1
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            where_clause=where_clause,
            into_variables=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        # Execute
        select_node.accept(interpreter_with_db)

        # Verify SQL and parameters
        call_args = mock_connector.query.call_args
        assert call_args[0][0] == "SELECT id, name FROM users WHERE (id = ?)"
        assert call_args[0][1] == (1,)

    def test_select_into_variables(self, interpreter_with_db, mock_connector, context_with_db):
        """Test SELECT INTO to assign values to variables."""
        # Setup
        mock_connector.query.return_value = [{"id": 1, "name": "Alice"}]

        # Define variables
        context_with_db.define_variable("v_id", None)
        context_with_db.define_variable("v_name", None)

        # Create SELECT INTO statement
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=["v_id", "v_name"],
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        # Execute
        select_node.accept(interpreter_with_db)

        # Verify variables were assigned
        assert context_with_db.get_variable("v_id") == 1
        assert context_with_db.get_variable("v_name") == "Alice"

    def test_select_with_order_by(self, interpreter_with_db, mock_connector):
        """Test SELECT with ORDER BY clause."""
        # Setup
        mock_connector.query.return_value = []

        # Create SELECT with ORDER BY
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            where_clause=None,
            into_variables=None,
            order_by=[("name", "ASC"), ("id", "DESC")],
            group_by=None,
            line=1,
            column=1,
        )

        # Execute
        select_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.query.call_args
        assert "ORDER BY name ASC, id DESC" in call_args[0][0]

    def test_select_with_group_by(self, interpreter_with_db, mock_connector):
        """Test SELECT with GROUP BY clause."""
        # Setup
        mock_connector.query.return_value = []

        # Create SELECT with GROUP BY
        select_node = SelectStatement(
            columns=["category", "COUNT(*)"],
            from_table="products",
            where_clause=None,
            into_variables=None,
            order_by=None,
            group_by=["category"],
            line=1,
            column=1,
        )

        # Execute
        select_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.query.call_args
        assert "GROUP BY category" in call_args[0][0]

    # ========================================================================
    # INSERT Statement Tests
    # ========================================================================

    def test_insert_simple(self, interpreter_with_db, mock_connector):
        """Test simple INSERT statement."""
        # Create INSERT statement: INSERT INTO users VALUES (1, 'Alice')
        insert_node = InsertStatement(
            table_name="users",
            columns=None,
            values=[
                Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
                Literal(value="Alice", token_type=TokenType.STRING_LITERAL, line=1, column=1),
            ],
            line=1,
            column=1,
        )

        # Execute
        insert_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert call_args[0][0] == "INSERT INTO users VALUES (?, ?)"
        assert call_args[0][1] == (1, "Alice")

    def test_insert_with_columns(self, interpreter_with_db, mock_connector):
        """Test INSERT with column list."""
        # Create INSERT statement: INSERT INTO users (id, name) VALUES (1, 'Alice')
        insert_node = InsertStatement(
            table_name="users",
            columns=["id", "name"],
            values=[
                Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
                Literal(value="Alice", token_type=TokenType.STRING_LITERAL, line=1, column=1),
            ],
            line=1,
            column=1,
        )

        # Execute
        insert_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert "INSERT INTO users (id, name)" in call_args[0][0]
        assert call_args[0][1] == (1, "Alice")

    # ========================================================================
    # UPDATE Statement Tests
    # ========================================================================

    def test_update_simple(self, interpreter_with_db, mock_connector):
        """Test simple UPDATE statement."""
        # Create UPDATE statement: UPDATE users SET name = 'Bob'
        update_node = UpdateStatement(
            table_name="users",
            assignments=[
                (
                    "name",
                    Literal(value="Bob", token_type=TokenType.STRING_LITERAL, line=1, column=1),
                )
            ],
            where_clause=None,
            line=1,
            column=1,
        )

        # Execute
        update_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert call_args[0][0] == "UPDATE users SET name = ?"
        assert call_args[0][1] == ("Bob",)

    def test_update_with_where(self, interpreter_with_db, mock_connector):
        """Test UPDATE with WHERE clause."""
        # Create WHERE clause: id = 1
        where_clause = BinaryOp(
            left=Identifier(name="id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        # Create UPDATE statement: UPDATE users SET name = 'Bob' WHERE id = 1
        update_node = UpdateStatement(
            table_name="users",
            assignments=[
                (
                    "name",
                    Literal(value="Bob", token_type=TokenType.STRING_LITERAL, line=1, column=1),
                )
            ],
            where_clause=where_clause,
            line=1,
            column=1,
        )

        # Execute
        update_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert "UPDATE users SET name = ?" in call_args[0][0]
        assert "WHERE (id = ?)" in call_args[0][0]
        assert call_args[0][1] == ("Bob", 1)

    def test_update_multiple_columns(self, interpreter_with_db, mock_connector):
        """Test UPDATE with multiple column assignments."""
        # Create UPDATE statement
        update_node = UpdateStatement(
            table_name="users",
            assignments=[
                (
                    "name",
                    Literal(value="Bob", token_type=TokenType.STRING_LITERAL, line=1, column=1),
                ),
                ("age", Literal(value=30, token_type=TokenType.INTEGER_LITERAL, line=1, column=1)),
            ],
            where_clause=None,
            line=1,
            column=1,
        )

        # Execute
        update_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert "UPDATE users SET name = ?, age = ?" in call_args[0][0]
        assert call_args[0][1] == ("Bob", 30)

    # ========================================================================
    # DELETE Statement Tests
    # ========================================================================

    def test_delete_simple(self, interpreter_with_db, mock_connector):
        """Test simple DELETE statement."""
        # Create DELETE statement: DELETE FROM users
        delete_node = DeleteStatement(table_name="users", where_clause=None, line=1, column=1)

        # Execute
        delete_node.accept(interpreter_with_db)

        # Verify
        mock_connector.execute.assert_called_once_with("DELETE FROM users", None)

    def test_delete_with_where(self, interpreter_with_db, mock_connector):
        """Test DELETE with WHERE clause."""
        # Create WHERE clause: id = 1
        where_clause = BinaryOp(
            left=Identifier(name="id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        # Create DELETE statement: DELETE FROM users WHERE id = 1
        delete_node = DeleteStatement(
            table_name="users", where_clause=where_clause, line=1, column=1
        )

        # Execute
        delete_node.accept(interpreter_with_db)

        # Verify
        call_args = mock_connector.execute.call_args
        assert "DELETE FROM users WHERE (id = ?)" in call_args[0][0]
        assert call_args[0][1] == (1,)

    # ========================================================================
    # Cursor Tests
    # ========================================================================

    def test_declare_cursor(self, interpreter_with_db, context_with_db):
        """Test DECLARE cursor statement."""
        # Create SELECT for cursor
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        # Create DECLARE statement
        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )

        # Execute
        declare_node.accept(interpreter_with_db)

        # Verify cursor was declared
        assert context_with_db.has_cursor("user_cursor")
        cursor_info = context_with_db.get_cursor("user_cursor")
        assert cursor_info["select_statement"] == select_node

    def test_open_cursor(self, interpreter_with_db, context_with_db, mock_connector):
        """Test OPEN cursor statement."""
        # Setup mock results
        mock_connector.query.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        # Declare cursor first
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )
        declare_node.accept(interpreter_with_db)

        # Open cursor
        open_node = OpenStatement(cursor_name="user_cursor", line=1, column=1)
        open_node.accept(interpreter_with_db)

        # Verify query was executed
        mock_connector.query.assert_called_once()

        # Verify results were stored
        cursor_info = context_with_db.get_cursor("user_cursor")
        assert cursor_info["results"] is not None
        assert len(cursor_info["results"]) == 2

    def test_close_cursor(self, interpreter_with_db, context_with_db, mock_connector):
        """Test CLOSE cursor statement."""
        # Declare and open cursor
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )
        declare_node.accept(interpreter_with_db)

        mock_connector.query.return_value = [{"id": 1, "name": "Alice"}]
        open_node = OpenStatement(cursor_name="user_cursor", line=1, column=1)
        open_node.accept(interpreter_with_db)

        # Close cursor
        close_node = CloseStatement(cursor_name="user_cursor", line=1, column=1)
        close_node.accept(interpreter_with_db)

        # Verify results were cleared
        cursor_info = context_with_db.get_cursor("user_cursor")
        assert cursor_info["results"] is None

    def test_free_cursor(self, interpreter_with_db, context_with_db):
        """Test FREE cursor statement."""
        # Declare cursor
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )
        declare_node.accept(interpreter_with_db)

        # Free cursor
        free_node = FreeStatement(cursor_name="user_cursor", line=1, column=1)
        free_node.accept(interpreter_with_db)

        # Verify cursor was removed
        assert not context_with_db.has_cursor("user_cursor")

    def test_foreach_cursor(self, interpreter_with_db, context_with_db, mock_connector):
        """Test FOREACH loop with cursor."""
        # Setup mock results
        mock_connector.query.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        # Declare and open cursor
        select_node = SelectStatement(
            columns=["id", "name"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )
        declare_node.accept(interpreter_with_db)

        open_node = OpenStatement(cursor_name="user_cursor", line=1, column=1)
        open_node.accept(interpreter_with_db)

        # Define variables for FOREACH
        context_with_db.define_variable("v_id", None)
        context_with_db.define_variable("v_name", None)
        context_with_db.define_variable("counter", 0)

        # Create FOREACH loop (with empty body for testing)
        from src.fglinterpreter.parser.ast_nodes import LetStatement

        # Body: counter = counter + 1
        body = [
            LetStatement(
                variable="counter",
                value=BinaryOp(
                    left=Identifier(name="counter", line=1, column=1),
                    operator="+",
                    operator_type=TokenType.PLUS,
                    right=Literal(value=1, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
                    line=1,
                    column=1,
                ),
                line=1,
                column=1,
            )
        ]

        foreach_node = ForeachStatement(
            cursor_name="user_cursor",
            into_variables=["v_id", "v_name"],
            body=body,
            line=1,
            column=1,
        )

        # Execute FOREACH
        foreach_node.accept(interpreter_with_db)

        # Verify loop executed 3 times
        assert context_with_db.get_variable("counter") == 3

        # Note: After FOREACH completes, the INTO variables may not retain their last values
        # as they are scoped to the loop iteration. The counter test above verifies
        # that the loop executed correctly.

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_select_without_connector(self):
        """Test SELECT fails without database connector."""
        interpreter = Interpreter()  # No connector set

        select_node = SelectStatement(
            columns=["id"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        with pytest.raises(Exception) as exc_info:
            select_node.accept(interpreter)

        assert "No database connector configured" in str(exc_info.value)

    def test_open_undeclared_cursor(self, interpreter_with_db):
        """Test OPEN fails for undeclared cursor."""
        open_node = OpenStatement(cursor_name="nonexistent", line=1, column=1)

        with pytest.raises(Exception) as exc_info:
            open_node.accept(interpreter_with_db)

        assert "not declared" in str(exc_info.value)

    def test_foreach_unopened_cursor(self, interpreter_with_db, context_with_db):
        """Test FOREACH fails for unopened cursor."""
        # Declare but don't open cursor
        select_node = SelectStatement(
            columns=["id"],
            from_table="users",
            into_variables=None,
            where_clause=None,
            order_by=None,
            group_by=None,
            line=1,
            column=1,
        )

        declare_node = DeclareStatement(
            cursor_name="user_cursor", select_statement=select_node, line=1, column=1
        )
        declare_node.accept(interpreter_with_db)

        # Try FOREACH without opening
        foreach_node = ForeachStatement(
            cursor_name="user_cursor", into_variables=["v_id"], body=[], line=1, column=1
        )

        with pytest.raises(Exception) as exc_info:
            foreach_node.accept(interpreter_with_db)

        assert "not opened" in str(exc_info.value)


@pytest.mark.unit
class TestSQLParameterBinding:
    """Tests for SQL parameter binding and expression conversion."""

    @pytest.fixture
    def interpreter_with_db(self):
        """Create interpreter with database connector."""
        context = ExecutionContext()
        connector = Mock()
        connector.query = Mock(return_value=[])
        connector.execute = Mock(return_value=0)
        connector.is_connected = Mock(return_value=True)
        context.set_database_connector(connector)
        return Interpreter(context)

    def test_build_expression_literal(self, interpreter_with_db):
        """Test building SQL from literal expression."""
        expr = Literal(value=42, token_type=TokenType.INTEGER_LITERAL, line=1, column=1)
        sql, params = interpreter_with_db._build_expression_sql(expr)

        assert sql == "?"
        assert params == [42]

    def test_build_expression_identifier(self, interpreter_with_db):
        """Test building SQL from identifier expression."""
        expr = Identifier(name="user_id", line=1, column=1)
        sql, params = interpreter_with_db._build_expression_sql(expr)

        assert sql == "user_id"
        assert params == []

    def test_build_expression_binary_op(self, interpreter_with_db):
        """Test building SQL from binary operation."""
        # id = 42
        expr = BinaryOp(
            left=Identifier(name="id", line=1, column=1),
            operator="=",
            operator_type=TokenType.EQUAL,
            right=Literal(value=42, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
            line=1,
            column=1,
        )

        sql, params = interpreter_with_db._build_expression_sql(expr)

        assert sql == "(id = ?)"
        assert params == [42]

    def test_build_expression_complex(self, interpreter_with_db):
        """Test building SQL from complex expression."""
        # (id > 10) AND (name = 'Alice')
        expr = BinaryOp(
            left=BinaryOp(
                left=Identifier(name="id", line=1, column=1),
                operator=">",
                operator_type=TokenType.GREATER_THAN,
                right=Literal(value=10, token_type=TokenType.INTEGER_LITERAL, line=1, column=1),
                line=1,
                column=1,
            ),
            operator="AND",
            operator_type=TokenType.AND,
            right=BinaryOp(
                left=Identifier(name="name", line=1, column=1),
                operator="=",
                operator_type=TokenType.EQUAL,
                right=Literal(value="Alice", token_type=TokenType.STRING_LITERAL, line=1, column=1),
                line=1,
                column=1,
            ),
            line=1,
            column=1,
        )

        sql, params = interpreter_with_db._build_expression_sql(expr)

        assert sql == "((id > ?) AND (name = ?))"
        assert params == [10, "Alice"]
