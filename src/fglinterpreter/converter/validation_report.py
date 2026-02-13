"""
Validation report generation in multiple formats.

Generates comprehensive reports for validation test results.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .validator import ValidationResult


@dataclass
class ValidationReport:
    """
    Summary report of validation tests.

    Aggregates multiple ValidationResult instances and provides
    statistics and reporting capabilities.
    """

    results: List[ValidationResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_tests(self) -> int:
        """Total number of tests."""
        return len(self.results)

    @property
    def passed(self) -> int:
        """Number of passed tests."""
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        """Number of failed tests."""
        return sum(1 for r in self.results if not r.success and r.fgl_error is None)

    @property
    def errors(self) -> int:
        """Number of tests with execution errors."""
        return sum(1 for r in self.results if r.fgl_error is not None)

    @property
    def pass_rate(self) -> float:
        """Pass rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def average_execution_time_ratio(self) -> float:
        """Average Python/4GL execution time ratio."""
        if not self.results:
            return 1.0

        ratios = [r.performance_ratio for r in self.results if r.fgl_execution_time > 0]
        if not ratios:
            return 1.0

        return sum(ratios) / len(ratios)

    @property
    def total_diff_lines(self) -> int:
        """Total number of diff lines across all failed tests."""
        return sum(len(r.diff_output.splitlines()) for r in self.results if r.diff_output)

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report."""
        self.results.append(result)

    def to_text(self) -> str:
        """
        Generate text report.

        Returns:
            Formatted text report
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("Validation Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.timestamp}")
        lines.append("")

        # Summary statistics
        lines.append("Summary")
        lines.append("-" * 80)
        lines.append(f"Total Tests:  {self.total_tests}")
        lines.append(f"Passed:       {self.passed} ({self.pass_rate:.1f}%)")
        lines.append(f"Failed:       {self.failed}")
        lines.append(f"Errors:       {self.errors}")
        lines.append("")
        lines.append(
            f"Avg Performance Ratio: {self.average_execution_time_ratio:.2f}x " f"(Python/4GL)"
        )
        lines.append(f"Total Diff Lines: {self.total_diff_lines}")
        lines.append("")

        # Passed tests (summary only)
        if self.passed > 0:
            lines.append("Passed Tests")
            lines.append("-" * 80)
            for result in self.results:
                if result.success:
                    perf = result.performance_ratio
                    perf_str = f"{perf:.2f}x"
                    lines.append(
                        f"✓ {result.test_name} "
                        f"(4GL: {result.fgl_execution_time:.3f}s, "
                        f"Python: {result.python_execution_time:.3f}s, "
                        f"Ratio: {perf_str})"
                    )
            lines.append("")

        # Failed tests (detailed)
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            lines.append("Failed Tests")
            lines.append("-" * 80)

            for i, result in enumerate(failed_results, 1):
                lines.append(f"\n{i}. {result.test_name}")
                lines.append("   Status: FAILED")
                lines.append("")

                if result.fgl_error:
                    lines.append(f"   4GL Error: {result.fgl_error}")
                if result.python_error:
                    lines.append(f"   Python Error: {result.python_error}")

                if not result.outputs_match and result.diff_output:
                    lines.append("   Diff:")
                    for diff_line in result.diff_output.splitlines():
                        lines.append(f"   {diff_line}")

                if result.custom_validation_results:
                    lines.append("")
                    lines.append("   Custom Validators:")
                    for name, success in result.custom_validation_results.items():
                        status = "✓" if success else "✗"
                        message = result.custom_validation_messages.get(name, "")
                        lines.append(f"     {status} {name}: {message}")

                lines.append("")

        # Recommendations
        lines.append("Recommendations")
        lines.append("-" * 80)
        recommendations = self._generate_recommendations()
        if recommendations:
            for rec in recommendations:
                lines.append(f"• {rec}")
        else:
            lines.append("✓ All tests passed - no recommendations")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def to_json(self) -> str:
        """
        Generate JSON report.

        Returns:
            JSON-formatted report
        """
        data = {
            "timestamp": self.timestamp,
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "pass_rate": self.pass_rate,
                "average_execution_time_ratio": self.average_execution_time_ratio,
                "total_diff_lines": self.total_diff_lines,
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "fgl_execution_time": r.fgl_execution_time,
                    "python_execution_time": r.python_execution_time,
                    "performance_ratio": r.performance_ratio,
                    "outputs_match": r.outputs_match,
                    "exit_codes_match": r.exit_codes_match,
                    "fgl_error": r.fgl_error,
                    "python_error": r.python_error,
                    "diff_output": r.diff_output,
                    "custom_validation_results": r.custom_validation_results,
                    "custom_validation_messages": r.custom_validation_messages,
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations(),
        }

        return json.dumps(data, indent=2)

    def to_junit_xml(self) -> str:
        """
        Generate JUnit XML report for CI/CD integration.

        Returns:
            JUnit XML formatted report
        """
        total_time = sum(r.fgl_execution_time for r in self.results)

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(
            f'<testsuite name="4GL-Python Validation" '
            f'tests="{self.total_tests}" '
            f'failures="{self.failed}" '
            f'errors="{self.errors}" '
            f'time="{total_time:.3f}">'
        )

        for result in self.results:
            test_time = result.fgl_execution_time + result.python_execution_time

            lines.append(
                f'  <testcase name="{_xml_escape(result.test_name)}" ' f'time="{test_time:.3f}">'
            )

            if not result.success:
                if result.fgl_error or result.python_error:
                    error_msg = result.fgl_error or result.python_error
                    lines.append(f'    <error message="{_xml_escape(error_msg)}">')
                    lines.append(f"      {_xml_escape(error_msg)}")
                    lines.append("    </error>")
                elif not result.outputs_match:
                    lines.append('    <failure message="Output mismatch">')
                    lines.append(f"      {_xml_escape(result.diff_output)}")
                    lines.append("    </failure>")

            lines.append("  </testcase>")

        lines.append("</testsuite>")

        return "\n".join(lines)

    def to_html(self) -> str:
        """
        Generate interactive HTML report.

        Returns:
            HTML formatted report
        """
        # Calculate statistics for chart
        (self.failed / self.total_tests * 100) if self.total_tests else 0
        (self.errors / self.total_tests * 100) if self.total_tests else 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Report - {self.timestamp}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header .timestamp {{
            opacity: 0.9;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin-top: 10px;
        }}
        .stat-card.passed .value {{ color: #10b981; }}
        .stat-card.failed .value {{ color: #ef4444; }}
        .stat-card.errors .value {{ color: #f59e0b; }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            max-width: 400px;
        }}
        .results {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .results h2 {{
            margin-top: 0;
            color: #333;
        }}
        .result-item {{
            border-left: 4px solid #ccc;
            padding: 15px;
            margin-bottom: 15px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        .result-item.passed {{ border-left-color: #10b981; }}
        .result-item.failed {{ border-left-color: #ef4444; }}
        .result-item.error {{ border-left-color: #f59e0b; }}
        .result-item h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        .result-item .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .diff {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            margin-top: 10px;
        }}
        .diff .add {{ color: #10b981; }}
        .diff .remove {{ color: #ef4444; }}
        .recommendations {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .recommendations h2 {{
            margin-top: 0;
        }}
        .recommendations ul {{
            line-height: 2;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Validation Report</h1>
        <div class="timestamp">Generated: {self.timestamp}</div>
    </div>

    <div class="summary">
        <div class="stat-card">
            <div class="label">Total Tests</div>
            <div class="value">{self.total_tests}</div>
        </div>
        <div class="stat-card passed">
            <div class="label">Passed</div>
            <div class="value">{self.passed}</div>
        </div>
        <div class="stat-card failed">
            <div class="label">Failed</div>
            <div class="value">{self.failed}</div>
        </div>
        <div class="stat-card errors">
            <div class="label">Errors</div>
            <div class="value">{self.errors}</div>
        </div>
        <div class="stat-card">
            <div class="label">Pass Rate</div>
            <div class="value">{self.pass_rate:.1f}%</div>
        </div>
        <div class="stat-card">
            <div class="label">Avg Performance</div>
            <div class="value">{self.average_execution_time_ratio:.2f}x</div>
        </div>
    </div>

    <div class="chart-container">
        <canvas id="validationChart"></canvas>
    </div>

    <div class="results">
        <h2>Test Results</h2>
"""

        # Add passed tests (summary)
        for result in self.results:
            if result.success:
                html += f"""
        <div class="result-item passed">
            <h3>✓ {_html_escape(result.test_name)}</h3>
            <div class="meta">
                4GL: {result.fgl_execution_time:.3f}s |
                Python: {result.python_execution_time:.3f}s |
                Ratio: {result.performance_ratio:.2f}x
            </div>
        </div>
"""

        # Add failed tests (detailed)
        for result in self.results:
            if not result.success:
                status = "error" if result.fgl_error or result.python_error else "failed"
                icon = "⚠" if status == "error" else "✗"

                html += f"""
        <div class="result-item {status}">
            <h3>{icon} {_html_escape(result.test_name)}</h3>
            <div class="meta">
                4GL: {result.fgl_execution_time:.3f}s |
                Python: {result.python_execution_time:.3f}s
            </div>
"""

                if result.fgl_error:
                    html += (
                        f"<div><strong>4GL Error:</strong> {_html_escape(result.fgl_error)}</div>"
                    )
                if result.python_error:
                    html += f"<div><strong>Python Error:</strong> {_html_escape(result.python_error)}</div>"

                if result.diff_output:
                    html += '<div class="diff">'
                    for line in result.diff_output.splitlines():
                        line_escaped = _html_escape(line)
                        if line.startswith("+"):
                            html += f'<div class="add">{line_escaped}</div>'
                        elif line.startswith("-"):
                            html += f'<div class="remove">{line_escaped}</div>'
                        else:
                            html += f"<div>{line_escaped}</div>"
                    html += "</div>"

                html += "        </div>\n"

        html += """
    </div>

    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"""

        recommendations = self._generate_recommendations()
        if recommendations:
            for rec in recommendations:
                html += f"            <li>{_html_escape(rec)}</li>\n"
        else:
            html += "            <li>✓ All tests passed - no recommendations</li>\n"

        html += f"""
        </ul>
    </div>

    <script>
        const ctx = document.getElementById('validationChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Errors'],
                datasets: [{{
                    data: [{self.passed}, {self.failed}, {self.errors}],
                    backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{
                        display: true,
                        text: 'Validation Results Distribution'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

        return html

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []

        if self.errors > 0:
            recommendations.append(f"Fix {self.errors} execution error(s) in 4GL or Python code")

        if self.failed > 0:
            recommendations.append(f"Review and resolve {self.failed} output mismatch(es)")

        # Check for performance issues
        slow_tests = [r for r in self.results if r.success and r.performance_ratio > 2.0]
        if slow_tests:
            recommendations.append(
                f"Investigate {len(slow_tests)} test(s) where Python is >2x slower than 4GL"
            )

        # Check for whitespace-only differences
        whitespace_diffs = [
            r
            for r in self.results
            if not r.success and r.fgl_output.strip() == r.python_output.strip()
        ]
        if whitespace_diffs:
            recommendations.append(
                f"Consider using normalized matching for {len(whitespace_diffs)} test(s) "
                "with whitespace-only differences"
            )

        if self.pass_rate == 100:
            recommendations.append("All tests passed! Consider adding more edge case tests.")

        return recommendations


def _html_escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
