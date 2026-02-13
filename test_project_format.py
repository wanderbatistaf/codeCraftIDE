#!/usr/bin/env python3
"""
Test CodeCraft Project (.ccp) project format.
"""

from pathlib import Path

from src.fglinterpreter.project import CodeCraftProject, create_project


def test_create_and_save():
    """Test creating and saving a project."""
    print("=" * 80)
    print("TEST 1: Create and Save Project")
    print("=" * 80)

    # Create a new project
    project = create_project(name="ware_print_loc", description="Warehouse label printing system")

    # Add some files
    project.add_file(
        path="ware_print_loc.4gl", content="MAIN\n  CALL localizar()\nEND MAIN", file_type="4gl"
    )

    project.add_file(
        path="localizador.per",
        content="DATABASE soporcel\nSCREEN\n{\n  Label: [field]\n}\nEND\nATTRIBUTES\nEND",
        file_type="per",
    )

    # Save to file
    output_path = "test_project.ccp"
    project.save(output_path)

    print(f"✓ Project saved to {output_path}")
    print(f"  - Name: {project.name}")
    print(f"  - Files: {len(project.files)}")
    print()


def test_load_and_verify():
    """Test loading a project and verifying its contents."""
    print("=" * 80)
    print("TEST 2: Load and Verify Project")
    print("=" * 80)

    # Load the project
    project = CodeCraftProject.load("test_project.ccp")

    print("✓ Project loaded successfully")
    print(f"  - Name: {project.name}")
    print(f"  - Description: {project.description}")
    print(f"  - Version: {project.version}")
    print(f"  - Files: {len(project.files)}")
    print()

    # Verify files
    print("Files in project:")
    for file in project.files:
        print(f"  - {file.path} ({file.type})")
    print()


def test_create_from_workspace():
    """Test creating a project from workspace directory."""
    print("=" * 80)
    print("TEST 3: Create Project from Workspace")
    print("=" * 80)

    workspace_path = Path("realCaseExample/ware_print_loc")

    if not workspace_path.exists():
        print(f"⚠ Workspace directory not found: {workspace_path}")
        print()
        return

    # Create project from workspace
    project = CodeCraftProject.from_workspace(
        workspace_path=workspace_path,
        name="ware_print_loc_real",
        include_patterns=["*.4gl", "*.per", "4make.def"],
    )

    print("✓ Project created from workspace")
    print(f"  - Name: {project.name}")
    print(f"  - Files: {len(project.files)}")
    print()

    # Show file types
    file_types = {}
    for file in project.files:
        file_types[file.type] = file_types.get(file.type, 0) + 1

    print("File types:")
    for file_type, count in file_types.items():
        print(f"  - {file_type}: {count} file(s)")
    print()

    # Show source files
    source_files = project.get_files_by_type("4gl")
    print(f"4GL source files ({len(source_files)}):")
    for file in source_files:
        print(f"  - {file.path}")
    print()

    # Show form files
    form_files = project.get_files_by_type("per")
    print(f"Form files ({len(form_files)}):")
    for file in form_files:
        print(f"  - {file.path}")
    print()

    # Save the project
    output_path = "ware_print_loc_real.ccp"
    project.save(output_path)
    print(f"✓ Project saved to {output_path}")
    print()


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("=" * 80)
    print("TEST 4: JSON Serialization")
    print("=" * 80)

    # Create project
    project1 = create_project("test_json", "Test JSON serialization")
    project1.add_file("test.4gl", "MAIN\nEND MAIN", "4gl")

    # Serialize to JSON
    json_str = project1.to_json()
    print(f"✓ Serialized to JSON ({len(json_str)} bytes)")
    print()

    # Deserialize
    project2 = CodeCraftProject.from_json(json_str)
    print("✓ Deserialized from JSON")
    print(f"  - Name: {project2.name}")
    print(f"  - Files: {len(project2.files)}")
    print()

    # Verify data integrity
    assert project2.name == project1.name
    assert len(project2.files) == len(project1.files)
    assert project2.files[0].path == project1.files[0].path
    print("✓ Data integrity verified")
    print()


def cleanup():
    """Clean up test files."""
    import os

    test_files = ["test_project.ccp", "ware_print_loc_real.ccp"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up: {file}")


if __name__ == "__main__":
    test_create_and_save()
    test_load_and_verify()
    test_create_from_workspace()
    test_json_serialization()

    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print()

    cleanup()
