"""
Unit tests for execution profiling and benchmarking.

Tests the profiler infrastructure and benchmarking capabilities.
"""

import time

import pytest

from src.fglinterpreter.profiler import (
    Benchmark,
    ExecutionProfiler,
    ProfileEntry,
    disable_profiling,
    enable_profiling,
    get_profile_report,
    get_profiler,
)


@pytest.mark.unit
class TestProfileEntry:
    """Tests for ProfileEntry dataclass."""

    def test_profile_entry_creation(self):
        """Test creating a profile entry."""
        entry = ProfileEntry(name="test_operation", start_time=1.0, end_time=2.0)

        assert entry.name == "test_operation"
        assert entry.start_time == 1.0
        assert entry.end_time == 2.0
        assert entry.duration == 1.0
        assert entry.call_count == 1

    def test_profile_entry_add_child(self):
        """Test adding child entries."""
        parent = ProfileEntry("parent", 1.0, 3.0)
        child = ProfileEntry("child", 1.5, 2.5)

        parent.add_child(child)

        assert len(parent.children) == 1
        assert parent.children[0] == child

    def test_profile_entry_total_time(self):
        """Test total time calculation including children."""
        parent = ProfileEntry("parent", 1.0, 4.0)  # 3.0s
        child1 = ProfileEntry("child1", 1.5, 2.5)  # 1.0s
        child2 = ProfileEntry("child2", 2.5, 3.0)  # 0.5s

        parent.add_child(child1)
        parent.add_child(child2)

        # Total: 3.0 + 1.0 + 0.5 = 4.5s
        assert parent.total_time() == pytest.approx(4.5)

    def test_profile_entry_self_time(self):
        """Test self time calculation excluding children."""
        parent = ProfileEntry("parent", 1.0, 4.0)  # 3.0s
        child1 = ProfileEntry("child1", 1.5, 2.5)  # 1.0s
        child2 = ProfileEntry("child2", 2.5, 3.0)  # 0.5s

        parent.add_child(child1)
        parent.add_child(child2)

        # Self time: 3.0 - (1.0 + 0.5) = 1.5s
        assert parent.self_time() == pytest.approx(1.5)


@pytest.mark.unit
class TestExecutionProfiler:
    """Tests for ExecutionProfiler class."""

    @pytest.fixture
    def profiler(self):
        """Create a profiler for testing."""
        return ExecutionProfiler(enabled=True)

    def test_profiler_initialization(self, profiler):
        """Test profiler initialization."""
        assert profiler.enabled is True
        assert len(profiler.entries) == 0
        assert profiler.start_time is None
        assert profiler.end_time is None

    def test_profiler_start_stop(self, profiler):
        """Test profiler start and stop."""
        profiler.start()
        assert profiler.start_time is not None

        time.sleep(0.01)

        profiler.stop()
        assert profiler.end_time is not None
        assert profiler.total_duration() >= 0.01

    def test_profiler_disabled(self):
        """Test that disabled profiler doesn't record."""
        profiler = ExecutionProfiler(enabled=False)

        profiler.record_statement("LET", 0.01)
        profiler.record_function_call("test_func", 0.01)

        assert len(profiler.statement_counts) == 0
        assert len(profiler.function_calls) == 0

    def test_record_statement(self, profiler):
        """Test recording statement execution."""
        profiler.record_statement("LET", 0.01)
        profiler.record_statement("LET", 0.02)
        profiler.record_statement("IF", 0.03)

        assert profiler.statement_counts["LET"] == 2
        assert profiler.statement_counts["IF"] == 1
        assert len(profiler.statement_times["LET"]) == 2
        assert profiler.statement_times["LET"][0] == 0.01
        assert profiler.statement_times["LET"][1] == 0.02

    def test_record_function_call(self, profiler):
        """Test recording function calls."""
        profiler.record_function_call("func1", 0.05)
        profiler.record_function_call("func1", 0.03)
        profiler.record_function_call("func2", 0.02)

        assert profiler.function_calls["func1"] == 2
        assert profiler.function_calls["func2"] == 1
        assert sum(profiler.function_times["func1"]) == pytest.approx(0.08)

    def test_record_database_query(self, profiler):
        """Test recording database queries."""
        profiler.record_database_query(
            query="SELECT * FROM users", duration=0.025, row_count=10, params_count=0
        )

        profiler.record_database_query(
            query="SELECT * FROM orders WHERE id = ?", duration=0.015, row_count=1, params_count=1
        )

        assert len(profiler.database_queries) == 2
        assert profiler.database_queries[0]["query"] == "SELECT * FROM users"
        assert profiler.database_queries[0]["duration"] == 0.025
        assert profiler.database_queries[0]["row_count"] == 10
        assert profiler.database_queries[1]["params_count"] == 1

    def test_profile_operation_context_manager(self, profiler):
        """Test profiling operation with context manager."""
        profiler.start()

        with profiler.profile_operation("test_op", op_type="statement") as entry:
            time.sleep(0.01)

        profiler.stop()

        assert entry.name == "test_op"
        assert entry.duration >= 0.01
        assert profiler.statement_counts["test_op"] == 1

    def test_profile_operation_nesting(self, profiler):
        """Test nested profiling operations."""
        profiler.start()

        with profiler.profile_operation("parent", op_type="function"):
            time.sleep(0.005)

            with profiler.profile_operation("child1", op_type="statement"):
                time.sleep(0.005)

            with profiler.profile_operation("child2", op_type="statement"):
                time.sleep(0.005)

        profiler.stop()

        assert len(profiler.entries) == 1
        parent_entry = profiler.entries[0]
        assert parent_entry.name == "parent"
        assert len(parent_entry.children) == 2
        assert parent_entry.children[0].name == "child1"
        assert parent_entry.children[1].name == "child2"

    def test_get_hotspots(self, profiler):
        """Test getting performance hotspots."""
        profiler.record_statement("LET", 0.01)
        profiler.record_statement("FOR", 0.50)  # Slowest
        profiler.record_statement("IF", 0.05)
        profiler.record_function_call("func1", 0.30)  # Second slowest

        hotspots = profiler.get_hotspots(limit=2)

        assert len(hotspots) == 2
        assert hotspots[0][0] == "STMT:FOR"  # Slowest
        assert hotspots[0][1] == pytest.approx(0.50)
        assert hotspots[1][0] == "FUNC:func1"  # Second slowest
        assert hotspots[1][1] == pytest.approx(0.30)

    def test_get_summary(self, profiler):
        """Test getting profile summary."""
        profiler.start()

        # Record some operations
        profiler.record_statement("LET", 0.01)
        profiler.record_statement("LET", 0.02)
        profiler.record_function_call("func1", 0.05)
        profiler.record_database_query("SELECT * FROM users", 0.03, row_count=10)
        profiler.record_database_query("SELECT * FROM orders", 0.02, row_count=5)

        time.sleep(0.01)
        profiler.stop()

        summary = profiler.get_summary()

        assert summary["statement_count"] == 2
        assert summary["function_call_count"] == 1
        assert summary["database_query_count"] == 2
        assert summary["average_query_time"] == pytest.approx(0.025)
        assert summary["unique_statements"] == 1  # Only LET
        assert summary["unique_functions"] == 1  # Only func1
        assert summary["total_duration"] >= 0.01

    def test_generate_report(self, profiler):
        """Test generating profile report."""
        profiler.start()

        profiler.record_statement("LET", 0.01)
        profiler.record_function_call("test_func", 0.05)
        profiler.record_database_query("SELECT * FROM users", 0.03)

        time.sleep(0.01)
        profiler.stop()

        report = profiler.generate_report(detailed=False)

        assert "EXECUTION PROFILE REPORT" in report
        assert "Total Duration:" in report
        assert "Statements Executed:" in report
        assert "Function Calls:" in report
        assert "Database Queries:" in report
        assert "TOP 10 HOTSPOTS" in report

    def test_generate_detailed_report(self, profiler):
        """Test generating detailed profile report."""
        profiler.start()

        profiler.record_statement("LET", 0.01)
        profiler.record_statement("IF", 0.02)
        profiler.record_function_call("func1", 0.05)
        profiler.record_database_query("SELECT * FROM users", 0.03)

        profiler.stop()

        report = profiler.generate_report(detailed=True)

        assert "STATEMENT BREAKDOWN" in report
        assert "FUNCTION BREAKDOWN" in report
        assert "DATABASE QUERIES" in report
        assert "LET" in report
        assert "IF" in report
        assert "func1" in report


@pytest.mark.unit
class TestBenchmark:
    """Tests for Benchmark class."""

    def test_benchmark_initialization(self):
        """Test benchmark initialization."""
        bench = Benchmark("test_benchmark")

        assert bench.name == "test_benchmark"
        assert len(bench.results) == 0

    def test_benchmark_run(self):
        """Test running a benchmark."""
        bench = Benchmark("simple_operation")

        def operation():
            time.sleep(0.001)

        results = bench.run(operation, iterations=10)

        assert results["name"] == "simple_operation"
        assert results["iterations"] == 10
        assert results["mean"] >= 0.001
        assert results["median"] >= 0.001
        assert results["min"] > 0
        assert results["max"] > 0

    def test_benchmark_add_result(self):
        """Test manually adding benchmark results."""
        bench = Benchmark("manual_benchmark")

        bench.add_result(0.01)
        bench.add_result(0.02)
        bench.add_result(0.03)

        results = bench.get_results()

        assert results["iterations"] == 3
        assert results["mean"] == pytest.approx(0.02)
        assert results["min"] == pytest.approx(0.01)
        assert results["max"] == pytest.approx(0.03)

    def test_benchmark_compare(self):
        """Test comparing two benchmarks."""
        bench_a = Benchmark("operation_a")
        bench_a.add_result(0.01)
        bench_a.add_result(0.01)

        bench_b = Benchmark("operation_b")
        bench_b.add_result(0.02)
        bench_b.add_result(0.02)

        comparison = bench_a.compare(bench_b)

        assert comparison["benchmark_a"] == "operation_a"
        assert comparison["benchmark_b"] == "operation_b"
        assert comparison["mean_a"] == pytest.approx(0.01)
        assert comparison["mean_b"] == pytest.approx(0.02)
        assert comparison["speedup"] == pytest.approx(2.0)  # A is 2x faster
        assert comparison["faster"] == "operation_a"

    def test_benchmark_report(self):
        """Test generating benchmark report."""
        bench = Benchmark("test_operation")

        bench.add_result(0.01)
        bench.add_result(0.02)
        bench.add_result(0.03)

        report = bench.report()

        assert "Benchmark: test_operation" in report
        assert "Iterations: 3" in report
        assert "Mean:" in report
        assert "Median:" in report
        assert "Min:" in report
        assert "Max:" in report
        assert "StdDev:" in report


@pytest.mark.unit
class TestGlobalProfiler:
    """Tests for global profiler functions."""

    def test_get_profiler(self):
        """Test getting global profiler."""
        profiler = get_profiler()

        assert profiler is not None
        assert isinstance(profiler, ExecutionProfiler)

    def test_enable_disable_profiling(self):
        """Test enabling and disabling profiling."""
        disable_profiling()

        profiler = get_profiler()
        assert profiler.enabled is False

        enable_profiling()

        profiler = get_profiler()
        assert profiler.enabled is True

    def test_get_profile_report(self):
        """Test getting profile report from global profiler."""
        enable_profiling()

        profiler = get_profiler()
        profiler.record_statement("LET", 0.01)
        profiler.record_function_call("test_func", 0.02)

        report = get_profile_report(detailed=False)

        assert "EXECUTION PROFILE REPORT" in report
        assert "LET" in report or "test_func" in report


@pytest.mark.unit
class TestProfilerIntegration:
    """Integration tests for profiler with execution context."""

    def test_profiler_with_context(self):
        """Test profiler integration with execution context."""
        from src.fglinterpreter.interpreter import ExecutionContext

        profiler = ExecutionProfiler(enabled=True)
        context = ExecutionContext()

        context.set_profiler(profiler)

        assert context.has_profiler() is True
        assert context.get_profiler() is profiler

    def test_profiler_operation_tracking(self):
        """Test tracking operations with profiler."""
        profiler = ExecutionProfiler(enabled=True)
        profiler.start()

        # Simulate some operations
        with profiler.profile_operation("variable_assignment", op_type="statement"):
            time.sleep(0.001)

        with profiler.profile_operation("function_call", op_type="function"):
            time.sleep(0.002)

        with profiler.profile_operation("SELECT * FROM users", op_type="query"):
            time.sleep(0.003)

        profiler.stop()

        summary = profiler.get_summary()

        assert summary["statement_count"] == 1
        assert summary["function_call_count"] == 1
        assert summary["database_query_count"] == 1
        assert summary["total_duration"] >= 0.006


@pytest.mark.unit
class TestProfilerPerformance:
    """Tests for profiler performance overhead."""

    def test_profiler_overhead(self):
        """Test profiler overhead is minimal."""
        # With profiling (disabled) - should be very fast
        profiler_disabled = ExecutionProfiler(enabled=False)
        start = time.time()
        for _ in range(1000):
            profiler_disabled.record_statement("LET", 0.001)
        disabled_time = time.time() - start

        # With profiling (enabled) - will have overhead
        profiler_enabled = ExecutionProfiler(enabled=True)
        start = time.time()
        for _ in range(1000):
            profiler_enabled.record_statement("LET", 0.001)
        enabled_time = time.time() - start

        # Disabled profiler should be faster than enabled
        assert disabled_time < enabled_time

        # Both should complete in reasonable time (less than 1 second for 1000 ops)
        assert disabled_time < 1.0
        assert enabled_time < 1.0

    def test_profiler_memory_efficiency(self):
        """Test profiler doesn't leak memory."""

        profiler = ExecutionProfiler(enabled=True)

        # Record many operations
        for i in range(1000):
            profiler.record_statement(f"STMT_{i % 10}", 0.001)
            profiler.record_function_call(f"func_{i % 10}", 0.001)

        # Profiler should consolidate data efficiently
        assert len(profiler.statement_times) == 10  # Only 10 unique statement types
        assert len(profiler.function_times) == 10  # Only 10 unique functions
        assert sum(profiler.statement_counts.values()) == 1000
        assert sum(profiler.function_calls.values()) == 1000
