"""
Generator for 4make.def files.

Replicates the logic from wb4make script to create build configuration files.
"""

from pathlib import Path
from typing import List, Optional


class MakeDefGenerator:
    """Generates 4make.def files for 4GL compilation."""

    def __init__(
        self,
        target: Optional[str] = None,
        library_path: str = "/test/QX/src/lib/libs_final.a",
    ):
        """
        Initialize the generator.

        Args:
            target: Target executable name (defaults to directory name)
            library_path: Path to the library file to link
        """
        self.target = target
        self.library_path = library_path

    def generate_from_directory(self, directory: Path, output_file: Optional[Path] = None) -> str:
        """
        Generate 4make.def from files in a directory.

        Replicates the wb4make script logic:
        - Lists all .4gl files as SOURCES
        - Lists all .per files as FORMS
        - Lists all .msg files as MSG
        - Sets TARGET based on directory name or provided name

        Args:
            directory: Directory containing 4GL files
            output_file: Optional path to write the 4make.def file

        Returns:
            Generated 4make.def content

        Raises:
            ValueError: If no .4gl files found in directory
        """
        directory = Path(directory)

        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")

        # Find all relevant files
        sources = self._find_files(directory, "*.4gl")
        forms = self._find_files(directory, "*.per")
        messages = self._find_files(directory, "*.msg")

        if not sources:
            raise ValueError(f"No 4GL files found in {directory}")

        # Determine target name
        target = self.target or directory.name

        # Generate content
        content = self.generate(target=target, sources=sources, forms=forms, messages=messages)

        # Write to file if requested
        if output_file:
            output_file = Path(output_file)
            with open(output_file, "w") as f:
                f.write(content)

        return content

    def generate(
        self,
        target: str,
        sources: List[str],
        forms: Optional[List[str]] = None,
        messages: Optional[List[str]] = None,
        additional_libraries: Optional[List[str]] = None,
    ) -> str:
        """
        Generate 4make.def content.

        Args:
            target: Target executable name
            sources: List of .4gl source files
            forms: List of .per form files
            messages: List of .msg message files
            additional_libraries: Additional library files to link

        Returns:
            4make.def file content
        """
        forms = forms or []
        messages = messages or []
        additional_libraries = additional_libraries or []

        lines = []

        # TARGET line
        lines.append(f"TARGET={target}")

        # SOURCES line (4gl files + libraries)
        sources_line = "SOURCES=" + " ".join(sources)
        if self.library_path:
            sources_line += f" {self.library_path}"
        for lib in additional_libraries:
            sources_line += f" {lib}"
        lines.append(sources_line)

        # FORMS line
        forms_line = "FORMS=" + " ".join(forms) if forms else "FORMS="
        lines.append(forms_line)

        # MSG line
        msg_line = "MSG=" + " ".join(messages) if messages else "MSG="
        lines.append(msg_line)

        return "\n".join(lines) + "\n"

    def generate_for_single_file(
        self, source_file: Path, output_file: Optional[Path] = None
    ) -> str:
        """
        Generate 4make.def for a single .4gl file.

        Args:
            source_file: Path to the .4gl file
            output_file: Optional path to write the 4make.def file

        Returns:
            Generated 4make.def content

        Raises:
            ValueError: If file doesn't exist or isn't a .4gl file
        """
        source_file = Path(source_file)

        if not source_file.exists():
            raise ValueError(f"Source file does not exist: {source_file}")

        if source_file.suffix != ".4gl":
            raise ValueError(f"File must be a .4gl file: {source_file}")

        # Get directory and check for related files
        directory = source_file.parent
        base_name = source_file.stem

        # Look for related .per and .msg files
        per_file = directory / f"{base_name}.per"
        msg_file = directory / f"{base_name}.msg"

        forms = [per_file.name] if per_file.exists() else []
        messages = [msg_file.name] if msg_file.exists() else []

        # Generate content
        target = self.target or base_name
        content = self.generate(
            target=target,
            sources=[source_file.name],
            forms=forms,
            messages=messages,
        )

        # Write to file if requested
        if output_file:
            output_file = Path(output_file)
            with open(output_file, "w") as f:
                f.write(content)

        return content

    def _find_files(self, directory: Path, pattern: str) -> List[str]:
        """
        Find files matching pattern in directory.

        Args:
            directory: Directory to search
            pattern: Glob pattern (e.g., "*.4gl")

        Returns:
            List of matching filenames (not full paths)
        """
        files = []
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                files.append(file_path.name)
        return sorted(files)


def generate_4make_def(
    directory: Path,
    target: Optional[str] = None,
    library_path: str = "/test/QX/src/lib/libs_final.a",
    output_file: Optional[Path] = None,
) -> str:
    """
    Convenience function to generate 4make.def from a directory.

    Args:
        directory: Directory containing 4GL files
        target: Target executable name (defaults to directory name)
        library_path: Path to the library file
        output_file: Optional path to write the 4make.def file

    Returns:
        Generated 4make.def content
    """
    generator = MakeDefGenerator(target=target, library_path=library_path)
    return generator.generate_from_directory(directory, output_file)
