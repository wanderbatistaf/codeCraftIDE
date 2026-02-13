"""
FastAPI router for database configuration and connection management.

This module provides endpoints for managing database connections in the IDE.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Try to import database connectors (may not be available in all environments)
try:
    from ..database import ConnectionConfig, WBJDBCConnector, WBORMConnector

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    ConnectionConfig = None
    WBJDBCConnector = None
    WBORMConnector = None

router = APIRouter(prefix="/api/database", tags=["database"])

# Path to store database configurations
CONFIG_DIR = Path.home() / ".fglinterpreter"
DB_CONFIG_FILE = CONFIG_DIR / "database_connections.json"


class DatabaseConfigModel(BaseModel):
    """Database connection configuration model."""

    name: str  # User-friendly name for the connection
    host: str
    port: int
    database: str
    username: str
    password: Optional[str] = ""
    driver: str = "wbjdbc"
    server: Optional[str] = None  # Informix server name
    db_type: Optional[str] = "informix"  # Database type (informix, mysql, postgresql)
    # SSH-specific fields for terminal connection (optional)
    ssh_host: Optional[str] = None  # SSH host (default: same as host)
    ssh_port: Optional[int] = None  # SSH port (default: 22)
    ssh_username: Optional[str] = None  # SSH username (default: same as username)
    ssh_password: Optional[str] = None  # SSH password (default: same as password)
    # Remote file system settings (optional)
    use_remote_files: bool = False  # Use SFTP for file operations
    remote_workspace_path: str = "~/fgl-projects"  # Remote workspace directory


class TestConnectionRequest(BaseModel):
    """Request model for testing database connection."""

    config: DatabaseConfigModel


class TestConnectionResponse(BaseModel):
    """Response model for connection test."""

    success: bool
    message: str
    error: Optional[str] = None


class SaveConfigRequest(BaseModel):
    """Request model for saving database configuration."""

    config: DatabaseConfigModel


class SaveConfigResponse(BaseModel):
    """Response model for saving configuration."""

    success: bool
    message: str


class ListConfigsResponse(BaseModel):
    """Response model for listing configurations."""

    configs: List[DatabaseConfigModel]


class DeleteConfigRequest(BaseModel):
    """Request model for deleting a configuration."""

    name: str


class DeleteConfigResponse(BaseModel):
    """Response model for deleting configuration."""

    success: bool
    message: str


def _load_configs() -> Dict[str, DatabaseConfigModel]:
    """Load database configurations from file."""
    if not DB_CONFIG_FILE.exists():
        return {}

    try:
        with open(DB_CONFIG_FILE) as f:
            data = json.load(f)
            return {name: DatabaseConfigModel(**config) for name, config in data.items()}
    except Exception as e:
        print(f"Error loading database configs: {e}")
        return {}


def _save_configs(configs: Dict[str, DatabaseConfigModel]) -> None:
    """Save database configurations to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(DB_CONFIG_FILE, "w") as f:
            data = {name: config.dict() for name, config in configs.items()}
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving database configs: {e}")
        raise


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """
    Test a database connection.

    Args:
        request: Connection configuration to test

    Returns:
        Connection test results
    """
    if not DATABASE_AVAILABLE:
        return TestConnectionResponse(
            success=False,
            message="Database drivers not available",
            error="wbjdbc or wborm not installed",
        )

    try:
        # Create connection config
        config = ConnectionConfig(
            host=request.config.host,
            port=request.config.port,
            database=request.config.database,
            username=request.config.username,
            password=request.config.password or "",
            driver=request.config.driver,
            extra_params={
                "server": request.config.server,
                "db_type": request.config.db_type or "informix",
            },
        )

        # Try to connect (use correct connector based on driver)
        if request.config.driver == "wborm":
            connector = WBORMConnector(config)
        else:
            connector = WBJDBCConnector(config)

        connector.connect()

        # Test a simple query
        try:
            # Try a simple query to verify connection works
            connector.query("SELECT 1 FROM systables WHERE tabid = 1")
            connector.disconnect()

            return TestConnectionResponse(
                success=True, message=f"Successfully connected to {request.config.database}"
            )
        except Exception as query_error:
            connector.disconnect()
            return TestConnectionResponse(
                success=True,
                message=f"Connected to {request.config.database} (query test failed: {str(query_error)})",
            )

    except Exception as e:
        return TestConnectionResponse(success=False, message="Connection failed", error=str(e))


@router.get("/configs", response_model=ListConfigsResponse)
async def list_configs():
    """
    List all saved database configurations.

    Returns:
        List of saved configurations
    """
    configs = _load_configs()

    # Add sample configuration if no configs exist
    if not configs:
        sample_config = DatabaseConfigModel(
            name="Docker Informix (Sample)",
            host="informix",
            port=9088,
            database="stores_demo",
            username="informix",
            password="in4mix",
            driver="wbjdbc",
            server="informix",
            db_type="informix",
            ssh_host="informix",  # Same as database host for Docker setup
            ssh_port=22,
            ssh_username="informix",
            ssh_password="in4mix",
        )
        configs["Docker Informix (Sample)"] = sample_config

    # Don't return passwords
    for config in configs.values():
        config.password = "***"
        if config.ssh_password:
            config.ssh_password = "***"

    return ListConfigsResponse(configs=list(configs.values()))


@router.get("/configs/{name}", response_model=DatabaseConfigModel)
async def get_config(name: str):
    """
    Get a specific database configuration with password.

    Args:
        name: Name of the configuration to retrieve

    Returns:
        Complete configuration including password
    """
    configs = _load_configs()

    if name not in configs:
        raise HTTPException(status_code=404, detail=f"Configuration '{name}' not found")

    return configs[name]


@router.post("/configs", response_model=SaveConfigResponse)
async def save_config(request: SaveConfigRequest):
    """
    Save a database configuration.

    Args:
        request: Configuration to save

    Returns:
        Save operation result
    """
    try:
        configs = _load_configs()

        # Add or update configuration
        configs[request.config.name] = request.config

        _save_configs(configs)

        return SaveConfigResponse(
            success=True, message=f"Configuration '{request.config.name}' saved successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.delete("/configs", response_model=DeleteConfigResponse)
async def delete_config(request: DeleteConfigRequest):
    """
    Delete a database configuration.

    Args:
        request: Name of configuration to delete

    Returns:
        Delete operation result
    """
    try:
        configs = _load_configs()

        if request.name not in configs:
            raise HTTPException(status_code=404, detail=f"Configuration '{request.name}' not found")

        del configs[request.name]
        _save_configs(configs)

        return DeleteConfigResponse(
            success=True, message=f"Configuration '{request.name}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")


@router.get("/drivers")
async def get_available_drivers():
    """
    Get list of available database drivers.

    Returns:
        List of available drivers and their status
    """
    import importlib.util

    drivers = {"wbjdbc": False, "wborm": False}

    if importlib.util.find_spec("wbjdbc") is not None:
        drivers["wbjdbc"] = True
    if importlib.util.find_spec("wborm") is not None:
        drivers["wborm"] = True

    return {
        "available": drivers,
        "supported_db_types": ["informix", "mysql", "postgresql"],
    }
