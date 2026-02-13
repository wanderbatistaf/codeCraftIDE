#!/usr/bin/env python3
"""Test DATETIME/INTERVAL qualifiers parsing."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fglinterpreter.lexer.lexer import Lexer
from fglinterpreter.parser.parser import Parser


def test_datetime_qualifiers():
    """Test parsing of DATETIME and INTERVAL qualifiers."""

    test_cases = [
        ("order_time DATETIME YEAR TO SECOND", "DATETIME", "YEAR", "SECOND"),
        ("order_date DATETIME YEAR TO DAY", "DATETIME", "YEAR", "DAY"),
        ("ship_date DATETIME YEAR TO MONTH", "DATETIME", "YEAR", "MONTH"),
        ("time_elapsed INTERVAL HOUR TO MINUTE", "INTERVAL", "HOUR", "MINUTE"),
        ("duration INTERVAL DAY TO SECOND", "INTERVAL", "DAY", "SECOND"),
        ("age_years INTERVAL YEAR TO MONTH", "INTERVAL", "YEAR", "MONTH"),
        ("simple_date DATETIME", "DATETIME", None, None),
    ]

    print("Testing DATETIME/INTERVAL qualifier parsing...")
    print("=" * 70)

    for define_clause, expected_type, expected_start, expected_end in test_cases:
        source = f"MAIN\nDEFINE {define_clause}\nEND MAIN"
        print(f"\nTest: DEFINE {define_clause}")

        try:
            # Tokenize
            lexer = Lexer(source)
            tokens = lexer.tokenize()

            # Parse
            parser = Parser(tokens)
            ast = parser.parse()

            # Get the DEFINE statement (inside the MAIN block)
            if ast and hasattr(ast, "main_block") and ast.main_block:
                main_block = ast.main_block
                if main_block.body:
                    define_stmt = main_block.body[0]
                else:
                    print("  ✗ FAILED: No body in MAIN block")
                    continue
            else:
                print("  ✗ FAILED: No main block parsed")
                continue

            # Check results
            print(f"  Data type: {define_stmt.data_type}")
            print(f"  Qualifier start: {define_stmt.qualifier_start}")
            print(f"  Qualifier end: {define_stmt.qualifier_end}")

            # Validate
            assert (
                define_stmt.data_type.upper() == expected_type
            ), f"Expected type {expected_type}, got {define_stmt.data_type}"
            assert (
                define_stmt.qualifier_start == expected_start
            ), f"Expected start {expected_start}, got {define_stmt.qualifier_start}"
            assert (
                define_stmt.qualifier_end == expected_end
            ), f"Expected end {expected_end}, got {define_stmt.qualifier_end}"

            print("  ✓ PASSED")

        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All tests completed!")


if __name__ == "__main__":
    test_datetime_qualifiers()
