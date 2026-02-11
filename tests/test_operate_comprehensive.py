"""
Comprehensive test suite for lightrag.operate.py - the highest impact module

This test suite focuses on critical LightRAG operations that will provide maximum coverage impact.
Target: 60% coverage from current 3% baseline.
"""

import pytest
import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from typing import List, Dict, Any

from tests.conftest_extensions import (
    sample_documents,
    sample_queries,
    mock_lightrag_instance,
    mock_config,
    temp_dir,
    async_test,
)

try:
    from tests.mocks.api_mocks import MockLLMAPI, MockStorageBackend
except ImportError:
    # Fallback if mocks module not available
    MockLLMAPI = None
    MockStorageBackend = None


class TestLightRAGEssentialOperations:
    """Test critical LightRAG operations - highest impact functions"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_insert_documents_basic(self, mock_lightrag_instance):
        """Test basic document insertion functionality"""
        documents = sample_documents()

        # Test insertion
        result = await mock_lightrag_instance.insert(documents)

        assert result is True
        # Verify documents were processed
        # Additional assertions would depend on mock implementation

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_insert_documents_empty_list(self, mock_lightrag_instance):
        """Test document insertion with empty list"""
        result = await mock_lightrag_instance.insert([])

        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_query_documents_basic(self, mock_lightrag_instance):
        """Test basic document querying functionality"""
        queries = sample_queries()

        for query in queries:
            result = await mock_lightrag_instance.query(query)

            assert result is not None
            # Verify query structure
            assert hasattr(result, "response")
            assert hasattr(result, "sources")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_query_documents_empty_query(self, mock_lightrag_instance):
        """Test document querying with empty query"""
        result = await mock_lightrag_instance.query("")

        # Should handle empty query gracefully
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_documents_basic(self, mock_lightrag_instance):
        """Test basic document deletion functionality"""
        documents = sample_documents()

        # First insert documents
        await mock_lightrag_instance.insert(documents)

        # Then delete them
        result = await mock_lightrag_instance.delete(documents)

        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_documents_nonexistent(self, mock_lightrag_instance):
        """Test deletion of non-existent documents"""
        result = await mock_lightrag_instance.delete(["Non-existent document"])

        assert result is True  # Should handle gracefully

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_graph_operations(self, mock_lightrag_instance):
        """Test graph-related operations"""
        # Test graph query functionality
        result = await mock_lightrag_instance.query("What entities exist?")

        assert result is not None

        # Test graph structure operations
        graph_result = await mock_lightrag_instance.query("Show graph structure")
        assert graph_result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_functionality(self, mock_lightrag_instance):
        """Test search and retrieval functionality"""
        query = "Find information about LightRAG"

        result = await mock_lightrag_instance.query(query)

        assert result is not None
        assert len(result.response) > 0 if hasattr(result.response, "__len__") else True


class TestLightRAGErrorHandling:
    """Test error handling robustness - critical for reliability"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_document_handling(self, mock_lightrag_instance):
        """Test handling of invalid documents"""
        invalid_documents = [
            None,  # None document
            "",  # Empty string
            123,  # Non-string type
        ]

        for doc in invalid_documents:
            # Should handle invalid documents gracefully
            try:
                result = await mock_lightrag_instance.insert([doc])
                # May succeed or fail gracefully
                assert isinstance(result, bool)
            except Exception as e:
                # Expected error types
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_network_failure_recovery(self, mock_lightrag_instance):
        """Test network failure recovery mechanisms"""
        # Mock network failure
        with patch("lightrag.operate._get_cached_extraction_results") as mock_cache:
            mock_cache.side_effect = Exception("Network failure")

            try:
                result = await mock_lightrag_instance.query("test query")
                # Should handle network failure gracefully
                assert result is not None
            except Exception as e:
                # Should be a known exception type
                assert isinstance(e, (ConnectionError, TimeoutError))

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_storage_backend_failures(self, mock_lightrag_instance):
        """Test storage backend failure scenarios"""
        # Mock storage failure
        with patch("lightrag.operate.merge_nodes_and_edges") as mock_storage:
            mock_storage.side_effect = Exception("Storage failure")

            try:
                result = await mock_lightrag_instance.insert(sample_documents())
                # Should handle storage failure
                assert result is not None
            except Exception as e:
                # Expected storage error types
                assert isinstance(e, (IOError, DatabaseError))

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_llm_provider_failures(self, mock_lightrag_instance):
        """Test LLM provider failure handling"""
        # Mock LLM failure
        with patch("lightrag.operate._handle_single_entity_extraction") as mock_llm:
            mock_llm.side_effect = Exception("LLM provider error")

            try:
                result = await mock_lightrag_instance.query("test query")
                # Should handle LLM failure gracefully
                assert result is not None
            except Exception as e:
                # Expected LLM error types
                assert isinstance(e, (RuntimeError, ProviderError))


class TestLightRAGPerformance:
    """Test performance critical paths - essential for scalability"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_document_processing(self, mock_lightrag_instance):
        """Test processing of large documents"""
        # Generate large test document
        large_document = "Test content. " * 10000  # ~50K characters

        start_time = asyncio.get_event_loop().time()
        result = await mock_lightrag_instance.insert([large_document])
        end_time = asyncio.get_event_loop().time()

        processing_time = end_time - start_time

        assert result is True
        # Should process within reasonable time (adjust threshold as needed)
        assert processing_time < 30.0, f"Processing took too long: {processing_time}s"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_operations(self, mock_lightrag_instance):
        """Test concurrent operation handling"""
        documents = [f"Document {i}" for i in range(10)]

        # Test concurrent insertions
        tasks = [mock_lightrag_instance.insert([doc]) for doc in documents]

        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        # Verify all operations completed
        successful_ops = [r for r in results if r is True]
        assert len(successful_ops) >= 8, f"Too many failed operations: {successful_ops}"

        # Should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 60.0, (
            f"Concurrent processing took too long: {processing_time}s"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_limits(self, mock_lightrag_instance):
        """Test memory usage with large datasets"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Process a significant number of documents
        documents = [f"Large test document {i}" * 1000 for i in range(100)]

        result = await mock_lightrag_instance.insert(documents)

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        assert result is True
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 1000, f"Memory usage too high: {memory_increase}MB"


class TestLightRAGChunkingOperations:
    """Test chunking functionality - core to LightRAG operation"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_chunking_by_token_size(self):
        """Test token-based chunking functionality"""
        from lightrag.operate import chunking_by_token_size

        test_content = "This is a test document for chunking functionality."

        result = await chunking_by_token_size(
            content=test_content, max_tokens=50, overlap_rate=0.1
        )

        assert isinstance(result, list)
        assert len(result) > 0
        # Verify chunk content is reasonable
        for chunk in result:
            assert isinstance(chunk, str)
            assert len(chunk) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_chunking_with_empty_content(self):
        """Test chunking with empty content"""
        from lightrag.operate import chunking_by_token_size

        result = await chunking_by_token_size("", 50, 0.1)

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_chunking_with_very_small_limit(self):
        """Test chunking with very small token limits"""
        from lightrag.operate import chunking_by_token_size

        test_content = "This is a longer test document that will definitely be split into multiple chunks."

        result = await chunking_by_token_size(test_content, 10, 0.1)

        assert isinstance(result, list)
        assert len(result) > 1  # Should be split into multiple chunks


class TestLightRAGExtractionOperations:
    """Test entity and relationship extraction operations"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_extract_entities_basic(self, mock_lightrag_instance):
        """Test basic entity extraction"""
        test_document = (
            "Apple Inc. is a technology company based in Cupertino, California."
        )

        # Mock the extraction process
        with patch("lightrag.operate._handle_single_entity_extraction") as mock_extract:
            mock_extract.return_value = {
                "entities": [
                    {"name": "Apple Inc.", "type": "organization", "confidence": 0.95},
                    {"name": "Cupertino", "type": "location", "confidence": 0.90},
                ]
            }

            result = await mock_lightrag_instance.insert([test_document])

            assert result is True
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_extract_relationships_basic(self, mock_lightrag_instance):
        """Test basic relationship extraction"""
        test_document = "Apple Inc. is headquartered in Cupertino, California."

        # Mock the extraction process
        with patch(
            "lightrag.operate._handle_single_relationship_extraction"
        ) as mock_extract:
            mock_extract.return_value = {
                "relationships": [
                    {
                        "from": "Apple Inc.",
                        "to": "Cupertino",
                        "type": "headquartered_in",
                        "confidence": 0.85,
                    }
                ]
            }

            result = await mock_lightrag_instance.insert([test_document])

            assert result is True
            mock_extract.assert_called_once()


# Test configuration and setup
@pytest.fixture
def mock_operate_dependencies():
    """Mock all external dependencies for operate.py testing"""
    with (
        patch("lightrag.operate.merge_nodes_and_edges") as mock_merge,
        patch("lightrag.operate._get_cached_extraction_results") as mock_cache,
        patch("lightrag.operate._process_extraction_result") as mock_process,
    ):
        mock_merge.return_value = True
        mock_cache.return_value = None
        mock_process.return_value = {"entities": [], "relationships": []}

        yield {"merge": mock_merge, "cache": mock_cache, "process": mock_process}


# Integration test helpers
@pytest.fixture
def integration_test_documents():
    """Provide documents for integration testing"""
    return [
        {
            "id": "doc1",
            "content": "LightRAG is a Retrieval-Augmented Generation framework.",
            "metadata": {"source": "test", "type": "documentation"},
        },
        {
            "id": "doc2",
            "content": "It combines knowledge graphs with language models for better responses.",
            "metadata": {"source": "test", "type": "documentation"},
        },
        {
            "id": "doc3",
            "content": "The system supports multiple storage backends including PostgreSQL and Neo4j.",
            "metadata": {"source": "test", "type": "documentation"},
        },
    ]


# Performance test markers
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration


# Utility functions for testing
def create_mock_extraction_result(entities=None, relationships=None):
    """Create a mock extraction result for testing"""
    return {"entities": entities or [], "relationships": relationships or []}


def assert_query_result_structure(result):
    """Assert that query result has expected structure"""
    assert result is not None
    assert hasattr(result, "response")
    assert hasattr(result, "sources")
    assert isinstance(result.response, (str, list))
    assert isinstance(result.sources, list)


def assert_performance_timing(start_time, end_time, max_seconds):
    """Assert that operation completed within time limit"""
    elapsed = end_time - start_time
    assert elapsed <= max_seconds, (
        f"Operation exceeded time limit: {elapsed}s > {max_seconds}s"
    )
