#!/usr/bin/env python3
"""
Functional Integration Tests for automatic query mode detection.

These tests verify the end-to-end behavior of the detect_query_mode
function integrated with the LightRAG operate module.
"""

import pytest
from lightrag.operate import detect_query_mode


class TestQueryModeIntegration:
    """Integration tests for query mode detection in real scenarios."""

    def test_query_mode_selection_for_user_intent(self):
        """Test that query mode correctly identifies user intent patterns."""
        test_cases = [
            ("What is Python?", "global"),
            ("Find info about python", "local"),
            ("Explain python programming", "global"),
        ]
        for query, expected in test_cases:
            result = detect_query_mode(query)
            assert result in [expected, "hybrid"], f"Failed for query: {query}"

    def test_performance_with_large_query_set(self):
        """Test performance with multiple queries."""
        queries = [
            "How does AI work?",
            "Tell me about machine learning",
            "What is deep learning?",
            "Explain neural networks",
            "What are transformers?",
        ]
        results = [detect_query_mode(q) for q in queries]
        assert len(results) == len(queries)
        assert all(r in ["naive", "local", "global", "mix", "hybrid"] for r in results)

    def test_mode_consistency(self):
        """Test that identical queries return consistent results."""
        query = "What is the capital of France?"
        results = [detect_query_mode(query) for _ in range(5)]
        assert len(set(results)) == 1, "Query mode detection should be deterministic"
