# Entity Type Mapping Guide

## Overview
This document describes the mapping between academic benchmark entity types and LightRAG's 11 entity types.

**Issue**: lightrag-4om (P0: Test Review & Academic Benchmarks)

---

## LightRAG Entity Types (11 types)

```
1. Person
2. Creature
3. Organization
4. Location
5. Event
6. Concept
7. Method
8. Content
9. Data
10. Artifact
11. NaturalObject
```

---

## Few-NERD → LightRAG Mapping

### Few-NERD Entity Types (66 types)

| Few-NERD Type | LightRAG Type | Notes |
|---------------|---------------|-------|
| PERSON | Person | Direct mapping |
| ORGANIZATION | Organization | Direct mapping |
| LOCATION | Location | Direct mapping |
| ARTIFACT | Artifact | Direct mapping |
| EVENT | Event | Direct mapping |
| WORK | Content | Writing, art, music |
| PRODUCT | Artifact | Manufactured goods |
| LIVING_THING | Creature | Animals, plants |
| NATURAL_PHENOMENON | NaturalObject | Weather, disasters |
| MEDICAL | Other | No direct match |
| FOOD | Other | No direct match |
| VEHICLE | Artifact | Transportation |
| SPORTS | Event | Athletic events |
| LANGUAGE | Concept | Communication |
| CULTURAL | Concept | Traditions, customs |
| DISEASE | Other | No direct match |
| ... | ... | 66 total types |

### Current Mapping (11 → 4 covered)

```python
FEWNERD_TO_LIGHTRAG = {
    "Person": "Person",
    "Organization": "Organization",
    "Location": "Location",
    "Artifact": "Artifact",
    "Concept": "Concept",
    "Event": "Event",
    "Method": "Method",
    "Product": "Artifact",
    "Work": "Content",
    "Natural Phenomenon": "NaturalObject",
    # All others → "Other"
}
```

### Unmapped Types (Need Future Investigation)

| Few-NERD Type | Suggested LightRAG Type | Priority |
|---------------|------------------------|----------|
| MEDICAL | Content | P3 |
| FOOD | Other | P3 |
| DISEASE | Other | P3 |
| PLANT | Creature | P3 |
| FOOD | Other | P3 |

---

## Text2KGBench → LightRAG Mapping

### Text2KGBench Entity Types

Text2KGBench uses Wikidata-based ontology. Common mappings:

| Text2KGBench Type | LightRAG Type | Example |
|-------------------|---------------|---------|
| Person | Person | Barack Obama |
| Organization | Organization | Google |
| Location | Location | California |
| Work | Content | Books, movies |
| Event | Event | Awards, elections |
| Artifact | Artifact | Products, tools |
| Concept | Concept | Theories, ideas |

---

## CoNLL 2003 → LightRAG Mapping

| CoNLL Type | LightRAG Type |
|------------|---------------|
| PER | Person |
| LOC | Location |
| ORG | Organization |
| MISC | Other |

---

## Mapping Function

```python
def map_entity_type(
    benchmark_type: str,
    benchmark_name: str = "fewnerd"
) -> str:
    """Map benchmark entity type to LightRAG type."""
    if benchmark_name == "fewnerd":
        mapping = FEWNERD_TO_LIGHTRAG
    elif benchmark_name == "text2kgbench":
        mapping = TEXT2KGBENCH_TO_LIGHTRAG
    elif benchmark_name == "conll2003":
        mapping = CONLL_TO_LIGHTRAG
    else:
        return "Other"

    return mapping.get(benchmark_type, "Other")
```

---

## Future Work: Fine-Grained Mapping

**Issue**: (Future P2) Add support for fine-grained entity types without losing information.

### Proposed Approach

1. **Preserve Original Type**: Store original benchmark type in entity metadata
2. **Add Mapping Layer**: Create flexible mapping system
3. **Type Hierarchy**: Support hierarchical type relationships
4. **Custom Mappings**: Allow user-defined type mappings

### Example Implementation

```python
class EntityTypeMapper:
    """Flexible entity type mapper with hierarchy support."""

    def __init__(self, mapping_file: str = None):
        self.primary_mapping = FEWNERD_TO_LIGHTRAG
        self.fine_grained_mapping = {}
        self.hierarchy = {
            "Person": ["Person", "Character"],
            "Organization": ["Organization", "Institution", "Company"],
        }

    def map_to_lightrag(
        self,
        entity_type: str,
        preserve_fine_grained: bool = False
    ) -> dict:
        """Map entity type with optional fine-grained preservation."""
        lr_type = self.primary_mapping.get(entity_type, "Other")

        result = {"lightrag_type": lr_type}

        if preserve_fine_grained:
            result["original_type"] = entity_type
            result["fine_grained"] = self.fine_grained_mapping.get(
                entity_type, entity_type
            )

        return result
```

---

## Recommendations

1. **Current**: Use simple 11-type mapping (lossy but simple)
2. **Future**: Add fine-grained mapping layer for research-grade evaluation
3. **User Config**: Allow custom type mappings via configuration

---

*Generated: 2026-01-30*
*Part of: lightrag-4om (P0: Test Review & Academic Benchmarks)*
