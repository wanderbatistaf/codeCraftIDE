"""
Parser for Lycia .fm2 form files (XML format).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LyciaComponent:
    """Represents a Lycia form component."""

    component_type: str  # Label, TextField, Separator, CoordPanel, etc.
    identifier: str
    location: Optional[str] = None  # "Xqch,Yqch"
    preferred_size: Optional[str] = None  # "widthqch,heightqch"
    text: Optional[str] = None  # For Label
    field_table: Optional[str] = None
    data_type: Optional[str] = None  # For TextField
    no_entry: bool = False
    to_case: Optional[str] = None  # "Up" for uppercase
    is_dynamic: bool = False  # For dynamic labels
    separator_type: Optional[str] = None  # "Vertical" for vertical separators
    z_order: Optional[str] = None
    children: List["LyciaComponent"] = field(default_factory=list)

    # Parsed location values
    x: int = 0
    y: int = 0
    width: int = 1
    height: int = 1

    def __post_init__(self):
        """Parse location and size into numeric values."""
        if self.location:
            self._parse_location()
        if self.preferred_size:
            self._parse_size()

    def _parse_location(self):
        """Parse location string like '10qch,5qch' into x, y."""
        try:
            parts = self.location.replace("qch", "").split(",")
            self.x = int(float(parts[0]))
            self.y = int(float(parts[1]))
        except (ValueError, IndexError):
            pass

    def _parse_size(self):
        """Parse size string like '20qch,1qch' into width, height."""
        try:
            parts = self.preferred_size.replace("qch", "").split(",")
            self.width = int(float(parts[0]))
            self.height = int(float(parts[1]))
        except (ValueError, IndexError):
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": self.component_type,
            "identifier": self.identifier,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

        if self.text:
            result["text"] = self.text
        if self.field_table:
            result["fieldTable"] = self.field_table
        if self.data_type:
            result["dataType"] = self.data_type
        if self.no_entry:
            result["noEntry"] = True
        if self.to_case:
            result["toCase"] = self.to_case
        if self.is_dynamic:
            result["isDynamic"] = True
        if self.separator_type:
            result["separatorType"] = self.separator_type
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]

        return result


@dataclass
class LyciaScreenRecord:
    """Represents a screen record definition."""

    identifier: str
    fields: str


@dataclass
class LyciaForm:
    """Represents a complete Lycia form."""

    database: Optional[str] = None
    root_container: Optional[LyciaComponent] = None
    screen_records: List[LyciaScreenRecord] = field(default_factory=list)
    interact_settings: Optional[str] = None

    # Form dimensions
    width: int = 80
    height: int = 24

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "database": self.database,
            "width": self.width,
            "height": self.height,
            "rootContainer": self.root_container.to_dict() if self.root_container else None,
            "screenRecords": [
                {"identifier": sr.identifier, "fields": sr.fields} for sr in self.screen_records
            ],
        }


class FM2Parser:
    """Parser for .fm2 XML form files."""

    NAMESPACE = "http://namespaces.querix.com/2015/fglForms"

    def __init__(self, content: str):
        """
        Initialize parser with XML content.

        Args:
            content: XML content of the .fm2 file
        """
        self.content = content
        self.form = LyciaForm()

    def parse(self) -> LyciaForm:
        """
        Parse the .fm2 content and return a LyciaForm object.

        Returns:
            Parsed LyciaForm object
        """
        # Parse XML
        root = ET.fromstring(self.content)

        # Get namespace
        ns = {"fm": self.NAMESPACE}

        # Check for interactSettings attribute
        interact_settings = root.get("interactSettings")
        if interact_settings:
            self.form.interact_settings = interact_settings

        # Parse database
        db_elem = root.find("fm:form.database/fm:Database", ns)
        if db_elem is None:
            # Try without namespace
            db_elem = root.find(".//Database")
        if db_elem is not None:
            self.form.database = db_elem.get("name")

        # Parse root container
        root_container_elem = root.find("fm:form.rootContainer", ns)
        if root_container_elem is None:
            root_container_elem = root.find(".//form.rootContainer")

        if root_container_elem is not None and len(root_container_elem) > 0:
            self.form.root_container = self._parse_component(root_container_elem[0])

            # Extract form dimensions from root container
            if self.form.root_container:
                self.form.width = self.form.root_container.width
                self.form.height = self.form.root_container.height

        # Parse screen records
        screen_records_elem = root.find("fm:form.screenRecords", ns)
        if screen_records_elem is None:
            screen_records_elem = root.find(".//form.screenRecords")

        if screen_records_elem is not None:
            for sr_elem in screen_records_elem:
                tag = sr_elem.tag.replace(f"{{{self.NAMESPACE}}}", "")
                if tag == "ScreenRecord":
                    sr = LyciaScreenRecord(
                        identifier=sr_elem.get("identifier", ""), fields=sr_elem.get("fields", "")
                    )
                    self.form.screen_records.append(sr)

        return self.form

    def _parse_component(self, elem: ET.Element) -> LyciaComponent:
        """
        Parse a component element recursively.

        Args:
            elem: XML element to parse

        Returns:
            LyciaComponent object
        """
        # Get tag name without namespace
        tag = elem.tag.replace(f"{{{self.NAMESPACE}}}", "")

        component = LyciaComponent(
            component_type=tag,
            identifier=elem.get("identifier", ""),
            location=elem.get("location"),
            preferred_size=elem.get("preferredSize"),
            text=elem.get("text"),
            field_table=elem.get("fieldTable"),
            data_type=elem.get("dataType"),
            no_entry=elem.get("noEntry", "").lower() == "true",
            to_case=elem.get("toCase"),
            is_dynamic=elem.get("isDynamic", "").lower() == "true",
            separator_type=elem.get("separatorType"),
            z_order=elem.get("zOrder"),
        )

        # Parse children
        for child_elem in elem:
            child_tag = child_elem.tag.replace(f"{{{self.NAMESPACE}}}", "")
            # Skip non-component elements
            if child_tag in [
                "Label",
                "TextField",
                "Separator",
                "CoordPanel",
                "GridPanel",
                "Button",
                "CheckBox",
                "ComboBox",
                "Table",
                "Tree",
                "Canvas",
                "Image",
                "WebView",
                "TabFolder",
                "TabPage",
                "GroupBox",
                "ScrollPanel",
            ]:
                child = self._parse_component(child_elem)
                component.children.append(child)

        return component


def parse_fm2_file(content: str) -> Dict[str, Any]:
    """
    Convenience function to parse .fm2 content and return a dictionary.

    Args:
        content: XML content of the .fm2 file

    Returns:
        Dictionary representation of the form
    """
    parser = FM2Parser(content)
    form = parser.parse()
    return form.to_dict()
