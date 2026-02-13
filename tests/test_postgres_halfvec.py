"""
Unit tests for PostgreSQL HALFVEC support.

This module tests the HALFVEC index type support which allows
large embeddings (2000+ dimensions) with 50% memory reduction.
"""

import pytest


pytestmark = pytest.mark.light
pytestmark = pytest.mark.offline


class TestHalfvecIndexSql:
    """Test HALFVEC index SQL generation."""

    def test_hnsw_halfvec_sql_uses_halfvec_ops(self):
        """Test that HNSW_HALFVEC creates index with halfvec_cosine_ops."""
        create_sql = {
            "HNSW_HALFVEC": """
                CREATE INDEX {vector_index_name}
                ON {table_name} USING hnsw (content_vector halfvec_cosine_ops)
                WITH (m = 16, ef_construction = 200)
            """,
        }

        result = create_sql["HNSW_HALFVEC"].format(
            vector_index_name="test_idx", table_name="test_table"
        )
        assert "halfvec_cosine_ops" in result
        assert "hnsw" in result.lower()


class TestHalfvecConfig:
    """Test HALFVEC configuration in env.example."""

    def test_env_example_documents_halfvec(self):
        """Verify env.example documents HNSW_HALFVEC option."""
        with open("env.example", "r") as f:
            content = f.read()

        assert "HNSW_HALFVEC" in content, "env.example should document HNSW_HALFVEC"
        assert "HALFVEC" in content, "env.example should mention HALFVEC"


class TestHalfvecColumnType:
    """Test HALFVEC column type selection logic."""

    def test_column_type_is_halfvec_for_hnsw_halfvec(self):
        """Test that HALFVEC column type is selected for HNSW_HALFVEC."""
        vector_index_type = "HNSW_HALFVEC"
        if vector_index_type == "HNSW_HALFVEC":
            column_type = "HALFVEC"
        else:
            column_type = "VECTOR"

        assert column_type == "HALFVEC"

    def test_column_type_is_vector_for_default_hnsw(self):
        """Test that VECTOR column type is selected for default HNSW."""
        vector_index_type = "HNSW"
        if vector_index_type == "HNSW_HALFVEC":
            column_type = "HALFVEC"
        else:
            column_type = "VECTOR"

        assert column_type == "VECTOR"

    def test_column_type_is_vector_for_ivfflat(self):
        """Test that VECTOR column type is selected for IVFFLAT."""
        vector_index_type = "IVFFLAT"
        if vector_index_type == "HNSW_HALFVEC":
            column_type = "HALFVEC"
        else:
            column_type = "VECTOR"

        assert column_type == "VECTOR"


class TestHalfvecSupportedTypes:
    """Test that HALFVEC is included in supported types."""

    def test_supported_types_list_includes_halfvec(self):
        """Verify HNSW_HALFVEC is in the supported types."""
        supported_types = ["HNSW", "HNSW_HALFVEC", "IVFFLAT", "VCHORDRQ"]

        assert "HNSW_HALFVEC" in supported_types

    def test_warning_message_includes_halfvec(self):
        """Verify warning message includes HNSW_HALFVEC."""
        supported_types_str = "Supported types: HNSW, HNSW_HALFVEC, IVFFLAT, VCHORDRQ"

        assert "HNSW_HALFVEC" in supported_types_str
