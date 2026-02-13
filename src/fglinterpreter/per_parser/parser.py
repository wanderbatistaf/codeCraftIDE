"""
Parser for Querix .per form files.

Converts a sequence of tokens into an Abstract Syntax Tree (AST).
"""

import re
from typing import List

from .ast_nodes import (
    AttributesSection,
    DatabaseDirective,
    FieldAttribute,
    FormDefinition,
    InstructionsSection,
    ScreenField,
    ScreenLine,
    ScreenSection,
    TablesSection,
)
from .tokens import Token, TokenType


class PerParser:
    """
    Parser for .per form files.
    Converts tokens into an AST.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None

    def error(self, message: str):
        if self.current_token:
            raise Exception(
                f"Parser error at line {self.current_token.line}, "
                f"column {self.current_token.column}: {message}"
            )
        else:
            raise Exception(f"Parser error: {message}")

    def advance(self):
        """Move to the next token."""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def skip_newlines(self):
        """Skip any newline tokens."""
        while self.current_token and self.current_token.type == TokenType.NEWLINE:
            self.advance()

    def expect(self, token_type: TokenType) -> Token:
        """
        Expect a specific token type and consume it.
        Raises an error if the current token doesn't match.
        """
        if not self.current_token or self.current_token.type != token_type:
            expected = token_type.name
            actual = self.current_token.type.name if self.current_token else "EOF"
            self.error(f"Expected {expected}, got {actual}")

        token = self.current_token
        self.advance()
        return token

    def parse(self) -> FormDefinition:
        """Parse the entire .per file and return a FormDefinition AST."""
        form = FormDefinition()

        self.skip_newlines()

        while self.current_token and self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.DATABASE:
                form.database = self.parse_database()
            elif self.current_token.type == TokenType.SCREEN:
                form.screen = self.parse_screen()
            elif self.current_token.type == TokenType.TABLES:
                form.tables = self.parse_tables()
            elif self.current_token.type == TokenType.ATTRIBUTES:
                form.attributes = self.parse_attributes()
            elif self.current_token.type == TokenType.INSTRUCTIONS:
                form.instructions = self.parse_instructions()
            elif self.current_token.type == TokenType.NEWLINE:
                self.advance()
            else:
                self.error(
                    f"Unexpected token: {self.current_token.type.name} "
                    f"({self.current_token.value})"
                )

        return form

    def parse_database(self) -> DatabaseDirective:
        """
        Parse DATABASE directive.
        Example: DATABASE soporcel without null input
        """
        line = self.current_token.line
        self.expect(TokenType.DATABASE)

        # Read database name
        db_name_token = self.expect(TokenType.IDENTIFIER)
        db_name = db_name_token.value

        # Read optional clauses (without null input, etc.)
        options = []
        while (
            self.current_token
            and self.current_token.type != TokenType.NEWLINE
            and self.current_token.type != TokenType.SCREEN
            and self.current_token.type != TokenType.EOF
        ):
            if self.current_token.type == TokenType.IDENTIFIER:
                options.append(self.current_token.value)
                self.advance()
            elif self.current_token.type in (
                TokenType.WITHOUT,
                TokenType.NULL,
                TokenType.INPUT,
            ):
                options.append(self.current_token.value)
                self.advance()
            else:
                break

        self.skip_newlines()

        return DatabaseDirective(database_name=db_name, options=options, line=line)

    def parse_screen(self) -> ScreenSection:
        """
        Parse SCREEN section.
        Example:
        SCREEN
        {
            Label: [field_name]
        }
        END
        """
        line = self.current_token.line
        self.expect(TokenType.SCREEN)
        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        lines = []
        row = 0

        # Read lines until we hit }
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.NEWLINE:
                self.advance()
                continue

            # Read entire line as raw text
            line_start = self.current_token.line
            line_content = self._read_screen_line()

            # Parse fields from the line
            fields = self._extract_fields_from_line(line_content, row)

            screen_line = ScreenLine(row=row, content=line_content, fields=fields, line=line_start)
            lines.append(screen_line)
            row += 1

        self.expect(TokenType.RBRACE)
        self.skip_newlines()
        self.expect(TokenType.END)
        self.skip_newlines()

        return ScreenSection(lines=lines, height=row, line=line)

    def parse_tables(self) -> TablesSection:
        """
        Parse TABLES section.
        Example:
        TABLES
            equipment, pr_inventory_stat
        or
        TABLES
            equipment
        """
        line = self.current_token.line
        self.expect(TokenType.TABLES)
        self.skip_newlines()

        tables = []

        # Read table names until we hit another section keyword or END
        while self.current_token and self.current_token.type not in (
            TokenType.ATTRIBUTES,
            TokenType.INSTRUCTIONS,
            TokenType.END,
            TokenType.EOF,
        ):
            if self.current_token.type == TokenType.NEWLINE:
                self.advance()
                continue

            if self.current_token.type == TokenType.IDENTIFIER:
                tables.append(self.current_token.value)
                self.advance()

                # Skip comma if present
                if self.current_token and self.current_token.type == TokenType.COMMA:
                    self.advance()
            else:
                break

        self.skip_newlines()

        return TablesSection(tables=tables, line=line)

    def _read_screen_line(self) -> str:
        """
        Read a single line of screen layout, handling all tokens until newline.
        Reconstructs the line from tokens while preserving spacing.
        """
        tokens_in_line = []
        current_line = self.current_token.line if self.current_token else 0

        while (
            self.current_token
            and self.current_token.type != TokenType.NEWLINE
            and self.current_token.type != TokenType.RBRACE
            and self.current_token.line == current_line
        ):
            tokens_in_line.append(self.current_token)
            self.advance()

        # Reconstruct line from tokens
        if not tokens_in_line:
            return ""

        # Build line by positioning tokens according to their column
        line_chars = []
        last_column = 0

        for token in tokens_in_line:
            # Add spacing before token
            spaces_needed = token.column - last_column - 1
            if spaces_needed > 0:
                line_chars.append(" " * spaces_needed)

            # Add token value
            if token.type == TokenType.LBRACKET:
                line_chars.append("[")
                last_column = token.column
            elif token.type == TokenType.RBRACKET:
                line_chars.append("]")
                last_column = token.column
            elif token.type == TokenType.COLON:
                line_chars.append(":")
                last_column = token.column
            elif token.type == TokenType.LAYOUT_TEXT:
                line_chars.append(token.value)
                last_column = token.column + len(token.value) - 1
            else:
                line_chars.append(token.value)
                last_column = token.column + len(token.value) - 1

        return "".join(line_chars)

    def _extract_fields_from_line(self, line_content: str, row: int) -> List[ScreenField]:
        """
        Extract field references from a screen line.
        Fields are enclosed in brackets: [field_name]
        """
        fields = []
        # Use regex to find all [field_name] patterns
        pattern = r"\[([a-zA-Z_][a-zA-Z0-9_]*(?:\s+)?)\]"

        for match in re.finditer(pattern, line_content):
            field_name = match.group(1).strip()
            column = match.start()
            width = match.end() - match.start() - 2  # Exclude brackets

            field = ScreenField(name=field_name, position=(row, column), width=width)
            fields.append(field)

        return fields

    def parse_attributes(self) -> AttributesSection:
        """
        Parse ATTRIBUTES section.
        Example:
        ATTRIBUTES
          f_armazem = formonly.armazem, upshift;
          f_msg = formonly.msg type CHAR, widget="label";
        END
        """
        line = self.current_token.line
        self.expect(TokenType.ATTRIBUTES)
        self.skip_newlines()

        fields = []

        while self.current_token and self.current_token.type != TokenType.END:
            if self.current_token.type == TokenType.NEWLINE:
                self.advance()
                continue

            if self.current_token.type == TokenType.IDENTIFIER:
                field_attr = self.parse_field_attribute()
                fields.append(field_attr)
            else:
                break

        self.expect(TokenType.END)
        self.skip_newlines()

        return AttributesSection(fields=fields, line=line)

    def parse_field_attribute(self) -> FieldAttribute:
        """
        Parse a single field attribute definition.
        Example: f_armazem = formonly.armazem, upshift;
        """
        line = self.current_token.line

        # Screen field name (left side of =)
        screen_field = self.current_token.value
        self.advance()

        self.expect(TokenType.EQUALS)

        # Data source (right side of =)
        # Can be: formonly.varname or tablename.columnname
        table_name = None
        column_name = None

        if self.current_token.type == TokenType.FORMONLY:
            table_name = "formonly"
            self.advance()
        elif self.current_token.type == TokenType.IDENTIFIER:
            table_name = self.current_token.value
            self.advance()
        else:
            self.error(f"Expected table or formonly, got {self.current_token.type.name}")

        self.expect(TokenType.DOT)

        column_name = self.expect(TokenType.IDENTIFIER).value

        data_source = f"{table_name}.{column_name}"

        # Parse optional properties (upshift, type CHAR, widget="label", etc.)
        properties = {}

        while (
            self.current_token
            and self.current_token.type != TokenType.SEMICOLON
            and self.current_token.type != TokenType.NEWLINE
        ):
            if self.current_token.type == TokenType.COMMA:
                self.advance()
                continue

            # Simple flag properties (upshift, downshift, noentry, wordwrap, required)
            if self.current_token.type in (
                TokenType.UPSHIFT,
                TokenType.DOWNSHIFT,
                TokenType.NOENTRY,
                TokenType.WORDWRAP,
                TokenType.REQUIRED,
            ):
                prop_name = self.current_token.value.lower()
                properties[prop_name] = True
                self.advance()

            # type TYPENAME
            elif self.current_token.type == TokenType.TYPE:
                self.advance()
                if self.current_token.type in (
                    TokenType.CHAR,
                    TokenType.INTEGER,
                    TokenType.SMALLINT,
                    TokenType.DECIMAL,
                    TokenType.DATE,
                    TokenType.DATETIME,
                    TokenType.MONEY,
                    TokenType.IDENTIFIER,
                ):
                    properties["type"] = self.current_token.value.upper()
                    self.advance()
                else:
                    self.error("Expected data type after TYPE")

            # widget="value"
            elif self.current_token.type == TokenType.WIDGET:
                self.advance()
                self.expect(TokenType.EQUALS)
                widget_value = self.expect(TokenType.STRING).value
                properties["widget"] = widget_value

            # Other identifier-based properties
            elif self.current_token.type == TokenType.IDENTIFIER:
                prop_name = self.current_token.value.lower()
                self.advance()

                # Check if followed by = value
                if self.current_token and self.current_token.type == TokenType.EQUALS:
                    self.advance()
                    if self.current_token.type == TokenType.STRING:
                        properties[prop_name] = self.current_token.value
                        self.advance()
                    elif self.current_token.type == TokenType.NUMBER:
                        properties[prop_name] = self.current_token.value
                        self.advance()
                    elif self.current_token.type == TokenType.IDENTIFIER:
                        properties[prop_name] = self.current_token.value
                        self.advance()
                else:
                    # Just a flag
                    properties[prop_name] = True

            else:
                break

        # Expect semicolon at end
        if self.current_token and self.current_token.type == TokenType.SEMICOLON:
            self.advance()

        return FieldAttribute(
            screen_field=screen_field,
            data_source=data_source,
            table_name=table_name,
            column_name=column_name,
            properties=properties,
            line=line,
        )

    def parse_instructions(self) -> InstructionsSection:
        """
        Parse INSTRUCTIONS section.
        Example:
        INSTRUCTIONS
          DELIMITERS "  "
          SCREEN RECORD scr_name(field1, field2)
        END
        """
        line = self.current_token.line
        self.expect(TokenType.INSTRUCTIONS)
        self.skip_newlines()

        instructions = {}
        screen_records = []

        while self.current_token and self.current_token.type != TokenType.END:
            if self.current_token.type == TokenType.NEWLINE:
                self.advance()
                continue

            # Skip semicolons
            if self.current_token.type == TokenType.SEMICOLON:
                self.advance()
                continue

            if self.current_token.type == TokenType.DELIMITERS:
                self.advance()
                delimiter_value = self.expect(TokenType.STRING).value
                instructions["delimiters"] = delimiter_value
                # Skip trailing semicolon if present
                if self.current_token and self.current_token.type == TokenType.SEMICOLON:
                    self.advance()

            # Handle SCREEN RECORD instruction
            elif self.current_token.type == TokenType.SCREEN:
                self.advance()  # skip SCREEN
                # Expect RECORD (as identifier)
                if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
                    if self.current_token.value.lower() == "record":
                        self.advance()  # skip RECORD
                        # Get record name
                        if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
                            record_name = self.current_token.value
                            self.advance()
                            # Parse field list in parentheses
                            fields = []
                            if self.current_token and self.current_token.type == TokenType.LPAREN:
                                self.advance()  # skip (
                                while (
                                    self.current_token
                                    and self.current_token.type != TokenType.RPAREN
                                ):
                                    if self.current_token.type == TokenType.IDENTIFIER:
                                        fields.append(self.current_token.value)
                                        self.advance()
                                    elif self.current_token.type == TokenType.COMMA:
                                        self.advance()
                                    elif self.current_token.type == TokenType.NEWLINE:
                                        self.advance()
                                    else:
                                        self.advance()
                                if (
                                    self.current_token
                                    and self.current_token.type == TokenType.RPAREN
                                ):
                                    self.advance()  # skip )
                            screen_records.append({"name": record_name, "fields": fields})
                # Skip trailing semicolon if present
                if self.current_token and self.current_token.type == TokenType.SEMICOLON:
                    self.advance()

            elif self.current_token.type == TokenType.IDENTIFIER:
                # Generic instruction handling
                instr_name = self.current_token.value.lower()
                self.advance()

                # Try to read value if present
                if self.current_token and self.current_token.type in (
                    TokenType.STRING,
                    TokenType.NUMBER,
                    TokenType.IDENTIFIER,
                ):
                    instructions[instr_name] = self.current_token.value
                    self.advance()
                else:
                    instructions[instr_name] = True
                # Skip trailing semicolon if present
                if self.current_token and self.current_token.type == TokenType.SEMICOLON:
                    self.advance()
            else:
                break

        if screen_records:
            instructions["screen_records"] = screen_records

        self.expect(TokenType.END)
        self.skip_newlines()

        return InstructionsSection(instructions=instructions, line=line)


def parse_per_file(text: str) -> FormDefinition:
    """
    Parse a .per form file and return the AST.

    Args:
        text: The .per file content as a string

    Returns:
        FormDefinition AST representing the parsed form
    """
    from .lexer import tokenize_per_file

    tokens = tokenize_per_file(text)
    parser = PerParser(tokens)
    return parser.parse()
