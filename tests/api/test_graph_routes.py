"""
Comprehensive API tests for graph routes.
Tests all graph management endpoints including entity/relationship CRUD operations,
graph visualization, search functionality, and ACE integration.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from lightrag.base import DocStatus
from tests.api.conftest import (
    APIResponseValidator,
    MockLightRAG,
)


class MockGraphResponse:
    """Mock graph response data for testing."""

    @staticmethod
    def graph_labels():
        return ["PERSON", "ORGANIZATION", "LOCATION", "CONCEPT"]

    @staticmethod
    def popular_labels():
        return ["PERSON", "ORGANIZATION", "LOCATION"]

    @staticmethod
    def search_results():
        return ["Tesla", "Elon Musk", "Electric Vehicle"]

    @staticmethod
    def knowledge_graph():
        return {
            "nodes": [
                {"id": "Elon Musk", "label": "PERSON", "type": "entity"},
                {"id": "Tesla", "label": "ORGANIZATION", "type": "entity"},
            ],
            "edges": [
                {
                    "source": "Elon Musk",
                    "target": "Tesla",
                    "relationship": "CEO_OF",
                    "weight": 1.0,
                }
            ],
        }

    @staticmethod
    def entity_exists_true():
        return {"exists": True}

    @staticmethod
    def entity_exists_false():
        return {"exists": False}

    @staticmethod
    def entity_data():
        return {
            "entity_name": "Tesla",
            "description": "Electric vehicle manufacturer",
            "entity_type": "ORGANIZATION",
            "source_id": "chunk-123<SEP>chunk-456",
        }

    @staticmethod
    def relation_data():
        return {
            "src_id": "Elon Musk",
            "tgt_id": "Tesla",
            "description": "Elon Musk is CEO of Tesla",
            "keywords": "CEO, founder",
            "weight": 1.0,
        }

    @staticmethod
    def merge_result():
        return {
            "merged_entity": "Elon Musk",
            "deleted_entities": ["Elon Msk", "Ellon Musk"],
            "relationships_transferred": 15,
        }


@pytest.mark.asyncio
@pytest.mark.api
class TestGraphLabels:
    """Test graph label endpoints."""

    async def test_get_graph_labels_success(
        self, authenticated_api_client, response_validator
    ):
        """Test getting all graph labels."""
        with patch.object(MockLightRAG, "get_graph_labels") as mock_get_labels:
            mock_get_labels.return_value = MockGraphResponse.graph_labels()

            response = await authenticated_api_client.get("/graph/label/list")
            data = response_validator.assert_success_response(response)

            assert isinstance(data, list)
            assert len(data) == 4
            assert "PERSON" in data
            assert "ORGANIZATION" in data

    async def test_get_popular_labels_success(
        self, authenticated_api_client, response_validator
    ):
        """Test getting popular labels with limit."""
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.get_popular_labels.return_value = (
                MockGraphResponse.popular_labels()
            )

            response = await authenticated_api_client.get(
                "/graph/label/popular?limit=50"
            )
            data = response_validator.assert_success_response(response)

            assert isinstance(data, list)
            assert len(data) == 3
            assert "PERSON" in data
            assert "ORGANIZATION" in data

    async def test_get_popular_labels_default_limit(
        self, authenticated_api_client, response_validator
    ):
        """Test getting popular labels with default limit."""
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.get_popular_labels.return_value = (
                MockGraphResponse.popular_labels()
            )

            response = await authenticated_api_client.get("/graph/label/popular")
            data = response_validator.assert_success_response(response)

            assert isinstance(data, list)
            mock_graph.get_popular_labels.assert_called_with(300)  # Default limit

    async def test_get_popular_labels_invalid_limit(
        self, authenticated_api_client, response_validator
    ):
        """Test getting popular labels with invalid limit."""
        response = await authenticated_api_client.get("/graph/label/popular?limit=0")
        response_validator.assert_error_response(response, 422)

        response = await authenticated_api_client.get("/graph/label/popular?limit=1001")
        response_validator.assert_error_response(response, 422)

    async def test_search_labels_success(
        self, authenticated_api_client, response_validator
    ):
        """Test searching labels with query."""
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.search_labels.return_value = MockGraphResponse.search_results()

            response = await authenticated_api_client.get(
                "/graph/label/search?q=Tesla&limit=20"
            )
            data = response_validator.assert_success_response(response)

            assert isinstance(data, list)
            assert len(data) == 3
            assert "Tesla" in data
            mock_graph.search_labels.assert_called_with("Tesla", 20)

    async def test_search_labels_missing_query(
        self, authenticated_api_client, response_validator
    ):
        """Test searching labels without required query parameter."""
        response = await authenticated_api_client.get("/graph/label/search")
        response_validator.assert_error_response(response, 422)

    async def test_search_labels_invalid_limit(
        self, authenticated_api_client, response_validator
    ):
        """Test searching labels with invalid limit."""
        response = await authenticated_api_client.get(
            "/graph/label/search?q=test&limit=0"
        )
        response_validator.assert_error_response(response, 422)

        response = await authenticated_api_client.get(
            "/graph/label/search?q=test&limit=101"
        )
        response_validator.assert_error_response(response, 422)


@pytest.mark.asyncio
@pytest.mark.api
class TestKnowledgeGraph:
    """Test knowledge graph retrieval endpoints."""

    async def test_get_knowledge_graph_success(
        self, authenticated_api_client, response_validator
    ):
        """Test getting knowledge graph for a label."""
        with patch.object(MockLightRAG, "get_knowledge_graph") as mock_get_graph:
            mock_get_graph.return_value = MockGraphResponse.knowledge_graph()

            response = await authenticated_api_client.get(
                "/graphs?label=Tesla&max_depth=2&max_nodes=500"
            )
            data = response_validator.assert_success_response(response)

            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == 2
            assert len(data["edges"]) == 1
            mock_get_graph.assert_called_with(
                node_label="Tesla", max_depth=2, max_nodes=500
            )

    async def test_get_knowledge_graph_default_params(
        self, authenticated_api_client, response_validator
    ):
        """Test getting knowledge graph with default parameters."""
        with patch.object(MockLightRAG, "get_knowledge_graph") as mock_get_graph:
            mock_get_graph.return_value = MockGraphResponse.knowledge_graph()

            response = await authenticated_api_client.get("/graphs?label=Tesla")
            data = response_validator.assert_success_response(response)

            mock_get_graph.assert_called_with(
                node_label="Tesla", max_depth=3, max_nodes=1000
            )

    async def test_get_knowledge_graph_missing_label(
        self, authenticated_api_client, response_validator
    ):
        """Test getting knowledge graph without required label."""
        response = await authenticated_api_client.get("/graphs")
        response_validator.assert_error_response(response, 422)

    async def test_get_knowledge_graph_invalid_depth(
        self, authenticated_api_client, response_validator
    ):
        """Test getting knowledge graph with invalid depth."""
        response = await authenticated_api_client.get("/graphs?label=Tesla&max_depth=0")
        response_validator.assert_error_response(response, 422)

    async def test_get_knowledge_graph_invalid_nodes(
        self, authenticated_api_client, response_validator
    ):
        """Test getting knowledge graph with invalid max_nodes."""
        response = await authenticated_api_client.get("/graphs?label=Tesla&max_nodes=0")
        response_validator.assert_error_response(response, 422)


@pytest.mark.asyncio
@pytest.mark.api
class TestEntityOperations:
    """Test entity CRUD operations."""

    async def test_check_entity_exists_true(
        self, authenticated_api_client, response_validator
    ):
        """Test checking existing entity."""
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.has_node.return_value = True

            response = await authenticated_api_client.get(
                "/graph/entity/exists?name=Tesla"
            )
            data = response_validator.assert_success_response(response)

            assert data["exists"] is True
            mock_graph.has_node.assert_called_with("Tesla")

    async def test_check_entity_exists_false(
        self, authenticated_api_client, response_validator
    ):
        """Test checking non-existent entity."""
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.has_node.return_value = False

            response = await authenticated_api_client.get(
                "/graph/entity/exists?name=NonExistent"
            )
            data = response_validator.assert_success_response(response)

            assert data["exists"] is False
            mock_graph.has_node.assert_called_with("NonExistent")

    async def test_check_entity_exists_missing_name(
        self, authenticated_api_client, response_validator
    ):
        """Test checking entity existence without name parameter."""
        response = await authenticated_api_client.get("/graph/entity/exists")
        response_validator.assert_error_response(response, 422)

    async def test_create_entity_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful entity creation."""
        entity_request = {
            "entity_name": "Tesla",
            "entity_data": {
                "description": "Electric vehicle manufacturer",
                "entity_type": "ORGANIZATION",
            },
        }

        with patch.object(MockLightRAG, "acreate_entity") as mock_create:
            mock_create.return_value = MockGraphResponse.entity_data()

            response = await authenticated_api_client.post(
                "/graph/entity/create", json=entity_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "Tesla" in data["message"]
            assert "data" in data
            assert data["data"]["entity_name"] == "Tesla"
            assert data["data"]["entity_type"] == "ORGANIZATION"
            mock_create.assert_called_once_with(
                entity_name="Tesla",
                entity_data={
                    "description": "Electric vehicle manufacturer",
                    "entity_type": "ORGANIZATION",
                },
            )

    async def test_create_entity_missing_name(
        self, authenticated_api_client, response_validator
    ):
        """Test entity creation with missing name."""
        invalid_request = {
            "entity_data": {"description": "Test entity"},
        }

        response = await authenticated_api_client.post(
            "/graph/entity/create", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_create_entity_missing_data(
        self, authenticated_api_client, response_validator
    ):
        """Test entity creation with missing data."""
        invalid_request = {"entity_name": "Test"}

        response = await authenticated_api_client.post(
            "/graph/entity/create", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_create_entity_duplicate(
        self, authenticated_api_client, response_validator
    ):
        """Test entity creation with duplicate name."""
        entity_request = {
            "entity_name": "Tesla",  # Assume this already exists
            "entity_data": {"description": "Duplicate entity"},
        }

        with patch.object(MockLightRAG, "acreate_entity") as mock_create:
            mock_create.side_effect = ValueError("Entity already exists")

            response = await authenticated_api_client.post(
                "/graph/entity/create", json=entity_request
            )
            response_validator.assert_error_response(response, 400)

    async def test_update_entity_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful entity update."""
        update_request = {
            "entity_name": "Tesla",
            "updated_data": {"description": "Updated description"},
            "allow_rename": False,
            "allow_merge": False,
        }

        mock_result = MockGraphResponse.entity_data()
        mock_result["description"] = "Updated description"
        mock_result["operation_summary"] = {
            "merged": False,
            "merge_status": "not_attempted",
            "merge_error": None,
            "operation_status": "success",
            "target_entity": None,
            "final_entity": "Tesla",
            "renamed": False,
        }

        with patch.object(MockLightRAG, "aedit_entity") as mock_edit:
            mock_edit.return_value = mock_result

            response = await authenticated_api_client.post(
                "/graph/entity/edit", json=update_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert data["message"] == "Entity updated successfully"
            assert "data" in data
            assert "operation_summary" in data
            assert data["operation_summary"]["operation_status"] == "success"

    async def test_update_entity_with_rename(
        self, authenticated_api_client, response_validator
    ):
        """Test entity update with rename."""
        update_request = {
            "entity_name": "Tesla",
            "updated_data": {"entity_name": "Tesla Inc.", "description": "Updated"},
            "allow_rename": True,
            "allow_merge": False,
        }

        mock_result = MockGraphResponse.entity_data()
        mock_result["entity_name"] = "Tesla Inc."
        mock_result["operation_summary"] = {
            "merged": False,
            "merge_status": "not_attempted",
            "merge_error": None,
            "operation_status": "success",
            "target_entity": None,
            "final_entity": "Tesla Inc.",
            "renamed": True,
        }

        with patch.object(MockLightRAG, "aedit_entity") as mock_edit:
            mock_edit.return_value = mock_result

            response = await authenticated_api_client.post(
                "/graph/entity/edit", json=update_request
            )
            data = response_validator.assert_success_response(response)

            assert data["operation_summary"]["renamed"] is True
            assert data["operation_summary"]["final_entity"] == "Tesla Inc."

    async def test_update_entity_missing_name(
        self, authenticated_api_client, response_validator
    ):
        """Test entity update with missing entity name."""
        invalid_request = {
            "updated_data": {"description": "Updated"},
            "allow_rename": False,
            "allow_merge": False,
        }

        response = await authenticated_api_client.post(
            "/graph/entity/edit", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_update_entity_missing_data(
        self, authenticated_api_client, response_validator
    ):
        """Test entity update with missing updated data."""
        invalid_request = {
            "entity_name": "Tesla",
            "allow_rename": False,
            "allow_merge": False,
        }

        response = await authenticated_api_client.post(
            "/graph/entity/edit", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_merge_entities_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful entity merge."""
        merge_request = {
            "entities_to_change": ["Elon Msk", "Ellon Musk"],
            "entity_to_change_into": "Elon Musk",
        }

        with patch.object(MockLightRAG, "amerge_entities") as mock_merge:
            mock_merge.return_value = MockGraphResponse.merge_result()

            response = await authenticated_api_client.post(
                "/graph/entities/merge", json=merge_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "merged 2 entities" in data["message"]
            assert "Elon Musk" in data["message"]
            assert data["data"]["merged_entity"] == "Elon Musk"
            assert len(data["data"]["deleted_entities"]) == 2
            mock_merge.assert_called_once_with(
                source_entities=["Elon Msk", "Ellon Musk"],
                target_entity="Elon Musk",
            )

    async def test_merge_entities_empty_list(
        self, authenticated_api_client, response_validator
    ):
        """Test entity merge with empty entity list."""
        invalid_request = {
            "entities_to_change": [],
            "entity_to_change_into": "Target",
        }

        response = await authenticated_api_client.post(
            "/graph/entities/merge", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_merge_entities_missing_target(
        self, authenticated_api_client, response_validator
    ):
        """Test entity merge with missing target entity."""
        invalid_request = {"entities_to_change": ["Source1", "Source2"]}

        response = await authenticated_api_client.post(
            "/graph/entities/merge", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)


@pytest.mark.asyncio
@pytest.mark.api
class TestRelationOperations:
    """Test relationship CRUD operations."""

    async def test_create_relation_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful relationship creation."""
        relation_request = {
            "source_entity": "Elon Musk",
            "target_entity": "Tesla",
            "relation_data": {
                "description": "Elon Musk is CEO of Tesla",
                "keywords": "CEO, founder",
                "weight": 1.0,
            },
        }

        with patch.object(MockLightRAG, "acreate_relation") as mock_create:
            mock_create.return_value = MockGraphResponse.relation_data()

            response = await authenticated_api_client.post(
                "/graph/relation/create", json=relation_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "Elon Musk" in data["message"]
            assert "Tesla" in data["message"]
            assert data["data"]["src_id"] == "Elon Musk"
            assert data["data"]["tgt_id"] == "Tesla"
            mock_create.assert_called_once_with(
                source_entity="Elon Musk",
                target_entity="Tesla",
                relation_data={
                    "description": "Elon Musk is CEO of Tesla",
                    "keywords": "CEO, founder",
                    "weight": 1.0,
                },
            )

    async def test_create_relation_missing_source(
        self, authenticated_api_client, response_validator
    ):
        """Test relationship creation with missing source entity."""
        invalid_request = {
            "target_entity": "Tesla",
            "relation_data": {"description": "Test relation"},
        }

        response = await authenticated_api_client.post(
            "/graph/relation/create", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_create_relation_missing_target(
        self, authenticated_api_client, response_validator
    ):
        """Test relationship creation with missing target entity."""
        invalid_request = {
            "source_entity": "Elon Musk",
            "relation_data": {"description": "Test relation"},
        }

        response = await authenticated_api_client.post(
            "/graph/relation/create", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_create_relation_missing_data(
        self, authenticated_api_client, response_validator
    ):
        """Test relationship creation with missing relation data."""
        invalid_request = {
            "source_entity": "Elon Musk",
            "target_entity": "Tesla",
        }

        response = await authenticated_api_client.post(
            "/graph/relation/create", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_update_relation_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful relationship update."""
        update_request = {
            "source_id": "Elon Musk",
            "target_id": "Tesla",
            "updated_data": {"description": "Updated CEO relationship", "weight": 1.2},
        }

        with patch.object(MockLightRAG, "aedit_relation") as mock_edit:
            mock_edit.return_value = MockGraphResponse.relation_data()

            response = await authenticated_api_client.post(
                "/graph/relation/edit", json=update_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert data["message"] == "Relation updated successfully"
            assert "data" in data
            mock_edit.assert_called_once_with(
                source_entity="Elon Musk",
                target_entity="Tesla",
                updated_data={"description": "Updated CEO relationship", "weight": 1.2},
            )

    async def test_update_relation_missing_source_id(
        self, authenticated_api_client, response_validator
    ):
        """Test relationship update with missing source ID."""
        invalid_request = {
            "target_id": "Tesla",
            "updated_data": {"description": "Updated"},
        }

        response = await authenticated_api_client.post(
            "/graph/relation/edit", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_update_relation_missing_target_id(
        self, authenticated_api_client, response_validator
    ):
        """Test relationship update with missing target ID."""
        invalid_request = {
            "source_id": "Elon Musk",
            "updated_data": {"description": "Updated"},
        }

        response = await authenticated_api_client.post(
            "/graph/relation/edit", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.error_handling
class TestGraphRoutesErrorHandling:
    """Test error handling for graph routes."""

    async def test_graph_routes_unauthorized_access(
        self, api_client, response_validator
    ):
        """Test that unauthenticated requests are rejected."""
        endpoints = [
            "/graph/label/list",
            "/graph/label/popular",
            "/graph/label/search?q=test",
            "/graphs?label=test",
            "/graph/entity/exists?name=test",
        ]

        for endpoint in endpoints:
            response = await api_client.get(endpoint)
            response_validator.assert_error_response(response, 401)

        # Test POST endpoints
        post_endpoints = [
            ("/graph/entity/create", {"entity_name": "test", "entity_data": {}}),
            ("/graph/entity/edit", {"entity_name": "test", "updated_data": {}}),
            (
                "/graph/relation/create",
                {"source_entity": "a", "target_entity": "b", "relation_data": {}},
            ),
            (
                "/graph/relation/edit",
                {"source_id": "a", "target_id": "b", "updated_data": {}},
            ),
            (
                "/graph/entities/merge",
                {"entities_to_change": ["a"], "entity_to_change_into": "b"},
            ),
        ]

        for endpoint, payload in post_endpoints:
            response = await api_client.post(endpoint, json=payload)
            response_validator.assert_error_response(response, 401)

    async def test_graph_routes_invalid_json(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of malformed JSON requests."""
        response = await authenticated_api_client.post(
            "/graph/entity/create",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        response_validator.assert_error_response(response, 422)

    async def test_entity_not_found_error(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of non-existent entity operations."""
        with patch.object(MockLightRAG, "aedit_entity") as mock_edit:
            mock_edit.side_effect = ValueError("Entity not found")

            update_request = {
                "entity_name": "NonExistent",
                "updated_data": {"description": "Updated"},
                "allow_rename": False,
                "allow_merge": False,
            }

            response = await authenticated_api_client.post(
                "/graph/entity/edit", json=update_request
            )
            response_validator.assert_error_response(response, 400)

    async def test_relation_not_found_error(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of non-existent relationship operations."""
        with patch.object(MockLightRAG, "aedit_relation") as mock_edit:
            mock_edit.side_effect = ValueError("Relation not found")

            update_request = {
                "source_id": "NonExistent1",
                "target_id": "NonExistent2",
                "updated_data": {"description": "Updated"},
            }

            response = await authenticated_api_client.post(
                "/graph/relation/edit", json=update_request
            )
            response_validator.assert_error_response(response, 400)

    async def test_merge_target_not_found_error(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of merge target not found."""
        with patch.object(MockLightRAG, "amerge_entities") as mock_merge:
            mock_merge.side_effect = ValueError("Target entity not found")

            merge_request = {
                "entities_to_change": ["Source1", "Source2"],
                "entity_to_change_into": "NonExistentTarget",
            }

            response = await authenticated_api_client.post(
                "/graph/entities/merge", json=merge_request
            )
            response_validator.assert_error_response(response, 400)

    async def test_internal_server_error_handling(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of internal server errors."""
        with patch.object(MockLightRAG, "get_graph_labels") as mock_get_labels:
            mock_get_labels.side_effect = Exception("Database connection failed")

            response = await authenticated_api_client.get("/graph/label/list")
            response_validator.assert_error_response(response, 500)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
class TestGraphRoutesIntegration:
    """Integration tests for graph routes."""

    async def test_entity_lifecycle_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complete entity lifecycle: create -> update -> merge."""
        # 1. Create entity
        create_request = {
            "entity_name": "TestEntity",
            "entity_data": {
                "description": "Test entity description",
                "entity_type": "CONCEPT",
            },
        }

        with patch.object(MockLightRAG, "acreate_entity") as mock_create:
            mock_create.return_value = MockGraphResponse.entity_data()
            mock_create.return_value["entity_name"] = "TestEntity"

            response = await authenticated_api_client.post(
                "/graph/entity/create", json=create_request
            )
            create_data = response_validator.assert_success_response(response)
            assert create_data["status"] == "success"

        # 2. Update entity
        update_request = {
            "entity_name": "TestEntity",
            "updated_data": {"description": "Updated description"},
            "allow_rename": False,
            "allow_merge": False,
        }

        with patch.object(MockLightRAG, "aedit_entity") as mock_edit:
            mock_result = MockGraphResponse.entity_data()
            mock_result["description"] = "Updated description"
            mock_result["operation_summary"] = {
                "merged": False,
                "merge_status": "not_attempted",
                "merge_error": None,
                "operation_status": "success",
                "target_entity": None,
                "final_entity": "TestEntity",
                "renamed": False,
            }
            mock_edit.return_value = mock_result

            response = await authenticated_api_client.post(
                "/graph/entity/edit", json=update_request
            )
            update_data = response_validator.assert_success_response(response)
            assert update_data["status"] == "success"

        # 3. Check entity exists
        with patch.object(MockLightRAG, "chunk_entity_relation_graph") as mock_graph:
            mock_graph.has_node.return_value = True

            response = await authenticated_api_client.get(
                "/graph/entity/exists?name=TestEntity"
            )
            exists_data = response_validator.assert_success_response(response)
            assert exists_data["exists"] is True

    async def test_relationship_lifecycle_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complete relationship lifecycle: create -> update."""
        # 1. Create relationship
        relation_request = {
            "source_entity": "EntityA",
            "target_entity": "EntityB",
            "relation_data": {
                "description": "Test relationship",
                "keywords": "test",
                "weight": 1.0,
            },
        }

        with patch.object(MockLightRAG, "acreate_relation") as mock_create:
            mock_create.return_value = MockGraphResponse.relation_data()
            mock_create.return_value["src_id"] = "EntityA"
            mock_create.return_value["tgt_id"] = "EntityB"

            response = await authenticated_api_client.post(
                "/graph/relation/create", json=relation_request
            )
            create_data = response_validator.assert_success_response(response)
            assert create_data["status"] == "success"

        # 2. Update relationship
        update_request = {
            "source_id": "EntityA",
            "target_id": "EntityB",
            "updated_data": {"description": "Updated relationship", "weight": 1.5},
        }

        with patch.object(MockLightRAG, "aedit_relation") as mock_edit:
            mock_edit.return_value = MockGraphResponse.relation_data()
            mock_edit.return_value["description"] = "Updated relationship"
            mock_edit.return_value["weight"] = 1.5

            response = await authenticated_api_client.post(
                "/graph/relation/edit", json=update_request
            )
            update_data = response_validator.assert_success_response(response)
            assert update_data["status"] == "success"

    async def test_complex_entity_merge_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complex entity merge with multiple duplicates."""
        merge_request = {
            "entities_to_change": ["Variant1", "Variant2", "Variant3"],
            "entity_to_change_into": "CanonicalEntity",
        }

        with patch.object(MockLightRAG, "amerge_entities") as mock_merge:
            mock_result = {
                "merged_entity": "CanonicalEntity",
                "deleted_entities": ["Variant1", "Variant2", "Variant3"],
                "relationships_transferred": 25,
                "merge_details": {
                    "conflicts_resolved": 3,
                    "relationships_deduplicated": 5,
                },
            }
            mock_merge.return_value = mock_result

            response = await authenticated_api_client.post(
                "/graph/entities/merge", json=merge_request
            )
            data = response_validator.assert_success_response(response)

            assert data["status"] == "success"
            assert "merged 3 entities" in data["message"]
            assert data["data"]["merged_entity"] == "CanonicalEntity"
            assert len(data["data"]["deleted_entities"]) == 3
            assert data["data"]["relationships_transferred"] == 25
            mock_merge.assert_called_once_with(
                source_entities=["Variant1", "Variant2", "Variant3"],
                target_entity="CanonicalEntity",
            )
