"""
Type hierarchy definitions for academic benchmarks.

This module defines hierarchical type mappings for:
- Few-NERD: 66 fine-grained types organized into hierarchies
- Text2KGBench: Wikidata-based ontology types
- LightRAG: 11 primary types

The hierarchy allows:
- Mapping fine-grained types to primary types
- Preserving original type information
- Flexible remapping between benchmarks
"""

from typing import Any

# ============================================================================
# Few-NERD Type Hierarchy
# ============================================================================

# Few-NERD has 66 entity types organized into 10 coarse categories
# https://github.com/thunlp/Few-NERD

FEWNERD_HIERARCHY = {
    # Person types (8)
    "person": {
        "children": [
            "person-actor",
            "person-artist/author",
            "person-athlete",
            "person-director",
            "person-other",
            "person-politician",
            "person-scholar",
            "person-soldier",
        ],
        "description": "Human individuals",
    },
    # Organization types (10)
    "organization": {
        "children": [
            "organization-company",
            "organization-education",
            "organization-government/governmentagency",
            "organization-media/newspaper",
            "organization-other",
            "organization-politicalparty",
            "organization-religion",
            "organization-showorganization",
            "organization-sportsleague",
            "organization-sportsteam",
        ],
        "description": "Organizations and institutions",
    },
    # Location types (7)
    "location": {
        "children": [
            "location-bodiesofwater",
            "location-GPE",
            "location-island",
            "location-mountain",
            "location-other",
            "location-park",
            "location-road/railway/highway/transit",
        ],
        "description": "Geographic locations",
    },
    # Building types (7)
    "building": {
        "children": [
            "building-airport",
            "building-hospital",
            "building-hotel",
            "building-library",
            "building-other",
            "building-restaurant",
            "building-sportsfacility",
            "building-theater",
        ],
        "description": "Buildings and structures",
    },
    # Event types (6)
    "event": {
        "children": [
            "event-attack/battle/war/militaryconflict",
            "event-disaster",
            "event-election",
            "event-other",
            "event-protest",
            "event-sportsevent",
        ],
        "description": "Events and occurrences",
    },
    # Product/Artifact types (10)
    "product": {
        "children": [
            "product-airplane",
            "product-car",
            "product-food",
            "product-game",
            "product-other",
            "product-ship",
            "product-software",
            "product-train",
            "product-weapon",
        ],
        "description": "Products and artifacts",
    },
    # Art types (6)
    "art": {
        "children": [
            "art-broadcastprogram",
            "art-film",
            "art-music",
            "art-other",
            "art-painting",
            "art-writtenart",
        ],
        "description": "Artistic works",
    },
    # Other types (12)
    "other": {
        "children": [
            "other-astronomything",
            "other-award",
            "other-biologything",
            "other-chemicalthing",
            "other-currency",
            "other-disease",
            "other-educationaldegree",
            "other-god",
            "other-language",
            "other-law",
            "other-livingthing",
            "other-medical",
        ],
        "description": "Miscellaneous types",
    },
}


def get_fewnerd_types() -> dict[str, list[str]]:
    """Get all Few-NERD types organized by category."""
    result = {}
    for category, data in FEWNERD_HIERARCHY.items():
        result[category] = data["children"]
    return result


def get_all_fewnerd_types() -> list[str]:
    """Get all 66 Few-NERD types as a flat list."""
    all_types = []
    for category_data in FEWNERD_HIERARCHY.values():
        all_types.extend(category_data["children"])
    return all_types


# ============================================================================
# Text2KGBench Type Hierarchy
# ============================================================================

TEXT2KGBENCH_HIERARCHY = {
    "Person": {
        "children": ["Person"],
        "description": "Human individuals",
    },
    "Organization": {
        "children": [
            "Company",
            "EducationalInstitution",
            "GovernmentAgency",
            "MediaOrganization",
            "NonProfitOrganization",
            "SportsTeam",
        ],
        "description": "Organizations",
    },
    "Location": {
        "children": [
            "City",
            "Country",
            "Continent",
            "Mountain",
            "River",
            "Region",
            "Planet",
        ],
        "description": "Geographic locations",
    },
    "Event": {
        "children": [
            "SportsCompetition",
            "Award Ceremony",
            "Conference",
            "PoliticalEvent",
            "NaturalEvent",
        ],
        "description": "Events",
    },
    "Artifact": {
        "children": [
            "Aircraft",
            "Vehicle",
            "ElectronicDevice",
            "Software",
            "PublishedWork",
        ],
        "description": "Man-made artifacts",
    },
    "Concept": {
        "children": [
            "ScientificTheory",
            "ProgrammingLanguage",
            "ArtMovement",
            "FieldOfStudy",
            "Award",
        ],
        "description": "Abstract concepts",
    },
    "Data": {
        "children": [
            "Year",
            "Number",
            "Currency",
            "Percentage",
            "TimePeriod",
        ],
        "description": "Data values",
    },
}


def get_text2kgbench_types() -> dict[str, list[str]]:
    """Get all Text2KGBench types organized by category."""
    result = {}
    for category, data in TEXT2KGBENCH_HIERARCHY.items():
        result[category] = data["children"]
    return result


# ============================================================================
# LightRAG Type Hierarchy (11 primary types)
# ============================================================================

LIGHTRAG_TYPES = [
    "Person",
    "Creature",
    "Organization",
    "Location",
    "Event",
    "Concept",
    "Method",
    "Content",
    "Data",
    "Artifact",
    "NaturalObject",
]


# ============================================================================
# Benchmark to LightRAG Mapping
# ============================================================================

# Few-NERD -> LightRAG (simple mapping)
FEWNERD_TO_LIGHTRAG = {
    # Person
    "person-actor": "Person",
    "person-artist/author": "Person",
    "person-athlete": "Person",
    "person-director": "Person",
    "person-other": "Person",
    "person-politician": "Person",
    "person-scholar": "Person",
    "person-soldier": "Person",
    # Organization
    "organization-company": "Organization",
    "organization-education": "Organization",
    "organization-government/governmentagency": "Organization",
    "organization-media/newspaper": "Organization",
    "organization-other": "Organization",
    "organization-politicalparty": "Organization",
    "organization-religion": "Organization",
    "organization-showorganization": "Organization",
    "organization-sportsleague": "Organization",
    "organization-sportsteam": "Organization",
    # Location
    "location-bodiesofwater": "Location",
    "location-GPE": "Location",
    "location-island": "Location",
    "location-mountain": "Location",
    "location-other": "Location",
    "location-park": "Location",
    "location-road/railway/highway/transit": "Location",
    # Building -> Location
    "building-airport": "Location",
    "building-hospital": "Location",
    "building-hotel": "Location",
    "building-library": "Location",
    "building-other": "Location",
    "building-restaurant": "Location",
    "building-sportsfacility": "Location",
    "building-theater": "Location",
    # Event
    "event-attack/battle/war/militaryconflict": "Event",
    "event-disaster": "Event",
    "event-election": "Event",
    "event-other": "Event",
    "event-protest": "Event",
    "event-sportsevent": "Event",
    # Product -> Artifact
    "product-airplane": "Artifact",
    "product-car": "Artifact",
    "product-food": "Content",
    "product-game": "Content",
    "product-other": "Artifact",
    "product-ship": "Artifact",
    "product-software": "Artifact",
    "product-train": "Artifact",
    "product-weapon": "Artifact",
    # Art -> Content
    "art-broadcastprogram": "Content",
    "art-film": "Content",
    "art-music": "Content",
    "art-other": "Content",
    "art-painting": "Content",
    "art-writtenart": "Content",
    # Other
    "other-astronomything": "NaturalObject",
    "other-award": "Data",
    "other-biologything": "Creature",
    "other-chemicalthing": "Data",
    "other-currency": "Data",
    "other-disease": "Data",
    "other-educationaldegree": "Data",
    "other-god": "Concept",
    "other-language": "Concept",
    "other-law": "Data",
    "other-livingthing": "Creature",
    "other-medical": "Data",
}


# Text2KGBench -> LightRAG
TEXT2KGBENCH_TO_LIGHTRAG = {
    "Person": "Person",
    "Company": "Organization",
    "EducationalInstitution": "Organization",
    "GovernmentAgency": "Organization",
    "MediaOrganization": "Organization",
    "NonProfitOrganization": "Organization",
    "SportsTeam": "Organization",
    "City": "Location",
    "Country": "Location",
    "Continent": "Location",
    "Mountain": "Location",
    "River": "Location",
    "Region": "Location",
    "Planet": "Location",
    "SportsCompetition": "Event",
    "Award Ceremony": "Event",
    "Conference": "Event",
    "PoliticalEvent": "Event",
    "NaturalEvent": "Event",
    "Aircraft": "Artifact",
    "Vehicle": "Artifact",
    "ElectronicDevice": "Artifact",
    "Software": "Artifact",
    "PublishedWork": "Content",
    "ScientificTheory": "Concept",
    "ProgrammingLanguage": "Concept",
    "ArtMovement": "Concept",
    "FieldOfStudy": "Concept",
    "Award": "Data",
    "Year": "Data",
    "Number": "Data",
    "Currency": "Data",
    "Percentage": "Data",
    "TimePeriod": "Data",
}


def get_fine_grained_category(fine_type: str, benchmark: str = "fewnerd") -> str | None:
    """Get the category (parent type) for a fine-grained type."""
    if benchmark == "fewnerd":
        hierarchy = FEWNERD_HIERARCHY
    elif benchmark == "text2kgbench":
        hierarchy = TEXT2KGBENCH_HIERARCHY
    else:
        return None

    for category, data in hierarchy.items():
        if fine_type in data["children"]:
            return category
    return None


def map_to_lightrag(fine_type: str, benchmark: str = "fewnerd") -> str:
    """Map a fine-grained type to LightRAG primary type."""
    if benchmark == "fewnerd":
        return FEWNERD_TO_LIGHTRAG.get(fine_type, "Other")
    elif benchmark == "text2kgbench":
        return TEXT2KGBENCH_TO_LIGHTRAG.get(fine_type, "Other")
    return "Other"


def map_with_metadata(
    fine_type: str, benchmark: str = "fewnerd", preserve_original: bool = True
) -> dict[str, Any]:
    """Map a fine-grained type with full metadata."""
    primary_type = map_to_lightrag(fine_type, benchmark)
    category = get_fine_grained_category(fine_type, benchmark)

    result = {
        "lightrag_type": primary_type,
        "category": category,
        "fine_grained": fine_type,
    }

    if preserve_original:
        result["original_type"] = fine_type
        result["benchmark"] = benchmark

    return result


if __name__ == "__main__":
    # Print type hierarchy summary
    print("=" * 60)
    print("FEWNERD TYPE HIERARCHY")
    print("=" * 60)

    for category, data in FEWNERD_HIERARCHY.items():
        print(f"\n{category.upper()} ({len(data['children'])} types):")
        for child in data["children"][:5]:
            primary = FEWNERD_TO_LIGHTRAG.get(child, "Other")
            print(f"  {child} -> {primary}")
        if len(data["children"]) > 5:
            print(f"  ... and {len(data['children']) - 5} more")

    print("\n" + "=" * 60)
    print(f"Total Few-NERD types: {len(get_all_fewnerd_types())}")
    print(f"LightRAG types: {len(LIGHTRAG_TYPES)}")
    print("=" * 60)
