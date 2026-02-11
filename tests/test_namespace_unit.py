"""
Unit tests for lightrag.namespace module
Tests high-impact namespace functionality
"""

import pytest
import sys
import os

# Add path to avoid import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lightrag.namespace import NameSpace, is_namespace


class TestNameSpace:
    """Test NameSpace constants"""

    def test_namespace_constants(self):
        """Test that all namespace constants are defined"""
        constants = [
            "KV_STORE_FULL_DOCS",
            "KV_STORE_TEXT_CHUNKS",
            "KV_STORE_LLM_RESPONSE_CACHE",
            "KV_STORE_FULL_ENTITIES",
            "KV_STORE_FULL_RELATIONS",
            "KV_STORE_ENTITY_CHUNKS",
            "KV_STORE_RELATION_CHUNKS",
            "VECTOR_STORE_ENTITIES",
            "VECTOR_STORE_RELATIONSHIPS",
            "VECTOR_STORE_CHUNKS",
            "GRAPH_STORE_CHUNK_ENTITY_RELATION",
            "DOC_STATUS",
            "KEYWORD_STORE",
        ]

        for constant in constants:
            assert hasattr(NameSpace, constant), f"Missing constant: {constant}"
            value = getattr(NameSpace, constant)
            assert isinstance(value, str), f"Constant {constant} should be a string"
            assert len(value) > 0, f"Constant {constant} should not be empty"

    def test_namespace_constant_values(self):
        """Test specific namespace constant values"""
        # Test key constants
        assert NameSpace.KV_STORE_FULL_DOCS == "full_docs"
        assert NameSpace.KV_STORE_TEXT_CHUNKS == "text_chunks"
        assert NameSpace.VECTOR_STORE_ENTITIES == "entities"
        assert NameSpace.GRAPH_STORE_CHUNK_ENTITY_RELATION == "chunk_entity_relation"
        assert NameSpace.DOC_STATUS == "doc_status"


class TestNamespaceFunction:
    """Test is_namespace function"""

    def test_is_namespace_with_string(self):
        """Test namespace check with string base"""
        # Test positive cases
        assert is_namespace("test_full_docs", "_full_docs") is True
        assert is_namespace("test_text_chunks", "_text_chunks") is True
        assert is_namespace("test_entities", "_entities") is True

        # Test negative cases
        assert is_namespace("test_full_docs", "_text_chunks") is False
        assert is_namespace("test_text_chunks", "_entities") is False
        assert is_namespace("test_entities", "_full_docs") is False

    def test_is_namespace_with_iterable(self):
        """Test namespace check with iterable base"""
        bases = ["_full_docs", "_text_chunks", "_entities"]

        # Test positive cases
        assert is_namespace("test_full_docs", bases) is True
        assert is_namespace("test_text_chunks", bases) is True
        assert is_namespace("test_entities", bases) is True

        # Test negative cases
        assert is_namespace("test_other", bases) is False
        assert is_namespace("test_invalid", bases) is False

    def test_is_namespace_with_list(self):
        """Test namespace check with list base"""
        bases = ["full_docs", "text_chunks", "entities", "relationships"]

        # Test without underscores
        assert is_namespace("testfulldocs", bases) is False
        assert is_namespace("test.text_chunks", bases) is False

        # Test correct matching
        assert is_namespace("test.full_docs", "full_docs") is True
        assert is_namespace("test.text_chunks", "text_chunks") is True

    def test_is_namespace_edge_cases(self):
        """Test edge cases for namespace function"""
        # Empty strings
        assert is_namespace("", "test") is False
        assert is_namespace("test", "") is False

        # Single character
        assert is_namespace("a", "a") is True
        assert is_namespace("a", "b") is False

        # Multiple base patterns
        bases = ["_docs", "_chunks", "_cache"]
        assert is_namespace("test_docs", bases) is True
        assert is_namespace("test_chunks", bases) is True
        assert is_namespace("test_cache", bases) is True

    def test_is_namespace_type_handling(self):
        """Test that function handles different input types"""
        # Test with list
        assert is_namespace("test_docs", ["_docs", "_chunks"]) is True

        # Test with tuple
        assert is_namespace("test_docs", ("_docs", "_chunks")) is True

        # Test with set
        assert is_namespace("test_docs", {"_docs", "_chunks"}) is True
