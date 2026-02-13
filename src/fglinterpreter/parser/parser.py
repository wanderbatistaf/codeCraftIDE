"""
Recursive descent parser for Informix 4GL.

This module implements a parser that converts a token stream from the lexer
into an Abstract Syntax Tree (AST).
"""

from typing import List, Optional

from ..lexer import Lexer, Token, TokenType
from .ast_nodes import *
from .exceptions import (
    InvalidSyntaxError,
    ParserError,
    UnexpectedEOFError,
    UnexpectedTokenError,
)


class Parser:
    """
    Recursive descent parser for 4GL source code.

    The parser converts a flat token stream into a hierarchical AST
    representing the program structure.
    """

    def __init__(self, tokens: List[Token]) -> None:
        """
        Initialize the parser with a token list.

        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.position = 0
        self.current_token: Optional[Token] = tokens[0] if tokens else None
        self.errors: List[ParserError] = []
        self.pending_statements: List[Statement] = []  # For multi-part DEFINE statements

    def current(self) -> Optional[Token]:
        """Get the current token without advancing."""
        return self.current_token

    def peek(self, offset: int = 1) -> Optional[Token]:
        """
        Look ahead at a future token without advancing.

        Args:
            offset: How many tokens to look ahead (default 1)

        Returns:
            Token at position + offset, or None if out of bounds
        """
        pos = self.position + offset
        if 0 <= pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def advance(self) -> Token:
        """
        Move to the next token and return the previous one.

        Returns:
            The token that was current before advancing
        """
        prev_token = self.current_token

        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
        else:
            # Stay at EOF
            self.current_token = self.tokens[-1] if self.tokens else None

        return prev_token

    def match(self, *token_types: TokenType) -> bool:
        """
        Check if the current token matches any of the given types.

        Args:
            *token_types: Token types to match against

        Returns:
            True if current token matches any of the types
        """
        if not self.current_token:
            return False
        return self.current_token.type in token_types

    def consume(self, token_type: TokenType, error_message: Optional[str] = None) -> Token:
        """
        Consume a token of the expected type, or raise an error.

        Args:
            token_type: Expected token type
            error_message: Custom error message (optional)

        Returns:
            The consumed token

        Raises:
            UnexpectedTokenError: If the current token doesn't match
        """
        if not self.current_token:
            raise UnexpectedEOFError([token_type])

        if self.current_token.type != token_type:
            message = error_message or f"Expected {token_type.name}"
            raise UnexpectedTokenError(self.current_token, [token_type], message)

        return self.advance()

    def synchronize(self) -> None:
        """
        Synchronize after a parse error by skipping to the next statement boundary.

        This helps with error recovery by finding a safe point to continue parsing.
        """
        self.advance()

        while self.current_token and self.current_token.type != TokenType.EOF:
            # Look for statement boundaries
            if self.current_token.type in (
                TokenType.END,
                TokenType.MAIN,
                TokenType.FUNCTION,
                TokenType.RETURN,
                TokenType.LET,
                TokenType.DEFINE,
                TokenType.IF,
                TokenType.FOR,
                TokenType.WHILE,
                TokenType.CASE,
                TokenType.DISPLAY,
            ):
                return

            self.advance()

    # ========================================================================
    # Main Parsing Entry Points
    # ========================================================================

    def parse(self) -> Program:
        """
        Parse the complete token stream into a Program AST.

        Returns:
            Program AST node

        Raises:
            ParserError: If parsing fails
        """
        functions: List[FunctionDef] = []
        main_block: Optional[MainBlock] = None
        global_defines: List[DefineStatement] = []
        database: Optional[str] = None
        globals_block: Optional[GlobalsBlock] = None
        globals_imports: List[str] = []

        while self.current_token and self.current_token.type != TokenType.EOF:
            try:
                if self.match(TokenType.DATABASE):
                    # Parse DATABASE statement
                    if database:
                        raise InvalidSyntaxError(
                            "Multiple DATABASE statements not allowed", self.current_token
                        )
                    database = self.parse_database_name()
                elif self.match(TokenType.GLOBALS):
                    # Parse GLOBALS block or import
                    if self.peek() and self.peek().type == TokenType.STRING_LITERAL:
                        # GLOBALS "filename"
                        self.advance()  # consume GLOBALS
                        filename_token = self.consume(TokenType.STRING_LITERAL)
                        globals_imports.append(filename_token.value)
                    else:
                        # GLOBALS ... END GLOBALS block
                        if globals_block:
                            raise InvalidSyntaxError(
                                "Multiple GLOBALS blocks not allowed", self.current_token
                            )
                        globals_block = self.parse_globals_block()
                elif self.match(TokenType.DEFINE):
                    # Parse global DEFINE statements with continuations
                    define_stmt = self.parse_define_statement_with_continuations()
                    global_defines.append(define_stmt)
                    # Add any pending continuation statements
                    while self.pending_statements:
                        global_defines.append(self.pending_statements.pop(0))
                elif self.match(TokenType.FUNCTION):
                    functions.append(self.parse_function())
                elif self.match(TokenType.MAIN):
                    if main_block:
                        raise InvalidSyntaxError(
                            "Multiple MAIN blocks not allowed", self.current_token
                        )
                    main_block = self.parse_main_block()
                else:
                    raise UnexpectedTokenError(
                        self.current_token,
                        [
                            TokenType.DATABASE,
                            TokenType.GLOBALS,
                            TokenType.DEFINE,
                            TokenType.FUNCTION,
                            TokenType.MAIN,
                        ],
                        "top-level",
                    )
            except ParserError as e:
                self.errors.append(e)
                self.synchronize()

        # If we collected errors, raise the first one
        if self.errors:
            raise self.errors[0]

        return Program(
            functions=functions,
            main_block=main_block,
            global_defines=global_defines,
            database=database,
            globals_block=globals_block,
            globals_imports=globals_imports,
            line=1,
            column=1,
        )

    def parse_main_block(self) -> MainBlock:
        """
        Parse a MAIN ... END MAIN block.

        Returns:
            MainBlock AST node
        """
        main_token = self.consume(TokenType.MAIN)
        body = self.parse_block_until(TokenType.END)
        self.consume(TokenType.END)
        self.consume(TokenType.MAIN, "Expected MAIN after END")

        return MainBlock(body=body, line=main_token.line, column=main_token.column)

    def parse_database_name(self) -> str:
        """
        Parse a DATABASE name (simple version).

        Syntax: DATABASE database_name

        Returns:
            Database name as string
        """
        self.consume(TokenType.DATABASE)
        db_name_token = self.consume(TokenType.IDENTIFIER, "Expected database name")
        return db_name_token.value

    def parse_globals_block(self) -> GlobalsBlock:
        """
        Parse a GLOBALS ... END GLOBALS block.

        Syntax:
            GLOBALS
                DEFINE ...
            END GLOBALS

        Returns:
            GlobalsBlock AST node
        """
        globals_token = self.consume(TokenType.GLOBALS)
        body = self.parse_block_until(TokenType.END)
        self.consume(TokenType.END)
        self.consume(TokenType.GLOBALS, "Expected GLOBALS after END")

        return GlobalsBlock(body=body, line=globals_token.line, column=globals_token.column)

    def parse_function(self) -> FunctionDef:
        """
        Parse a function definition.

        Returns:
            FunctionDef AST node
        """
        func_token = self.consume(TokenType.FUNCTION)

        # Function name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        function_name = name_token.value

        # Parameters
        self.consume(TokenType.LPAREN)
        parameters = self.parse_parameter_list()
        self.consume(TokenType.RPAREN)

        # Function body
        body = self.parse_block_until(TokenType.END)

        self.consume(TokenType.END)
        self.consume(TokenType.FUNCTION, "Expected FUNCTION after END")

        return FunctionDef(
            name=function_name,
            parameters=parameters,
            body=body,
            line=func_token.line,
            column=func_token.column,
        )

    def parse_parameter_list(self) -> List[Parameter]:
        """
        Parse function parameter list.

        Returns:
            List of Parameter objects
        """
        parameters: List[Parameter] = []

        if self.match(TokenType.RPAREN):
            return parameters

        while True:
            if not self.match(TokenType.IDENTIFIER):
                break

            param_token = self.advance()
            parameters.append(
                Parameter(name=param_token.value, line=param_token.line, column=param_token.column)
            )

            if not self.match(TokenType.COMMA):
                break

            self.advance()  # Consume comma

        return parameters

    def parse_block_until(self, *end_tokens: TokenType) -> List[Statement]:
        """
        Parse a block of statements until one of the end tokens is reached.

        Args:
            *end_tokens: Token types that mark the end of the block

        Returns:
            List of Statement AST nodes
        """
        statements: List[Statement] = []

        while self.current_token and not self.match(*end_tokens, TokenType.EOF):
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append(e)
                self.synchronize()

        return statements

    # ========================================================================
    # Statement Parsing
    # ========================================================================

    def parse_statement(self) -> Optional[Statement]:
        """
        Parse a single statement.

        Returns:
            Statement AST node, or None if no statement found
        """
        # Check if there are pending statements from previous multi-part parsing
        if self.pending_statements:
            return self.pending_statements.pop(0)

        if not self.current_token or self.current_token.type == TokenType.EOF:
            return None

        # DEFINE statement
        if self.match(TokenType.DEFINE):
            return self.parse_define_statement_with_continuations()

        # LET statement
        if self.match(TokenType.LET):
            return self.parse_let_statement()

        # DISPLAY statement
        if self.match(TokenType.DISPLAY):
            return self.parse_display_statement()

        # IF statement
        if self.match(TokenType.IF):
            return self.parse_if_statement()

        # FOR statement
        if self.match(TokenType.FOR):
            return self.parse_for_statement()

        # WHILE statement
        if self.match(TokenType.WHILE):
            return self.parse_while_statement()

        # CASE statement
        if self.match(TokenType.CASE):
            return self.parse_case_statement()

        # RETURN statement
        if self.match(TokenType.RETURN):
            return self.parse_return_statement()

        # CALL statement
        if self.match(TokenType.CALL):
            return self.parse_call_statement()

        # EXIT statement
        if self.match(TokenType.EXIT):
            return self.parse_exit_statement()

        # CONTINUE statement
        if self.match(TokenType.CONTINUE):
            return self.parse_continue_statement()

        # SQL statements
        if self.match(TokenType.SELECT):
            return self.parse_select_statement()

        if self.match(TokenType.INSERT):
            return self.parse_insert_statement()

        if self.match(TokenType.UPDATE):
            return self.parse_update_statement()

        if self.match(TokenType.DELETE):
            return self.parse_delete_statement()

        if self.match(TokenType.DECLARE):
            return self.parse_declare_statement()

        if self.match(TokenType.OPEN):
            return self.parse_open_statement()

        if self.match(TokenType.CLOSE):
            return self.parse_close_statement()

        if self.match(TokenType.FREE):
            return self.parse_free_statement()

        if self.match(TokenType.FOREACH):
            return self.parse_foreach_statement()

        # Transaction control statements
        if self.match(TokenType.BEGIN):
            return self.parse_begin_work_statement()

        if self.match(TokenType.COMMIT):
            return self.parse_commit_work_statement()

        if self.match(TokenType.ROLLBACK):
            return self.parse_rollback_work_statement()

        # Database statement
        if self.match(TokenType.DATABASE):
            return self.parse_database_statement()

        # Unknown statement
        raise UnexpectedTokenError(self.current_token, context="statement")

    def parse_define_statement_with_continuations(self) -> DefineStatement:
        """
        Parse DEFINE statement with support for multi-line continuations.

        Syntax:
            DEFINE var1 type1, var2 type2, var3 type3

        Returns the first DefineStatement and queues the rest as pending.
        """
        first_stmt = self.parse_define_statement()

        # If there was a trailing comma, parse continuation statements
        while self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            # This is a continuation of the DEFINE (var after comma)
            continuation = self.parse_define_continuation()
            self.pending_statements.append(continuation)

        return first_stmt

    def parse_define_continuation(self) -> DefineStatement:
        """Parse a continuation line of DEFINE (after comma)."""
        # We're already positioned at the variable name (no DEFINE keyword)
        var_token = self.current_token
        variables = [self.consume(TokenType.IDENTIFIER).value]

        # Check for multiple variables with same type
        while (
            self.match(TokenType.COMMA) and self.peek() and self.peek().type == TokenType.IDENTIFIER
        ):
            peek_after = self.peek(2)
            if peek_after and self.is_data_type(peek_after.type):
                # Next is "var type," - stop here
                break
            self.advance()  # consume comma
            variables.append(self.consume(TokenType.IDENTIFIER).value)

        # Parse data type
        if not self.current_token or not self.is_data_type(self.current_token.type):
            raise UnexpectedTokenError(self.current_token, context="expected data type")

        data_type = self.advance().value

        # Parse type parameters
        type_params = None
        if self.match(TokenType.LPAREN):
            self.advance()
            type_params = []
            if self.match(TokenType.INTEGER_LITERAL):
                type_params.append(self.advance().literal)
                if self.match(TokenType.COMMA):
                    self.advance()
                    if self.match(TokenType.INTEGER_LITERAL):
                        type_params.append(self.advance().literal)
            self.consume(TokenType.RPAREN)

        # Consume trailing comma if present
        if self.match(TokenType.COMMA):
            self.advance()

        return DefineStatement(
            variables=variables,
            data_type=data_type,
            type_params=type_params,
            qualifier_start=None,
            qualifier_end=None,
            line=var_token.line,
            column=var_token.column,
        )

    def parse_define_statement(self) -> DefineStatement:
        """
        Parse DEFINE statement.

        Supports both single-type and multi-type formats:
        - DEFINE var1, var2 INTEGER  (same type for all)
        - DEFINE var1 VARCHAR(10), var2 INTEGER  (different types - returns first only)
        """
        define_token = self.advance()  # Consume DEFINE

        # Parse first variable
        variables: List[str] = []
        variables.append(self.consume(TokenType.IDENTIFIER).value)

        # Check if next is comma (multi-var same type) or type (multi-var different types)
        # For multi-type format, we parse only the first variable and type,
        # then let the comma trigger another DEFINE parse
        if self.match(TokenType.COMMA) and self.peek() and self.peek().type == TokenType.IDENTIFIER:
            # Comma right after variable name means shared-type format:
            # "DEFINE var1, var2, ... type" - all variables get the same type
            while self.match(TokenType.COMMA):
                self.advance()
                # Check if next is a type (end of variable list)
                if self.current_token and self.is_data_type(self.current_token.type):
                    break
                variables.append(self.consume(TokenType.IDENTIFIER).value)

        # Parse data type
        data_type_token = self.current_token
        if not data_type_token or not self.is_data_type(data_type_token.type):
            raise UnexpectedTokenError(self.current_token, context="expected data type")

        data_type = self.advance().value

        # Parse type parameters (e.g., CHAR(50), DECIMAL(10,2))
        type_params: Optional[List[Any]] = None
        if self.match(TokenType.LPAREN):
            self.advance()
            type_params = []

            # First parameter
            if self.match(TokenType.INTEGER_LITERAL):
                type_params.append(self.advance().literal)

                # Second parameter (for DECIMAL, etc.)
                if self.match(TokenType.COMMA):
                    self.advance()
                    if self.match(TokenType.INTEGER_LITERAL):
                        type_params.append(self.advance().literal)

            self.consume(TokenType.RPAREN)

        # Parse DATETIME/INTERVAL qualifiers (e.g., YEAR TO SECOND)
        qualifier_start: Optional[str] = None
        qualifier_end: Optional[str] = None
        if data_type.upper() in ("DATETIME", "INTERVAL") and self.is_time_unit(self.current_token):
            # Parse start qualifier (e.g., YEAR, MONTH, DAY, HOUR, MINUTE, SECOND)
            qualifier_start = self.advance().value.upper()

            # Parse TO keyword
            if self.match(TokenType.TO):
                self.advance()

                # Parse end qualifier
                if self.is_time_unit(self.current_token):
                    qualifier_end = self.advance().value.upper()
                else:
                    raise UnexpectedTokenError(
                        self.current_token, context="expected time unit after TO"
                    )

        # If there's a comma after the type, it means more DEFINE statements follow
        # We consume it so the next parse_statement call will handle the next variable
        if self.match(TokenType.COMMA):
            self.advance()

        return DefineStatement(
            variables=variables,
            data_type=data_type,
            type_params=type_params,
            qualifier_start=qualifier_start,
            qualifier_end=qualifier_end,
            line=define_token.line,
            column=define_token.column,
        )

    def parse_let_statement(self) -> LetStatement:
        """Parse LET statement."""
        let_token = self.advance()  # Consume LET
        variable = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.EQUAL)
        value = self.parse_expression()

        return LetStatement(
            variable=variable, value=value, line=let_token.line, column=let_token.column
        )

    def parse_display_statement(self) -> DisplayStatement:
        """Parse DISPLAY statement."""
        display_token = self.advance()  # Consume DISPLAY

        expressions: List[Expression] = []
        expressions.append(self.parse_expression())

        while self.match(TokenType.COMMA):
            self.advance()
            expressions.append(self.parse_expression())

        return DisplayStatement(
            expressions=expressions, line=display_token.line, column=display_token.column
        )

    def parse_return_statement(self) -> ReturnStatement:
        """Parse RETURN statement."""
        return_token = self.advance()  # Consume RETURN

        # Check if there's an expression to return
        value: Optional[Expression] = None
        if not self.match(TokenType.END, TokenType.EOF):
            # Try to parse an expression if not at block end
            try:
                value = self.parse_expression()
            except ParserError:
                # No expression, just RETURN
                pass

        return ReturnStatement(value=value, line=return_token.line, column=return_token.column)

    def parse_call_statement(self) -> CallStatement:
        """Parse CALL statement."""
        call_token = self.advance()  # Consume CALL
        function_name = self.consume(TokenType.IDENTIFIER).value

        self.consume(TokenType.LPAREN)
        arguments = self.parse_argument_list()
        self.consume(TokenType.RPAREN)

        return CallStatement(
            function_name=function_name,
            arguments=arguments,
            line=call_token.line,
            column=call_token.column,
        )

    def parse_exit_statement(self) -> ExitStatement:
        """Parse EXIT statement."""
        exit_token = self.advance()  # Consume EXIT

        loop_type: Optional[str] = None
        if self.match(TokenType.FOR, TokenType.WHILE, TokenType.FOREACH):
            loop_type = self.advance().value

        return ExitStatement(loop_type=loop_type, line=exit_token.line, column=exit_token.column)

    def parse_continue_statement(self) -> ContinueStatement:
        """Parse CONTINUE statement."""
        continue_token = self.advance()  # Consume CONTINUE

        loop_type: Optional[str] = None
        if self.match(TokenType.FOR, TokenType.WHILE, TokenType.FOREACH):
            loop_type = self.advance().value

        return ContinueStatement(
            loop_type=loop_type, line=continue_token.line, column=continue_token.column
        )

    # ========================================================================
    # Control Flow Parsing
    # ========================================================================

    def parse_if_statement(self) -> IfStatement:
        """Parse IF statement."""
        if_token = self.advance()  # Consume IF
        condition = self.parse_expression()
        self.consume(TokenType.THEN)

        then_block = self.parse_block_until(TokenType.ELIF, TokenType.ELSE, TokenType.END)

        # Handle ELIF blocks
        elif_blocks: List[tuple[Expression, List[Statement]]] = []
        while self.match(TokenType.ELIF):
            self.advance()
            elif_condition = self.parse_expression()
            self.consume(TokenType.THEN)
            elif_body = self.parse_block_until(TokenType.ELIF, TokenType.ELSE, TokenType.END)
            elif_blocks.append((elif_condition, elif_body))

        # Handle ELSE block
        else_block: Optional[List[Statement]] = None
        if self.match(TokenType.ELSE):
            self.advance()
            else_block = self.parse_block_until(TokenType.END)

        self.consume(TokenType.END)
        self.consume(TokenType.IF, "Expected IF after END")

        return IfStatement(
            condition=condition,
            then_block=then_block,
            elif_blocks=elif_blocks,
            else_block=else_block,
            line=if_token.line,
            column=if_token.column,
        )

    def parse_for_statement(self) -> ForStatement:
        """Parse FOR statement."""
        for_token = self.advance()  # Consume FOR

        variable = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.EQUAL)
        start_value = self.parse_expression()
        self.consume(TokenType.TO)
        end_value = self.parse_expression()

        step_value: Optional[Expression] = None
        if self.match(TokenType.STEP):
            self.advance()
            step_value = self.parse_expression()

        body = self.parse_block_until(TokenType.END)
        self.consume(TokenType.END)
        self.consume(TokenType.FOR, "Expected FOR after END")

        return ForStatement(
            variable=variable,
            start_value=start_value,
            end_value=end_value,
            step_value=step_value,
            body=body,
            line=for_token.line,
            column=for_token.column,
        )

    def parse_while_statement(self) -> WhileStatement:
        """Parse WHILE statement."""
        while_token = self.advance()  # Consume WHILE
        condition = self.parse_expression()

        body = self.parse_block_until(TokenType.END)
        self.consume(TokenType.END)
        self.consume(TokenType.WHILE, "Expected WHILE after END")

        return WhileStatement(
            condition=condition, body=body, line=while_token.line, column=while_token.column
        )

    def parse_case_statement(self) -> CaseStatement:
        """Parse CASE statement."""
        case_token = self.advance()  # Consume CASE

        # Optional expression after CASE
        expression: Optional[Expression] = None
        if not self.match(TokenType.WHEN):
            expression = self.parse_expression()

        # Parse WHEN clauses
        when_clauses: List[CaseStatement.WhenClause] = []
        while self.match(TokenType.WHEN):
            self.advance()
            condition = self.parse_expression()
            statements = self.parse_block_until(TokenType.WHEN, TokenType.OTHERWISE, TokenType.END)
            when_clauses.append(CaseStatement.WhenClause(condition, statements))

        # Optional OTHERWISE block
        otherwise_block: Optional[List[Statement]] = None
        if self.match(TokenType.OTHERWISE):
            self.advance()
            otherwise_block = self.parse_block_until(TokenType.END)

        self.consume(TokenType.END)
        self.consume(TokenType.CASE, "Expected CASE after END")

        return CaseStatement(
            expression=expression,
            when_clauses=when_clauses,
            otherwise_block=otherwise_block,
            line=case_token.line,
            column=case_token.column,
        )

    def parse_foreach_statement(self) -> ForeachStatement:
        """Parse FOREACH statement."""
        foreach_token = self.advance()  # Consume FOREACH

        cursor_name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.INTO)

        into_variables: List[str] = []
        into_variables.append(self.consume(TokenType.IDENTIFIER).value)

        while self.match(TokenType.COMMA):
            self.advance()
            into_variables.append(self.consume(TokenType.IDENTIFIER).value)

        body = self.parse_block_until(TokenType.END)
        self.consume(TokenType.END)
        self.consume(TokenType.FOREACH, "Expected FOREACH after END")

        return ForeachStatement(
            cursor_name=cursor_name,
            into_variables=into_variables,
            body=body,
            line=foreach_token.line,
            column=foreach_token.column,
        )

    # ========================================================================
    # SQL Statement Parsing (Simplified)
    # ========================================================================

    def parse_select_statement(self) -> SelectStatement:
        """Parse SELECT statement with full support for cursors."""
        select_token = self.advance()  # Consume SELECT

        # Parse optional DISTINCT
        distinct: bool = False
        if self.match(TokenType.DISTINCT):
            self.advance()
            distinct = True

        # Parse optional FIRST N modifier
        first_n: Optional[int] = None
        if self.match(TokenType.FIRST):
            self.advance()
            if self.match(TokenType.INTEGER_LITERAL):
                first_n = self.advance().literal
            else:
                raise UnexpectedTokenError(
                    self.current_token, [TokenType.INTEGER_LITERAL], "Expected integer after FIRST"
                )

        # Parse column list - support *, identifiers, and function calls
        columns: List[str] = []

        # Handle SELECT *
        if self.match(TokenType.MULTIPLY):
            self.advance()
            columns.append("*")
        else:
            # Parse first column (identifier or function call)
            columns.append(self.parse_select_column())

            while self.match(TokenType.COMMA):
                self.advance()
                columns.append(self.parse_select_column())

        # Parse INTO clause
        into_variables: Optional[List[str]] = None
        if self.match(TokenType.INTO):
            self.advance()
            into_variables = []
            into_variables.append(self.consume(TokenType.IDENTIFIER).value)

            while self.match(TokenType.COMMA):
                self.advance()
                into_variables.append(self.consume(TokenType.IDENTIFIER).value)

        # Parse FROM clause
        from_table: Optional[str] = None
        if self.match(TokenType.FROM):
            self.advance()
            from_table = self.consume(TokenType.IDENTIFIER).value

        # Parse WHERE clause
        where_clause: Optional[Expression] = None
        if self.match(TokenType.WHERE):
            self.advance()
            where_clause = self.parse_expression()

        # Parse GROUP BY clause
        group_by: Optional[List[str]] = None
        if self.match(TokenType.GROUP):
            self.advance()
            self.consume(TokenType.BY, "Expected BY after GROUP")
            group_by = []
            group_by.append(self.consume(TokenType.IDENTIFIER).value)

            while self.match(TokenType.COMMA):
                self.advance()
                group_by.append(self.consume(TokenType.IDENTIFIER).value)

        # Parse HAVING clause (must come after GROUP BY)
        having_clause: Optional[Expression] = None
        if self.match(TokenType.HAVING):
            self.advance()
            having_clause = self.parse_expression()

        # Parse ORDER BY clause
        order_by: Optional[List[tuple[str, Optional[str]]]] = None
        if self.match(TokenType.ORDER):
            self.advance()
            self.consume(TokenType.BY, "Expected BY after ORDER")
            order_by = []

            # Parse first order column
            column_name = self.consume(TokenType.IDENTIFIER).value
            direction: Optional[str] = None
            if self.match(TokenType.ASC, TokenType.DESC):
                direction = self.advance().value
            order_by.append((column_name, direction))

            # Parse additional order columns
            while self.match(TokenType.COMMA):
                self.advance()
                column_name = self.consume(TokenType.IDENTIFIER).value
                direction = None
                if self.match(TokenType.ASC, TokenType.DESC):
                    direction = self.advance().value
                order_by.append((column_name, direction))

        return SelectStatement(
            columns=columns,
            into_variables=into_variables,
            from_table=from_table,
            where_clause=where_clause,
            order_by=order_by,
            group_by=group_by,
            first_n=first_n,
            distinct=distinct,
            having_clause=having_clause,
            line=select_token.line,
            column=select_token.column,
        )

    def parse_select_column(self) -> str:
        """
        Parse a column specification in SELECT list.
        Handles identifiers and function calls like COUNT(*), SUM(column), etc.
        """
        if not self.match(TokenType.IDENTIFIER):
            raise UnexpectedTokenError(
                self.current_token, [TokenType.IDENTIFIER], "Expected column name or function"
            )

        name = self.advance().value

        # Check if it's a function call
        if self.match(TokenType.LPAREN):
            self.advance()

            # Build function call string
            func_str = name + "("

            # Handle special case: COUNT(*), MAX(*), etc.
            if self.match(TokenType.MULTIPLY):
                self.advance()
                func_str += "*"
            elif not self.match(TokenType.RPAREN):
                # Parse function arguments (column names or expressions)
                # For simplicity, we'll just capture the identifier
                if self.match(TokenType.IDENTIFIER):
                    func_str += self.advance().value

                    # Handle multiple arguments
                    while self.match(TokenType.COMMA):
                        self.advance()
                        func_str += ", "
                        if self.match(TokenType.IDENTIFIER):
                            func_str += self.advance().value

            self.consume(TokenType.RPAREN)
            func_str += ")"

            return func_str

        return name

    def parse_insert_statement(self) -> InsertStatement:
        """Parse INSERT statement (simplified)."""
        insert_token = self.advance()  # Consume INSERT
        self.consume(TokenType.INTO)
        table_name = self.consume(TokenType.IDENTIFIER).value

        # Parse column list
        columns: Optional[List[str]] = None
        if self.match(TokenType.LPAREN):
            self.advance()
            columns = []
            columns.append(self.consume(TokenType.IDENTIFIER).value)

            while self.match(TokenType.COMMA):
                self.advance()
                columns.append(self.consume(TokenType.IDENTIFIER).value)

            self.consume(TokenType.RPAREN)

        # Parse VALUES clause
        values: Optional[List[Expression]] = None
        if self.match(TokenType.VALUES):
            self.advance()
            self.consume(TokenType.LPAREN)
            values = []
            values.append(self.parse_expression())

            while self.match(TokenType.COMMA):
                self.advance()
                values.append(self.parse_expression())

            self.consume(TokenType.RPAREN)

        return InsertStatement(
            table_name=table_name,
            columns=columns,
            values=values,
            line=insert_token.line,
            column=insert_token.column,
        )

    def parse_update_statement(self) -> UpdateStatement:
        """Parse UPDATE statement (simplified)."""
        update_token = self.advance()  # Consume UPDATE
        table_name = self.consume(TokenType.IDENTIFIER).value

        self.consume(TokenType.SET)

        # Parse assignments
        assignments: List[tuple[str, Expression]] = []
        column = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.EQUAL)
        value = self.parse_expression()
        assignments.append((column, value))

        while self.match(TokenType.COMMA):
            self.advance()
            column = self.consume(TokenType.IDENTIFIER).value
            self.consume(TokenType.EQUAL)
            value = self.parse_expression()
            assignments.append((column, value))

        # Parse WHERE clause
        where_clause: Optional[Expression] = None
        if self.match(TokenType.WHERE):
            self.advance()
            where_clause = self.parse_expression()

        return UpdateStatement(
            table_name=table_name,
            assignments=assignments,
            where_clause=where_clause,
            line=update_token.line,
            column=update_token.column,
        )

    def parse_delete_statement(self) -> DeleteStatement:
        """Parse DELETE statement."""
        delete_token = self.advance()  # Consume DELETE
        self.consume(TokenType.FROM)
        table_name = self.consume(TokenType.IDENTIFIER).value

        # Parse WHERE clause
        where_clause: Optional[Expression] = None
        if self.match(TokenType.WHERE):
            self.advance()
            where_clause = self.parse_expression()

        return DeleteStatement(
            table_name=table_name,
            where_clause=where_clause,
            line=delete_token.line,
            column=delete_token.column,
        )

    def parse_declare_statement(self) -> DeclareStatement:
        """Parse DECLARE statement (simplified)."""
        declare_token = self.advance()  # Consume DECLARE
        cursor_name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.CURSOR)
        self.consume(TokenType.FOR)

        # Parse the SELECT statement
        select_stmt = self.parse_select_statement()

        return DeclareStatement(
            cursor_name=cursor_name,
            select_statement=select_stmt,
            line=declare_token.line,
            column=declare_token.column,
        )

    def parse_open_statement(self) -> OpenStatement:
        """Parse OPEN statement with optional USING clause."""
        open_token = self.advance()  # Consume OPEN
        cursor_name = self.consume(TokenType.IDENTIFIER).value

        # Parse optional USING clause for parametric cursors
        using_variables = None
        if self.match(TokenType.USING):
            self.advance()  # Consume USING
            using_variables = []
            using_variables.append(self.consume(TokenType.IDENTIFIER).value)

            while self.match(TokenType.COMMA):
                self.advance()
                using_variables.append(self.consume(TokenType.IDENTIFIER).value)

        return OpenStatement(
            cursor_name=cursor_name,
            using_variables=using_variables,
            line=open_token.line,
            column=open_token.column,
        )

    def parse_close_statement(self) -> CloseStatement:
        """Parse CLOSE statement."""
        close_token = self.advance()  # Consume CLOSE
        cursor_name = self.consume(TokenType.IDENTIFIER).value

        return CloseStatement(
            cursor_name=cursor_name, line=close_token.line, column=close_token.column
        )

    def parse_free_statement(self) -> FreeStatement:
        """Parse FREE statement."""
        free_token = self.advance()  # Consume FREE
        cursor_name = self.consume(TokenType.IDENTIFIER).value

        return FreeStatement(
            cursor_name=cursor_name, line=free_token.line, column=free_token.column
        )

    def parse_begin_work_statement(self) -> BeginWorkStatement:
        """Parse BEGIN WORK statement."""
        begin_token = self.advance()  # Consume BEGIN
        self.consume(TokenType.WORK, "Expected WORK after BEGIN")

        return BeginWorkStatement(line=begin_token.line, column=begin_token.column)

    def parse_commit_work_statement(self) -> CommitWorkStatement:
        """Parse COMMIT WORK statement."""
        commit_token = self.advance()  # Consume COMMIT
        self.consume(TokenType.WORK, "Expected WORK after COMMIT")

        return CommitWorkStatement(line=commit_token.line, column=commit_token.column)

    def parse_rollback_work_statement(self) -> RollbackWorkStatement:
        """Parse ROLLBACK WORK statement."""
        rollback_token = self.advance()  # Consume ROLLBACK
        self.consume(TokenType.WORK, "Expected WORK after ROLLBACK")

        return RollbackWorkStatement(line=rollback_token.line, column=rollback_token.column)

    def parse_database_statement(self) -> DatabaseStatement:
        """Parse DATABASE statement."""
        database_token = self.advance()  # Consume DATABASE
        database_name = self.consume(TokenType.IDENTIFIER).value

        # Optional @host:port
        host: Optional[str] = None
        port: Optional[int] = None

        # Check for @ symbol
        if self.match(TokenType.AT):
            self.advance()  # Consume @
            host = self.consume(TokenType.IDENTIFIER).value

            # Check for :port
            if self.match(TokenType.COLON):
                self.advance()
                port_token = self.consume(TokenType.INTEGER_LITERAL)
                port = port_token.literal

        return DatabaseStatement(
            database_name=database_name,
            host=host,
            port=port,
            line=database_token.line,
            column=database_token.column,
        )

    # ========================================================================
    # Expression Parsing with Operator Precedence
    # ========================================================================

    def parse_expression(self) -> Expression:
        """Parse an expression with operator precedence."""
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        """Parse logical OR expression."""
        expr = self.parse_logical_and()

        while self.match(TokenType.OR):
            op_token = self.advance()
            right = self.parse_logical_and()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_logical_and(self) -> Expression:
        """Parse logical AND expression."""
        expr = self.parse_equality()

        while self.match(TokenType.AND):
            op_token = self.advance()
            right = self.parse_equality()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_equality(self) -> Expression:
        """Parse equality/inequality expression."""
        expr = self.parse_comparison()

        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            op_token = self.advance()
            right = self.parse_comparison()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_comparison(self) -> Expression:
        """Parse comparison expression including IS NULL, LIKE, IN, BETWEEN."""
        expr = self.parse_additive()

        while True:
            # Handle IS [NOT] NULL
            if self.match(TokenType.IS):
                is_token = self.advance()

                # Check for IS NOT NULL
                if self.match(TokenType.NOT):
                    self.advance()
                    self.consume(TokenType.NULL, "Expected NULL after IS NOT")
                    expr = BinaryOp(
                        left=expr,
                        operator="IS NOT",
                        operator_type=TokenType.NOT_EQUAL,
                        right=Literal(
                            value=None,
                            token_type=TokenType.NULL,
                            line=is_token.line,
                            column=is_token.column,
                        ),
                        line=is_token.line,
                        column=is_token.column,
                    )
                # Check for IS NULL
                elif self.match(TokenType.NULL):
                    self.advance()
                    expr = BinaryOp(
                        left=expr,
                        operator="IS",
                        operator_type=TokenType.EQUAL,
                        right=Literal(
                            value=None,
                            token_type=TokenType.NULL,
                            line=is_token.line,
                            column=is_token.column,
                        ),
                        line=is_token.line,
                        column=is_token.column,
                    )
                else:
                    raise UnexpectedTokenError(
                        self.current_token,
                        [TokenType.NULL, TokenType.NOT],
                        "Expected NULL or NOT after IS",
                    )

            # Handle LIKE operator
            elif self.match(TokenType.LIKE):
                like_token = self.advance()
                pattern = self.parse_additive()
                expr = BinaryOp(
                    left=expr,
                    operator="LIKE",
                    operator_type=TokenType.LIKE,
                    right=pattern,
                    line=like_token.line,
                    column=like_token.column,
                )

            # Handle IN operator
            elif self.match(TokenType.IN):
                in_token = self.advance()
                self.consume(TokenType.LPAREN, "Expected ( after IN")

                # Parse list of values
                values = []
                values.append(self.parse_expression())

                while self.match(TokenType.COMMA):
                    self.advance()
                    values.append(self.parse_expression())

                self.consume(TokenType.RPAREN, "Expected ) after IN list")

                # Create a special IN expression
                # We'll represent this as a BinaryOp where right is a list
                expr = BinaryOp(
                    left=expr,
                    operator="IN",
                    operator_type=TokenType.IN,
                    right=Literal(
                        value=values,
                        token_type=TokenType.IN,
                        line=in_token.line,
                        column=in_token.column,
                    ),
                    line=in_token.line,
                    column=in_token.column,
                )

            # Handle BETWEEN operator
            elif self.match(TokenType.BETWEEN):
                between_token = self.advance()
                low = self.parse_additive()
                self.consume(TokenType.AND, "Expected AND in BETWEEN expression")
                high = self.parse_additive()

                # BETWEEN x AND y is equivalent to (expr >= x AND expr <= y)
                # We'll represent it as a special BETWEEN operator
                expr = BinaryOp(
                    left=expr,
                    operator="BETWEEN",
                    operator_type=TokenType.BETWEEN,
                    right=Literal(
                        value=[low, high],
                        token_type=TokenType.BETWEEN,
                        line=between_token.line,
                        column=between_token.column,
                    ),
                    line=between_token.line,
                    column=between_token.column,
                )

            # Handle regular comparison operators
            elif self.match(
                TokenType.LESS_THAN,
                TokenType.LESS_EQUAL,
                TokenType.GREATER_THAN,
                TokenType.GREATER_EQUAL,
            ):
                op_token = self.advance()
                right = self.parse_additive()
                expr = BinaryOp(
                    left=expr,
                    operator=op_token.value,
                    operator_type=op_token.type,
                    right=right,
                    line=op_token.line,
                    column=op_token.column,
                )
            else:
                break

        return expr

    def parse_additive(self) -> Expression:
        """Parse addition/subtraction/concatenation expression."""
        expr = self.parse_multiplicative()

        while self.match(TokenType.PLUS, TokenType.MINUS, TokenType.CONCAT):
            op_token = self.advance()
            right = self.parse_multiplicative()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_multiplicative(self) -> Expression:
        """Parse multiplication/division/modulo expression."""
        expr = self.parse_power()

        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op_token = self.advance()
            right = self.parse_power()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_power(self) -> Expression:
        """Parse power expression."""
        expr = self.parse_unary()

        while self.match(TokenType.POWER):
            op_token = self.advance()
            right = self.parse_unary()
            expr = BinaryOp(
                left=expr,
                operator=op_token.value,
                operator_type=op_token.type,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return expr

    def parse_unary(self) -> Expression:
        """Parse unary expression."""
        if self.match(TokenType.MINUS, TokenType.NOT):
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operator_type=op_token.type,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        return self.parse_primary()

    def parse_primary(self) -> Expression:
        """Parse primary expression (literals, identifiers, function calls, parentheses)."""
        if not self.current_token:
            raise UnexpectedEOFError(context="expression")

        token = self.current_token

        # Literals
        if self.match(
            TokenType.INTEGER_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.STRING_LITERAL,
            TokenType.BOOLEAN_LITERAL,
        ):
            self.advance()
            return Literal(
                value=token.literal, token_type=token.type, line=token.line, column=token.column
            )

        # NULL literal
        if self.match(TokenType.NULL):
            self.advance()
            return Literal(
                value=None, token_type=TokenType.NULL, line=token.line, column=token.column
            )

        # Parameter placeholder (?) for parametric queries
        if self.match(TokenType.QUESTION_MARK):
            self.advance()
            return Literal(
                value="?", token_type=TokenType.QUESTION_MARK, line=token.line, column=token.column
            )

        # Identifier or function call
        if self.match(TokenType.IDENTIFIER):
            self.advance()

            # Function call
            if self.match(TokenType.LPAREN):
                self.advance()
                arguments = self.parse_argument_list()
                self.consume(TokenType.RPAREN)
                return FunctionCall(
                    function_name=token.value,
                    arguments=arguments,
                    line=token.line,
                    column=token.column,
                )

            # Array access
            if self.match(TokenType.LBRACKET):
                self.advance()
                index = self.parse_expression()
                self.consume(TokenType.RBRACKET)
                return ArrayAccess(
                    array_name=token.value, index=index, line=token.line, column=token.column
                )

            # Just an identifier
            return Identifier(name=token.value, line=token.line, column=token.column)

        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr

        raise UnexpectedTokenError(token, context="expression")

    def parse_argument_list(self) -> List[Expression]:
        """Parse function argument list."""
        arguments: List[Expression] = []

        if self.match(TokenType.RPAREN):
            return arguments

        arguments.append(self.parse_expression())

        while self.match(TokenType.COMMA):
            self.advance()
            arguments.append(self.parse_expression())

        return arguments

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def is_time_unit(self, token: Optional[Token]) -> bool:
        """Check if a token represents a time unit for DATETIME/INTERVAL qualifiers."""
        if not token or token.type != TokenType.IDENTIFIER:
            return False

        time_units = {"YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND", "FRACTION"}
        return token.value.upper() in time_units

    def is_data_type(self, token_type: TokenType) -> bool:
        """Check if a token type represents a data type."""
        data_types = {
            TokenType.INTEGER,
            TokenType.SMALLINT,
            TokenType.DECIMAL,
            TokenType.MONEY,
            TokenType.FLOAT,
            TokenType.SMALLFLOAT,
            TokenType.DATE,
            TokenType.DATETIME,
            TokenType.INTERVAL,
            TokenType.CHAR,
            TokenType.VARCHAR,
            TokenType.NCHAR,
            TokenType.NVARCHAR,
            TokenType.TEXT,
            TokenType.BYTE,
            TokenType.SERIAL,
            TokenType.SERIAL8,
            TokenType.BIGSERIAL,
            TokenType.BIGINT,
            TokenType.INT8,
            TokenType.BOOLEAN,
        }
        return token_type in data_types


# ============================================================================
# Convenience Function
# ============================================================================


def parse_source(source: str, filename: str = "<stdin>") -> Program:
    """
    Parse 4GL source code into an AST.

    Args:
        source: The 4GL source code
        filename: Name of the source file (for error messages)

    Returns:
        Program AST node

    Raises:
        ParserError: If parsing fails
    """

    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
