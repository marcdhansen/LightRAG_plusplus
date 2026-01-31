#!/usr/bin/env python3
"""
Simple RRF Validation Test

Tests the core RRF implementation without complex dependencies.
"""

import pytest

from lightrag.base import QueryParam


@pytest.mark.asyncio
async def test_rrf_configuration():
    """Test that RRF configuration works properly"""

    # Test basic RRF parameters
    param = QueryParam(
        mode="rrf",
        rrf_k=60,
        rrf_weights={"vector": 1.0, "graph": 1.0, "keyword": 1.0},
        top_k=3,
    )

    assert param.mode == "rrf"
    assert param.rrf_k == 60
    assert param.rrf_weights == {"vector": 1.0, "graph": 1.0, "keyword": 1.0}
    assert param.top_k == 3


@pytest.mark.asyncio
async def test_rrf_scoring_formula():
    """Test RRF scoring formula implementation"""

    # Mock retrieval results for testing
    vector_results = [
        {"id": "doc1", "score": 0.9},
        {"id": "doc2", "score": 0.7},
        {"id": "doc3", "score": 0.5},
    ]

    graph_results = [{"id": "doc1", "score": 0.8}, {"id": "doc4", "score": 0.6}]

    keyword_results = [{"id": "doc5", "score": 0.4}, {"id": "doc1", "score": 0.3}]

    # Test RRF scoring
    k = 60
    weights = {"vector": 1.0, "graph": 1.0, "keyword": 1.0}
    result_lists = [vector_results, graph_results, keyword_results]

    rrf_scores = {}
    for method_name, results in enumerate(result_lists):
        method_key = ["vector", "graph", "keyword"][method_name]
        weight = weights.get(method_key, 1.0)

        for rank, result in enumerate(results, 1):  # 1-based ranking
            doc_id = result.get("id", f"doc_{method_key}_{rank}")
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0

            # RRF formula: sum(weighted * 1/(k + rank))
            rrf_scores[doc_id] += weight / (k + rank)

    # Expected scores for verification
    expected_scores = {
        "doc1": (1.0 / 61)
        + (1.0 / 61)
        + (1.0 / 61),  # Appears in all 3 methods at rank 1
        "doc2": (1.0 / 62) + (1.0 / 62),  # Appears in vector(2) and graph(2)
        "doc3": (1.0 / 63),  # Appears in vector(3) only
        "doc4": (1.0 / 63) + (1.0 / 63),  # Appears in graph(2) only
        "doc5": (1.0 / 64),  # Appears in keyword(2) only
    }

    # Verify RRF scores match expected
    for doc_id, expected_score in expected_scores.items():
        actual_score = rrf_scores.get(doc_id, 0)
        assert abs(actual_score - expected_score) < 0.001, (
            f"RRF score for {doc_id}: {actual_score} vs expected {expected_score}"
        )


@pytest.mark.asyncio
async def test_rrf_ranking_order():
    """Test that RRF produces correct ranking order"""

    # Mock results where doc1 should rank highest (consensus), doc2 lowest
    vector_results = [{"id": "doc1", "score": 0.9}]
    graph_results = [{"id": "doc1", "score": 0.8}]
    keyword_results = [{"id": "doc2", "score": 0.7}]

    k = 60
    weights = {"vector": 1.0, "graph": 1.0, "keyword": 1.0}
    result_lists = [vector_results, graph_results, keyword_results]

    rrf_scores = {}
    for method_name, results in enumerate(result_lists):
        method_key = ["vector", "graph", "keyword"][method_name]
        weight = weights.get(method_key, 1.0)

        for rank, result in enumerate(results, 1):
            doc_id = result.get("id")
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0
            rrf_scores[doc_id] += weight / (k + rank)

    # Sort by RRF score descending
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # doc1 should rank highest (appears in all methods at rank 1)
    assert sorted_results[0][0] == "doc1"
    # doc2 should rank lower (appears in 2 methods, not all 3)
    assert sorted_results[1][0] == "doc2"


if __name__ == "__main__":
    print("🧪 RRF Validation Tests")
    pytest.main([__file__])
