"""
Test suite for lightrag.rerank module

This module provides document reranking functionality using various rerankers.
Tests cover chunking, aggregation, API reranking, error handling, and configuration.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np
from typing import List, Dict, Any

from lightrag.rerank import (
    chunk_documents_for_rerank,
    aggregate_chunk_scores,
    local_rerank,
    _RERANKER_INSTANCE,
)


class TestChunkDocumentsForRerank:
    """Test cases for document chunking functionality"""

    def test_chunk_documents_short_content(self):
        """Test chunking when documents are under token limit"""
        documents = ["Short doc 1", "Short doc 2", "Short doc 3"]

        with patch("lightrag.rerank.tiktoken.encoding_for_model") as mock_encoding:
            mock_encoder = MagicMock()
            mock_encoder.encode = MagicMock(return_value=[1, 2, 3])  # 3 tokens
            mock_encoding.return_value = mock_encoder

            with patch("lightrag.rerank._split_document_by_tokens") as mock_split:
                # Since token count < max_tokens, no splitting needed
                mock_split.return_value = ([], [])

                chunks, indices = chunk_documents_for_rerank(documents, max_tokens=10)

                # Documents should remain unchanged when under limit
                assert chunks == documents
                assert indices == [0, 1, 2]

    def test_chunk_documents_long_content(self):
        """Test chunking when documents exceed token limit"""
        documents = ["Very long document 1", "Very long document 2"]

        with patch("lightrag.rerank.tiktoken.encoding_for_model") as mock_encoding:
            mock_encoder = MagicMock()
            # First document returns 15 tokens, second returns 12 tokens
            mock_encoder.encode.side_effect = [
                list(range(15)),  # 15 tokens for first doc
                list(range(12)),  # 12 tokens for second doc
            ]
            mock_encoding.return_value = mock_encoder

            with patch("lightrag.rerank._split_document_by_tokens") as mock_split:
                mock_split.side_effect = [
                    (["Chunk 1-1", "Chunk 1-2"], [0, 0]),  # First doc split into 2
                    (["Chunk 2-1"], [1]),  # Second doc split into 1
                ]

                chunks, indices = chunk_documents_for_rerank(documents, max_tokens=10)

                # Combine all chunks and indices
                expected_chunks = ["Chunk 1-1", "Chunk 1-2", "Chunk 2-1"]
                expected_indices = [0, 0, 1]

                assert chunks == expected_chunks
                assert indices == expected_indices

    def test_chunk_documents_default_parameters(self):
        """Test chunking with default parameters"""
        documents = ["Test document"]

        with patch("lightrag.rerank.tiktoken.encoding_for_model") as mock_encoding:
            mock_encoder = MagicMock()
            mock_encoder.encode = MagicMock(return_value=list(range(5)))  # 5 tokens
            mock_encoding.return_value = mock_encoder

            chunks, indices = chunk_documents_for_rerank(documents)

            # Should use default tokenizer model
            mock_encoding.assert_called_once_with("gpt-4o-mini")
            assert chunks == ["Test document"]
            assert indices == [0]

    def test_chunk_documents_empty_list(self):
        """Test chunking with empty document list"""
        chunks, indices = chunk_documents_for_rerank([])

        assert chunks == []
        assert indices == []


class TestAggregateChunkScores:
    """Test cases for chunk score aggregation functionality"""

    def test_aggregate_chunk_scores_basic(self):
        """Test basic score aggregation"""
        chunk_results = [
            {"index": 0, "relevance_score": 0.8},
            {"index": 1, "relevance_score": 0.6},
            {"index": 2, "relevance_score": 0.7},
        ]
        doc_indices = [0, 0, 1]  # Two chunks from doc 0, one from doc 1

        with patch("lightrag.rerank._aggregate_scores") as mock_agg:
            mock_agg.return_value = [(0, 0.7), (1, 0.7)]  # avg of 0.8,0.6 and 0.7

            results = aggregate_chunk_scores(chunk_results, doc_indices, 2)

            assert len(results) == 2
            assert results[0] == {"index": 0, "relevance_score": 0.7}
            assert results[1] == {"index": 1, "relevance_score": 0.7}

    def test_aggregate_chunk_scores_empty(self):
        """Test aggregation with empty inputs"""
        results = aggregate_chunk_scores([], [], 0)

        assert results == []

    def test_aggregate_chunk_scores_single_document(self):
        """Test aggregation when all chunks from same document"""
        chunk_results = [
            {"index": 0, "relevance_score": 0.8},
            {"index": 1, "relevance_score": 0.6},
            {"index": 2, "relevance_score": 0.7},
        ]
        doc_indices = [0, 0, 0]  # All from doc 0

        with patch("lightrag.rerank._aggregate_scores") as mock_agg:
            mock_agg.return_value = [(0, 0.7)]  # avg of 0.8,0.6,0.7

            results = aggregate_chunk_scores(chunk_results, doc_indices, 1)

            assert len(results) == 1
            assert results[0] == {"index": 0, "relevance_score": 0.7}


class TestLocalRerank:
    """Test cases for local reranker functionality"""

    @pytest.mark.asyncio
    async def test_local_rerank_success(self):
        """Test successful local reranking"""
        # Clear global instance
        import lightrag.rerank

        lightrag.rerank._RERANKER_INSTANCE = None

        with patch("lightrag.rerank.FlagReranker") as mock_flag_class:
            mock_reranker = MagicMock()
            mock_reranker.compute_score = MagicMock(return_value=[0.8, 0.6])
            mock_flag_class.return_value = mock_reranker

            results = await local_rerank(
                "test query", ["doc1", "doc2"], model="test-model"
            )

            assert len(results) == 2
            assert results[0]["index"] == 0
            assert results[0]["relevance_score"] == 0.8
            assert results[1]["index"] == 1
            assert results[1]["relevance_score"] == 0.6

            # Verify model was loaded
            mock_flag_class.assert_called_once_with("test-model", use_fp16=True)

    @pytest.mark.asyncio
    async def test_local_rerank_with_cached_instance(self):
        """Test local reranking with cached instance"""
        import lightrag.rerank

        mock_reranker = MagicMock()
        mock_reranker.compute_score = MagicMock(return_value=[0.7, 0.9])
        lightrag.rerank._RERANKER_INSTANCE = mock_reranker

        results = await local_rerank(
            "test query",
            ["doc1", "doc2"],
            model="any-model",  # Should not matter since instance is cached
        )

        assert len(results) == 2
        assert results[0]["index"] == 0
        assert results[0]["relevance_score"] == 0.7
        assert results[1]["index"] == 1
        assert results[1]["relevance_score"] == 0.9

    @pytest.mark.asyncio
    async def test_local_rerank_no_flagembedding(self):
        """Test local reranking without FlagEmbedding"""
        import lightrag.rerank

        original_flag_reranker = lightrag.rerank.FlagReranker
        lightrag.rerank.FlagReranker = None
        lightrag.rerank._RERANKER_INSTANCE = None

        try:
            with pytest.raises(ImportError, match="FlagEmbedding is not installed"):
                await local_rerank("test query", ["doc1", "doc2"])
        finally:
            lightrag.rerank.FlagReranker = original_flag_reranker

    @pytest.mark.asyncio
    async def test_local_rerank_single_score(self):
        """Test local reranking when compute_score returns float"""
        import lightrag.rerank

        lightrag.rerank._RERANKER_INSTANCE = None

        with patch("lightrag.rerank.FlagReranker") as mock_flag_class:
            mock_reranker = MagicMock()
            mock_reranker.compute_score = MagicMock(return_value=0.85)  # Single float
            mock_flag_class.return_value = mock_reranker

            results = await local_rerank("test query", ["doc1"])

            assert len(results) == 1
            assert results[0]["index"] == 0
            assert results[0]["relevance_score"] == 0.85

    @pytest.mark.asyncio
    async def test_local_rerank_top_n(self):
        """Test local reranking with top_n limit"""
        import lightrag.rerank

        lightrag.rerank._RERANKER_INSTANCE = None

        with patch("lightrag.rerank.FlagReranker") as mock_flag_class:
            mock_reranker = MagicMock()
            mock_reranker.compute_score = MagicMock(return_value=[0.8, 0.6, 0.9])
            mock_flag_class.return_value = mock_reranker

            results = await local_rerank(
                "test query", ["doc1", "doc2", "doc3"], top_n=2
            )

            assert len(results) == 2  # Limited by top_n
            # Should be sorted by score (highest first)
            assert results[0]["index"] == 2
            assert results[0]["relevance_score"] == 0.9
            assert results[1]["index"] == 0
            assert results[1]["relevance_score"] == 0.8
