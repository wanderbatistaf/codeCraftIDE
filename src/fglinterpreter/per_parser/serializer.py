"""
Utilities for serializing .per form AST to JSON-compatible dictionaries.
"""

from typing import Any, Dict

from .ast_nodes import (
    AttributesSection,
    DatabaseDirective,
    FieldAttribute,
    FormDefinition,
    InstructionsSection,
    ScreenField,
    ScreenLine,
    ScreenSection,
)


def serialize_screen_field(field: ScreenField) -> Dict[str, Any]:
    """Serialize a ScreenField to a dictionary."""
    return {
        "name": field.name,
        "position": {"row": field.position[0], "column": field.position[1]},
        "width": field.width,
    }


def serialize_screen_line(line: ScreenLine) -> Dict[str, Any]:
    """Serialize a ScreenLine to a dictionary."""
    return {
        "row": line.row,
        "content": line.content,
        "fields": [serialize_screen_field(f) for f in line.fields],
    }


def serialize_screen_section(screen: ScreenSection) -> Dict[str, Any]:
    """Serialize a ScreenSection to a dictionary."""
    return {
        "width": screen.width,
        "height": screen.height,
        "lines": [serialize_screen_line(line) for line in screen.lines],
    }


def serialize_field_attribute(attr: FieldAttribute) -> Dict[str, Any]:
    """Serialize a FieldAttribute to a dictionary."""
    return {
        "screen_field": attr.screen_field,
        "data_source": attr.data_source,
        "table_name": attr.table_name,
        "column_name": attr.column_name,
        "properties": attr.properties,
    }


def serialize_attributes_section(attrs: AttributesSection) -> Dict[str, Any]:
    """Serialize an AttributesSection to a dictionary."""
    return {
        "fields": [serialize_field_attribute(f) for f in attrs.fields],
    }


def serialize_instructions_section(instrs: InstructionsSection) -> Dict[str, Any]:
    """Serialize an InstructionsSection to a dictionary."""
    return {
        "instructions": instrs.instructions,
    }


def serialize_database_directive(db: DatabaseDirective) -> Dict[str, Any]:
    """Serialize a DatabaseDirective to a dictionary."""
    return {
        "database_name": db.database_name,
        "options": db.options,
    }


def serialize_form_definition(form: FormDefinition) -> Dict[str, Any]:
    """
    Serialize a FormDefinition to a JSON-compatible dictionary.

    Args:
        form: The FormDefinition AST to serialize

    Returns:
        Dictionary representation of the form
    """
    result = {}

    if form.database:
        result["database"] = serialize_database_directive(form.database)

    if form.screen:
        result["screen"] = serialize_screen_section(form.screen)

    if form.attributes:
        result["attributes"] = serialize_attributes_section(form.attributes)

    if form.instructions:
        result["instructions"] = serialize_instructions_section(form.instructions)

    return result
