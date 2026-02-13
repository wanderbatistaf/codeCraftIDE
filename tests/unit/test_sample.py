"""
Sample unit tests to verify test infrastructure.

This file will be replaced with actual tests once the interpreter components are implemented.
"""

import pytest


@pytest.mark.unit
class TestSampleInfrastructure:
    """Sample tests to verify pytest configuration."""

    def test_basic_assertion(self) -> None:
        """Test basic assertion works."""
        assert True

    def test_basic_arithmetic(self) -> None:
        """Test basic arithmetic operations."""
        assert 1 + 1 == 2
        assert 10 - 5 == 5
        assert 3 * 4 == 12
        assert 10 / 2 == 5

    def test_string_operations(self) -> None:
        """Test basic string operations."""
        assert "hello".upper() == "HELLO"
        assert "WORLD".lower() == "world"
        assert "hello world".split() == ["hello", "world"]

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            (0, False),
            (1, True),
            (-1, True),
            (100, True),
        ],
    )
    def test_parametrized(self, input_value: int, expected: bool) -> None:
        """Test parametrized test fixture."""
        assert bool(input_value) == expected


@pytest.mark.unit
class TestFixtures:
    """Test that fixtures are working correctly."""

    def test_sample_4gl_code_fixture(self, sample_4gl_code: str) -> None:
        """Test sample 4GL code fixture."""
        assert isinstance(sample_4gl_code, str)
        assert "MAIN" in sample_4gl_code
        assert "END MAIN" in sample_4gl_code

    def test_sample_4gl_with_loop_fixture(self, sample_4gl_with_loop: str) -> None:
        """Test sample 4GL loop fixture."""
        assert isinstance(sample_4gl_with_loop, str)
        assert "FOR" in sample_4gl_with_loop
        assert "END FOR" in sample_4gl_with_loop

    def test_sample_4gl_with_sql_fixture(self, sample_4gl_with_sql: str) -> None:
        """Test sample 4GL SQL fixture."""
        assert isinstance(sample_4gl_with_sql, str)
        assert "SELECT" in sample_4gl_with_sql
        assert "FROM" in sample_4gl_with_sql

    def test_temp_4gl_file_fixture(self, temp_4gl_file: pytest.fixture) -> None:
        """Test temporary 4GL file fixture."""
        assert temp_4gl_file.exists()
        assert temp_4gl_file.suffix == ".4gl"
        content = temp_4gl_file.read_text()
        assert "MAIN" in content

    def test_mock_env_config_fixture(self, mock_env_config: dict[str, str]) -> None:
        """Test mock environment configuration fixture."""
        assert isinstance(mock_env_config, dict)
        assert "LOG_LEVEL" in mock_env_config
        assert "DEBUG" in mock_env_config
        assert mock_env_config["TEST_MODE"] == "true"


@pytest.mark.unit
def test_imports_work() -> None:
    """Test that basic Python imports work."""
    import sys
    from pathlib import Path

    assert sys.version_info >= (3, 9)
    assert Path(__file__).exists()
