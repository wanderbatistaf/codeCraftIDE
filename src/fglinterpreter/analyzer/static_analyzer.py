"""Static analyzer for FGL code.

This module provides static analysis capabilities including:
- Undefined variable detection
- Type inference from assignments
- Code action suggestions (quick fixes)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..parser.ast_nodes import (
    ASTNode,
    ASTVisitor,
    BinaryOp,
    DefineStatement,
    ForeachStatement,
    ForStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    LetStatement,
    Literal,
    MainBlock,
    Program,
    ReturnStatement,
    UnaryOp,
    WhileStatement,
)


class DiagnosticSeverity(Enum):
    """Severity levels for diagnostics."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class QuickFix:
    """A suggested quick fix for a diagnostic."""

    title: str
    new_text: str
    insert_line: int
    insert_column: int = 0
    description: Optional[str] = None


@dataclass
class Diagnostic:
    """A diagnostic message (error, warning, etc.)."""

    severity: DiagnosticSeverity
    message: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    quick_fixes: List[QuickFix] = field(default_factory=list)


@dataclass
class UndefinedVariable:
    """Information about an undefined variable."""

    name: str
    line: int
    column: int
    inferred_type: Optional[str] = None
    inferred_params: Optional[List[Any]] = None
    context: str = "usage"  # "let_assignment", "usage", "parameter"


class TypeInferrer:
    """Infers types from AST nodes."""

    @staticmethod
    def infer_from_value(value_node: ASTNode) -> tuple[Optional[str], Optional[List[Any]]]:
        """Infer type from a value expression.

        Returns:
            Tuple of (data_type, type_params)
        """
        if isinstance(value_node, Literal):
            return TypeInferrer._infer_from_literal(value_node)
        elif isinstance(value_node, FunctionCall):
            return TypeInferrer._infer_from_function(value_node)
        elif isinstance(value_node, BinaryOp):
            return TypeInferrer._infer_from_binary_op(value_node)

        # Default to generic types for unknown expressions
        return None, None

    @staticmethod
    def _infer_from_literal(literal: Literal) -> tuple[Optional[str], Optional[List[Any]]]:
        """Infer type from a literal value."""
        value = literal.value

        # String literal
        if isinstance(value, str):
            length = len(value)
            # Use a reasonable minimum length
            length = max(length, 1)
            return "CHAR", [length]

        # Integer literal
        elif isinstance(value, int):
            # Choose SMALLINT for small values, INTEGER otherwise
            if -32768 <= value <= 32767:
                return "SMALLINT", None
            else:
                return "INTEGER", None

        # Float/Decimal literal
        elif isinstance(value, float):
            return "DECIMAL", [10, 2]  # Default to DECIMAL(10,2)

        # Boolean (might be represented as integer in some cases)
        elif isinstance(value, bool):
            return "SMALLINT", None

        return None, None

    @staticmethod
    def _infer_from_function(func_call: FunctionCall) -> tuple[Optional[str], Optional[List[Any]]]:
        """Infer type from a function call."""
        func_name = func_call.function_name.upper()

        # Date/Time functions
        if func_name in ("TODAY", "CURRENT"):
            return "DATE", None
        elif func_name == "MDY":
            return "DATE", None
        elif func_name == "WEEKDAY":
            return "SMALLINT", None
        elif func_name == "MONTH" or func_name == "DAY" or func_name == "YEAR":
            return "SMALLINT", None

        # String functions
        elif func_name in ("UPSHIFT", "DOWNSHIFT", "TRIM", "CLIPPED"):
            return "CHAR", [50]  # Default string length
        elif func_name == "LENGTH":
            return "INTEGER", None

        # Math functions
        elif func_name in ("SQRT", "ABS", "FLOOR", "CEIL"):
            return "DECIMAL", [10, 2]

        # Default for unknown functions
        return None, None

    @staticmethod
    def _infer_from_binary_op(binary_op: BinaryOp) -> tuple[Optional[str], Optional[List[Any]]]:
        """Infer type from a binary operation."""
        # Infer from left operand (could be enhanced to check both sides)
        left_type, left_params = TypeInferrer.infer_from_value(binary_op.left)

        # For arithmetic operations, result might be numeric
        if binary_op.operator in ("+", "-", "*", "/"):
            if left_type in ("INTEGER", "SMALLINT", "DECIMAL", "FLOAT"):
                return left_type, left_params
            # Default to INTEGER for numeric operations
            return "INTEGER", None

        # For comparison operations, result is boolean (SMALLINT)
        elif binary_op.operator in ("=", "!=", "<", ">", "<=", ">=", "<>"):
            return "SMALLINT", None

        # For string concatenation
        elif binary_op.operator == "||":
            return "CHAR", [100]  # Default length for concatenated strings

        return left_type, left_params


class StaticAnalyzer(ASTVisitor):
    """Analyzes FGL AST for errors and warnings before execution."""

    def __init__(self):
        self.diagnostics: List[Diagnostic] = []
        self.undefined_variables: List[UndefinedVariable] = []

        # Track defined variables per scope
        self.scopes: List[Dict[str, DefineStatement]] = [{}]  # Start with global scope
        self.current_scope_level = 0

        # Track all variable references
        self.variable_references: Set[str] = set()

    def visit(self, node: ASTNode) -> Any:
        """Generic visit method that dispatches to specific visitor methods."""
        if node is None:
            return None
        return node.accept(self)

    def analyze(self, program: Program) -> List[Diagnostic]:
        """Analyze a program and return diagnostics."""
        self.diagnostics = []
        self.undefined_variables = []
        self.scopes = [{}]
        self.current_scope_level = 0
        self.variable_references = set()

        # Visit the entire program
        self.visit_program(program)

        # Generate diagnostics for undefined variables
        self._generate_undefined_variable_diagnostics()

        return self.diagnostics

    def _push_scope(self):
        """Enter a new scope (function, block, etc.)."""
        self.scopes.append({})
        self.current_scope_level += 1

    def _pop_scope(self):
        """Exit current scope."""
        if self.current_scope_level > 0:
            self.scopes.pop()
            self.current_scope_level -= 1

    def _define_variable(self, var_name: str, define_stmt: DefineStatement):
        """Register a variable definition in current scope."""
        self.scopes[self.current_scope_level][var_name] = define_stmt

    def _is_defined(self, var_name: str) -> bool:
        """Check if a variable is defined in any accessible scope."""
        # Check from current scope up to global scope
        for scope in reversed(self.scopes):
            if var_name in scope:
                return True
        return False

    def _generate_undefined_variable_diagnostics(self):
        """Generate diagnostics for all undefined variables."""
        for undef_var in self.undefined_variables:
            # Create diagnostic
            diagnostic = Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                message=f"Variable '{undef_var.name}' is not defined",
                line=undef_var.line,
                column=undef_var.column,
            )

            # Generate quick fixes
            quick_fixes = self._generate_quick_fixes(undef_var)
            diagnostic.quick_fixes = quick_fixes

            self.diagnostics.append(diagnostic)

    def _generate_quick_fixes(self, undef_var: UndefinedVariable) -> List[QuickFix]:
        """Generate quick fix suggestions for an undefined variable."""
        quick_fixes = []

        # Determine the type declaration
        if undef_var.inferred_type:
            type_decl = undef_var.inferred_type
            if undef_var.inferred_params:
                params_str = ", ".join(str(p) for p in undef_var.inferred_params)
                type_decl += f"({params_str})"
        else:
            type_decl = "INTEGER"  # Default type

        define_stmt = f"    DEFINE {undef_var.name} {type_decl}\n"

        # Quick fix 1: Add DEFINE at the beginning of current function/main
        quick_fixes.append(
            QuickFix(
                title=f"Define '{undef_var.name}' as {type_decl}",
                new_text=define_stmt,
                insert_line=1,  # Will be adjusted based on context
                description=f"Add 'DEFINE {undef_var.name} {type_decl}' to current scope",
            )
        )

        # Quick fix 2: Add DEFINE globally (if not already in global scope)
        if self.current_scope_level > 0:
            quick_fixes.append(
                QuickFix(
                    title=f"Define '{undef_var.name}' globally as {type_decl}",
                    new_text=define_stmt,
                    insert_line=0,  # Global scope
                    description=f"Add 'DEFINE {undef_var.name} {type_decl}' to global scope",
                )
            )

        return quick_fixes

    # Visitor methods

    def visit_program(self, node: Program) -> Any:
        """Visit a program node."""
        # Visit global defines first (if any)
        for define_stmt in node.global_defines:
            self.visit_define_statement(define_stmt)

        # Visit main block
        if node.main_block:
            self.visit_main_block(node.main_block)

        # Visit functions
        for function in node.functions:
            self.visit_function_def(function)

    def visit_main_block(self, node: MainBlock) -> Any:
        """Visit main block."""
        # Visit all statements
        for statement in node.body:
            self.visit(statement)

    def visit_function_def(self, node: FunctionDef) -> Any:
        """Visit function definition."""
        # Enter new scope for function
        self._push_scope()

        # Define parameters
        for param in node.parameters:
            # Parameters are implicitly defined
            # Create a pseudo DefineStatement for tracking
            pseudo_define = DefineStatement(
                variables=[param],
                data_type="ANY",  # Parameters can be any type
                line=node.line,
                column=node.column,
            )
            self._define_variable(param, pseudo_define)

        # Visit function body
        for statement in node.body:
            self.visit(statement)

        # Exit function scope
        self._pop_scope()

    def visit_define_statement(self, node: DefineStatement) -> Any:
        """Visit DEFINE statement."""
        # Register all variables in this DEFINE
        for var_name in node.variables:
            self._define_variable(var_name, node)

    def visit_let_statement(self, node: LetStatement) -> Any:
        """Visit LET statement."""
        # Check if target variable is defined
        target_name = node.variable

        if not self._is_defined(target_name):
            # Try to infer type from value
            inferred_type, inferred_params = TypeInferrer.infer_from_value(node.value)

            # Record undefined variable
            self.undefined_variables.append(
                UndefinedVariable(
                    name=target_name,
                    line=node.line,
                    column=node.column,
                    inferred_type=inferred_type,
                    inferred_params=inferred_params,
                    context="let_assignment",
                )
            )

        # Visit the value expression (might contain more variable references)
        self.visit(node.value)

    def visit_identifier(self, node: Identifier) -> Any:
        """Visit identifier (variable reference)."""
        var_name = node.name
        self.variable_references.add(var_name)

        # Check if this identifier is defined
        if not self._is_defined(var_name):
            # Only add if not already in undefined list
            if not any(
                uv.name == var_name and uv.line == node.line for uv in self.undefined_variables
            ):
                self.undefined_variables.append(
                    UndefinedVariable(
                        name=var_name, line=node.line, column=node.column, context="usage"
                    )
                )

    def visit_if_statement(self, node: IfStatement) -> Any:
        """Visit IF statement."""
        # Visit condition
        self.visit(node.condition)

        # Visit then branch
        for stmt in node.then_branch:
            self.visit(stmt)

        # Visit else branch if exists
        if node.else_branch:
            for stmt in node.else_branch:
                self.visit(stmt)

    def visit_while_statement(self, node: WhileStatement) -> Any:
        """Visit WHILE statement."""
        self.visit(node.condition)
        for stmt in node.body:
            self.visit(stmt)

    def visit_for_statement(self, node: ForStatement) -> Any:
        """Visit FOR statement."""
        # Check loop variable
        self.visit(node.variable)
        self.visit(node.start)
        self.visit(node.end)

        if node.step:
            self.visit(node.step)

        for stmt in node.body:
            self.visit(stmt)

    def visit_foreach_statement(self, node: ForeachStatement) -> Any:
        """Visit FOREACH statement."""
        # Visit the cursor/query
        # For now, just visit the body
        for stmt in node.body:
            self.visit(stmt)

    def visit_function_call(self, node: FunctionCall) -> Any:
        """Visit function call."""
        # Visit all arguments
        for arg in node.arguments:
            self.visit(arg)

    def visit_return_statement(self, node: ReturnStatement) -> Any:
        """Visit RETURN statement."""
        if node.value:
            self.visit(node.value)

    def visit_binary_op(self, node: BinaryOp) -> Any:
        """Visit binary operation."""
        self.visit(node.left)
        self.visit(node.right)

    def visit_unary_op(self, node: UnaryOp) -> Any:
        """Visit unary operation."""
        self.visit(node.operand)

    def visit_literal(self, node: Literal) -> Any:
        """Visit literal value."""
        # Literals don't need processing
        pass

    def visit_array_access(self, node: Any) -> Any:
        """Visit array access."""
        # Visit the array identifier
        if hasattr(node, "array"):
            self.visit(node.array)
        # Visit index expressions
        if hasattr(node, "indices"):
            for index in node.indices:
                self.visit(index)

    def visit_display_statement(self, node: Any) -> Any:
        """Visit DISPLAY statement."""
        if hasattr(node, "expressions"):
            for expr in node.expressions:
                self.visit(expr)

    def visit_call_statement(self, node: Any) -> Any:
        """Visit CALL statement."""
        if hasattr(node, "function_call"):
            self.visit(node.function_call)

    def visit_exit_statement(self, node: Any) -> Any:
        """Visit EXIT statement."""
        # Nothing to check in EXIT statement
        pass

    def visit_continue_statement(self, node: Any) -> Any:
        """Visit CONTINUE statement."""
        # Nothing to check in CONTINUE statement
        pass

    def visit_case_statement(self, node: Any) -> Any:
        """Visit CASE statement."""
        # Visit test expression
        if hasattr(node, "test_expression") and node.test_expression:
            self.visit(node.test_expression)

        # Visit all when branches
        if hasattr(node, "when_branches"):
            for when_branch in node.when_branches:
                # Visit condition
                if hasattr(when_branch, "condition"):
                    self.visit(when_branch.condition)
                # Visit statements
                if hasattr(when_branch, "statements"):
                    for stmt in when_branch.statements:
                        self.visit(stmt)

        # Visit otherwise branch
        if hasattr(node, "otherwise_branch") and node.otherwise_branch:
            for stmt in node.otherwise_branch:
                self.visit(stmt)

    def visit_select_statement(self, node: Any) -> Any:
        """Visit SELECT statement."""
        # Visit all expressions in the SELECT
        if hasattr(node, "columns"):
            for col in node.columns:
                self.visit(col)
        if hasattr(node, "where_clause"):
            self.visit(node.where_clause)

    def visit_insert_statement(self, node: Any) -> Any:
        """Visit INSERT statement."""
        if hasattr(node, "values"):
            for val in node.values:
                self.visit(val)

    def visit_update_statement(self, node: Any) -> Any:
        """Visit UPDATE statement."""
        if hasattr(node, "assignments"):
            for assignment in node.assignments:
                self.visit(assignment)
        if hasattr(node, "where_clause"):
            self.visit(node.where_clause)

    def visit_delete_statement(self, node: Any) -> Any:
        """Visit DELETE statement."""
        if hasattr(node, "where_clause"):
            self.visit(node.where_clause)

    def visit_declare_statement(self, node: Any) -> Any:
        """Visit DECLARE statement."""
        # Cursors don't define variables, so nothing to check
        pass

    def visit_open_statement(self, node: Any) -> Any:
        """Visit OPEN statement."""
        pass

    def visit_close_statement(self, node: Any) -> Any:
        """Visit CLOSE statement."""
        pass

    def visit_free_statement(self, node: Any) -> Any:
        """Visit FREE statement."""
        pass

    def visit_begin_work_statement(self, node: Any) -> Any:
        """Visit BEGIN WORK statement."""
        pass

    def visit_commit_work_statement(self, node: Any) -> Any:
        """Visit COMMIT WORK statement."""
        pass

    def visit_rollback_work_statement(self, node: Any) -> Any:
        """Visit ROLLBACK WORK statement."""
        pass

    def visit_database_statement(self, node: Any) -> Any:
        """Visit DATABASE statement."""
        pass
