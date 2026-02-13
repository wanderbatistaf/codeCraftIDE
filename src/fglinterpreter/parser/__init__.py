"""
Parser and AST construction for Informix 4GL.

This module provides:
- AST node definitions (Expression, Statement, Program, etc.)
- Parser implementation (recursive descent parser)
- Syntax error handling
"""

from .ast_nodes import (
    ArrayAccess,
    ASTNode,
    ASTVisitor,
    BinaryOp,
    CallStatement,
    CaseStatement,
    CloseStatement,
    ContinueStatement,
    DeclareStatement,
    DefineStatement,
    DeleteStatement,
    DisplayStatement,
    ExitStatement,
    Expression,
    ForeachStatement,
    ForStatement,
    FreeStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    InsertStatement,
    LetStatement,
    Literal,
    MainBlock,
    OpenStatement,
    Parameter,
    Program,
    ReturnStatement,
    SelectStatement,
    SQLStatement,
    Statement,
    UnaryOp,
    UpdateStatement,
    WhileStatement,
)
from .exceptions import (
    InvalidSyntaxError,
    MissingTokenError,
    ParserError,
    UnexpectedEOFError,
    UnexpectedTokenError,
)
from .parser import Parser, parse_source

__all__ = [
    # Parser
    "Parser",
    "parse_source",
    # AST Nodes - Base
    "ASTNode",
    "ASTVisitor",
    "Expression",
    "Statement",
    "SQLStatement",
    # AST Nodes - Expressions
    "Literal",
    "Identifier",
    "BinaryOp",
    "UnaryOp",
    "FunctionCall",
    "ArrayAccess",
    # AST Nodes - Statements
    "DefineStatement",
    "LetStatement",
    "DisplayStatement",
    "ReturnStatement",
    "CallStatement",
    "ExitStatement",
    "ContinueStatement",
    # AST Nodes - Control Flow
    "IfStatement",
    "ForStatement",
    "WhileStatement",
    "CaseStatement",
    "ForeachStatement",
    # AST Nodes - Function/Program
    "Parameter",
    "FunctionDef",
    "MainBlock",
    "Program",
    # AST Nodes - SQL
    "SelectStatement",
    "InsertStatement",
    "UpdateStatement",
    "DeleteStatement",
    "DeclareStatement",
    "OpenStatement",
    "CloseStatement",
    "FreeStatement",
    # Exceptions
    "ParserError",
    "UnexpectedTokenError",
    "UnexpectedEOFError",
    "MissingTokenError",
    "InvalidSyntaxError",
]
