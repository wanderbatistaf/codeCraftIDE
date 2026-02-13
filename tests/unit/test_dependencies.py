"""
Unit tests for the Dependency Resolver module.

Tests for Epic 4, Story 4.3: Dependency Resolver for Multi-File Projects
"""

from pathlib import Path

import pytest

from fglinterpreter.converter.dependencies import (
    DependencyAnalyzer,
    DependencyGraph,
    DependencyResolver,
    FileInfo,
    FunctionExtractor,
    resolve_dependencies,
)
from fglinterpreter.parser import parse_source


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with test 4GL files."""
    project = tmp_path / "project"
    project.mkdir()

    # File 1: utils.4gl - defines utility functions
    (project / "utils.4gl").write_text("""
        FUNCTION add(a, b)
            DEFINE a INTEGER
            DEFINE b INTEGER
            RETURN a + b
        END FUNCTION

        FUNCTION multiply(x, y)
            DEFINE x INTEGER
            DEFINE y INTEGER
            RETURN x * y
        END FUNCTION
        """)

    # File 2: math.4gl - uses utils functions
    (project / "math.4gl").write_text("""
        FUNCTION calculate(a, b)
            DEFINE a INTEGER
            DEFINE b INTEGER
            DEFINE result INTEGER
            LET result = add(a, b)
            RETURN multiply(result, 2)
        END FUNCTION
        """)

    # File 3: main.4gl - uses math functions
    (project / "main.4gl").write_text("""
        MAIN
            DEFINE result INTEGER
            LET result = calculate(5, 3)
            DISPLAY result
        END MAIN
        """)

    # File 4: standalone.4gl - no dependencies
    (project / "standalone.4gl").write_text("""
        MAIN
            DISPLAY "Hello World"
        END MAIN
        """)

    return project


@pytest.fixture
def circular_dependency_dir(tmp_path: Path) -> Path:
    """Create a project with circular dependencies."""
    project = tmp_path / "circular"
    project.mkdir()

    # File A calls function in B
    (project / "a.4gl").write_text("""
        FUNCTION funcA()
            CALL funcB()
        END FUNCTION
        """)

    # File B calls function in C
    (project / "b.4gl").write_text("""
        FUNCTION funcB()
            CALL funcC()
        END FUNCTION
        """)

    # File C calls function in A (creates cycle)
    (project / "c.4gl").write_text("""
        FUNCTION funcC()
            CALL funcA()
        END FUNCTION
        """)

    return project


@pytest.mark.unit
class TestFunctionExtractor:
    """Tests for FunctionExtractor class."""

    def test_extract_function_definitions(self) -> None:
        """Test extracting function definitions."""
        code = """
        FUNCTION foo()
            DISPLAY "foo"
        END FUNCTION

        FUNCTION bar()
            DISPLAY "bar"
        END FUNCTION
        """
        ast = parse_source(code)
        extractor = FunctionExtractor()
        ast.accept(extractor)

        assert "foo" in extractor.defined_functions
        assert "bar" in extractor.defined_functions
        assert len(extractor.defined_functions) == 2

    def test_extract_function_calls(self) -> None:
        """Test extracting function calls."""
        code = """
        FUNCTION test_main()
            CALL foo()
            CALL bar()
        END FUNCTION
        """
        ast = parse_source(code)
        extractor = FunctionExtractor()
        ast.accept(extractor)

        assert "foo" in extractor.called_functions
        assert "bar" in extractor.called_functions

    def test_extract_function_call_expressions(self) -> None:
        """Test extracting function calls in expressions."""
        code = """
        FUNCTION test_calc()
            DEFINE result INTEGER
            LET result = add(1, 2)
            DISPLAY multiply(result, 3)
        END FUNCTION
        """
        ast = parse_source(code)
        extractor = FunctionExtractor()
        ast.accept(extractor)

        assert "add" in extractor.called_functions
        assert "multiply" in extractor.called_functions

    def test_detect_main_block(self) -> None:
        """Test detecting MAIN block."""
        code = """
        MAIN
            DISPLAY "Hello"
        END MAIN
        """
        ast = parse_source(code)
        extractor = FunctionExtractor()
        ast.accept(extractor)

        assert extractor.has_main is True

    def test_no_main_block(self) -> None:
        """Test file without MAIN block."""
        code = """
        FUNCTION foo()
            DISPLAY "foo"
        END FUNCTION
        """
        ast = parse_source(code)
        extractor = FunctionExtractor()
        ast.accept(extractor)

        assert extractor.has_main is False


@pytest.mark.unit
class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer class."""

    def test_analyze_single_file(self, temp_project_dir: Path) -> None:
        """Test analyzing a single file."""
        analyzer = DependencyAnalyzer()
        info = analyzer.analyze_file(temp_project_dir / "utils.4gl")

        assert "add" in info.defined_functions
        assert "multiply" in info.defined_functions
        assert info.has_main is False
        assert info.parse_error is None

    def test_analyze_file_with_dependencies(self, temp_project_dir: Path) -> None:
        """Test analyzing a file that calls other functions."""
        analyzer = DependencyAnalyzer()
        info = analyzer.analyze_file(temp_project_dir / "math.4gl")

        assert "calculate" in info.defined_functions
        assert "add" in info.called_functions
        assert "multiply" in info.called_functions

    def test_analyze_directory(self, temp_project_dir: Path) -> None:
        """Test analyzing all files in a directory."""
        analyzer = DependencyAnalyzer()
        analyzer.analyze_directory(temp_project_dir, recursive=False)

        assert len(analyzer.files) == 4
        assert temp_project_dir / "utils.4gl" in analyzer.files
        assert temp_project_dir / "math.4gl" in analyzer.files

    def test_function_to_file_mapping(self, temp_project_dir: Path) -> None:
        """Test building function-to-file mapping."""
        analyzer = DependencyAnalyzer()
        analyzer.analyze_directory(temp_project_dir)

        assert analyzer.function_to_file["add"] == temp_project_dir / "utils.4gl"
        assert analyzer.function_to_file["multiply"] == temp_project_dir / "utils.4gl"
        assert analyzer.function_to_file["calculate"] == temp_project_dir / "math.4gl"

    def test_resolve_dependencies(self, temp_project_dir: Path) -> None:
        """Test resolving dependencies between files."""
        analyzer = DependencyAnalyzer()
        analyzer.analyze_directory(temp_project_dir)
        analyzer.resolve_dependencies()

        # math.4gl should depend on utils.4gl
        math_info = analyzer.files[temp_project_dir / "math.4gl"]
        assert temp_project_dir / "utils.4gl" in math_info.dependencies

        # main.4gl should depend on math.4gl
        main_info = analyzer.files[temp_project_dir / "main.4gl"]
        assert temp_project_dir / "math.4gl" in main_info.dependencies

        # standalone.4gl should have no dependencies
        standalone_info = analyzer.files[temp_project_dir / "standalone.4gl"]
        assert len(standalone_info.dependencies) == 0


@pytest.mark.unit
class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_add_node(self) -> None:
        """Test adding nodes to the graph."""
        graph = DependencyGraph()
        graph.add_node(Path("a.4gl"))
        graph.add_node(Path("b.4gl"))

        assert Path("a.4gl") in graph.nodes
        assert Path("b.4gl") in graph.nodes

    def test_add_edge(self) -> None:
        """Test adding edges to the graph."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("b.4gl"))

        assert Path("a.4gl") in graph.nodes
        assert Path("b.4gl") in graph.nodes
        assert Path("b.4gl") in graph.get_dependencies(Path("a.4gl"))

    def test_get_dependencies(self) -> None:
        """Test getting dependencies of a node."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("b.4gl"))
        graph.add_edge(Path("a.4gl"), Path("c.4gl"))

        deps = graph.get_dependencies(Path("a.4gl"))
        assert Path("b.4gl") in deps
        assert Path("c.4gl") in deps

    def test_get_dependents(self) -> None:
        """Test getting dependents of a node."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("c.4gl"))
        graph.add_edge(Path("b.4gl"), Path("c.4gl"))

        dependents = graph.get_dependents(Path("c.4gl"))
        assert Path("a.4gl") in dependents
        assert Path("b.4gl") in dependents

    def test_no_cycle(self) -> None:
        """Test cycle detection with no cycles."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("b.4gl"))
        graph.add_edge(Path("b.4gl"), Path("c.4gl"))

        has_cycle, cycle = graph.has_cycle()
        assert has_cycle is False
        assert cycle is None

    def test_detect_cycle(self) -> None:
        """Test detecting circular dependencies."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("b.4gl"))
        graph.add_edge(Path("b.4gl"), Path("c.4gl"))
        graph.add_edge(Path("c.4gl"), Path("a.4gl"))

        has_cycle, cycle = graph.has_cycle()
        assert has_cycle is True
        assert cycle is not None
        assert len(cycle) >= 3

    def test_topological_sort(self) -> None:
        """Test topological sorting."""
        graph = DependencyGraph()
        graph.add_edge(Path("main.4gl"), Path("math.4gl"))
        graph.add_edge(Path("math.4gl"), Path("utils.4gl"))
        graph.add_node(Path("standalone.4gl"))

        order = graph.topological_sort()

        # utils.4gl should come before math.4gl
        utils_idx = order.index(Path("utils.4gl"))
        math_idx = order.index(Path("math.4gl"))
        assert utils_idx < math_idx

        # math.4gl should come before main.4gl
        main_idx = order.index(Path("main.4gl"))
        assert math_idx < main_idx

    def test_topological_sort_with_cycle(self) -> None:
        """Test that topological sort raises error on cycle."""
        graph = DependencyGraph()
        graph.add_edge(Path("a.4gl"), Path("b.4gl"))
        graph.add_edge(Path("b.4gl"), Path("a.4gl"))

        with pytest.raises(ValueError, match="Circular dependency"):
            graph.topological_sort()


@pytest.mark.unit
class TestDependencyResolver:
    """Tests for DependencyResolver class."""

    def test_init(self, temp_project_dir: Path) -> None:
        """Test initializing the resolver."""
        resolver = DependencyResolver(temp_project_dir)

        assert resolver.directory == temp_project_dir
        assert resolver.recursive is True

    def test_analyze(self, temp_project_dir: Path) -> None:
        """Test analyzing a project."""
        resolver = DependencyResolver(temp_project_dir)
        resolver.analyze()

        # Check that files were analyzed
        assert len(resolver.analyzer.files) > 0

        # Check that graph was built
        assert len(resolver.graph.nodes) > 0

    def test_get_conversion_order(self, temp_project_dir: Path) -> None:
        """Test getting conversion order."""
        resolver = DependencyResolver(temp_project_dir)
        resolver.analyze()
        order = resolver.get_conversion_order()

        # Should return all files
        assert len(order) == 4

        # utils.4gl should come before math.4gl
        utils_path = temp_project_dir / "utils.4gl"
        math_path = temp_project_dir / "math.4gl"
        main_path = temp_project_dir / "main.4gl"

        utils_idx = order.index(utils_path)
        math_idx = order.index(math_path)
        main_idx = order.index(main_path)

        assert utils_idx < math_idx
        assert math_idx < main_idx

    def test_get_file_info(self, temp_project_dir: Path) -> None:
        """Test getting file information."""
        resolver = DependencyResolver(temp_project_dir)
        resolver.analyze()

        info = resolver.get_file_info(temp_project_dir / "utils.4gl")
        assert info is not None
        assert "add" in info.defined_functions

    def test_detect_circular_dependencies(self, circular_dependency_dir: Path) -> None:
        """Test detecting circular dependencies."""
        resolver = DependencyResolver(circular_dependency_dir)
        resolver.analyze()

        circular_deps = resolver.get_circular_dependencies()
        assert circular_deps is not None
        assert len(circular_deps) >= 3

    def test_circular_dependencies_error(self, circular_dependency_dir: Path) -> None:
        """Test that circular dependencies raise error in conversion order."""
        resolver = DependencyResolver(circular_dependency_dir)
        resolver.analyze()

        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.get_conversion_order()


@pytest.mark.unit
class TestResolveDependenciesAPI:
    """Tests for the high-level resolve_dependencies API."""

    def test_resolve_dependencies(self, temp_project_dir: Path) -> None:
        """Test the resolve_dependencies convenience function."""
        order, file_info = resolve_dependencies(temp_project_dir)

        # Should return conversion order
        assert len(order) > 0

        # Should return file info
        assert len(file_info) > 0

        # Check correct order
        utils_path = temp_project_dir / "utils.4gl"
        math_path = temp_project_dir / "math.4gl"

        utils_idx = order.index(utils_path)
        math_idx = order.index(math_path)

        assert utils_idx < math_idx

    def test_resolve_dependencies_with_circular(self, circular_dependency_dir: Path) -> None:
        """Test resolving dependencies with circular dependencies."""
        with pytest.raises(ValueError, match="Circular dependency"):
            resolve_dependencies(circular_dependency_dir)
