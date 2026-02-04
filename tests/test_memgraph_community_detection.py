"""Tests for community detection functionality in MemgraphStorage."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lightrag.kg.memgraph_impl import MemgraphStorage


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "embedding_batch_num": 32,
        "vector_db_storage_cls_kwargs": {"cosine_better_than_threshold": 0.2},
    }


@pytest.fixture
def mock_embedding_func():
    """Mock embedding function."""
    mock_func = MagicMock()
    mock_func.embedding_dim = 768
    return mock_func


@pytest.fixture
def memgraph_storage(mock_config, mock_embedding_func):
    """Create MemgraphStorage instance for testing."""
    with patch.dict(
        os.environ,
        {
            "MEMGRAPH_URI": "bolt://localhost:7687",
            "MEMGRAPH_USERNAME": "",
            "MEMGRAPH_PASSWORD": "",
            "MEMGRAPH_DATABASE": "memgraph",
        },
    ):
        storage = MemgraphStorage(
            namespace="test_namespace",
            global_config=mock_config,
            embedding_func=mock_embedding_func,
            workspace="test_workspace",
        )

        # Mock the driver
        storage._driver = MagicMock()
        storage._DATABASE = "memgraph"

        return storage


@pytest.fixture
def mock_session():
    """Mock Neo4j session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_driver(mock_session):
    """Mock Neo4j driver."""
    driver = MagicMock()
    driver.session.return_value.__aenter__.return_value = mock_session
    driver.session.return_value.__aexit__.return_value = None
    return driver


class TestCommunityDetection:
    """Test suite for community detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_communities_louvain(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test Louvain community detection."""
        memgraph_storage._driver = mock_driver

        # Mock successful community detection results
        mock_records = [
            {"node_id": "node1", "community_id": 0},
            {"node_id": "node2", "community_id": 0},
            {"node_id": "node3", "community_id": 1},
            {"node_id": "node4", "community_id": 1},
            {"node_id": "node5", "community_id": 2},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test community detection
        communities = await memgraph_storage.detect_communities(algorithm="louvain")

        # Verify results
        expected_communities = {
            "node1": 0,
            "node2": 0,
            "node3": 1,
            "node4": 1,
            "node5": 2,
        }
        assert communities == expected_communities

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args[0][0]
        assert "louvain.projection" in call_args
        assert "test_workspace" in call_args

    @pytest.mark.asyncio
    async def test_detect_communities_leiden(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test Leiden community detection."""
        memgraph_storage._driver = mock_driver

        # Mock successful community detection results
        mock_records = [
            {"node_id": "node1", "community_id": 0},
            {"node_id": "node2", "community_id": 0},
            {"node_id": "node3", "community_id": 1},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test community detection
        communities = await memgraph_storage.detect_communities(algorithm="leiden")

        # Verify results
        expected_communities = {"node1": 0, "node2": 0, "node3": 1}
        assert communities == expected_communities

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args[0][0]
        assert "leiden.projection" in call_args

    @pytest.mark.asyncio
    async def test_detect_communities_invalid_algorithm(
        self, memgraph_storage, mock_driver
    ):
        """Test community detection with invalid algorithm."""
        memgraph_storage._driver = mock_driver

        # Test with invalid algorithm
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            await memgraph_storage.detect_communities(algorithm="invalid")

    @pytest.mark.asyncio
    async def test_detect_communities_uninitialized_driver(self, memgraph_storage):
        """Test community detection without initialized driver."""
        memgraph_storage._driver = None

        with pytest.raises(RuntimeError, match="Memgraph driver is not initialized"):
            await memgraph_storage.detect_communities()

    @pytest.mark.asyncio
    async def test_assign_community_ids(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test assigning community IDs to nodes."""
        memgraph_storage._driver = mock_driver

        # Mock successful assignment
        mock_record = {"updated_count": 5}
        mock_result = AsyncMock()
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result

        communities = {"node1": 0, "node2": 0, "node3": 1, "node4": 1, "node5": 2}

        # Test community assignment
        updated_count = await memgraph_storage.assign_community_ids(
            communities, algorithm="louvain"
        )

        # Verify results
        assert updated_count == 5

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "UNWIND $updates AS update" in query
        assert "louvain_community" in query
        assert call_args[1]["updates"] == [
            {"node_id": "node1", "community_id": 0},
            {"node_id": "node2", "community_id": 0},
            {"node_id": "node3", "community_id": 1},
            {"node_id": "node4", "community_id": 1},
            {"node_id": "node5", "community_id": 2},
        ]

    @pytest.mark.asyncio
    async def test_assign_community_ids_empty(self, memgraph_storage, mock_driver):
        """Test assigning community IDs with empty dictionary."""
        memgraph_storage._driver = mock_driver

        # Test with empty communities
        updated_count = await memgraph_storage.assign_community_ids({})
        assert updated_count == 0

        # Verify no query was executed
        mock_driver.session.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_node_communities(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test retrieving community IDs for specific nodes."""
        memgraph_storage._driver = mock_driver

        # Mock community retrieval results
        mock_records = [
            {"node_id": "node1", "community_id": 0},
            {"node_id": "node3", "community_id": 1},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test community retrieval
        communities = await memgraph_storage.get_node_communities(
            ["node1", "node2", "node3"], algorithm="louvain"
        )

        # Verify results
        expected_communities = {"node1": 0, "node3": 1}
        assert communities == expected_communities

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "louvain_community" in query
        assert "n.id IN $node_ids" in query
        assert call_args[1]["node_ids"] == ["node1", "node2", "node3"]

    @pytest.mark.asyncio
    async def test_get_node_communities_empty_list(self, memgraph_storage, mock_driver):
        """Test retrieving community IDs with empty node list."""
        memgraph_storage._driver = mock_driver

        # Test with empty node list
        communities = await memgraph_storage.get_node_communities([])
        assert communities == {}

        # Verify no query was executed
        mock_driver.session.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_labels_with_community_filter(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test label search with community filtering."""
        memgraph_storage._driver = mock_driver

        # Mock search results
        mock_records = [
            {"label": "entity1"},
            {"label": "entity2"},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test community-filtered search
        labels = await memgraph_storage.search_labels_with_community_filter(
            query="test", limit=10, community_ids=[0, 1], algorithm="louvain"
        )

        # Verify results
        expected_labels = ["entity1", "entity2"]
        assert labels == expected_labels

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "louvain_community" in query
        assert "IN $community_ids" in query
        assert call_args[1]["query_lower"] == "test"
        assert call_args[1]["community_ids"] == [0, 1]

    @pytest.mark.asyncio
    async def test_search_labels_without_community_filter(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test label search without community filtering."""
        memgraph_storage._driver = mock_driver

        # Mock search results
        mock_records = [
            {"label": "entity1"},
            {"label": "entity2"},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test search without community filtering
        labels = await memgraph_storage.search_labels_with_community_filter(
            query="test", limit=10
        )

        # Verify results
        expected_labels = ["entity1", "entity2"]
        assert labels == expected_labels

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "louvain_community" not in query  # Should not contain community filter
        assert call_args[1]["query_lower"] == "test"
        assert (
            "community_ids" not in call_args[1]
        )  # Should not have community_ids parameter

    @pytest.mark.asyncio
    async def test_search_labels_empty_query(self, memgraph_storage, mock_driver):
        """Test label search with empty query."""
        memgraph_storage._driver = mock_driver

        # Test with empty query
        labels = await memgraph_storage.search_labels_with_community_filter(query="   ")
        assert labels == []

        # Verify no query was executed
        mock_driver.session.assert_not_called()

    @pytest.mark.asyncio
    async def test_community_detection_error_handling(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test error handling in community detection."""
        memgraph_storage._driver = mock_driver

        # Mock database error
        mock_session.run.side_effect = Exception("Database error")

        # Test error handling
        with pytest.raises(Exception, match="Database error"):
            await memgraph_storage.detect_communities()

    @pytest.mark.asyncio
    async def test_filter_by_community_integration(
        self, memgraph_storage, mock_driver, mock_session
    ):
        """Test the filter_by_community method."""
        memgraph_storage._driver = mock_driver

        # Mock search results
        mock_records = [
            {"labels": "entity1"},
            {"labels": "entity2"},
        ]

        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter(mock_records)
        mock_session.run.return_value = mock_result

        # Test community filtering
        labels = await memgraph_storage.filter_by_community(
            query="test", community_ids=[0, 1], algorithm="louvain", top_k=5
        )

        # Verify results
        expected_labels = ["entity1", "entity2"]
        assert labels == expected_labels

        # Verify the correct query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "louvain_community" in query
        assert "IN $community_ids" in query


if __name__ == "__main__":
    pytest.main([__file__])
