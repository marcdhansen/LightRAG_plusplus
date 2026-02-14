"""
Comprehensive API tests for document routes.
Tests document upload, status checking, deletion, and clearing operations.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from lightrag.base import DocStatus
from tests.api.conftest import (
    APIResponseValidator,
    MockLightRAG,
    document_insert_request_data,
    documents_insert_request_data,
    delete_document_request,
)


@pytest.mark.asyncio
@pytest.mark.api
class TestDocumentUpload:
    """Test document upload endpoints."""

    async def test_insert_text_document_success(
        self, api_client, response_validator, document_insert_request_data
    ):
        """Test successful single text document insertion."""
        response = await api_client.post(
            "/documents/text", json=document_insert_request_data
        )

        data = response_validator.assert_success_response(response)
        assert data["status"] in ["success", "partial_success"]
        assert "track_id" in data
        assert len(data["track_id"]) > 0
        assert "message" in data

    async def test_insert_text_document_validation_error(
        self, authenticated_api_client, response_validator
    ):
        """Test validation error for empty text document."""
        invalid_data = {
            "text": "",  # Empty text should fail validation
            "file_source": "test.txt",
        }

        response = await authenticated_api_client.post(
            "/documents/insert_text", json=invalid_data
        )
        response_validator.assert_error_response(response, 422)

    async def test_insert_multiple_text_documents_success(
        self,
        authenticated_api_client,
        response_validator,
        documents_insert_request_data,
    ):
        """Test successful multiple text documents insertion."""
        response = await authenticated_api_client.post(
            "/documents/texts", json=documents_insert_request_data
        )

        data = response_validator.assert_success_response(response)
        assert data["status"] in ["success", "partial_success"]
        assert "track_id" in data
        assert "message" in data

    async def test_insert_multiple_text_documents_mismatch_length(
        self, authenticated_api_client, response_validator
    ):
        """Test error when texts and file_sources have different lengths."""
        invalid_data = {
            "texts": ["text1", "text2"],
            "file_sources": ["source1"],  # Mismatched length
        }

        response = await authenticated_api_client.post(
            "/documents/insert_texts", json=invalid_data
        )
        response_validator.assert_error_response(response, 422)

    async def test_upload_file_success(
        self, authenticated_api_client, response_validator, sample_text_file
    ):
        """Test successful file upload."""
        with open(sample_text_file, "rb") as f:
            files = {"files": ("test_document.txt", f, "text/plain")}
            response = await authenticated_api_client.post(
                "/documents/upload", files=files
            )

        data = response_validator.assert_success_response(response)
        assert data["status"] == "success"
        assert "track_id" in data
        assert "test_document.txt" in data["message"]

    async def test_upload_multiple_files_success(
        self,
        authenticated_api_client,
        response_validator,
        sample_text_file,
        temp_upload_dir,
    ):
        """Test successful multiple file upload."""
        # Create another test file
        second_file = temp_upload_dir / "second_test.txt"
        second_file.write_text("Second test document content")

        with open(sample_text_file, "rb") as f1, open(second_file, "rb") as f2:
            files = [
                ("files", ("test_document.txt", f1, "text/plain")),
                ("files", ("second_test.txt", f2, "text/plain")),
            ]
            response = await authenticated_api_client.post(
                "/documents/upload", files=files
            )

        data = response_validator.assert_success_response(response)
        assert data["status"] in ["success", "partial_success"]
        assert "track_id" in data

    async def test_upload_unsupported_file_type(
        self, authenticated_api_client, response_validator, invalid_file
    ):
        """Test upload of unsupported file type."""
        with open(invalid_file, "rb") as f:
            files = {"files": ("invalid.xyz", f, "application/octet-stream")}
            response = await authenticated_api_client.post(
                "/documents/upload", files=files
            )

        # Should either succeed with processing error or fail validation
        # This depends on implementation details
        assert response.status_code in [200, 400, 422]

    async def test_upload_large_file(
        self, authenticated_api_client, response_validator, temp_upload_dir
    ):
        """Test upload of large file."""
        # Create a large file (>10MB)
        large_file = temp_upload_dir / "large_file.txt"
        large_content = "A" * (11 * 1024 * 1024)  # 11MB
        large_file.write_text(large_content)

        with open(large_file, "rb") as f:
            files = {"files": ("large_file.txt", f, "text/plain")}
            response = await authenticated_api_client.post(
                "/documents/upload", files=files
            )

        # Should either succeed or fail due to size limits
        assert response.status_code in [200, 413, 422]


@pytest.mark.asyncio
@pytest.mark.api
class TestDocumentStatus:
    """Test document status and listing endpoints."""

    async def test_get_document_by_id_success(
        self, authenticated_api_client, mock_rag, response_validator
    ):
        """Test getting document by ID."""
        # First, add a document to mock RAG
        await mock_rag.apipeline_enqueue_documents([{"content": "test content"}])

        # Get the first document ID
        doc_id = list(mock_rag.documents.keys())[0]

        response = await authenticated_api_client.get(f"/documents/{doc_id}")
        data = response_validator.assert_success_response(response)

        assert data["id"] == doc_id
        assert data["content_summary"] in data["content"]
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "content_length" in data

    async def test_get_document_by_id_not_found(
        self, authenticated_api_client, response_validator
    ):
        """Test getting non-existent document."""
        response = await authenticated_api_client.get("/documents/nonexistent_doc")
        response_validator.assert_error_response(response, 404)

    async def test_get_documents_by_status_all(
        self, authenticated_api_client, mock_rag, response_validator
    ):
        """Test getting all documents (no status filter)."""
        # Add test documents
        await mock_rag.apipeline_enqueue_documents(
            [{"content": "doc1"}, {"content": "doc2"}]
        )

        response = await authenticated_api_client.get("/documents/")
        data = response_validator.assert_success_response(response)

        assert "documents" in data
        assert "pagination" in data
        assert "status_counts" in data
        assert len(data["documents"]) >= 2

    async def test_get_documents_by_status_filtered(
        self, authenticated_api_client, mock_rag, response_validator
    ):
        """Test getting documents filtered by status."""
        # Add test documents
        await mock_rag.apipeline_enqueue_documents([{"content": "test doc"}])

        response = await authenticated_api_client.get("/documents/?status=PROCESSED")
        data = response_validator.assert_success_response(response)

        assert "documents" in data
        assert "pagination" in data
        # Should return documents (mock implementation may not filter properly)

    async def test_get_documents_with_pagination(
        self, authenticated_api_client, response_validator
    ):
        """Test document listing with pagination."""
        params = {"page": 1, "page_size": 10}
        response = await authenticated_api_client.get("/documents/", params=params)

        data = response_validator.assert_success_response(response)
        pagination = data["pagination"]

        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert "total_count" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination

    async def test_get_documents_sorting(
        self, authenticated_api_client, response_validator
    ):
        """Test document listing with sorting."""
        params = {"sort_field": "created_at", "sort_direction": "desc"}
        response = await authenticated_api_client.get("/documents/", params=params)

        data = response_validator.assert_success_response(response)
        assert "documents" in data
        # Verify sorting (implementation dependent)

    async def test_get_status_counts(
        self, authenticated_api_client, response_validator
    ):
        """Test getting document status counts."""
        response = await authenticated_api_client.get("/documents/status_counts")

        data = response_validator.assert_success_response(response)
        assert "status_counts" in data
        assert isinstance(data["status_counts"], dict)

    async def test_track_status_success(
        self, authenticated_api_client, mock_rag, response_validator
    ):
        """Test tracking status by track_id."""
        # Add documents to get a track ID
        track_id = await mock_rag.apipeline_enqueue_documents([{"content": "test"}])

        response = await authenticated_api_client.get(f"/documents/track/{track_id}")
        data = response_validator.assert_success_response(response)

        assert data["track_id"] == track_id
        assert "documents" in data
        assert "total_count" in data
        assert "status_summary" in data

    async def test_track_status_not_found(
        self, authenticated_api_client, response_validator
    ):
        """Test tracking non-existent track_id."""
        response = await authenticated_api_client.get(
            "/documents/track/nonexistent_track"
        )
        response_validator.assert_error_response(response, 404)


@pytest.mark.asyncio
@pytest.mark.api
class TestDocumentDeletion:
    """Test document deletion endpoints."""

    async def test_delete_documents_success(
        self,
        authenticated_api_client,
        mock_rag,
        response_validator,
        delete_document_request,
    ):
        """Test successful document deletion."""
        # First add documents
        await mock_rag.apipeline_enqueue_documents(
            [{"content": "doc1"}, {"content": "doc2"}]
        )

        # Delete the documents
        response = await authenticated_api_client.post(
            "/documents/delete", json=delete_document_request
        )
        data = response_validator.assert_success_response(response)

        assert data["status"] == "success"
        assert "message" in data

    async def test_delete_documents_not_found(
        self, authenticated_api_client, response_validator
    ):
        """Test deletion of non-existent documents."""
        delete_data = {
            "doc_ids": ["nonexistent1", "nonexistent2"],
            "delete_file": False,
            "delete_llm_cache": False,
        }

        response = await authenticated_api_client.post(
            "/documents/delete", json=delete_data
        )
        data = response_validator.assert_success_response(response)

        # Should still return success but indicate which docs were not found
        assert data["status"] in ["success", "partial_success"]

    async def test_delete_documents_empty_list(
        self, authenticated_api_client, response_validator
    ):
        """Test deletion with empty document list."""
        delete_data = {"doc_ids": [], "delete_file": False, "delete_llm_cache": False}

        response = await authenticated_api_client.post(
            "/documents/delete", json=delete_data
        )
        response_validator.assert_error_response(response, 422)

    async def test_delete_entity_by_name_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful entity deletion."""
        delete_data = {"entity_name": "test_entity"}

        # Mock entity deletion endpoint
        with patch.object(MockLightRAG, "adelete_entity") as mock_delete:
            mock_delete.return_value = {
                "status": "success",
                "message": "Entity deleted",
            }

            response = await authenticated_api_client.post(
                "/graphs/entities/delete", json=delete_data
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"

    async def test_delete_entity_empty_name(
        self, authenticated_api_client, response_validator
    ):
        """Test entity deletion with empty name."""
        delete_data = {"entity_name": ""}

        response = await authenticated_api_client.post(
            "/graphs/entities/delete", json=delete_data
        )
        response_validator.assert_error_response(response, 422)

    async def test_delete_relation_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful relationship deletion."""
        delete_data = {"source_entity": "entity1", "target_entity": "entity2"}

        with patch.object(MockLightRAG, "adelete_relation") as mock_delete:
            mock_delete.return_value = {
                "status": "success",
                "message": "Relation deleted",
            }

            response = await authenticated_api_client.post(
                "/graphs/relations/delete", json=delete_data
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"

    async def test_delete_failed_documents_while_pipeline_busy(
        self,
        authenticated_api_client,
        mock_rag,
        response_validator,
    ):
        """Test that failed documents can be deleted while pipeline is busy.

        This tests the fix for GitHub Issue #2690:
        Allow deleting individual documents while pipeline is busy.

        Documents with status='failed' should be deletable even when
        pipeline_busy is True.
        """
        # First add documents with failed status
        await mock_rag.apipeline_enqueue_documents([{"content": "doc1"}])

        # Simulate setting document as failed
        for doc_id, doc_data in mock_rag.documents.items():
            doc_data["status"] = DocStatus.FAILED

        # Mock pipeline as busy using the shared_storage mechanism
        with patch(
            "lightrag.api.routers.document_routes.get_namespace_data"
        ) as mock_get_data:
            # Return busy=True for pipeline_status
            mock_get_data.return_value = {"busy": True}

            # Try to delete failed documents - should succeed
            delete_data = {
                "doc_ids": list(mock_rag.documents.keys()),
                "delete_file": False,
                "delete_llm_cache": False,
            }

            response = await authenticated_api_client.post(
                "/documents/delete", json=delete_data
            )

            # Should NOT return busy status - deletion should be allowed for failed docs
            data = response.json()
            assert data.get("status") != "busy", (
                "Failed documents should be deletable even when pipeline is busy"
            )

            # Should NOT return busy status - deletion should be allowed
            data = response.json()
            assert data.get("status") != "busy", (
                "Failed documents should be deletable even when pipeline is busy"
            )


@pytest.mark.asyncio
@pytest.mark.api
class TestDocumentManagement:
    """Test document management endpoints."""

    async def test_scan_documents_success(
        self, authenticated_api_client, response_validator
    ):
        """Test document scanning endpoint."""
        response = await authenticated_api_client.post("/documents/scan")

        data = response_validator.assert_success_response(response)
        assert data["status"] == "scanning_started"
        assert "track_id" in data
        assert len(data["track_id"]) > 0

    async def test_reprocess_failed_documents_success(
        self, authenticated_api_client, response_validator
    ):
        """Test reprocessing failed documents."""
        response = await authenticated_api_client.post("/documents/reprocess")

        data = response_validator.assert_success_response(response)
        assert data["status"] == "reprocessing_started"
        assert "message" in data
        assert data["track_id"] == ""  # Track ID is empty for reprocess

    async def test_cancel_pipeline_success(
        self, authenticated_api_client, response_validator
    ):
        """Test pipeline cancellation."""
        response = await authenticated_api_client.post("/documents/cancel_pipeline")

        data = response_validator.assert_success_response(response)
        assert data["status"] in ["cancellation_requested", "not_busy"]
        assert "message" in data

    async def test_clear_documents_success(
        self, authenticated_api_client, response_validator
    ):
        """Test clearing all documents."""
        response = await authenticated_api_client.post("/documents/clear")

        data = response_validator.assert_success_response(response)
        assert data["status"] == "success"
        assert "message" in data

    async def test_clear_cache_success(
        self, authenticated_api_client, response_validator
    ):
        """Test cache clearing."""
        response = await authenticated_api_client.post(
            "/documents/clear_cache", json={}
        )

        data = response_validator.assert_success_response(response)
        assert data["status"] == "success"
        assert "message" in data

    async def test_get_pipeline_status(
        self, authenticated_api_client, response_validator
    ):
        """Test getting pipeline status."""
        response = await authenticated_api_client.get("/documents/pipeline_status")

        data = response_validator.assert_success_response(response)
        required_fields = [
            "autoscanned",
            "busy",
            "job_name",
            "job_start",
            "docs",
            "batchs",
            "cur_batch",
            "request_pending",
            "latest_message",
            "log_level",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    async def test_update_log_level(self, authenticated_api_client, response_validator):
        """Test updating pipeline log level."""
        update_data = {"log_level": 20}  # INFO level

        response = await authenticated_api_client.post(
            "/documents/log_level", json=update_data
        )
        data = response_validator.assert_success_response(response)

        assert data["status"] == "success"
        assert "message" in data

    async def test_update_log_level_invalid(
        self, authenticated_api_client, response_validator
    ):
        """Test updating with invalid log level."""
        update_data = {"log_level": 99}  # Invalid level

        response = await authenticated_api_client.post(
            "/documents/log_level", json=update_data
        )
        response_validator.assert_error_response(response, 422)


@pytest.mark.asyncio
@pytest.mark.api
class TestDocumentEndpointsAuthentication:
    """Test authentication and authorization for document endpoints."""

    async def test_unauthorized_access(self, api_client, response_validator):
        """Test that unauthenticated requests are rejected."""
        response = await api_client.get("/documents/")
        response_validator.assert_error_response(response, 401)

    async def test_invalid_token(self, api_client, response_validator):
        """Test that invalid tokens are rejected."""
        api_client.headers.update({"Authorization": "Bearer invalid_token"})

        response = await api_client.get("/documents/")
        response_validator.assert_error_response(response, 401)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/documents/",
            "/documents/status_counts",
            "/documents/pipeline_status",
            "/documents/scan",
            "/documents/clear",
            "/documents/clear_cache",
        ],
    )
    async def test_protected_endpoints_require_auth(
        self, api_client, response_validator, endpoint
    ):
        """Test that protected endpoints require authentication."""
        response = (
            await api_client.get(endpoint)
            if endpoint.startswith("GET")
            else await api_client.post(endpoint)
        )
        response_validator.assert_error_response(response, 401)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.error_handling
class TestDocumentEndpointsErrorHandling:
    """Test error handling and edge cases."""

    async def test_malformed_json_request(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of malformed JSON requests."""
        response = await authenticated_api_client.post(
            "/documents/insert_text",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        response_validator.assert_error_response(response, 422)

    async def test_missing_required_fields(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of missing required fields."""
        # Missing 'text' field
        incomplete_data = {"file_source": "test.txt"}

        response = await authenticated_api_client.post(
            "/documents/insert_text", json=incomplete_data
        )
        response_validator.assert_error_response(response, 422)

    async def test_invalid_pagination_parameters(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of pagination parameters."""
        # Invalid page number
        params = {"page": -1, "page_size": 10}
        response = await authenticated_api_client.get("/documents/", params=params)
        response_validator.assert_error_response(response, 422)

        # Invalid page size
        params = {"page": 1, "page_size": 1000}  # Too large
        response = await authenticated_api_client.get("/documents/", params=params)
        response_validator.assert_error_response(response, 422)

    async def test_invalid_sort_parameters(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of sort parameters."""
        # Invalid sort field
        params = {"sort_field": "invalid_field", "sort_direction": "asc"}
        response = await authenticated_api_client.get("/documents/", params=params)
        response_validator.assert_error_response(response, 422)

        # Invalid sort direction
        params = {"sort_field": "created_at", "sort_direction": "invalid"}
        response = await authenticated_api_client.get("/documents/", params=params)
        response_validator.assert_error_response(response, 422)

    async def test_content_too_large(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of content that's too large."""
        large_content = "x" * (10 * 1024 * 1024 + 1)  # >10MB
        data = {"text": large_content}

        response = await authenticated_api_client.post(
            "/documents/insert_text", json=data
        )
        # Should either succeed or fail with 413/422
        assert response.status_code in [200, 413, 422]


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
class TestDocumentEndpointsIntegration:
    """Integration tests for document endpoints."""

    async def test_document_lifecycle_workflow(
        self, authenticated_api_client, mock_rag, response_validator
    ):
        """Test complete document lifecycle: upload -> check status -> delete."""
        # 1. Upload document
        insert_data = {
            "text": "Integration test document",
            "file_source": "integration_test.txt",
        }
        upload_response = await authenticated_api_client.post(
            "/documents/insert_text", json=insert_data
        )
        upload_data = response_validator.assert_success_response(upload_response)
        track_id = upload_data["track_id"]

        # 2. Check status
        status_response = await authenticated_api_client.get(
            f"/documents/track/{track_id}"
        )
        status_data = response_validator.assert_success_response(status_response)
        assert status_data["total_count"] >= 1

        # 3. Get document details (if we can extract doc_id)
        if status_data["documents"]:
            doc_id = status_data["documents"][0]["id"]
            doc_response = await authenticated_api_client.get(f"/documents/{doc_id}")
            doc_data = response_validator.assert_success_response(doc_response)
            assert doc_data["content_summary"] == "Integration test document"

        # 4. Delete documents (if we can identify them)
        doc_ids_to_delete = [doc["id"] for doc in status_data.get("documents", [])]
        if doc_ids_to_delete:
            delete_data = {
                "doc_ids": doc_ids_to_delete,
                "delete_file": False,
                "delete_llm_cache": False,
            }
            delete_response = await authenticated_api_client.post(
                "/documents/delete", json=delete_data
            )
            delete_data_result = response_validator.assert_success_response(
                delete_response
            )
            assert delete_data_result["status"] == "success"

    async def test_batch_operations_performance(
        self, authenticated_api_client, response_validator, temp_upload_dir
    ):
        """Test performance with batch operations."""
        # Create multiple test files
        files_data = []
        for i in range(5):
            file_path = temp_upload_dir / f"batch_test_{i}.txt"
            file_path.write_text(f"Batch test document {i}")
            files_data.append(
                ("files", (f"batch_test_{i}.txt", open(file_path, "rb"), "text/plain"))
            )

        # Upload multiple files
        with contextlib.ExitStack() as stack:
            files = [stack.enter_context(open(f[1], "rb")) for f in files_data]
            multipart_files = [
                (f[0], (f[1], file, f[2])) for f, file in zip(files_data, files)
            ]
            response = await authenticated_api_client.post(
                "/documents/upload", files=multipart_files
            )

        data = response_validator.assert_success_response(response)
        assert data["status"] in ["success", "partial_success"]

        # Test getting all documents
        list_response = await authenticated_api_client.get("/documents/")
        list_data = response_validator.assert_success_response(list_response)
        assert len(list_data["documents"]) >= 5


# Import contextlib for the performance test
import contextlib
