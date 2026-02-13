"""
Dependency resolution for multi-file 4GL projects.

This module provides functionality for:
- Analyzing 4GL files for function definitions and calls
- Building dependency graphs between files
- Determining correct conversion order using topological sort
- Detecting circular dependencies
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..lexer import LexerError
from ..parser import ParserError, parse_source
from ..parser.ast_nodes import (
    ASTVisitor,
    CallStatement,
    FunctionCall,
    FunctionDef,
    Program,
)


@dataclass
class FileInfo:
    """Information about a 4GL file."""

    path: Path
    defined_functions: Set[str] = field(default_factory=set)
    called_functions: Set[str] = field(default_factory=set)
    dependencies: Set[Path] = field(default_factory=set)
    has_main: bool = False
    parse_error: Optional[str] = None


class FunctionExtractor(ASTVisitor):
    """AST visitor to extract function definitions and calls."""

    def __init__(self):
        """Initialize the extractor."""
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()
        self.has_main: bool = False

    def visit_program(self, node: Program) -> None:
        """Visit program node."""
        # Check for main block
        if node.main_block:
            self.has_main = True

        # Visit functions
        for func in node.functions:
            func.accept(self)

        # Visit main block statements if present
        if node.main_block and node.main_block.body:
            for stmt in node.main_block.body:
                stmt.accept(self)

    def visit_function_def(self, node: FunctionDef) -> None:
        """Visit function definition."""
        self.defined_functions.add(node.name)

        # Visit function body for calls
        if node.body:
            for stmt in node.body:
                stmt.accept(self)

    def visit_call_statement(self, node: CallStatement) -> None:
        """Visit CALL statement."""
        self.called_functions.add(node.function_name)

    def visit_function_call(self, node: FunctionCall) -> str:
        """Visit function call expression."""
        self.called_functions.add(node.function_name)
        return ""

    # Default visitors for other node types
    def visit_main_block(self, node) -> None:
        """Visit main block."""
        if node.body:
            for stmt in node.body:
                stmt.accept(self)

    def visit_let_statement(self, node) -> None:
        """Visit let statement."""
        if hasattr(node, "value"):
            node.value.accept(self)

    def visit_if_statement(self, node) -> None:
        """Visit if statement."""
        node.condition.accept(self)
        if node.then_block:
            for stmt in node.then_block:
                stmt.accept(self)
        for elif_cond, elif_block in node.elif_blocks:
            elif_cond.accept(self)
            if elif_block:
                for stmt in elif_block:
                    stmt.accept(self)
        if node.else_block:
            for stmt in node.else_block:
                stmt.accept(self)

    def visit_for_statement(self, node) -> None:
        """Visit for statement."""
        node.start_value.accept(self)
        node.end_value.accept(self)
        if node.step_value:
            node.step_value.accept(self)
        if node.body:
            for stmt in node.body:
                stmt.accept(self)

    def visit_while_statement(self, node) -> None:
        """Visit while statement."""
        node.condition.accept(self)
        if node.body:
            for stmt in node.body:
                stmt.accept(self)

    def visit_return_statement(self, node) -> None:
        """Visit return statement."""
        if node.value:
            node.value.accept(self)

    def visit_display_statement(self, node) -> None:
        """Visit display statement."""
        if node.expressions:
            for expr in node.expressions:
                expr.accept(self)

    def visit_binary_op(self, node) -> str:
        """Visit binary operation."""
        node.left.accept(self)
        node.right.accept(self)
        return ""

    def visit_unary_op(self, node) -> str:
        """Visit unary operation."""
        node.operand.accept(self)
        return ""

    # Terminal nodes
    def visit_literal(self, node) -> str:
        """Visit literal."""
        return ""

    def visit_identifier(self, node) -> str:
        """Visit identifier."""
        return ""

    def visit_define_statement(self, node) -> None:
        """Visit define statement."""
        pass

    def visit_case_statement(self, node) -> None:
        """Visit case statement."""
        for when_clause in node.when_clauses:
            when_clause.condition.accept(self)
            if when_clause.statements:
                for stmt in when_clause.statements:
                    stmt.accept(self)
        if node.otherwise_block:
            for stmt in node.otherwise_block:
                stmt.accept(self)

    def visit_exit_statement(self, node) -> None:
        """Visit exit statement."""
        pass

    def visit_continue_statement(self, node) -> None:
        """Visit continue statement."""
        pass

    # Database-related visitors (not used for dependency analysis)
    def visit_array_access(self, node) -> str:
        """Visit array access."""
        return ""

    def visit_foreach_statement(self, node) -> None:
        """Visit foreach statement."""
        pass

    def visit_select_statement(self, node) -> None:
        """Visit select statement."""
        pass

    def visit_insert_statement(self, node) -> None:
        """Visit insert statement."""
        pass

    def visit_update_statement(self, node) -> None:
        """Visit update statement."""
        pass

    def visit_delete_statement(self, node) -> None:
        """Visit delete statement."""
        pass

    def visit_declare_statement(self, node) -> None:
        """Visit declare statement."""
        pass

    def visit_open_statement(self, node) -> None:
        """Visit open statement."""
        pass

    def visit_close_statement(self, node) -> None:
        """Visit close statement."""
        pass

    def visit_free_statement(self, node) -> None:
        """Visit free statement."""
        pass

    def visit_database_statement(self, node) -> None:
        """Visit database statement."""
        pass

    def visit_begin_work_statement(self, node) -> None:
        """Visit begin work statement."""
        pass

    def visit_commit_work_statement(self, node) -> None:
        """Visit commit work statement."""
        pass

    def visit_rollback_work_statement(self, node) -> None:
        """Visit rollback work statement."""
        pass


class DependencyAnalyzer:
    """Analyzes 4GL files for dependencies."""

    def __init__(self):
        """Initialize the analyzer."""
        self.files: Dict[Path, FileInfo] = {}
        self.function_to_file: Dict[str, Path] = {}

    def analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single 4GL file.

        Args:
            file_path: Path to the .4gl file

        Returns:
            FileInfo with analysis results
        """
        info = FileInfo(path=file_path)

        try:
            # Read and parse the file
            source_code = file_path.read_text()
            ast = parse_source(source_code, filename=str(file_path))

            # Extract functions and calls
            extractor = FunctionExtractor()
            ast.accept(extractor)

            info.defined_functions = extractor.defined_functions
            info.called_functions = extractor.called_functions
            info.has_main = extractor.has_main

        except (LexerError, ParserError) as e:
            info.parse_error = str(e)
        except Exception as e:
            info.parse_error = f"Unexpected error: {e}"

        return info

    def analyze_directory(self, directory: Path, recursive: bool = True) -> None:
        """Analyze all 4GL files in a directory.

        Args:
            directory: Directory containing .4gl files
            recursive: Whether to search subdirectories
        """
        # Find all .4gl files
        if recursive:
            files = sorted(directory.rglob("*.4gl"))
        else:
            files = sorted(directory.glob("*.4gl"))

        # Analyze each file
        for file_path in files:
            info = self.analyze_file(file_path)
            self.files[file_path] = info

            # Build function-to-file mapping
            for func_name in info.defined_functions:
                self.function_to_file[func_name] = file_path

    def resolve_dependencies(self) -> None:
        """Resolve dependencies between files based on function calls."""
        for file_path, info in self.files.items():
            # For each function called in this file
            for called_func in info.called_functions:
                # Find which file defines this function
                if called_func in self.function_to_file:
                    defining_file = self.function_to_file[called_func]
                    # Only add dependency if it's a different file
                    if defining_file != file_path:
                        info.dependencies.add(defining_file)


@dataclass
class DependencyGraph:
    """Represents the dependency graph of a project."""

    nodes: Set[Path] = field(default_factory=set)
    edges: Dict[Path, Set[Path]] = field(default_factory=lambda: defaultdict(set))
    reverse_edges: Dict[Path, Set[Path]] = field(default_factory=lambda: defaultdict(set))

    def add_node(self, node: Path) -> None:
        """Add a node to the graph."""
        self.nodes.add(node)

    def add_edge(self, from_node: Path, to_node: Path) -> None:
        """Add a directed edge (from_node depends on to_node)."""
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        self.edges[from_node].add(to_node)
        self.reverse_edges[to_node].add(from_node)

    def get_dependencies(self, node: Path) -> Set[Path]:
        """Get all nodes that the given node depends on."""
        return self.edges.get(node, set())

    def get_dependents(self, node: Path) -> Set[Path]:
        """Get all nodes that depend on the given node."""
        return self.reverse_edges.get(node, set())

    def has_cycle(self) -> Tuple[bool, Optional[List[Path]]]:
        """Check if the graph has cycles.

        Returns:
            Tuple of (has_cycle, cycle_path)
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = dict.fromkeys(self.nodes, WHITE)
        parent = dict.fromkeys(self.nodes)

        def dfs(node: Path) -> Optional[List[Path]]:
            """DFS to detect cycles."""
            color[node] = GRAY

            for neighbor in self.edges.get(node, set()):
                if color[neighbor] == GRAY:
                    # Found a cycle, reconstruct the path
                    cycle = [neighbor]
                    current = node
                    while current != neighbor:
                        cycle.append(current)
                        current = parent[current]
                    cycle.append(neighbor)
                    return list(reversed(cycle))

                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle

            color[node] = BLACK
            return None

        for node in self.nodes:
            if color[node] == WHITE:
                cycle = dfs(node)
                if cycle:
                    return True, cycle

        return False, None

    def topological_sort(self) -> List[Path]:
        """Perform topological sort on the graph.

        Returns:
            List of nodes in topological order (dependencies first)

        Raises:
            ValueError: If the graph contains cycles
        """
        has_cycle, cycle = self.has_cycle()
        if has_cycle:
            cycle_str = " -> ".join(str(p.name) for p in cycle)
            raise ValueError(f"Circular dependency detected: {cycle_str}")

        # Kahn's algorithm (using reverse graph for dependencies-first order)
        # Count outgoing edges (dependencies) for each node
        out_degree = {node: len(self.edges.get(node, set())) for node in self.nodes}

        # Start with nodes that have no dependencies (out_degree 0)
        queue = deque([node for node in self.nodes if out_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Process all nodes that depend on this node
            for dependent in self.reverse_edges.get(node, set()):
                out_degree[dependent] -= 1
                if out_degree[dependent] == 0:
                    queue.append(dependent)

        return result


class DependencyResolver:
    """Resolves dependencies for multi-file 4GL projects."""

    def __init__(self, directory: Path, recursive: bool = True):
        """Initialize the dependency resolver.

        Args:
            directory: Project directory containing .4gl files
            recursive: Whether to search subdirectories
        """
        self.directory = directory
        self.recursive = recursive
        self.analyzer = DependencyAnalyzer()
        self.graph = DependencyGraph()

    def analyze(self) -> None:
        """Analyze the project and build dependency graph."""
        # Analyze all files
        self.analyzer.analyze_directory(self.directory, self.recursive)

        # Resolve dependencies between files
        self.analyzer.resolve_dependencies()

        # Build dependency graph
        for file_path, info in self.analyzer.files.items():
            self.graph.add_node(file_path)
            for dependency in info.dependencies:
                self.graph.add_edge(file_path, dependency)

    def get_conversion_order(self) -> List[Path]:
        """Get the optimal order for converting files.

        Returns:
            List of file paths in conversion order (dependencies first)

        Raises:
            ValueError: If circular dependencies are detected
        """
        return self.graph.topological_sort()

    def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Get information about a specific file.

        Args:
            file_path: Path to the file

        Returns:
            FileInfo or None if not analyzed
        """
        return self.analyzer.files.get(file_path)

    def get_circular_dependencies(self) -> Optional[List[Path]]:
        """Check for circular dependencies.

        Returns:
            List of files in the circular dependency, or None if no cycles
        """
        has_cycle, cycle = self.graph.has_cycle()
        return cycle if has_cycle else None


def resolve_dependencies(
    directory: Path, recursive: bool = True
) -> Tuple[List[Path], Dict[Path, FileInfo]]:
    """Convenience function to resolve dependencies.

    Args:
        directory: Project directory containing .4gl files
        recursive: Whether to search subdirectories

    Returns:
        Tuple of (conversion_order, file_info_dict)

    Raises:
        ValueError: If circular dependencies are detected
    """
    resolver = DependencyResolver(directory, recursive)
    resolver.analyze()
    conversion_order = resolver.get_conversion_order()
    file_info = resolver.analyzer.files

    return conversion_order, file_info
