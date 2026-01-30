"""
Flexible Entity Type Mapper.

This module provides the EntityTypeMapper class for flexible type mapping
between academic benchmarks and LightRAG's primary types.

Features:
- Hierarchical type mapping (fine-grained -> category -> primary)
- Preserve original benchmark types in metadata
- Custom hierarchy support via configuration
- Backward compatibility with existing code
"""

from typing import Any
from tests.benchmarks.type_hierarchy import (
    FEWNERD_TO_LIGHTRAG,
    TEXT2KGBENCH_TO_LIGHTRAG,
    FEWNERD_HIERARCHY,
    TEXT2KGBENCH_HIERARCHY,
    get_fine_grained_category,
    get_all_fewnerd_types,
    LIGHTRAG_TYPES,
)


class EntityTypeMapper:
    """Flexible entity type mapper with hierarchy support.

    Usage:
        mapper = EntityTypeMapper()

        # Simple mapping
        lr_type = mapper.map_to_lightrag("person-actor", "fewnerd")
        # Returns: "Person"

        # Mapping with metadata
        metadata = mapper.map_with_metadata("person-actor", "fewnerd")
        # Returns: {"lightrag_type": "Person", "category": "person", "fine_grained": "person-actor", ...}

        # Custom hierarchy
        mapper.add_custom_hierarchy("my_type", ["subtype1", "subtype2"])
    """

    def __init__(self, preserve_original: bool = True):
        """Initialize the mapper.

        Args:
            preserve_original: If True, preserve original benchmark types in metadata
        """
        self.preserve_original = preserve_original
        self.custom_hierarchies: dict[str, dict[str, Any]] = {}
        self.custom_mappings: dict[str, dict[str, str]] = {}

    def map_to_lightrag(self, entity_type: str, benchmark: str = "fewnerd") -> str:
        """Map an entity type to LightRAG primary type.

        Args:
            entity_type: The fine-grained entity type (e.g., "person-actor")
            benchmark: The benchmark source ("fewnerd" or "text2kgbench")

        Returns:
            The mapped LightRAG primary type (e.g., "Person")
        """
        # Check custom mappings first
        key = f"{benchmark}:{entity_type}"
        if key in self.custom_mappings:
            return self.custom_mappings[key].get("lightrag", "Other")

        # Use standard mappings
        if benchmark == "fewnerd":
            return FEWNERD_TO_LIGHTRAG.get(entity_type, "Other")
        elif benchmark == "text2kgbench":
            return TEXT2KGBENCH_TO_LIGHTRAG.get(entity_type, "Other")
        return "Other"

    def map_with_metadata(
        self, entity_type: str, benchmark: str = "fewnerd"
    ) -> dict[str, Any]:
        """Map an entity type with full metadata.

        Args:
            entity_type: The fine-grained entity type
            benchmark: The benchmark source

        Returns:
            Dict containing:
                - lightrag_type: Primary LightRAG type
                - category: Parent category (if available)
                - fine_grained: Original fine-grained type
                - benchmark: Source benchmark
                - original_type: Original type (if preserve_original=True)
        """
        lightrag_type = self.map_to_lightrag(entity_type, benchmark)
        category = get_fine_grained_category(entity_type, benchmark)

        result = {
            "lightrag_type": lightrag_type,
            "category": category,
            "fine_grained": entity_type,
            "benchmark": benchmark,
        }

        if self.preserve_original:
            result["original_type"] = entity_type

        return result

    def map_entities(
        self, entities: list[dict], benchmark: str = "fewnerd"
    ) -> list[dict]:
        """Map a list of entities to LightRAG format.

        Args:
            entities: List of entity dicts with "name" and "type" keys
            benchmark: The benchmark source

        Returns:
            List of entities with mapped types and preserved metadata
        """
        mapped = []
        for entity in entities:
            entity_type = entity.get("type", "Other")
            mapping = self.map_with_metadata(entity_type, benchmark)

            mapped_entity = {
                "name": entity.get("name", "Unknown"),
                "type": mapping["lightrag_type"],
                "description": entity.get("description", ""),
                "_type_mapping": {
                    "category": mapping.get("category"),
                    "fine_grained": mapping.get("fine_grained"),
                    "benchmark": benchmark,
                },
            }

            if self.preserve_original:
                mapped_entity["_type_mapping"]["original_type"] = mapping.get(
                    "original_type"
                )

            mapped.append(mapped_entity)

        return mapped

    def get_hierarchy(
        self, lightrag_type: str = None, benchmark: str = "fewnerd"
    ) -> dict[str, Any]:
        """Get type hierarchy for a LightRAG type or all types.

        Args:
            lightrag_type: Optional LightRAG type to get hierarchy for
            benchmark: The benchmark source

        Returns:
            Dict mapping categories to their fine-grained types
        """
        if benchmark == "fewnerd":
            base_hierarchy = FEWNERD_HIERARCHY.copy()
        elif benchmark == "text2kgbench":
            base_hierarchy = TEXT2KGBENCH_HIERARCHY.copy()
        else:
            base_hierarchy = {}

        # Add custom hierarchies
        base_hierarchy.update(self.custom_hierarchies)

        # Filter by LightRAG type if specified
        if lightrag_type:
            filtered = {}
            for category, data in base_hierarchy.items():
                # Check if this category maps to the LightRAG type
                for child in data["children"]:
                    if self.map_to_lightrag(child, benchmark) == lightrag_type:
                        filtered[category] = data
                        break
            return filtered

        return base_hierarchy

    def get_fine_grained_types(
        self, category: str = None, benchmark: str = "fewnerd"
    ) -> list[str]:
        """Get all fine-grained types, optionally filtered by category.

        Args:
            category: Optional category to filter by
            benchmark: The benchmark source

        Returns:
            List of fine-grained entity types
        """
        if benchmark == "fewnerd":
            if category:
                return FEWNERD_HIERARCHY.get(category, {}).get("children", [])
            return get_all_fewnerd_types()
        elif benchmark == "text2kgbench":
            if category:
                return TEXT2KGBENCH_HIERARCHY.get(category, {}).get("children", [])
            all_types = []
            for data in TEXT2KGBENCH_HIERARCHY.values():
                all_types.extend(data["children"])
            return all_types
        return []

    def add_custom_hierarchy(
        self,
        category: str,
        children: list[str],
        lightrag_mapping: dict[str, str] = None,
    ):
        """Add a custom type hierarchy.

        Args:
            category: The category name (e.g., "custom_type")
            children: List of fine-grained types in this category
            lightrag_mapping: Dict mapping each child to LightRAG type
        """
        self.custom_hierarchies[category] = {
            "children": children,
            "custom": True,
        }

        if lightrag_mapping:
            for child, lr_type in lightrag_mapping.items():
                key = f"custom:{child}"
                self.custom_mappings[key] = {"lightrag": lr_type}

    def add_custom_mapping(self, benchmark: str, entity_type: str, lightrag_type: str):
        """Add a custom type mapping override.

        Args:
            benchmark: The benchmark source
            entity_type: The entity type to remap
            lightrag_type: The LightRAG type to map to
        """
        key = f"{benchmark}:{entity_type}"
        self.custom_mappings[key] = {"lightrag": lightrag_type}

    def is_lightrag_type(self, entity_type: str) -> bool:
        """Check if a type is a LightRAG primary type.

        Args:
            entity_type: The type to check

        Returns:
            True if it's a LightRAG primary type
        """
        return entity_type in LIGHTRAG_TYPES

    def get_category_stats(self, benchmark: str = "fewnerd") -> dict[str, int]:
        """Get statistics about type categories.

        Args:
            benchmark: The benchmark source

        Returns:
            Dict mapping categories to their type counts
        """
        hierarchy = self.get_hierarchy(benchmark=benchmark)
        stats = {}
        for category, data in hierarchy.items():
            stats[category] = len(data["children"])
        return stats


def create_mapper(preserve_original: bool = True) -> EntityTypeMapper:
    """Factory function to create a configured mapper.

    Args:
        preserve_original: If True, preserve original types in metadata

    Returns:
        Configured EntityTypeMapper instance
    """
    return EntityTypeMapper(preserve_original=preserve_original)


if __name__ == "__main__":
    # Demo usage
    mapper = EntityTypeMapper(preserve_original=True)

    print("=" * 60)
    print("EntityTypeMapper Demo")
    print("=" * 60)

    # Simple mapping
    print("\n1. Simple mapping:")
    lr_type = mapper.map_to_lightrag("person-actor", "fewnerd")
    print(f"   person-actor -> {lr_type}")

    lr_type = mapper.map_to_lightrag("organization-company", "fewnerd")
    print(f"   organization-company -> {lr_type}")

    # Mapping with metadata
    print("\n2. Mapping with metadata:")
    metadata = mapper.map_with_metadata("person-athlete", "fewnerd")
    for key, value in metadata.items():
        print(f"   {key}: {value}")

    # Hierarchy
    print("\n3. Category statistics:")
    stats = mapper.get_category_stats("fewnerd")
    for category, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"   {category}: {count} types")

    # Custom hierarchy
    print("\n4. Custom hierarchy:")
    mapper.add_custom_hierarchy(
        "custom_type",
        ["custom-subtype1", "custom-subtype2"],
        {"custom-subtype1": "Person", "custom-subtype2": "Organization"},
    )
    hierarchy = mapper.get_hierarchy(benchmark="custom")
    print(
        f"   Added custom hierarchy with {len(hierarchy.get('custom_type', {}).get('children', []))} types"
    )

    print("\n" + "=" * 60)
