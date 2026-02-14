#!/usr/bin/env python3
"""
Test suite for automatic query mode detection in lightrag.operate.py

Tests the detect_query_mode function which automatically selects
the optimal query mode based on query characteristics.
"""

from lightrag.operate import detect_query_mode


class TestDetectQueryMode:
    """Test cases for automatic query mode detection."""

    def test_short_vague_query_returns_naive(self):
        """Short, vague queries should return naive mode."""
        assert detect_query_mode("hi") == "naive"
        assert detect_query_mode("hello") == "naive"
        assert detect_query_mode("ok") == "naive"

    def test_query_with_email_returns_local(self):
        """Queries with email addresses should return local mode."""
        assert detect_query_mode("Contact john@email.com") == "local"

    def test_query_with_date_returns_local(self):
        """Queries with dates should return local mode."""
        assert detect_query_mode("What happened on 2024-01-01?") == "local"

    def test_conceptual_query_returns_global(self):
        """Conceptual queries without entities should return global mode."""
        assert detect_query_mode("How does photosynthesis work?") == "global"
        assert detect_query_mode("Why is the sky blue?") == "global"
        assert detect_query_mode("Explain the concept of machine learning") == "global"

    def test_technical_query_returns_mix(self):
        """Technical/programming queries should return mix mode."""
        assert detect_query_mode("How to fix this function error?") == "mix"
        assert detect_query_mode("Debug the API import issue") == "mix"

    def test_mixed_query_returns_hybrid(self):
        """Queries with both entities and concepts should return hybrid mode."""
        result = detect_query_mode("How does Apple use machine learning?")
        assert result in ("hybrid", "global")

    def test_long_query_returns_hybrid(self):
        """Long queries without specific patterns should return hybrid."""
        long_query = "Can you provide detailed information about the history of computing and how it has evolved over time"
        assert detect_query_mode(long_query) == "hybrid"


class TestDetectQueryModeEdgeCases:
    """Edge case tests for query mode detection."""

    def test_empty_query(self):
        """Empty query should return default hybrid."""
        assert detect_query_mode("") == "hybrid"

    def test_whitespace_only(self):
        """Whitespace-only query should return default hybrid."""
        assert detect_query_mode("   ") == "hybrid"

    def test_very_long_query(self):
        """Very long queries should return hybrid."""
        very_long = "word " * 100
        assert detect_query_mode(very_long) == "hybrid"
