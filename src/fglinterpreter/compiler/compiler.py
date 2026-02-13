"""
4GL Compiler integration using 4make.

Provides compilation functionality for 4GL source files using Informix 4make.
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .error_parser import CompilationMessage, ErrorFileParser
from .exceptions import (
    CompilationError,
    CompilerExecutionError,
    CompilerNotFoundError,
    MakeDefGenerationError,
)
from .make_def_generator import MakeDefGenerator


@dataclass
class CompilationResult:
    """Result of a compilation operation."""

    success: bool
    target: str
    output: str = ""
    errors: List[CompilationMessage] = field(default_factory=list)
    warnings: List[CompilationMessage] = field(default_factory=list)
    compilation_time: float = 0.0
    make_def_content: str = ""

    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get number of warnings."""
        return len(self.warnings)

    @property
    def has_errors(self) -> bool:
        """Check if compilation has errors."""
        return len(self.errors) > 0

    def format_messages(self, include_warnings: bool = True) -> str:
        """
        Format compilation messages for display.

        Args:
            include_warnings: Whether to include warnings

        Returns:
            Formatted message string
        """
        lines = []

        if self.errors:
            lines.append("❌ Compilation Errors:")
            lines.append("=" * 60)
            for error in self.errors:
                lines.append(str(error))
                lines.append("")

        if include_warnings and self.warnings:
            lines.append("⚠️  Warnings:")
            lines.append("=" * 60)
            for warning in self.warnings:
                lines.append(str(warning))
                lines.append("")

        if self.success:
            lines.append(f"✅ Compilation successful: {self.target}")
            if self.compilation_time:
                lines.append(f"   Time: {self.compilation_time:.2f}s")
        else:
            lines.append(f"❌ Compilation failed: {self.error_count} error(s)")

        return "\n".join(lines)


class FourMakeCompiler:
    """Compiler for 4GL using 4make."""

    def __init__(
        self,
        make_executable: str = "4make",
        library_path: str = "/test/QX/src/lib/libs_final.a",
        work_dir: Optional[Path] = None,
        keep_temp_files: bool = False,
    ):
        """
        Initialize the compiler.

        Args:
            make_executable: Path to 4make executable (or command if in PATH)
            library_path: Path to the library file to link
            work_dir: Working directory for compilation (uses temp if not specified)
            keep_temp_files: Keep temporary files after compilation
        """
        self.make_executable = make_executable
        self.library_path = library_path
        self.work_dir = Path(work_dir) if work_dir else None
        self.keep_temp_files = keep_temp_files
        self._verify_compiler()

    def _verify_compiler(self):
        """Verify that 4make executable exists and is accessible."""
        try:
            subprocess.run(
                [self.make_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # 4make might not support --version, so we just check if it exists
        except FileNotFoundError:
            # Try without --version
            try:
                subprocess.run(
                    [self.make_executable],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                raise CompilerNotFoundError(
                    f"4make executable not found: {self.make_executable}. "
                    "Make sure it's installed and in your PATH."
                )
        except subprocess.TimeoutExpired:
            # Timeout is OK - means the command exists but is waiting for input
            pass

    def compile_file(
        self, source_file: Path, target_name: Optional[str] = None
    ) -> CompilationResult:
        """
        Compile a single 4GL file.

        Args:
            source_file: Path to the .4gl file
            target_name: Target executable name (defaults to file stem)

        Returns:
            CompilationResult object

        Raises:
            CompilationError: If compilation fails critically
        """
        import time

        source_file = Path(source_file)
        if not source_file.exists():
            raise CompilationError(f"Source file not found: {source_file}")

        if source_file.suffix != ".4gl":
            raise CompilationError(f"File must be a .4gl file: {source_file}")

        target_name = target_name or source_file.stem

        # Create or use work directory
        if self.work_dir:
            work_dir = self.work_dir
            work_dir.mkdir(parents=True, exist_ok=True)
            cleanup = False
        else:
            work_dir = Path(tempfile.mkdtemp(prefix="4make_"))
            cleanup = not self.keep_temp_files

        try:
            # Copy source file to work directory
            work_source = work_dir / source_file.name
            shutil.copy2(source_file, work_source)

            # Check for related .per and .msg files
            for ext in [".per", ".msg"]:
                related_file = source_file.with_suffix(ext)
                if related_file.exists():
                    shutil.copy2(related_file, work_dir / related_file.name)

            # Compile in work directory
            start_time = time.time()
            result = self._compile_in_directory(work_dir, target_name)
            result.compilation_time = time.time() - start_time

            return result

        finally:
            if cleanup and work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)

    def compile_directory(
        self, directory: Path, target_name: Optional[str] = None
    ) -> CompilationResult:
        """
        Compile all 4GL files in a directory.

        Args:
            directory: Directory containing 4GL files
            target_name: Target executable name (defaults to directory name)

        Returns:
            CompilationResult object
        """
        import time

        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise CompilationError(f"Directory not found: {directory}")

        target_name = target_name or directory.name

        start_time = time.time()
        result = self._compile_in_directory(directory, target_name)
        result.compilation_time = time.time() - start_time

        return result

    def _compile_in_directory(self, directory: Path, target_name: str) -> CompilationResult:
        """
        Perform compilation in the given directory.

        Args:
            directory: Directory containing source files
            target_name: Target executable name

        Returns:
            CompilationResult object
        """
        # Generate 4make.def
        try:
            generator = MakeDefGenerator(target=target_name, library_path=self.library_path)
            make_def_path = directory / "4make.def"
            make_def_content = generator.generate_from_directory(
                directory, output_file=make_def_path
            )
        except Exception as e:
            raise MakeDefGenerationError(f"Failed to generate 4make.def: {e}")

        # Execute 4make
        output, return_code = self._execute_4make(directory)

        # Check for .4er error file
        error_file = directory / f"{target_name}.4er"
        messages = []

        if error_file.exists():
            parser = ErrorFileParser(default_file=f"{target_name}.4gl")
            messages = parser.parse_file(error_file)

            # Delete the .4er file unless keeping temp files
            if not self.keep_temp_files:
                error_file.unlink()

        # Separate errors and warnings
        errors = [msg for msg in messages if msg.severity == "error"]
        warnings = [msg for msg in messages if msg.severity in ["warning", "info"]]

        # Determine success
        success = return_code == 0 and len(errors) == 0

        return CompilationResult(
            success=success,
            target=target_name,
            output=output,
            errors=errors,
            warnings=warnings,
            make_def_content=make_def_content,
        )

    def _execute_4make(self, directory: Path) -> Tuple[str, int]:
        """
        Execute 4make in the given directory.

        Args:
            directory: Directory containing 4make.def

        Returns:
            Tuple of (output, return_code)

        Raises:
            CompilerExecutionError: If 4make fails to execute
        """
        try:
            result = subprocess.run(
                [self.make_executable],
                cwd=str(directory),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            output = result.stdout + result.stderr
            return output, result.returncode

        except subprocess.TimeoutExpired:
            raise CompilerExecutionError("Compilation timeout (5 minutes)")
        except Exception as e:
            raise CompilerExecutionError(f"Failed to execute 4make: {e}")


def compile_4gl_file(
    source_file: Path,
    target_name: Optional[str] = None,
    make_executable: str = "4make",
    library_path: str = "/test/QX/src/lib/libs_final.a",
) -> CompilationResult:
    """
    Convenience function to compile a 4GL file.

    Args:
        source_file: Path to the .4gl file
        target_name: Target executable name
        make_executable: Path to 4make executable
        library_path: Path to library file

    Returns:
        CompilationResult object
    """
    compiler = FourMakeCompiler(make_executable=make_executable, library_path=library_path)
    return compiler.compile_file(source_file, target_name)
