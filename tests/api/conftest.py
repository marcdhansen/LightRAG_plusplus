"""
Test configuration and fixtures for API testing.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

import httpx
import pytest
from pydantic import BaseModel

from lightrag import LightRAG
from lightrag.api.config import global_args
from lightrag.api.lightrag_server import create_app
from lightrag.base import DocStatus


class MockDocStatusStorage:
    """Mock document status storage."""

    def __init__(self, rag_instance):
        self.rag = rag_instance
        self._storage_lock = True  # Mock storage lock initialized

    async def get_doc_by_file_path(self, file_path):
        """Mock get document by file path."""
        if self._storage_lock is None:
            raise Exception("JsonDocStatusStorage not initialized")

        # Simple mock without context manager for testing
        for doc_id, doc_data in self.rag.documents.items():
            if doc_data.get("file_source") == file_path:
                return {
                    "id": doc_id,
                    "content": doc_data.get("content", ""),
                    "status": DocStatus.PROCESSED,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                    "content_length": len(doc_data.get("content", "")),
                    "content_summary": doc_data.get("content", "")[:100] + "...",
                }
        return None


class MockLightRAG:
    """Mock LightRAG instance for testing API endpoints without full dependencies."""

    def __init__(self):
        self.documents = {}
        self.track_counter = 0
        # Mock storage initialization
        self._doc_status_storage = MockDocStatusStorage(self)

    async def apipeline_enqueue_documents(self, documents, track_id=None):
        """Mock document enqueue."""
        if track_id is None:
            self.track_counter += 1
            track_id = f"test_track_{self.track_counter}"

        for doc in documents:
            doc_id = f"doc_{len(self.documents) + 1}"
            self.documents[doc_id] = {
                "id": doc_id,
                "content": doc.get("content", ""),
                "status": DocStatus.PENDING,
                "track_id": track_id,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "content_length": len(doc.get("content", "")),
                "content_summary": doc.get("content", "")[:100] + "...",
            }

        return track_id

    async def apipeline_enqueue_error_documents(self, error_docs, track_id=None):
        """Mock error document handling."""
        pass  # Implement error handling as needed

    async def aget_doc_status(self, doc_id: str):
        """Mock getting document status."""
        doc = self.documents.get(doc_id)
        if doc:
            return doc
        return None

    async def aget_documents_by_status(self, status: DocStatus = None):
        """Mock getting documents by status."""
        if status is None:
            return list(self.documents.values())
        return [doc for doc in self.documents.values() if doc["status"] == status]

    async def adelete_documents(
        self, doc_ids, delete_file=False, delete_llm_cache=False
    ):
        """Mock document deletion."""
        deletion_results = []
        for doc_id in doc_ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
                deletion_results.append({"doc_id": doc_id, "status": "success"})
            else:
                deletion_results.append({"doc_id": doc_id, "status": "not_found"})
        return deletion_results

    async def aclear_documents(self):
        """Mock clearing all documents."""
        self.documents.clear()
        return {"status": "success", "message": "All documents cleared"}

    async def apipeline_status(self):
        """Mock pipeline status."""
        return {
            "autoscanned": True,
            "busy": False,
            "job_name": "test_job",
            "job_start": None,
            "docs": len(self.documents),
            "batchs": 1,
            "cur_batch": 1,
            "request_pending": False,
            "latest_message": "Test pipeline running",
            "history_messages": [],
            "update_status": {},
            "log_level": 20,
        }

    @property
    def doc_status(self):
        """Mock doc status storage."""
        return self._doc_status_storage


@pytest.fixture
async def mock_rag():
    """Create a mock LightRAG instance for testing."""
    return MockLightRAG()


@pytest.fixture
async def api_client(mock_rag):
    """Create a test client for FastAPI app with mocked RAG instance."""
    # Override RAG instance in global args and set required config for testing
    original_rag = getattr(global_args, "rag", None)
    original_rerank = getattr(global_args, "rerank_binding", None)
    original_token_secret = getattr(global_args, "token_secret", None)
    original_jwt_algorithm = getattr(global_args, "jwt_algorithm", None)

    global_args.rag = mock_rag
    global_args.rerank_binding = "null"  # Disable reranking for tests
    global_args.llm_binding = "openai"  # Set a valid LLM binding
    global_args.embedding_binding = "openai"  # Set a valid embedding binding
    global_args.token_secret = "test_secret"  # Set test JWT secret
    global_args.jwt_algorithm = "HS256"  # Set test JWT algorithm

    app = create_app(global_args)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Restore original RAG instance
    if original_rag:
        global_args.rag = original_rag
    else:
        # If there was no original rag, remove the attribute
        if hasattr(global_args, "rag"):
            delattr(global_args, "rag")

    if original_rerank:
        global_args.rerank_binding = original_rerank
    else:
        if hasattr(global_args, "rerank_binding"):
            delattr(global_args, "rerank_binding")

    if original_token_secret:
        global_args.token_secret = original_token_secret
    else:
        if hasattr(global_args, "token_secret"):
            delattr(global_args, "token_secret")

    if original_jwt_algorithm:
        global_args.jwt_algorithm = original_jwt_algorithm
    else:
        if hasattr(global_args, "jwt_algorithm"):
            delattr(global_args, "jwt_algorithm")


@pytest.fixture
async def authenticated_api_client(api_client):
    """Create an authenticated API client."""
    # Create a valid JWT token for testing
    import jwt
    import datetime

    # Create token payload
    payload = {
        "sub": "test_user",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "role": "user",
        "metadata": {},
    }

    # Generate token
    token = jwt.encode(payload, "test_secret", algorithm="HS256")

    # Set up authentication token
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    return api_client


@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_text_file(temp_upload_dir):
    """Create a sample text file for upload testing."""
    file_path = temp_upload_dir / "test_document.txt"
    file_path.write_text("This is a test document for API testing.")
    return file_path


@pytest.fixture
def sample_pdf_file(temp_upload_dir):
    """Create a sample PDF file (mock PDF)."""
    file_path = temp_upload_dir / "test_document.pdf"
    # Create a minimal PDF-like file
    file_path.write_bytes(b"%PDF-1.4\n%Mock PDF for testing\n")
    return file_path


@pytest.fixture
def invalid_file(temp_upload_dir):
    """Create an invalid file for negative testing."""
    file_path = temp_upload_dir / "invalid.xyz"
    file_path.write_bytes(b"Invalid file content")
    return file_path


@pytest.fixture
async def test_documents():
    """Create test document data."""
    return [
        {
            "content": "This is the first test document with some content.",
            "metadata": {"source": "test1.txt", "type": "text"},
        },
        {
            "content": "This is the second test document with different content.",
            "metadata": {"source": "test2.txt", "type": "text"},
        },
    ]


class APIResponseValidator:
    """Helper class to validate API responses."""

    @staticmethod
    def assert_success_response(response: httpx.Response, expected_status: int = 200):
        """Assert that response indicates success."""
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}"
        )

        data = response.json()
        assert "status" in data or "response" in data, (
            "Response should have status or response field"
        )
        return data

    @staticmethod
    def assert_error_response(response: httpx.Response, expected_status: int = None):
        """Assert that response indicates error."""
        if expected_status:
            assert response.status_code == expected_status, (
                f"Expected {expected_status}, got {response.status_code}"
            )
        else:
            assert response.status_code >= 400, (
                f"Expected error status, got {response.status_code}"
            )

        data = response.json()
        assert "detail" in data or "error" in data, (
            "Error response should have detail or error field"
        )
        return data

    @staticmethod
    def assert_schema_valid(data: dict, schema_model: BaseModel):
        """Assert that data matches expected schema."""
        try:
            schema_model.model_validate(data)
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")


@pytest.fixture
def response_validator():
    """Create API response validator fixture."""
    return APIResponseValidator()


# Test data fixtures
@pytest.fixture
def document_insert_request_data():
    """Sample document insert request data."""
    return {
        "text": "This is a test document for insertion.",
        "file_source": "test_source.txt",
    }


@pytest.fixture
def documents_insert_request_data():
    """Sample multiple documents insert request data."""
    return {
        "texts": [
            "First test document content.",
            "Second test document content.",
            "Third test document content.",
        ],
        "file_sources": ["source1.txt", "source2.txt", "source3.txt"],
    }


@pytest.fixture
def delete_document_request():
    """Sample delete document request."""
    return {
        "doc_ids": ["doc_1", "doc_2"],
        "delete_file": True,
        "delete_llm_cache": False,
    }
