"""
FastAPI application for fglInterpreter IDE backend.

This API provides endpoints for executing, parsing, and validating 4GL code.
"""

import importlib.util
import os
import time
from typing import Optional, Union

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..analyzer import StaticAnalyzer
from ..cross_reference import validate_fgl_per_binding
from ..interpreter import ExecutionContext, Interpreter
from ..interpreter.exceptions import RuntimeError as InterpreterRuntimeError
from ..lexer.exceptions import LexerError
from ..parser import parse_source
from ..parser.exceptions import ParserError
from ..per_parser import parse_per_file, serialize_form_definition
from ..profiler import ExecutionProfiler
from ..project import CodeCraftProject, create_project

# Auth imports
from .auth.config import auth_config
from .auth.core.permissions import Permission
from .auth.database import init_auth_database
from .auth.dependencies.auth_deps import get_current_user_optional
from .auth.models import CurrentUser
from .auth.routers import auth_router, users_router

# Try to import database connectors (may not be available in all environments)
try:
    from ..database import ConnectionConfig, WBJDBCConnector, WBORMConnector

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    ConnectionConfig = None
    WBJDBCConnector = None
    WBORMConnector = None

# Import routers
from .conversion import router as conversion_router
from .database import router as database_router
from .database_schema import router as database_schema_router
from .files import router as files_router
from .lycia import router as lycia_router
from .models import (
    CodeActionModel,
    CodeActionsRequest,
    CodeActionsResponse,
    CompilationMessageModel,
    CompileRequest,
    CompileResponse,
    CreateProjectRequest,
    DiagnosticModel,
    DiagnosticsRequest,
    DiagnosticsResponse,
    ErrorResponse,
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    ImportFilesRequest,
    LoadProjectRequest,
    ParseFormRequest,
    ParseFormResponse,
    ParseRequest,
    ParseResponse,
    ProjectResponse,
    QuickFixModel,
    SaveProjectRequest,
    ValidateCrossReferenceRequest,
    ValidateCrossReferenceResponse,
)
from .sftp import router as sftp_router
from .sql_query import router as sql_query_router
from .terminal import router as terminal_router

# Create FastAPI app
app = FastAPI(
    title="fglInterpreter API",
    description="Backend API for the fglInterpreter ReactJS IDE",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
if cors_origins_env:
    cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    cors_origins = [
        "http://localhost:5173",  # Vite (old IDE)
        "http://localhost:3000",  # CRA
        "http://localhost:9002",  # Studio IDE
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversion_router)
app.include_router(database_router)
app.include_router(database_schema_router)
app.include_router(files_router)
app.include_router(terminal_router)
app.include_router(sftp_router)
app.include_router(sql_query_router)
app.include_router(lycia_router)

# Include auth routers if authentication is enabled
if auth_config.enabled:
    app.include_router(auth_router.router)
    app.include_router(users_router.router)


# Startup event to initialize auth database
@app.on_event("startup")
async def startup_event():
    """Initialize authentication database on startup."""
    if auth_config.enabled:
        init_auth_database()


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns the API status, version, and available features.
    """
    # Check available database drivers
    drivers = []
    if importlib.util.find_spec("wbjdbc") is not None:
        drivers.append("wbjdbc")
    if importlib.util.find_spec("wborm") is not None:
        drivers.append("wborm")

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        interpreter_ready=True,
        database_drivers=drivers,
        auth_enabled=auth_config.enabled,
    )


@app.post("/api/execute", response_model=Union[ExecuteResponse, ErrorResponse])
async def execute_code(
    request: ExecuteRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """
    Execute 4GL code and return the output.

    Requires EXECUTE_CODE permission (Developer or Admin role).

    Args:
        request: Execution request with code and optional database config
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Execution results with output, timing, and profiling data

    Raises:
        HTTPException: If execution fails or user lacks permission
    """
    # Check permissions if auth is enabled
    if auth_config.enabled and current_user:
        from .auth.core.permissions import has_permission

        if not has_permission(current_user.role, Permission.EXECUTE_CODE):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Required permission: execute_code",
            )
    elif auth_config.enabled and not current_user:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")

    start_time = time.time()

    try:
        # Create execution context
        context = ExecutionContext()

        # Set up database connector if config provided
        if request.database_config:
            if not DATABASE_AVAILABLE:
                return ErrorResponse(
                    error="DatabaseNotAvailable",
                    message="Database connectors are not available in this environment. Install wbjdbc or wborm to enable database features.",
                    details={"requested_driver": request.database_config.driver},
                )

            try:
                db_config = ConnectionConfig(
                    host=request.database_config.host,
                    port=request.database_config.port,
                    database=request.database_config.database,
                    username=request.database_config.username,
                    password=request.database_config.password,
                    driver=request.database_config.driver,
                    extra_params={
                        "server": request.database_config.server,
                        "db_type": request.database_config.db_type or "informix",
                    },
                )

                # Create connector (wbjdbc or wborm based on driver)
                if db_config.driver == "wborm":
                    connector = WBORMConnector(db_config)
                else:
                    # Default to wbjdbc
                    connector = WBJDBCConnector(db_config)

                connector.connect()
                context.set_database_connector(connector)

            except Exception as e:
                return ErrorResponse(
                    error="DatabaseConnectionError",
                    message=f"Failed to connect to database: {str(e)}",
                    details={"config": request.database_config.dict()},
                )

        # Set up profiler if requested
        profiler = None
        if request.enable_profiling:
            profiler = ExecutionProfiler(enabled=True)
            profiler.start()
            context.set_profiler(profiler)

        # Parse the code
        try:
            ast = parse_source(request.code, filename="<ide>")
        except LexerError as e:
            return ErrorResponse(
                error="LexerError",
                message=str(e),
                line=getattr(e, "line", None),
                column=getattr(e, "column", None),
            )
        except ParserError as e:
            return ErrorResponse(
                error="ParserError",
                message=str(e),
                line=getattr(e, "line", None),
                column=getattr(e, "column", None),
            )

        # Execute the code
        try:
            interpreter = Interpreter(context)
            output = interpreter.execute(ast)

            execution_time = time.time() - start_time

            # Stop profiler and get data
            profiling_data = None
            if profiler:
                profiler.stop()
                profiling_data = {
                    "total_duration": profiler.total_duration(),
                    "statement_count": len(profiler.entries),
                    "hotspots": [
                        {"name": name, "time": total_time, "calls": calls}
                        for name, total_time, calls in profiler.get_hotspots(limit=10)
                    ],
                }

            return ExecuteResponse(
                output=output,
                execution_time=execution_time,
                profiling=profiling_data,
            )

        except InterpreterRuntimeError as e:
            return ErrorResponse(
                error="RuntimeError",
                message=str(e),
                line=getattr(e.node, "line", None) if hasattr(e, "node") else None,
                column=getattr(e.node, "column", None) if hasattr(e, "node") else None,
            )

        finally:
            # Clean up database connection
            if request.database_config and context.has_database_connector():
                connector = context.get_database_connector()
                if connector and connector.is_connected():
                    connector.disconnect()

    except Exception as e:
        # Catch-all for unexpected errors
        return ErrorResponse(
            error="UnexpectedError",
            message=f"An unexpected error occurred: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/parse", response_model=Union[ParseResponse, ErrorResponse])
async def parse_code(request: ParseRequest):
    """
    Parse 4GL code and return the AST.

    Args:
        request: Parse request with code

    Returns:
        AST and token information

    Raises:
        HTTPException: If parsing fails
    """
    try:
        # Parse the code
        ast = parse_source(request.code, filename="<ide>")

        # Convert AST to dictionary
        ast_dict = ast.to_dict()

        return ParseResponse(
            ast=ast_dict,
            tokens=None,  # Could add tokenization if needed
        )

    except LexerError as e:
        return ErrorResponse(
            error="LexerError",
            message=str(e),
            line=getattr(e, "line", None),
            column=getattr(e, "column", None),
        )
    except ParserError as e:
        return ErrorResponse(
            error="ParserError",
            message=str(e),
            line=getattr(e, "line", None),
            column=getattr(e, "column", None),
        )
    except Exception as e:
        return ErrorResponse(
            error="UnexpectedError",
            message=f"An unexpected error occurred: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/parse-form", response_model=Union[ParseFormResponse, ErrorResponse])
async def parse_form(request: ParseFormRequest):
    """
    Parse a .per form file and return its structure.

    Args:
        request: Parse form request with .per file content

    Returns:
        Parsed form definition with screen layout, attributes, and validation

    Raises:
        HTTPException: If parsing fails
    """
    try:
        # Parse the .per file
        form_def = parse_per_file(request.content)

        # Serialize to dictionary
        form_dict = serialize_form_definition(form_def)

        # Get formonly variables mapping
        formonly_vars = form_def.get_formonly_variables()

        # Validate the form
        validation_errors = form_def.validate()

        return ParseFormResponse(
            form=form_dict,
            formonly_variables=formonly_vars,
            validation_errors=validation_errors,
        )

    except Exception as e:
        return ErrorResponse(
            error="FormParseError",
            message=f"Failed to parse .per form file: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post(
    "/api/validate-cross-reference",
    response_model=Union[ValidateCrossReferenceResponse, ErrorResponse],
)
async def validate_cross_reference(request: ValidateCrossReferenceRequest):
    """
    Validate cross-references between .4gl code and .per form file.

    Checks that:
    - Variables in INPUT BY NAME exist in the form
    - Form variables are used in the code

    Args:
        request: Validation request with .4gl and .per content

    Returns:
        Validation results with any mismatches

    Raises:
        HTTPException: If validation fails
    """
    try:
        results = validate_fgl_per_binding(request.fgl_code, request.per_content)

        return ValidateCrossReferenceResponse(
            missing_in_form=results.get("missing_in_form", []),
            unused_in_code=results.get("unused_in_code", []),
            warnings=results.get("warnings", []),
        )

    except Exception as e:
        return ErrorResponse(
            error="ValidationError",
            message=f"Failed to validate cross-references: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/project/create", response_model=Union[ProjectResponse, ErrorResponse])
async def create_new_project(request: CreateProjectRequest):
    """
    Create a new CodeCraft project.

    Creates a clean workspace with:
    - A folder named after the project
    - A main file: project_name.4gl

    Args:
        request: Project creation request with name, description, and mode information

    Returns:
        New project data

    Raises:
        HTTPException: If project creation fails
    """
    try:
        # Import file tree utilities
        from .files import FileNode, load_file_tree, save_file_tree
        from .sftp import _create_sftp_client

        # Create project
        project = create_project(name=request.name, description=request.description)

        # Define file contents
        main_file_content = f"""MAIN
    -- {request.description or 'Main program'}

    DISPLAY "Welcome to {request.name}!"

END MAIN
"""

        global_file_content = """-- Global definitions
-- This file contains global variables, constants, and type definitions

-- Example global variables:
-- DEFINE g_user_name STRING
-- DEFINE g_company_id INTEGER

-- Example constants:
-- CONSTANT TRUE = 1
-- CONSTANT FALSE = 0
"""

        per_file_content = f"""DATABASE template

SCREEN
{{
    {request.name.upper()}

    [field1                ]  [field2                ]
    [field3                ]  [field4                ]
}}
END

ATTRIBUTES
    field1 = formonly.field1;
    field2 = formonly.field2;
    field3 = formonly.field3;
    field4 = formonly.field4;
END

INSTRUCTIONS
    SCREEN RECORD sc_{request.name}[1]
END
"""

        # Check if we're in remote mode
        if request.mode == "remote" and request.remote_config_name and request.remote_config:
            # Create project structure via SFTP

            # Create SFTP client
            ssh_client = _create_sftp_client(request.remote_config)
            sftp = ssh_client.open_sftp()

            try:
                # Get workspace path from config (e.g., ~/fgl-projects)
                workspace_path = request.remote_config.get(
                    "remote_workspace_path", "~/fgl-projects"
                )

                # Expand ~ to home directory if needed
                if workspace_path.startswith("~/"):
                    stdin, stdout, stderr = ssh_client.exec_command("pwd")
                    home_dir = stdout.read().decode().strip()
                    workspace_path = workspace_path.replace("~", home_dir)

                # Ensure workspace directory exists
                try:
                    sftp.stat(workspace_path)
                except OSError:
                    # Workspace doesn't exist, create it
                    sftp.mkdir(workspace_path)

                project_path = f"{workspace_path}/{request.name}"

                # Create project directory
                try:
                    sftp.mkdir(project_path)
                except OSError:
                    # Directory might already exist, that's okay
                    pass

                # Create main.4gl file
                main_file_path = f"{project_path}/{request.name}.4gl"
                with sftp.open(main_file_path, "w") as f:
                    f.write(main_file_content)

                # Create global.4gl file
                global_file_path = f"{project_path}/global.4gl"
                with sftp.open(global_file_path, "w") as f:
                    f.write(global_file_content)

                # Create .per file
                per_file_path = f"{project_path}/{request.name}.per"
                with sftp.open(per_file_path, "w") as f:
                    f.write(per_file_content)

            finally:
                sftp.close()
                ssh_client.close()

            # Set IDE state to open main file (using absolute path for remote)
            project.ide_state.open_tabs = [f"{project_path}/{request.name}.4gl"]
            project.ide_state.active_tab = f"{project_path}/{request.name}.4gl"

            # For expanded folders, use relative path (project name) for file tree ID matching
            # File tree IDs are based on relative paths from workspace, so "Teste" not absolute path
            project.ide_state.expanded_folders = ["root", request.name]

        else:
            # Local mode - use existing file tree logic
            # Load existing workspace and add project to it (don't replace!)
            workspace_root = load_file_tree()

            # Create project folder
            project_folder = FileNode(
                id=request.name,
                name=request.name,
                type="folder",
                path=f"/{request.name}",
                children=[],
            )

            main_file = FileNode(
                id=f"{request.name}/{request.name}.4gl",
                name=f"{request.name}.4gl",
                type="file",
                path=f"/{request.name}/{request.name}.4gl",
                content=main_file_content,
            )

            global_file = FileNode(
                id=f"{request.name}/global.4gl",
                name="global.4gl",
                type="file",
                path=f"/{request.name}/global.4gl",
                content=global_file_content,
            )

            per_file = FileNode(
                id=f"{request.name}/{request.name}.per",
                name=f"{request.name}.per",
                type="file",
                path=f"/{request.name}/{request.name}.per",
                content=per_file_content,
            )

            # Build structure with all files
            project_folder.children = [main_file, global_file, per_file]
            # Sort: files alphabetically
            project_folder.children.sort(key=lambda n: n.name.lower())

            # Add project folder to existing workspace (preserve examples!)
            workspace_root.children.append(project_folder)

            # Sort workspace folders
            workspace_root.children.sort(key=lambda n: (n.type != "folder", n.name.lower()))

            # Save updated workspace
            save_file_tree(workspace_root)

            # Set IDE state to open main file
            project.ide_state.open_tabs = [f"/{request.name}/{request.name}.4gl"]
            project.ide_state.active_tab = f"/{request.name}/{request.name}.4gl"
            project.ide_state.expanded_folders = ["root", request.name]

        # Add files to project metadata (same for both modes)
        project.add_file(
            path=f"{request.name}.4gl",
            content=main_file_content,
            file_type="4gl",
        )
        project.add_file(
            path="global.4gl",
            content=global_file_content,
            file_type="4gl",
        )
        project.add_file(
            path=f"{request.name}.per",
            content=per_file_content,
            file_type="per",
        )

        return ProjectResponse(project=project.to_dict())

    except Exception as e:
        return ErrorResponse(
            error="ProjectCreationError",
            message=f"Failed to create project: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/project/load", response_model=Union[ProjectResponse, ErrorResponse])
async def load_project(request: LoadProjectRequest):
    """
    Load a CodeCraft project from .ccp file content.

    Args:
        request: Load project request with .ccp file content (compressed base64 or JSON)

    Returns:
        Loaded project data

    Raises:
        HTTPException: If project loading fails
    """
    try:
        import base64

        # Try to load as compressed format first
        try:
            # Decode from base64
            ccp_bytes = base64.b64decode(request.content)
            project = CodeCraftProject.from_ccp_bytes(ccp_bytes)
        except Exception:
            # Fall back to plain JSON format (backward compatibility)
            project = CodeCraftProject.from_json(request.content)

        return ProjectResponse(project=project.to_dict())

    except Exception as e:
        return ErrorResponse(
            error="ProjectLoadError",
            message=f"Failed to load project: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/project/save", response_model=Union[dict, ErrorResponse])
async def save_project(request: SaveProjectRequest):
    """
    Convert project data to .ccp file content.

    Args:
        request: Save project request with project data

    Returns:
        .ccp file content as compressed base64 string

    Raises:
        HTTPException: If project saving fails
    """
    try:
        import base64

        project = CodeCraftProject.from_dict(request.project)

        # Create compressed, encoded .ccp content
        ccp_bytes = project.to_ccp_bytes()
        ccp_content = base64.b64encode(ccp_bytes).decode("utf-8")

        return {
            "status": "success",
            "content": ccp_content,
            "filename": f"{project.name}.ccp",
        }

    except Exception as e:
        return ErrorResponse(
            error="ProjectSaveError",
            message=f"Failed to save project: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/files/import")
async def import_files(request: ImportFilesRequest):
    """
    Import files into the workspace.

    Args:
        request: Import files request with file data

    Returns:
        Success status

    Raises:
        HTTPException: If import fails
    """
    try:
        # This endpoint will be used by the frontend to upload files
        # The actual file writing is handled by the files router
        return {
            "status": "success",
            "imported": len(request.files),
            "message": f"Successfully imported {len(request.files)} file(s)",
        }

    except Exception as e:
        return ErrorResponse(
            error="ImportError",
            message=f"Failed to import files: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/diagnostics", response_model=Union[DiagnosticsResponse, ErrorResponse])
async def get_diagnostics(request: DiagnosticsRequest):
    """
    Analyze code and return diagnostics (errors, warnings, etc.).

    This endpoint performs static analysis on the provided code without executing it.
    It detects:
    - Undefined variables
    - Type mismatches
    - Other potential issues

    For each diagnostic, it provides quick fix suggestions.
    """
    try:
        # Parse the code
        ast = parse_source(request.code)

        # Run static analysis
        analyzer = StaticAnalyzer()
        diagnostics = analyzer.analyze(ast)

        # Convert diagnostics to response models
        diagnostic_models = []
        for diag in diagnostics:
            quick_fixes = [
                QuickFixModel(
                    title=qf.title,
                    new_text=qf.new_text,
                    insert_line=qf.insert_line,
                    insert_column=qf.insert_column,
                    description=qf.description,
                )
                for qf in diag.quick_fixes
            ]

            diagnostic_models.append(
                DiagnosticModel(
                    severity=diag.severity.value,
                    message=diag.message,
                    line=diag.line,
                    column=diag.column,
                    end_line=diag.end_line,
                    end_column=diag.end_column,
                    quick_fixes=quick_fixes,
                )
            )

        return DiagnosticsResponse(diagnostics=diagnostic_models)

    except LexerError as e:
        return ErrorResponse(
            error="LexerError",
            message=str(e),
            line=e.line if hasattr(e, "line") else None,
            column=e.column if hasattr(e, "column") else None,
        )
    except ParserError as e:
        return ErrorResponse(
            error="ParserError",
            message=str(e),
            line=e.line if hasattr(e, "line") else None,
            column=e.column if hasattr(e, "column") else None,
        )
    except Exception as e:
        return ErrorResponse(
            error="AnalysisError",
            message=f"Failed to analyze code: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/code-actions", response_model=Union[CodeActionsResponse, ErrorResponse])
async def get_code_actions(request: CodeActionsRequest):
    """
    Get available code actions (quick fixes) at a specific position.

    This endpoint returns context-specific quick fixes for the code at the
    given line and column position.
    """
    try:
        # Parse the code
        ast = parse_source(request.code)

        # Run static analysis
        analyzer = StaticAnalyzer()
        diagnostics = analyzer.analyze(ast)

        # Find diagnostics at the requested position
        actions = []
        for diag in diagnostics:
            # Check if diagnostic is at the requested position
            if diag.line == request.line:
                # Add all quick fixes from this diagnostic as actions
                for qf in diag.quick_fixes:
                    actions.append(
                        CodeActionModel(
                            title=qf.title,
                            new_text=qf.new_text,
                            insert_line=qf.insert_line,
                            insert_column=qf.insert_column,
                            description=qf.description,
                        )
                    )

        return CodeActionsResponse(actions=actions)

    except LexerError as e:
        return ErrorResponse(
            error="LexerError",
            message=str(e),
            line=e.line if hasattr(e, "line") else None,
            column=e.column if hasattr(e, "column") else None,
        )
    except ParserError as e:
        return ErrorResponse(
            error="ParserError",
            message=str(e),
            line=e.line if hasattr(e, "line") else None,
            column=e.column if hasattr(e, "column") else None,
        )
    except Exception as e:
        return ErrorResponse(
            error="AnalysisError",
            message=f"Failed to get code actions: {str(e)}",
            details={"type": type(e).__name__},
        )


@app.post("/api/compile", response_model=Union[CompileResponse, ErrorResponse])
async def compile_code(
    request: CompileRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """
    Compile 4GL code using 4make.

    Requires COMPILE_CODE permission (Developer or Admin role).

    Supports three modes:
    1. Compile from code string (creates temporary file)
    2. Compile from file path
    3. Compile entire directory

    Args:
        request: Compilation request
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Compilation results with errors, warnings, and output

    Raises:
        HTTPException: If compilation setup fails or user lacks permission
    """
    # Check permissions if auth is enabled
    if auth_config.enabled and current_user:
        from .auth.core.permissions import has_permission

        if not has_permission(current_user.role, Permission.COMPILE_CODE):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Required permission: compile_code",
            )
    elif auth_config.enabled and not current_user:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        import tempfile
        from pathlib import Path

        from ..compiler import CompilerNotFoundError, FourMakeCompiler

        # Validate request
        if not any([request.code, request.file_path, request.directory]):
            return ErrorResponse(
                error="InvalidRequest",
                message="Must provide either 'code', 'file_path', or 'directory'",
            )

        # Initialize compiler
        try:
            compiler = FourMakeCompiler(
                make_executable=request.make_executable,
                library_path=request.library_path,
                keep_temp_files=request.keep_temp_files,
            )
        except CompilerNotFoundError as e:
            return ErrorResponse(
                error="CompilerNotFound",
                message=str(e),
                details={
                    "make_executable": request.make_executable,
                    "suggestion": "Ensure 4make is installed and accessible in your PATH",
                },
            )

        # Perform compilation based on request type
        result = None

        if request.code:
            # Compile from code string
            temp_dir = Path(tempfile.mkdtemp(prefix="4make_compile_"))
            try:
                target_name = request.target_name or "program"
                temp_file = temp_dir / f"{target_name}.4gl"
                temp_file.write_text(request.code, encoding="utf-8")

                result = compiler.compile_file(temp_file, target_name=target_name)

            finally:
                if not request.keep_temp_files and temp_dir.exists():
                    import shutil

                    shutil.rmtree(temp_dir, ignore_errors=True)

        elif request.file_path:
            # Compile from file path
            file_path = Path(request.file_path)
            if not file_path.exists():
                return ErrorResponse(
                    error="FileNotFound",
                    message=f"Source file not found: {request.file_path}",
                )

            result = compiler.compile_file(file_path, target_name=request.target_name)

        elif request.directory:
            # Compile directory
            directory = Path(request.directory)
            if not directory.exists() or not directory.is_dir():
                return ErrorResponse(
                    error="DirectoryNotFound",
                    message=f"Directory not found: {request.directory}",
                )

            result = compiler.compile_directory(directory, target_name=request.target_name)

        # Convert result to response model
        error_models = [
            CompilationMessageModel(
                file=err.file,
                line=err.line,
                column=err.column,
                severity=err.severity,
                code=err.code,
                message=err.message,
                suggestion=err.suggestion,
            )
            for err in result.errors
        ]

        warning_models = [
            CompilationMessageModel(
                file=warn.file,
                line=warn.line,
                column=warn.column,
                severity=warn.severity,
                code=warn.code,
                message=warn.message,
                suggestion=warn.suggestion,
            )
            for warn in result.warnings
        ]

        return CompileResponse(
            success=result.success,
            target=result.target,
            output=result.output,
            errors=error_models,
            warnings=warning_models,
            compilation_time=result.compilation_time,
            make_def_content=result.make_def_content,
            error_count=result.error_count,
            warning_count=result.warning_count,
        )

    except Exception as e:
        return ErrorResponse(
            error="CompilationError",
            message=f"Compilation failed: {str(e)}",
            details={"type": type(e).__name__},
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "fglInterpreter API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
