"""
Tests for clean_llm_query_cache.py - LLM query cache cleanup tool.

This test suite covers:
- Basic functionality testing
- Configuration validation
- Statistics tracking
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import the module under test
from lightrag.tools.clean_llm_query_cache import (
    CleanupStats,
    CleanupTool,
    STORAGE_TYPES,
    QUERY_MODES,
    CACHE_TYPES,
    DEFAULT_BATCH_SIZE,
    main,
    async_main,
)


class TestCleanupStats:
    """Test cases for CleanupStats dataclass."""

    def test_cleanup_stats_initialization(self):
        """Test CleanupStats initializes with correct defaults."""
        stats = CleanupStats()

        assert stats.counts_before == {}
        assert stats.total_to_delete == 0
        assert stats.total_batches == 0
        assert stats.successful_batches == 0
        assert stats.failed_batches == 0
        assert stats.successfully_deleted == 0
        assert stats.failed_to_delete == 0
        assert stats.counts_after == {}
        assert stats.errors == []

    def test_add_error(self):
        """Test error recording functionality."""
        stats = CleanupStats()
        test_error = ValueError("Test error")

        stats.add_error(1, test_error, 100)

        assert len(stats.errors) == 1
        assert stats.errors[0]["batch"] == 1
        assert stats.errors[0]["error_type"] == "ValueError"
        assert stats.errors[0]["error_msg"] == "Test error"
        assert stats.errors[0]["records_lost"] == 100
        assert "timestamp" in stats.errors[0]

    def test_initialize_counts(self):
        """Test counts initialization."""
        stats = CleanupStats()
        stats.initialize_counts()

        expected = {
            mode: {cache_type: 0 for cache_type in CACHE_TYPES} for mode in QUERY_MODES
        }
        assert stats.counts_before == expected
        assert stats.counts_after == expected


class TestCleanupTool:
    """Test cases for CleanupTool class."""

    def test_cleanup_tool_initialization(self):
        """Test CleanupTool initializes correctly."""
        tool = CleanupTool()

        assert tool.storage is None
        assert tool.workspace == ""
        assert tool.batch_size == DEFAULT_BATCH_SIZE

    def test_get_workspace_for_storage(self):
        """Test workspace retrieval for different storage types."""
        tool = CleanupTool()

        # Test storage types when no environment variables are set
        assert tool.get_workspace_for_storage("PGKVStorage") == ""
        assert tool.get_workspace_for_storage("MongoKVStorage") == ""
        assert tool.get_workspace_for_storage("RedisKVStorage") == ""

        # Test storage type that doesn't require workspace
        assert tool.get_workspace_for_storage("JsonKVStorage") == ""

    @patch.dict(os.environ, {"POSTGRES_WORKSPACE": "test_workspace"})
    def test_get_workspace_for_storage_with_env_var(self):
        """Test workspace retrieval when environment variable is set."""
        tool = CleanupTool()

        workspace = tool.get_workspace_for_storage("PGKVStorage")
        assert workspace == "test_workspace"

    def test_check_config_ini_for_storage(self):
        """Test configuration file checking."""
        tool = CleanupTool()

        # This test should work with a mock approach
        with patch("os.path.exists", return_value=True):
            result = tool.check_config_ini_for_storage("JsonKVStorage")
            # The actual result depends on configuration content
            assert isinstance(result, bool)

    @patch.dict(os.environ, {"POSTGRES_HOST": "localhost", "POSTGRES_DB": "test"})
    def test_check_env_vars_pg(self):
        """Test environment variable checking for PostgreSQL."""
        tool = CleanupTool()

        result = tool.check_env_vars("PGKVStorage")
        # This should return True if all required env vars are present
        assert isinstance(result, bool)

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/test"})
    def test_check_env_vars_mongo(self):
        """Test environment variable checking for MongoDB."""
        tool = CleanupTool()

        result = tool.check_env_vars("MongoKVStorage")
        # This should return True if all required env vars are present
        assert isinstance(result, bool)

    @patch.dict(os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379"})
    def test_check_env_vars_redis(self):
        """Test environment variable checking for Redis."""
        tool = CleanupTool()

        result = tool.check_env_vars("RedisKVStorage")
        # This should return True if all required env vars are present
        assert isinstance(result, bool)

    def test_check_env_vars_json(self):
        """Test environment variable checking for JSON storage."""
        tool = CleanupTool()

        result = tool.check_env_vars("JsonKVStorage")
        # JSON storage doesn't require specific env vars
        assert result is True

    @patch("lightrag.kg.json_kv_impl.JsonKVStorage")
    def test_get_storage_class_json(self, mock_storage_class):
        """Test storage class retrieval for JSON storage."""
        tool = CleanupTool()

        result = tool.get_storage_class("JsonKVStorage")
        assert result == mock_storage_class

    @patch("lightrag.kg.redis_impl.RedisKVStorage")
    def test_get_storage_class_redis(self, mock_storage_class):
        """Test storage class retrieval for Redis storage."""
        tool = CleanupTool()

        result = tool.get_storage_class("RedisKVStorage")
        assert result == mock_storage_class

    def test_get_storage_class_invalid(self):
        """Test storage class retrieval for invalid storage type."""
        tool = CleanupTool()

        with pytest.raises(ValueError):
            tool.get_storage_class("InvalidStorage")

    def test_print_header(self):
        """Test header printing."""
        tool = CleanupTool()

        # This should not raise an exception
        tool.print_header()

    def test_print_storage_types(self):
        """Test storage types printing."""
        tool = CleanupTool()

        # This should not raise an exception
        tool.print_storage_types()

    def test_format_workspace(self):
        """Test workspace formatting."""
        tool = CleanupTool()

        # Test normal workspace
        result = tool.format_workspace("test_workspace")
        assert result == f"\033[1;36mtest_workspace\033[0m"

        # Test workspace with quotes - method doesn't strip quotes
        result = tool.format_workspace('"test_workspace"')
        assert result == f'\033[1;36m"test_workspace"\033[0m'


class TestCleanCacheTool:
    """Test cases for overall clean cache tool functionality."""

    def test_constants(self):
        """Test that constants are correctly defined."""
        assert "JsonKVStorage" in STORAGE_TYPES.values()
        assert "RedisKVStorage" in STORAGE_TYPES.values()
        assert "PGKVStorage" in STORAGE_TYPES.values()
        assert "MongoKVStorage" in STORAGE_TYPES.values()

        assert "mix" in QUERY_MODES
        assert "hybrid" in QUERY_MODES
        assert "local" in QUERY_MODES
        assert "global" in QUERY_MODES

        assert "query" in CACHE_TYPES
        assert "keywords" in CACHE_TYPES

        assert DEFAULT_BATCH_SIZE == 1000

    @patch("builtins.input")
    @patch("lightrag.tools.clean_llm_query_cache.CleanupTool")
    @patch("sys.argv", ["clean_llm_query_cache.py"])
    def test_main_function_interactive_mode(self, mock_tool_class, mock_input):
        """Test main function in interactive mode."""
        # Setup mocks
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool
        mock_input.side_effect = ["1", "y"]  # Choose JsonKVStorage, confirm deletion

        # Mock the async run method
        mock_run = AsyncMock()
        mock_tool.run = mock_run

        # Run the main function
        main()

        # Verify tool was created and run was called
        mock_tool_class.assert_called_once()
        mock_run.assert_called_once()

    @patch("builtins.input")
    @patch("lightrag.tools.clean_llm_query_cache.CleanupTool")
    @patch("sys.argv", ["clean_llm_query_cache.py"])
    def test_main_function_abort(self, mock_tool_class, mock_input):
        """Test main function when user aborts."""
        # Setup mocks
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool
        mock_input.side_effect = ["1", "n"]  # Choose JsonKVStorage, abort deletion

        # Mock the run method to be async so it can be awaited
        mock_tool.run = AsyncMock()

        # Run the main function
        main()

        # Verify tool was created and run was called (but should return early)
        mock_tool_class.assert_called_once()
        mock_tool.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_main(self):
        """Test async_main function."""
        with patch(
            "lightrag.tools.clean_llm_query_cache.CleanupTool"
        ) as mock_tool_class:
            mock_tool = MagicMock()
            mock_tool_class.return_value = mock_tool
            mock_run = AsyncMock()
            mock_tool.run = mock_run

            await async_main()

            mock_tool_class.assert_called_once()
            mock_run.assert_called_once()


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_invalid_storage_type_handling(self):
        """Test handling of invalid storage types."""
        tool = CleanupTool()

        with pytest.raises(ValueError):
            tool.get_storage_class("InvalidStorageType")

    def test_constants_values(self):
        """Test that storage types are correctly mapped."""
        expected_storage_types = {
            "1": "JsonKVStorage",
            "2": "RedisKVStorage",
            "3": "PGKVStorage",
            "4": "MongoKVStorage",
        }
        assert STORAGE_TYPES == expected_storage_types
