"""
Extended pytest fixtures and utilities for comprehensive testing
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any, AsyncGenerator
from pathlib import Path

# Import our mock classes
try:
    from .mocks.api_mocks import (
        MockConfig,
        MockStorageBackend,
        set_mock_environment,
        reset_mock_environment,
    )
except ImportError:
    # Fallback implementations
    class MockConfig:
        def __init__(self):
            self.openai_api_key = "mock-key"
            self.cohere_api_key = "mock-key"

    class MockStorageBackend:
        def __init__(self):
            self.data = {}

    def set_mock_environment():
        pass

    def reset_mock_environment():
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Provide mock configuration for tests"""
    return MockConfig()


@pytest.fixture
def mock_env_setup():
    """Set up mock environment variables for tests"""
    set_mock_environment()
    yield
    reset_mock_environment()


@pytest.fixture
async def mock_lightrag_instance(mock_config):
    """Create a mock LightRAG instance for testing"""
    from lightrag import LightRAG

    # Create with mocked components
    with tempfile.TemporaryDirectory() as tmpdir:
        instance = LightRAG(
            working_dir=tmpdir,
            llm_model_func=lambda *args, **kwargs: "Mock LLM response",
            embedding_func=lambda texts: [
                {"id": i, "vector": [0.1] * 1536} for i in range(len(texts))
            ],
            mock_llm_config=True,
            mock_embedding_config=True,
        )
        yield instance


@pytest.fixture
def sample_documents():
    """Provide sample documents for testing"""
    return [
        "LightRAG is a Retrieval-Augmented Generation framework.",
        "It combines knowledge graphs with language models.",
        "The system provides accurate, citation-based responses.",
        "Users can query their documents using natural language.",
        "The framework supports multiple storage backends.",
    ]


@pytest.fixture
def sample_queries():
    """Provide sample queries for testing"""
    return [
        "What is LightRAG?",
        "How does LightRAG work?",
        "What are the key features?",
    ]


@pytest.fixture
def mock_graph_data():
    """Provide sample graph data for testing"""
    return {
        "nodes": [
            {"id": "1", "type": "entity", "name": "LightRAG"},
            {"id": "2", "type": "entity", "name": "knowledge graph"},
            {"id": "3", "type": "entity", "name": "language model"},
        ],
        "edges": [
            {"from": "1", "to": "2", "type": "uses"},
            {"from": "1", "to": "3", "type": "combines"},
            {"from": "2", "to": "3", "type": "enhances"},
        ],
    }


# Async testing utilities
@pytest.fixture
def async_test():
    """Utility for running async tests"""

    async def run_async_test(test_func, *args, **kwargs):
        return await test_func(*args, **kwargs)

    return run_async_test


# Coverage measurement utilities
@pytest.fixture
def coverage_tracker():
    """Track coverage during tests"""
    import coverage

    cov = coverage.Coverage()
    cov.start()
    yield cov
    cov.stop()
    cov.save()


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time

    start_time = None
    end_time = None

    class Timer:
        def start(self):
            nonlocal start_time
            start_time = time.time()

        def stop(self):
            nonlocal end_time
            end_time = time.time()

        @property
        def elapsed(self):
            if start_time and end_time:
                return end_time - start_time
            return 0

    timer = Timer()
    yield timer


# Error testing utilities
@pytest.fixture
def error_injector():
    """Inject errors for testing error handling"""

    class ErrorInjector:
        def __init__(self):
            self.errors = {}

        def add_error(self, func_name: str, error: Exception):
            """Add an error to inject for a specific function"""
            self.errors[func_name] = error

        def should_error(self, func_name: str):
            """Check if we should inject an error for this function"""
            return func_name in self.errors

        def get_error(self, func_name: str):
            """Get the error to inject for this function"""
            return self.errors.get(func_name)

    return ErrorInjector()


# Database testing utilities
@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection for testing"""
    import asyncpg

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_conn.fetchrow.return_value = None
    mock_conn.execute.return_value = None
    mock_conn.close.return_value = None
    return mock_conn


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection for testing"""
    import aioredis

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    return mock_redis


# File system utilities
@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing"""
    import builtins

    original_open = builtins.open

    class MockFileSystem:
        def __init__(self):
            self.files = {}

        def add_file(self, path: str, content: str):
            self.files[path] = content

        def mock_open(self, path: str, mode: str = "r"):
            if path in self.files:
                from io import StringIO

                return StringIO(self.files[path])
            return original_open(path, mode)

    fs = MockFileSystem()
    return fs


# Test data generators
@pytest.fixture
def generate_test_data():
    """Generate test data for various scenarios"""

    class DataGenerator:
        @staticmethod
        def documents(count: int = 10) -> list:
            return [f"Test document {i + 1} with sample content." for i in range(count)]

        @staticmethod
        def queries(count: int = 5) -> list:
            return [f"Test query {i + 1}" for i in range(count)]

        @staticmethod
        def graph_nodes(count: int = 5) -> list:
            return [{"id": str(i), "name": f"Node {i}"} for i in range(count)]

        @staticmethod
        def graph_edges(count: int = 3) -> list:
            return [
                {"from": str(i), "to": str(i + 1), "type": "relates"}
                for i in range(count)
            ]

    return DataGenerator()


# Integration testing utilities
@pytest.fixture
def integration_test_setup():
    """Set up integration test environment"""
    import tempfile
    import shutil

    # Create temporary working directory
    temp_dir = tempfile.mkdtemp()

    # Setup configuration
    config = {
        "working_dir": temp_dir,
        "llm_model": "mock-model",
        "embedding_model": "mock-embedding",
    }

    class IntegrationSetup:
        def __init__(self, config: dict, temp_dir: str):
            self.config = config
            self.temp_dir = temp_dir
            self.cleanup_done = False

        def cleanup(self):
            if not self.cleanup_done:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.cleanup_done = True

    setup = IntegrationSetup(config, temp_dir)
    yield setup

    # Cleanup
    setup.cleanup()


# Markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.api_mock = pytest.mark.api_mock
pytest.mark.slow = pytest.mark.slow


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "api_mock: mark test as using API mocks")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Test collection utilities
def collect_tests_by_marker(marker: str) -> list:
    """Collect tests by pytest marker"""
    import pytest

    collector = pytest.Collector()
    return [item for item in collector.collect() if marker in item.keywords]
