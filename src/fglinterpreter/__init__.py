"""
fglInterpreter - A Python-based interpreter and tooling framework for Informix 4GL.

This package provides:
- Lexer and tokenizer for 4GL syntax
- Parser and AST construction
- Interpreter for direct 4GL execution
- Converter for 4GL to Python translation
- Database integration via wbjdbc/wborm
"""

__version__ = "0.1.0"
__author__ = "Wand"
__license__ = "MIT"

# Version information
VERSION = __version__

# These will be implemented in future stories
# from .lexer import Lexer, Token
# from .parser import Parser, AST
# from .interpreter import Interpreter
# from .converter import Converter

__all__ = [
    "__version__",
    "VERSION",
    # Future exports will be added as components are implemented
    # "Lexer",
    # "Token",
    # "Parser",
    # "AST",
    # "Interpreter",
    # "Converter",
]
