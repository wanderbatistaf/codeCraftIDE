"""
Parser for 4make.def files.

The 4make.def file defines the build configuration for 4GL projects,
including source files, forms, and dependencies.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class MakeDef:
    """Represents a parsed 4make.def file."""

    target: str = ""
    sources: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    msg: List[str] = field(default_factory=list)
    other: dict = field(default_factory=dict)

    def get_source_files(self) -> List[str]:
        """
        Get list of .4gl source files (excluding libraries).

        Returns:
            List of .4gl file paths
        """
        return [s for s in self.sources if s.endswith(".4gl")]

    def get_library_files(self) -> List[str]:
        """
        Get list of library files (.a, .so, etc.).

        Returns:
            List of library file paths
        """
        return [s for s in self.sources if not s.endswith(".4gl")]

    def get_form_files(self) -> List[str]:
        """
        Get list of .per form files.

        Returns:
            List of .per file paths
        """
        return self.forms


def parse_4make_def(content: str) -> MakeDef:
    """
    Parse a 4make.def file.

    The format is:
    KEY=value1 value2 value3
    KEY=value

    Args:
        content: The 4make.def file content

    Returns:
        MakeDef object with parsed configuration
    """
    make_def = MakeDef()

    for line in content.split("\n"):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Parse KEY=VALUE
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Parse values (space-separated list)
            values = value.split() if value else []

            # Store in appropriate field
            if key.upper() == "TARGET":
                make_def.target = value
            elif key.upper() == "SOURCES":
                make_def.sources = values
            elif key.upper() == "FORMS":
                make_def.forms = values
            elif key.upper() == "MSG":
                make_def.msg = values
            else:
                # Store other keys
                make_def.other[key] = value

    return make_def


def find_function_definitions(source_files: List[str], workspace_path: Path) -> dict:
    """
    Find all function definitions across source files.

    Args:
        source_files: List of .4gl source file paths
        workspace_path: Path to the workspace

    Returns:
        Dictionary mapping function names to their source file
    """
    from .parser import parse_source
    from .parser.ast_nodes import FunctionDef

    functions = {}

    for source_file in source_files:
        file_path = workspace_path / source_file
        if not file_path.exists():
            continue

        try:
            with open(file_path) as f:
                code = f.read()

            # Parse the file
            ast = parse_source(code, filename=str(file_path))

            # Find all function definitions
            for node in ast.functions:
                if isinstance(node, FunctionDef):
                    functions[node.name] = source_file

        except Exception as e:
            # Skip files that fail to parse
            print(f"Warning: Failed to parse {source_file}: {e}")

    return functions
