"""
Pydantic models for API request/response validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 9088
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    driver: str = "wbjdbc"
    server: Optional[str] = None  # Informix server name (mandatory for Informix)
    db_type: Optional[str] = "informix"  # Database type (informix, mysql, postgresql)


class ExecuteRequest(BaseModel):
    """Request model for code execution."""

    code: str = Field(..., min_length=1, description="4GL source code to execute")
    database_config: Optional[DatabaseConfig] = Field(
        None, description="Optional database configuration"
    )
    enable_profiling: bool = Field(False, description="Enable execution profiling")


class ExecuteResponse(BaseModel):
    """Response model for successful execution."""

    status: str = "success"
    output: str
    execution_time: float = Field(..., description="Execution time in seconds")
    profiling: Optional[Dict[str, Any]] = Field(None, description="Profiling data if enabled")


class ErrorResponse(BaseModel):
    """Response model for execution errors."""

    status: str = "error"
    error: str = Field(..., description="Error type (SyntaxError, RuntimeError, etc.)")
    message: str = Field(..., description="Human-readable error message")
    line: Optional[int] = Field(None, description="Line number where error occurred")
    column: Optional[int] = Field(None, description="Column number where error occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ParseRequest(BaseModel):
    """Request model for code parsing."""

    code: str = Field(..., min_length=1, description="4GL source code to parse")


class ParseResponse(BaseModel):
    """Response model for successful parsing."""

    status: str = "success"
    ast: Dict[str, Any] = Field(..., description="Abstract syntax tree")
    tokens: Optional[List[Dict[str, Any]]] = Field(None, description="Token list")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = "healthy"
    version: str
    interpreter_ready: bool = True
    database_drivers: List[str] = Field(default_factory=list)
    auth_enabled: bool = Field(default=False, description="Authentication enabled")


class ParseFormRequest(BaseModel):
    """Request model for .per form file parsing."""

    content: str = Field(..., min_length=1, description=".per form file content to parse")


class ParseFormResponse(BaseModel):
    """Response model for successful .per form parsing."""

    status: str = "success"
    form: Dict[str, Any] = Field(..., description="Parsed form definition")
    validation_errors: List[str] = Field(default_factory=list, description="Form validation errors")
    formonly_variables: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of formonly variables to screen fields"
    )


class ValidateCrossReferenceRequest(BaseModel):
    """Request model for cross-reference validation between .4gl and .per files."""

    fgl_code: str = Field(..., description=".4gl source code")
    per_content: str = Field(..., description=".per form file content")


class ValidateCrossReferenceResponse(BaseModel):
    """Response model for cross-reference validation."""

    status: str = "success"
    missing_in_form: List[str] = Field(
        default_factory=list, description="Variables in INPUT BY NAME but not in form"
    )
    unused_in_code: List[str] = Field(
        default_factory=list, description="Form variables not used in INPUT BY NAME"
    )
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""

    name: str = Field(..., min_length=1, description="Project name")
    description: str = Field("", description="Project description")
    mode: str = Field("local", description="File system mode (local or remote)")
    remote_config_name: Optional[str] = Field(None, description="Remote configuration name")
    remote_config: Optional[Dict[str, Any]] = Field(None, description="Remote configuration data")


class SaveProjectRequest(BaseModel):
    """Request model for saving a project as .ccp file."""

    project: Dict[str, Any] = Field(..., description="Project data")


class LoadProjectRequest(BaseModel):
    """Request model for loading a project from .ccp content."""

    content: str = Field(..., min_length=1, description=".ccp file content (JSON)")


class ProjectResponse(BaseModel):
    """Response model for project operations."""

    status: str = "success"
    project: Dict[str, Any] = Field(..., description="Project data")


class ImportFilesRequest(BaseModel):
    """Request model for importing files into the workspace."""

    files: List[Dict[str, str]] = Field(..., description="List of files with path and content")


class DiagnosticsRequest(BaseModel):
    """Request model for code diagnostics."""

    code: str = Field(..., min_length=1, description="4GL source code to analyze")


class QuickFixModel(BaseModel):
    """Model for a quick fix suggestion."""

    title: str = Field(..., description="Quick fix title/label")
    new_text: str = Field(..., description="Text to insert")
    insert_line: int = Field(..., description="Line where to insert the fix")
    insert_column: int = Field(0, description="Column where to insert the fix")
    description: Optional[str] = Field(None, description="Detailed description of the fix")


class DiagnosticModel(BaseModel):
    """Model for a diagnostic message."""

    severity: str = Field(..., description="Severity level (error, warning, info, hint)")
    message: str = Field(..., description="Diagnostic message")
    line: int = Field(..., description="Line number")
    column: int = Field(..., description="Column number")
    end_line: Optional[int] = Field(None, description="End line number")
    end_column: Optional[int] = Field(None, description="End column number")
    quick_fixes: List[QuickFixModel] = Field(
        default_factory=list, description="Suggested quick fixes"
    )


class DiagnosticsResponse(BaseModel):
    """Response model for diagnostics."""

    status: str = "success"
    diagnostics: List[DiagnosticModel] = Field(
        default_factory=list, description="List of diagnostics"
    )


class CodeActionsRequest(BaseModel):
    """Request model for code actions at a specific position."""

    code: str = Field(..., min_length=1, description="4GL source code")
    line: int = Field(..., description="Line number where action is requested")
    column: int = Field(..., description="Column number where action is requested")


class CodeActionModel(BaseModel):
    """Model for a code action."""

    title: str = Field(..., description="Action title")
    new_text: str = Field(..., description="Text to insert/replace")
    insert_line: int = Field(..., description="Line where to apply the action")
    insert_column: int = Field(0, description="Column where to apply the action")
    description: Optional[str] = Field(None, description="Action description")


class CodeActionsResponse(BaseModel):
    """Response model for code actions."""

    status: str = "success"
    actions: List[CodeActionModel] = Field(
        default_factory=list, description="Available code actions"
    )


class CompileRequest(BaseModel):
    """Request model for 4GL compilation using 4make."""

    code: Optional[str] = Field(None, description="4GL source code to compile (for single file)")
    file_path: Optional[str] = Field(None, description="Path to .4gl file to compile")
    directory: Optional[str] = Field(None, description="Directory containing 4GL files to compile")
    target_name: Optional[str] = Field(
        None, description="Target executable name (defaults to file/dir name)"
    )
    make_executable: str = Field("4make", description="Path to 4make executable")
    library_path: str = Field(
        "/test/QX/src/lib/libs_final.a", description="Path to library file to link"
    )
    keep_temp_files: bool = Field(False, description="Keep temporary files after compilation")


class CompilationMessageModel(BaseModel):
    """Model for a compilation error or warning."""

    file: str = Field(..., description="Source file name")
    line: Optional[int] = Field(None, description="Line number")
    column: Optional[int] = Field(None, description="Column number")
    severity: str = Field(..., description="Severity (error, warning, info)")
    code: Optional[str] = Field(None, description="Error code (e.g., E1234)")
    message: str = Field(..., description="Error/warning message")
    suggestion: Optional[str] = Field(None, description="Helpful suggestion to fix the issue")


class CompileResponse(BaseModel):
    """Response model for compilation."""

    status: str = "success"
    success: bool = Field(..., description="Whether compilation succeeded")
    target: str = Field(..., description="Target executable name")
    output: str = Field("", description="Compilation output")
    errors: List[CompilationMessageModel] = Field(
        default_factory=list, description="Compilation errors"
    )
    warnings: List[CompilationMessageModel] = Field(
        default_factory=list, description="Compilation warnings"
    )
    compilation_time: float = Field(0.0, description="Compilation time in seconds")
    make_def_content: str = Field("", description="Generated 4make.def content")
    error_count: int = Field(0, description="Number of errors")
    warning_count: int = Field(0, description="Number of warnings")
