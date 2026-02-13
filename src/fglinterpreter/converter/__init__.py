"""
Code converter for translating 4GL to Python.

This module provides:
- Conversion engine (PythonCodeGenerator)
- 4GL to Python AST mapping
- Code generation and formatting
- High-level conversion API
- Batch conversion tools (Epic 4, Story 4.2)
- Dependency resolution (Epic 4, Story 4.3)

Story 1.5: Conversion Layer (4GL → Python AST) - COMPLETE
Story 4.2: File-Based Batch Conversion Tool - COMPLETE
Story 4.3: Dependency Resolver - IN PROGRESS
"""

from .api import convert_source
from .batch import (
    BatchConversionReport,
    BatchConverter,
    ConversionResult,
    convert_directory,
)
from .converter import PythonCodeGenerator, convert_to_python
from .dependencies import (
    DependencyAnalyzer,
    DependencyGraph,
    DependencyResolver,
    FileInfo,
    resolve_dependencies,
)
from .formatter import format_python_code, is_black_available
from .reverse_converter import PythonTo4GLConverter, convert_python_to_4gl

__all__ = [
    # High-level API
    "convert_source",
    # Core converter
    "PythonCodeGenerator",
    "convert_to_python",
    # Reverse converter
    "PythonTo4GLConverter",
    "convert_python_to_4gl",
    # Formatting
    "format_python_code",
    "is_black_available",
    # Batch conversion
    "BatchConverter",
    "ConversionResult",
    "BatchConversionReport",
    "convert_directory",
    # Dependency resolution
    "DependencyResolver",
    "DependencyAnalyzer",
    "DependencyGraph",
    "FileInfo",
    "resolve_dependencies",
]
