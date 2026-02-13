"""
Abstract Syntax Tree (AST) node definitions for Informix 4GL.

This module defines all AST node types using Python dataclasses.
Each node preserves position information from the source code for error reporting.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..lexer import TokenType


@dataclass
class ASTNode(ABC):
    """
    Base class for all AST nodes.

    All nodes include position information from the source code
    for error reporting and debugging.
    """

    line: int
    column: int

    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        """Accept a visitor for the visitor pattern."""
        pass

    def to_dict(self) -> dict:
        """Convert AST node to dictionary representation."""
        result = {
            "type": self.__class__.__name__,
            "line": self.line,
            "column": self.column,
        }

        # Add all fields except line and column
        for key, value in self.__dict__.items():
            if key not in ("line", "column"):
                if isinstance(value, ASTNode):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [
                        item.to_dict() if isinstance(item, ASTNode) else item for item in value
                    ]
                else:
                    result[key] = value

        return result


# ============================================================================
# Expression Nodes
# ============================================================================


@dataclass
class Expression(ASTNode):
    """Base class for all expression nodes."""

    pass


@dataclass
class Literal(Expression):
    """Literal value (integer, float, string, boolean)."""

    value: Any
    token_type: TokenType

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_literal(self)


@dataclass
class Identifier(Expression):
    """Variable or function identifier."""

    name: str

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_identifier(self)


@dataclass
class BinaryOp(Expression):
    """Binary operation (e.g., a + b, x < y)."""

    left: Expression
    operator: str
    operator_type: TokenType
    right: Expression

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOp(Expression):
    """Unary operation (e.g., -x, NOT y)."""

    operator: str
    operator_type: TokenType
    operand: Expression

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_unary_op(self)


@dataclass
class FunctionCall(Expression):
    """Function call expression."""

    function_name: str
    arguments: List[Expression]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_call(self)


@dataclass
class ArrayAccess(Expression):
    """Array element access (e.g., arr[i])."""

    array_name: str
    index: Expression

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_array_access(self)


# ============================================================================
# Statement Nodes
# ============================================================================


@dataclass
class Statement(ASTNode):
    """Base class for all statement nodes."""

    pass


@dataclass
class DefineStatement(Statement):
    """Variable definition statement (DEFINE x INTEGER)."""

    variables: List[str]
    data_type: str
    type_params: Optional[List[Any]] = None  # For CHAR(50), DECIMAL(10,2), etc.
    qualifier_start: Optional[str] = None  # For DATETIME/INTERVAL qualifiers (e.g., YEAR)
    qualifier_end: Optional[str] = None  # For DATETIME/INTERVAL qualifiers (e.g., SECOND)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_define_statement(self)


@dataclass
class LetStatement(Statement):
    """Assignment statement (LET x = expr)."""

    variable: str
    value: Expression

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_let_statement(self)


@dataclass
class DisplayStatement(Statement):
    """Display/output statement (DISPLAY expr1, expr2, ...)."""

    expressions: List[Expression]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_display_statement(self)


@dataclass
class ReturnStatement(Statement):
    """Return statement (RETURN expr)."""

    value: Optional[Expression] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_return_statement(self)


@dataclass
class CallStatement(Statement):
    """Call statement (CALL function_name(args))."""

    function_name: str
    arguments: List[Expression]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_call_statement(self)


@dataclass
class ExitStatement(Statement):
    """Exit statement (EXIT FOR/WHILE/FOREACH)."""

    loop_type: Optional[str] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_exit_statement(self)


@dataclass
class ContinueStatement(Statement):
    """Continue statement (CONTINUE FOR/WHILE/FOREACH)."""

    loop_type: Optional[str] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_continue_statement(self)


# ============================================================================
# Control Flow Nodes
# ============================================================================


@dataclass
class IfStatement(Statement):
    """If-then-else statement."""

    condition: Expression
    then_block: List[Statement]
    elif_blocks: List[tuple[Expression, List[Statement]]] = field(default_factory=list)
    else_block: Optional[List[Statement]] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_if_statement(self)


@dataclass
class ForStatement(Statement):
    """For loop statement (FOR i = start TO end [STEP step])."""

    variable: str
    start_value: Expression
    end_value: Expression
    step_value: Optional[Expression] = None
    body: List[Statement] = field(default_factory=list)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_for_statement(self)


@dataclass
class WhileStatement(Statement):
    """While loop statement (WHILE condition ... END WHILE)."""

    condition: Expression
    body: List[Statement]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_while_statement(self)


@dataclass
class CaseStatement(Statement):
    """Case/switch statement."""

    @dataclass
    class WhenClause:
        """When clause in case statement."""

        condition: Expression
        statements: List[Statement]

    expression: Optional[Expression] = None  # None for CASE without expression
    when_clauses: List[WhenClause] = field(default_factory=list)
    otherwise_block: Optional[List[Statement]] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_case_statement(self)


@dataclass
class ForeachStatement(Statement):
    """Foreach loop for cursor iteration."""

    cursor_name: str
    into_variables: List[str]
    body: List[Statement]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_foreach_statement(self)


# ============================================================================
# Function and Program Structure Nodes
# ============================================================================


@dataclass
class Parameter:
    """Function parameter definition."""

    name: str
    data_type: Optional[str] = None
    type_params: Optional[List[Any]] = None
    line: int = 0
    column: int = 0


@dataclass
class FunctionDef(ASTNode):
    """Function definition."""

    name: str
    parameters: List[Parameter]
    body: List[Statement]
    return_type: Optional[str] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_def(self)


@dataclass
class MainBlock(ASTNode):
    """Main program block (MAIN ... END MAIN)."""

    body: List[Statement]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_main_block(self)


@dataclass
class GlobalsBlock(ASTNode):
    """GLOBALS ... END GLOBALS block with global variable definitions."""

    body: List[Statement]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_globals_block(self)


@dataclass
class Program(ASTNode):
    """Top-level program node containing all functions and main block."""

    functions: List[FunctionDef]
    main_block: Optional[MainBlock] = None
    global_defines: List["DefineStatement"] = field(default_factory=list)
    database: Optional[str] = None
    globals_block: Optional["GlobalsBlock"] = None
    globals_imports: List[str] = field(default_factory=list)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_program(self)


# ============================================================================
# SQL Statement Nodes
# ============================================================================


@dataclass
class SQLStatement(Statement):
    """Base class for SQL statement nodes."""

    pass


@dataclass
class SelectStatement(SQLStatement):
    """SELECT statement."""

    columns: List[str]
    into_variables: Optional[List[str]] = None
    from_table: Optional[str] = None
    where_clause: Optional[Expression] = None
    order_by: Optional[List[tuple[str, Optional[str]]]] = None  # [(column, ASC|DESC|None)]
    group_by: Optional[List[str]] = None
    first_n: Optional[int] = None  # FIRST N modifier
    distinct: bool = False  # SELECT DISTINCT
    having_clause: Optional[Expression] = None  # HAVING clause (with GROUP BY)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_select_statement(self)


@dataclass
class InsertStatement(SQLStatement):
    """INSERT statement."""

    table_name: str
    columns: Optional[List[str]] = None
    values: Optional[List[Expression]] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_insert_statement(self)


@dataclass
class UpdateStatement(SQLStatement):
    """UPDATE statement."""

    table_name: str
    assignments: List[tuple[str, Expression]]  # [(column, value)]
    where_clause: Optional[Expression] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_update_statement(self)


@dataclass
class DeleteStatement(SQLStatement):
    """DELETE statement."""

    table_name: str
    where_clause: Optional[Expression] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_delete_statement(self)


@dataclass
class DeclareStatement(Statement):
    """DECLARE statement for cursors."""

    cursor_name: str
    select_statement: Optional[SelectStatement] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_declare_statement(self)


@dataclass
class OpenStatement(Statement):
    """OPEN cursor statement."""

    cursor_name: str
    using_variables: Optional[List[str]] = (
        None  # For parametric cursors: OPEN cursor USING var1, var2
    )

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_open_statement(self)


@dataclass
class CloseStatement(Statement):
    """CLOSE cursor statement."""

    cursor_name: str

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_close_statement(self)


@dataclass
class FreeStatement(Statement):
    """FREE cursor statement."""

    cursor_name: str

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_free_statement(self)


@dataclass
class BeginWorkStatement(Statement):
    """BEGIN WORK statement to start a transaction."""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_begin_work_statement(self)


@dataclass
class CommitWorkStatement(Statement):
    """COMMIT WORK statement to commit a transaction."""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_commit_work_statement(self)


@dataclass
class RollbackWorkStatement(Statement):
    """ROLLBACK WORK statement to rollback a transaction."""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_rollback_work_statement(self)


@dataclass
class DatabaseStatement(Statement):
    """DATABASE statement to connect to a database."""

    database_name: str
    host: Optional[str] = None
    port: Optional[int] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_database_statement(self)


# ============================================================================
# Visitor Pattern Base Class
# ============================================================================


class ASTVisitor(ABC):
    """
    Base class for AST visitors (visitor pattern).

    This allows different operations on the AST (interpretation, code generation,
    optimization, etc.) without modifying the AST node classes.
    """

    @abstractmethod
    def visit_literal(self, node: Literal) -> Any:
        pass

    @abstractmethod
    def visit_identifier(self, node: Identifier) -> Any:
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOp) -> Any:
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOp) -> Any:
        pass

    @abstractmethod
    def visit_function_call(self, node: FunctionCall) -> Any:
        pass

    @abstractmethod
    def visit_array_access(self, node: ArrayAccess) -> Any:
        pass

    @abstractmethod
    def visit_define_statement(self, node: DefineStatement) -> Any:
        pass

    @abstractmethod
    def visit_let_statement(self, node: LetStatement) -> Any:
        pass

    @abstractmethod
    def visit_display_statement(self, node: DisplayStatement) -> Any:
        pass

    @abstractmethod
    def visit_return_statement(self, node: ReturnStatement) -> Any:
        pass

    @abstractmethod
    def visit_call_statement(self, node: CallStatement) -> Any:
        pass

    @abstractmethod
    def visit_exit_statement(self, node: ExitStatement) -> Any:
        pass

    @abstractmethod
    def visit_continue_statement(self, node: ContinueStatement) -> Any:
        pass

    @abstractmethod
    def visit_if_statement(self, node: IfStatement) -> Any:
        pass

    @abstractmethod
    def visit_for_statement(self, node: ForStatement) -> Any:
        pass

    @abstractmethod
    def visit_while_statement(self, node: WhileStatement) -> Any:
        pass

    @abstractmethod
    def visit_case_statement(self, node: CaseStatement) -> Any:
        pass

    @abstractmethod
    def visit_foreach_statement(self, node: ForeachStatement) -> Any:
        pass

    @abstractmethod
    def visit_function_def(self, node: FunctionDef) -> Any:
        pass

    @abstractmethod
    def visit_main_block(self, node: MainBlock) -> Any:
        pass

    @abstractmethod
    def visit_program(self, node: Program) -> Any:
        pass

    @abstractmethod
    def visit_select_statement(self, node: SelectStatement) -> Any:
        pass

    @abstractmethod
    def visit_insert_statement(self, node: InsertStatement) -> Any:
        pass

    @abstractmethod
    def visit_update_statement(self, node: UpdateStatement) -> Any:
        pass

    @abstractmethod
    def visit_delete_statement(self, node: DeleteStatement) -> Any:
        pass

    @abstractmethod
    def visit_declare_statement(self, node: DeclareStatement) -> Any:
        pass

    @abstractmethod
    def visit_open_statement(self, node: OpenStatement) -> Any:
        pass

    @abstractmethod
    def visit_close_statement(self, node: CloseStatement) -> Any:
        pass

    @abstractmethod
    def visit_free_statement(self, node: FreeStatement) -> Any:
        pass

    @abstractmethod
    def visit_begin_work_statement(self, node: BeginWorkStatement) -> Any:
        pass

    @abstractmethod
    def visit_commit_work_statement(self, node: CommitWorkStatement) -> Any:
        pass

    @abstractmethod
    def visit_rollback_work_statement(self, node: RollbackWorkStatement) -> Any:
        pass

    @abstractmethod
    def visit_database_statement(self, node: DatabaseStatement) -> Any:
        pass
