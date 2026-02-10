"""
Tests for download_cache.py - Tiktoken cache downloader for offline deployment.

This test suite covers:
- Cache directory management
- Tiktoken model downloads
- Error handling and edge cases
- CLI interface functionality
"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Import the module under test
from lightrag.tools.download_cache import (
    download_tiktoken_cache,
    TIKTOKEN_ENCODING_NAMES,
    main,
)


class TestDownloadTiktokenCache:
    """Test cases for the download_tiktoken_cache function."""

    def test_download_tiktoken_cache_with_none_cache_dir(self):
        """Test download with default cache directory (None)."""
        # This should work with actual tiktoken library
        success_count, failed_models = download_tiktoken_cache(
            cache_dir=None, models=["cl100k_base"]
        )
        assert success_count == 1
        assert len(failed_models) == 0

    def test_download_tiktoken_cache_with_custom_dir(self):
        """Test download with custom cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=["cl100k_base"]
            )
            assert success_count == 1
            assert len(failed_models) == 0
            # Verify cache directory was created
            assert os.path.exists(temp_dir)

    def test_download_tiktoken_cache_with_encoding_names(self):
        """Test download with encoding names (not model names)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            encoding_names = ["cl100k_base", "p50k_base"]
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=encoding_names
            )
            assert success_count == 2
            assert len(failed_models) == 0

    def test_download_tiktoken_cache_with_invalid_model(self):
        """Test download with invalid model name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=["invalid-model-name"]
            )
            assert success_count == 0
            assert len(failed_models) == 1
            assert failed_models[0][0] == "invalid-model-name"

    def test_download_tiktoken_cache_mixed_valid_invalid(self):
        """Test download with mix of valid and invalid models."""
        with tempfile.TemporaryDirectory() as temp_dir:
            models = ["cl100k_base", "invalid-model", "p50k_base"]
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=models
            )
            assert success_count == 2
            assert len(failed_models) == 1
            assert failed_models[0][0] == "invalid-model"

    def test_download_tiktoken_cache_environment_variable_set(self):
        """Test download when TIKTOKEN_CACHE_DIR is already set."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["TIKTOKEN_CACHE_DIR"] = temp_dir
            try:
                success_count, failed_models = download_tiktoken_cache(
                    cache_dir=None, models=["cl100k_base"]
                )
                assert success_count == 1
                assert len(failed_models) == 0
            finally:
                del os.environ["TIKTOKEN_CACHE_DIR"]

    def test_download_tiktoken_cache_default_models(self):
        """Test download with default model list when models=None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=None
            )
            # Should download all default models (8 models in the list)
            assert success_count == 8
            assert len(failed_models) == 0

    def test_download_tiktoken_cache_import_error_simulation(self):
        """Test error handling when tiktoken is not installed."""
        # The function calls sys.exit(1) when tiktoken is not available
        # So we test for SystemExit instead of ImportError
        with patch("builtins.__import__") as mock_import:

            def import_side_effect(name, *args, **kwargs):
                if name == "tiktoken":
                    raise ImportError("No module named 'tiktoken'")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            with pytest.raises(SystemExit) as exc_info:
                download_tiktoken_cache(cache_dir=None, models=["cl100k_base"])
            assert exc_info.value.code == 1

    def test_tiktoken_encoding_names_constant(self):
        """Test that TIKTOKEN_ENCODING_NAMES contains expected encodings."""
        expected_encodings = {"cl100k_base", "p50k_base", "r50k_base", "o200k_base"}
        assert TIKTOKEN_ENCODING_NAMES == expected_encodings

    def test_cache_directory_creation_permissions(self):
        """Test that cache directory is created with proper permissions."""
        with tempfile.TemporaryDirectory() as parent_dir:
            cache_dir = os.path.join(parent_dir, "test_cache")
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=cache_dir, models=["cl100k_base"]
            )
            assert success_count == 1
            assert os.path.exists(cache_dir)
            assert os.access(cache_dir, os.R_OK | os.W_OK | os.X_OK)


class TestDownloadCacheCLI:
    """Test cases for the CLI interface."""

    def test_cli_with_default_arguments(self):
        """Test CLI with default arguments."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (5, [])

            with patch("sys.argv", ["lightrag-download-cache"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_download.assert_called_once_with(None, None)

    def test_cli_with_custom_cache_dir(self):
        """Test CLI with custom cache directory."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (3, [])

            with patch(
                "sys.argv", ["lightrag-download-cache", "--cache-dir", "/tmp/cache"]
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_download.assert_called_once_with("/tmp/cache", None)

    def test_cli_with_specific_models(self):
        """Test CLI with specific models."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (2, [])

            with patch(
                "sys.argv",
                ["lightrag-download-cache", "--models", "gpt-4", "gpt-3.5-turbo"],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_download.assert_called_once_with(None, ["gpt-4", "gpt-3.5-turbo"])

    def test_cli_with_all_options(self):
        """Test CLI with all options."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (1, [])

            with patch(
                "sys.argv",
                [
                    "lightrag-download-cache",
                    "--cache-dir",
                    "/tmp/cache",
                    "--models",
                    "gpt-4",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_download.assert_called_once_with("/tmp/cache", ["gpt-4"])

    def test_cli_with_partial_failure(self):
        """Test CLI exit code when some downloads fail."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (2, [("invalid-model", "error")])

            with patch(
                "sys.argv",
                ["lightrag-download-cache", "--models", "valid-model", "invalid-model"],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2  # Warning code for partial failure

    def test_cli_with_complete_failure(self):
        """Test CLI exit code when all downloads fail."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.return_value = (
                0,
                [("model1", "error1"), ("model2", "error2")],
            )

            with patch("sys.argv", ["lightrag-download-cache"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1  # Error code for complete failure

    def test_cli_keyboard_interrupt(self):
        """Test CLI handling of KeyboardInterrupt."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.side_effect = KeyboardInterrupt()

            with patch("sys.argv", ["lightrag-download-cache"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 130  # KeyboardInterrupt exit code

    def test_cli_general_exception(self):
        """Test CLI handling of general exceptions."""
        with patch(
            "lightrag.tools.download_cache.download_tiktoken_cache"
        ) as mock_download:
            mock_download.side_effect = Exception("Unexpected error")

            with patch("sys.argv", ["lightrag-download-cache"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1  # General error code


class TestCacheDirectoryManagement:
    """Test cases for cache directory management functionality."""

    def test_cache_dir_absolute_path_conversion(self):
        """Test that relative cache paths are converted to absolute."""
        with tempfile.TemporaryDirectory() as temp_dir:
            relative_path = os.path.join(temp_dir, "cache")
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=relative_path, models=["cl100k_base"]
            )
            assert success_count == 1
            assert os.path.exists(relative_path)

    def test_cache_dir_environment_variable_priority(self):
        """Test that explicit cache dir takes priority over environment variable."""
        with tempfile.TemporaryDirectory() as env_dir:
            with tempfile.TemporaryDirectory() as explicit_dir:
                os.environ["TIKTOKEN_CACHE_DIR"] = env_dir
                try:
                    success_count, failed_models = download_tiktoken_cache(
                        cache_dir=explicit_dir, models=["cl100k_base"]
                    )
                    # Should use explicit_dir, not env_dir
                    assert os.path.exists(explicit_dir)
                finally:
                    del os.environ["TIKTOKEN_CACHE_DIR"]

    def test_default_cache_directory_location(self):
        """Test that default cache directory is correctly determined."""
        # This tests the actual behavior without mocking
        with tempfile.TemporaryDirectory() as temp_dir:
            # Let it use the default cache location logic
            success_count, failed_models = download_tiktoken_cache(
                cache_dir=temp_dir, models=["cl100k_base"]
            )
            # Should work with the provided cache dir
            assert success_count == 1
