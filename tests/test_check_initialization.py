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
        mock_rag = MagicMock()
        mock_rag.storage_status = {
            "vector_storage": "initialized",
            "kv_storage": "initialized",
            "graph_storage": "initialized",
            "doc_status_storage": "initialized",
        }
        mock_rag.get_storages_status.return_value = {
            "vector_storage": {"status": "ready"},
            "kv_storage": {"status": "ready"},
            "graph_storage": {"status": "ready"},
            "doc_status_storage": {"status": "ready"},
        }
        return mock_rag

    @pytest.mark.asyncio
    async def test_check_lightrag_setup_success(self, mock_rag_instance):
        """Test successful LightRAG setup check."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        result = await check_lightrag_setup(mock_rag_instance, verbose=False)

        assert result is True
        mock_rag_instance.get_storages_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_lightrag_setup_failure(self):
        """Test LightRAG setup check with missing components."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        mock_rag_fail = MagicMock()
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
        mock_rag_instance.get_storages_status.assert_called_once()

    def test_constants(self):
        """Test that constants are defined correctly."""
        from lightrag.tools.check_initialization import check_lightrag_setup

        # Basic validation that function exists
        assert hasattr(check_lightrag_setup, "__call__")
        assert check_lightrag_setup.__code__.co_argcount == 2  # rag_instance, verbose
