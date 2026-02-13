"""
Batch conversion tools for converting directories of 4GL files to Python.

This module provides functionality for:
- Batch converting .4gl files to .py files
- Preserving directory structure
- Generating conversion reports (Text, JSON, Markdown, HTML)
- Handling errors gracefully
- Tracking unmapped constructs and warnings

Enhanced in Story 4.5 with comprehensive reporting capabilities.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..lexer import LexerError
from ..parser import ParserError
from . import convert_source
from .report_generator import (
    calculate_migration_readiness_score,
    generate_html_report,
    generate_markdown_report,
    generate_recommendations,
    scan_for_unmapped_constructs,
)


@dataclass
class ConversionResult:
    """Result of converting a single file."""

    source_file: Path
    target_file: Path
    success: bool
    error: Optional[str] = None
    error_type: Optional[str] = None
    lines_converted: int = 0
    execution_time: float = 0.0
    unmapped_constructs: List[str] = field(
        default_factory=list
    )  # Story 4.5: Track unmapped features
    warning_count: int = 0  # Story 4.5: Count of warnings


@dataclass
class BatchConversionReport:
    """Report for batch conversion operation."""

    source_dir: Path
    target_dir: Path
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: List[ConversionResult] = field(default_factory=list)
    has_circular_dependencies: bool = False
    circular_dependency_path: Optional[List[Path]] = None

    @property
    def duration(self) -> float:
        """Get the duration of the batch conversion in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100

    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization."""
        result = {
            "source_dir": self.source_dir.as_posix(),
            "target_dir": self.target_dir.as_posix(),
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate, 2),
            "duration_seconds": round(self.duration, 2),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "has_circular_dependencies": self.has_circular_dependencies,
            "results": [
                {
                    "source_file": str(r.source_file),
                    "target_file": str(r.target_file),
                    "success": r.success,
                    "error": r.error,
                    "error_type": r.error_type,
                    "lines_converted": r.lines_converted,
                    "execution_time": round(r.execution_time, 4),
                }
                for r in self.results
            ],
        }
        if self.circular_dependency_path:
            result["circular_dependency_path"] = [str(p) for p in self.circular_dependency_path]
        return result

    def to_text(self) -> str:
        """Generate a human-readable text report."""
        lines = []
        lines.append("=" * 70)
        lines.append("4GL to Python Batch Conversion Report")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Source Directory: {self.source_dir.as_posix()}")
        lines.append(f"Target Directory: {self.target_dir.as_posix()}")
        lines.append(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.end_time:
            lines.append(f"End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {self.duration:.2f} seconds")
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  Total Files: {self.total_files}")
        lines.append(f"  Successful: {self.successful} ({self.success_rate:.1f}%)")
        lines.append(f"  Failed: {self.failed}")
        lines.append(f"  Skipped: {self.skipped}")
        lines.append("")

        if self.has_circular_dependencies and self.circular_dependency_path:
            lines.append("⚠️  Warning: Circular Dependencies Detected")
            cycle_str = " -> ".join(str(p.name) for p in self.circular_dependency_path)
            lines.append(f"  Cycle: {cycle_str}")
            lines.append("")

        if self.results:
            lines.append("Results:")
            lines.append("-" * 70)
            for result in self.results:
                status = "✓ SUCCESS" if result.success else "✗ FAILED"
                lines.append(f"{status}: {result.source_file.name}")
                lines.append(f"  Source: {result.source_file}")
                lines.append(f"  Target: {result.target_file}")
                if result.success:
                    lines.append(f"  Lines: {result.lines_converted}")
                    lines.append(f"  Time: {result.execution_time:.3f}s")
                else:
                    lines.append(f"  Error Type: {result.error_type}")
                    lines.append(f"  Error: {result.error}")
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Generate Markdown report (Story 4.5).

        Returns:
            Formatted Markdown report string
        """
        report_data = self._get_enhanced_report_data()
        return generate_markdown_report(report_data)

    def to_html(self) -> str:
        """Generate interactive HTML report with charts (Story 4.5).

        Returns:
            Formatted HTML report string with embedded charts
        """
        report_data = self._get_enhanced_report_data()
        return generate_html_report(report_data)

    def _get_enhanced_report_data(self) -> Dict:
        """Get enhanced report data for advanced reporting (Story 4.5).

        Returns:
            Dictionary with all report data including analysis metrics
        """
        # Start with base dictionary
        base_data = self.to_dict()

        # Calculate unmapped constructs summary
        unmapped_summary = {}
        for result in self.results:
            for construct in result.unmapped_constructs:
                unmapped_summary[construct] = unmapped_summary.get(construct, 0) + 1

        # Count total warnings
        total_warnings = sum(r.warning_count for r in self.results)

        # Prepare results with warning counts
        enhanced_results = []
        for result in self.results:
            r_dict = {
                "source_file": str(result.source_file),
                "target_file": str(result.target_file),
                "success": result.success,
                "error": result.error,
                "error_type": result.error_type,
                "lines_converted": result.lines_converted,
                "execution_time": round(result.execution_time, 4),
                "warning_count": result.warning_count,
                "unmapped_count": len(result.unmapped_constructs),
            }
            enhanced_results.append(r_dict)

        # Add enhanced data
        base_data.update(
            {
                "results": enhanced_results,
                "unmapped_constructs": unmapped_summary,
                "unique_unmapped_count": len(unmapped_summary),
                "total_warnings": total_warnings,
                "manual_review_items": [],  # Could be populated with specific issues
                "manual_review_count": len(unmapped_summary),  # Rough estimate
            }
        )

        # Calculate readiness score
        base_data["migration_readiness_score"] = calculate_migration_readiness_score(base_data)

        # Calculate automated percentage
        if base_data["total_files"] > 0:
            manual_items = len(unmapped_summary)
            automated = base_data["total_files"] - (manual_items / 10)  # Rough estimate
            base_data["automated_percentage"] = max(
                0, min(100, (automated / base_data["total_files"]) * 100)
            )
        else:
            base_data["automated_percentage"] = 0.0

        # Generate recommendations
        base_data["recommendations"] = generate_recommendations(base_data)

        return base_data


class BatchConverter:
    """Batch converter for converting directories of 4GL files to Python."""

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        recursive: bool = True,
        format_code: bool = True,
        line_length: int = 88,
        overwrite: bool = False,
        resolve_dependencies: bool = False,
        sql_backend: str = "wbjdbc",
    ):
        """Initialize the batch converter.

        Args:
            source_dir: Source directory containing .4gl files
            target_dir: Target directory for converted .py files
            recursive: Whether to recursively search subdirectories
            format_code: Whether to format generated Python code with black
            line_length: Maximum line length for code formatting
            overwrite: Whether to overwrite existing .py files
            resolve_dependencies: Whether to resolve dependencies and convert in order
            sql_backend: SQL backend to use ("wbjdbc" or "wborm")
        """
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.recursive = recursive
        self.format_code = format_code
        self.line_length = line_length
        self.overwrite = overwrite
        self.resolve_dependencies = resolve_dependencies
        self.sql_backend = sql_backend

        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        if not self.source_dir.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {self.source_dir}")

    def find_4gl_files(self) -> List[Path]:
        """Find all .4gl files in the source directory.

        Returns:
            List of paths to .4gl files
        """
        if self.recursive:
            return sorted(self.source_dir.rglob("*.4gl"))
        else:
            return sorted(self.source_dir.glob("*.4gl"))

    def get_target_path(self, source_file: Path) -> Path:
        """Get the target path for a source file, preserving directory structure.

        Args:
            source_file: Source .4gl file path

        Returns:
            Target .py file path
        """
        # Get relative path from source directory
        relative_path = source_file.relative_to(self.source_dir)

        # Change extension to .py
        target_relative = relative_path.with_suffix(".py")

        # Combine with target directory
        return self.target_dir / target_relative

    def convert_file(self, source_file: Path) -> ConversionResult:
        """Convert a single 4GL file to Python.

        Args:
            source_file: Path to the .4gl source file

        Returns:
            ConversionResult with conversion details
        """
        import time

        target_file = self.get_target_path(source_file)

        # Check if target exists and we're not overwriting
        if target_file.exists() and not self.overwrite:
            return ConversionResult(
                source_file=source_file,
                target_file=target_file,
                success=False,
                error="Target file already exists (use --overwrite to replace)",
                error_type="FileExists",
            )

        try:
            start_time = time.time()

            # Read source code
            source_code = source_file.read_text()
            lines_in_source = len(source_code.splitlines())

            # Convert to Python
            python_code = convert_source(
                source_code,
                filename=str(source_file),
                format_code=self.format_code,
                line_length=self.line_length,
                sql_backend=self.sql_backend,
            )

            # Story 4.5: Scan for unmapped constructs
            unmapped = scan_for_unmapped_constructs(python_code)

            # Story 4.5: Count warnings (TODO comments are warnings)
            warning_count = python_code.count("# TODO")

            # Create target directory if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Write converted code
            target_file.write_text(python_code)

            execution_time = time.time() - start_time

            return ConversionResult(
                source_file=source_file,
                target_file=target_file,
                success=True,
                lines_converted=lines_in_source,
                execution_time=execution_time,
                unmapped_constructs=unmapped,
                warning_count=warning_count,
            )

        except LexerError as e:
            return ConversionResult(
                source_file=source_file,
                target_file=target_file,
                success=False,
                error=str(e),
                error_type="LexerError",
            )
        except ParserError as e:
            return ConversionResult(
                source_file=source_file,
                target_file=target_file,
                success=False,
                error=str(e),
                error_type="ParserError",
            )
        except Exception as e:
            return ConversionResult(
                source_file=source_file,
                target_file=target_file,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )

    def convert_batch(self) -> BatchConversionReport:
        """Convert all 4GL files in the source directory.

        Returns:
            BatchConversionReport with conversion results
        """
        report = BatchConversionReport(source_dir=self.source_dir, target_dir=self.target_dir)

        # Find all 4GL files
        files_to_convert = self.find_4gl_files()

        # If dependency resolution is enabled, sort files by dependencies
        if self.resolve_dependencies:
            try:
                from .dependencies import DependencyResolver

                resolver = DependencyResolver(self.source_dir, self.recursive)
                resolver.analyze()

                # Check for circular dependencies
                circular_deps = resolver.get_circular_dependencies()
                if circular_deps:
                    # Include warning in report but continue
                    report.has_circular_dependencies = True
                    report.circular_dependency_path = circular_deps

                # Get conversion order (dependencies first)
                files_to_convert = resolver.get_conversion_order()
            except ValueError:
                # Circular dependency detected, fall back to alphabetical order
                pass

        report.total_files = len(files_to_convert)

        # Convert each file
        for source_file in files_to_convert:
            result = self.convert_file(source_file)
            report.results.append(result)

            if result.success:
                report.successful += 1
            elif result.error_type == "FileExists":
                report.skipped += 1
            else:
                report.failed += 1

        report.end_time = datetime.now()

        return report


def convert_directory(
    source_dir: str,
    target_dir: str,
    recursive: bool = True,
    format_code: bool = True,
    line_length: int = 88,
    overwrite: bool = False,
    resolve_dependencies: bool = False,
    sql_backend: str = "wbjdbc",
    report_file: Optional[str] = None,
    report_format: str = "text",
) -> BatchConversionReport:
    """Convert a directory of 4GL files to Python.

    Args:
        source_dir: Source directory containing .4gl files
        target_dir: Target directory for converted .py files
        recursive: Whether to recursively search subdirectories
        format_code: Whether to format generated Python code with black
        line_length: Maximum line length for code formatting
        overwrite: Whether to overwrite existing .py files
        resolve_dependencies: Whether to resolve dependencies and convert in order
        sql_backend: SQL backend to use ("wbjdbc" or "wborm")
        report_file: Optional file path to save the report
        report_format: Format for the report ('text' or 'json')

    Returns:
        BatchConversionReport with conversion results
    """
    converter = BatchConverter(
        source_dir=Path(source_dir),
        target_dir=Path(target_dir),
        recursive=recursive,
        format_code=format_code,
        line_length=line_length,
        overwrite=overwrite,
        resolve_dependencies=resolve_dependencies,
        sql_backend=sql_backend,
    )

    report = converter.convert_batch()

    # Save report if requested
    if report_file:
        report_path = Path(report_file)
        if report_format == "json":
            report_content = json.dumps(report.to_dict(), indent=2)
        elif report_format == "markdown":
            report_content = report.to_markdown()
        elif report_format == "html":
            report_content = report.to_html()
        else:  # text (default)
            report_content = report.to_text()

        report_path.write_text(report_content, encoding="utf-8")

    return report
