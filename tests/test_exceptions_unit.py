"""
Unit tests for lightrag.exceptions module
Provides high-impact coverage for exception handling utilities
"""

import pytest
import httpx
from unittest.mock import Mock


# Import exceptions directly to avoid torch import issues
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lightrag.exceptions import (
    APIStatusError,
    APIConnectionError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    RateLimitError,
    APITimeoutError,
    StorageNotInitializedError,
    PipelineNotInitializedError,
    PipelineCancelledException,
    ChunkTokenLimitExceededError,
    DataMigrationError,
)


class TestAPIStatusError:
    """Test API status error base class"""

    def test_api_status_error_creation(self):
        """Test API status error creation with response"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.headers = {"x-request-id": "test-123"}

        error = APIStatusError(
            "Not found", response=mock_response, body={"error": "details"}
        )

        assert str(error) == "Not found"
        assert error.response == mock_response
        assert error.status_code == 404
        assert error.request_id == "test-123"
        assert error.body == {"error": "details"}

    def test_api_status_error_without_request_id(self):
        """Test API status error without request ID"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.headers = {}

        error = APIStatusError("Server error", response=mock_response, body=None)

        assert error.request_id is None
        assert error.body is None


class TestAPIConnectionError:
    """Test API connection error"""

    def test_connection_error_creation(self):
        """Test connection error creation"""
        mock_request = Mock(spec=httpx.Request)

        error = APIConnectionError(request=mock_request)

        assert str(error) == "Connection error."
        assert error.request == mock_request

    def test_connection_error_with_custom_message(self):
        """Test connection error with custom message"""
        mock_request = Mock(spec=httpx.Request)

        error = APIConnectionError(message="Custom message", request=mock_request)

        assert str(error) == "Custom message"


class TestAPIStatusSubclasses:
    """Test specific API status error subclasses"""

    def test_bad_request_error(self):
        """Test bad request error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.headers = {}

        error = BadRequestError("Invalid input", response=mock_response, body=None)

        assert error.status_code == 400
        assert isinstance(error, APIStatusError)

    def test_authentication_error(self):
        """Test authentication error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.headers = {}

        error = AuthenticationError("Unauthorized", response=mock_response, body=None)

        assert error.status_code == 401
        assert isinstance(error, APIStatusError)

    def test_permission_denied_error(self):
        """Test permission denied error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.headers = {}

        error = PermissionDeniedError(
            "Access denied", response=mock_response, body=None
        )

        assert error.status_code == 403
        assert isinstance(error, APIStatusError)

    def test_not_found_error(self):
        """Test not found error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.headers = {}

        error = NotFoundError("Resource not found", response=mock_response, body=None)

        assert error.status_code == 404
        assert isinstance(error, APIStatusError)

    def test_conflict_error(self):
        """Test conflict error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 409
        mock_response.headers = {}

        error = ConflictError("Resource conflict", response=mock_response, body=None)

        assert error.status_code == 409
        assert isinstance(error, APIStatusError)

    def test_unprocessable_entity_error(self):
        """Test unprocessable entity error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.headers = {}

        error = UnprocessableEntityError(
            "Invalid data", response=mock_response, body=None
        )

        assert error.status_code == 422
        assert isinstance(error, APIStatusError)

    def test_rate_limit_error(self):
        """Test rate limit error"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {}

        error = RateLimitError("Rate limit exceeded", response=mock_response, body=None)

        assert error.status_code == 429
        assert isinstance(error, APIStatusError)


class TestAPITimeoutError:
    """Test API timeout error"""

    def test_timeout_error_creation(self):
        """Test timeout error creation"""
        mock_request = Mock(spec=httpx.Request)

        error = APITimeoutError(request=mock_request)

        assert str(error) == "Request timed out."
        assert error.request == mock_request
        assert isinstance(error, APIConnectionError)


class TestStorageNotInitializedError:
    """Test storage not initialized error"""

    def test_storage_not_initialized_default(self):
        """Test default storage not initialized error"""
        error = StorageNotInitializedError()

        assert "Storage not initialized" in str(error)
        assert "await rag.initialize_storages()" in str(error)
        assert isinstance(error, RuntimeError)

    def test_storage_not_initialized_custom_type(self):
        """Test storage not initialized error with custom type"""
        error = StorageNotInitializedError("Neo4j")

        assert "Neo4j not initialized" in str(error)
        assert isinstance(error, RuntimeError)


class TestPipelineNotInitializedError:
    """Test pipeline not initialized error"""

    def test_pipeline_not_initialized_default(self):
        """Test default pipeline not initialized error"""
        error = PipelineNotInitializedError()

        assert "Pipeline namespace '' not found" in str(error)
        assert "initialize_storages()" in str(error)
        assert isinstance(error, KeyError)

    def test_pipeline_not_initialized_with_namespace(self):
        """Test pipeline not initialized error with namespace"""
        error = PipelineNotInitializedError("test_workspace")

        assert "Pipeline namespace 'test_workspace' not found" in str(error)
        assert isinstance(error, KeyError)


class TestPipelineCancelledException:
    """Test pipeline cancelled exception"""

    def test_pipeline_cancelled_default(self):
        """Test default pipeline cancelled exception"""
        error = PipelineCancelledException()

        assert str(error) == "User cancelled"
        assert error.message == "User cancelled"

    def test_pipeline_cancelled_custom_message(self):
        """Test pipeline cancelled exception with custom message"""
        error = PipelineCancelledException("Operation cancelled by user")

        assert str(error) == "Operation cancelled by user"
        assert error.message == "Operation cancelled by user"


class TestChunkTokenLimitExceededError:
    """Test chunk token limit exceeded error"""

    def test_chunk_token_limit_basic(self):
        """Test basic chunk token limit error"""
        error = ChunkTokenLimitExceededError(chunk_tokens=1500, chunk_token_limit=1000)

        assert "1500 exceeds 1000" in str(error)
        assert error.chunk_tokens == 1500
        assert error.chunk_token_limit == 1000
        assert error.chunk_preview is None
        assert isinstance(error, ValueError)

    def test_chunk_token_limit_with_preview(self):
        """Test chunk token limit error with preview"""
        preview = "This is a long chunk of text that exceeds the token limit"
        error = ChunkTokenLimitExceededError(
            chunk_tokens=1500, chunk_token_limit=1000, chunk_preview=preview
        )

        assert "1500 exceeds 1000" in str(error)
        assert "Preview:" in str(error)
        assert "This is a long chunk of text that exceeds" in str(error)
        assert error.chunk_preview == "This is a long chunk of text that exceeds"

    def test_chunk_token_limit_with_short_preview(self):
        """Test chunk token limit error with short preview"""
        preview = "Short text"
        error = ChunkTokenLimitExceededError(
            chunk_tokens=1500, chunk_token_limit=1000, chunk_preview=preview
        )

        assert "1500 exceeds 1000" in str(error)
        assert "Preview:" not in str(error)  # Should not show preview for short text
        assert error.chunk_preview == "Short text"

    def test_chunk_token_limit_with_whitespace_preview(self):
        """Test chunk token limit error with whitespace preview"""
        preview = "  Short text with spaces  "
        error = ChunkTokenLimitExceededError(
            chunk_tokens=1500, chunk_token_limit=1000, chunk_preview=preview
        )

        assert error.chunk_preview == "Short text with spaces"
        assert "1500 exceeds 1000" in str(error)


class TestDataMigrationError:
    """Test data migration error"""

    def test_data_migration_error_creation(self):
        """Test data migration error creation"""
        error = DataMigrationError("Migration failed: incompatible schema")

        assert str(error) == "Migration failed: incompatible schema"
        assert error.message == "Migration failed: incompatible schema"
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test the complete exception hierarchy"""

    def test_api_timeout_inheritance(self):
        """Test that APITimeoutError inherits correctly"""
        mock_request = Mock(spec=httpx.Request)
        error = APITimeoutError(request=mock_request)

        assert isinstance(error, APIConnectionError)
        assert isinstance(error, Exception)

    def test_status_error_subclasses_inheritance(self):
        """Test that all status error subclasses inherit correctly"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.headers = {}

        subclasses = [
            BadRequestError,
            AuthenticationError,
            PermissionDeniedError,
            NotFoundError,
            ConflictError,
            UnprocessableEntityError,
            RateLimitError,
        ]

        for error_class in subclasses:
            error = error_class("Test", response=mock_response, body=None)
            assert isinstance(error, APIStatusError)
            assert isinstance(error, Exception)

    def test_runtime_error_subclasses(self):
        """Test runtime error subclasses"""
        storage_error = StorageNotInitializedError()
        assert isinstance(storage_error, RuntimeError)

    def test_key_error_subclasses(self):
        """Test key error subclasses"""
        pipeline_error = PipelineNotInitializedError("test")
        assert isinstance(pipeline_error, KeyError)

    def test_value_error_subclasses(self):
        """Test value error subclasses"""
        chunk_error = ChunkTokenLimitExceededError(1500, 1000)
        assert isinstance(chunk_error, ValueError)
