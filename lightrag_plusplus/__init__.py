"""
LightRAG++ - Python package alias for backward compatibility.

This module provides the 'lightrag_plusplus' import name while
maintaining compatibility with existing 'lightrag' imports.

The actual package implementation is in the 'lightrag' directory.
"""

import importlib.util
import sys
import os

_lightrag_plusplus_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lightrag_dir = os.path.join(_lightrag_plusplus_dir, "lightrag")

_lightrag_init_file = os.path.join(_lightrag_dir, "__init__.py")

if os.path.isfile(_lightrag_init_file):
    if "lightrag" not in sys.modules:
        spec = importlib.util.spec_from_file_location("lightrag", _lightrag_init_file)
        if spec and spec.loader:
            _lightrag_module = importlib.util.module_from_spec(spec)
            sys.modules["lightrag"] = _lightrag_module
            spec.loader.exec_module(_lightrag_module)

from lightrag import LightRAG, QueryParam
from lightrag_plusplus._version import __version__, __author__, __url__

__all__ = [
    "LightRAG",
    "QueryParam",
    "__version__",
    "__author__",
    "__url__",
]
