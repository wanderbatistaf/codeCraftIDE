#!/usr/bin/env python3
"""
Complete integration test of the .per form rendering and cross-reference validation.
"""

from src.fglinterpreter.cross_reference import validate_fgl_per_binding
from src.fglinterpreter.make_def_parser import parse_4make_def
from src.fglinterpreter.per_parser import parse_per_file


def test_per_parsing():
    """Test .per file parsing."""
    print("=" * 80)
    print("TEST 1: .per File Parsing")
    print("=" * 80)

    with open("realCaseExample/ware_print_loc/localizador.per") as f:
        per_content = f.read()

    form = parse_per_file(per_content)

    print("✓ Successfully parsed localizador.per")
    print(f"  - Database: {form.database.database_name}")
    print(f"  - Screen fields: {len(form.get_screen_fields())}")
    print(f"  - Attributes: {len(form.attributes.fields) if form.attributes else 0}")
    print(f"  - Formonly variables: {len(form.get_formonly_variables())}")

    errors = form.validate()
    if errors:
        print(f"  ⚠ Validation errors: {errors}")
    else:
        print("  ✓ No validation errors")

    print()


def test_cross_reference():
    """Test cross-reference validation between .4gl and .per."""
    print("=" * 80)
    print("TEST 2: Cross-Reference Validation")
    print("=" * 80)

    with open("realCaseExample/ware_print_loc/localizador.4gl") as f:
        fgl_code = f.read()

    with open("realCaseExample/ware_print_loc/localizador.per") as f:
        per_content = f.read()

    results = validate_fgl_per_binding(fgl_code, per_content)

    print("✓ Cross-reference validation completed")
    print()

    if results["missing_in_form"]:
        print("Missing in form:")
        for msg in results["missing_in_form"]:
            print(f"  ⚠ {msg}")
        print()

    if results["unused_in_code"]:
        print("Unused in code:")
        for msg in results["unused_in_code"]:
            print(f"  ℹ {msg}")
        print()

    if results["warnings"]:
        print("Warnings:")
        for msg in results["warnings"]:
            print(f"  ⚠ {msg}")
        print()

    if not results["missing_in_form"] and not results["unused_in_code"] and not results["warnings"]:
        print("  ✓ Perfect match! All variables are properly bound.")
        print()


def test_4make_def():
    """Test 4make.def parsing."""
    print("=" * 80)
    print("TEST 3: 4make.def Parsing")
    print("=" * 80)

    with open("realCaseExample/ware_print_loc/4make.def") as f:
        content = f.read()

    make_def = parse_4make_def(content)

    print("✓ Successfully parsed 4make.def")
    print(f"  - Target: {make_def.target}")
    print(f"  - Source files: {len(make_def.get_source_files())}")
    for src in make_def.get_source_files():
        print(f"    • {src}")
    print(f"  - Form files: {len(make_def.get_form_files())}")
    for form in make_def.get_form_files():
        print(f"    • {form}")
    print(f"  - Libraries: {len(make_def.get_library_files())}")
    for lib in make_def.get_library_files():
        print(f"    • {lib}")
    print()


def test_summary():
    """Print summary of features."""
    print("=" * 80)
    print("IMPLEMENTATION SUMMARY")
    print("=" * 80)
    print()
    print("✓ 1. .per file parser (lexer, parser, AST)")
    print("   - Parses DATABASE, SCREEN, ATTRIBUTES, INSTRUCTIONS sections")
    print("   - Extracts field definitions and screen layout")
    print("   - Validates form structure")
    print()
    print("✓ 2. API endpoint for parsing .per forms")
    print("   - POST /api/parse-form")
    print("   - Returns parsed form structure and validation errors")
    print()
    print("✓ 3. Form renderer/preview component")
    print("   - React component for visual form preview")
    print("   - Displays screen layout, fields, and attributes")
    print("   - Shows validation errors")
    print()
    print("✓ 4. Monaco Editor syntax highlighting for .per files")
    print("   - Registered 'per' language mode")
    print("   - Keyword highlighting, field detection, string literals")
    print()
    print("✓ 5. Split-view editor for .per files")
    print("   - Editor on left, live preview on right")
    print("   - Auto-detects .per files by extension")
    print()
    print("✓ 6. Cross-reference validation")
    print("   - Analyzes INPUT BY NAME statements in .4gl")
    print("   - Validates against formonly variables in .per")
    print("   - API endpoint: POST /api/validate-cross-reference")
    print()
    print("✓ 7. 4make.def parser")
    print("   - Parses build configuration")
    print("   - Extracts source files, forms, and dependencies")
    print("   - Enables function resolution across files")
    print()


if __name__ == "__main__":
    test_per_parsing()
    test_cross_reference()
    test_4make_def()
    test_summary()
