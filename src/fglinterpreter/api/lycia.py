"""API endpoints for Lycia form operations."""

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..lycia.fm2_parser import parse_fm2_file

router = APIRouter(prefix="/api/lycia", tags=["lycia"])


class ParseFM2Request(BaseModel):
    """Request to parse a .fm2 file."""

    content: str


class ParseFM2Response(BaseModel):
    """Response from parsing a .fm2 file."""

    status: str
    form: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/parse-fm2", response_model=ParseFM2Response)
async def parse_fm2(request: ParseFM2Request) -> ParseFM2Response:
    """
    Parse a .fm2 file content and return the form structure.

    Args:
        request: Request containing the .fm2 XML content

    Returns:
        Parsed form structure or error message
    """
    try:
        form_data = parse_fm2_file(request.content)
        return ParseFM2Response(status="success", form=form_data)
    except Exception as e:
        return ParseFM2Response(status="error", error=str(e))


class ConvertPerToFM2Request(BaseModel):
    """Request to convert .per to .fm2 format."""

    content: str
    form_name: str


@router.post("/convert-per-to-fm2")
async def convert_per_to_fm2(request: ConvertPerToFM2Request) -> Dict[str, Any]:
    """
    Convert a .per file to .fm2 format.

    This uses the existing .per parser and generates .fm2 XML.

    Args:
        request: Request containing .per content and form name

    Returns:
        Generated .fm2 XML content
    """
    try:
        from ..per_parser import parse_per_file

        # Parse the .per file
        per_data = parse_per_file(request.content)

        # Generate .fm2 XML
        fm2_content = generate_fm2_from_per(per_data, request.form_name)

        return {"status": "success", "fm2": fm2_content}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def generate_fm2_from_per(per_data: Dict[str, Any], form_name: str) -> str:
    """
    Generate .fm2 XML from parsed .per data.

    Args:
        per_data: Parsed .per form data
        form_name: Name for the form

    Returns:
        Generated .fm2 XML string
    """
    import xml.etree.ElementTree as ET

    # Create root form element
    form = ET.Element("form")
    form.set("xmlns", "http://namespaces.querix.com/2015/fglForms")

    # Add database
    if per_data.get("database"):
        form_db = ET.SubElement(form, "form.database")
        db = ET.SubElement(form_db, "Database")
        db.set("name", per_data["database"])

    # Add root container
    form_root = ET.SubElement(form, "form.rootContainer")

    # Calculate form dimensions from screen layout
    screen = per_data.get("screen", {})
    layout = screen.get("layout", [])

    max_width = 80
    max_height = len(layout) if layout else 24

    # Find actual max width from layout
    for line in layout:
        if isinstance(line, str) and len(line) > max_width:
            max_width = len(line)

    coord_panel = ET.SubElement(form_root, "CoordPanel")
    coord_panel.set("preferredSize", f"{max_width}qch,{max_height}qch")
    coord_panel.set("fieldTable", "")
    coord_panel.set("identifier", "coord1")

    # Track field positions from layout
    field_positions = {}
    label_count = 0

    if layout:
        for y, line in enumerate(layout):
            if not isinstance(line, str):
                continue

            x = 0
            i = 0
            while i < len(line):
                char = line[i]

                if char == "[":
                    # Found a field marker
                    field_start = i
                    field_end = line.find("]", i)
                    if field_end > field_start:
                        field_name = line[field_start + 1 : field_end].strip()
                        field_width = field_end - field_start - 1

                        field_positions[field_name] = {"x": x, "y": y, "width": field_width}

                        i = field_end + 1
                        x += field_width + 2
                        continue

                elif char not in " \t":
                    # Found label text
                    label_start = i
                    # Read until we hit a field marker or end of line
                    while i < len(line) and line[i] != "[" and line[i] != "\n":
                        i += 1

                    label_text = line[label_start:i].strip()
                    if label_text:
                        label_count += 1
                        label = ET.SubElement(coord_panel, "Label")
                        label.set("text", label_text)
                        label.set("location", f"{x}qch,{y}qch")
                        label.set("preferredSize", f"{len(label_text)}qch,1qch")
                        label.set("fieldTable", "")
                        label.set("identifier", f"label{label_count}")

                    x += len(label_text)
                    continue

                x += 1
                i += 1

    # Add fields from attributes
    attributes = per_data.get("attributes", {})
    for attr in attributes:
        field_name = attr.get("field_name", "")
        table_col = attr.get("table_column", "")
        properties = attr.get("properties", [])

        # Get position from layout
        pos = field_positions.get(field_name, {"x": 0, "y": 0, "width": 10})

        # Determine field table and column
        field_table = "formonly"
        column_name = field_name

        if table_col and "." in table_col:
            parts = table_col.split(".")
            field_table = parts[0]
            column_name = parts[1] if len(parts) > 1 else field_name

        # Create TextField
        text_field = ET.SubElement(coord_panel, "TextField")
        text_field.set("location", f"{pos['x']}qch,{pos['y']}qch")
        text_field.set("preferredSize", f"{pos['width']}qch,1qch")
        text_field.set("fieldTable", field_table)
        text_field.set("identifier", column_name)

        # Add properties
        for prop in properties:
            prop_lower = prop.lower()
            if prop_lower == "noentry":
                text_field.set("noEntry", "true")
            elif prop_lower == "upshift":
                text_field.set("toCase", "Up")

        # Try to determine data type
        type_info = attr.get("type_info", {})
        if type_info:
            data_type = type_info.get("type", "Char")
            text_field.set("dataType", f"{data_type},,,,")

    # Add screen records
    tables = per_data.get("tables", [])
    if tables:
        form_records = ET.SubElement(form, "form.screenRecords")
        for table in tables:
            sr = ET.SubElement(form_records, "ScreenRecord")
            sr.set("identifier", table)
            sr.set("fields", "")

    # Generate XML string
    ET.indent(form, space="\t")
    xml_str = ET.tostring(form, encoding="unicode", xml_declaration=True)

    return xml_str
