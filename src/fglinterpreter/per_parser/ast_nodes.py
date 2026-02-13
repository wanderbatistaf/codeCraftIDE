"""
AST node definitions for Querix .per form files.

This module defines the Abstract Syntax Tree (AST) nodes used to represent
the structure of a .per form file, including:
- Screen layout
- Field attributes
- Instructions
- Database configuration
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FormASTNode:
    """Base class for all .per form AST nodes."""

    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class ScreenField(FormASTNode):
    """Represents a field in the screen layout [field_name]."""

    name: str = ""
    position: Tuple[int, int] = (0, 0)  # (row, column)
    width: int = 0


@dataclass
class ScreenLine(FormASTNode):
    """Represents a single line in the screen layout."""

    row: int = 0
    content: str = ""  # Raw line content including fields
    fields: List[ScreenField] = field(default_factory=list)


@dataclass
class ScreenSection(FormASTNode):
    """Represents the SCREEN { ... } END section."""

    lines: List[ScreenLine] = field(default_factory=list)
    width: int = 80  # Default screen width
    height: int = 0  # Calculated from lines


@dataclass
class FieldAttribute(FormASTNode):
    """
    Represents a field attribute definition.
    Example: f_armazem = formonly.armazem, upshift;
    """

    screen_field: str = ""  # e.g., "f_armazem"
    data_source: str = ""  # e.g., "formonly.armazem"
    table_name: Optional[str] = None  # "formonly" or actual table name
    column_name: Optional[str] = None  # "armazem"
    properties: Dict[str, Any] = field(default_factory=dict)
    # Properties can include: upshift, noentry, type, widget, wordwrap, etc.


@dataclass
class AttributesSection(FormASTNode):
    """Represents the ATTRIBUTES ... END section."""

    fields: List[FieldAttribute] = field(default_factory=list)


@dataclass
class TablesSection(FormASTNode):
    """Represents the TABLES section listing table names."""

    tables: List[str] = field(default_factory=list)


@dataclass
class InstructionsSection(FormASTNode):
    """Represents the INSTRUCTIONS ... END section."""

    instructions: Dict[str, Any] = field(default_factory=dict)
    # Examples: DELIMITERS, SCREEN RECORD, etc.


@dataclass
class DatabaseDirective(FormASTNode):
    """
    Represents the DATABASE directive.
    Example: DATABASE soporcel without null input
    """

    database_name: str = ""
    options: List[str] = field(default_factory=list)
    # Options can include: "without null input", etc.


@dataclass
class FormDefinition(FormASTNode):
    """
    Root node representing the entire .per form file.
    """

    database: Optional[DatabaseDirective] = None
    screen: Optional[ScreenSection] = None
    tables: Optional[TablesSection] = None
    attributes: Optional[AttributesSection] = None
    instructions: Optional[InstructionsSection] = None

    def get_field_mapping(self) -> Dict[str, FieldAttribute]:
        """
        Returns a mapping of screen field names to their attributes.
        Example: {"f_armazem": FieldAttribute(...)}
        """
        if not self.attributes:
            return {}
        return {attr.screen_field: attr for attr in self.attributes.fields}

    def get_formonly_variables(self) -> Dict[str, str]:
        """
        Returns a mapping of formonly variable names to screen field names.
        Example: {"armazem": "f_armazem"}
        """
        result = {}
        if self.attributes:
            for attr in self.attributes.fields:
                if attr.table_name == "formonly" and attr.column_name:
                    result[attr.column_name] = attr.screen_field
        return result

    def get_screen_fields(self) -> List[ScreenField]:
        """Returns all fields found in the screen layout."""
        if not self.screen:
            return []
        fields = []
        for line in self.screen.lines:
            fields.extend(line.fields)
        return fields

    def validate(self) -> List[str]:
        """
        Validates the form definition and returns a list of error messages.
        Checks:
        - All screen fields have corresponding attributes
        - All attribute fields exist in screen
        """
        errors = []

        if not self.screen or not self.attributes:
            return errors

        # Get all screen field names
        screen_field_names = {f.name for f in self.get_screen_fields()}

        # Get all attribute field names
        attribute_field_names = {attr.screen_field for attr in self.attributes.fields}

        # Check for screen fields without attributes
        for field_name in screen_field_names:
            if field_name not in attribute_field_names:
                errors.append(
                    f"Screen field '{field_name}' has no corresponding attribute definition"
                )

        # Check for attributes without screen fields
        for field_name in attribute_field_names:
            if field_name not in screen_field_names:
                errors.append(f"Attribute field '{field_name}' is not used in screen layout")

        return errors
