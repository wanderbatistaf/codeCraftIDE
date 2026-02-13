"""
Pytest configuration and shared fixtures for fglInterpreter tests.
"""

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture(scope="session")
def project_root_dir() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def examples_dir(project_root_dir: Path) -> Path:
    """Return the examples directory."""
    return project_root_dir / "examples"


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the test data directory."""
    test_dir = Path(__file__).parent
    data_dir = test_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_4gl_code() -> str:
    """Return a simple 4GL code snippet for testing."""
    return """
MAIN
    DEFINE x, y INTEGER

    LET x = 10
    LET y = 20

    IF x < y THEN
        DISPLAY "x is less than y"
    ELSE
        DISPLAY "x is greater than or equal to y"
    END IF

END MAIN
""".strip()


@pytest.fixture
def sample_4gl_with_loop() -> str:
    """Return a 4GL code snippet with a loop for testing."""
    return """
MAIN
    DEFINE i INTEGER

    FOR i = 1 TO 10
        DISPLAY "Count: ", i
    END FOR

END MAIN
""".strip()


@pytest.fixture
def sample_4gl_with_sql() -> str:
    """Return a 4GL code snippet with SQL for testing."""
    return """
MAIN
    DEFINE cust_name CHAR(50)
    DEFINE cust_id INTEGER

    SELECT customer_name, customer_id
        INTO cust_name, cust_id
        FROM customers
        WHERE customer_id = 1

    DISPLAY "Customer: ", cust_name

END MAIN
""".strip()


@pytest.fixture
def temp_4gl_file(tmp_path: Path, sample_4gl_code: str) -> Generator[Path, None, None]:
    """Create a temporary 4GL file for testing."""
    file_path = tmp_path / "test_script.4gl"
    file_path.write_text(sample_4gl_code)
    yield file_path
    # Cleanup is automatic with tmp_path


@pytest.fixture
def mock_env_config(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up mock environment configuration for testing."""
    config = {
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true",
        "STRICT_MODE": "false",
        "ENABLE_AST_CACHE": "false",
        "TEST_MODE": "true",
    }

    for key, value in config.items():
        monkeypatch.setenv(key, value)

    return config


# Test markers
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests that don't require external dependencies")
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require database or external services"
    )
    config.addinivalue_line("markers", "slow: Tests that take significant time to run")
    config.addinivalue_line("markers", "database: Tests that require database connection")


# Skip database tests if no database is configured
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test collection based on markers and configuration."""
    skip_db = pytest.mark.skip(reason="Database not configured (TEST_MODE=true)")
    skip_integration = pytest.mark.skip(reason="Integration tests skipped in unit test mode")

    # Check if we're in test mode (no real database)
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    unit_only = config.getoption("-m") == "unit"

    for item in items:
        # Skip database tests in test mode
        if test_mode and "database" in item.keywords:
            item.add_marker(skip_db)

        # Skip integration tests when running unit tests only
        if unit_only and "integration" in item.keywords:
            item.add_marker(skip_integration)
