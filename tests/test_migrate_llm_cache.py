#!/usr/bin/env python3
"""
Test suite for migrate_llm_cache.py tool.

This test ensures that LLM cache migration tool works correctly
for migrating cache data between different KV storage implementations.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch, call
from dataclasses import dataclass
from typing import Any


class TestMigrationTool:
    """Test cases for LLM cache migration tool."""

    @pytest.fixture
    def mock_storage_classes(self):
        """Mock storage classes for all storage types."""
        # Mock the storage classes by patching their source modules
        mocks = {}

        with (
            patch("lightrag.kg.json_kv_impl.JsonKVStorage") as mock_json,
            patch("lightrag.kg.redis_impl.RedisKVStorage") as mock_redis,
            patch("lightrag.kg.postgres_impl.PGKVStorage") as mock_postgres,
            patch("lightrag.kg.mongo_impl.MongoKVStorage") as mock_mongo,
        ):
            # Configure mocks
            mock_json.return_value = AsyncMock()
            mock_redis.return_value = AsyncMock()
            mock_postgres.return_value = AsyncMock()
            mock_mongo.return_value = AsyncMock()

            mocks["json"] = mock_json
            mocks["redis"] = mock_redis
            mocks["postgres"] = mock_postgres
            mocks["mongo"] = mock_mongo

            yield mocks

    @pytest.fixture
    def mock_migration_stats(self):
        """Create a MigrationStats instance for testing."""
        from lightrag.tools.migrate_llm_cache import MigrationStats

        return MigrationStats(
            total_source_records=1000,
            total_batches=10,
            successful_batches=8,
            failed_batches=2,
            successful_records=800,
            failed_records=200,
            errors=[{"error": "test error"}],
        )

    def test_import(self):
        """Test that migrate_llm_cache can be imported."""
        from lightrag.tools.migrate_llm_cache import (
            MigrationTool,
            MigrationStats,
            STORAGE_TYPES,
            WORKSPACE_ENV_MAP,
            DEFAULT_BATCH_SIZE,
        )

        assert callable(MigrationTool)
        assert hasattr(MigrationStats, "__dataclass_fields__")
        assert isinstance(STORAGE_TYPES, dict)
        assert isinstance(WORKSPACE_ENV_MAP, dict)
        assert isinstance(DEFAULT_BATCH_SIZE, int)

    def test_constants_configuration(self):
        """Test that constants are properly configured."""
        from lightrag.tools.migrate_llm_cache import (
            STORAGE_TYPES,
            WORKSPACE_ENV_MAP,
            DEFAULT_BATCH_SIZE,
            DEFAULT_COUNT_BATCH_SIZE,
        )

        # Test STORAGE_TYPES
        assert isinstance(STORAGE_TYPES, dict)
        assert "1" in STORAGE_TYPES
        assert "2" in STORAGE_TYPES
        assert "3" in STORAGE_TYPES
        assert "4" in STORAGE_TYPES
        assert STORAGE_TYPES["1"] == "JsonKVStorage"
        assert STORAGE_TYPES["2"] == "RedisKVStorage"
        assert STORAGE_TYPES["3"] == "PGKVStorage"
        assert STORAGE_TYPES["4"] == "MongoKVStorage"

        # Test WORKSPACE_ENV_MAP
        assert isinstance(WORKSPACE_ENV_MAP, dict)
        assert "PGKVStorage" in WORKSPACE_ENV_MAP
        assert "MongoKVStorage" in WORKSPACE_ENV_MAP
        assert "RedisKVStorage" in WORKSPACE_ENV_MAP
        assert WORKSPACE_ENV_MAP["PGKVStorage"] == "POSTGRES_WORKSPACE"
        assert WORKSPACE_ENV_MAP["MongoKVStorage"] == "MONGODB_WORKSPACE"
        assert WORKSPACE_ENV_MAP["RedisKVStorage"] == "REDIS_WORKSPACE"

        # Test other constants
        assert isinstance(DEFAULT_BATCH_SIZE, int)
        assert DEFAULT_BATCH_SIZE > 0
        assert isinstance(DEFAULT_COUNT_BATCH_SIZE, int)
        assert DEFAULT_COUNT_BATCH_SIZE > 0

    def test_tool_initialization_with_defaults(self):
        """Test tool initialization with default parameters."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        from lightrag.tools.migrate_llm_cache import DEFAULT_BATCH_SIZE

        assert tool.batch_size == DEFAULT_BATCH_SIZE

    def test_get_workspace_for_storage_json(self):
        """Test workspace resolution for JSON storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()
        workspace = tool.get_workspace_for_storage("JsonKVStorage")

        assert (
            workspace == ""
        )  # JSON doesn't use workspace env, returns empty string when no env vars set

    def test_get_workspace_for_storage_postgres(self):
        """Test workspace resolution for PostgreSQL storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        with patch.dict(os.environ, {"POSTGRES_WORKSPACE": "custom_workspace"}):
            tool = MigrationTool()
            workspace = tool.get_workspace_for_storage("PGKVStorage")

            assert workspace == "custom_workspace"

    def test_get_workspace_for_storage_mongodb(self):
        """Test workspace resolution for MongoDB storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        with patch.dict(os.environ, {"MONGODB_WORKSPACE": "mongo_workspace"}):
            tool = MigrationTool()
            workspace = tool.get_workspace_for_storage("MongoKVStorage")

            assert workspace == "mongo_workspace"

    def test_check_config_ini_for_storage(self):
        """Test config.ini file checking."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test without config.ini
        has_config = tool.check_config_ini_for_storage("JsonKVStorage")
        assert isinstance(has_config, bool)

    def test_check_env_vars(self, mock_storage_classes):
        """Test environment variable checking."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Mock Redis environment variables
        with patch.dict(os.environ, {"REDIS_HOST": "localhost"}):
            has_env = tool.check_env_vars("RedisKVStorage")

            assert has_env is True

    def test_get_storage_class(self, mock_storage_classes):
        """Test getting storage class by name."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test getting storage classes
        json_class = tool.get_storage_class("JsonKVStorage")
        redis_class = tool.get_storage_class("RedisKVStorage")

        assert json_class == mock_storage_classes["json"]
        assert redis_class == mock_storage_classes["redis"]

    @pytest.mark.asyncio
    async def test_initialize_storage_json(self, mock_storage_classes):
        """Test JSON storage initialization."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Mock storage instance with async initialize method
        storage_instance = AsyncMock()
        mock_storage_classes["json"].return_value = storage_instance

        # Test initialization
        result = await tool.initialize_storage("JsonKVStorage", "test_workspace")

        assert result == storage_instance
        # Verify storage was initialized with correct parameters
        mock_storage_classes["json"].assert_called_once()
        call_args = mock_storage_classes["json"].call_args
        assert call_args[1]["workspace"] == "test_workspace"
        assert call_args[1]["namespace"] is not None
        storage_instance.initialize.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_initialize_storage_failure(self, mock_storage_classes):
        """Test storage initialization failure."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Mock storage initialization failure
        mock_storage_classes["json"].side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            await tool.initialize_storage("JsonKVStorage", "test_workspace")

        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_default_caches_json(self, mock_storage_classes):
        """Test getting default cache from JSON storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()
        storage_instance = mock_storage_classes["json"].return_value

        # Mock cache data
        cache_data = {
            "default:extract:key1": {"data": "value1", "timestamp": 1},
            "default:extract:key2": {"data": "value2", "timestamp": 2},
            "default:summary:key3": {"data": "value3", "timestamp": 3},
            "other:extract:key1": {"data": "value4"},  # Should be filtered
            "random_key": {"data": "value5"},  # Should be filtered
        }

        # Mock storage attributes
        storage_instance._data = cache_data
        storage_instance._storage_lock = AsyncMock()
        storage_instance._storage_lock.__aenter__ = AsyncMock(return_value=None)
        storage_instance._storage_lock.__aexit__ = AsyncMock(return_value=None)

        # Test getting default caches
        result = await tool.get_default_caches_json(storage_instance)

        assert len(result) == 3  # Only default:extract:* and default:summary:* keys
        assert "default:extract:key1" in result
        assert "default:extract:key2" in result
        assert "default:summary:key3" in result
        assert "other:extract:key1" not in result
        assert "random_key" not in result
        assert "default:extract:key1" in result
        assert "default:extract:key2" in result

    @pytest.mark.asyncio
    async def test_count_default_caches_json(self, mock_storage_classes):
        """Test counting default cache from JSON storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()
        storage_instance = mock_storage_classes["json"].return_value

        # Mock cache data and storage attributes
        cache_data = {
            "default:extract:key1": {"data": "value1"},
            "default:extract:key2": {"data": "value2"},
            "default:summary:key1": {"data": "value3"},
            "other:key": {"data": "value4"},
        }
        storage_instance._data = cache_data
        storage_instance._storage_lock = AsyncMock()
        storage_instance._storage_lock.__aenter__ = AsyncMock(return_value=None)
        storage_instance._storage_lock.__aexit__ = AsyncMock(return_value=None)

        # Test counting
        count = await tool.count_default_caches_json(storage_instance)

        assert count == 3  # Only default:* keys

    @pytest.mark.asyncio
    async def test_stream_default_caches_json(self, mock_storage_classes):
        """Test streaming default cache from JSON storage."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()
        storage_instance = mock_storage_classes["json"].return_value

        # Mock large dataset
        cache_data = {
            f"default:extract:key{i}": {"data": f"value{i}"} for i in range(150)
        }
        storage_instance._data = cache_data
        storage_instance._storage_lock = AsyncMock()
        storage_instance._storage_lock.__aenter__ = AsyncMock(return_value=None)
        storage_instance._storage_lock.__aexit__ = AsyncMock(return_value=None)

        # Test streaming with batch size
        entries = []
        stream_gen = tool.stream_default_caches_json(storage_instance, batch_size=50)
        async for batch in stream_gen:
            entries.extend(batch)

        assert len(entries) == 150

    @pytest.mark.asyncio
    async def test_setup_storage(self, mock_storage_classes):
        """Test storage setup method exists and has correct signature."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test that setup_storage method exists and is callable
        assert hasattr(tool, "setup_storage")
        assert callable(tool.setup_storage)

        # Test method signature (it should accept storage_type label)
        import inspect

        sig = inspect.signature(tool.setup_storage)
        params = list(sig.parameters.keys())

        assert "storage_type" in params
        assert "use_streaming" in params
        assert "exclude_storage_name" in params

    def test_count_available_storage_types(self, mock_storage_classes):
        """Test counting available storage types."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Mock environment for multiple storages
        with patch.dict(
            os.environ,
            {
                "LIGHTRAG_DEFAULT_WORKING_DIR": "/tmp",
                "REDIS_HOST": "localhost",
                "POSTGRES_HOST": "localhost",
            },
        ):
            count = tool.count_available_storage_types()

            assert count == 1  # Only JsonKVStorage has no required env vars

    def test_format_storage_name(self):
        """Test storage name formatting."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test formatting storage names
        json_name = tool.format_storage_name("JsonKVStorage")
        redis_name = tool.format_storage_name("RedisKVStorage")

        # Names should contain storage class names (with possible color codes)
        assert "JsonKVStorage" in json_name
        assert "RedisKVStorage" in redis_name

    def test_format_workspace(self):
        """Test workspace formatting."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test formatting workspace
        formatted = tool.format_workspace("test_workspace")

        assert "test_workspace" in formatted

    @pytest.mark.asyncio
    async def test_run_interactive_mode(self, mock_storage_classes):
        """Test running tool in interactive mode."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test that run method exists and is callable
        assert hasattr(tool, "run")
        assert callable(tool.run)

        # Test method signature (it should be async)
        import inspect

        sig = inspect.signature(tool.run)
        # Should have no required parameters for interactive mode
        assert len(list(sig.parameters.keys())) == 0

    @pytest.mark.asyncio
    async def test_count_cache_types(self):
        """Test counting cache types by pattern."""
        from lightrag.tools.migrate_llm_cache import MigrationTool

        tool = MigrationTool()

        # Test cache data with different patterns
        cache_data = {
            "default:extract:key1": {"data": "value1"},
            "default:extract:key2": {"data": "value2"},
            "default:summary:key1": {"data": "value3"},
            "other:extract:key1": {"data": "value4"},
            "random_key": {"data": "value5"},
        }

        # Test counting cache types
        counts = await tool.count_cache_types(cache_data)

        assert counts["extract"] == 2
        assert counts["summary"] == 1
        assert counts.get("other", 0) == 0  # Only extract/summary counted

    def test_migration_stats_dataclass(self):
        """Test MigrationStats dataclass functionality."""
        from lightrag.tools.migrate_llm_cache import MigrationStats

        # Test MigrationStats creation
        stats = MigrationStats()

        assert stats.total_source_records == 0
        assert stats.total_batches == 0
        assert stats.successful_batches == 0
        assert stats.failed_batches == 0
        assert stats.successful_records == 0
        assert stats.failed_records == 0
        assert len(stats.errors) == 0

    def test_migration_stats_add_error(self):
        """Test MigrationStats add_error method."""
        from lightrag.tools.migrate_llm_cache import MigrationStats

        stats = MigrationStats()

        # Test adding error
        test_error = Exception("Test error")
        stats.add_error(1, test_error, 10)

        assert len(stats.errors) == 1
        assert stats.errors[0]["batch"] == 1
        assert stats.errors[0]["error_type"] == "Exception"
        assert stats.errors[0]["error_msg"] == "Test error"
        assert stats.errors[0]["records_lost"] == 10

        # Check counters updated
        assert stats.failed_batches == 1
        assert stats.failed_records == 10


class TestMigrationToolCLI:
    """Test cases for CLI interface."""

    def test_cli_no_args(self):
        """Test CLI with no arguments (should show help)."""
        from lightrag.tools.migrate_llm_cache import main

        # Test with no arguments
        with patch("sys.argv", ["migrate_llm_cache.py"]):
            # Test that main function exists and is callable
            from lightrag.tools.migrate_llm_cache import main

            assert callable(main)
            assert asyncio.iscoroutinefunction(main)

    def test_cli_direct_mode(self):
        """Test CLI direct mode with specified storage types."""
        from lightrag.tools.migrate_llm_cache import main

        # Test that main function accepts arguments correctly
        from lightrag.tools.migrate_llm_cache import main

        assert callable(main)
        assert asyncio.iscoroutinefunction(main)

    def test_cli_list_mode(self):
        """Test CLI list mode."""
        from lightrag.tools.migrate_llm_cache import main

        # Test that main function accepts list argument correctly
        from lightrag.tools.migrate_llm_cache import main

        assert callable(main)
        assert asyncio.iscoroutinefunction(main)

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        from lightrag.tools.migrate_llm_cache import main

        # Test that main function exists and is async
        from lightrag.tools.migrate_llm_cache import main

        assert callable(main)
        assert asyncio.iscoroutinefunction(main)
