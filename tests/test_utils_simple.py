"""
Test suite for lightrag.utils module (core functions)

Tests cover core utility functions that are confirmed to exist.
"""

import asyncio
import json
from unittest.mock import mock_open, patch, MagicMock

import pytest

from lightrag.utils import (
    compute_args_hash,
    compute_mdhash_id,
    convert_to_user_format,
    cosine_similarity,
    generate_cache_key,
    get_content_summary,
    handle_cache,
    sanitize_text_for_encoding,
    set_verbose_debug,
    split_string_by_multi_markers,
    statistic_data,
    verbose_debug,
)


class TestStringSplittingFunctions:
    """Test cases for string manipulation functions"""

    def test_split_string_by_multi_markers_single_marker(self):
        """Test splitting with single marker"""
        text = "item1,item2,item3"
        markers = [","]

        result = split_string_by_multi_markers(text, markers)

        assert result == ["item1", "item2", "item3"]

    def test_split_string_by_multi_markers_multiple_markers(self):
        """Test splitting with multiple markers"""
        text = "item1,item2;item3|item4"
        markers = [",", ";", "|"]

        result = split_string_by_multi_markers(text, markers)

        assert result == ["item1", "item2", "item3", "item4"]

    def test_split_string_by_multi_markers_empty_string(self):
        """Test splitting empty string"""
        text = ""
        markers = [","]

        result = split_string_by_multi_markers(text, markers)

        assert result == [""]

    def test_split_string_by_multi_markers_no_markers(self):
        """Test splitting when no markers found"""
        text = "nosplithere"
        markers = [","]

        result = split_string_by_multi_markers(text, markers)

        assert result == ["nosplithere"]

    def test_split_string_by_multi_markers_consecutive_markers(self):
        """Test splitting with consecutive markers"""
        text = "item1,,,item2"
        markers = [","]

        result = split_string_by_multi_markers(text, markers)

        assert result == ["item1", "", "", "item2"]


class TestHashAndKeyFunctions:
    """Test cases for hash and key generation functions"""

    def test_compute_args_hash_consistency(self):
        """Test that args hash is consistent"""
        args = ("arg1", "arg2", {"key": "value"})

        hash1 = compute_args_hash(args)
        hash2 = compute_args_hash(args)

        assert hash1 == hash2

    def test_compute_args_hash_different_inputs(self):
        """Test that different args produce different hashes"""
        args1 = ("arg1", "arg2")
        args2 = ("arg2", "arg1")

        hash1 = compute_args_hash(args1)
        hash2 = compute_args_hash(args2)

        assert hash1 != hash2

    def test_compute_mdhash_id(self):
        """Test MD5 hash ID computation"""
        text = "test string"

        result = compute_mdhash_id(text)

        # MD5 should be 32 character hexadecimal string
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_compute_mdhash_id_consistency(self):
        """Test MD5 hash consistency"""
        text = "test string"

        hash1 = compute_mdhash_id(text)
        hash2 = compute_mdhash_id(text)

        assert hash1 == hash2

    def test_generate_cache_key(self):
        """Test cache key generation"""
        namespace = "test_namespace"
        args = ("arg1", "arg2")
        kwargs = {"key": "value"}

        key = generate_cache_key(namespace, *args, **kwargs)

        assert isinstance(key, str)
        assert "test_namespace" in key
        # Should be deterministic
        key2 = generate_cache_key(namespace, *args, **kwargs)
        assert key == key2


class TestTextProcessingFunctions:
    """Test cases for text processing functions"""

    def test_sanitize_text_for_encoding(self):
        """Test text sanitization for encoding"""
        dirty_text = "Hello\nWorld\tTest"

        result = sanitize_text_for_encoding(dirty_text)

        # Should normalize whitespace
        assert "\n" not in result or "\t" not in result

    def test_get_content_summary_short_text(self):
        """Test content summary for short text"""
        short_text = "This is short"

        result = get_content_summary(short_text, max_length=100)

        assert result == "This is short"

    def test_get_content_summary_long_text(self):
        """Test content summary for long text"""
        long_text = "This is a very long text that should be truncated because it exceeds maximum length limit for summary generation and testing purposes"

        result = get_content_summary(long_text, max_length=50)

        assert len(result) <= 50
        assert "..." in result or len(result) < len(long_text)


class TestMathAndSimilarityFunctions:
    """Test cases for mathematical and similarity functions"""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]

        result = cosine_similarity(vec1, vec2)

        # Identical vectors should have similarity of 1.0
        assert abs(result - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors"""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]

        result = cosine_similarity(vec1, vec2)

        # Orthogonal vectors should have similarity of 0.0
        assert abs(result - 0.0) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors"""
        vec1 = [1.0, 2.0]
        vec2 = [-1.0, -2.0]

        result = cosine_similarity(vec1, vec2)

        # Opposite vectors should have similarity of -1.0
        assert abs(result - (-1.0)) < 1e-6


class TestCacheFunctions:
    """Test cases for cache-related functions"""

    @pytest.mark.asyncio
    async def test_handle_cache_none_hashing_kv(self):
        """Test handle_cache with None hashing_kv returns None"""
        result = await handle_cache(None, "test_hash", "test_prompt")
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_cache_disabled_llm_cache(self):
        """Test handle_cache when LLM cache is disabled"""
        # Create mock hashing_kv with disabled cache
        mock_hashing_kv = MagicMock()
        mock_hashing_kv.global_config = {"enable_llm_cache_for_entity_extract": False}

        result = await handle_cache(
            mock_hashing_kv, "test_hash", "test_prompt", mode="default"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_cache_hit(self):
        """Test handle_cache when cache hit occurs"""
        mock_hashing_kv = MagicMock()
        mock_hashing_kv.global_config = {"enable_llm_cache_for_entity_extract": True}
        cache_content = "cached result"
        cache_entry = {"return": cache_content, "create_time": 1234567890}

        async def mock_get_by_id(key):
            return cache_entry

        mock_hashing_kv.get_by_id = mock_get_by_id

        result = await handle_cache(
            mock_hashing_kv, "test_hash", "test_prompt", mode="default"
        )
        assert result == (cache_content, 1234567890)

    @pytest.mark.asyncio
    async def test_handle_cache_miss(self):
        """Test handle_cache when cache miss occurs"""
        mock_hashing_kv = MagicMock()
        mock_hashing_kv.global_config = {"enable_llm_cache_for_entity_extract": True}

        async def mock_get_by_id(key):
            return None

        mock_hashing_kv.get_by_id = mock_get_by_id

        result = await handle_cache(
            mock_hashing_kv, "test_hash", "test_prompt", mode="default"
        )
        assert result is None


class TestUtilityFunctions:
    """Test cases for general utility functions"""

    def test_statistic_data(self):
        """Test statistic data function"""
        data = [1, 2, 3, 4, 5]

        result = statistic_data(data)

        assert "mean" in result
        assert "median" in result
        assert "std" in result
        assert "min" in result
        assert "max" in result

    def test_convert_to_user_format(self):
        """Test user format conversion"""
        data = {"key": "value", "nested": {"inner": "data"}}

        result = convert_to_user_format(data)

        # Should return formatted version
        assert isinstance(result, (dict, str, list))

    def test_set_verbose_debug(self):
        """Test setting verbose debug"""
        with patch("lightrag.utils.VERBOSE_DEBUG", False):
            set_verbose_debug(True)
            # Should update global debug setting
            from lightrag.utils import VERBOSE_DEBUG

            assert VERBOSE_DEBUG is True

    def test_verbose_debug(self):
        """Test verbose debug function"""
        with patch("lightrag.utils.logger.debug") as mock_debug:
            with patch("lightrag.utils.VERBOSE_DEBUG", True):
                verbose_debug("Debug message")

                mock_debug.assert_called_once_with("Debug message")


class TestIntegrationScenarios:
    """Integration test scenarios for utils module"""

    def test_text_processing_pipeline(self):
        """Test a complete text processing pipeline"""
        # Test splitting and processing together
        dirty_text = "item1,item2\nitem3\t,item4"

        # Split by markers
        items = split_string_by_multi_markers(dirty_text, [",", "\n", "\t"])
        assert items == ["item1", "item2", "item3", "item4"]

        # Generate cache key from processed items
        cache_key = generate_cache_key("test", items)
        assert isinstance(cache_key, str)

        # Compute hash consistency
        hash1 = compute_args_hash(items)
        hash2 = compute_args_hash(items)
        assert hash1 == hash2

    def test_cache_and_persistence_pipeline(self):
        """Test cache handling and persistence workflow"""
        # Test data
        test_data = {"results": [1, 2, 3], "metadata": {"processed": True}}

        # Save to cache
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_dump:
                handle_cache(test_data, "test_cache.json", "save")

                mock_file.assert_called_once()
                mock_dump.assert_called_once()

        # Load from cache
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(test_data))
        ) as mock_file:
            with patch("json.load") as mock_load:
                mock_load.return_value = test_data

                loaded_data = handle_cache(None, "test_cache.json", "load")

                assert loaded_data == test_data

    @pytest.mark.parametrize(
        "text,markers,expected",
        [
            ("a,b,c", [","], ["a", "b", "c"]),
            ("a|b;c", ["|", ";"], ["a", "b", "c"]),
            ("abc", [","], ["abc"]),
            ("", [","], [""]),
            ("a,,,b", [","], ["a", "", "", "b"]),
        ],
    )
    def test_split_string_variations(self, text, markers, expected):
        """Test split_string_by_multi_markers with various inputs"""
        result = split_string_by_multi_markers(text, markers)
        assert result == expected

    @pytest.mark.parametrize(
        "vec1,vec2,expected_range",
        [
            ([1, 0], [1, 0], (0.999, 1.001)),  # Identical
            ([1, 0], [0, 1], (-0.001, 0.001)),  # Orthogonal
            ([1, 2], [-1, -2], (-1.001, -0.999)),  # Opposite
        ],
    )
    def test_cosine_similarity_variations(self, vec1, vec2, expected_range):
        """Test cosine similarity with various vector combinations"""
        result = cosine_similarity(vec1, vec2)
        assert expected_range[0] <= result <= expected_range[1]

    @pytest.mark.parametrize(
        "data,expected_keys",
        [
            ([1, 2, 3, 4, 5], ["mean", "median", "std", "min", "max"]),
            ([], ["mean", "median", "std", "min", "max"]),
            ([42], ["mean", "median", "std", "min", "max"]),
        ],
    )
    def test_statistic_data_variations(self, data, expected_keys):
        """Test statistic_data with various inputs"""
        result = statistic_data(data)
        for key in expected_keys:
            assert key in result
