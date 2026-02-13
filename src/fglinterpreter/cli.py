"""
Command-line interface for fglInterpreter.

This module provides the main CLI entry point for the interpreter.
"""

import sys
from typing import Optional, Tuple

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="fglInterpreter")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def main(ctx: click.Context, verbose: bool, debug: bool) -> None:
    """
    fglInterpreter - A Python-based interpreter and tooling framework for Informix 4GL.

    Use --help with any command to see detailed usage information.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.pass_context
def run(ctx: click.Context, file: str, output: Optional[str]) -> None:
    """
    Execute a 4GL script file.

    Example: fgl run script.4gl
    Example: fgl run script.4gl -o output.txt
    """
    from pathlib import Path

    from .interpreter import RuntimeError as InterpreterRuntimeError
    from .interpreter import interpret_source

    try:
        # Read the source file
        source_code = Path(file).read_text()

        if ctx.obj.get("verbose"):
            click.echo(f"Executing {file}...")

        # Execute the script
        result = interpret_source(source_code, filename=file)

        # Output to file if specified
        if output:
            Path(output).write_text(result)
            click.echo(f"✓ Output written to {output}")
        # Otherwise output was already printed to console during execution

        if ctx.obj.get("verbose"):
            click.echo("\n✓ Execution completed successfully")

    except InterpreterRuntimeError as e:
        click.echo(f"❌ Runtime error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for token list")
@click.option(
    "--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format"
)
@click.pass_context
def tokenize(ctx: click.Context, file: str, output: Optional[str], format: str) -> None:
    """
    Tokenize a 4GL script and display the token stream.

    Example: fgl tokenize script.4gl
    Example: fgl tokenize script.4gl --format json -o tokens.json
    """
    from pathlib import Path

    from .lexer import Lexer, LexerError

    try:
        # Read the source file
        source_code = Path(file).read_text()

        # Create lexer and tokenize
        lexer = Lexer(source_code, filename=file)
        tokens = lexer.tokenize()

        # Format output
        if format == "json":
            import json

            token_list = [
                {
                    "type": token.type.name,
                    "value": token.value,
                    "line": token.line,
                    "column": token.column,
                    "literal": token.literal,
                }
                for token in tokens
            ]
            output_text = json.dumps(token_list, indent=2)
        else:
            # Text format
            output_lines = []
            output_lines.append(f"Tokenized {file}: {len(tokens)} tokens\n")
            output_lines.append("=" * 70)

            for token in tokens:
                if token.type.name == "EOF":
                    output_lines.append(f"\n{token.type.name:20} (end of file)")
                else:
                    line_info = f"[{token.line}:{token.column}]"
                    if token.literal is not None:
                        output_lines.append(
                            f"{token.type.name:20} {line_info:10} {token.value!r:20} -> {token.literal!r}"
                        )
                    else:
                        output_lines.append(f"{token.type.name:20} {line_info:10} {token.value!r}")

            output_text = "\n".join(output_lines)

        # Output to file or console
        if output:
            Path(output).write_text(output_text)
            click.echo(f"✓ Tokens written to {output}")
        else:
            click.echo(output_text)

        if ctx.obj.get("verbose"):
            click.echo(f"\n✓ Successfully tokenized {len(tokens)} tokens")

    except LexerError as e:
        click.echo(f"❌ Lexical error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output Python file")
@click.option("--no-format", is_flag=True, help="Skip code formatting with black")
@click.option("--line-length", type=int, default=88, help="Maximum line length for formatting")
@click.option(
    "--sql-backend",
    type=click.Choice(["wbjdbc", "wborm"]),
    default="wbjdbc",
    help="SQL backend to use (wbjdbc or wborm)",
)
@click.pass_context
def convert(
    ctx: click.Context,
    file: str,
    output: Optional[str],
    no_format: bool,
    line_length: int,
    sql_backend: str,
) -> None:
    """
    Convert a 4GL script to Python.

    Example: fgl convert script.4gl -o script.py
    Example: fgl convert script.4gl -o script.py --no-format
    Example: fgl convert script.4gl -o script.py --sql-backend wborm
    """
    from pathlib import Path

    from .converter import convert_source
    from .lexer import LexerError
    from .parser import ParserError

    try:
        # Read the source file
        source_code = Path(file).read_text()

        if ctx.obj.get("verbose"):
            click.echo(f"Converting {file} to Python...")

        # Convert the script
        python_code = convert_source(
            source_code,
            filename=file,
            format_code=not no_format,
            line_length=line_length,
            sql_backend=sql_backend,
        )

        # Output to file or console
        if output:
            Path(output).write_text(python_code)
            click.echo(f"✓ Python code written to {output}")
        else:
            # Default output filename: replace .4gl with .py
            default_output = str(Path(file).with_suffix(".py"))
            Path(default_output).write_text(python_code)
            click.echo(f"✓ Python code written to {default_output}")

        if ctx.obj.get("verbose"):
            click.echo("\n✓ Conversion completed successfully")

    except LexerError as e:
        click.echo(f"❌ Lexical error: {e}", err=True)
        sys.exit(1)
    except ParserError as e:
        click.echo(f"❌ Parse error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for AST")
@click.option(
    "--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format"
)
@click.pass_context
def parse(ctx: click.Context, file: str, output: Optional[str], format: str) -> None:
    """
    Parse a 4GL script and display the AST.

    Example: fgl parse script.4gl
    Example: fgl parse script.4gl --format json -o ast.json
    """
    from pathlib import Path

    from .parser import ParserError, parse_source

    try:
        # Read the source file
        source_code = Path(file).read_text()

        # Parse the source code
        ast = parse_source(source_code, filename=file)

        # Format output
        if format == "json":
            import json

            ast_dict = ast.to_dict()
            output_text = json.dumps(ast_dict, indent=2)
        else:
            # Text format (simplified tree view)
            output_lines = []
            output_lines.append(f"Parsed {file} successfully\n")
            output_lines.append("=" * 70)
            output_lines.append("\nProgram:")
            output_lines.append(f"  Functions: {len(ast.functions)}")
            for func in ast.functions:
                output_lines.append(
                    f"    - {func.name}({', '.join(p.name for p in func.parameters)})"
                )
                output_lines.append(f"      Body: {len(func.body)} statements")

            if ast.main_block:
                output_lines.append("  Main Block:")
                output_lines.append(f"    Statements: {len(ast.main_block.body)}")
                for i, stmt in enumerate(ast.main_block.body, 1):
                    output_lines.append(f"      {i}. {stmt.__class__.__name__} (line {stmt.line})")

            output_text = "\n".join(output_lines)

        # Output to file or console
        if output:
            Path(output).write_text(output_text)
            click.echo(f"✓ AST written to {output}")
        else:
            click.echo(output_text)

        if ctx.obj.get("verbose"):
            click.echo(f"\n✓ Successfully parsed {file}")

    except ParserError as e:
        click.echo(f"❌ Parse error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("target_dir", type=click.Path(file_okay=False, dir_okay=True))
@click.option("--recursive/--no-recursive", default=True, help="Recursively convert subdirectories")
@click.option("--overwrite", is_flag=True, help="Overwrite existing .py files")
@click.option("--no-format", is_flag=True, help="Skip code formatting with black")
@click.option("--line-length", type=int, default=88, help="Maximum line length for formatting")
@click.option(
    "--resolve-dependencies", is_flag=True, help="Resolve dependencies and convert in order"
)
@click.option(
    "--sql-backend",
    type=click.Choice(["wbjdbc", "wborm"]),
    default="wbjdbc",
    help="SQL backend to use (wbjdbc or wborm)",
)
@click.option(
    "--report",
    "-r",
    type=click.Path(),
    help="Save conversion report to file",
)
@click.option(
    "--report-format",
    type=click.Choice(["text", "json", "markdown", "html"]),
    default="text",
    help="Report format (text, json, markdown, html)",
)
@click.pass_context
def batch_convert(
    ctx: click.Context,
    source_dir: str,
    target_dir: str,
    recursive: bool,
    overwrite: bool,
    no_format: bool,
    line_length: int,
    resolve_dependencies: bool,
    sql_backend: str,
    report: Optional[str],
    report_format: str,
) -> None:
    """
    Batch convert a directory of 4GL files to Python.

    Converts all .4gl files in SOURCE_DIR to .py files in TARGET_DIR,
    preserving the directory structure.

    Example: fgl batch-convert src/4gl src/python
    Example: fgl batch-convert src/4gl src/python --recursive --overwrite
    Example: fgl batch-convert src/4gl src/python --resolve-dependencies
    Example: fgl batch-convert src/4gl src/python --sql-backend wborm
    Example: fgl batch-convert src/4gl src/python -r report.txt
    Example: fgl batch-convert src/4gl src/python -r report.md --report-format markdown
    Example: fgl batch-convert src/4gl src/python -r report.html --report-format html
    """

    from .converter import convert_directory

    try:
        if ctx.obj.get("verbose"):
            click.echo(f"Batch converting {source_dir} to {target_dir}...")
            click.echo(f"Recursive: {recursive}")
            click.echo(f"Overwrite: {overwrite}")
            click.echo(f"SQL Backend: {sql_backend}")
            click.echo("")

        # Perform batch conversion
        batch_report = convert_directory(
            source_dir=source_dir,
            target_dir=target_dir,
            recursive=recursive,
            format_code=not no_format,
            line_length=line_length,
            overwrite=overwrite,
            sql_backend=sql_backend,
            resolve_dependencies=resolve_dependencies,
            report_file=report,
            report_format=report_format,
        )

        # Display summary
        click.echo("Batch Conversion Complete!")
        click.echo("")

        # Warn about circular dependencies if detected
        if batch_report.has_circular_dependencies and batch_report.circular_dependency_path:
            cycle_str = " -> ".join(str(p.name) for p in batch_report.circular_dependency_path)
            click.echo(f"⚠️  Warning: Circular dependencies detected: {cycle_str}", err=True)
            click.echo("")

        click.echo(f"Total Files: {batch_report.total_files}")
        click.echo(f"✓ Successful: {batch_report.successful} ({batch_report.success_rate:.1f}%)")
        if batch_report.failed > 0:
            click.echo(f"✗ Failed: {batch_report.failed}", err=True)
        if batch_report.skipped > 0:
            click.echo(f"⊘ Skipped: {batch_report.skipped}")
        click.echo(f"Duration: {batch_report.duration:.2f}s")
        click.echo("")

        # Show failed files
        if batch_report.failed > 0:
            click.echo("Failed conversions:")
            for result in batch_report.results:
                if not result.success and result.error_type != "FileExists":
                    click.echo(f"  ✗ {result.source_file.name}: {result.error_type}", err=True)
            click.echo("")

        # Show report file location
        if report:
            click.echo(f"Full report saved to: {report}")

        # Exit with error code if any conversions failed
        if batch_report.failed > 0:
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except NotADirectoryError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("source_4gl", type=click.Path(exists=True))
@click.argument("converted_python", type=click.Path(exists=True))
@click.option(
    "--validation-mode",
    type=click.Choice(["exact", "normalized", "semantic"]),
    default="exact",
    help="Validation matching mode",
)
@click.option(
    "--diff-format",
    type=click.Choice(["unified", "side-by-side", "html"]),
    default="unified",
    help="Diff report format",
)
@click.option(
    "--custom-validator",
    multiple=True,
    help="Custom validator to run (can be specified multiple times)",
)
@click.option("--timeout", type=int, default=30, help="Execution timeout in seconds")
@click.pass_context
def validate(
    ctx: click.Context,
    source_4gl: str,
    converted_python: str,
    validation_mode: str,
    diff_format: str,
    custom_validator: Tuple[str, ...],
    timeout: int,
) -> None:
    """
    Validate converted Python against original 4GL.

    Executes both the 4GL source (through the interpreter) and the
    converted Python code, then compares their outputs to ensure
    conversion fidelity.

    Example: fgl validate source.4gl converted.py
    Example: fgl validate source.4gl converted.py --validation-mode normalized
    Example: fgl validate source.4gl converted.py --custom-validator numeric_tolerance
    Example: fgl validate source.4gl converted.py --diff-format html
    """
    from pathlib import Path

    from .converter.validator import DiffReporter, ValidationContext, Validator

    try:
        # Read source files
        source_4gl_code = Path(source_4gl).read_text()
        converted_python_code = Path(converted_python).read_text()

        if ctx.obj.get("verbose"):
            click.echo(f"Validating: {source_4gl} → {converted_python}")
            click.echo(f"Mode: {validation_mode}")
            click.echo("")

        # Create validation context
        context = ValidationContext(
            source_4gl=source_4gl_code,
            source_python=converted_python_code,
            test_name=Path(source_4gl).stem,
            validation_mode=validation_mode,
            custom_validators=list(custom_validator),
            timeout=timeout,
        )

        # Run validation
        validator = Validator()
        result = validator.validate(context)

        # Display result
        if result.success:
            click.echo(f"✓ Validation PASSED: {Path(source_4gl).name}")
            click.echo("")
            click.echo(f"  4GL execution:    {result.fgl_execution_time:.3f}s")
            click.echo(f"  Python execution: {result.python_execution_time:.3f}s")
            click.echo(f"  Performance ratio: {result.performance_ratio:.2f}x")
            click.echo("  Outputs match: Yes")
            click.echo("  Exit codes match: Yes")

            if result.custom_validation_results:
                click.echo("")
                click.echo("  Custom validators:")
                for name, success in result.custom_validation_results.items():
                    status = "✓" if success else "✗"
                    message = result.custom_validation_messages.get(name, "")
                    click.echo(f"    {status} {name}: {message}")

        else:
            click.echo(f"✗ Validation FAILED: {Path(source_4gl).name}", err=True)
            click.echo("")

            if result.fgl_error:
                click.echo(f"  4GL error: {result.fgl_error}", err=True)
            if result.python_error:
                click.echo(f"  Python error: {result.python_error}", err=True)

            if not result.outputs_match:
                click.echo("  Outputs match: No", err=True)

                # Generate and display diff
                if diff_format == "unified":
                    diff = result.diff_output
                elif diff_format == "side-by-side":
                    diff = DiffReporter.side_by_side_diff(result.fgl_output, result.python_output)
                elif diff_format == "html":
                    diff = DiffReporter.html_diff(result.fgl_output, result.python_output)
                    # Save HTML to temp file and notify user
                    import tempfile

                    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                        f.write(diff)
                        click.echo(f"  HTML diff saved to: {f.name}")
                    diff = "[HTML diff saved to file]"

                click.echo("")
                click.echo("  Diff:")
                for line in diff.splitlines()[:20]:  # Limit to 20 lines
                    click.echo(f"    {line}")
                if len(diff.splitlines()) > 20:
                    click.echo(f"    ... ({len(diff.splitlines()) - 20} more lines)")

            if result.custom_validation_results:
                click.echo("")
                click.echo("  Custom validators:")
                for name, success in result.custom_validation_results.items():
                    status = "✓" if success else "✗"
                    message = result.custom_validation_messages.get(name, "")
                    click.echo(f"    {status} {name}: {message}")

            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--validation-mode",
    type=click.Choice(["exact", "normalized", "semantic"]),
    default="exact",
    help="Validation matching mode",
)
@click.option(
    "--custom-validator",
    multiple=True,
    help="Custom validator to run (can be specified multiple times)",
)
@click.option("--timeout", type=int, default=30, help="Execution timeout in seconds per test")
@click.option("--report", "-r", type=click.Path(), help="Save validation report to file")
@click.option(
    "--report-format",
    type=click.Choice(["text", "json", "html", "junit"]),
    default="text",
    help="Report format",
)
@click.option("--continue-on-failure", is_flag=True, help="Continue validation even if tests fail")
@click.pass_context
def validate_batch(
    ctx: click.Context,
    source_dir: str,
    target_dir: str,
    validation_mode: str,
    custom_validator: Tuple[str, ...],
    timeout: int,
    report: Optional[str],
    report_format: str,
    continue_on_failure: bool,
) -> None:
    """
    Validate a batch of converted Python files against original 4GL.

    Validates all .4gl/.py file pairs in the source and target directories.

    Example: fgl validate-batch src/4gl src/python
    Example: fgl validate-batch src/4gl src/python --report validation.html --report-format html
    Example: fgl validate-batch src/4gl src/python --validation-mode normalized
    Example: fgl validate-batch src/4gl src/python --custom-validator numeric_tolerance
    """
    from pathlib import Path

    from .converter.validation_report import ValidationReport
    from .converter.validator import ValidationContext, Validator

    try:
        source_path = Path(source_dir)
        target_path = Path(target_dir)

        if ctx.obj.get("verbose"):
            click.echo(f"Batch validation: {source_dir} → {target_dir}")
            click.echo(f"Mode: {validation_mode}")
            click.echo("")

        # Find all .4gl files and their corresponding .py files
        source_files = list(source_path.rglob("*.4gl"))

        if not source_files:
            click.echo(f"No .4gl files found in {source_dir}")
            sys.exit(1)

        click.echo(f"Found {len(source_files)} 4GL file(s) to validate")
        click.echo("")

        # Create validator and report
        validator = Validator()
        validation_report = ValidationReport()

        # Validate each file pair
        for source_file in source_files:
            # Determine corresponding Python file
            relative_path = source_file.relative_to(source_path)
            python_file = target_path / relative_path.with_suffix(".py")

            if not python_file.exists():
                click.echo(f"⊘ Skipped: {source_file.name} (no corresponding .py file)", err=True)
                continue

            # Read files
            source_4gl_code = source_file.read_text()
            converted_python_code = python_file.read_text()

            # Create context and validate
            context = ValidationContext(
                source_4gl=source_4gl_code,
                source_python=converted_python_code,
                test_name=source_file.stem,
                validation_mode=validation_mode,
                custom_validators=list(custom_validator),
                timeout=timeout,
            )

            result = validator.validate(context)
            validation_report.add_result(result)

            # Display result
            if result.success:
                click.echo(
                    f"✓ {source_file.name} ({result.fgl_execution_time:.3f}s / {result.python_execution_time:.3f}s)"
                )
            else:
                click.echo(f"✗ {source_file.name} - FAILED", err=True)
                if not continue_on_failure:
                    click.echo("")
                    click.echo("Stopping validation (use --continue-on-failure to continue)")
                    break

        # Display summary
        click.echo("")
        click.echo("=" * 60)
        click.echo("Validation Summary")
        click.echo("=" * 60)
        click.echo(f"Total Tests:  {validation_report.total_tests}")
        click.echo(f"Passed:       {validation_report.passed} ({validation_report.pass_rate:.1f}%)")
        click.echo(f"Failed:       {validation_report.failed}")
        click.echo(f"Errors:       {validation_report.errors}")
        click.echo(f"Avg Performance: {validation_report.average_execution_time_ratio:.2f}x")
        click.echo("")

        # Save report if requested
        if report:
            if report_format == "text":
                report_content = validation_report.to_text()
            elif report_format == "json":
                report_content = validation_report.to_json()
            elif report_format == "html":
                report_content = validation_report.to_html()
            elif report_format == "junit":
                report_content = validation_report.to_junit_xml()

            Path(report).write_text(report_content)
            click.echo(f"Full report saved to: {report}")
            click.echo("")

        # Exit with error if any validations failed
        if validation_report.failed > 0 or validation_report.errors > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--target", "-t", help="Target executable name (defaults to file/dir name)")
@click.option("--make-executable", default="4make", help="Path to 4make executable")
@click.option(
    "--library-path",
    default="/test/QX/src/lib/libs_final.a",
    help="Path to library file to link",
)
@click.option("--keep-temp-files", is_flag=True, help="Keep temporary files after compilation")
@click.option("--show-warnings", is_flag=True, help="Show warnings in addition to errors")
@click.pass_context
def compile(
    ctx: click.Context,
    file: str,
    target: Optional[str],
    make_executable: str,
    library_path: str,
    keep_temp_files: bool,
    show_warnings: bool,
) -> None:
    """
    Compile a 4GL file or directory using 4make.

    Generates 4make.def, executes 4make, and displays compilation errors and warnings.

    Examples:
        fgl compile script.4gl
        fgl compile /path/to/project --target myprogram
        fgl compile script.4gl --show-warnings
    """
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax

    from .compiler import (
        CompilationError,
        CompilerNotFoundError,
        FourMakeCompiler,
    )

    console = Console()

    try:
        # Initialize compiler
        try:
            compiler = FourMakeCompiler(
                make_executable=make_executable,
                library_path=library_path,
                keep_temp_files=keep_temp_files,
            )
        except CompilerNotFoundError as e:
            console.print(f"[red]❌ {e}[/red]")
            console.print(
                "\n[yellow]💡 Suggestion:[/yellow] Ensure 4make is installed and in your PATH"
            )
            sys.exit(1)

        file_path = Path(file)

        if ctx.obj.get("verbose"):
            console.print(f"[blue]Compiling {file}...[/blue]")

        # Compile file or directory
        if file_path.is_dir():
            result = compiler.compile_directory(file_path, target_name=target)
        else:
            result = compiler.compile_file(file_path, target_name=target)

        # Display results
        if result.errors:
            console.print("\n[red bold]❌ Compilation Errors:[/red bold]")
            console.print("=" * 60)
            for error in result.errors:
                location = f"{error.file}"
                if error.line:
                    location += f":{error.line}"
                    if error.column:
                        location += f":{error.column}"

                console.print(f"\n[red]❌ {location}[/red]")
                if error.code:
                    console.print(f"   [dim]Error Code:[/dim] {error.code}")
                console.print(f"   {error.message}")
                if error.suggestion:
                    console.print(f"   [yellow]💡 Suggestion:[/yellow] {error.suggestion}")

        if show_warnings and result.warnings:
            console.print("\n[yellow bold]⚠️  Warnings:[/yellow bold]")
            console.print("=" * 60)
            for warning in result.warnings:
                location = f"{warning.file}"
                if warning.line:
                    location += f":{warning.line}"
                    if warning.column:
                        location += f":{warning.column}"

                console.print(f"\n[yellow]⚠️  {location}[/yellow]")
                if warning.code:
                    console.print(f"   [dim]Warning Code:[/dim] {warning.code}")
                console.print(f"   {warning.message}")
                if warning.suggestion:
                    console.print(f"   [yellow]💡 Suggestion:[/yellow] {warning.suggestion}")

        # Display summary
        console.print("\n" + "=" * 60)
        if result.success:
            console.print("[green bold]✅ Compilation successful![/green bold]")
            console.print(f"   Target: {result.target}")
            console.print(f"   Time: {result.compilation_time:.2f}s")
            if result.warning_count > 0:
                console.print(f"   Warnings: {result.warning_count}")
        else:
            console.print("[red bold]❌ Compilation failed[/red bold]")
            console.print(f"   Errors: {result.error_count}")
            if result.warning_count > 0:
                console.print(f"   Warnings: {result.warning_count}")

        if ctx.obj.get("verbose") and result.make_def_content:
            console.print("\n[blue]Generated 4make.def:[/blue]")
            syntax = Syntax(result.make_def_content, "makefile", theme="monokai")
            console.print(Panel(syntax, title="4make.def", border_style="blue"))

        # Exit with error code if compilation failed
        if not result.success:
            sys.exit(1)

    except CompilationError as e:
        console.print(f"[red]❌ Compilation error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if ctx.obj.get("debug"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command()
def info() -> None:
    """
    Display information about fglInterpreter.
    """
    click.echo(f"fglInterpreter version {__version__}")
    click.echo("")
    click.echo("A Python-based interpreter and tooling framework for Informix 4GL")
    click.echo("")
    click.echo("Status:")
    click.echo("  ✅ Story 1.1: Project Infrastructure & Setup - COMPLETE")
    click.echo("  ✅ Story 1.2: Lexer & Tokenizer - COMPLETE")
    click.echo("  ✅ Story 1.3: Parser & AST Construction - COMPLETE")
    click.echo("  ✅ Story 1.4: Interpreter Execution Engine - COMPLETE")
    click.echo("  ✅ Story 1.5: Conversion Layer - COMPLETE")
    click.echo("  🚧 Story 4.2: Batch Conversion Tool - IN PROGRESS")
    click.echo("")
    click.echo("For more information: https://github.com/wanderbatistaf/fglInterpreter")


if __name__ == "__main__":
    sys.exit(main())
