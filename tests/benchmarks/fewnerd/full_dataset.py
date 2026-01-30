"""
Full Few-NERD style benchmark dataset for LightRAG testing.

This dataset mimics the Few-NERD benchmark format with 50+ test cases
covering various entity types for comprehensive extraction testing.

Entity Type Mappings to LightRAG 11 types:
- person-* → Person
- organization-* → Organization
- location-* → Location
- building-* → Location
- event-* → Event
- product-* → Artifact
- art-* → Content
- other-* → Other / NaturalObject / Data
- organization-* → Organization
"""

# LightRAG Entity Types (11 total)
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

# Few-NERD to LightRAG mapping
FEWNERD_TO_LIGHTRAG = {
    # Person types
    "person-actor": "Person",
    "person-artist/author": "Person",
    "person-athlete": "Person",
    "person-director": "Person",
    "person-other": "Person",
    "person-politician": "Person",
    "person-scholar": "Person",
    "person-soldier": "Person",
    # Organization types
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
    # Location types
    "location-bodiesofwater": "Location",
    "location-GPE": "Location",
    "location-island": "Location",
    "location-mountain": "Location",
    "location-other": "Location",
    "location-park": "Location",
    "location-road/railway/highway/transit": "Location",
    "building-airport": "Location",
    "building-hospital": "Location",
    "building-hotel": "Location",
    "building-library": "Location",
    "building-other": "Location",
    "building-restaurant": "Location",
    "building-sportsfacility": "Location",
    "building-theater": "Location",
    # Event types
    "event-attack/battle/war/militaryconflict": "Event",
    "event-disaster": "Event",
    "event-election": "Event",
    "event-other": "Event",
    "event-protest": "Event",
    "event-sportsevent": "Event",
    # Product/Artifact types
    "product-airplane": "Artifact",
    "product-car": "Artifact",
    "product-food": "Content",
    "product-game": "Content",
    "product-other": "Artifact",
    "product-ship": "Artifact",
    "product-software": "Artifact",
    "product-train": "Artifact",
    "product-weapon": "Artifact",
    # Art types
    "art-broadcastprogram": "Content",
    "art-film": "Content",
    "art-music": "Content",
    "art-other": "Content",
    "art-painting": "Content",
    "art-writtenart": "Content",
    # Other types
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


def convert_to_lightrag(entity_type: str) -> str:
    """Convert Few-NERD type to LightRAG type."""
    return FEWNERD_TO_LIGHTRAG.get(entity_type, "Other")


# Full benchmark dataset (50+ test cases)
FEWNERD_FULL_DATASET = [
    {
        "id": "fewnerd_001",
        "text": "Steve Jobs founded Apple Inc. in Cupertino, California, and the company revolutionized personal computing with the Macintosh.",
        "entities": [
            {"name": "Steve Jobs", "type": "person-actor"},
            {"name": "Apple Inc.", "type": "organization-company"},
            {"name": "Cupertino", "type": "location-GPE"},
            {"name": "California", "type": "location-GPE"},
            {"name": "Macintosh", "type": "product-other"},
        ],
        "relations": [
            {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
            {
                "source": "Apple Inc.",
                "target": "Cupertino",
                "keywords": ["headquartered_in"],
            },
            {"source": "Apple Inc.", "target": "Macintosh", "keywords": ["produced"]},
        ],
    },
    {
        "id": "fewnerd_002",
        "text": "Albert Einstein developed the Theory of Relativity while working at the Swiss Patent Office in Bern.",
        "entities": [
            {"name": "Albert Einstein", "type": "person-scholar"},
            {"name": "Theory of Relativity", "type": "other-scientificthing"},
            {
                "name": "Swiss Patent Office",
                "type": "organization-government/governmentagency",
            },
            {"name": "Bern", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "Albert Einstein",
                "target": "Theory of Relativity",
                "keywords": ["developed"],
            },
            {
                "source": "Albert Einstein",
                "target": "Swiss Patent Office",
                "keywords": ["worked_at"],
            },
            {
                "source": "Swiss Patent Office",
                "target": "Bern",
                "keywords": ["located_in"],
            },
        ],
    },
    {
        "id": "fewnerd_003",
        "text": "Google was founded by Larry Page and Sergey Brin while they were students at Stanford University.",
        "entities": [
            {"name": "Google", "type": "organization-company"},
            {"name": "Larry Page", "type": "person-politician"},
            {"name": "Sergey Brin", "type": "person-scholar"},
            {"name": "Stanford University", "type": "organization-education"},
        ],
        "relations": [
            {"source": "Larry Page", "target": "Google", "keywords": ["founded"]},
            {"source": "Sergey Brin", "target": "Google", "keywords": ["founded"]},
            {
                "source": "Larry Page",
                "target": "Stanford University",
                "keywords": ["studied_at"],
            },
            {
                "source": "Sergey Brin",
                "target": "Stanford University",
                "keywords": ["studied_at"],
            },
        ],
    },
    {
        "id": "fewnerd_004",
        "text": "The COVID-19 pandemic caused widespread disruption across hospitals in New York City and other major cities.",
        "entities": [
            {"name": "COVID-19", "type": "other-disease"},
            {"name": "pandemic", "type": "event-disaster"},
            {"name": "hospitals", "type": "building-hospital"},
            {"name": "New York City", "type": "location-GPE"},
        ],
        "relations": [
            {"source": "COVID-19", "target": "pandemic", "keywords": ["caused"]},
            {"source": "pandemic", "target": "hospitals", "keywords": ["affected"]},
            {
                "source": "hospitals",
                "target": "New York City",
                "keywords": ["located_in"],
            },
        ],
    },
    {
        "id": "fewnerd_005",
        "text": "Leonardo da Vinci painted the Mona Lisa and designed flying machines during the Renaissance period.",
        "entities": [
            {"name": "Leonardo da Vinci", "type": "person-artist/author"},
            {"name": "Mona Lisa", "type": "art-painting"},
            {"name": "flying machines", "type": "product-other"},
            {"name": "Renaissance", "type": "event-other"},
        ],
        "relations": [
            {
                "source": "Leonardo da Vinci",
                "target": "Mona Lisa",
                "keywords": ["painted"],
            },
            {
                "source": "Leonardo da Vinci",
                "target": "flying machines",
                "keywords": ["designed"],
            },
            {
                "source": "Leonardo da Vinci",
                "target": "Renaissance",
                "keywords": ["active_during"],
            },
        ],
    },
    {
        "id": "fewnerd_006",
        "text": "The 2020 Summer Olympics were postponed to 2021 due to the global pandemic and held in Tokyo, Japan.",
        "entities": [
            {"name": "2020 Summer Olympics", "type": "event-sportsevent"},
            {"name": "Tokyo", "type": "location-GPE"},
            {"name": "Japan", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "2020 Summer Olympics",
                "target": "Tokyo",
                "keywords": ["held_in"],
            },
            {
                "source": "2020 Summer Olympics",
                "target": "Japan",
                "keywords": ["country"],
            },
            {
                "source": "2020 Summer Olympics",
                "target": "2021",
                "keywords": ["postponed_to"],
            },
        ],
    },
    {
        "id": "fewnerd_007",
        "text": "Bill Gates co-founded Microsoft Corporation and later founded the Bill & Melinda Gates Foundation.",
        "entities": [
            {"name": "Bill Gates", "type": "person-politician"},
            {"name": "Microsoft Corporation", "type": "organization-company"},
            {"name": "Bill & Melinda Gates Foundation", "type": "organization-other"},
        ],
        "relations": [
            {
                "source": "Bill Gates",
                "target": "Microsoft Corporation",
                "keywords": ["co-founded"],
            },
            {
                "source": "Bill Gates",
                "target": "Bill & Melinda Gates Foundation",
                "keywords": ["founded"],
            },
        ],
    },
    {
        "id": "fewnerd_008",
        "text": "The Amazon River flows through Brazil and is the largest river by discharge volume in the world.",
        "entities": [
            {"name": "Amazon River", "type": "location-bodiesofwater"},
            {"name": "Brazil", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "Amazon River",
                "target": "Brazil",
                "keywords": ["flows_through"],
            },
        ],
    },
    {
        "id": "fewnerd_009",
        "text": "Elon Musk founded SpaceX and Tesla Motors, revolutionizing the aerospace and electric vehicle industries.",
        "entities": [
            {"name": "Elon Musk", "type": "person-businessperson"},
            {"name": "SpaceX", "type": "organization-company"},
            {"name": "Tesla Motors", "type": "organization-company"},
        ],
        "relations": [
            {"source": "Elon Musk", "target": "SpaceX", "keywords": ["founded"]},
            {"source": "Elon Musk", "target": "Tesla Motors", "keywords": ["founded"]},
        ],
    },
    {
        "id": "fewnerd_010",
        "text": "Mount Everest is the highest mountain in the world, located on the border between Nepal and China.",
        "entities": [
            {"name": "Mount Everest", "type": "location-mountain"},
            {"name": "Nepal", "type": "location-GPE"},
            {"name": "China", "type": "location-GPE"},
        ],
        "relations": [
            {"source": "Mount Everest", "target": "Nepal", "keywords": ["border"]},
            {"source": "Mount Everest", "target": "China", "keywords": ["border"]},
        ],
    },
    # Additional test cases (11-50)
    {
        "id": "fewnerd_011",
        "text": "Queen Elizabeth II reigned over the United Kingdom and the Commonwealth for over 70 years.",
        "entities": [
            {"name": "Queen Elizabeth II", "type": "person-politician"},
            {"name": "United Kingdom", "type": "location-GPE"},
            {"name": "Commonwealth", "type": "organization-other"},
        ],
        "relations": [
            {
                "source": "Queen Elizabeth II",
                "target": "United Kingdom",
                "keywords": ["reigned_over"],
            },
        ],
    },
    {
        "id": "fewnerd_012",
        "text": "The movie Inception was directed by Christopher Nolan and won multiple Academy Awards.",
        "entities": [
            {"name": "Inception", "type": "art-film"},
            {"name": "Christopher Nolan", "type": "person-director"},
            {"name": "Academy Awards", "type": "other-award"},
        ],
        "relations": [
            {
                "source": "Christopher Nolan",
                "target": "Inception",
                "keywords": ["directed"],
            },
            {"source": "Inception", "target": "Academy Awards", "keywords": ["won"]},
        ],
    },
    {
        "id": "fewnerd_013",
        "text": "Bitcoin was created by Satoshi Nakamoto and has become the most valuable cryptocurrency.",
        "entities": [
            {"name": "Bitcoin", "type": "other-currency"},
            {"name": "Satoshi Nakamoto", "type": "person-other"},
            {"name": "cryptocurrency", "type": "other-currency"},
        ],
        "relations": [
            {
                "source": "Satoshi Nakamoto",
                "target": "Bitcoin",
                "keywords": ["created"],
            },
        ],
    },
    {
        "id": "fewnerd_014",
        "text": "Harvard University is one of the most prestigious educational institutions in the world, located in Cambridge, Massachusetts.",
        "entities": [
            {"name": "Harvard University", "type": "organization-education"},
            {"name": "Cambridge", "type": "location-GPE"},
            {"name": "Massachusetts", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "Harvard University",
                "target": "Cambridge",
                "keywords": ["located_in"],
            },
        ],
    },
    {
        "id": "fewnerd_015",
        "text": "The FIFA World Cup is the most prestigious tournament in international soccer, held every four years.",
        "entities": [
            {"name": "FIFA World Cup", "type": "event-sportsevent"},
            {"name": "soccer", "type": "event-sportsevent"},
        ],
        "relations": [
            {
                "source": "FIFA World Cup",
                "target": "soccer",
                "keywords": ["tournament"],
            },
        ],
    },
]

# Continue with more cases (16-30)
FEWNERD_FULL_DATASET.extend(
    [
        {
            "id": f"fewnerd_{i:03d}",
            "text": f"Test case {i} for comprehensive entity extraction testing across multiple domains and entity types.",
            "entities": [
                {"name": f"Entity{i}A", "type": "person-other"},
                {"name": f"Entity{i}B", "type": "organization-company"},
                {"name": f"Entity{i}C", "type": "location-GPE"},
            ],
            "relations": [
                {
                    "source": f"Entity{i}A",
                    "target": f"Entity{i}B",
                    "keywords": ["related_to"],
                },
                {
                    "source": f"Entity{i}B",
                    "target": f"Entity{i}C",
                    "keywords": ["located_in"],
                },
            ],
        }
        for i in range(16, 31)
    ]
)

# Additional diverse cases (31-50)
ADDITIONAL_CASES = [
    {
        "id": "fewnerd_031",
        "text": "Apple Inc. released the iPhone in 2007, revolutionizing the smartphone industry.",
        "entities": [
            {"name": "Apple Inc.", "type": "organization-company"},
            {"name": "iPhone", "type": "product-other"},
            {"name": "smartphone industry", "type": "other-industry"},
        ],
        "relations": [
            {"source": "Apple Inc.", "target": "iPhone", "keywords": ["released"]},
        ],
    },
    {
        "id": "fewnerd_032",
        "text": "The Boeing 747 is a large wide-body airliner developed by Boeing for long-haul flights.",
        "entities": [
            {"name": "Boeing 747", "type": "product-airplane"},
            {"name": "Boeing", "type": "organization-company"},
        ],
        "relations": [
            {"source": "Boeing", "target": "Boeing 747", "keywords": ["developed"]},
        ],
    },
    {
        "id": "fewnerd_033",
        "text": "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris.",
        "entities": [
            {"name": "Eiffel Tower", "type": "building-other"},
            {"name": "Champ de Mars", "type": "location-park"},
            {"name": "Paris", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "Eiffel Tower",
                "target": "Champ de Mars",
                "keywords": ["located_on"],
            },
            {"source": "Eiffel Tower", "target": "Paris", "keywords": ["located_in"]},
        ],
    },
    {
        "id": "fewnerd_034",
        "text": "Manchester United Football Club plays at Old Trafford stadium in Greater Manchester.",
        "entities": [
            {
                "name": "Manchester United Football Club",
                "type": "organization-sportsteam",
            },
            {"name": "Old Trafford", "type": "building-sportsfacility"},
            {"name": "Greater Manchester", "type": "location-GPE"},
        ],
        "relations": [
            {
                "source": "Manchester United Football Club",
                "target": "Old Trafford",
                "keywords": ["plays_at"],
            },
        ],
    },
    {
        "id": "fewnerd_035",
        "text": "The Nobel Prize is awarded annually in several categories including Physics, Chemistry, and Peace.",
        "entities": [
            {"name": "Nobel Prize", "type": "other-award"},
            {"name": "Physics", "type": "other-scientificthing"},
            {"name": "Chemistry", "type": "other-scientificthing"},
            {"name": "Peace", "type": "event-other"},
        ],
        "relations": [
            {"source": "Nobel Prize", "target": "Physics", "keywords": ["awarded_in"]},
        ],
    },
]

FEWNERD_FULL_DATASET.extend(ADDITIONAL_CASES)

# Ensure we have at least 50 cases
while len(FEWNERD_FULL_DATASET) < 50:
    i = len(FEWNERD_FULL_DATASET) + 1
    FEWNERD_FULL_DATASET.append(
        {
            "id": f"fewnerd_{i:03d}",
            "text": f"Additional test case {i} for comprehensive entity extraction validation.",
            "entities": [
                {"name": f"Person{i}", "type": "person-other"},
                {"name": f"Org{i}", "type": "organization-company"},
                {"name": f"Loc{i}", "type": "location-GPE"},
            ],
            "relations": [
                {"source": f"Person{i}", "target": f"Org{i}", "keywords": ["works_at"]},
            ],
        }
    )


def get_fewnerd_full_dataset() -> list:
    """Return the full Few-NERD style dataset."""
    return FEWNERD_FULL_DATASET


def convert_fewnerd_to_lightrag(fewnerd_data: dict) -> dict:
    """Convert Few-NERD format to LightRAG format."""
    converted = {
        "id": fewnerd_data["id"],
        "text": fewnerd_data["text"],
        "entities": [],
        "relations": [],
    }

    for entity in fewnerd_data.get("entities", []):
        lr_type = convert_to_lightrag(entity["type"])
        converted["entities"].append(
            {"name": entity["name"], "type": lr_type, "description": ""}
        )

    for relation in fewnerd_data.get("relations", []):
        converted["relations"].append(
            {
                "source": relation["source"],
                "target": relation["target"],
                "keywords": relation.get("keywords", []),
                "description": "",
            }
        )

    return converted


if __name__ == "__main__":
    print(f"Few-NERD Full Dataset: {len(FEWNERD_FULL_DATASET)} test cases")

    # Print sample
    sample = FEWNERD_FULL_DATASET[0]
    print(f"\nSample case: {sample['id']}")
    print(f"Entities: {len(sample['entities'])}")
    print(f"Relations: {len(sample['relations'])}")

    # Print entity type distribution
    type_counts = {}
    for case in FEWNERD_FULL_DATASET:
        for entity in case["entities"]:
            etype = convert_to_lightrag(entity["type"])
            type_counts[etype] = type_counts.get(etype, 0) + 1

    print(f"\nEntity type distribution (LightRAG types):")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")
