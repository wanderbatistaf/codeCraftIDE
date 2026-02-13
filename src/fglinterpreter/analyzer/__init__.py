"""Static analysis module for FGL code."""

from .static_analyzer import (
    Diagnostic,
    DiagnosticSeverity,
    QuickFix,
    StaticAnalyzer,
    UndefinedVariable,
)

__all__ = [
    "StaticAnalyzer",
    "UndefinedVariable",
    "Diagnostic",
    "DiagnosticSeverity",
    "QuickFix",
]
