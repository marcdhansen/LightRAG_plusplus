#!/usr/bin/env python3
"""
Prompt Baseline Audit for ACE Optimizer (Phase 6.1)

This script benchmarks extraction quality across different model sizes (1.5B, 3B, 7B)
to establish baseline metrics for prompt optimization.

Metrics measured:
- Entity recall (% of expected entities extracted)
- Relationship accuracy (% of expected relationships extracted)
- YAML compliance rate (% of valid YAML outputs)
- Hallucination frequency (% of unexpected entities)
- Execution time per extraction

Usage:
    python run_prompt_baseline_audit.py [--models MODEL1,MODEL2] [--output OUTPUT_FILE]

Example:
    python run_prompt_baseline_audit.py --models qwen2.5-coder:1.5b,qwen2.5-coder:7b
"""

import argparse
import asyncio
import json
import os
import shutil
import time
from datetime import datetime
from functools import partial
from pathlib import Path

from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

# Test cases with ground truth
TEST_CASES = [
    {
        "id": "simple_person_org",
        "text": "Steve Jobs founded Apple.",
        "expected_entities": [
            {"name": "Apple", "type": "Organization"},
            {"name": "Steve Jobs", "type": "Person"},
        ],
        "expected_relations": [
            {"source": "Steve Jobs", "target": "Apple", "keywords": ["founded"]}
        ],
    },
    {
        "id": "einstein_basic",
        "text": (
            "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
            "He is best known for developing the Theory of Relativity."
        ),
        "expected_entities": [
            {"name": "Albert Einstein", "type": "Person"},
            {"name": "Ulm", "type": "Location"},
            {"name": "Germany", "type": "Location"},
            {"name": "Theory of Relativity", "type": "Concept"},
        ],
        "expected_relations": [
            {"source": "Albert Einstein", "target": "Ulm", "keywords": ["born"]},
            {"source": "Albert Einstein", "target": "Germany", "keywords": ["born"]},
            {"source": "Ulm", "target": "Germany", "keywords": ["located", "in"]},
            {
                "source": "Albert Einstein",
                "target": "Theory of Relativity",
                "keywords": ["developed", "developing"],
            },
        ],
    },
    {
        "id": "dickens_opening",
        "text": (
            "It was the best of times, it was the worst of times, it was the age of wisdom, "
            "it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity."
        ),
        "expected_entities": [
            {"name": "best of times", "type": "Concept"},
            {"name": "worst of times", "type": "Concept"},
            {"name": "age of wisdom", "type": "Concept"},
            {"name": "age of foolishness", "type": "Concept"},
            {"name": "epoch of belief", "type": "Concept"},
            {"name": "epoch of incredulity", "type": "Concept"},
        ],
        "expected_relations": [],  # Parallel structure, no explicit relations
    },
]


def normalize_name(name: str) -> str:
    """Normalize string for fuzzy comparison."""
    return name.lower().strip().replace("the ", "")


def find_entity_match(name: str, entities: list) -> dict | None:
    """Find a matching entity in the extracted list using fuzzy matching."""
    target = normalize_name(name)
    for e in entities:
        if target in normalize_name(e["id"]) or normalize_name(e["id"]) in target:
            return e
    return None


async def run_extraction_test(model_name: str, case: dict, working_dir: str) -> dict:
    """
    Run extraction test for a single case with a specific model.

    Returns:
        dict with metrics: entity_recall, relation_accuracy, execution_time, etc.
    """
    # Clean working directory
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(working_dir)

    # Initialize LightRAG
    rag = LightRAG(
        working_dir=working_dir,
        llm_model_name=model_name,
        extraction_format="yaml",  # Test YAML compliance
        entity_extract_max_gleaning=1,  # Standard gleaning
        addon_params={
            "entity_types": [
                "Person",
                "Location",
                "Organization",
                "Concept",
                "Theory",
                "Event",
            ]
        },
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()

    # Measure extraction time
    start_time = time.time()
    try:
        await rag.ainsert(case["text"])
        execution_time = time.time() - start_time
        yaml_compliant = True
    except Exception as e:
        execution_time = time.time() - start_time
        yaml_compliant = False
        print(f"❌ Extraction failed for {case['id']}: {e}")
        return {
            "case_id": case["id"],
            "model": model_name,
            "yaml_compliant": False,
            "execution_time": execution_time,
            "error": str(e),
            "entity_recall": 0.0,
            "relation_accuracy": 0.0,
            "hallucination_rate": 0.0,
        }

    # Get extracted entities
    entities = await rag.chunk_entity_relation_graph.get_all_nodes()
    entity_map = {normalize_name(e["id"]): e["id"] for e in entities}

    # Calculate entity recall
    found_entities = 0
    for expected in case["expected_entities"]:
        if find_entity_match(expected["name"], entities):
            found_entities += 1

    entity_recall = (
        found_entities / len(case["expected_entities"])
        if case["expected_entities"]
        else 1.0
    )

    # Calculate hallucination rate (unexpected entities)
    expected_entity_names = {
        normalize_name(e["name"]) for e in case["expected_entities"]
    }
    hallucinations = 0
    for entity in entities:
        entity_norm = normalize_name(entity["id"])
        # Check if this entity matches any expected entity
        is_expected = any(
            exp_norm in entity_norm or entity_norm in exp_norm
            for exp_norm in expected_entity_names
        )
        if not is_expected:
            hallucinations += 1

    hallucination_rate = hallucinations / len(entities) if entities else 0.0

    # Calculate relation accuracy
    found_relations = 0
    for expected in case["expected_relations"]:
        src_norm = normalize_name(expected["source"])
        tgt_norm = normalize_name(expected["target"])

        src_real = next(
            (real for norm, real in entity_map.items() if src_norm in norm), None
        )
        tgt_real = next(
            (real for norm, real in entity_map.items() if tgt_norm in norm), None
        )

        if src_real and tgt_real:
            edge_exists = await rag.chunk_entity_relation_graph.has_edge(
                src_real, tgt_real
            )
            if not edge_exists:
                edge_exists = await rag.chunk_entity_relation_graph.has_edge(
                    tgt_real, src_real
                )
            if edge_exists:
                found_relations += 1

    relation_accuracy = (
        found_relations / len(case["expected_relations"])
        if case["expected_relations"]
        else 1.0
    )

    return {
        "case_id": case["id"],
        "model": model_name,
        "yaml_compliant": yaml_compliant,
        "execution_time": execution_time,
        "entity_recall": entity_recall,
        "relation_accuracy": relation_accuracy,
        "hallucination_rate": hallucination_rate,
        "entities_found": found_entities,
        "entities_expected": len(case["expected_entities"]),
        "entities_extracted": len(entities),
        "relations_found": found_relations,
        "relations_expected": len(case["expected_relations"]),
    }


async def run_baseline_audit(models: list[str], output_file: str):
    """
    Run baseline audit across all models and test cases.

    Args:
        models: List of model names to test
        output_file: Path to save results JSON
    """
    results = []
    timestamp = datetime.now().isoformat()

    print(f"\n🚀 Starting Prompt Baseline Audit - {timestamp}")
    print(f"📋 Testing {len(models)} models on {len(TEST_CASES)} test cases\n")

    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing Model: {model}")
        print(f"{'='*60}\n")

        for case in TEST_CASES:
            print(f"  Running case: {case['id']}...")
            working_dir = f"./rag_storage_audit_{model.replace(':', '_')}_{case['id']}"

            result = await run_extraction_test(model, case, working_dir)
            results.append(result)

            # Print summary
            print(f"    ✓ Entity Recall: {result['entity_recall']:.1%}")
            print(f"    ✓ Relation Accuracy: {result['relation_accuracy']:.1%}")
            print(f"    ✓ Hallucination Rate: {result['hallucination_rate']:.1%}")
            print(f"    ✓ Execution Time: {result['execution_time']:.2f}s")
            print(f"    ✓ YAML Compliant: {result['yaml_compliant']}\n")

            # Cleanup
            if os.path.exists(working_dir):
                shutil.rmtree(working_dir)

    # Calculate aggregate metrics per model
    print(f"\n{'='*60}")
    print("📊 Aggregate Results")
    print(f"{'='*60}\n")

    model_aggregates = {}
    for model in models:
        model_results = [r for r in results if r["model"] == model]

        avg_entity_recall = sum(r["entity_recall"] for r in model_results) / len(
            model_results
        )
        avg_relation_accuracy = sum(
            r["relation_accuracy"] for r in model_results
        ) / len(model_results)
        avg_hallucination_rate = sum(
            r["hallucination_rate"] for r in model_results
        ) / len(model_results)
        avg_execution_time = sum(r["execution_time"] for r in model_results) / len(
            model_results
        )
        yaml_compliance_rate = sum(
            1 for r in model_results if r["yaml_compliant"]
        ) / len(model_results)

        model_aggregates[model] = {
            "avg_entity_recall": avg_entity_recall,
            "avg_relation_accuracy": avg_relation_accuracy,
            "avg_hallucination_rate": avg_hallucination_rate,
            "avg_execution_time": avg_execution_time,
            "yaml_compliance_rate": yaml_compliance_rate,
        }

        print(f"Model: {model}")
        print(f"  Entity Recall: {avg_entity_recall:.1%}")
        print(f"  Relation Accuracy: {avg_relation_accuracy:.1%}")
        print(f"  Hallucination Rate: {avg_hallucination_rate:.1%}")
        print(f"  YAML Compliance: {yaml_compliance_rate:.1%}")
        print(f"  Avg Execution Time: {avg_execution_time:.2f}s\n")

    # Save results
    output_data = {
        "timestamp": timestamp,
        "models_tested": models,
        "test_cases": [c["id"] for c in TEST_CASES],
        "individual_results": results,
        "model_aggregates": model_aggregates,
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")
    print("\n🎯 Baseline audit complete!")

    return output_data


def main():
    parser = argparse.ArgumentParser(
        description="Run prompt baseline audit for ACE Optimizer"
    )
    parser.add_argument(
        "--models",
        type=str,
        default="qwen2.5-coder:1.5b,qwen2.5-coder:7b",
        help="Comma-separated list of model names to test",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./audit_results/prompt_baseline_audit.json",
        help="Output file path for results",
    )

    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",")]

    asyncio.run(run_baseline_audit(models, args.output))


if __name__ == "__main__":
    main()
