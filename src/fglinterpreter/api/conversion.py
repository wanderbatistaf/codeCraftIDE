"""
Conversion assistance API endpoints for assisted 4GL → Python conversion.

Provides endpoints for real-time conversion with custom configuration,
configuration persistence, and mapping management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/conversion", tags=["conversion"])


class ConversionRequest(BaseModel):
    """Request model for code conversion."""

    source: str
    config: Optional[Dict] = None


class ConversionResponse(BaseModel):
    """Response model for code conversion."""

    python: str
    warnings: List[str]
    lineMapping: Dict[int, int]  # 4GL line → Python line mapping


class ConversionConfig(BaseModel):
    """Configuration model for conversion customization."""

    variableNameMappings: Dict[str, str] = {}
    typeOverrides: Dict[str, str] = {}
    sqlBackend: str = "wbjdbc"
    formatCode: bool = True
    lineLength: int = 88


@router.post("/convert", response_model=ConversionResponse)
async def convert_code(request: ConversionRequest):
    """
    Convert 4GL code to Python with custom configuration.

    This endpoint provides real-time conversion with support for:
    - Variable name overrides
    - Type hint customization
    - SQL backend selection
    - Code formatting options

    Args:
        request: ConversionRequest with source code and optional config

    Returns:
        ConversionResponse with converted Python code and warnings

    Raises:
        HTTPException: If conversion fails
    """
    from ..converter import convert_source

    # Parse configuration
    config = ConversionConfig(**(request.config or {}))

    try:
        # Convert with custom configuration
        python_code = convert_source(
            source_code=request.source,
            format_code=config.formatCode,
            line_length=config.lineLength,
            sql_backend=config.sqlBackend,
        )

        # Apply variable name mappings (post-processing)
        if config.variableNameMappings:
            for old_name, new_name in config.variableNameMappings.items():
                python_code = python_code.replace(f"{old_name}:", f"{new_name}:")
                python_code = python_code.replace(f" {old_name} ", f" {new_name} ")

        # Apply type overrides (post-processing)
        if config.typeOverrides:
            for var_name, type_hint in config.typeOverrides.items():
                # Replace type hints
                python_code = python_code.replace(f"{var_name}: int", f"{var_name}: {type_hint}")
                python_code = python_code.replace(f"{var_name}: str", f"{var_name}: {type_hint}")
                python_code = python_code.replace(f"{var_name}: float", f"{var_name}: {type_hint}")

        # Extract warnings (TODO comments)
        warnings = []
        for line in python_code.split("\n"):
            if "# TODO:" in line:
                warnings.append(line.strip())

        # TODO: Generate line mapping (4GL line → Python line)
        line_mapping = {}

        return ConversionResponse(python=python_code, warnings=warnings, lineMapping=line_mapping)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


@router.get("/config", response_model=ConversionConfig)
async def get_config():
    """
    Get current conversion configuration.

    Loads configuration from .fglinterpreter/conversion-config.json
    or returns default configuration if file doesn't exist.

    Returns:
        ConversionConfig with current settings
    """
    config_file = Path(".fglinterpreter/conversion-config.json")

    if config_file.exists():
        try:
            config_data = json.loads(config_file.read_text())
            return ConversionConfig(**config_data)
        except Exception:
            # Return default config if file is corrupted
            return ConversionConfig()
    else:
        return ConversionConfig()


@router.post("/config")
async def save_config(config: ConversionConfig):
    """
    Save conversion configuration to file.

    Persists configuration to .fglinterpreter/conversion-config.json
    for use in future conversions.

    Args:
        config: ConversionConfig to save

    Returns:
        Status message
    """
    try:
        config_dir = Path(".fglinterpreter")
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "conversion-config.json"
        config_file.write_text(config.json(indent=2))

        return {"status": "saved", "file": str(config_file)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/mappings")
async def get_mappings():
    """
    Get available type and function mappings.

    Provides a reference of available mappings for the UI to display.

    Returns:
        Dictionary with available types, SQL backends, and function mappings
    """
    return {
        "types": {
            "INTEGER": "int",
            "SMALLINT": "int",
            "FLOAT": "float",
            "DECIMAL": "float",
            "DECIMAL(p,s)": "Decimal",
            "CHAR": "str",
            "VARCHAR": "str",
            "DATE": "datetime.date",
            "DATETIME": "datetime.datetime",
            "MONEY": "Decimal",
        },
        "sqlBackends": [
            {"value": "wbjdbc", "label": "wbjdbc (Direct SQL)"},
            {"value": "wborm", "label": "wborm (ORM-style)"},
        ],
        "functions": {
            "TODAY": "datetime.date.today()",
            "CURRENT": "datetime.datetime.now()",
            "LENGTH": "len()",
            "UPSHIFT": "upper()",
            "DOWNSHIFT": "lower()",
        },
    }


class ReverseConversionRequest(BaseModel):
    """Request model for Python to 4GL conversion."""

    python_code: str


class ReverseConversionResponse(BaseModel):
    """Response model for Python to 4GL conversion."""

    fgl_code: str
    warnings: List[str]


@router.post("/reverse", response_model=ReverseConversionResponse)
async def convert_python_to_fgl(request: ReverseConversionRequest):
    """
    Convert Python code back to 4GL.

    This is a basic implementation that works primarily for Python code
    generated by the 4GL to Python converter.

    Args:
        request: ReverseConversionRequest with Python source code

    Returns:
        ReverseConversionResponse with converted 4GL code

    Raises:
        HTTPException: If conversion fails
    """
    from ..converter import convert_python_to_4gl

    try:
        fgl_code = convert_python_to_4gl(request.python_code)

        warnings = []
        if "???" in fgl_code:
            warnings.append("Some Python constructs could not be converted to 4GL")

        return ReverseConversionResponse(fgl_code=fgl_code, warnings=warnings)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reverse conversion failed: {str(e)}")
