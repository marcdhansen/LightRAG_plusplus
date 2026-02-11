#!/usr/bin/env python3
"""
Test suite for check_initialization.py tool.

This test ensures that diagnostic tool works correctly for checking LightRAG initialization.
"""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, patch


class TestCheckInitialization:
    """Test cases for check_initialization tool."""

    @pytest.fixture
    def mock_rag_instance(self):
        """Create a mock LightRAG instance."""
        from lightrag.base import StoragesStatus

        mock_rag = MagicMock()
        # Set the correct enum value for _storages_status
        mock_rag._storages_status = StoragesStatus.INITIALIZED
        mock_rag.workspace = "test_workspace"

        # Mock storage components with proper _storage_lock
        storage_components = [
            "full_docs",
            "text_chunks",
            "entities_vdb",
            "relationships_vdb",
            "chunks_vdb",
            "doc_status",
            "llm_response_cache",
            "full_entities",
            "full_relations",
            "chunk_entity_relation_graph",
        ]

        for component in storage_components:
            storage = MagicMock()
            storage._storage_lock = MagicMock()  # Non-None value
            setattr(mock_rag, component, storage)

        mock_rag.get_storages_status.return_value = {
            "vector_storage": {"status": "ready"},
            "kv_storage": {"status": "ready"},
            "graph_storage": {"status": "ready"},
            "doc_status_storage": {"status": "ready"},
        }
        return mock_rag

    @pytest.fixture(autouse=True)
    def mock_get_namespace_data(self):
        """Mock get_namespace_data to prevent async warnings."""
        with patch(
            "lightrag.kg.shared_storage.get_namespace_data", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"status": "initialized"}
            yield mock_get

    @pytest.mark.asyncio
    async def test_check_lightrag_setup_success(self, mock_rag_instance):
        """Test successful LightRAG setup check."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        result = await check_lightrag_setup(mock_rag_instance, verbose=False)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_lightrag_setup_failure(self):
        """Test LightRAG setup check with missing components."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        mock_rag_fail = MagicMock()
        # Missing _storages_status attribute to simulate failure
        del mock_rag_fail._storages_status
        mock_rag_fail.get_storages_status.return_value = {
            "vector_storage": {"status": "error"},
            "kv_storage": {"status": "ready"},
        }

        result = await check_lightrag_setup(mock_rag_fail, verbose=False)

        assert result is False

    def test_import(self):
        """Test that check_initialization can be imported."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        assert callable(check_lightrag_setup)

    @pytest.mark.asyncio
    async def test_demo_mode(self):
        """Test demo mode functionality."""
        from lightrag.tools.check_initialization import demo

        with patch(
            "lightrag.tools.check_initialization.check_lightrag_setup"
        ) as mock_check:
            mock_check.return_value = True

            # This should not raise an exception
            try:
                await demo()
            except SystemExit:
                # Expected for demo mode
                pass

    @pytest.mark.asyncio
    async def test_verbose_output(self, mock_rag_instance):
        """Test verbose output mode."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        result = await check_lightrag_setup(mock_rag_instance, verbose=True)

        assert result is True

    def test_constants(self):
        """Test that constants are defined correctly."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        # Basic validation that function exists
        assert hasattr(check_lightrag_setup, "__call__")
        assert check_lightrag_setup.__code__.co_argcount == 2  # rag_instance, verbose
