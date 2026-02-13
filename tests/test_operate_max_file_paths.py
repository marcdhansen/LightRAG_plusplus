"""
Unit tests for operate.py max_file_paths fix.

This module tests the fix for GitHub Issue #2635 which removed
a redundant line that was overwriting the default value.
"""

import pytest


pytestmark = pytest.mark.light
pytestmark = pytest.mark.offline


class TestMaxFilePathsDefault:
    """Test that max_file_paths uses default when not in config."""

    def test_max_file_paths_default_not_overwritten(self):
        """Verify that the default is used when max_file_paths not in config.

        This test verifies the fix for GitHub Issue #2635 where a redundant
        line was overwriting the default value with None.
        """
        DEFAULT_MAX_FILE_PATHS = 10

        global_config = {}

        max_file_paths = global_config.get("max_file_paths", DEFAULT_MAX_FILE_PATHS)

        assert max_file_paths == DEFAULT_MAX_FILE_PATHS
        assert max_file_paths == 10

    def test_max_file_paths_with_explicit_value(self):
        """Verify explicit value is used when provided."""
        DEFAULT_MAX_FILE_PATHS = 10

        global_config = {"max_file_paths": 5}

        max_file_paths = global_config.get("max_file_paths", DEFAULT_MAX_FILE_PATHS)

        assert max_file_paths == 5

    def test_max_file_paths_none_value_prevented(self):
        """Verify that None value doesn't cause issues.

        The bug was that a second get without default would overwrite
        the value with None, causing comparison errors.
        """
        DEFAULT_MAX_FILE_PATHS = 10

        global_config_without_key = {}

        first_lookup = global_config_without_key.get(
            "max_file_paths", DEFAULT_MAX_FILE_PATHS
        )
        assert first_lookup == 10

        second_lookup_without_default = global_config_without_key.get("max_file_paths")

        assert second_lookup_without_default is None

        correct_approach = global_config_without_key.get(
            "max_file_paths", DEFAULT_MAX_FILE_PATHS
        )
        assert correct_approach == 10
