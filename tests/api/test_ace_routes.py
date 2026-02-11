"""
Comprehensive API tests for ACE (Automated Curator and Explorer) routes.
Tests all ACE-related endpoints including pending repairs, approval, and rejection workflows.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from tests.api.conftest import (
    APIResponseValidator,
    MockLightRAG,
)


class MockACEResponse:
    """Mock ACE response data for testing."""

    @staticmethod
    def pending_repairs():
        return [
            {
                "repair_id": "repair_001",
                "entity_name": "Elon Musk",
                "issue_type": "duplicate_entity",
                "description": "Duplicate entity 'Elon Msk' detected",
                "suggested_action": "Merge into 'Elon Musk'",
                "confidence": 0.95,
                "created_at": "2024-01-01T00:00:00Z",
                "status": "pending",
            },
            {
                "repair_id": "repair_002",
                "entity_name": "Tesla",
                "issue_type": "missing_relation",
                "description": "Missing relation between 'Tesla' and 'CEO'",
                "suggested_action": "Add relation 'CEO_OF'",
                "confidence": 0.87,
                "created_at": "2024-01-01T01:00:00Z",
                "status": "pending",
            },
        ]

    @staticmethod
    def approve_response():
        return {"status": "success", "message": "Repair repair_001 approved"}

    @staticmethod
    def reject_response():
        return {"status": "success", "message": "Repair repair_002 rejected"}

    @staticmethod
    def not_found_response():
        return {"detail": "Repair not found"}


@pytest.mark.asyncio
@pytest.mark.api
class TestACERepairManagement:
    """Test ACE repair management endpoints."""

    async def test_get_pending_repairs_success(
        self, authenticated_api_client, response_validator
    ):
        """Test getting pending ACE repairs."""
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.get_pending_repairs.return_value = (
                MockACEResponse.pending_repairs()
            )

            response = await authenticated_api_client.get("/ace/repairs/pending")
            data = response_validator.assert_success_response(response)

            assert isinstance(data, list)
            assert len(data) == 2

            # Verify repair structure
            repair = data[0]
            assert "repair_id" in repair
            assert "entity_name" in repair
            assert "issue_type" in repair
            assert "description" in repair
            assert "suggested_action" in repair
            assert "confidence" in repair
            assert "created_at" in repair
            assert "status" in repair
            assert repair["status"] == "pending"
            assert repair["confidence"] == 0.95

    async def test_get_pending_repairs_no_curator(
        self, authenticated_api_client, response_validator
    ):
        """Test getting pending repairs when ACE curator not initialized."""
        # Mock rag without ace_curator
        with patch.object(MockLightRAG, "__dict__", {}):
            response = await authenticated_api_client.get("/ace/repairs/pending")
            data = response_validator.assert_success_response(response)

            assert data == []  # Should return empty list

    async def test_approve_repair_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful repair approval."""
        repair_id = "repair_001"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.return_value = True

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "repair_001" in data["message"]
            assert "approved" in data["message"]
            mock_curator.approve_repair.assert_called_once_with(repair_id)

    async def test_approve_repair_not_found(
        self, authenticated_api_client, response_validator
    ):
        """Test approving non-existent repair."""
        repair_id = "nonexistent_repair"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.return_value = False

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            data = response_validator.assert_error_response(response, 404)

            assert data["detail"] == "Repair not found"
            mock_curator.approve_repair.assert_called_once_with(repair_id)

    async def test_approve_repair_no_curator(
        self, authenticated_api_client, response_validator
    ):
        """Test approving repair when ACE curator not initialized."""
        repair_id = "repair_001"

        with patch.object(MockLightRAG, "__dict__", {}):
            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            data = response_validator.assert_error_response(response, 400)

            assert "ACE Curator not initialized" in data["detail"]

    async def test_reject_repair_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful repair rejection."""
        repair_id = "repair_002"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.reject_repair.return_value = True

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "repair_002" in data["message"]
            assert "rejected" in data["message"]
            mock_curator.reject_repair.assert_called_once_with(repair_id)

    async def test_reject_repair_not_found(
        self, authenticated_api_client, response_validator
    ):
        """Test rejecting non-existent repair."""
        repair_id = "nonexistent_repair"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.reject_repair.return_value = False

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )
            data = response_validator.assert_error_response(response, 404)

            assert data["detail"] == "Repair not found"
            mock_curator.reject_repair.assert_called_once_with(repair_id)

    async def test_reject_repair_no_curator(
        self, authenticated_api_client, response_validator
    ):
        """Test rejecting repair when ACE curator not initialized."""
        repair_id = "repair_002"

        with patch.object(MockLightRAG, "__dict__", {}):
            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )
            data = response_validator.assert_error_response(response, 400)

            assert "ACE Curator not initialized" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.validation
class TestACEParameterValidation:
    """Test parameter validation for ACE routes."""

    async def test_repair_id_validation(
        self, authenticated_api_client, response_validator
    ):
        """Test repair ID parameter validation."""
        # Test empty repair ID (should still work)
        response = await authenticated_api_client.post("/ace/repairs//approve")
        # FastAPI will handle this as 404 for invalid path format

        # Test special characters in repair ID
        special_chars_id = "repair_with_@#$%_chars"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.return_value = False

            response = await authenticated_api_client.post(
                f"/ace/repairs/{special_chars_id}/approve"
            )
            # Should handle special chars gracefully
            data = response_validator.assert_error_response(response, 404)
            mock_curator.approve_repair.assert_called_once_with(special_chars_id)

    async def test_repair_id_length_validation(
        self, authenticated_api_client, response_validator
    ):
        """Test repair ID length validation."""
        # Test very long repair ID
        long_id = "repair_" + "a" * 1000  # 1007 characters

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.return_value = False

            response = await authenticated_api_client.post(
                f"/ace/repairs/{long_id}/approve"
            )
            # Should handle long IDs gracefully
            mock_curator.approve_repair.assert_called_once_with(long_id)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.error_handling
class TestACEErrorHandling:
    """Test error handling for ACE routes."""

    async def test_ace_routes_unauthorized_access(self, api_client, response_validator):
        """Test that unauthenticated requests are rejected."""
        endpoints = [
            "/ace/repairs/pending",
            "/ace/repairs/repair_001/approve",
            "/ace/repairs/repair_002/reject",
        ]

        for endpoint in endpoints:
            if "approve" in endpoint or "reject" in endpoint:
                response = await api_client.post(endpoint)
            else:
                response = await api_client.get(endpoint)
            response_validator.assert_error_response(response, 401)

    async def test_curator_exception_handling(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of curator method exceptions."""
        repair_id = "repair_001"

        # Test get_pending_repairs exception
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.get_pending_repairs.side_effect = Exception("Database error")

            response = await authenticated_api_client.get("/ace/repairs/pending")
            response_validator.assert_error_response(response, 500)

        # Test approve_repair exception
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.side_effect = Exception(
                "Database update failed"
            )

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            response_validator.assert_error_response(response, 500)

        # Test reject_repair exception
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.reject_repair.side_effect = Exception("Database update failed")

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )
            response_validator.assert_error_response(response, 500)

    async def test_concurrent_repair_operations(
        self, authenticated_api_client, response_validator
    ):
        """Test concurrent repair operations."""
        import asyncio

        repair_id = "repair_concurrent"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.approve_repair.return_value = True
            mock_curator.reject_repair.return_value = True

            # Send concurrent approve and reject for same repair
            approve_task = authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            reject_task = authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )

            responses = await asyncio.gather(
                approve_task, reject_task, return_exceptions=True
            )

            # Both should complete but one might be invalid state
            for response in responses:
                if not isinstance(response, Exception):
                    # Should either be success or conflict
                    assert response.status_code in [200, 409, 422]

    async def test_repair_id_injection_attempts(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of potential injection in repair IDs."""
        # Test various injection patterns
        injection_attempts = [
            "../../admin/repair_001",  # Path traversal
            "repair_001'; DROP TABLE repairs; --",  # SQL injection
            "repair_001<script>alert('xss')</script>",  # XSS injection
            "repair_001\napprove",  # Line break injection
        ]

        for malicious_id in injection_attempts:
            with patch.object(MockLightRAG, "ace_curator") as mock_curator:
                mock_curator.approve_repair.return_value = False

                response = await authenticated_api_client.post(
                    f"/ace/repairs/{malicious_id}/approve"
                )
                # Should handle malicious input gracefully
                assert response.status_code in [400, 404, 422]

    async def test_ace_service_unavailable(
        self, authenticated_api_client, response_validator
    ):
        """Test ACE behavior when service is temporarily unavailable."""
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            # Simulate service unavailable
            mock_curator.get_pending_repairs.side_effect = ConnectionError(
                "Service unavailable"
            )
            mock_curator.approve_repair.side_effect = ConnectionError(
                "Service unavailable"
            )
            mock_curator.reject_repair.side_effect = ConnectionError(
                "Service unavailable"
            )

            # Test pending repairs
            response = await authenticated_api_client.get("/ace/repairs/pending")
            response_validator.assert_error_response(response, 500)

            # Test approve repair
            response = await authenticated_api_client.post(
                "/ace/repairs/repair_001/approve"
            )
            response_validator.assert_error_response(response, 500)

            # Test reject repair
            response = await authenticated_api_client.post(
                "/ace/repairs/repair_002/reject"
            )
            response_validator.assert_error_response(response, 500)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
class TestACEIntegration:
    """Integration tests for ACE routes."""

    async def test_complete_repair_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complete repair workflow: pending -> approve/reject."""
        # 1. Get pending repairs
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.get_pending_repairs.return_value = (
                MockACEResponse.pending_repairs()
            )

            response = await authenticated_api_client.get("/ace/repairs/pending")
            pending_data = response_validator.assert_success_response(response)

            assert len(pending_data) == 2
            repair_id_1 = pending_data[0]["repair_id"]
            repair_id_2 = pending_data[1]["repair_id"]

        # 2. Approve first repair
        mock_curator.approve_repair.return_value = True

        response = await authenticated_api_client.post(
            f"/ace/repairs/{repair_id_1}/approve"
        )
        approve_data = response_validator.assert_success_response(response)

        assert approve_data["status"] == "success"
        assert "approved" in approve_data["message"]
        mock_curator.approve_repair.assert_called_with(repair_id_1)

        # 3. Reject second repair
        mock_curator.reject_repair.return_value = True

        response = await authenticated_api_client.post(
            f"/ace/repairs/{repair_id_2}/reject"
        )
        reject_data = response_validator.assert_success_response(response)

        assert reject_data["status"] == "success"
        assert "rejected" in reject_data["message"]
        mock_curator.reject_repair.assert_called_with(repair_id_2)

    async def test_batch_repair_operations(
        self, authenticated_api_client, response_validator
    ):
        """Test batch processing of multiple repairs."""
        # Simulate multiple pending repairs
        batch_repairs = [
            {
                "repair_id": f"repair_batch_{i}",
                "entity_name": f"Entity_{i}",
                "issue_type": "duplicate_entity",
                "description": f"Duplicate entity for Entity_{i}",
                "suggested_action": "Merge entities",
                "confidence": 0.8 + (i * 0.05),
                "created_at": f"2024-01-01T{i:02d}:00Z",
                "status": "pending",
            }
            for i in range(5)
        ]

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.get_pending_repairs.return_value = batch_repairs
            mock_curator.approve_repair.return_value = True
            mock_curator.reject_repair.return_value = True

            # Get all pending repairs
            response = await authenticated_api_client.get("/ace/repairs/pending")
            data = response_validator.assert_success_response(response)

            assert len(data) == 5

            # Approve first 2 repairs
            for i in range(2):
                repair_id = batch_repairs[i]["repair_id"]
                response = await authenticated_api_client.post(
                    f"/ace/repairs/{repair_id}/approve"
                )
                response_validator.assert_success_response(response)

                mock_curator.approve_repair.assert_called_with(repair_id)

            # Reject remaining 3 repairs
            for i in range(2, 5):
                repair_id = batch_repairs[i]["repair_id"]
                response = await authenticated_api_client.post(
                    f"/ace/repairs/{repair_id}/reject"
                )
                response_validator.assert_success_response(response)

                mock_curator.reject_repair.assert_called_with(repair_id)

    async def test_repair_conflict_resolution(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of repair operation conflicts."""
        repair_id = "conflict_repair"

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            # Simulate conflict: repair already processed
            mock_curator.approve_repair.side_effect = ValueError(
                "Repair already processed"
            )

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            response_validator.assert_error_response(response, 400)

            assert "already processed" in response.json()["detail"]

            # Test rejection conflict
            mock_curator.reject_repair.side_effect = ValueError(
                "Repair already processed"
            )

            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/reject"
            )
            response_validator.assert_error_response(response, 400)

    async def test_repair_data_consistency(
        self, authenticated_api_client, response_validator
    ):
        """Test data consistency across repair operations."""
        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            # Mock consistent repair data
            repair_data = MockACEResponse.pending_repairs()[0]
            mock_curator.get_pending_repairs.return_value = [repair_data]
            mock_curator.approve_repair.return_value = True

            # Get pending repairs
            response = await authenticated_api_client.get("/ace/repairs/pending")
            pending_data = response_validator.assert_success_response(response)

            assert len(pending_data) == 1
            assert pending_data[0]["repair_id"] == repair_data["repair_id"]
            assert pending_data[0]["entity_name"] == repair_data["entity_name"]
            assert pending_data[0]["confidence"] == repair_data["confidence"]

            # Approve repair
            repair_id = repair_data["repair_id"]
            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            approve_data = response_validator.assert_success_response(response)

            # Verify data consistency in response
            assert repair_id in approve_data["message"]
            mock_curator.approve_repair.assert_called_with(repair_id)

    async def test_ace_with_graph_operations(
        self, authenticated_api_client, response_validator
    ):
        """Test ACE integration with graph operations."""
        # Simulate scenario where ACE suggests graph modifications
        repair_with_graph_ops = {
            "repair_id": "graph_repair_001",
            "entity_name": "TestEntity",
            "issue_type": "graph_structure",
            "description": "Suggested graph restructuring",
            "suggested_action": "merge_entities",
            "suggested_entities": ["Variant1", "Variant2"],
            "target_entity": "CanonicalEntity",
            "confidence": 0.92,
            "created_at": "2024-01-01T00:00:00Z",
            "status": "pending",
        }

        with patch.object(MockLightRAG, "ace_curator") as mock_curator:
            mock_curator.get_pending_repairs.return_value = [repair_with_graph_ops]
            mock_curator.approve_repair.return_value = True

            # Get pending repairs (should include graph operation suggestion)
            response = await authenticated_api_client.get("/ace/repairs/pending")
            data = response_validator.assert_success_response(response)

            repair = data[0]
            assert repair["issue_type"] == "graph_structure"
            assert repair["suggested_action"] == "merge_entities"
            assert "suggested_entities" in repair
            assert "target_entity" in repair

            # Approve the graph repair
            repair_id = repair["repair_id"]
            response = await authenticated_api_client.post(
                f"/ace/repairs/{repair_id}/approve"
            )
            approve_data = response_validator.assert_success_response(response)

            assert approve_data["status"] == "success"
            mock_curator.approve_repair.assert_called_with(repair_id)
