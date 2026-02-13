"""
Integration tests for database functionality in the interpreter.

These tests validate that the interpreter can execute SQL statements,
manage cursors, handle transactions, and update SQLCA correctly.
"""

from unittest.mock import Mock

import pytest

from fglinterpreter.interpreter import ExecutionContext, Interpreter
from fglinterpreter.interpreter.exceptions import RuntimeError as InterpreterRuntimeError
from fglinterpreter.lexer import TokenType
from fglinterpreter.parser.ast_nodes import *


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock database connector (no specific spec to avoid import issues)
        self.mock_connector = Mock()
        self.mock_connector.is_connected = Mock(return_value=True)
        self.mock_connector.query = Mock(return_value=[])
        self.mock_connector.execute = Mock(return_value=1)
        self.mock_connector.begin_transaction = Mock()
        self.mock_connector.commit = Mock()
        self.mock_connector.rollback = Mock()

        # Create execution context with database connector
        self.context = ExecutionContext()
        self.context.set_database_connector(self.mock_connector)

        # Create interpreter
        self.interpreter = Interpreter(self.context)

    def test_select_statement_execution(self):
        """Test SELECT statement execution."""
        # Setup mock response
        self.mock_connector.query.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        # Create SELECT statement AST
        select_stmt = SelectStatement(
            line=1, column=1, columns=["id", "name"], from_table="users", where_clause=None
        )

        # Execute
        select_stmt.accept(self.interpreter)

        # Verify connector was called
        self.mock_connector.query.assert_called_once()
        call_args = self.mock_connector.query.call_args
        assert "SELECT id, name FROM users" in call_args[0][0]

    def test_select_with_into_clause(self):
        """Test SELECT with INTO clause assigns variables."""
        # Setup mock response
        self.mock_connector.query.return_value = [{"id": 1, "name": "Alice"}]

        # Define variables first
        self.context.define_variable("user_id", None)
        self.context.define_variable("user_name", None)

        # Create SELECT statement with INTO
        select_stmt = SelectStatement(
            line=1,
            column=1,
            columns=["id", "name"],
            into_variables=["user_id", "user_name"],
            from_table="users",
        )

        # Execute
        select_stmt.accept(self.interpreter)

        # Verify variables were set
        assert self.context.get_variable("user_id") == 1
        assert self.context.get_variable("user_name") == "Alice"

    def test_insert_statement_execution(self):
        """Test INSERT statement execution."""
        self.mock_connector.execute.return_value = 1

        # Create INSERT statement
        insert_stmt = InsertStatement(
            line=1,
            column=1,
            table_name="users",
            columns=["name", "email"],
            values=[
                Literal(line=1, column=1, value="John Doe", token_type=TokenType.STRING_LITERAL),
                Literal(
                    line=1, column=1, value="john@example.com", token_type=TokenType.STRING_LITERAL
                ),
            ],
        )

        # Execute
        insert_stmt.accept(self.interpreter)

        # Verify connector was called
        self.mock_connector.execute.assert_called_once()
        call_args = self.mock_connector.execute.call_args
        assert "INSERT INTO users" in call_args[0][0]
        assert call_args[0][1] == ("John Doe", "john@example.com")

    def test_update_statement_execution(self):
        """Test UPDATE statement execution."""
        self.mock_connector.execute.return_value = 1

        # Create UPDATE statement
        update_stmt = UpdateStatement(
            line=1,
            column=1,
            table_name="users",
            assignments=[
                (
                    "name",
                    Literal(
                        line=1, column=1, value="Jane Doe", token_type=TokenType.STRING_LITERAL
                    ),
                )
            ],
        )

        # Execute
        update_stmt.accept(self.interpreter)

        # Verify connector was called
        self.mock_connector.execute.assert_called_once()
        call_args = self.mock_connector.execute.call_args
        assert "UPDATE users SET name = ?" in call_args[0][0]
        assert call_args[0][1] == ("Jane Doe",)

    def test_delete_statement_execution(self):
        """Test DELETE statement execution."""
        self.mock_connector.execute.return_value = 1

        # Create DELETE statement
        delete_stmt = DeleteStatement(line=1, column=1, table_name="users")

        # Execute
        delete_stmt.accept(self.interpreter)

        # Verify connector was called
        self.mock_connector.execute.assert_called_once()
        call_args = self.mock_connector.execute.call_args
        assert "DELETE FROM users" in call_args[0][0]

    def test_begin_work_statement(self):
        """Test BEGIN WORK statement."""
        # Create BEGIN WORK statement
        begin_stmt = BeginWorkStatement(line=1, column=1)

        # Execute
        begin_stmt.accept(self.interpreter)

        # Verify connector method was called
        self.mock_connector.begin_transaction.assert_called_once()

        # Verify SQLCA was updated
        sqlca = self.context.get_sqlca()
        assert sqlca["sqlcode"] == 0  # Success

    def test_commit_work_statement(self):
        """Test COMMIT WORK statement."""
        # Create COMMIT WORK statement
        commit_stmt = CommitWorkStatement(line=1, column=1)

        # Execute
        commit_stmt.accept(self.interpreter)

        # Verify connector method was called
        self.mock_connector.commit.assert_called_once()

        # Verify SQLCA was updated
        sqlca = self.context.get_sqlca()
        assert sqlca["sqlcode"] == 0  # Success

    def test_rollback_work_statement(self):
        """Test ROLLBACK WORK statement."""
        # Create ROLLBACK WORK statement
        rollback_stmt = RollbackWorkStatement(line=1, column=1)

        # Execute
        rollback_stmt.accept(self.interpreter)

        # Verify connector method was called
        self.mock_connector.rollback.assert_called_once()

        # Verify SQLCA was updated
        sqlca = self.context.get_sqlca()
        assert sqlca["sqlcode"] == 0  # Success

    def test_database_statement(self):
        """Test DATABASE statement."""
        # Create DATABASE statement
        db_stmt = DatabaseStatement(
            line=1, column=1, database_name="testdb", host="localhost", port=9088
        )

        # Execute
        db_stmt.accept(self.interpreter)

        # Verify connection was checked
        self.mock_connector.is_connected.assert_called()

    def test_transaction_workflow(self):
        """Test complete transaction workflow."""
        # BEGIN WORK
        begin_stmt = BeginWorkStatement(line=1, column=1)
        begin_stmt.accept(self.interpreter)
        self.mock_connector.begin_transaction.assert_called_once()

        # INSERT
        insert_stmt = InsertStatement(
            line=2,
            column=1,
            table_name="users",
            columns=["name"],
            values=[
                Literal(line=2, column=1, value="Test User", token_type=TokenType.STRING_LITERAL)
            ],
        )
        insert_stmt.accept(self.interpreter)
        self.mock_connector.execute.assert_called()

        # COMMIT
        commit_stmt = CommitWorkStatement(line=3, column=1)
        commit_stmt.accept(self.interpreter)
        self.mock_connector.commit.assert_called_once()

    def test_cursor_lifecycle(self):
        """Test complete cursor lifecycle (DECLARE, OPEN, FOREACH, CLOSE)."""
        # Setup mock query results
        self.mock_connector.query.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        # DECLARE CURSOR
        select_for_cursor = SelectStatement(
            line=1, column=1, columns=["id", "name"], from_table="users"
        )

        declare_stmt = DeclareStatement(
            line=1, column=1, cursor_name="user_cursor", select_statement=select_for_cursor
        )
        declare_stmt.accept(self.interpreter)

        # Verify cursor was declared
        assert self.context.has_cursor("user_cursor")

        # OPEN CURSOR
        open_stmt = OpenStatement(line=2, column=1, cursor_name="user_cursor")
        open_stmt.accept(self.interpreter)

        # Verify query was executed
        self.mock_connector.query.assert_called_once()

        # Verify cursor has results
        cursor_info = self.context.get_cursor("user_cursor")
        assert cursor_info["results"] is not None
        assert len(cursor_info["results"]) == 2

        # CLOSE CURSOR
        close_stmt = CloseStatement(line=3, column=1, cursor_name="user_cursor")
        close_stmt.accept(self.interpreter)

        # Verify cursor results were cleared
        cursor_info = self.context.get_cursor("user_cursor")
        assert cursor_info["results"] is None

    def test_sqlca_initialization(self):
        """Test SQLCA is properly initialized."""
        sqlca = self.context.get_sqlca()

        assert sqlca["sqlcode"] == 0
        assert sqlca["sqlerrd"] == [0, 0, 0, 0, 0, 0]
        assert sqlca["sqlerrm"] == ""
        assert len(sqlca["sqlwarn"]) == 8

    def test_error_without_database_connector(self):
        """Test error is raised when no database connector is configured."""
        # Create context without connector
        empty_context = ExecutionContext()
        interpreter = Interpreter(empty_context)

        # Try to execute SELECT
        select_stmt = SelectStatement(line=1, column=1, columns=["id"], from_table="users")

        # Should raise InterpreterRuntimeError
        with pytest.raises(InterpreterRuntimeError, match="No database connector configured"):
            select_stmt.accept(interpreter)


class TestFOREACHIntegration:
    """Integration tests for FOREACH cursor iteration."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock connector (no specific spec to avoid import issues)
        self.mock_connector = Mock()
        self.mock_connector.is_connected = Mock(return_value=True)

        # Create context and interpreter
        self.context = ExecutionContext()
        self.context.set_database_connector(self.mock_connector)
        self.interpreter = Interpreter(self.context)

    def test_foreach_iteration(self):
        """Test FOREACH statement iterates through cursor results."""
        # Setup mock results
        self.mock_connector.query.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        # DECLARE and OPEN cursor
        select_stmt = SelectStatement(line=1, column=1, columns=["id", "name"], from_table="users")

        declare_stmt = DeclareStatement(
            line=1, column=1, cursor_name="user_cursor", select_statement=select_stmt
        )
        declare_stmt.accept(self.interpreter)

        open_stmt = OpenStatement(line=2, column=1, cursor_name="user_cursor")
        open_stmt.accept(self.interpreter)

        # Define variables (matching column names from SELECT)
        self.context.define_variable("id", None)
        self.context.define_variable("name", None)

        # Create FOREACH statement with DISPLAY body
        foreach_stmt = ForeachStatement(
            line=3,
            column=1,
            cursor_name="user_cursor",
            into_variables=["id", "name"],
            body=[
                DisplayStatement(
                    line=4,
                    column=1,
                    expressions=[
                        Identifier(line=4, column=1, name="id"),
                        Identifier(line=4, column=1, name="name"),
                    ],
                )
            ],
        )

        # Execute FOREACH
        foreach_stmt.accept(self.interpreter)

        # Verify output was generated for all 3 rows
        output = self.context.get_output()
        assert "1" in output and "Alice" in output
        assert "2" in output and "Bob" in output
        assert "3" in output and "Charlie" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
