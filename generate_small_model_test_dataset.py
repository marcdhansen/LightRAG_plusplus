#!/usr/bin/env python3
"""
Generate comprehensive test datasets for 1.5B/7B model prompt optimization.

This script creates diverse test cases spanning different complexity levels,
domain types, and extraction challenges specifically designed for small model testing.

Categories covered:
- Simple entity-relation pairs
- Medium complexity scientific/technical content
- High complexity nested relationships
- Edge cases and challenging extractions
- Domain-specific content (tech, science, literature, business)
"""

import json
from datetime import datetime
from pathlib import Path


def generate_test_dataset():
    """Generate comprehensive test dataset for small model testing."""

    # Simple cases for 1.5B models
    simple_cases = [
        {
            "id": "basic_person_location",
            "text": "Ada Lovelace was born in London.",
            "expected_entities": [
                {"name": "Ada Lovelace", "type": "Person"},
                {"name": "London", "type": "Location"},
            ],
            "expected_relations": [
                {"source": "Ada Lovelace", "target": "London", "keywords": ["born"]}
            ],
            "complexity": "simple",
            "domain": "biography",
            "target_models": ["1.5B", "7B"],
            "extraction_difficulty": "easy",
        },
        {
            "id": "simple_org_founding",
            "text": "Microsoft was founded by Bill Gates and Paul Allen.",
            "expected_entities": [
                {"name": "Microsoft", "type": "Organization"},
                {"name": "Bill Gates", "type": "Person"},
                {"name": "Paul Allen", "type": "Person"},
            ],
            "expected_relations": [
                {
                    "source": "Bill Gates",
                    "target": "Microsoft",
                    "keywords": ["founded"],
                },
                {
                    "source": "Paul Allen",
                    "target": "Microsoft",
                    "keywords": ["founded"],
                },
            ],
            "complexity": "simple",
            "domain": "business",
            "target_models": ["1.5B", "7B"],
            "extraction_difficulty": "easy",
        },
        {
            "id": "basic_concept_discovery",
            "text": "Isaac Newton discovered gravity.",
            "expected_entities": [
                {"name": "Isaac Newton", "type": "Person"},
                {"name": "gravity", "type": "Concept"},
            ],
            "expected_relations": [
                {
                    "source": "Isaac Newton",
                    "target": "gravity",
                    "keywords": ["discovered"],
                }
            ],
            "complexity": "simple",
            "domain": "science",
            "target_models": ["1.5B", "7B"],
            "extraction_difficulty": "easy",
        },
    ]

    # Medium complexity cases for 7B models
    medium_cases = [
        {
            "id": "tech_startup_ecosystem",
            "text": "OpenAI developed ChatGPT with funding from Microsoft. Sam Altman leads the company as CEO.",
            "expected_entities": [
                {"name": "OpenAI", "type": "Organization"},
                {"name": "ChatGPT", "type": "Product"},
                {"name": "Microsoft", "type": "Organization"},
                {"name": "Sam Altman", "type": "Person"},
            ],
            "expected_relations": [
                {"source": "OpenAI", "target": "ChatGPT", "keywords": ["developed"]},
                {"source": "Microsoft", "target": "OpenAI", "keywords": ["funding"]},
                {
                    "source": "Sam Altman",
                    "target": "OpenAI",
                    "keywords": ["leads", "CEO"],
                },
            ],
            "complexity": "medium",
            "domain": "technology",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
        },
        {
            "id": "scientific_research_paper",
            "text": "Researchers at MIT published a study in Nature about quantum computing. The paper discusses qubit stability.",
            "expected_entities": [
                {"name": "MIT", "type": "Organization"},
                {"name": "Nature", "type": "Organization"},
                {"name": "quantum computing", "type": "Concept"},
                {"name": "qubit stability", "type": "Concept"},
            ],
            "expected_relations": [
                {
                    "source": "MIT",
                    "target": "Nature",
                    "keywords": ["published", "study"],
                },
                {
                    "source": "paper",
                    "target": "quantum computing",
                    "keywords": ["discusses"],
                },
                {
                    "source": "paper",
                    "target": "qubit stability",
                    "keywords": ["discusses"],
                },
            ],
            "complexity": "medium",
            "domain": "academic",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
        },
        {
            "id": "historical_event_chain",
            "text": "The Wright Brothers achieved first flight at Kitty Hawk in 1903. This event revolutionized aviation.",
            "expected_entities": [
                {"name": "Wright Brothers", "type": "Person"},
                {"name": "first flight", "type": "Event"},
                {"name": "Kitty Hawk", "type": "Location"},
                {"name": "1903", "type": "Time"},
                {"name": "aviation", "type": "Concept"},
            ],
            "expected_relations": [
                {
                    "source": "Wright Brothers",
                    "target": "first flight",
                    "keywords": ["achieved"],
                },
                {"source": "first flight", "target": "Kitty Hawk", "keywords": ["at"]},
                {"source": "first flight", "target": "1903", "keywords": ["in"]},
                {
                    "source": "first flight",
                    "target": "aviation",
                    "keywords": ["revolutionized"],
                },
            ],
            "complexity": "medium",
            "domain": "history",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
        },
    ]

    # High complexity challenging cases
    complex_cases = [
        {
            "id": "nested_tech_relationships",
            "text": "NVIDIA's RTX GPUs, powered by CUDA architecture, enable AI workloads through TensorFlow integration while competing with AMD's Radeon cards.",
            "expected_entities": [
                {"name": "NVIDIA", "type": "Organization"},
                {"name": "RTX GPUs", "type": "Product"},
                {"name": "CUDA", "type": "Technology"},
                {"name": "AI workloads", "type": "Concept"},
                {"name": "TensorFlow", "type": "Technology"},
                {"name": "AMD", "type": "Organization"},
                {"name": "Radeon cards", "type": "Product"},
            ],
            "expected_relations": [
                {"source": "NVIDIA", "target": "RTX GPUs", "keywords": ["produces"]},
                {"source": "RTX GPUs", "target": "CUDA", "keywords": ["powered", "by"]},
                {
                    "source": "RTX GPUs",
                    "target": "AI workloads",
                    "keywords": ["enable"],
                },
                {
                    "source": "AI workloads",
                    "target": "TensorFlow",
                    "keywords": ["through"],
                },
                {
                    "source": "RTX GPUs",
                    "target": "Radeon cards",
                    "keywords": ["competing", "with"],
                },
                {"source": "AMD", "target": "Radeon cards", "keywords": ["produces"]},
            ],
            "complexity": "high",
            "domain": "technology",
            "target_models": ["7B"],
            "extraction_difficulty": "hard",
        },
        {
            "id": "multi_domain_research",
            "text": "CERN's Large Hadron Collider discovers Higgs boson through particle collisions, collaborating with Oxford physicists and publishing in Physical Review Letters.",
            "expected_entities": [
                {"name": "CERN", "type": "Organization"},
                {"name": "Large Hadron Collider", "type": "Technology"},
                {"name": "Higgs boson", "type": "Concept"},
                {"name": "particle collisions", "type": "Concept"},
                {"name": "Oxford", "type": "Organization"},
                {"name": "physicists", "type": "Person"},
                {"name": "Physical Review Letters", "type": "Organization"},
            ],
            "expected_relations": [
                {
                    "source": "CERN",
                    "target": "Large Hadron Collider",
                    "keywords": ["operates"],
                },
                {
                    "source": "Large Hadron Collider",
                    "target": "Higgs boson",
                    "keywords": ["discovers"],
                },
                {
                    "source": "discovery",
                    "target": "particle collisions",
                    "keywords": ["through"],
                },
                {
                    "source": "CERN",
                    "target": "Oxford",
                    "keywords": ["collaborating", "with"],
                },
                {"source": "Oxford", "target": "physicists", "keywords": ["employs"]},
                {
                    "source": "research",
                    "target": "Physical Review Letters",
                    "keywords": ["published", "in"],
                },
            ],
            "complexity": "high",
            "domain": "physics",
            "target_models": ["7B"],
            "extraction_difficulty": "hard",
        },
    ]

    # Edge cases and problematic extractions
    edge_cases = [
        {
            "id": "ambiguous_entities",
            "text": "Apple announced new features for Apple Watch while competing with Apple Records in court.",
            "expected_entities": [
                {"name": "Apple", "type": "Organization"},
                {"name": "Apple Watch", "type": "Product"},
                {"name": "Apple Records", "type": "Organization"},
            ],
            "expected_relations": [
                {
                    "source": "Apple",
                    "target": "Apple Watch",
                    "keywords": ["announced", "features"],
                },
                {
                    "source": "Apple",
                    "target": "Apple Records",
                    "keywords": ["competing", "with"],
                },
                {"source": "competition", "target": "court", "keywords": ["in"]},
            ],
            "complexity": "medium",
            "domain": "legal/business",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
            "notes": "Entity disambiguation challenge",
        },
        {
            "id": "implicit_relationships",
            "text": "The morning sun rose over mountains. Birds began singing their daily songs.",
            "expected_entities": [
                {"name": "morning sun", "type": "Natural"},
                {"name": "mountains", "type": "Location"},
                {"name": "Birds", "type": "Natural"},
                {"name": "songs", "type": "Concept"},
            ],
            "expected_relations": [
                {
                    "source": "morning sun",
                    "target": "mountains",
                    "keywords": ["rose", "over"],
                },
                {"source": "Birds", "target": "songs", "keywords": ["singing"]},
            ],
            "complexity": "medium",
            "domain": "nature",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
            "notes": "Temporal and causal relationships",
        },
    ]

    # Domain-specific test suites
    business_cases = [
        {
            "id": "corporate_structure",
            "text": "Google's parent company Alphabet owns DeepMind, which acquired Dark Blue Labs. Sundar Pichai serves as Google's CEO.",
            "expected_entities": [
                {"name": "Google", "type": "Organization"},
                {"name": "Alphabet", "type": "Organization"},
                {"name": "DeepMind", "type": "Organization"},
                {"name": "Dark Blue Labs", "type": "Organization"},
                {"name": "Sundar Pichai", "type": "Person"},
            ],
            "expected_relations": [
                {
                    "source": "Alphabet",
                    "target": "Google",
                    "keywords": ["parent", "company"],
                },
                {"source": "Alphabet", "target": "DeepMind", "keywords": ["owns"]},
                {
                    "source": "DeepMind",
                    "target": "Dark Blue Labs",
                    "keywords": ["acquired"],
                },
                {
                    "source": "Sundar Pichai",
                    "target": "Google",
                    "keywords": ["CEO", "serves"],
                },
            ],
            "complexity": "medium",
            "domain": "business",
            "target_models": ["7B"],
            "extraction_difficulty": "moderate",
        }
    ]

    # Combine all test cases
    all_test_cases = (
        simple_cases + medium_cases + complex_cases + edge_cases + business_cases
    )

    return all_test_cases


def calculate_test_metrics(test_cases):
    """Calculate metadata for test cases."""

    metadata = {
        "total_cases": len(test_cases),
        "complexity_distribution": {},
        "domain_distribution": {},
        "difficulty_distribution": {},
        "model_target_distribution": {},
        "entity_counts": {"min": float("inf"), "max": 0, "avg": 0},
        "relation_counts": {"min": float("inf"), "max": 0, "avg": 0},
    }

    total_entities = 0
    total_relations = 0

    for case in test_cases:
        # Complexity distribution
        complexity = case.get("complexity", "unknown")
        metadata["complexity_distribution"][complexity] = (
            metadata["complexity_distribution"].get(complexity, 0) + 1
        )

        # Domain distribution
        domain = case.get("domain", "unknown")
        metadata["domain_distribution"][domain] = (
            metadata["domain_distribution"].get(domain, 0) + 1
        )

        # Difficulty distribution
        difficulty = case.get("extraction_difficulty", "unknown")
        metadata["difficulty_distribution"][difficulty] = (
            metadata["difficulty_distribution"].get(difficulty, 0) + 1
        )

        # Model target distribution
        for model in case.get("target_models", []):
            metadata["model_target_distribution"][model] = (
                metadata["model_target_distribution"].get(model, 0) + 1
            )

        # Entity/Relation counts
        entity_count = len(case["expected_entities"])
        relation_count = len(case["expected_relations"])

        total_entities += entity_count
        total_relations += relation_count

        metadata["entity_counts"]["min"] = min(
            metadata["entity_counts"]["min"], entity_count
        )
        metadata["entity_counts"]["max"] = max(
            metadata["entity_counts"]["max"], entity_count
        )
        metadata["relation_counts"]["min"] = min(
            metadata["relation_counts"]["min"], relation_count
        )
        metadata["relation_counts"]["max"] = max(
            metadata["relation_counts"]["max"], relation_count
        )

    metadata["entity_counts"]["avg"] = total_entities / len(test_cases)
    metadata["relation_counts"]["avg"] = total_relations / len(test_cases)

    return metadata


def main():
    """Generate and save comprehensive test dataset."""

    print("🔧 Generating comprehensive test dataset for 1.5B/7B model optimization...")

    # Generate test cases
    test_cases = generate_test_dataset()
    metadata = calculate_test_metrics(test_cases)

    # Create dataset structure
    dataset = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
        "purpose": "1.5B/7B model prompt optimization testing",
        "metadata": metadata,
        "test_cases": test_cases,
    }

    # Save dataset
    output_dir = Path("./test_datasets")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "small_model_test_dataset.json"
    with open(output_file, "w") as f:
        json.dump(dataset, f, indent=2)

    # Print summary
    print(f"\n✅ Dataset generated: {output_file}")
    print("📊 Dataset Statistics:")
    print(f"   Total test cases: {metadata['total_cases']}")
    print(f"   Complexity: {dict(metadata['complexity_distribution'])}")
    print(f"   Domains: {dict(metadata['domain_distribution'])}")
    print(f"   Difficulty: {dict(metadata['difficulty_distribution'])}")
    print(f"   Model targets: {dict(metadata['model_target_distribution'])}")
    print(
        f"   Entity counts: min={metadata['entity_counts']['min']}, max={metadata['entity_counts']['max']}, avg={metadata['entity_counts']['avg']:.1f}"
    )
    print(
        f"   Relation counts: min={metadata['relation_counts']['min']}, max={metadata['relation_counts']['max']}, avg={metadata['relation_counts']['avg']:.1f}"
    )

    # Generate simplified subsets for quick testing
    simple_subset = [
        case for case in test_cases if case.get("extraction_difficulty") == "easy"
    ]
    medium_subset = [
        case
        for case in test_cases
        if case.get("extraction_difficulty") in ["easy", "moderate"]
    ]

    # Save subsets
    simple_dataset = {
        **dataset,
        "test_cases": simple_subset,
        "metadata": calculate_test_metrics(simple_subset),
    }
    simple_dataset["metadata"]["subset_type"] = "simple_only"

    with open(output_dir / "simple_test_subset.json", "w") as f:
        json.dump(simple_dataset, f, indent=2)

    medium_dataset = {
        **dataset,
        "test_cases": medium_subset,
        "metadata": calculate_test_metrics(medium_subset),
    }
    medium_dataset["metadata"]["subset_type"] = "easy_to_medium"

    with open(output_dir / "medium_test_subset.json", "w") as f:
        json.dump(medium_dataset, f, indent=2)

    print("\n📂 Additional subsets created:")
    print(f"   Simple subset: {len(simple_subset)} cases")
    print(f"   Medium subset: {len(medium_subset)} cases")

    print("\n🎯 Ready for Phase 1 testing!")


if __name__ == "__main__":
    main()
