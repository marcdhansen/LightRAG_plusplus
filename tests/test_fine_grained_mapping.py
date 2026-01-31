"""
Tests for fine-grained entity type mapping.

These tests validate:
1. Type hierarchy definitions
2. EntityTypeMapper functionality
3. Type mapping accuracy
4. Custom hierarchy support
"""

import pytest

from tests.benchmarks.entity_type_mapper import (
    EntityTypeMapper,
    create_mapper,
)
from tests.benchmarks.type_hierarchy import (
    LIGHTRAG_TYPES,
    get_all_fewnerd_types,
    get_fine_grained_category,
    map_to_lightrag,
)


class TestTypeHierarchy:
    """Tests for type hierarchy definitions."""

    def test_fewnerd_type_count(self):
        """Verify all 66 Few-NERD types are defined."""
        all_types = get_all_fewnerd_types()
        assert len(all_types) == 66, f"Expected 66 types, got {len(all_types)}"

    def test_fewnerd_categories(self):
        """Verify Few-NERD has expected categories."""
        from tests.benchmarks.type_hierarchy import FEWNERD_HIERARCHY

        expected_categories = [
            "person",
            "organization",
            "location",
            "building",
            "event",
            "product",
            "art",
            "other",
        ]
        actual_categories = list(FEWNERD_HIERARCHY.keys())

        for cat in expected_categories:
            assert cat in actual_categories, f"Missing category: {cat}"

    def test_category_mapping(self):
        """Verify types map to correct categories."""
        test_cases = [
            ("person-actor", "person"),
            ("organization-company", "organization"),
            ("location-GPE", "location"),
            ("event-sportsevent", "event"),
        ]

        for entity_type, expected_category in test_cases:
            category = get_fine_grained_category(entity_type, "fewnerd")
            assert (
                category == expected_category
            ), f"{entity_type} should be in {expected_category}"

    def test_unknown_type_mapping(self):
        """Unknown types should map to 'Other'."""
        result = map_to_lightrag("unknown-type", "fewnerd")
        assert result == "Other"


class TestEntityTypeMapper:
    """Tests for EntityTypeMapper class."""

    def test_simple_mapping(self):
        """Test simple type mapping."""
        mapper = EntityTypeMapper(preserve_original=False)

        assert mapper.map_to_lightrag("person-actor", "fewnerd") == "Person"
        assert (
            mapper.map_to_lightrag("organization-company", "fewnerd") == "Organization"
        )
        assert mapper.map_to_lightrag("location-GPE", "fewnerd") == "Location"

    def test_mapping_with_metadata(self):
        """Test mapping with full metadata."""
        mapper = EntityTypeMapper(preserve_original=True)

        metadata = mapper.map_with_metadata("person-athlete", "fewnerd")

        assert metadata["lightrag_type"] == "Person"
        assert metadata["category"] == "person"
        assert metadata["fine_grained"] == "person-athlete"
        assert metadata["benchmark"] == "fewnerd"
        assert metadata["original_type"] == "person-athlete"

    def test_preserve_original_flag(self):
        """Test that preserve_original flag works correctly."""
        # With preserve_original=True
        mapper_with = EntityTypeMapper(preserve_original=True)
        metadata = mapper_with.map_with_metadata("person-actor", "fewnerd")
        assert "original_type" in metadata

        # With preserve_original=False
        mapper_without = EntityTypeMapper(preserve_original=False)
        metadata = mapper_without.map_with_metadata("person-actor", "fewnerd")
        assert "original_type" not in metadata

    def test_map_entities(self):
        """Test batch entity mapping."""
        mapper = EntityTypeMapper(preserve_original=True)

        entities = [
            {"name": "Steve Jobs", "type": "person-actor"},
            {"name": "Apple Inc.", "type": "organization-company"},
            {"name": "Cupertino", "type": "location-GPE"},
        ]

        mapped = mapper.map_entities(entities, "fewnerd")

        assert len(mapped) == 3
        assert mapped[0]["type"] == "Person"
        assert mapped[1]["type"] == "Organization"
        assert mapped[2]["type"] == "Location"

        # Verify metadata is preserved
        assert "_type_mapping" in mapped[0]
        assert mapped[0]["_type_mapping"]["fine_grained"] == "person-actor"

    def test_get_hierarchy(self):
        """Test hierarchy retrieval."""
        mapper = EntityTypeMapper()

        hierarchy = mapper.get_hierarchy(benchmark="fewnerd")

        assert "person" in hierarchy
        assert "organization" in hierarchy
        assert len(hierarchy["person"]["children"]) == 8

    def test_get_fine_grained_types(self):
        """Test getting fine-grained types."""
        mapper = EntityTypeMapper()

        person_types = mapper.get_fine_grained_types("person", "fewnerd")
        assert "person-actor" in person_types
        assert "person-athlete" in person_types
        assert len(person_types) == 8

    def test_get_category_stats(self):
        """Test category statistics."""
        mapper = EntityTypeMapper()

        stats = mapper.get_category_stats("fewnerd")

        assert stats["person"] == 8
        assert stats["organization"] == 10
        assert stats["location"] == 7

    def test_custom_hierarchy(self):
        """Test adding custom hierarchy."""
        mapper = EntityTypeMapper()

        mapper.add_custom_hierarchy(
            "custom_type",
            ["custom-subtype1", "custom-subtype2"],
            {"custom-subtype1": "Person", "custom-subtype2": "Organization"},
        )

        hierarchy = mapper.get_hierarchy(benchmark="custom")
        assert "custom_type" in hierarchy
        assert len(hierarchy["custom_type"]["children"]) == 2

    def test_custom_mapping(self):
        """Test adding custom type mapping."""
        mapper = EntityTypeMapper()

        # Override default mapping
        mapper.add_custom_mapping("fewnerd", "person-actor", "Organization")

        # Verify override works
        assert mapper.map_to_lightrag("person-actor", "fewnerd") == "Organization"
        # Verify other mappings still work
        assert mapper.map_to_lightrag("person-athlete", "fewnerd") == "Person"

    def test_is_lightrag_type(self):
        """Test LightRAG type detection."""
        mapper = EntityTypeMapper()

        assert mapper.is_lightrag_type("Person")
        assert mapper.is_lightrag_type("Organization")
        assert mapper.is_lightrag_type("Location")
        assert not mapper.is_lightrag_type("person-actor")
        assert not mapper.is_lightrag_type("unknown-type")

    def test_hierarchy_filter_by_lightrag_type(self):
        """Test hierarchy filtering by LightRAG type."""
        mapper = EntityTypeMapper()

        # Get all categories that map to "Person"
        person_hierarchy = mapper.get_hierarchy(
            lightrag_type="Person", benchmark="fewnerd"
        )

        # Should include 'person' category
        assert "person" in person_hierarchy


class TestFactoryFunction:
    """Tests for create_mapper factory function."""

    def test_create_mapper_default(self):
        """Test default mapper creation."""
        mapper = create_mapper()
        assert isinstance(mapper, EntityTypeMapper)
        assert mapper.preserve_original is True

    def test_create_mapper_custom(self):
        """Test mapper creation with custom settings."""
        mapper = create_mapper(preserve_original=False)
        assert mapper.preserve_original is False


class TestIntegration:
    """Integration tests with actual data."""

    def test_fewnerd_subset_mapping(self):
        """Test mapping Few-NERD subset data."""
        from tests.benchmarks.entity_type_mapper import create_mapper
        from tests.benchmarks.fewnerd.full_dataset import get_fewnerd_full_dataset

        mapper = create_mapper()
        dataset = get_fewnerd_full_dataset()

        for case in dataset[:5]:  # Test first 5 cases
            mapped = mapper.map_entities(case["entities"], "fewnerd")

            # All entities should have valid LightRAG types
            for entity in mapped:
                # Some types may map to "Other" if not in our mapping
                assert entity["type"] in LIGHTRAG_TYPES or entity["type"] == "Other"
                assert "_type_mapping" in entity
                assert "fine_grained" in entity["_type_mapping"]

    def test_text2kgbench_mapping(self):
        """Test mapping Text2KGBench data."""
        from tests.benchmarks.entity_type_mapper import create_mapper
        from tests.benchmarks.text2kgbench.full_dataset import (
            get_text2kgbench_full_dataset,
        )

        mapper = create_mapper()
        dataset = get_text2kgbench_full_dataset()

        for case in dataset[:5]:  # Test first 5 cases
            mapped = mapper.map_entities(case["entities"], "text2kgbench")

            # All entities should have valid LightRAG types
            for entity in mapped:
                # Some types may map to "Other" if not in our mapping
                assert entity["type"] in LIGHTRAG_TYPES or entity["type"] == "Other"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
