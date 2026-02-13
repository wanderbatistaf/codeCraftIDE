"""
Unit tests for the Batch Converter module.

Tests for Epic 4, Story 4.2: File-Based Batch Conversion Tool
"""

import json
from pathlib import Path

import pytest

from fglinterpreter.converter.batch import (
    BatchConversionReport,
    BatchConverter,
    ConversionResult,
    convert_directory,
)


@pytest.fixture
def temp_source_dir(tmp_path: Path) -> Path:
    """Create a temporary source directory with test 4GL files."""
    source = tmp_path / "source"
    source.mkdir()

    # Create test 4GL files
    (source / "test1.4gl").write_text("""
        MAIN
            DISPLAY "Test 1"
        END MAIN
        """)

    (source / "test2.4gl").write_text("""
        FUNCTION add(a, b)
            DEFINE a INTEGER
            DEFINE b INTEGER
            RETURN a + b
        END FUNCTION

        MAIN
            DEFINE result INTEGER
            LET result = add(5, 3)
            DISPLAY result
        END MAIN
        """)

    # Create subdirectory with more files
    subdir = source / "subdir"
    subdir.mkdir()

    (subdir / "test3.4gl").write_text("""
        MAIN
            DISPLAY "Test 3 in subdirectory"
        END MAIN
        """)

    # Create an invalid 4GL file (syntax error)
    (source / "invalid.4gl").write_text("""
        MAIN
            DISPLAY "Missing END MAIN
        """)

    return source


@pytest.fixture
def temp_target_dir(tmp_path: Path) -> Path:
    """Create a temporary target directory."""
    target = tmp_path / "target"
    target.mkdir()
    return target


@pytest.mark.unit
class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_successful_result(self) -> None:
        """Test creating a successful conversion result."""
        result = ConversionResult(
            source_file=Path("test.4gl"),
            target_file=Path("test.py"),
            success=True,
            lines_converted=10,
            execution_time=0.123,
        )

        assert result.success is True
        assert result.source_file == Path("test.4gl")
        assert result.target_file == Path("test.py")
        assert result.lines_converted == 10
        assert result.execution_time == 0.123
        assert result.error is None
        assert result.error_type is None

    def test_failed_result(self) -> None:
        """Test creating a failed conversion result."""
        result = ConversionResult(
            source_file=Path("test.4gl"),
            target_file=Path("test.py"),
            success=False,
            error="Parse error at line 5",
            error_type="ParserError",
        )

        assert result.success is False
        assert result.error == "Parse error at line 5"
        assert result.error_type == "ParserError"
        assert result.lines_converted == 0


@pytest.mark.unit
class TestBatchConversionReport:
    """Tests for BatchConversionReport dataclass."""

    def test_empty_report(self) -> None:
        """Test creating an empty report."""
        report = BatchConversionReport(source_dir=Path("/src"), target_dir=Path("/target"))

        assert report.total_files == 0
        assert report.successful == 0
        assert report.failed == 0
        assert report.skipped == 0
        assert report.success_rate == 0.0
        assert len(report.results) == 0

    def test_report_with_results(self) -> None:
        """Test report with conversion results."""
        report = BatchConversionReport(
            source_dir=Path("/src"),
            target_dir=Path("/target"),
            total_files=3,
            successful=2,
            failed=1,
        )

        assert report.total_files == 3
        assert report.successful == 2
        assert report.failed == 1
        assert report.success_rate == pytest.approx(66.67, rel=0.1)

    def test_report_to_dict(self) -> None:
        """Test converting report to dictionary."""
        report = BatchConversionReport(
            source_dir=Path("/src"),
            target_dir=Path("/target"),
            total_files=1,
            successful=1,
        )

        result = ConversionResult(
            source_file=Path("test.4gl"),
            target_file=Path("test.py"),
            success=True,
            lines_converted=5,
            execution_time=0.1,
        )
        report.results.append(result)

        report_dict = report.to_dict()

        assert report_dict["source_dir"] == "/src"
        assert report_dict["target_dir"] == "/target"
        assert report_dict["total_files"] == 1
        assert report_dict["successful"] == 1
        assert report_dict["failed"] == 0
        assert len(report_dict["results"]) == 1
        assert report_dict["results"][0]["success"] is True

    def test_report_to_text(self) -> None:
        """Test generating text report."""
        report = BatchConversionReport(
            source_dir=Path("/src"),
            target_dir=Path("/target"),
            total_files=1,
            successful=1,
        )

        result = ConversionResult(
            source_file=Path("test.4gl"),
            target_file=Path("test.py"),
            success=True,
            lines_converted=5,
            execution_time=0.1,
        )
        report.results.append(result)

        text = report.to_text()

        assert "4GL to Python Batch Conversion Report" in text
        assert "Source Directory: /src" in text
        assert "Target Directory: /target" in text
        assert "Total Files: 1" in text
        assert "Successful: 1" in text
        assert "✓ SUCCESS" in text


@pytest.mark.unit
class TestBatchConverter:
    """Tests for BatchConverter class."""

    def test_init_with_valid_directories(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test initializing converter with valid directories."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
        )

        assert converter.source_dir == temp_source_dir.resolve()
        assert converter.target_dir == temp_target_dir.resolve()
        assert converter.recursive is True
        assert converter.format_code is True
        assert converter.overwrite is False

    def test_init_with_nonexistent_source(self, tmp_path: Path) -> None:
        """Test initializing converter with nonexistent source directory."""
        with pytest.raises(FileNotFoundError):
            BatchConverter(
                source_dir=tmp_path / "nonexistent",
                target_dir=tmp_path / "target",
            )

    def test_init_with_file_as_source(self, tmp_path: Path) -> None:
        """Test initializing converter with file as source directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(NotADirectoryError):
            BatchConverter(
                source_dir=file_path,
                target_dir=tmp_path / "target",
            )

    def test_find_4gl_files_non_recursive(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test finding 4GL files without recursion."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            recursive=False,
        )

        files = converter.find_4gl_files()

        # Should find only top-level .4gl files (test1, test2, invalid)
        assert len(files) == 3
        assert all(f.suffix == ".4gl" for f in files)
        assert all(f.parent == temp_source_dir for f in files)

    def test_find_4gl_files_recursive(self, temp_source_dir: Path, temp_target_dir: Path) -> None:
        """Test finding 4GL files with recursion."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            recursive=True,
        )

        files = converter.find_4gl_files()

        # Should find all .4gl files including subdirectories (test1, test2, invalid, test3)
        assert len(files) == 4
        assert all(f.suffix == ".4gl" for f in files)

    def test_get_target_path_preserves_structure(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test that target path preserves directory structure."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
        )

        # Test top-level file
        source_file = temp_source_dir / "test1.4gl"
        target_file = converter.get_target_path(source_file)
        assert target_file == temp_target_dir / "test1.py"

        # Test subdirectory file
        source_file = temp_source_dir / "subdir" / "test3.4gl"
        target_file = converter.get_target_path(source_file)
        assert target_file == temp_target_dir / "subdir" / "test3.py"

    def test_convert_file_success(self, temp_source_dir: Path, temp_target_dir: Path) -> None:
        """Test successfully converting a single file."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            format_code=False,  # Skip formatting for speed
        )

        source_file = temp_source_dir / "test1.4gl"
        result = converter.convert_file(source_file)

        assert result.success is True
        assert result.source_file == source_file
        assert result.target_file.exists()
        assert result.target_file.suffix == ".py"
        assert result.lines_converted > 0
        assert result.execution_time > 0
        assert result.error is None

        # Check converted content
        python_code = result.target_file.read_text()
        assert "def main()" in python_code
        assert 'print("Test 1")' in python_code

    def test_convert_file_with_syntax_error(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test converting a file with syntax error."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
        )

        source_file = temp_source_dir / "invalid.4gl"
        result = converter.convert_file(source_file)

        assert result.success is False
        assert result.error is not None
        assert result.error_type in ["LexerError", "ParserError"]

    def test_convert_file_skip_existing_without_overwrite(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test that existing files are skipped without overwrite flag."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            overwrite=False,
        )

        # Create existing target file
        source_file = temp_source_dir / "test1.4gl"
        target_file = converter.get_target_path(source_file)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("existing content")

        result = converter.convert_file(source_file)

        assert result.success is False
        assert result.error_type == "FileExists"
        assert "already exists" in result.error

    def test_convert_file_overwrite_existing(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test that existing files are overwritten with overwrite flag."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            overwrite=True,
            format_code=False,
        )

        # Create existing target file
        source_file = temp_source_dir / "test1.4gl"
        target_file = converter.get_target_path(source_file)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("existing content")

        result = converter.convert_file(source_file)

        assert result.success is True
        # Check that content was overwritten
        python_code = result.target_file.read_text()
        assert "existing content" not in python_code
        assert "def main()" in python_code

    def test_convert_batch_success(self, temp_source_dir: Path, temp_target_dir: Path) -> None:
        """Test batch converting multiple files."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            recursive=True,
            format_code=False,
        )

        report = converter.convert_batch()

        assert report.total_files == 4  # test1, test2, test3, invalid
        assert report.successful == 3  # test1, test2, test3
        assert report.failed == 1  # invalid
        assert report.skipped == 0
        assert report.end_time is not None
        assert report.duration > 0

        # Check that successful files were created
        assert (temp_target_dir / "test1.py").exists()
        assert (temp_target_dir / "test2.py").exists()
        assert (temp_target_dir / "subdir" / "test3.py").exists()

    def test_convert_batch_preserves_directory_structure(
        self, temp_source_dir: Path, temp_target_dir: Path
    ) -> None:
        """Test that batch conversion preserves directory structure."""
        converter = BatchConverter(
            source_dir=temp_source_dir,
            target_dir=temp_target_dir,
            recursive=True,
            format_code=False,
        )

        _ = converter.convert_batch()

        # Check directory structure
        assert (temp_target_dir / "subdir").exists()
        assert (temp_target_dir / "subdir").is_dir()
        assert (temp_target_dir / "subdir" / "test3.py").exists()


@pytest.mark.unit
class TestConvertDirectoryAPI:
    """Tests for the high-level convert_directory API."""

    def test_convert_directory_basic(self, temp_source_dir: Path, temp_target_dir: Path) -> None:
        """Test basic directory conversion."""
        report = convert_directory(
            source_dir=str(temp_source_dir),
            target_dir=str(temp_target_dir),
            recursive=True,
            format_code=False,
        )

        assert isinstance(report, BatchConversionReport)
        assert report.total_files > 0
        assert report.successful > 0

    def test_convert_directory_with_text_report(
        self, temp_source_dir: Path, tmp_path: Path
    ) -> None:
        """Test directory conversion with text report generation."""
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        report_file = tmp_path / "report.txt"

        _ = convert_directory(
            source_dir=str(temp_source_dir),
            target_dir=str(target_dir),
            recursive=False,
            format_code=False,
            report_file=str(report_file),
            report_format="text",
        )

        assert report_file.exists()
        report_content = report_file.read_text(encoding="utf-8")
        assert "4GL to Python Batch Conversion Report" in report_content
        assert "Total Files:" in report_content

    def test_convert_directory_with_json_report(
        self, temp_source_dir: Path, tmp_path: Path
    ) -> None:
        """Test directory conversion with JSON report generation."""
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        report_file = tmp_path / "report.json"

        _ = convert_directory(
            source_dir=str(temp_source_dir),
            target_dir=str(target_dir),
            recursive=False,
            format_code=False,
            report_file=str(report_file),
            report_format="json",
        )

        assert report_file.exists()
        report_content = json.loads(report_file.read_text())
        assert "total_files" in report_content
        assert "successful" in report_content
        assert "results" in report_content
        assert isinstance(report_content["results"], list)
