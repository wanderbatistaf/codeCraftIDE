"""
Cross-reference validation between .4gl and .per files.

This module provides utilities to:
- Extract OPEN FORM and INPUT BY NAME statements from .4gl code
- Validate that form fields referenced in .4gl exist in .per files
- Check data flow between program variables and form fields
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .per_parser import parse_per_file


class FormReference:
    """Represents a reference to a form in 4GL code."""

    def __init__(self, form_name: str, per_file: str, line: int):
        self.form_name = form_name
        self.per_file = per_file
        self.line = line

    def __repr__(self):
        return f"FormReference({self.form_name} -> {self.per_file} at line {self.line})"


class InputByName:
    """Represents an INPUT BY NAME statement with its variables."""

    def __init__(self, variables: List[str], line: int):
        self.variables = variables
        self.line = line

    def __repr__(self):
        return f"InputByName({self.variables} at line {self.line})"


class CrossReferenceAnalyzer:
    """Analyzes cross-references between .4gl and .per files."""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.form_references: List[FormReference] = []
        self.input_by_name_statements: List[InputByName] = []

    def analyze_4gl_file(self, code: str) -> Tuple[List[FormReference], List[InputByName]]:
        """
        Analyze a .4gl file to extract form references and INPUT BY NAME statements.

        Args:
            code: The .4gl source code

        Returns:
            Tuple of (form_references, input_by_name_statements)
        """
        form_refs = []
        input_statements = []

        lines = code.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Extract OPEN FORM statements
            # Pattern: OPEN FORM form_name FROM "file_name"
            open_form_match = re.search(
                r'\bOPEN\s+FORM\s+(\w+)\s+FROM\s+["\']([^"\']+)["\']',
                line,
                re.IGNORECASE,
            )
            if open_form_match:
                form_name = open_form_match.group(1)
                per_file = open_form_match.group(2)
                if not per_file.endswith(".per"):
                    per_file += ".per"
                form_refs.append(FormReference(form_name, per_file, line_num))

            # Extract INPUT BY NAME statements
            # Pattern: INPUT BY NAME var1, var2, var3
            input_match = re.search(r"\bINPUT\s+BY\s+NAME\s+([\w\s,]+)", line, re.IGNORECASE)
            if input_match:
                # Extract variable names
                var_list = input_match.group(1)
                # Handle multi-line INPUT BY NAME (basic approach)
                # Look ahead for continuation
                full_var_list = var_list
                next_line_idx = line_num
                while next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    # Check if line continues (doesn't have WITHOUT DEFAULTS or other keywords)
                    if re.match(r"^\w+[\w\s,]*$", next_line):
                        full_var_list += " " + next_line
                        next_line_idx += 1
                    else:
                        break

                # Parse variable names
                variables = [
                    v.strip()
                    for v in re.split(r"[,\s]+", full_var_list)
                    if v.strip() and v.upper() not in ("WITHOUT", "DEFAULTS", "HELP")
                ]
                input_statements.append(InputByName(variables, line_num))

        return form_refs, input_statements

    def validate_form_binding(self, fgl_code: str, per_content: str) -> Dict[str, List[str]]:
        """
        Validate that INPUT BY NAME variables match formonly variables in .per file.

        Args:
            fgl_code: The .4gl source code
            per_content: The .per file content

        Returns:
            Dictionary with validation results:
            - 'missing_in_form': Variables in INPUT BY NAME but not in .per
            - 'unused_in_code': Variables in .per but not used in INPUT BY NAME
            - 'warnings': Other validation warnings
        """
        results = {
            "missing_in_form": [],
            "unused_in_code": [],
            "warnings": [],
        }

        try:
            # Parse .per file
            form_def = parse_per_file(per_content)
            formonly_vars = form_def.get_formonly_variables()

            # Extract INPUT BY NAME from .4gl
            _, input_statements = self.analyze_4gl_file(fgl_code)

            # Collect all INPUT BY NAME variables
            input_vars = set()
            for stmt in input_statements:
                input_vars.update(stmt.variables)

            # Check for missing form fields
            for var in input_vars:
                if var not in formonly_vars:
                    results["missing_in_form"].append(
                        f"Variable '{var}' used in INPUT BY NAME but not defined in form"
                    )

            # Check for unused form fields
            for var in formonly_vars.keys():
                if var not in input_vars:
                    results["unused_in_code"].append(
                        f"Form variable '{var}' defined but not used in INPUT BY NAME"
                    )

        except Exception as e:
            results["warnings"].append(f"Validation error: {str(e)}")

        return results

    def find_per_file_for_form(self, form_name: str, fgl_code: str) -> Optional[str]:
        """
        Find the .per file associated with a form name in .4gl code.

        Args:
            form_name: The form name
            fgl_code: The .4gl source code

        Returns:
            The .per file name, or None if not found
        """
        form_refs, _ = self.analyze_4gl_file(fgl_code)

        for ref in form_refs:
            if ref.form_name.lower() == form_name.lower():
                return ref.per_file

        # Try common convention: form_name.per
        return f"{form_name}.per"


def validate_fgl_per_binding(fgl_code: str, per_content: str) -> Dict[str, List[str]]:
    """
    Convenience function to validate binding between .4gl and .per files.

    Args:
        fgl_code: The .4gl source code
        per_content: The .per file content

    Returns:
        Dictionary with validation results
    """
    analyzer = CrossReferenceAnalyzer()
    return analyzer.validate_form_binding(fgl_code, per_content)
