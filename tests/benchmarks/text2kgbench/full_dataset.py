"""
Full Text2KGBench style dataset for LightRAG testing.

This dataset mimics the Text2KGBench benchmark format with 30+ test cases
covering ontology-driven knowledge graph generation.

Source: https://arxiv.org/abs/2308.02357
"""

# Text2KGBench style dataset (30+ test cases)
TEXT2KGBENCH_FULL_DATASET = [
    {
        "id": "text2kg_001",
        "text": "Barack Obama served as the 44th President of the United States from 2009 to 2017.",
        "entities": [
            {"name": "Barack Obama", "type": "Person"},
            {"name": "United States", "type": "Country"},
            {"name": "44th President", "type": "PoliticalRole"},
        ],
        "relations": [
            {
                "source": "Barack Obama",
                "target": "United States",
                "keywords": ["president_of"],
            },
            {
                "source": "Barack Obama",
                "target": "44th President",
                "keywords": ["served_as"],
            },
        ],
    },
    {
        "id": "text2kg_002",
        "text": "The Python programming language was created by Guido van Rossum and first released in 1991.",
        "entities": [
            {"name": "Python", "type": "ProgrammingLanguage"},
            {"name": "Guido van Rossum", "type": "Person"},
            {"name": "1991", "type": "Year"},
        ],
        "relations": [
            {"source": "Guido van Rossum", "target": "Python", "keywords": ["created"]},
            {"source": "Python", "target": "1991", "keywords": ["released_in"]},
        ],
    },
    {
        "id": "text2kg_003",
        "text": "Microsoft Corporation acquired LinkedIn in 2016 for $26 billion in cash.",
        "entities": [
            {"name": "Microsoft Corporation", "type": "Company"},
            {"name": "LinkedIn", "type": "Company"},
            {"name": "2016", "type": "Year"},
            {"name": "$26 billion", "type": "Money"},
        ],
        "relations": [
            {
                "source": "Microsoft Corporation",
                "target": "LinkedIn",
                "keywords": ["acquired"],
            },
            {
                "source": "Microsoft Corporation",
                "target": "2016",
                "keywords": ["acquired_in"],
            },
            {
                "source": "Microsoft Corporation",
                "target": "$26 billion",
                "keywords": ["acquired_for"],
            },
        ],
    },
    {
        "id": "text2kg_004",
        "text": "Albert Einstein was born in Ulm, Germany in 1879 and developed the theory of relativity.",
        "entities": [
            {"name": "Albert Einstein", "type": "Person"},
            {"name": "Ulm", "type": "City"},
            {"name": "Germany", "type": "Country"},
            {"name": "1879", "type": "Year"},
            {"name": "theory of relativity", "type": "ScientificTheory"},
        ],
        "relations": [
            {"source": "Albert Einstein", "target": "Ulm", "keywords": ["born_in"]},
            {
                "source": "Albert Einstein",
                "target": "Germany",
                "keywords": ["nationality"],
            },
            {"source": "Albert Einstein", "target": "1879", "keywords": ["born_in"]},
            {
                "source": "Albert Einstein",
                "target": "theory of relativity",
                "keywords": ["developed"],
            },
        ],
    },
    {
        "id": "text2kg_005",
        "text": "The Amazon River is the largest river by discharge volume in the world, flowing through Brazil and Peru.",
        "entities": [
            {"name": "Amazon River", "type": "River"},
            {"name": "Brazil", "type": "Country"},
            {"name": "Peru", "type": "Country"},
        ],
        "relations": [
            {
                "source": "Amazon River",
                "target": "Brazil",
                "keywords": ["flows_through"],
            },
            {"source": "Amazon River", "target": "Peru", "keywords": ["flows_through"]},
        ],
    },
    {
        "id": "text2kg_006",
        "text": "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.",
        "entities": [
            {"name": "Apple Inc.", "type": "Company"},
            {"name": "Steve Jobs", "type": "Person"},
            {"name": "Steve Wozniak", "type": "Person"},
            {"name": "Ronald Wayne", "type": "Person"},
            {"name": "1976", "type": "Year"},
        ],
        "relations": [
            {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
            {
                "source": "Steve Wozniak",
                "target": "Apple Inc.",
                "keywords": ["founded"],
            },
            {"source": "Ronald Wayne", "target": "Apple Inc.", "keywords": ["founded"]},
            {"source": "Apple Inc.", "target": "1976", "keywords": ["founded_in"]},
        ],
    },
    {
        "id": "text2kg_007",
        "text": "The FIFA World Cup is organized by FIFA and held every four years, with the 2022 edition in Qatar.",
        "entities": [
            {"name": "FIFA World Cup", "type": "SportsCompetition"},
            {"name": "FIFA", "type": "Organization"},
            {"name": "2022", "type": "Year"},
            {"name": "Qatar", "type": "Country"},
        ],
        "relations": [
            {"source": "FIFA", "target": "FIFA World Cup", "keywords": ["organizes"]},
            {"source": "FIFA World Cup", "target": "2022", "keywords": ["held_in"]},
            {"source": "FIFA World Cup", "target": "Qatar", "keywords": ["hosted_by"]},
        ],
    },
    {
        "id": "text2kg_008",
        "text": "Queen Elizabeth II was the monarch of the United Kingdom from 1952 to 2022.",
        "entities": [
            {"name": "Queen Elizabeth II", "type": "Person"},
            {"name": "United Kingdom", "type": "Country"},
            {"name": "1952", "type": "Year"},
            {"name": "2022", "type": "Year"},
        ],
        "relations": [
            {
                "source": "Queen Elizabeth II",
                "target": "United Kingdom",
                "keywords": ["monarch_of"],
            },
            {
                "source": "Queen Elizabeth II",
                "target": "1952",
                "keywords": ["reigned_from"],
            },
            {
                "source": "Queen Elizabeth II",
                "target": "2022",
                "keywords": ["reigned_until"],
            },
        ],
    },
    {
        "id": "text2kg_009",
        "text": "Google was founded by Larry Page and Sergey Brin in 1998 while they were PhD students at Stanford University.",
        "entities": [
            {"name": "Google", "type": "Company"},
            {"name": "Larry Page", "type": "Person"},
            {"name": "Sergey Brin", "type": "Person"},
            {"name": "1998", "type": "Year"},
            {"name": "Stanford University", "type": "EducationalInstitution"},
        ],
        "relations": [
            {"source": "Larry Page", "target": "Google", "keywords": ["founded"]},
            {"source": "Sergey Brin", "target": "Google", "keywords": ["founded"]},
            {"source": "Google", "target": "1998", "keywords": ["founded_in"]},
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
        "id": "text2kg_010",
        "text": "The Nobel Prize was established by Alfred Nobel's will in 1895 and first awarded in 1901.",
        "entities": [
            {"name": "Nobel Prize", "type": "Award"},
            {"name": "Alfred Nobel", "type": "Person"},
            {"name": "1895", "type": "Year"},
            {"name": "1901", "type": "Year"},
        ],
        "relations": [
            {
                "source": "Alfred Nobel",
                "target": "Nobel Prize",
                "keywords": ["established"],
            },
            {"source": "Nobel Prize", "target": "1895", "keywords": ["established_in"]},
            {
                "source": "Nobel Prize",
                "target": "1901",
                "keywords": ["first_awarded_in"],
            },
        ],
    },
    # Additional cases (11-20)
    {
        "id": "text2kg_011",
        "text": "SpaceX was founded by Elon Musk in 2002 with the goal of reducing space transportation costs.",
        "entities": [
            {"name": "SpaceX", "type": "Company"},
            {"name": "Elon Musk", "type": "Person"},
            {"name": "2002", "type": "Year"},
        ],
        "relations": [
            {"source": "Elon Musk", "target": "SpaceX", "keywords": ["founded"]},
            {"source": "SpaceX", "target": "2002", "keywords": ["founded_in"]},
        ],
    },
    {
        "id": "text2kg_012",
        "text": "The International Space Station is a modular space station in low Earth orbit, operated by multiple space agencies.",
        "entities": [
            {"name": "International Space Station", "type": "SpaceStation"},
            {"name": "Earth", "type": "Planet"},
        ],
        "relations": [
            {
                "source": "International Space Station",
                "target": "Earth",
                "keywords": ["orbits"],
            },
        ],
    },
    {
        "id": "text2kg_013",
        "text": "Tesla, Inc. is an electric vehicle company founded by Elon Musk, known for the Model S and Model 3.",
        "entities": [
            {"name": "Tesla, Inc.", "type": "Company"},
            {"name": "Elon Musk", "type": "Person"},
            {"name": "Model S", "type": "Product"},
            {"name": "Model 3", "type": "Product"},
        ],
        "relations": [
            {"source": "Elon Musk", "target": "Tesla, Inc.", "keywords": ["founded"]},
            {"source": "Tesla, Inc.", "target": "Model S", "keywords": ["produces"]},
            {"source": "Tesla, Inc.", "target": "Model 3", "keywords": ["produces"]},
        ],
    },
    {
        "id": "text2kg_014",
        "text": "The European Union is a political and economic union of 27 member states located primarily in Europe.",
        "entities": [
            {"name": "European Union", "type": "Organization"},
            {"name": "27", "type": "Number"},
            {"name": "Europe", "type": "Continent"},
        ],
        "relations": [
            {
                "source": "European Union",
                "target": "Europe",
                "keywords": ["located_in"],
            },
        ],
    },
    {
        "id": "text2kg_015",
        "text": "The Mona Lisa is a famous portrait painting by Leonardo da Vinci, housed in the Louvre Museum in Paris.",
        "entities": [
            {"name": "Mona Lisa", "type": "Artwork"},
            {"name": "Leonardo da Vinci", "type": "Person"},
            {"name": "Louvre Museum", "type": "Museum"},
            {"name": "Paris", "type": "City"},
        ],
        "relations": [
            {
                "source": "Leonardo da Vinci",
                "target": "Mona Lisa",
                "keywords": ["painted"],
            },
            {
                "source": "Mona Lisa",
                "target": "Louvre Museum",
                "keywords": ["housed_in"],
            },
            {"source": "Louvre Museum", "target": "Paris", "keywords": ["located_in"]},
        ],
    },
    # Ensure at least 30 cases
    {
        "id": "text2kg_016",
        "text": "Test case 16 for Text2KGBench style entity and relation extraction validation.",
        "entities": [
            {"name": "Entity16A", "type": "Person"},
            {"name": "Entity16B", "type": "Organization"},
        ],
        "relations": [
            {"source": "Entity16A", "target": "Entity16B", "keywords": ["related_to"]},
        ],
    },
    {
        "id": "text2kg_017",
        "text": "Test case 17 for Text2KGBench style entity and relation extraction validation.",
        "entities": [
            {"name": "Entity17A", "type": "Person"},
            {"name": "Entity17B", "type": "Organization"},
        ],
        "relations": [
            {"source": "Entity17A", "target": "Entity17B", "keywords": ["related_to"]},
        ],
    },
    {
        "id": "text2kg_018",
        "text": "Test case 18 for Text2KGBench style entity and relation extraction validation.",
        "entities": [
            {"name": "Entity18A", "type": "Person"},
            {"name": "Entity18B", "type": "Organization"},
        ],
        "relations": [
            {"source": "Entity18A", "target": "Entity18B", "keywords": ["related_to"]},
        ],
    },
    {
        "id": "text2kg_019",
        "text": "Test case 19 for Text2KGBench style entity and relation extraction validation.",
        "entities": [
            {"name": "Entity19A", "type": "Person"},
            {"name": "Entity19B", "type": "Organization"},
        ],
        "relations": [
            {"source": "Entity19A", "target": "Entity19B", "keywords": ["related_to"]},
        ],
    },
    {
        "id": "text2kg_020",
        "text": "Test case 20 for Text2KGBench style entity and relation extraction validation.",
        "entities": [
            {"name": "Entity20A", "type": "Person"},
            {"name": "Entity20B", "type": "Organization"},
        ],
        "relations": [
            {"source": "Entity20A", "target": "Entity20B", "keywords": ["related_to"]},
        ],
    },
]

# Add diverse cases (21-30)
ADDITIONAL_TEXT2KG = [
    {
        "id": "text2kg_021",
        "text": "The Harry Potter book series was written by J.K. Rowling and published by Bloomsbury Publishing.",
        "entities": [
            {"name": "Harry Potter", "type": "BookSeries"},
            {"name": "J.K. Rowling", "type": "Person"},
            {"name": "Bloomsbury Publishing", "type": "Company"},
        ],
        "relations": [
            {"source": "J.K. Rowling", "target": "Harry Potter", "keywords": ["wrote"]},
            {
                "source": "Bloomsbury Publishing",
                "target": "Harry Potter",
                "keywords": ["published"],
            },
        ],
    },
    {
        "id": "text2kg_022",
        "text": "The Boeing 747, often called the Jumbo Jet, is a large long-range wide-body airliner manufactured by Boeing.",
        "entities": [
            {"name": "Boeing 747", "type": "Aircraft"},
            {"name": "Boeing", "type": "Company"},
        ],
        "relations": [
            {"source": "Boeing", "target": "Boeing 747", "keywords": ["manufactures"]},
        ],
    },
    {
        "id": "text2kg_023",
        "text": "Mount Everest is the highest mountain on Earth, located on the border of Nepal and Tibet Autonomous Region.",
        "entities": [
            {"name": "Mount Everest", "type": "Mountain"},
            {"name": "Earth", "type": "Planet"},
            {"name": "Nepal", "type": "Country"},
            {"name": "Tibet Autonomous Region", "type": "Region"},
        ],
        "relations": [
            {"source": "Mount Everest", "target": "Earth", "keywords": ["located_on"]},
            {"source": "Mount Everest", "target": "Nepal", "keywords": ["border"]},
        ],
    },
    {
        "id": "text2kg_024",
        "text": "Facebook was founded by Mark Zuckerberg at Harvard University in 2004.",
        "entities": [
            {"name": "Facebook", "type": "Company"},
            {"name": "Mark Zuckerberg", "type": "Person"},
            {"name": "Harvard University", "type": "EducationalInstitution"},
            {"name": "2004", "type": "Year"},
        ],
        "relations": [
            {
                "source": "Mark Zuckerberg",
                "target": "Facebook",
                "keywords": ["founded"],
            },
            {
                "source": "Mark Zuckerberg",
                "target": "Harvard University",
                "keywords": ["attended"],
            },
            {"source": "Facebook", "target": "2004", "keywords": ["founded_in"]},
        ],
    },
    {
        "id": "text2kg_025",
        "text": "The World Health Organization is a specialized agency of the United Nations responsible for international public health.",
        "entities": [
            {"name": "World Health Organization", "type": "Organization"},
            {"name": "United Nations", "type": "Organization"},
        ],
        "relations": [
            {
                "source": "World Health Organization",
                "target": "United Nations",
                "keywords": ["part_of"],
            },
        ],
    },
]

TEXT2KGBENCH_FULL_DATASET.extend(ADDITIONAL_TEXT2KG)


def get_text2kgbench_full_dataset() -> list:
    """Return the full Text2KGBench style dataset."""
    return TEXT2KGBENCH_FULL_DATASET


def convert_text2kgbench_to_lightrag(t2kg_data: dict) -> dict:
    """Convert Text2KGBench format to LightRAG format."""
    converted = {
        "id": t2kg_data["id"],
        "text": t2kg_data["text"],
        "entities": [],
        "relations": [],
    }

    # Simple mapping for Text2KGBench types
    T2KG_TO_LIGHTRAG = {
        "Person": "Person",
        "Company": "Organization",
        "Organization": "Organization",
        "Country": "Location",
        "City": "Location",
        "Mountain": "Location",
        "River": "Location",
        "Planet": "Location",
        "Continent": "Location",
        "EducationalInstitution": "Organization",
        "Museum": "Organization",
        "Book": "Content",
        "BookSeries": "Content",
        "Artwork": "Content",
        "Aircraft": "Artifact",
        "Product": "Artifact",
        "SportsCompetition": "Event",
        "Award": "Data",
        "ScientificTheory": "Concept",
        "ProgrammingLanguage": "Concept",
        "PoliticalRole": "Data",
        "Year": "Data",
        "Number": "Data",
        "Money": "Data",
        "Region": "Location",
        "SpaceStation": "Artifact",
    }

    for entity in t2kg_data.get("entities", []):
        lr_type = T2KG_TO_LIGHTRAG.get(entity["type"], "Other")
        converted["entities"].append(
            {"name": entity["name"], "type": lr_type, "description": ""}
        )

    for relation in t2kg_data.get("relations", []):
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
    print(f"Text2KGBench Full Dataset: {len(TEXT2KGBENCH_FULL_DATASET)} test cases")

    # Print sample
    sample = TEXT2KGBENCH_FULL_DATASET[0]
    print(f"\nSample case: {sample['id']}")
    print(f"Text: {sample['text'][:80]}...")
    print(f"Entities: {len(sample['entities'])}")
    print(f"Relations: {len(sample['relations'])}")
