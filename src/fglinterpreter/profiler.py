"""
Execution profiling and benchmarking infrastructure for fglInterpreter.

This module provides:
- Statement-level execution profiling
- Function call profiling
- Database operation benchmarking
- Performance metrics collection
- Profile reporting and analysis
"""

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from statistics import mean, median, stdev
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class ProfileEntry:
    """Represents a single profiled operation."""

    name: str
    start_time: float
    end_time: float
    duration: float = 0.0
    call_count: int = 1
    children: List["ProfileEntry"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate duration if not provided."""
        if self.duration == 0.0 and self.end_time > 0:
            self.duration = self.end_time - self.start_time

    def add_child(self, child: "ProfileEntry") -> None:
        """Add a child profile entry."""
        self.children.append(child)

    def total_time(self) -> float:
        """Get total time including children."""
        return self.duration + sum(child.total_time() for child in self.children)

    def self_time(self) -> float:
        """Get time excluding children."""
        return self.duration - sum(child.duration for child in self.children)


class ExecutionProfiler:
    """
    Tracks execution performance at statement and function level.

    Provides detailed timing information for interpreter execution,
    including statement execution, function calls, and database operations.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize execution profiler.

        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.entries: List[ProfileEntry] = []
        self.current_stack: List[ProfileEntry] = []
        self.statement_counts: Dict[str, int] = defaultdict(int)
        self.statement_times: Dict[str, List[float]] = defaultdict(list)
        self.function_calls: Dict[str, int] = defaultdict(int)
        self.function_times: Dict[str, List[float]] = defaultdict(list)
        self.database_queries: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start profiling session."""
        if not self.enabled:
            return

        self.start_time = time.time()
        self.entries.clear()
        self.current_stack.clear()
        self.statement_counts.clear()
        self.statement_times.clear()
        self.function_calls.clear()
        self.function_times.clear()
        self.database_queries.clear()

    def stop(self) -> None:
        """Stop profiling session."""
        if not self.enabled:
            return

        self.end_time = time.time()

    def total_duration(self) -> float:
        """Get total profiling session duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @contextmanager
    def profile_operation(
        self, name: str, op_type: str = "operation", metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager to profile an operation.

        Args:
            name: Operation name
            op_type: Operation type (statement, function, query, etc.)
            metadata: Additional metadata

        Yields:
            Profile entry for the operation
        """
        if not self.enabled:
            yield None
            return

        start_time = time.time()

        entry = ProfileEntry(
            name=name, start_time=start_time, end_time=0.0, metadata=metadata or {}
        )
        entry.metadata["type"] = op_type

        # Add to stack
        if self.current_stack:
            self.current_stack[-1].add_child(entry)
        else:
            self.entries.append(entry)

        self.current_stack.append(entry)

        try:
            yield entry
        finally:
            end_time = time.time()
            entry.end_time = end_time
            entry.duration = end_time - start_time

            # Update statistics
            if op_type == "statement":
                self.statement_counts[name] += 1
                self.statement_times[name].append(entry.duration)
            elif op_type == "function":
                self.function_calls[name] += 1
                self.function_times[name].append(entry.duration)
            elif op_type == "query":
                self.database_queries.append(
                    {
                        "query": name,
                        "duration": entry.duration,
                        "timestamp": start_time,
                        **entry.metadata,
                    }
                )

            # Pop from stack
            self.current_stack.pop()

    def record_statement(self, statement_type: str, duration: float) -> None:
        """
        Record a statement execution.

        Args:
            statement_type: Type of statement (e.g., "LET", "IF", "FOR")
            duration: Execution duration in seconds
        """
        if not self.enabled:
            return

        self.statement_counts[statement_type] += 1
        self.statement_times[statement_type].append(duration)

    def record_function_call(self, function_name: str, duration: float) -> None:
        """
        Record a function call.

        Args:
            function_name: Name of the function
            duration: Execution duration in seconds
        """
        if not self.enabled:
            return

        self.function_calls[function_name] += 1
        self.function_times[function_name].append(duration)

    def record_database_query(
        self, query: str, duration: float, row_count: int = 0, params_count: int = 0
    ) -> None:
        """
        Record a database query.

        Args:
            query: SQL query string
            duration: Execution duration in seconds
            row_count: Number of rows affected/returned
            params_count: Number of parameters
        """
        if not self.enabled:
            return

        self.database_queries.append(
            {
                "query": query[:200],  # Truncate long queries
                "duration": duration,
                "row_count": row_count,
                "params_count": params_count,
                "timestamp": time.time(),
            }
        )

    def get_hotspots(self, limit: int = 10) -> List[Tuple[str, float, int]]:
        """
        Get the slowest operations (hotspots).

        Args:
            limit: Maximum number of hotspots to return

        Returns:
            List of (name, total_time, call_count) tuples
        """
        hotspots = []

        # Combine statements and functions
        for name, times in self.statement_times.items():
            total_time = sum(times)
            count = self.statement_counts[name]
            hotspots.append((f"STMT:{name}", total_time, count))

        for name, times in self.function_times.items():
            total_time = sum(times)
            count = self.function_calls[name]
            hotspots.append((f"FUNC:{name}", total_time, count))

        # Sort by total time descending
        hotspots.sort(key=lambda x: x[1], reverse=True)

        return hotspots[:limit]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get profile summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        total_statements = sum(self.statement_counts.values())
        total_functions = sum(self.function_calls.values())
        total_queries = len(self.database_queries)

        avg_query_time = 0.0
        if self.database_queries:
            avg_query_time = mean([q["duration"] for q in self.database_queries])

        return {
            "total_duration": self.total_duration(),
            "statement_count": total_statements,
            "function_call_count": total_functions,
            "database_query_count": total_queries,
            "average_query_time": avg_query_time,
            "unique_statements": len(self.statement_counts),
            "unique_functions": len(self.function_calls),
            "hotspots": self.get_hotspots(5),
        }

    def generate_report(self, detailed: bool = False) -> str:
        """
        Generate a human-readable profile report.

        Args:
            detailed: Include detailed breakdown

        Returns:
            Formatted profile report
        """
        lines = []
        lines.append("=" * 70)
        lines.append("EXECUTION PROFILE REPORT")
        lines.append("=" * 70)

        summary = self.get_summary()

        lines.append(f"\nTotal Duration: {summary['total_duration']:.3f}s")
        lines.append(f"Statements Executed: {summary['statement_count']}")
        lines.append(f"Function Calls: {summary['function_call_count']}")
        lines.append(f"Database Queries: {summary['database_query_count']}")

        if summary["database_query_count"] > 0:
            lines.append(f"Average Query Time: {summary['average_query_time']*1000:.2f}ms")

        # Hotspots
        lines.append("\n" + "-" * 70)
        lines.append("TOP 10 HOTSPOTS (by total time)")
        lines.append("-" * 70)
        lines.append(f"{'Operation':<40} {'Total Time':<15} {'Calls':<10}")
        lines.append("-" * 70)

        for name, total_time, count in self.get_hotspots(10):
            avg_time = total_time / count if count > 0 else 0
            lines.append(
                f"{name:<40} {total_time*1000:>10.2f}ms ({avg_time*1000:.2f}ms avg)  {count:>6}"
            )

        if detailed:
            # Statement breakdown
            if self.statement_times:
                lines.append("\n" + "-" * 70)
                lines.append("STATEMENT BREAKDOWN")
                lines.append("-" * 70)
                lines.append(f"{'Statement':<30} {'Count':<10} {'Total':<15} {'Avg':<15}")
                lines.append("-" * 70)

                for stmt_type in sorted(self.statement_times.keys()):
                    times = self.statement_times[stmt_type]
                    count = self.statement_counts[stmt_type]
                    total = sum(times)
                    avg = mean(times)
                    lines.append(
                        f"{stmt_type:<30} {count:<10} {total*1000:>10.2f}ms   {avg*1000:>10.2f}ms"
                    )

            # Function breakdown
            if self.function_times:
                lines.append("\n" + "-" * 70)
                lines.append("FUNCTION BREAKDOWN")
                lines.append("-" * 70)
                lines.append(f"{'Function':<30} {'Calls':<10} {'Total':<15} {'Avg':<15}")
                lines.append("-" * 70)

                for func_name in sorted(self.function_times.keys()):
                    times = self.function_times[func_name]
                    count = self.function_calls[func_name]
                    total = sum(times)
                    avg = mean(times)
                    lines.append(
                        f"{func_name:<30} {count:<10} {total*1000:>10.2f}ms   {avg*1000:>10.2f}ms"
                    )

            # Database queries
            if self.database_queries:
                lines.append("\n" + "-" * 70)
                lines.append("DATABASE QUERIES")
                lines.append("-" * 70)

                # Get slowest queries
                slowest = sorted(self.database_queries, key=lambda q: q["duration"], reverse=True)[
                    :10
                ]

                for i, query_info in enumerate(slowest, 1):
                    lines.append(f"\n{i}. Duration: {query_info['duration']*1000:.2f}ms")
                    lines.append(f"   Query: {query_info['query']}")
                    if "row_count" in query_info:
                        lines.append(f"   Rows: {query_info['row_count']}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)


class Benchmark:
    """
    Performance benchmarking utility.

    Provides tools for measuring and comparing operation performance.
    """

    def __init__(self, name: str):
        """
        Initialize benchmark.

        Args:
            name: Benchmark name
        """
        self.name = name
        self.results: List[float] = []
        self.metadata: Dict[str, Any] = {}

    def run(self, func: Callable, iterations: int = 100) -> Dict[str, Any]:
        """
        Run benchmark for a function.

        Args:
            func: Function to benchmark
            iterations: Number of iterations

        Returns:
            Benchmark results dictionary
        """
        self.results.clear()

        # Warmup
        func()

        # Benchmark iterations
        for _ in range(iterations):
            start = time.time()
            func()
            duration = time.time() - start
            self.results.append(duration)

        return self.get_results()

    def add_result(self, duration: float) -> None:
        """
        Manually add a benchmark result.

        Args:
            duration: Operation duration in seconds
        """
        self.results.append(duration)

    def get_results(self) -> Dict[str, Any]:
        """
        Get benchmark results with statistics.

        Returns:
            Dictionary with benchmark statistics
        """
        if not self.results:
            return {
                "name": self.name,
                "iterations": 0,
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "stdev": 0.0,
            }

        return {
            "name": self.name,
            "iterations": len(self.results),
            "mean": mean(self.results),
            "median": median(self.results),
            "min": min(self.results),
            "max": max(self.results),
            "stdev": stdev(self.results) if len(self.results) > 1 else 0.0,
            "total": sum(self.results),
        }

    def compare(self, other: "Benchmark") -> Dict[str, Any]:
        """
        Compare this benchmark with another.

        Args:
            other: Another benchmark to compare with

        Returns:
            Comparison results
        """
        my_results = self.get_results()
        other_results = other.get_results()

        speedup = other_results["mean"] / my_results["mean"] if my_results["mean"] > 0 else 0
        diff_ms = (my_results["mean"] - other_results["mean"]) * 1000

        return {
            "benchmark_a": self.name,
            "benchmark_b": other.name,
            "mean_a": my_results["mean"],
            "mean_b": other_results["mean"],
            "speedup": speedup,
            "difference_ms": diff_ms,
            "faster": self.name if my_results["mean"] < other_results["mean"] else other.name,
        }

    def report(self) -> str:
        """
        Generate benchmark report.

        Returns:
            Formatted benchmark report
        """
        results = self.get_results()

        lines = []
        lines.append(f"Benchmark: {self.name}")
        lines.append(f"Iterations: {results['iterations']}")
        lines.append(f"Mean: {results['mean']*1000:.3f}ms")
        lines.append(f"Median: {results['median']*1000:.3f}ms")
        lines.append(f"Min: {results['min']*1000:.3f}ms")
        lines.append(f"Max: {results['max']*1000:.3f}ms")
        lines.append(f"StdDev: {results['stdev']*1000:.3f}ms")
        lines.append(f"Total: {results['total']*1000:.3f}ms")

        return "\n".join(lines)


# Global profiler instance
_global_profiler: Optional[ExecutionProfiler] = None


def get_profiler() -> ExecutionProfiler:
    """Get or create the global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = ExecutionProfiler(enabled=False)
    return _global_profiler


def enable_profiling() -> None:
    """Enable global profiling."""
    profiler = get_profiler()
    profiler.enabled = True
    profiler.start()


def disable_profiling() -> None:
    """Disable global profiling."""
    profiler = get_profiler()
    profiler.enabled = False


def get_profile_report(detailed: bool = False) -> str:
    """Get profile report from global profiler."""
    profiler = get_profiler()
    profiler.stop()
    return profiler.generate_report(detailed=detailed)
