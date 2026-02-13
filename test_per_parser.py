#!/usr/bin/env python3
"""
Quick test of the .per parser with the real example files.
"""

from src.fglinterpreter.per_parser import parse_per_file


def test_localizador_per():
    """Test parsing the localizador.per file."""
    with open("realCaseExample/ware_print_loc/localizador.per") as f:
        content = f.read()

    print("Parsing localizador.per...")
    form = parse_per_file(content)

    print("\n=== DATABASE ===")
    if form.database:
        print(f"  Name: {form.database.database_name}")
        print(f"  Options: {form.database.options}")

    print("\n=== SCREEN ===")
    if form.screen:
        print(f"  Height: {form.screen.height} lines")
        print(f"  Width: {form.screen.width} columns")
        print("\n  Fields found in screen:")
        for field in form.get_screen_fields():
            print(f"    - {field.name} at position {field.position}, width={field.width}")

    print("\n=== ATTRIBUTES ===")
    if form.attributes:
        print(f"  Total fields: {len(form.attributes.fields)}")
        for attr in form.attributes.fields:
            props_str = ", ".join(f"{k}={v}" for k, v in attr.properties.items())
            print(f"    - {attr.screen_field} = {attr.data_source}")
            if props_str:
                print(f"      Properties: {props_str}")

    print("\n=== INSTRUCTIONS ===")
    if form.instructions:
        print(f"  Instructions: {form.instructions.instructions}")

    print("\n=== FORMONLY VARIABLES ===")
    formonly_vars = form.get_formonly_variables()
    for var_name, screen_field in formonly_vars.items():
        print(f"  {var_name} -> {screen_field}")

    print("\n=== VALIDATION ===")
    errors = form.validate()
    if errors:
        print("  Validation errors:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✓ Form is valid!")


def test_w_lista_per():
    """Test parsing the w_lista.per file."""
    with open("realCaseExample/ware_print_loc/w_lista.per") as f:
        content = f.read()

    print("\n\n" + "=" * 80)
    print("Parsing w_lista.per...")
    form = parse_per_file(content)

    print("\n=== DATABASE ===")
    if form.database:
        print(f"  Name: {form.database.database_name}")
        print(f"  Options: {form.database.options}")

    print("\n=== SCREEN ===")
    if form.screen:
        print(f"  Height: {form.screen.height} lines")
        print("\n  Fields found in screen:")
        for field in form.get_screen_fields():
            print(f"    - {field.name} at position {field.position}, width={field.width}")

    print("\n=== ATTRIBUTES ===")
    if form.attributes:
        for attr in form.attributes.fields:
            props_str = ", ".join(f"{k}={v}" for k, v in attr.properties.items())
            print(f"    - {attr.screen_field} = {attr.data_source}")
            if props_str:
                print(f"      Properties: {props_str}")


if __name__ == "__main__":
    test_localizador_per()
    test_w_lista_per()
