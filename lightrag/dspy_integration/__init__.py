"""
DSPy Integration for LightRAG

This package provides phased integration of DSPy optimization capabilities
into the LightRAG framework, starting with prompt generation and optimization.
"""

from .config import DSPyConfig, configure_dspy_from_env, get_dspy_config

__version__ = "0.1.0"
__author__ = "LightRAG DSPy Integration Team"

# Export main configuration functions
__all__ = ["DSPyConfig", "get_dspy_config", "configure_dspy_from_env"]
