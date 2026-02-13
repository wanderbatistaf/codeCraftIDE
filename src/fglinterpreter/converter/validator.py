"""
Validation framework for ensuring 4GL to Python conversion fidelity.

This module provides tools to validate that converted Python scripts
behave identically to their original 4GL counterparts.
"""

import difflib
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..interpreter.interpreter import Interpreter


@dataclass
class ValidationContext:
    """
    Context for a validation test.

    Contains all information needed to run and validate a 4GL → Python conversion.
    """

    source_4gl: str  # 4GL source code
    source_python: str  # Converted Python code
    test_name: str  # Name of validation test
    input_data: Dict[str, Any] = field(default_factory=dict)  # Input variables/data
    expected_output: Optional[str] = None  # Expected stdout (if known)
    custom_validators: List[str] = field(default_factory=list)  # Custom validators
    timeout: int = 30  # Execution timeout in seconds
    validation_mode: str = "exact"  # exact, normalized, or semantic


@dataclass
class ValidationResult:
    """
    Result of a validation test.

    Contains execution results, comparison data, and validation status.
    """

    test_name: str
    success: bool

    # Execution results
    fgl_output: str = ""
    python_output: str = ""
    fgl_exit_code: int = 0
    python_exit_code: int = 0
    fgl_execution_time: float = 0.0
    python_execution_time: float = 0.0

    # Comparison
    outputs_match: bool = False
    exit_codes_match: bool = True
    diff_output: str = ""  # Unified diff format

    # Errors
    fgl_error: Optional[str] = None
    python_error: Optional[str] = None

    # Custom validation
    custom_validation_results: Dict[str, bool] = field(default_factory=dict)
    custom_validation_messages: Dict[str, str] = field(default_factory=dict)

    @property
    def performance_ratio(self) -> float:
        """Calculate Python/4GL execution time ratio (< 1.0 means Python is faster)."""
        if self.fgl_execution_time == 0:
            return 1.0
        return self.python_execution_time / self.fgl_execution_time

    def __str__(self) -> str:
        """Generate human-readable summary."""
        status = "✓ PASSED" if self.success else "✗ FAILED"
        lines = [
            f"Validation: {self.test_name}",
            f"Status: {status}",
            "",
            "4GL Execution:",
            f"  Exit Code: {self.fgl_exit_code}",
            f"  Time: {self.fgl_execution_time:.3f}s",
            f"  Error: {self.fgl_error or 'None'}",
            "",
            "Python Execution:",
            f"  Exit Code: {self.python_exit_code}",
            f"  Time: {self.python_execution_time:.3f}s",
            f"  Error: {self.python_error or 'None'}",
            f"  Performance: {self.performance_ratio:.2f}x",
            "",
            "Comparison:",
            f"  Outputs Match: {'Yes' if self.outputs_match else 'No'}",
            f"  Exit Codes Match: {'Yes' if self.exit_codes_match else 'No'}",
        ]

        if self.custom_validation_results:
            lines.append("")
            lines.append("Custom Validators:")
            for name, result in self.custom_validation_results.items():
                status_icon = "✓" if result else "✗"
                message = self.custom_validation_messages.get(name, "")
                lines.append(f"  {status_icon} {name}: {message}")

        if self.diff_output:
            lines.append("")
            lines.append("Diff:")
            lines.append(self.diff_output)

        return "\n".join(lines)


class DiffReporter:
    """Generate diff reports in various formats."""

    @staticmethod
    def unified_diff(fgl_output: str, python_output: str, context_lines: int = 3) -> str:
        """
        Generate unified diff format.

        Args:
            fgl_output: Output from 4GL execution
            python_output: Output from Python execution
            context_lines: Number of context lines to show

        Returns:
            Unified diff string
        """
        diff = difflib.unified_diff(
            fgl_output.splitlines(keepends=True),
            python_output.splitlines(keepends=True),
            fromfile="4GL Output",
            tofile="Python Output",
            n=context_lines,
        )
        return "".join(diff)

    @staticmethod
    def side_by_side_diff(fgl_output: str, python_output: str, width: int = 80) -> str:
        """
        Generate side-by-side diff.

        Args:
            fgl_output: Output from 4GL execution
            python_output: Output from Python execution
            width: Total width of the output

        Returns:
            Side-by-side diff string
        """
        fgl_lines = fgl_output.splitlines()
        python_lines = python_output.splitlines()
        max_lines = max(len(fgl_lines), len(python_lines))

        # Pad shorter output
        fgl_lines += [""] * (max_lines - len(fgl_lines))
        python_lines += [""] * (max_lines - len(python_lines))

        col_width = width // 2 - 3
        lines = []
        lines.append("4GL Output".ljust(col_width) + " | " + "Python Output")
        lines.append("-" * col_width + "-+-" + "-" * col_width)

        for fgl_line, python_line in zip(fgl_lines, python_lines):
            fgl_part = fgl_line[:col_width].ljust(col_width)
            python_part = python_line[:col_width].ljust(col_width)

            if fgl_line != python_line:
                marker = "≠"
            else:
                marker = "|"

            lines.append(f"{fgl_part} {marker} {python_part}")

        return "\n".join(lines)

    @staticmethod
    def html_diff(fgl_output: str, python_output: str) -> str:
        """
        Generate interactive HTML diff.

        Args:
            fgl_output: Output from 4GL execution
            python_output: Output from Python execution

        Returns:
            HTML diff string
        """
        differ = difflib.HtmlDiff(wrapcolumn=80)
        html = differ.make_file(
            fgl_output.splitlines(),
            python_output.splitlines(),
            fromdesc="4GL Output",
            todesc="Python Output",
        )
        return html


class CustomValidatorRegistry:
    """Registry for custom validation functions."""

    def __init__(self):
        self._validators: Dict[str, Callable] = {}

        # Register built-in validators
        self.register("numeric_tolerance", validate_numeric_output)
        self.register("whitespace_normalized", validate_whitespace_normalized)

    def register(self, name: str, validator: Callable) -> None:
        """
        Register a custom validator function.

        Args:
            name: Unique name for the validator
            validator: Callable that takes (fgl_output, python_output, context)
                      and returns (success: bool, message: str)
        """
        self._validators[name] = validator

    def run(
        self,
        name: str,
        fgl_output: str,
        python_output: str,
        context: ValidationContext,
    ) -> Tuple[bool, str]:
        """
        Run a custom validator.

        Args:
            name: Name of the validator to run
            fgl_output: Output from 4GL execution
            python_output: Output from Python execution
            context: Validation context

        Returns:
            (success, message) tuple
        """
        if name not in self._validators:
            return False, f"Unknown validator: {name}"

        try:
            return self._validators[name](fgl_output, python_output, context)
        except Exception as e:
            return False, f"Validator error: {str(e)}"

    def list_validators(self) -> List[str]:
        """Get list of registered validator names."""
        return list(self._validators.keys())


class Validator:
    """Main validation framework."""

    def __init__(self):
        self.interpreter = Interpreter()
        self.custom_validators = CustomValidatorRegistry()

    def validate(self, context: ValidationContext) -> ValidationResult:
        """
        Run validation test comparing 4GL and Python execution.

        Steps:
        1. Execute 4GL code through interpreter
        2. Execute converted Python code
        3. Compare outputs (stdout, stderr, exit codes)
        4. Run custom validators if specified
        5. Generate diff report
        6. Return comprehensive result

        Args:
            context: Validation context with source code and test data

        Returns:
            ValidationResult with execution and comparison data
        """
        result = ValidationResult(test_name=context.test_name, success=False)

        # Execute 4GL code
        fgl_start = time.time()
        fgl_output, fgl_exit_code, fgl_error = self._execute_4gl(
            context.source_4gl, context.timeout
        )
        fgl_end = time.time()

        result.fgl_output = fgl_output
        result.fgl_exit_code = fgl_exit_code
        result.fgl_error = fgl_error
        result.fgl_execution_time = fgl_end - fgl_start

        # Execute Python code
        python_start = time.time()
        python_output, python_exit_code, python_error = self._execute_python(
            context.source_python, context.timeout
        )
        python_end = time.time()

        result.python_output = python_output
        result.python_exit_code = python_exit_code
        result.python_error = python_error
        result.python_execution_time = python_end - python_start

        # Compare exit codes
        result.exit_codes_match = fgl_exit_code == python_exit_code

        # Compare outputs based on validation mode
        if context.validation_mode == "exact":
            result.outputs_match = self._exact_match(fgl_output, python_output)
        elif context.validation_mode == "normalized":
            result.outputs_match = self._normalized_match(fgl_output, python_output)
        elif context.validation_mode == "semantic":
            result.outputs_match = self._semantic_match(fgl_output, python_output)
        else:
            result.outputs_match = self._exact_match(fgl_output, python_output)

        # Generate diff if outputs don't match
        if not result.outputs_match:
            result.diff_output = DiffReporter.unified_diff(fgl_output, python_output)

        # Run custom validators
        for validator_name in context.custom_validators:
            success, message = self.custom_validators.run(
                validator_name, fgl_output, python_output, context
            )
            result.custom_validation_results[validator_name] = success
            result.custom_validation_messages[validator_name] = message

        # Determine overall success
        result.success = (
            result.outputs_match
            and result.exit_codes_match
            and all(result.custom_validation_results.values())
            and fgl_error is None
            and python_error is None
        )

        return result

    def _execute_4gl(self, source_code: str, timeout: int) -> Tuple[str, int, Optional[str]]:
        """
        Execute 4GL code through interpreter.

        Args:
            source_code: 4GL source code
            timeout: Execution timeout in seconds

        Returns:
            (output, exit_code, error) tuple
        """
        try:
            # Capture stdout during interpretation
            import io
            from contextlib import redirect_stdout

            output_buffer = io.StringIO()

            with redirect_stdout(output_buffer):
                result = self.interpreter.execute(source_code)

            output = output_buffer.getvalue()

            if result.success:
                return output, 0, None
            else:
                return output, 1, result.error

        except Exception as e:
            return "", 1, str(e)

    def _execute_python(self, source_code: str, timeout: int) -> Tuple[str, int, Optional[str]]:
        """
        Execute Python code in subprocess.

        Args:
            source_code: Python source code
            timeout: Execution timeout in seconds

        Returns:
            (output, exit_code, error) tuple
        """
        try:
            # Write Python code to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(source_code)
                temp_file = f.name

            try:
                # Execute Python file
                proc = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                output = proc.stdout
                exit_code = proc.returncode
                error = proc.stderr if proc.stderr else None

                return output, exit_code, error

            finally:
                # Clean up temporary file
                Path(temp_file).unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            return "", 1, f"Execution timeout after {timeout} seconds"
        except Exception as e:
            return "", 1, str(e)

    def _exact_match(self, fgl_output: str, python_output: str) -> bool:
        """Compare outputs exactly (character-by-character)."""
        return fgl_output.strip() == python_output.strip()

    def _normalized_match(self, fgl_output: str, python_output: str) -> bool:
        """Compare outputs with normalized whitespace."""
        return self._normalize_output(fgl_output) == self._normalize_output(python_output)

    def _semantic_match(self, fgl_output: str, python_output: str) -> bool:
        """
        Compare outputs semantically (for structured data like JSON).

        Falls back to normalized matching if not valid JSON.
        """
        import json

        try:
            fgl_json = json.loads(fgl_output)
            python_json = json.loads(python_output)
            return fgl_json == python_json
        except json.JSONDecodeError:
            # Not JSON, fall back to normalized matching
            return self._normalized_match(fgl_output, python_output)

    @staticmethod
    def _normalize_output(text: str) -> str:
        """
        Normalize output for comparison.

        - Normalize line endings to \\n
        - Collapse multiple spaces to single space
        - Strip trailing whitespace per line
        - Strip leading/trailing newlines
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n")
        # Normalize multiple spaces
        text = re.sub(r" +", " ", text)
        # Strip trailing whitespace per line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines).strip()


# Built-in custom validators


def validate_numeric_output(
    fgl_output: str,
    python_output: str,
    context: ValidationContext,
    tolerance: float = 1e-6,
) -> Tuple[bool, str]:
    """
    Validate numeric outputs with floating-point tolerance.

    Extracts all numbers from both outputs and compares them with tolerance.

    Args:
        fgl_output: Output from 4GL execution
        python_output: Output from Python execution
        context: Validation context
        tolerance: Absolute tolerance for floating-point comparison

    Returns:
        (success, message) tuple
    """
    # Extract all numbers from outputs
    number_pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"

    fgl_numbers = [float(n) for n in re.findall(number_pattern, fgl_output)]
    python_numbers = [float(n) for n in re.findall(number_pattern, python_output)]

    if len(fgl_numbers) != len(python_numbers):
        return (
            False,
            f"Different number count: {len(fgl_numbers)} vs {len(python_numbers)}",
        )

    for i, (fgl_num, python_num) in enumerate(zip(fgl_numbers, python_numbers)):
        if abs(fgl_num - python_num) > tolerance:
            return (
                False,
                f"Number {i+1} differs: {fgl_num} vs {python_num} "
                f"(diff: {abs(fgl_num - python_num)})",
            )

    return True, f"All {len(fgl_numbers)} numbers match within tolerance"


def validate_whitespace_normalized(
    fgl_output: str, python_output: str, context: ValidationContext
) -> Tuple[bool, str]:
    """
    Validate outputs ignoring whitespace differences.

    Args:
        fgl_output: Output from 4GL execution
        python_output: Output from Python execution
        context: Validation context

    Returns:
        (success, message) tuple
    """
    normalized_fgl = Validator._normalize_output(fgl_output)
    normalized_python = Validator._normalize_output(python_output)

    if normalized_fgl == normalized_python:
        return True, "Outputs match (whitespace normalized)"
    else:
        return False, "Outputs differ even after whitespace normalization"
