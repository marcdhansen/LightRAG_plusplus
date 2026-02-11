"""
Comprehensive mocking framework for external API dependencies
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional


class MockRerankAPI:
    """Mock base class for reranking APIs"""

    @staticmethod
    def create_mock_response(success: bool = True, count: int = 5):
        """Create standardized mock response for reranking APIs"""
        if success:
            return {
                "results": [
                    {"index": i, "relevance_score": 0.9 - (i * 0.1)}
                    for i in range(count)
                ],
                "meta": {"api_version": "mock", "model": "mock-model"},
            }
        else:
            raise Exception("Mock API error")


class MockLLMAPI:
    """Mock base class for LLM APIs"""

    @staticmethod
    def create_mock_response(text: str, model: str = "mock-model"):
        """Create standardized mock response for LLM APIs"""
        return {
            "choices": [
                {"message": {"content": text}, "finish_reason": "stop", "index": 0}
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            "model": model,
        }


class MockStorageBackend:
    """Mock base class for storage backends"""

    def __init__(self):
        self.data = {}
        self.graph_data = {"nodes": [], "edges": []}

    async def upsert(self, data: Dict[str, Any]) -> bool:
        """Mock upsert operation"""
        self.data.update(data)
        return True

    async def query(self, query: str) -> List[Dict[str, Any]]:
        """Mock query operation"""
        return [
            {"id": k, "content": v, "relevance": 0.8}
            for k, v in self.data.items()
            if query.lower() in str(v).lower()
        ]


# Pytest fixtures for mocking
@pytest.fixture
def mock_cohere_rerank():
    """Mock Cohere reranking API"""
    with patch("lightrag.rerank.cohere_rerank") as mock:
        mock.return_value = MockRerankAPI.create_mock_response(success=True, count=5)
        yield mock


@pytest.fixture
def mock_jina_rerank():
    """Mock Jina reranking API - handles relevance_score key issue"""

    async def mock_jina_response(*args, **kwargs):
        return MockRerankAPI.create_mock_response(success=True, count=5)

    with patch("lightrag.rerank.jina_rerank", side_effect=mock_jina_response) as mock:
        yield mock


@pytest.fixture
def mock_ali_rerank():
    """Mock Ali reranking API"""
    with patch("lightrag.rerank.ali_rerank") as mock:
        mock.return_value = MockRerankAPI.create_mock_response(success=True, count=5)
        yield mock


@pytest.fixture
def mock_openai_llm():
    """Mock OpenAI API"""
    with patch("lightrag.llm.openai_client") as mock:
        mock.chat.completions.create.return_value = MockLLMAPI.create_mock_response(
            text="Mock response from OpenAI"
        )
        yield mock


@pytest.fixture
def mock_postgres_storage():
    """Mock PostgreSQL storage backend"""
    return MockStorageBackend()


@pytest.fixture
def mock_qdrant_storage():
    """Mock Qdrant storage backend"""
    return MockStorageBackend()


# Mock configurations for testing
class MockConfig:
    """Mock configuration for testing"""

    def __init__(self):
        self.openai_api_key = "mock-openai-key"
        self.cohere_api_key = "mock-cohere-key"
        self.jina_api_key = "mock-jina-key"
        self.ali_api_key = "mock-ali-key"
        self.postgres_connection_string = "mock://localhost/test"
        self.qdrant_url = "http://mock-qdrant:6333"


# Environment setup utilities
def set_mock_environment():
    """Set up mock environment variables for testing"""
    import os

    os.environ["OPENAI_API_KEY"] = "mock-openai-key"
    os.environ["COHERE_API_KEY"] = "mock-cohere-key"
    os.environ["JINA_API_KEY"] = "mock-jina-key"
    os.environ["ALI_API_KEY"] = "mock-ali-key"


def reset_mock_environment():
    """Reset mock environment variables"""
    import os

    keys_to_remove = ["OPENAI_API_KEY", "COHERE_API_KEY", "JINA_API_KEY", "ALI_API_KEY"]
    for key in keys_to_remove:
        os.environ.pop(key, None)


# Patch decorators for skipping API calls when keys missing
def skip_if_no_api_key(service_name: str):
    """Decorator to skip tests if API key is missing"""
    key_map = {
        "cohere": "COHERE_API_KEY",
        "jina": "JINA_API_KEY",
        "ali": "ALI_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    def decorator(test_func):
        import os

        key = key_map.get(service_name.lower())
        if not key or not os.environ.get(key):
            return pytest.mark.skip(f"Skipping {service_name} test - no API key")(
                test_func
            )
        return test_func

    return decorator


# Performance testing utilities
class MockTimer:
    """Mock timer for performance testing"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        import time

        self.start_time = time.time()

    def stop(self):
        import time

        self.end_time = time.time()

    @property
    def elapsed(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
