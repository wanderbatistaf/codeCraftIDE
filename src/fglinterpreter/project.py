"""
CodeCraft Project (.ccp) Project Format

This module handles the .ccp project file format for CodeCraft IDE.
A .ccp file contains:
- Project metadata
- All source files and forms
- IDE state (open tabs, active file, expanded folders)
- Build configuration (from 4make.def)
- Database configuration

.ccp files are compressed and base64-encoded for optimization and protection.
"""

import base64
import gzip
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProjectFile:
    """Represents a file in the project."""

    path: str
    content: str
    type: str = "4gl"  # 4gl, per, def, sql, etc.


@dataclass
class BuildConfig:
    """Build configuration from 4make.def."""

    target: str = ""
    sources: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    msg: List[str] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    name: str = ""
    host: str = "localhost"
    port: int = 9088
    type: str = "informix"  # informix, mysql, postgresql
    server: Optional[str] = None


@dataclass
class IDEState:
    """IDE state to restore when opening project."""

    open_tabs: List[str] = field(default_factory=list)
    active_tab: Optional[str] = None
    expanded_folders: List[str] = field(default_factory=list)


@dataclass
class CodeCraftProject:
    """
    CodeCraft Project (.ccp) Project.

    This represents a complete 4GL project with all its files,
    configuration, and IDE state.
    """

    name: str
    version: str = "1.0.0"
    format_version: str = "1.0"  # .ccp format version
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""

    files: List[ProjectFile] = field(default_factory=list)
    build_config: Optional[BuildConfig] = None
    database_config: Optional[DatabaseConfig] = None
    ide_state: IDEState = field(default_factory=IDEState)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, path: str, content: str, file_type: str = "4gl"):
        """Add a file to the project."""
        # Check if file already exists
        for f in self.files:
            if f.path == path:
                f.content = content
                f.type = file_type
                return

        # Add new file
        self.files.append(ProjectFile(path=path, content=content, type=file_type))

    def remove_file(self, path: str):
        """Remove a file from the project."""
        self.files = [f for f in self.files if f.path != path]

    def get_file(self, path: str) -> Optional[ProjectFile]:
        """Get a file from the project."""
        for f in self.files:
            if f.path == path:
                return f
        return None

    def get_files_by_type(self, file_type: str) -> List[ProjectFile]:
        """Get all files of a specific type."""
        return [f for f in self.files if f.type == file_type]

    def update_modified_time(self):
        """Update the modified timestamp."""
        self.modified = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "format_version": self.format_version,
            "created": self.created,
            "modified": self.modified,
            "description": self.description,
            "files": [{"path": f.path, "content": f.content, "type": f.type} for f in self.files],
            "build_config": asdict(self.build_config) if self.build_config else None,
            "database_config": asdict(self.database_config) if self.database_config else None,
            "ide_state": asdict(self.ide_state),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeCraftProject":
        """Create project from dictionary."""
        project = cls(
            name=data.get("name", "Untitled"),
            version=data.get("version", "1.0.0"),
            format_version=data.get("format_version", "1.0"),
            created=data.get("created", datetime.now().isoformat()),
            modified=data.get("modified", datetime.now().isoformat()),
            description=data.get("description", ""),
        )

        # Load files
        for file_data in data.get("files", []):
            project.add_file(
                path=file_data["path"],
                content=file_data["content"],
                file_type=file_data.get("type", "4gl"),
            )

        # Load build config
        if data.get("build_config"):
            project.build_config = BuildConfig(**data["build_config"])

        # Load database config
        if data.get("database_config"):
            project.database_config = DatabaseConfig(**data["database_config"])

        # Load IDE state
        if data.get("ide_state"):
            project.ide_state = IDEState(**data["ide_state"])

        # Load metadata
        project.metadata = data.get("metadata", {})

        return project

    def to_json(self, indent: int = 2) -> str:
        """Serialize project to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "CodeCraftProject":
        """Deserialize project from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_ccp_bytes(self) -> bytes:
        """
        Serialize project to compressed and encoded bytes.

        This compresses the JSON data with gzip and encodes it with base64
        for optimization and protection.

        Returns:
            Compressed and encoded bytes suitable for .ccp file
        """
        # Serialize to JSON (compact, no indentation)
        json_str = json.dumps(self.to_dict())
        json_bytes = json_str.encode("utf-8")

        # Compress with gzip
        compressed = gzip.compress(json_bytes, compresslevel=9)

        # Encode with base64
        encoded = base64.b64encode(compressed)

        return encoded

    @classmethod
    def from_ccp_bytes(cls, ccp_bytes: bytes) -> "CodeCraftProject":
        """
        Deserialize project from compressed and encoded bytes.

        Args:
            ccp_bytes: Compressed and base64-encoded project data

        Returns:
            CodeCraftProject instance
        """
        # Decode from base64
        compressed = base64.b64decode(ccp_bytes)

        # Decompress
        json_bytes = gzip.decompress(compressed)

        # Parse JSON
        json_str = json_bytes.decode("utf-8")
        return cls.from_json(json_str)

    def save(self, path: str):
        """
        Save project to .ccp file.

        The file is compressed and base64-encoded for optimization and protection.
        """
        self.update_modified_time()

        # Ensure .ccp extension
        path_obj = Path(path)
        if path_obj.suffix != ".ccp":
            path_obj = path_obj.with_suffix(".ccp")

        # Write compressed and encoded data
        ccp_data = self.to_ccp_bytes()
        with open(path_obj, "wb") as f:
            f.write(ccp_data)

    @classmethod
    def load(cls, path: str) -> "CodeCraftProject":
        """
        Load project from .ccp file.

        Automatically detects if the file is compressed/encoded or plain JSON
        for backward compatibility.
        """
        with open(path, "rb") as f:
            file_data = f.read()

        # Try to load as compressed/encoded first
        try:
            return cls.from_ccp_bytes(file_data)
        except Exception:
            # Fallback to plain JSON for backward compatibility
            try:
                json_str = file_data.decode("utf-8")
                return cls.from_json(json_str)
            except Exception as e:
                raise ValueError(f"Invalid .ccp file format: {e}")

    @classmethod
    def from_workspace(
        cls, workspace_path: Path, name: str, include_patterns: List[str] = None
    ) -> "CodeCraftProject":
        """
        Create a project from a workspace directory.

        Args:
            workspace_path: Path to workspace directory
            name: Project name
            include_patterns: File patterns to include (e.g., ["*.4gl", "*.per"])

        Returns:
            CodeCraftProject with files loaded from workspace
        """
        if include_patterns is None:
            include_patterns = ["*.4gl", "*.per", "4make.def", "*.sql"]

        project = cls(name=name)

        # Scan workspace for files
        for pattern in include_patterns:
            for file_path in workspace_path.glob(f"**/{pattern}"):
                if file_path.is_file():
                    try:
                        with open(file_path) as f:
                            content = f.read()

                        # Determine file type from extension
                        ext = file_path.suffix.lower()
                        file_type = {
                            ".4gl": "4gl",
                            ".per": "per",
                            ".def": "def",
                            ".sql": "sql",
                        }.get(ext, "text")

                        # Get relative path
                        rel_path = file_path.relative_to(workspace_path)

                        project.add_file(path=str(rel_path), content=content, file_type=file_type)
                    except Exception as e:
                        print(f"Warning: Failed to load {file_path}: {e}")

        # Try to load 4make.def
        make_def_path = workspace_path / "4make.def"
        if make_def_path.exists():
            try:
                from .make_def_parser import parse_4make_def

                with open(make_def_path) as f:
                    make_def = parse_4make_def(f.read())

                project.build_config = BuildConfig(
                    target=make_def.target,
                    sources=make_def.sources,
                    forms=make_def.forms,
                    msg=make_def.msg,
                )
            except Exception as e:
                print(f"Warning: Failed to parse 4make.def: {e}")

        return project


def create_project(name: str, description: str = "") -> CodeCraftProject:
    """
    Create a new empty CodeCraft project.

    Args:
        name: Project name
        description: Project description

    Returns:
        New CodeCraftProject instance
    """
    return CodeCraftProject(name=name, description=description)
