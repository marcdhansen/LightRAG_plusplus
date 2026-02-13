"""
LightRAG++ - Python package alias for backward compatibility.

This module provides the 'lightrag_plusplus' import name while
maintaining compatibility with existing 'lightrag' imports.

The actual package implementation is in the 'lightrag' directory.
"""

import sys
import os

_lightrag_plusplus_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lightrag_dir = os.path.join(_lightrag_plusplus_dir, "lightrag")

if _lightrag_dir not in sys.path:
    sys.path.insert(0, _lightrag_dir)

from lightrag import LightRAG, QueryParam
from lightrag_plusplus._version import __version__, __author__, __url__

__all__ = [
    "LightRAG",
    "QueryParam",
    "__version__",
    "__author__",
    "__url__",
]
