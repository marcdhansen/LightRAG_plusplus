# Fine-Grained Entity Type Mapping Guide

## Overview
This document describes the enhanced entity type mapping system that supports hierarchical types with 66 fine-grained types mapped to LightRAG's 11 primary types.

**Issue**: lightrag-zna (P2: Fine-grained Entity Type Mapping)

---

## Architecture

### Three-Level Type System

```
Level 1: Fine-Grained (66 types)
    ↓
Level 2: Category (8 categories)
    ↓
Level 3: LightRAG Primary (11 types)
```

### Example Hierarchy

```
person (category)
├── person-actor ─────→ Person
├── person-artist/author → Person
├── person-athlete ────→ Person
├── person-director ───→ Person
├── person-other ──────→ Person
├── person-politician ─→ Person
├── person-scholar ────→ Person
└── person-soldier ────→ Person

organization (category)
├── organization-company ─────────→ Organization
├── organization-education ──────→ Organization
├── organization-government/...  → Organization
└── ... (7 more)
```

---

## Usage

### Simple Type Mapping

```python
from tests.benchmarks.entity_type_mapper import EntityTypeMapper

mapper = EntityTypeMapper()

# Map fine-grained type to LightRAG type
lr_type = mapper.map_to_lightrag("person-actor", "fewnerd")
# Returns: "Person"
```

### Mapping with Metadata

```python
metadata = mapper.map_with_metadata("person-actor", "fewnerd")
# Returns:
# {
#     "lightrag_type": "Person",
#     "category": "person",
#     "fine_grained": "person-actor",
#     "benchmark": "fewnerd",
#     "original_type": "person-actor"
# }
```

### Batch Entity Mapping

```python
entities = [
    {"name": "Steve Jobs", "type": "person-actor"},
    {"name": "Apple Inc.", "type": "organization-company"},
]

mapped = mapper.map_entities(entities, "fewnerd")
# Each entity now has:
# {
#     "name": "Steve Jobs",
#     "type": "Person",
#     "_type_mapping": {
#         "category": "person",
#         "fine_grained": "person-actor"
#     }
# }
```

---

## Few-NERD Type Hierarchy (66 types)

| Category | Types | LightRAG Mapping |
|----------|-------|------------------|
| person | 8 | Person |
| organization | 10 | Organization |
| location | 7 | Location |
| building | 8 | Location |
| event | 6 | Event |
| product | 9 | Artifact/Content |
| art | 6 | Content |
| other | 12 | Other/Creature/Data |

### Complete Type List

**Person (8 types)**
```
person-actor, person-artist/author, person-athlete, person-director,
person-other, person-politician, person-scholar, person-soldier
```

**Organization (10 types)**
```
organization-company, organization-education, organization-government/governmentagency,
organization-media/newspaper, organization-other, organization-politicalparty,
organization-religion, organization-showorganization,
organization-sportsleague, organization-sportsteam
```

**Location (7 types)**
```
location-bodiesofwater, location-GPE, location-island, location-mountain,
location-other, location-park, location-road/railway/highway/transit
```

**Building (8 types)**
```
building-airport, building-hospital, building-hotel, building-library,
building-other, building-restaurant, building-sportsfacility, building-theater
```

**Event (6 types)**
```
event-attack/battle/war/militaryconflict, event-disaster, event-election,
event-other, event-protest, event-sportsevent
```

**Product (9 types)**
```
product-airplane, product-car, product-food, product-game, product-other,
product-ship, product-software, product-train, product-weapon
```

**Art (6 types)**
```
art-broadcastprogram, art-film, art-music, art-other, art-painting, art-writtenart
```

**Other (12 types)**
```
other-astronomything, other-award, other-biologything, other-chemicalthing,
other-currency, other-disease, other-educationaldegree, other-god,
other-language, other-law, other-livingthing, other-medical
```

---

## Custom Hierarchies

### Adding Custom Types

```python
mapper.add_custom_hierarchy(
    "custom_type",
    ["custom-subtype1", "custom-subtype2"],
    {"custom-subtype1": "Person", "custom-subtype2": "Organization"}
)
```

### Overriding Default Mappings

```python
mapper.add_custom_mapping("fewnerd", "person-actor", "Organization")
```

---

## API Reference

### EntityTypeMapper Methods

| Method | Description |
|--------|-------------|
| `map_to_lightrag(type, benchmark)` | Map fine-grained type to LightRAG type |
| `map_with_metadata(type, benchmark)` | Map with full metadata |
| `map_entities(entities, benchmark)` | Batch map entity list |
| `get_hierarchy(lightrag_type, benchmark)` | Get type hierarchy |
| `get_fine_grained_types(category, benchmark)` | Get types by category |
| `get_category_stats(benchmark)` | Get category statistics |
| `add_custom_hierarchy(...)` | Add custom type hierarchy |
| `add_custom_mapping(...)` | Override default mapping |
| `is_lightrag_type(type)` | Check if type is LightRAG primary |

---

## Files

| File | Description |
|------|-------------|
| `tests/benchmarks/type_hierarchy.py` | Type hierarchy definitions |
| `tests/benchmarks/entity_type_mapper.py` | Flexible mapper class |
| `tests/test_fine_grained_mapping.py` | Test suite |

---

*Generated: 2026-01-30*
*Part of: lightrag-zna (Fine-grained Entity Type Mapping)*
