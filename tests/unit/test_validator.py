"""
Unit tests for the validation framework.

Tests the validator, diff reporting, and custom validators.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.fglinterpreter.converter.validation_report import ValidationReport
from src.fglinterpreter.converter.validator import (
    CustomValidatorRegistry,
    DiffReporter,
    ValidationContext,
    ValidationResult,
    Validator,
    validate_numeric_output,
    validate_whitespace_normalized,
)


class TestValidationContext:
    """Test ValidationContext dataclass."""

    def test_context_creation(self):
        """Test creating a validation context."""
        context = ValidationContext(
            source_4gl="MAIN\n  DISPLAY 'Hello'\nEND MAIN",
            source_python="def main():\n    print('Hello')",
            test_name="test_hello",
        )

        assert context.test_name == "test_hello"
        assert "DISPLAY" in context.source_4gl
        assert "print" in context.source_python
        assert context.timeout == 30
        assert context.validation_mode == "exact"

    def test_context_with_custom_validators(self):
        """Test context with custom validators."""
        context = ValidationContext(
            source_4gl="code",
            source_python="code",
            test_name="test",
            custom_validators=["numeric_tolerance", "whitespace_normalized"],
        )

        assert len(context.custom_validators) == 2
        assert "numeric_tolerance" in context.custom_validators

    def test_context_with_timeout(self):
        """Test context with custom timeout."""
        context = ValidationContext(
            source_4gl="code",
            source_python="code",
            test_name="test",
            timeout=60,
        )

        assert context.timeout == 60


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(test_name="test", success=True)

        assert result.test_name == "test"
        assert result.success
        assert result.fgl_output == ""
        assert result.python_output == ""

    def test_performance_ratio(self):
        """Test performance ratio calculation."""
        result = ValidationResult(
            test_name="test",
            success=True,
            fgl_execution_time=1.0,
            python_execution_time=0.5,
        )

        assert result.performance_ratio == 0.5

    def test_performance_ratio_zero_division(self):
        """Test performance ratio with zero 4GL time."""
        result = ValidationResult(
            test_name="test",
            success=True,
            fgl_execution_time=0.0,
            python_execution_time=0.5,
        )

        assert result.performance_ratio == 1.0

    def test_result_string_representation(self):
        """Test string representation of result."""
        result = ValidationResult(
            test_name="test_example",
            success=True,
            fgl_execution_time=0.1,
            python_execution_time=0.05,
        )

        result_str = str(result)
        assert "test_example" in result_str
        assert "PASSED" in result_str
        assert "0.100s" in result_str


class TestDiffReporter:
    """Test DiffReporter class."""

    def test_unified_diff(self):
        """Test unified diff generation."""
        fgl_output = "Hello World\nLine 2\nLine 3"
        python_output = "Hello World\nLine 2 Modified\nLine 3"

        diff = DiffReporter.unified_diff(fgl_output, python_output)

        assert "---" in diff or "+++" in diff or len(diff) > 0
        # Empty diff if outputs are same, non-empty if different

    def test_unified_diff_identical_outputs(self):
        """Test unified diff with identical outputs."""
        output = "Hello World\nLine 2"

        diff = DiffReporter.unified_diff(output, output)

        # Identical outputs should produce empty diff
        assert diff == "" or len(diff.strip()) == 0

    def test_side_by_side_diff(self):
        """Test side-by-side diff generation."""
        fgl_output = "Hello"
        python_output = "Hola"

        diff = DiffReporter.side_by_side_diff(fgl_output, python_output)

        assert "4GL Output" in diff
        assert "Python Output" in diff
        assert "Hello" in diff
        assert "Hola" in diff

    def test_side_by_side_diff_different_lengths(self):
        """Test side-by-side diff with different line counts."""
        fgl_output = "Line 1\nLine 2"
        python_output = "Line 1"

        diff = DiffReporter.side_by_side_diff(fgl_output, python_output)

        assert "Line 1" in diff
        # Should handle different lengths

    def test_html_diff(self):
        """Test HTML diff generation."""
        fgl_output = "Hello\nWorld"
        python_output = "Hello\nPython"

        html = DiffReporter.html_diff(fgl_output, python_output)

        assert "<" in html  # HTML tags
        assert ">" in html
        assert "Hello" in html


class TestCustomValidatorRegistry:
    """Test CustomValidatorRegistry class."""

    def test_registry_initialization(self):
        """Test registry initializes with built-in validators."""
        registry = CustomValidatorRegistry()

        validators = registry.list_validators()
        assert "numeric_tolerance" in validators
        assert "whitespace_normalized" in validators

    def test_register_custom_validator(self):
        """Test registering a custom validator."""
        registry = CustomValidatorRegistry()

        def custom_validator(fgl, python, context):
            return True, "Custom validation passed"

        registry.register("custom_test", custom_validator)

        assert "custom_test" in registry.list_validators()

    def test_run_validator_success(self):
        """Test running a validator that succeeds."""
        registry = CustomValidatorRegistry()
        context = ValidationContext("", "", "test")

        success, message = registry.run("whitespace_normalized", "Hello", "Hello", context)

        assert success
        assert "match" in message.lower()

    def test_run_validator_failure(self):
        """Test running a validator that fails."""
        registry = CustomValidatorRegistry()
        context = ValidationContext("", "", "test")

        success, message = registry.run("whitespace_normalized", "Hello", "Goodbye", context)

        assert not success

    def test_run_unknown_validator(self):
        """Test running an unknown validator."""
        registry = CustomValidatorRegistry()
        context = ValidationContext("", "", "test")

        success, message = registry.run("unknown_validator", "", "", context)

        assert not success
        assert "Unknown validator" in message

    def test_run_validator_with_exception(self):
        """Test validator that raises an exception."""
        registry = CustomValidatorRegistry()

        def buggy_validator(fgl, python, context):
            raise ValueError("Test error")

        registry.register("buggy", buggy_validator)
        context = ValidationContext("", "", "test")

        success, message = registry.run("buggy", "", "", context)

        assert not success
        assert "error" in message.lower()


class TestValidator:
    """Test Validator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = Validator()

        assert validator.interpreter is not None
        assert validator.custom_validators is not None

    def test_exact_match_same_outputs(self):
        """Test exact match with identical outputs."""
        validator = Validator()

        assert validator._exact_match("Hello World", "Hello World")
        assert validator._exact_match("Hello", "Hello  ")  # Strips whitespace

    def test_exact_match_different_outputs(self):
        """Test exact match with different outputs."""
        validator = Validator()

        assert not validator._exact_match("Hello", "Goodbye")
        assert not validator._exact_match("Hello\n", "Hello World\n")

    def test_normalized_match_same_content(self):
        """Test normalized match with whitespace differences."""
        validator = Validator()

        assert validator._normalized_match("Hello  World", "Hello World")
        assert validator._normalized_match("Hello\r\nWorld", "Hello\nWorld")
        assert validator._normalized_match("Hello   ", "Hello")

    def test_normalized_match_different_content(self):
        """Test normalized match with different content."""
        validator = Validator()

        assert not validator._normalized_match("Hello", "Goodbye")

    def test_semantic_match_json(self):
        """Test semantic match with JSON data."""
        validator = Validator()

        json1 = '{"name": "John", "age": 30}'
        json2 = '{"age": 30, "name": "John"}'  # Different order, same content

        assert validator._semantic_match(json1, json2)

    def test_semantic_match_non_json_fallback(self):
        """Test semantic match falls back to normalized for non-JSON."""
        validator = Validator()

        # Non-JSON should fall back to normalized matching
        assert validator._semantic_match("Hello  World", "Hello World")

    def test_normalize_output(self):
        """Test output normalization."""
        normalized = Validator._normalize_output("Hello   World  \r\n  ")

        assert normalized == "Hello World"
        assert "\r\n" not in normalized
        assert normalized.count(" ") == 1  # Collapsed multiple spaces

    def test_validate_simple_success(self):
        """Test validation of simple matching code."""
        validator = Validator()

        # Simple 4GL and Python that produce same output
        context = ValidationContext(
            source_4gl='MAIN\n  DISPLAY "Hello"\nEND MAIN',
            source_python='def main():\n    print("Hello")\n\nif __name__ == "__main__":\n    main()',
            test_name="test_simple",
        )

        with patch.object(validator, "_execute_4gl", return_value=("Hello\n", 0, None)):
            with patch.object(validator, "_execute_python", return_value=("Hello\n", 0, None)):
                result = validator.validate(context)

                assert result.success
                assert result.outputs_match
                assert result.exit_codes_match

    def test_validate_output_mismatch(self):
        """Test validation with output mismatch."""
        validator = Validator()

        context = ValidationContext(
            source_4gl='MAIN\n  DISPLAY "Hello"\nEND MAIN',
            source_python='print("Goodbye")',
            test_name="test_mismatch",
        )

        with patch.object(validator, "_execute_4gl", return_value=("Hello\n", 0, None)):
            with patch.object(validator, "_execute_python", return_value=("Goodbye\n", 0, None)):
                result = validator.validate(context)

                assert not result.success
                assert not result.outputs_match
                assert result.diff_output  # Should have diff

    def test_validate_with_4gl_error(self):
        """Test validation when 4GL execution fails."""
        validator = Validator()

        context = ValidationContext(
            source_4gl="INVALID 4GL CODE",
            source_python='print("Hello")',
            test_name="test_4gl_error",
        )

        with patch.object(validator, "_execute_4gl", return_value=("", 1, "Syntax error")):
            with patch.object(validator, "_execute_python", return_value=("Hello\n", 0, None)):
                result = validator.validate(context)

                assert not result.success
                assert result.fgl_error == "Syntax error"

    def test_validate_with_python_error(self):
        """Test validation when Python execution fails."""
        validator = Validator()

        context = ValidationContext(
            source_4gl='MAIN\n  DISPLAY "Hello"\nEND MAIN',
            source_python="invalid python code",
            test_name="test_python_error",
        )

        with patch.object(validator, "_execute_4gl", return_value=("Hello\n", 0, None)):
            with patch.object(validator, "_execute_python", return_value=("", 1, "SyntaxError")):
                result = validator.validate(context)

                assert not result.success
                assert result.python_error == "SyntaxError"

    def test_validate_with_custom_validator(self):
        """Test validation with custom validators."""
        validator = Validator()

        context = ValidationContext(
            source_4gl="code",
            source_python="code",
            test_name="test",
            custom_validators=["whitespace_normalized"],
        )

        with patch.object(validator, "_execute_4gl", return_value=("123", 0, None)):
            with patch.object(validator, "_execute_python", return_value=("123  ", 0, None)):
                result = validator.validate(context)

                assert result.success
                assert "whitespace_normalized" in result.custom_validation_results
                assert result.custom_validation_results["whitespace_normalized"]

    def test_validate_normalized_mode(self):
        """Test validation with normalized mode."""
        validator = Validator()

        context = ValidationContext(
            source_4gl="code",
            source_python="code",
            test_name="test",
            validation_mode="normalized",
        )

        with patch.object(validator, "_execute_4gl", return_value=("Hello  World", 0, None)):
            with patch.object(validator, "_execute_python", return_value=("Hello World", 0, None)):
                result = validator.validate(context)

                assert result.success
                assert result.outputs_match

    def test_validate_semantic_mode(self):
        """Test validation with semantic mode."""
        validator = Validator()

        context = ValidationContext(
            source_4gl="code",
            source_python="code",
            test_name="test",
            validation_mode="semantic",
        )

        json1 = '{"name": "John"}'
        json2 = '{ "name" : "John" }'  # Different formatting

        with patch.object(validator, "_execute_4gl", return_value=(json1, 0, None)):
            with patch.object(validator, "_execute_python", return_value=(json2, 0, None)):
                result = validator.validate(context)

                assert result.success
                assert result.outputs_match


class TestBuiltInValidators:
    """Test built-in custom validators."""

    def test_numeric_tolerance_exact_match(self):
        """Test numeric validator with exact match."""
        context = ValidationContext("", "", "test")

        success, message = validate_numeric_output("Result: 123.456", "Result: 123.456", context)

        assert success
        assert "match" in message.lower()

    def test_numeric_tolerance_within_tolerance(self):
        """Test numeric validator within tolerance."""
        context = ValidationContext("", "", "test")

        success, message = validate_numeric_output(
            "Result: 123.456789",
            "Result: 123.456790",
            context,
            tolerance=0.001,
        )

        assert success

    def test_numeric_tolerance_exceeds_tolerance(self):
        """Test numeric validator exceeds tolerance."""
        context = ValidationContext("", "", "test")

        success, message = validate_numeric_output(
            "Result: 123.456", "Result: 125.456", context, tolerance=0.01
        )

        assert not success
        assert "differs" in message.lower()

    def test_numeric_tolerance_different_count(self):
        """Test numeric validator with different number count."""
        context = ValidationContext("", "", "test")

        success, message = validate_numeric_output("Numbers: 1 2 3", "Numbers: 1 2", context)

        assert not success
        assert "count" in message.lower()

    def test_whitespace_normalized_match(self):
        """Test whitespace normalized validator with match."""
        context = ValidationContext("", "", "test")

        success, message = validate_whitespace_normalized("Hello  World  ", "Hello World", context)

        assert success
        assert "match" in message.lower()

    def test_whitespace_normalized_no_match(self):
        """Test whitespace normalized validator with no match."""
        context = ValidationContext("", "", "test")

        success, message = validate_whitespace_normalized("Hello World", "Goodbye World", context)

        assert not success


class TestValidationReport:
    """Test ValidationReport class."""

    def test_report_initialization(self):
        """Test report initialization."""
        report = ValidationReport()

        assert report.total_tests == 0
        assert report.passed == 0
        assert report.failed == 0

    def test_add_result(self):
        """Test adding results to report."""
        report = ValidationReport()

        result1 = ValidationResult(test_name="test1", success=True)
        result2 = ValidationResult(test_name="test2", success=False)

        report.add_result(result1)
        report.add_result(result2)

        assert report.total_tests == 2
        assert report.passed == 1
        assert report.failed == 1

    def test_pass_rate(self):
        """Test pass rate calculation."""
        report = ValidationReport()

        report.add_result(ValidationResult("test1", True))
        report.add_result(ValidationResult("test2", True))
        report.add_result(ValidationResult("test3", False))

        assert report.pass_rate == pytest.approx(66.67, rel=0.1)

    def test_pass_rate_zero_tests(self):
        """Test pass rate with zero tests."""
        report = ValidationReport()

        assert report.pass_rate == 0.0

    def test_average_execution_time_ratio(self):
        """Test average execution time ratio."""
        report = ValidationReport()

        result1 = ValidationResult("test1", True, fgl_execution_time=1.0, python_execution_time=0.5)
        result2 = ValidationResult("test2", True, fgl_execution_time=2.0, python_execution_time=1.5)

        report.add_result(result1)
        report.add_result(result2)

        # Average of 0.5 and 0.75
        assert report.average_execution_time_ratio == pytest.approx(0.625, rel=0.01)

    def test_to_text(self):
        """Test text report generation."""
        report = ValidationReport()

        report.add_result(ValidationResult("test1", True))
        report.add_result(ValidationResult("test2", False))

        text = report.to_text()

        assert "Validation Report" in text
        assert "Total Tests" in text
        assert "Passed" in text
        assert "Failed" in text

    def test_to_json(self):
        """Test JSON report generation."""
        import json

        report = ValidationReport()
        report.add_result(ValidationResult("test1", True))

        json_str = report.to_json()
        data = json.loads(json_str)

        assert "summary" in data
        assert "results" in data
        assert data["summary"]["total_tests"] == 1

    def test_to_junit_xml(self):
        """Test JUnit XML report generation."""
        report = ValidationReport()

        report.add_result(ValidationResult("test1", True))
        report.add_result(ValidationResult("test2", False))

        xml = report.to_junit_xml()

        assert "<?xml version" in xml
        assert "<testsuite" in xml
        assert "<testcase" in xml

    def test_to_html(self):
        """Test HTML report generation."""
        report = ValidationReport()

        report.add_result(ValidationResult("test1", True))
        report.add_result(ValidationResult("test2", False))

        html = report.to_html()

        assert "<!DOCTYPE html>" in html
        assert "Validation Report" in html
        assert "test1" in html
        assert "test2" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
