"""
Fix for Jina rerank API response format handling
"""

import pytest
from unittest.mock import AsyncMock, patch


async def mock_jina_response(*args, **kwargs):
    """Mock Jina API response with correct format"""
    # Jina API returns scores, not relevance_score
    return [
        {
            "index": i,
            "relevance_score": 0.9 - (i * 0.1),
        }  # Convert score to relevance_score
        for i in range(5)
    ]


@pytest.fixture
def mock_jina_rerank_fixed():
    """Fixed mock for Jina reranking API with proper relevance_score handling"""
    with patch("lightrag.rerank.jina_rerank", side_effect=mock_jina_response) as mock:
        yield mock


@pytest.fixture
def mock_all_rerank_apis():
    """Mock all reranking APIs for comprehensive testing"""

    async def mock_cohere(*args, **kwargs):
        return [{"index": i, "relevance_score": 0.9 - (i * 0.1)} for i in range(5)]

    async def mock_jina(*args, **kwargs):
        return [{"index": i, "relevance_score": 0.9 - (i * 0.1)} for i in range(5)]

    async def mock_ali(*args, **kwargs):
        return [{"index": i, "relevance_score": 0.9 - (i * 0.1)} for i in range(5)]

    with (
        patch("lightrag.rerank.cohere_rerank", side_effect=mock_cohere) as m1,
        patch("lightrag.rerank.jina_rerank", side_effect=mock_jina) as m2,
        patch("lightrag.rerank.ali_rerank", side_effect=mock_ali) as m3,
    ):
        yield (m1, m2, m3)
