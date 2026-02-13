"""
4GL Compiler module.

Provides integration with Informix 4make compiler for compiling 4GL source files.
"""

from .compiler import (
    CompilationResult,
    FourMakeCompiler,
    compile_4gl_file,
)
from .error_parser import (
    CompilationMessage,
    ErrorFileParser,
    parse_error_file,
)
from .exceptions import (
    CompilationError,
    CompilerError,
    CompilerExecutionError,
    CompilerNotFoundError,
    MakeDefGenerationError,
)
from .make_def_generator import (
    MakeDefGenerator,
    generate_4make_def,
)

__all__ = [
    # Main compiler
    "FourMakeCompiler",
    "CompilationResult",
    "compile_4gl_file",
    # Make def generator
    "MakeDefGenerator",
    "generate_4make_def",
    # Error parser
    "ErrorFileParser",
    "CompilationMessage",
    "parse_error_file",
    # Exceptions
    "CompilerError",
    "CompilationError",
    "MakeDefGenerationError",
    "CompilerNotFoundError",
    "CompilerExecutionError",
]
