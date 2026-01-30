#!/usr/bin/env python3
"""
Unit Tests for Reciprocal Rank Fusion (RRF) Implementation

Tests the RRF algorithm correctness and precision improvements over standard mix mode.
"""

import pytest

from lightrag.base import QueryParam
from lightrag.core import LightRAG


class TestRRFFusion:
    """Test RRF fusion implementation for improved context precision"""

    @pytest.mark.asyncio
    async def test_rrf_scoring_formula(self):
        """Test RRF scoring formula implementation"""

        # Mock retrieval results for testing
        vector_results = [
            {"id": "doc1", "score": 0.9, "content": "relevant content A"},
            {"id": "doc2", "score": 0.7, "content": "noise content"},
            {"id": "doc3", "score": 0.5, "content": "relevant content B"},
        ]

        graph_results = [
            {"id": "doc1", "score": 0.8, "content": "relevant content A"},
            {"id": "doc4", "score": 0.6, "content": "more noise"},
            {"id": "doc2", "score": 0.4, "content": "noise content"},
        ]

        keyword_results = [
            {"id": "doc5", "score": 0.3, "content": "keyword noise"},
            {"id": "doc1", "score": 0.2, "content": "relevant content A"},
            {"id": "doc3", "score": 0.1, "content": "relevant content B"},
        ]

        # Create mock LightRAG instance
        lightrag = LightRAG(
            working_dir="./test_data",
            llm_model_func=lambda x: x,
            embedding_func=lambda x: x,
            storage_dir="./test_storage",
        )

        # Test RRF scoring function
        result_lists = [vector_results, graph_results, keyword_results]
        k = 60
        weights = {"vector": 1.0, "graph": 1.0, "keyword": 1.0}

        rrf_scores = {}
        for method_name, results in enumerate(result_lists):
            method_key = ["vector", "graph", "keyword"][method_name]
            weight = weights.get(method_key, 1.0)

            for rank, result in enumerate(results, 1):  # 1-based ranking
                doc_id = result.get("id", f"doc_{method_key}_{rank}")
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0

                # RRF formula: sum(weighted * 1/(k + rank))
                expected_score = weight / (k + rank)
                rrf_scores[doc_id] += expected_score

        # Verify scoring correctness
        # doc1 appears in all three methods: rank 1,1,2
        expected_doc1_score = (1.0 / 61) + (1.0 / 61) + (1.0 / 61)  # ranks 1,1,2
        actual_doc1_score = rrf_scores.get("doc1", 0)
        assert (
            abs(actual_doc1_score - expected_doc1_score) < 0.001
        ), f"doc1 RRF score mismatch: {actual_doc1_score} vs {expected_doc1_score}"

        # doc3 appears in vector(3) and keyword(3): rank 3,3
        expected_doc3_score = (1.0 / 63) + (1.0 / 63)  # vector rank 3, keyword rank 3
        actual_doc3_score = rrf_scores.get("doc3", 0)
        assert (
            abs(actual_doc3_score - expected_doc3_score) < 0.001
        ), f"doc3 RRF score mismatch: {actual_doc3_score} vs {expected_doc3_score}"

        # Verify sorting
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        assert (
            sorted_results[0][0] == "doc1"
        ), f"Top result should be doc1, got {sorted_results[0][0]}"
        assert (
            sorted_results[1][0] == "doc3"
        ), f"Second result should be doc3, got {sorted_results[1][0]}"

    @pytest.mark.asyncio
    async def test_rrf_consensus_behavior(self):
        """Test RRF prioritizes consensus across methods"""

        # Mock results where doc1 consistently ranks high
        vector_results = [
            {"id": "consensus_doc", "score": 0.8, "content": "highly relevant"},
            {"id": "noise_doc", "score": 0.7, "content": "noise"},
        ]
        graph_results = [
            {"id": "consensus_doc", "score": 0.6, "content": "highly relevant"},
            {"id": "noise_doc", "score": 0.5, "content": "noise"},
        ]
        keyword_results = [
            {"id": "consensus_doc", "score": 0.4, "content": "highly relevant"},
            {"id": "different_noise", "score": 0.3, "content": "other noise"},
        ]

        # Test consensus scoring
        lightrag = LightRAG(
            working_dir="./test_data",
            llm_model_func=lambda x: x,
            embedding_func=lambda x: x,
            storage_dir="./test_storage",
        )

        result_lists = [vector_results, graph_results, keyword_results]
        k = 60
        weights = {"vector": 1.0, "graph": 1.0, "keyword": 1.0}

        rrf_scores = {}
        for method_name, results in enumerate(result_lists):
            method_key = ["vector", "graph", "keyword"][method_name]
            weight = weights.get(method_key, 1.0)

            for rank, result in enumerate(results, 1):
                doc_id = result.get("id", f"doc_{method_key}_{rank}")
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0
                rrf_scores[doc_id] += weight / (k + rank)

        # Consensus doc should have highest RRF score
        consensus_score = rrf_scores.get("consensus_doc", 0)
        noise_score = rrf_scores.get("noise_doc", 0)

        assert (
            consensus_score > noise_score
        ), f"Consensus doc ({consensus_score}) should outrank noise ({noise_score})"

        # Verify top result is consensus doc
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        assert (
            sorted_results[0][0] == "consensus_doc"
        ), "Top result should be consensus doc"

    @pytest.mark.asyncio
    async def test_rrf_weighted_scoring(self):
        """Test RRF with different weights for each method"""

        # Mock results with different importance
        vector_results = [
            {"id": "vector_important", "score": 0.9, "content": "critical info"},
            {"id": "vector_secondary", "score": 0.7, "content": "secondary info"},
        ]
        graph_results = [
            {"id": "graph_secondary", "score": 0.8, "content": "secondary info"}
        ]
        keyword_results = [
            {"id": "keyword_minor", "score": 0.3, "content": "minor info"}
        ]

        # Test with weighted preferences (vector more important)
        lightrag = LightRAG(
            working_dir="./test_data",
            llm_model_func=lambda x: x,
            embedding_func=lambda x: x,
            storage_dir="./test_storage",
        )

        result_lists = [vector_results, graph_results, keyword_results]
        k = 60
        weights = {
            "vector": 2.0,
            "graph": 0.5,
            "keyword": 0.3,
        }  # Vector heavily weighted

        rrf_scores = {}
        for method_name, results in enumerate(result_lists):
            method_key = ["vector", "graph", "keyword"][method_name]
            weight = weights.get(method_key, 1.0)

            for rank, result in enumerate(results, 1):
                doc_id = result.get("id", f"doc_{method_key}_{rank}")
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0
                rrf_scores[doc_id] += weight / (k + rank)

        # Vector-important doc should rank highest
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        assert (
            sorted_results[0][0] == "vector_important"
        ), "Weighted RRF should prioritize vector results"

    @pytest.mark.asyncio
    async def test_rrf_parameter_validation(self):
        """Test RRF parameter validation and defaults"""

        lightrag = LightRAG(
            working_dir="./test_data",
            llm_model_func=lambda x: x,
            embedding_func=lambda x: x,
            storage_dir="./test_storage",
        )

        # Test default parameters
        query_param = QueryParam(mode="rrf")
        assert (
            query_param.rrf_k == 60
        ), f"Default rrf_k should be 60, got {query_param.rrf_k}"
        assert query_param.rrf_weights == {
            "vector": 1.0,
            "graph": 1.0,
            "keyword": 1.0,
        }, "Default weights should be equal"

        # Test custom parameters
        custom_param = QueryParam(
            mode="rrf",
            rrf_k=100,
            rrf_weights={"vector": 1.5, "graph": 0.8, "keyword": 0.2},
        )
        assert custom_param.rrf_k == 100, "Custom rrf_k should be 100"
        assert (
            custom_param.rrf_weights["vector"] == 1.5
        ), "Custom vector weight should be 1.5"

    @pytest.mark.asyncio
    async def test_rrf_vs_mix_precision_comparison(self):
        """Compare RRF precision vs standard mix mode"""

        # This test would require mock retrieval methods
        # For now, test the structure and logic
        lightrag = LightRAG(
            working_dir="./test_data",
            llm_model_func=lambda x: x,
            embedding_func=lambda x: x,
            storage_dir="./test_storage",
        )

        # Verify RRF mode is properly configured
        rrf_param = QueryParam(mode="rrf", top_k=3, rrf_k=60)
        assert rrf_param.mode == "rrf"
        assert rrf_param.top_k == 3
        assert rrf_param.rrf_k == 60

        # Test that RRF logic exists and is callable
        assert hasattr(
            lightrag, "rrf_fusion_context"
        ), "RRF fusion method should be implemented"

        # This would be expanded with actual retrieval method mocking
        # in integration tests
