"""
Enhanced migration report generator for Story 4.5.

Provides comprehensive reporting with multiple formats (Text, JSON, Markdown, HTML),
unmapped construct tracking, and actionable recommendations.

Epic 4, Story 4.5: Migration Report Generator
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ConversionIssue:
    """Represents a warning or issue in converted code."""

    severity: str  # "warning", "error", "info"
    category: str  # "unmapped", "manual_review", "performance", "compatibility"
    message: str
    line_number: Optional[int] = None
    file_path: Optional[Path] = None
    recommendation: Optional[str] = None


def scan_for_unmapped_constructs(python_code: str) -> List[str]:
    """Scan Python code for TODO comments indicating unmapped features.

    Args:
        python_code: Generated Python code to scan

    Returns:
        List of unmapped construct descriptions
    """
    unmapped = []
    todo_pattern = re.compile(
        r"#\s*TODO:\s*(.+?)(?:not yet implemented|not implemented)", re.IGNORECASE
    )

    for line in python_code.split("\n"):
        match = todo_pattern.search(line)
        if match:
            construct = match.group(1).strip()
            unmapped.append(construct)

    return unmapped


def generate_markdown_report(report_data: Dict) -> str:
    """Generate a Markdown report from conversion data.

    Args:
        report_data: Dictionary containing conversion statistics and results

    Returns:
        Formatted Markdown report string
    """
    md = []

    # Header
    md.append("# 4GL to Python Migration Report\n")
    md.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append("---\n")

    # Executive Summary
    md.append("## Executive Summary\n")
    md.append(f"- **Source Directory**: `{report_data['source_dir']}`")
    md.append(f"- **Target Directory**: `{report_data['target_dir']}`")
    md.append(f"- **Total Files**: {report_data['total_files']}")
    md.append(
        f"- **Successfully Converted**: {report_data['successful']} ({report_data['success_rate']:.1f}%)"
    )
    md.append(f"- **Failed**: {report_data['failed']}")
    md.append(f"- **Duration**: {report_data['duration_seconds']:.2f} seconds\n")

    # Migration Readiness
    if "migration_readiness_score" in report_data:
        score = report_data["migration_readiness_score"]
        md.append("## Migration Readiness\n")
        md.append(f"**Readiness Score**: {score:.1f}/100\n")

        if score >= 90:
            md.append("✅ **Status**: Production Ready\n")
        elif score >= 70:
            md.append("⚠️ **Status**: Mostly Ready (minor fixes needed)\n")
        else:
            md.append("❌ **Status**: Needs Work\n")

        if "automated_percentage" in report_data:
            md.append(f"- **Automated**: {report_data['automated_percentage']:.1f}%")

        if "manual_review_count" in report_data:
            md.append(f"- **Manual Review Items**: {report_data['manual_review_count']}")

        if "unique_unmapped_count" in report_data:
            md.append(f"- **Unmapped Constructs**: {report_data['unique_unmapped_count']} types\n")

    # Detailed Results Table
    md.append("## Conversion Results\n")
    md.append("| File | Status | Lines | Time (s) | Warnings |\n")
    md.append("|------|--------|-------|----------|----------|\n")

    for result in report_data.get("results", []):
        status = "✅" if result["success"] else "❌"
        filename = Path(result["source_file"]).name
        lines = result.get("lines_converted", 0)
        time = result.get("execution_time", 0)
        warnings = result.get("warning_count", 0)
        md.append(f"| {filename} | {status} | {lines} | {time:.3f} | {warnings} |\n")

    # Unmapped Constructs
    if report_data.get("unmapped_constructs"):
        md.append("\n## Unmapped Constructs\n")
        md.append("The following 4GL features were encountered but not fully converted:\n\n")
        for construct, count in report_data["unmapped_constructs"].items():
            md.append(f"- **{construct}**: {count} occurrence(s)\n")
        md.append("\n⚠️ These items will need manual review and possibly custom implementation.\n")

    # Manual Review Items
    if report_data.get("manual_review_items"):
        md.append("\n## Items Requiring Manual Review\n")
        for item in report_data["manual_review_items"]:
            file_path = Path(item["file_path"]).name if item.get("file_path") else "Unknown"
            line_num = item.get("line_number", "?")
            message = item.get("message", "No details")
            md.append(f"- **{file_path}:{line_num}** - {message}\n")

    # Recommendations
    if report_data.get("recommendations"):
        md.append("\n## Recommended Next Steps\n")
        for i, rec in enumerate(report_data["recommendations"], 1):
            md.append(f"{i}. {rec}\n")

    # Circular Dependencies Warning
    if report_data.get("has_circular_dependencies"):
        md.append("\n## ⚠️ Circular Dependencies Detected\n")
        if report_data.get("circular_dependency_path"):
            cycle = " → ".join([Path(p).name for p in report_data["circular_dependency_path"]])
            md.append(f"**Dependency Cycle**: {cycle}\n")
        md.append("\nCircular dependencies should be refactored before deployment.\n")

    # Footer
    md.append("\n---\n")
    md.append(
        f"*Report generated by fglInterpreter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    )

    return "\n".join(md)


def generate_html_report(report_data: Dict) -> str:
    """Generate an interactive HTML report with charts from conversion data.

    Args:
        report_data: Dictionary containing conversion statistics and results

    Returns:
        Formatted HTML report string with embedded charts
    """
    # Calculate readiness indicator color
    score = report_data.get("migration_readiness_score", 0)
    if score >= 90:
        score_color = "#28a745"  # green
        status_text = "Production Ready"
    elif score >= 70:
        score_color = "#ffc107"  # yellow
        status_text = "Mostly Ready"
    else:
        score_color = "#dc3545"  # red
        status_text = "Needs Work"

    # Generate result rows
    result_rows = []
    for result in report_data.get("results", []):
        status_icon = "✅" if result["success"] else "❌"
        status_class = "success" if result["success"] else "failure"
        filename = Path(result["source_file"]).name
        lines = result.get("lines_converted", 0)
        time = result.get("execution_time", 0)
        warnings = result.get("warning_count", 0)
        warning_class = "warning" if warnings > 0 else ""

        result_rows.append(f"""
            <tr>
                <td>{filename}</td>
                <td class="{status_class}">{status_icon}</td>
                <td>{lines}</td>
                <td>{time:.3f}</td>
                <td class="{warning_class}">{warnings}</td>
            </tr>
        """)

    # Generate unmapped constructs section
    unmapped_section = ""
    if report_data.get("unmapped_constructs"):
        unmapped_items = []
        for construct, count in report_data["unmapped_constructs"].items():
            unmapped_items.append(f"<li><strong>{construct}</strong>: {count} occurrence(s)</li>")
        unmapped_section = f"""
        <div class="section">
            <h2>⚠️ Unmapped Constructs</h2>
            <p>The following 4GL features were encountered but not fully converted:</p>
            <ul>
                {"".join(unmapped_items)}
            </ul>
            <p class="warning">These items will need manual review and possibly custom implementation.</p>
        </div>
        """

    # Generate recommendations section
    recommendations_section = ""
    if report_data.get("recommendations"):
        rec_items = []
        for _i, rec in enumerate(report_data["recommendations"], 1):
            rec_items.append(f"<li>{rec}</li>")
        recommendations_section = f"""
        <div class="section">
            <h2>📋 Recommended Next Steps</h2>
            <ol class="recommendations">
                {"".join(rec_items)}
            </ol>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4GL to Python Migration Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .timestamp {{ opacity: 0.9; font-size: 0.9em; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}
        .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .readiness {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        .readiness-score {{
            font-size: 4em;
            font-weight: bold;
            color: {score_color};
            margin: 20px 0;
        }}
        .readiness-status {{
            font-size: 1.5em;
            color: {score_color};
            font-weight: 600;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        h2 {{ color: #333; margin-bottom: 20px; font-size: 1.8em; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        tbody tr:hover {{ background: #f8f9fa; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .failure {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 30px auto;
            max-width: 600px;
        }}
        .recommendations {{ padding-left: 20px; }}
        .recommendations li {{ margin: 10px 0; font-size: 1.1em; }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        ul {{ padding-left: 20px; }}
        ul li {{ margin: 8px 0; }}
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 4GL to Python Migration Report</h1>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>

        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{report_data['total_files']}</div>
                <div class="metric-label">Total Files</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['successful']}</div>
                <div class="metric-label">Successful</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['success_rate']:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['duration_seconds']:.1f}s</div>
                <div class="metric-label">Duration</div>
            </div>
        </div>

        <div class="readiness">
            <h2>Migration Readiness</h2>
            <div class="readiness-score">{score:.1f}/100</div>
            <div class="readiness-status">{status_text}</div>
        </div>

        <div class="section">
            <h2>📊 Conversion Progress</h2>
            <div class="chart-container">
                <canvas id="conversionChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>📁 Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Status</th>
                        <th>Lines</th>
                        <th>Time (s)</th>
                        <th>Warnings</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(result_rows)}
                </tbody>
            </table>
        </div>

        {unmapped_section}

        {recommendations_section}

        <footer>
            Report generated by <strong>fglInterpreter</strong> •
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </footer>
    </div>

    <script>
        // Conversion Progress Chart
        const ctx = document.getElementById('conversionChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Successful', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{report_data['successful']}, {report_data['failed']}, {report_data['skipped']}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    title: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return html


def calculate_migration_readiness_score(report_data: Dict) -> float:
    """Calculate migration readiness score (0-100).

    Args:
        report_data: Dictionary containing conversion statistics

    Returns:
        Readiness score from 0 to 100
    """
    score = 100.0

    total = report_data.get("total_files", 0)
    if total == 0:
        return 0.0

    # Deduct for failures (up to 30 points)
    failed = report_data.get("failed", 0)
    score -= (failed / total) * 30

    # Deduct for unmapped constructs (up to 20 points)
    unmapped_count = len(report_data.get("unmapped_constructs", {}))
    unmapped_penalty = min(unmapped_count * 2, 20)
    score -= unmapped_penalty

    # Deduct for manual review items (up to 20 points)
    manual_count = len(report_data.get("manual_review_items", []))
    manual_penalty = min(manual_count * 0.5, 20)
    score -= manual_penalty

    # Deduct for circular dependencies (10 points)
    if report_data.get("has_circular_dependencies", False):
        score -= 10

    return max(0.0, min(100.0, score))


def generate_recommendations(report_data: Dict) -> List[str]:
    """Generate actionable next steps for migration.

    Args:
        report_data: Dictionary containing conversion statistics

    Returns:
        List of recommendation strings
    """
    recommendations = []

    failed = report_data.get("failed", 0)
    report_data.get("total_files", 0)
    manual_count = len(report_data.get("manual_review_items", []))
    unmapped_count = len(report_data.get("unmapped_constructs", {}))
    readiness = report_data.get("migration_readiness_score", 0)

    if failed > 0:
        recommendations.append(
            f"⚠️ **Fix Conversion Failures**: {failed} file(s) failed to convert. "
            f"Review error logs and address syntax issues."
        )

    if manual_count > 10:
        recommendations.append(
            f"📋 **Manual Review Required**: {manual_count} items need manual attention. "
            f"Prioritize files with multiple warnings."
        )
    elif manual_count > 0:
        recommendations.append(f"📋 **Review {manual_count} items** that need manual attention.")

    if report_data.get("has_circular_dependencies", False):
        recommendations.append(
            "🔄 **Break Circular Dependencies**: Refactor code to eliminate dependency cycles "
            "before deployment."
        )

    if unmapped_count > 5:
        recommendations.append(
            f"🔧 **Address Unmapped Constructs**: {unmapped_count} 4GL features need custom "
            f"implementation or manual conversion."
        )
    elif unmapped_count > 0:
        recommendations.append(
            f"🔧 **Review {unmapped_count} unmapped construct(s)** for manual conversion."
        )

    # Overall status recommendation
    if readiness >= 90:
        recommendations.insert(
            0,
            "✅ **Migration Ready**: Code is production-ready! Run integration tests and "
            "deploy with confidence.",
        )
    elif readiness >= 70:
        recommendations.insert(
            0, "⚠️ **Nearly Ready**: Address critical warnings before production deployment."
        )
    else:
        recommendations.insert(
            0,
            "❌ **Significant Work Needed**: Focus on resolving conversion failures first, "
            "then address warnings.",
        )

    if not recommendations:
        recommendations.append("✅ All checks passed! Migration is complete.")

    return recommendations
