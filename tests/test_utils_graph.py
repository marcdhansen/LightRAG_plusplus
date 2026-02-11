"""
Comprehensive test suite for lightrag.utils_graph.py - Phase 2 core module targeting

This test suite focuses on graph manipulation functions.
Target: 70% coverage from current 0% baseline.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any


class TestUtilsGraphCoreFunctions:
    """Test core graph manipulation functions - highest impact"""

    @pytest.mark.asyncio
    async def test_adelete_by_entity_basic(self):
        """Test entity deletion functionality"""
        # Mock dependencies
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_entities_vdb.delete.return_value = True

            from lightrag.utils_graph import adelete_by_entity

            result = await adelete_by_entity(
                entity_name="Test Entity", entities_vdb=mock_entities_vdb
            )

            assert result is True
            mock_entities_vdb.delete.assert_called_once_with("Test Entity")
            mock_persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_adelete_by_entity_not_found(self):
        """Test entity deletion when entity not found"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instance - entity not found
            mock_entities_vdb = AsyncMock()
            mock_entities_vdb.delete.return_value = False

            from lightrag.utils_graph import adelete_by_entity

            result = await adelete_by_entity(
                entity_name="NonExistent Entity", entities_vdb=mock_entities_vdb
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_adelete_by_relation_basic(self):
        """Test relationship deletion functionality"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_relationships_vdb = AsyncMock()
            mock_relationships_vdb.delete.return_value = True

            from lightrag.utils_graph import adelete_by_relation

            result = await adelete_by_relation(
                from_entity="Entity1",
                to_entity="Entity2",
                relation_type="related_to",
                relationships_vdb=mock_relationships_vdb,
            )

            assert result is True
            mock_relationships_vdb.delete.assert_called_once()
            mock_persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_aedit_entity_basic(self):
        """Test entity editing functionality"""
        with patch("lightrag.utils_graph._edit_entity_impl") as mock_edit_impl:
            mock_edit_impl.return_value = True

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_entities_vdb.update.return_value = True

            from lightrag.utils_graph import aedit_entity

            result = await aedit_entity(
                entity_name="Test Entity",
                new_data={"description": "Updated description"},
                entities_vdb=mock_entities_vdb,
            )

            assert result is True
            mock_entities_vdb.update.assert_called_once()
            mock_edit_impl.assert_called_once()

    @pytest.mark.asyncio
    async def test_aedit_relation_basic(self):
        """Test relationship editing functionality"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_relationships_vdb = AsyncMock()
            mock_relationships_vdb.update.return_value = True

            from lightrag.utils_graph import aedit_relation

            result = await aedit_relation(
                from_entity="Entity1",
                to_entity="Entity2",
                relation_type="related_to",
                new_data={"weight": 0.9},
                relationships_vdb=mock_relationships_vdb,
            )

            assert result is True
            mock_relationships_vdb.update.assert_called_once()
            mock_persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_acreate_entity_basic(self):
        """Test entity creation functionality"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_entities_vdb.upsert.return_value = True

            from lightrag.utils_graph import acreate_entity

            result = await acreate_entity(
                entity_name="New Entity",
                entity_type="test_type",
                description="Test entity description",
                entities_vdb=mock_entities_vdb,
            )

            assert result is True
            mock_entities_vdb.upsert.assert_called_once()
            mock_persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_acreate_relation_basic(self):
        """Test relationship creation functionality"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_relationships_vdb = AsyncMock()
            mock_relationships_vdb.upsert.return_value = True

            from lightrag.utils_graph import acreate_relation

            result = await acreate_relation(
                from_entity="Entity1",
                to_entity="Entity2",
                relation_type="test_relation",
                weight=0.8,
                relationships_vdb=mock_relationships_vdb,
            )

            assert result is True
            mock_relationships_vdb.upsert.assert_called_once()
            mock_persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_amerge_entities_basic(self):
        """Test entity merging functionality"""
        with patch("lightrag.utils_graph._merge_entities_impl") as mock_merge_impl:
            mock_merge_impl.return_value = True

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_relationships_vdb = AsyncMock()
            mock_entities_vdb.upsert.return_value = True
            mock_relationships_vdb.upsert.return_value = True

            from lightrag.utils_graph import amerge_entities

            result = await amerge_entities(
                target_entity="Target Entity",
                source_entities=["Source Entity 1", "Source Entity 2"],
                entities_vdb=mock_entities_vdb,
                relationships_vdb=mock_relationships_vdb,
            )

            assert result is True
            mock_merge_impl.assert_called_once()
            mock_persist.assert_called_once()


class TestUtilsGraphQueryFunctions:
    """Test graph query and information retrieval functions"""

    @pytest.mark.asyncio
    async def test_get_entity_info_basic(self):
        """Test entity information retrieval"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_entity_data = {
                "name": "Test Entity",
                "type": "test_type",
                "description": "Test description",
                "attributes": {"attr1": "value1"},
            }
            mock_entities_vdb.get.return_value = mock_entity_data

            from lightrag.utils_graph import get_entity_info

            result = get_entity_info(
                entity_name="Test Entity", entities_vdb=mock_entities_vdb
            )

            assert result == mock_entity_data
            mock_entities_vdb.get.assert_called_once_with("Test Entity")

    @pytest.mark.asyncio
    async def test_get_entity_info_not_found(self):
        """Test entity information retrieval when entity not found"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_entities_vdb = AsyncMock()
            mock_entities_vdb.get.return_value = None

            from lightrag.utils_graph import get_entity_info

            result = get_entity_info(
                entity_name="NonExistent Entity", entities_vdb=mock_entities_vdb
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_relation_info_basic(self):
        """Test relationship information retrieval"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_relationships_vdb = AsyncMock()
            mock_relation_data = {
                "from": "Entity1",
                "to": "Entity2",
                "type": "test_relation",
                "weight": 0.8,
                "attributes": {"attr1": "value1"},
            }
            mock_relationships_vdb.get.return_value = mock_relation_data

            from lightrag.utils_graph import get_relation_info

            result = get_relation_info(
                from_entity="Entity1",
                to_entity="Entity2",
                relation_type="test_relation",
                relationships_vdb=mock_relationships_vdb,
            )

            assert result == mock_relation_data
            mock_relationships_vdb.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_relation_info_not_found(self):
        """Test relationship information retrieval when relation not found"""
        with patch("lightrag.utils_graph._persist_graph_updates") as mock_persist:
            mock_persist.return_value = None

            # Mock storage instances
            mock_relationships_vdb = AsyncMock()
            mock_relationships_vdb.get.return_value = None

            from lightrag.utils_graph import get_relation_info

            result = get_relation_info(
                from_entity="Entity1",
                to_entity="Entity2",
                relation_type="NonExistentRelation",
                relationships_vdb=mock_relationships_vdb,
            )

            assert result is None


class TestUtilsGraphUtilityFunctions:
    """Test utility functions in utils_graph.py"""

    def test_merge_attributes_basic(self):
        """Test attribute merging functionality"""
        from lightrag.utils_graph import _merge_attributes

        data_list = [
            {"attr1": "value1", "attr2": "original"},
            {"attr2": "updated", "attr3": "new_value"},
        ]
        merge_strategy = {"attr1": "first", "attr2": "last", "attr3": "first"}

        result = _merge_attributes(data_list, merge_strategy)

        expected = {"attr1": "value1", "attr2": "updated", "attr3": "new_value"}
        assert result == expected

    def test_merge_attributes_empty_base(self):
        """Test attribute merging with empty base attributes"""
        from lightrag.utils_graph import _merge_attributes

        base_attrs = {}
        new_attrs = {"attr1": "value1", "attr2": "value2"}

        result = _merge_attributes(base_attrs, new_attrs)

        assert result == new_attrs

    def test_merge_attributes_empty_new(self):
        """Test attribute merging with empty new attributes"""
        from lightrag.utils_graph import _merge_attributes

        base_attrs = {"attr1": "value1", "attr2": "value2"}
        new_attrs = {}

        result = _merge_attributes(base_attrs, new_attrs)

        assert result == base_attrs

    @pytest.mark.asyncio
    async def test_persist_graph_updates_no_storage(self):
        """Test persist updates with no storage instances"""
        from lightrag.utils_graph import _persist_graph_updates

        # Should not raise error with no storage instances
        result = await _persist_graph_updates()

        assert result is None

    @pytest.mark.asyncio
    async def test_persist_graph_updates_with_storage(self):
        """Test persist updates with storage instances"""
        from lightrag.utils_graph import _persist_graph_updates

        # Mock storage instances
        mock_entities_vdb = AsyncMock()
        mock_entities_vdb.index_done_callback.return_value = True

        result = await _persist_graph_updates(entities_vdb=mock_entities_vdb)

        assert result is None
        mock_entities_vdb.index_done_callback.assert_called_once()


# Mock fixtures
@pytest.fixture
def mock_storage_instances():
    """Create mock storage instances for testing"""
    mock_entities_vdb = AsyncMock()
    mock_relationships_vdb = AsyncMock()
    mock_chunk_storage = AsyncMock()

    mock_entities_vdb.upsert.return_value = True
    mock_entities_vdb.update.return_value = True
    mock_entities_vdb.delete.return_value = True
    mock_entities_vdb.get.return_value = {"name": "Test", "type": "entity"}
    mock_entities_vdb.index_done_callback.return_value = True

    mock_relationships_vdb.upsert.return_value = True
    mock_relationships_vdb.update.return_value = True
    mock_relationships_vdb.delete.return_value = True
    mock_relationships_vdb.get.return_value = {"from": "E1", "to": "E2"}

    mock_chunk_storage.index_done_callback.return_value = True

    return {
        "entities_vdb": mock_entities_vdb,
        "relationships_vdb": mock_relationships_vdb,
        "chunk_storage": mock_chunk_storage,
    }


# Helper functions for testing
def create_mock_entity_data(name="Test Entity", entity_type="test"):
    """Create mock entity data for testing"""
    return {
        "name": name,
        "type": entity_type,
        "description": f"Description for {name}",
        "attributes": {"attr1": "value1", "attr2": "value2"},
    }


def create_mock_relation_data(
    from_entity="E1", to_entity="E2", rel_type="test_relation"
):
    """Create mock relationship data for testing"""
    return {
        "from": from_entity,
        "to": to_entity,
        "type": rel_type,
        "weight": 0.8,
        "attributes": {"attr1": "rel_value1", "attr2": "rel_value2"},
    }


def assert_storage_call(storage_mock, expected_call_count=1):
    """Assert that storage mock was called expected number of times"""
    assert storage_mock.call_count == expected_call_count
    if hasattr(storage_mock, "upsert"):
        assert storage_mock.upsert.call_count == expected_call_count
    if hasattr(storage_mock, "update"):
        assert storage_mock.update.call_count == expected_call_count
    if hasattr(storage_mock, "delete"):
        assert storage_mock.delete.call_count == expected_call_count
