"""
Compiler-specific exceptions for 4make integration.
"""


class CompilerError(Exception):
    """Base exception for compiler errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CompilationError(CompilerError):
    """Raised when compilation fails."""

    def __init__(
        self,
        message: str,
        errors: list = None,
        warnings: list = None,
        details: dict = None,
    ):
        super().__init__(message, details)
        self.errors = errors or []
        self.warnings = warnings or []


class MakeDefGenerationError(CompilerError):
    """Raised when 4make.def generation fails."""

    pass


class CompilerNotFoundError(CompilerError):
    """Raised when 4make executable is not found."""

    pass


class CompilerExecutionError(CompilerError):
    """Raised when 4make execution fails."""

    def __init__(self, message: str, return_code: int = None, details: dict = None):
        super().__init__(message, details)
        self.return_code = return_code
