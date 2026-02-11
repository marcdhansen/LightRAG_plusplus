#!/usr/bin/env python3
"""
Test suite for prepare_qdrant_legacy_data.py tool.

This test ensures that Qdrant legacy data preparation tool works correctly
for copying data between new and legacy collections for testing migration logic.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch, call
from dataclasses import dataclass
from typing import Any


class TestQdrantLegacyDataPreparation:
    """Test cases for Qdrant legacy data preparation tool."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create a comprehensive mock Qdrant client."""
        with patch(
            "lightrag.tools.prepare_qdrant_legacy_data.QdrantClient"
        ) as mock_client_cls:
            client = mock_client_cls.return_value

            # Mock collection exists
            client.collection_exists.return_value = True

            # Mock collection info
            collection_info = MagicMock()
            collection_info.config.params.vectors.size = 768
            collection_info.config.params.vectors.distance = "Cosine"
            client.get_collection.return_value = collection_info

            # Mock count operations
            client.count.return_value = MagicMock(count=1000)

            # Mock scroll operations
            scroll_records = [
                {
                    "id": f"point_{i}",
                    "vector": [0.1] * 768,
                    "payload": {
                        "content": f"Test content {i}",
                        "workspace_id": "test_workspace",
                        "metadata": {"type": "test"},
                    },
                }
                for i in range(10)
            ]
            client.scroll.side_effect = [
                (scroll_records, None),  # First call returns data
                ([], None),  # Second call returns empty (end)
            ]

            # Mock upsert operations
            client.upsert.return_value = None

            # Mock create/delete operations
            client.create_collection.return_value = None
            client.delete_collection.return_value = None

            # Mock get_collections for connection check
            client.get_collections.return_value = MagicMock(collections=[])

            yield client

    @pytest.fixture
    def mock_copy_stats(self):
        """Create a CopyStats instance for testing."""
        from lightrag.tools.prepare_qdrant_legacy_data import CopyStats

        return CopyStats(
            collection_type="chunks",
            source_collection="lightrag_vdb_chunks",
            target_collection="test_workspace_chunks",
            total_records=1000,
            copied_records=10,
            failed_records=0,
            elapsed_time=5.0,
            errors=[],
        )

    def test_import(self):
        """Test that prepare_qdrant_legacy_data can be imported."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
            CopyStats,
            COLLECTION_NAMESPACES,
            DEFAULT_BATCH_SIZE,
        )

        assert callable(QdrantLegacyDataPreparationTool)
        assert hasattr(CopyStats, "__dataclass_fields__")
        assert isinstance(COLLECTION_NAMESPACES, dict)
        assert isinstance(DEFAULT_BATCH_SIZE, int)

    def test_tool_initialization_with_defaults(self):
        """Test tool initialization with default parameters."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        assert tool.workspace == "space1"  # Default workspace
        assert tool.batch_size == 500  # Default batch size
        assert tool.dry_run is False  # Default dry run
        assert tool.clear_target is False  # Default clear target

    def test_tool_initialization_with_custom_params(self):
        """Test tool initialization with custom parameters."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool(
            workspace="custom_workspace",
            batch_size=200,
            dry_run=True,
            clear_target=True,
        )

        assert tool.workspace == "custom_workspace"
        assert tool.batch_size == 200
        assert tool.dry_run is True
        assert tool.clear_target is True

    def test_check_connection_success(self, mock_qdrant_client):
        """Test successful connection check."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test successful connection
        result = tool.check_connection()

        assert result is True
        mock_qdrant_client.get_collections.assert_called_once()  # Check connection lists collections

    def test_check_connection_failure(self, mock_qdrant_client):
        """Test connection check failure."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock connection failure
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")

        tool = QdrantLegacyDataPreparationTool()

        # Test failed connection
        result = tool.check_connection()

        assert result is False

    def test_get_collection_info_success(self, mock_qdrant_client):
        """Test getting collection info successfully."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test getting collection info
        info = tool.get_collection_info("lightrag_vdb_chunks")

        assert info is not None
        assert info["vector_size"] == 768
        assert info["distance"] == "Cosine"
        assert info["count"] == 1000
        mock_qdrant_client.get_collection.assert_called_with("lightrag_vdb_chunks")

    def test_get_collection_info_failure(self, mock_qdrant_client):
        """Test getting collection info when collection doesn't exist."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock collection not found
        mock_qdrant_client.get_collection.side_effect = Exception(
            "Collection not found"
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test getting collection info
        info = tool.get_collection_info("nonexistent_collection")

        assert info is None

    def test_delete_collection_success(self, mock_qdrant_client):
        """Test successful collection deletion."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test deleting collection
        result = tool.delete_collection("test_collection")

        assert result is True
        mock_qdrant_client.delete_collection.assert_called_with("test_collection")

    def test_delete_collection_failure(self, mock_qdrant_client):
        """Test collection deletion failure."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock deletion failure
        mock_qdrant_client.delete_collection.side_effect = Exception("Delete failed")

        tool = QdrantLegacyDataPreparationTool()

        # Test deleting collection
        result = tool.delete_collection("test_collection")

        assert result is False

    def test_create_legacy_collection_success(self, mock_qdrant_client):
        """Test successful legacy collection creation."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test creating legacy collection
        result = tool.create_legacy_collection("test_collection", 768, "Cosine")

        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()

    def test_create_legacy_collection_failure(self, mock_qdrant_client):
        """Test legacy collection creation failure."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock creation failure
        mock_qdrant_client.create_collection.side_effect = Exception("Creation failed")

        tool = QdrantLegacyDataPreparationTool()

        # Test creating legacy collection
        result = tool.create_legacy_collection("test_collection", 768, "Cosine")

        assert result is False

    def test_get_workspace_count(self, mock_qdrant_client):
        """Test getting workspace count from collection."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test getting workspace count
        count = tool.get_workspace_count("lightrag_vdb_chunks")

        assert count == 1000
        # Verify filter was applied for workspace
        mock_qdrant_client.count.assert_called()

    def test_copy_collection_data_success(self, mock_qdrant_client):
        """Test successful collection data copying."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test data copying
        stats = tool.copy_collection_data(
            source_collection="lightrag_vdb_chunks",
            target_collection="test_workspace_chunks",
            collection_type="chunks",
            workspace_count=1000,
        )

        assert stats.collection_type == "chunks"
        assert stats.source_collection == "lightrag_vdb_chunks"
        assert stats.target_collection == "test_workspace_chunks"
        assert stats.total_records == 1000
        assert stats.copied_records > 0
        assert stats.failed_records == 0
        assert len(stats.errors) == 0

        # Verify operations were called
        mock_qdrant_client.scroll.assert_called()
        mock_qdrant_client.upsert.assert_called()

    def test_copy_collection_data_with_errors(self, mock_qdrant_client):
        """Test collection data copying with errors."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock upsert to raise exception
        mock_qdrant_client.upsert.side_effect = Exception("Connection error")

        tool = QdrantLegacyDataPreparationTool()

        # Test data copying with errors
        stats = tool.copy_collection_data(
            source_collection="lightrag_vdb_chunks",
            target_collection="test_workspace_chunks",
            collection_type="chunks",
            workspace_count=1000,
        )

        assert stats.failed_records > 0
        assert len(stats.errors) > 0
        assert stats.errors[0]["error_type"] == "Exception"

    def test_process_collection_type_success(self, mock_qdrant_client):
        """Test processing a single collection type."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Mock collection exists
        mock_qdrant_client.collection_exists.return_value = True

        # Test processing collection type
        stats = tool.process_collection_type("chunks")

        assert stats is not None
        assert stats.collection_type == "chunks"
        assert stats.source_collection == "lightrag_vdb_chunks"

    def test_process_collection_type_no_source(self, mock_qdrant_client):
        """Test processing collection type when source doesn't exist."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        # Mock source collection doesn't exist
        mock_qdrant_client.collection_exists.side_effect = (
            lambda name: name != "lightrag_vdb_chunks"
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test processing non-existent collection
        stats = tool.process_collection_type("chunks")

        assert stats is None

    @pytest.mark.asyncio
    async def test_run_all_collections(self, mock_qdrant_client):
        """Test running the tool for all collections."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Mock all collections exist
        mock_qdrant_client.collection_exists.return_value = True

        # Test running for all collections
        await tool.run()

        # Should process all three collection types
        assert mock_qdrant_client.collection_exists.call_count >= 3

    @pytest.mark.asyncio
    async def test_run_specific_collections(self, mock_qdrant_client):
        """Test running the tool for specific collections."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            QdrantLegacyDataPreparationTool,
        )

        tool = QdrantLegacyDataPreparationTool()

        # Test running for specific collections
        await tool.run(["chunks", "entities"])

        # Should only process specified collections
        collection_names = [
            call[0][0] for call in mock_qdrant_client.collection_exists.call_args_list
        ]
        assert "lightrag_vdb_chunks" in collection_names
        assert "lightrag_vdb_entities" in collection_names

    def test_copy_stats_dataclass(self):
        """Test CopyStats dataclass functionality."""
        from lightrag.tools.prepare_qdrant_legacy_data import CopyStats

        # Test CopyStats creation
        stats = CopyStats(
            collection_type="chunks",
            source_collection="lightrag_vdb_chunks",
            target_collection="test_chunks",
            total_records=100,
            copied_records=50,
            failed_records=5,
            elapsed_time=2.5,
            errors=[{"error": "test error"}],
        )

        assert stats.collection_type == "chunks"
        assert stats.source_collection == "lightrag_vdb_chunks"
        assert stats.copied_records == 50
        assert stats.failed_records == 5
        assert len(stats.errors) == 1
        assert stats.elapsed_time == 2.5

    def test_copy_stats_add_error(self):
        """Test CopyStats add_error method."""
        from lightrag.tools.prepare_qdrant_legacy_data import CopyStats

        stats = CopyStats(
            collection_type="chunks",
            source_collection="lightrag_vdb_chunks",
            target_collection="test_chunks",
        )

        # Test adding error
        test_error = Exception("Test error")
        stats.add_error(1, test_error, 10)

        assert len(stats.errors) == 1
        assert stats.errors[0]["batch"] == 1
        assert stats.errors[0]["error_type"] == "Exception"
        assert stats.errors[0]["error_msg"] == "Test error"
        assert stats.errors[0]["records_lost"] == 10

    def test_constants_configuration(self):
        """Test that constants are properly configured."""
        from lightrag.tools.prepare_qdrant_legacy_data import (
            COLLECTION_NAMESPACES,
            DEFAULT_BATCH_SIZE,
            WORKSPACE_ID_FIELD,
        )

        # Test COLLECTION_NAMESPACES
        assert isinstance(COLLECTION_NAMESPACES, dict)
        assert "chunks" in COLLECTION_NAMESPACES
        assert "entities" in COLLECTION_NAMESPACES
        assert "relationships" in COLLECTION_NAMESPACES

        # Test collection namespace structure
        chunks_ns = COLLECTION_NAMESPACES["chunks"]
        assert "new" in chunks_ns
        assert "suffix" in chunks_ns
        assert chunks_ns["new"] == "lightrag_vdb_chunks"
        assert chunks_ns["suffix"] == "chunks"

        # Test other constants
        assert isinstance(DEFAULT_BATCH_SIZE, int)
        assert DEFAULT_BATCH_SIZE > 0
        assert isinstance(WORKSPACE_ID_FIELD, str)
        assert WORKSPACE_ID_FIELD == "workspace_id"


class TestQdrantLegacyDataCLI:
    """Test cases for CLI interface."""

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing."""
        from lightrag.tools.prepare_qdrant_legacy_data import main

        # Test with custom arguments
        with patch(
            "sys.argv",
            [
                "prepare_qdrant_legacy_data.py",
                "--workspace",
                "custom_workspace",
                "--types",
                "chunks,entities",
                "--batch-size",
                "200",
                "--dry-run",
            ],
        ):
            with patch(
                "lightrag.tools.prepare_qdrant_legacy_data.QdrantLegacyDataPreparationTool"
            ) as mock_tool_cls:
                mock_tool = AsyncMock()
                mock_tool.run.return_value = None
                mock_tool_cls.return_value = mock_tool

                # Should not raise exception
                with pytest.raises(SystemExit) as exc_info:
                    asyncio.run(main())

                assert exc_info.value.code == 0

                # Verify tool was created with correct parameters
                mock_tool_cls.assert_called_once()
                call_kwargs = mock_tool_cls.call_args[1]
                assert call_kwargs.get("workspace") == "custom_workspace"
                assert call_kwargs.get("batch_size") == 200

                # Verify run was called with correct params
                mock_tool.run.assert_called_once_with(["chunks", "entities"])

    def test_cli_with_default_arguments(self):
        """Test CLI with default arguments."""
        from lightrag.tools.prepare_qdrant_legacy_data import main

        with patch("sys.argv", ["prepare_qdrant_legacy_data.py"]):
            with patch(
                "lightrag.tools.prepare_qdrant_legacy_data.QdrantLegacyDataPreparationTool"
            ) as mock_tool_cls:
                mock_tool = AsyncMock()
                mock_tool.run.return_value = None
                mock_tool_cls.return_value = mock_tool

                with pytest.raises(SystemExit) as exc_info:
                    asyncio.run(main())

                assert exc_info.value.code == 0

                # Verify tool was created with defaults
                mock_tool_cls.assert_called_once()

                # Verify run was called with None (all collections)
                mock_tool.run.assert_called_once_with(None)

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        from lightrag.tools.prepare_qdrant_legacy_data import main

        with patch("sys.argv", ["prepare_qdrant_legacy_data.py"]):
            with patch(
                "lightrag.tools.prepare_qdrant_legacy_data.QdrantLegacyDataPreparationTool"
            ) as mock_tool_cls:
                mock_tool = AsyncMock()
                mock_tool.run.side_effect = Exception("Test error")
                mock_tool_cls.return_value = mock_tool

                with pytest.raises(SystemExit) as exc_info:
                    asyncio.run(main())

                assert exc_info.value.code == 1
