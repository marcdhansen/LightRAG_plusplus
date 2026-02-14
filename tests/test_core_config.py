"""Tests for lightrag.core.config module."""

from lightrag.core.config import LightRAGConfig


def test_lightrag_config_defaults():
    """Test LightRAGConfig has expected default values."""
    config = LightRAGConfig()

    assert config.working_dir == "./rag_storage"
    assert config.kv_storage == "JsonKVStorage"
    assert config.vector_storage == "NanoVectorDBStorage"
    assert config.graph_storage == "NetworkXStorage"
    assert config.doc_status_storage == "JsonDocStatusStorage"


def test_lightrag_config_custom_values():
    """Test LightRAGConfig can be customized."""
    config = LightRAGConfig(
        working_dir="/custom/path",
        kv_storage="CustomKVStorage",
        vector_storage="CustomVectorStorage",
    )

    assert config.working_dir == "/custom/path"
    assert config.kv_storage == "CustomKVStorage"
    assert config.vector_storage == "CustomVectorStorage"


def test_lightrag_config_is_dataclass():
    """Test LightRAGConfig is a dataclass."""
    from dataclasses import is_dataclass

    assert is_dataclass(LightRAGConfig)
