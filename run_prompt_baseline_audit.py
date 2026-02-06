#!/usr/bin/env python3
"""
Enhanced Prompt Baseline Audit for 1.5B/7B Model Optimization (Phase 1)

This script benchmarks extraction quality across different model sizes (1.5B, 7B)
to establish baseline metrics for prompt optimization with comprehensive token tracking.

Enhanced metrics measured:
- Entity recall (% of expected entities extracted)
- Relationship accuracy (% of expected relationships extracted)
- YAML compliance rate (% of valid YAML outputs)
- Hallucination frequency (% of unexpected entities)
- Execution time per extraction
- Token efficiency metrics (prompt/completion/total tokens)
- Cost optimization tracking
- Quality preservation scores

Usage:
    python run_prompt_baseline_audit.py [--models MODEL1,MODEL2] [--output OUTPUT_FILE] [--prompt-variants]

Examples:
    python run_prompt_baseline_audit.py --models qwen2.5-coder:1.5b,qwen2.5-coder:7b
    python run_prompt_baseline_audit.py --models qwen2.5-coder:1.5b --prompt-variants --keep-storage
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
from lightrag.operate import parse_model_size
from lightrag.utils import EmbeddingFunc
from lightrag.utils.token_tracker import get_token_tracker

# Comprehensive test cases with ground truth for 1.5B/7B model testing
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
        "complexity": "low",
        "text_tokens_estimated": 6,
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
        "complexity": "medium",
        "text_tokens_estimated": 25,
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
        "complexity": "high",
        "text_tokens_estimated": 35,
    },
    {
        "id": "tech_startup_ecosystem",
        "text": (
            "Silicon Valley hosts numerous tech companies including Google, Meta, and Apple. "
            "Startups like OpenAI and Anthropic compete in the AI space, while venture capital firms "
            "such as Sequoia Capital and Andreessen Horowitz provide funding. Engineers from Stanford "
            "University often join these companies after graduation."
        ),
        "expected_entities": [
            {"name": "Silicon Valley", "type": "Location"},
            {"name": "Google", "type": "Organization"},
            {"name": "Meta", "type": "Organization"},
            {"name": "Apple", "type": "Organization"},
            {"name": "OpenAI", "type": "Organization"},
            {"name": "Anthropic", "type": "Organization"},
            {"name": "Sequoia Capital", "type": "Organization"},
            {"name": "Andreessen Horowitz", "type": "Organization"},
            {"name": "Stanford University", "type": "Organization"},
        ],
        "expected_relations": [
            {
                "source": "Google",
                "target": "Silicon Valley",
                "keywords": ["hosts", "located"],
            },
            {
                "source": "Meta",
                "target": "Silicon Valley",
                "keywords": ["hosts", "located"],
            },
            {
                "source": "Apple",
                "target": "Silicon Valley",
                "keywords": ["hosts", "located"],
            },
            {
                "source": "OpenAI",
                "target": "AI space",
                "keywords": ["compete", "competing"],
            },
            {
                "source": "Anthropic",
                "target": "AI space",
                "keywords": ["compete", "competing"],
            },
            {
                "source": "Sequoia Capital",
                "target": "startups",
                "keywords": ["provide", "funding"],
            },
            {
                "source": "Andreessen Horowitz",
                "target": "startups",
                "keywords": ["provide", "funding"],
            },
            {
                "source": "Engineers",
                "target": "Stanford University",
                "keywords": ["from", "graduate"],
            },
            {
                "source": "Engineers",
                "target": "tech companies",
                "keywords": ["join", "work"],
            },
        ],
        "complexity": "high",
        "text_tokens_estimated": 45,
    },
    {
        "id": "scientific_discovery",
        "text": (
            "Marie Curie discovered radioactivity while working at the University of Paris. "
            "Her research on radium and polonium earned two Nobel Prizes, one in Physics and another in Chemistry. "
            "She collaborated with her husband Pierre Curie, and their work laid the foundation for nuclear physics."
        ),
        "expected_entities": [
            {"name": "Marie Curie", "type": "Person"},
            {"name": "Pierre Curie", "type": "Person"},
            {"name": "University of Paris", "type": "Organization"},
            {"name": "radioactivity", "type": "Concept"},
            {"name": "radium", "type": "Concept"},
            {"name": "polonium", "type": "Concept"},
            {"name": "Nobel Prizes", "type": "Event"},
            {"name": "Physics", "type": "Concept"},
            {"name": "Chemistry", "type": "Concept"},
            {"name": "nuclear physics", "type": "Concept"},
        ],
        "expected_relations": [
            {
                "source": "Marie Curie",
                "target": "radioactivity",
                "keywords": ["discovered"],
            },
            {
                "source": "Marie Curie",
                "target": "University of Paris",
                "keywords": ["working", "at"],
            },
            {
                "source": "Marie Curie",
                "target": "radium",
                "keywords": ["research", "on"],
            },
            {
                "source": "Marie Curie",
                "target": "polonium",
                "keywords": ["research", "on"],
            },
            {"source": "Marie Curie", "target": "Nobel Prizes", "keywords": ["earned"]},
            {"source": "Nobel Prizes", "target": "Physics", "keywords": ["in"]},
            {"source": "Nobel Prizes", "target": "Chemistry", "keywords": ["in"]},
            {
                "source": "Marie Curie",
                "target": "Pierre Curie",
                "keywords": ["collaborated", "with"],
            },
            {
                "source": "Pierre Curie",
                "target": "nuclear physics",
                "keywords": ["laid", "foundation"],
            },
        ],
        "complexity": "medium",
        "text_tokens_estimated": 38,
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


async def run_extraction_test(
    model_name: str,
    case: dict,
    working_dir: str,
    prompt_variant: str = "standard",
    track_tokens: bool = True,
) -> dict:
    """
    Run entity extraction on a single test case with a specific model and prompt variant.

    Args:
        model_name: Model to test (e.g., "qwen2.5-coder:1.5b")
        case: Test case dictionary with text and expected outputs
        working_dir: Directory for RAG storage
        prompt_variant: Prompt variant to test ("standard", "lite", "small", "ultra_lite")
        track_tokens: Whether to track token usage

    Returns:
        dict with metrics: entity_recall, relation_accuracy, execution_time, token_metrics, etc.
    """
    # Ensure a fresh directory
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(working_dir)

    # Configure extraction based on model size and prompt variant
    model_size = parse_model_size(model_name)
    is_small_model = model_size is not None and model_size <= 8.0

    # Configure extraction parameters
    if prompt_variant == "ultra_lite":
        lite_extraction = True
        extraction_format = "key_value"
        max_gleaning = 2 if is_small_model else 1
        cot_depth = "minimal"
    elif prompt_variant == "lite":
        lite_extraction = True
        extraction_format = "key_value"
        max_gleaning = 2 if is_small_model else 1
        cot_depth = "minimal"
    elif prompt_variant == "small":
        lite_extraction = False
        extraction_format = "standard"
        max_gleaning = 1
        cot_depth = "standard"
    elif prompt_variant == "optimized":
        lite_extraction = False
        extraction_format = "standard"
        max_gleaning = 1
        cot_depth = "standard"
    else:  # standard
        lite_extraction = False
        extraction_format = "yaml"
        max_gleaning = 1
        cot_depth = "standard"

    # Reset token tracker for this test
    token_tracker = get_token_tracker()
    if track_tokens:
        token_tracker.reset()

    # Initialize LightRAG with working configuration
    rag = LightRAG(
        working_dir=working_dir,
        llm_model_name=model_name,
        extraction_format=extraction_format,
        entity_extract_max_gleaning=max_gleaning,
        lite_extraction=lite_extraction,
        addon_params={
            "entity_types": [
                "Person",
                "Location",
                "Organization",
                "Concept",
                "Theory",
                "Event",
                "Location",
                "Object",
            ],
            "cot_depth": cot_depth,
            "cot_enabled": True,
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
        print(f"      [DEBUG] Starting ainsert for {case['id']}...")
        await rag.ainsert(case["text"])
        execution_time = time.time() - start_time
        print(f"      [DEBUG] ainsert completed in {execution_time:.4f}s")
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

    # Get token usage metrics
    token_metrics = {}
    if track_tokens and token_tracker.is_enabled:
        token_summary = token_tracker.get_summary()
        extraction_stats = token_tracker.get_operation_stats("entity_extraction")
        token_metrics = {
            "total_tokens": token_summary["total_tokens"],
            "prompt_tokens": token_summary["total_prompt_tokens"],
            "completion_tokens": token_summary["total_completion_tokens"],
            "estimated_cost_dollars": token_summary["estimated_cost_dollars"],
            "avg_tokens_per_extraction": extraction_stats["avg_total_tokens"],
            "token_efficiency_score": len(case["expected_entities"])
            / max(token_summary["total_tokens"], 1),
        }

    # Calculate quality preservation score
    quality_score = (
        (entity_recall * 0.4 + relation_accuracy * 0.4 + (1 - hallucination_rate) * 0.2)
        if yaml_compliant
        else 0.0
    )

    return {
        "case_id": case["id"],
        "model": model_name,
        "prompt_variant": prompt_variant,
        "model_size_gb": model_size,
        "yaml_compliant": yaml_compliant,
        "execution_time": execution_time,
        "entity_recall": entity_recall,
        "relation_accuracy": relation_accuracy,
        "hallucination_rate": hallucination_rate,
        "quality_preservation_score": quality_score,
        "entities_found": found_entities,
        "entities_expected": len(case["expected_entities"]),
        "entities_extracted": len(entities),
        "relations_found": found_relations,
        "relations_expected": len(case["expected_relations"]),
        "text_complexity": case.get("complexity", "unknown"),
        "text_tokens_estimated": case.get("text_tokens_estimated", 0),
        **token_metrics,
    }


async def run_baseline_audit(
    models: list[str],
    output_file: str,
    prompt_variants: list[str] | None = None,
    track_tokens: bool = True,
):
    """
    Run enhanced baseline audit across all models, prompt variants, and test cases.

    Args:
        models: List of model names to test
        output_file: Path to save results JSON
        prompt_variants: List of prompt variants to test ("standard", "lite", "small", "ultra_lite")
        track_tokens: Whether to track token usage
    """
    if prompt_variants is None:
        prompt_variants = ["standard"]
    results = []
    timestamp = datetime.now().isoformat()

    print(f"\n🚀 Starting Enhanced Prompt Baseline Audit - {timestamp}")
    print(
        f"📋 Testing {len(models)} models × {len(prompt_variants)} prompt variants × {len(TEST_CASES)} test cases"
    )
    print(f"🔍 Total tests: {len(models) * len(prompt_variants) * len(TEST_CASES)}\n")

    for model in models:
        model_size = parse_model_size(model)
        print(f"\n{'=' * 80}")
        print(f"Testing Model: {model} (Size: {model_size}B)")
        print(f"{'=' * 80}\n")

        for variant in prompt_variants:
            print(f"  📝 Prompt Variant: {variant}")
            print(f"  {'-' * 40}")

            for case in TEST_CASES:
                print(
                    f"    📋 Case: {case['id']} ({case.get('complexity', 'unknown')} complexity)..."
                )
                working_dir = f"./rag_storage_audit_{model.replace(':', '_')}_{variant}_{case['id']}"

                result = await run_extraction_test(
                    model, case, working_dir, variant, track_tokens
                )
                results.append(result)

                # Print enhanced summary
                print(f"      ✓ Entity Recall: {result['entity_recall']:.1%}")
                print(f"      ✓ Relation Accuracy: {result['relation_accuracy']:.1%}")
                print(f"      ✓ Hallucination Rate: {result['hallucination_rate']:.1%}")
                print(
                    f"      ✓ Quality Score: {result['quality_preservation_score']:.3f}"
                )
                print(f"      ✓ Execution Time: {result['execution_time']:.2f}s")

                if track_tokens and result.get("total_tokens", 0) > 0:
                    print(
                        f"      ✓ Token Efficiency: {result.get('token_efficiency_score', 0):.4f}"
                    )
                    print(f"      ✓ Total Tokens: {result.get('total_tokens', 0)}")
                    print(
                        f"      ✓ Cost Est: ${result.get('estimated_cost_dollars', 0):.6f}"
                    )

                print(f"      ✓ YAML Compliant: {result['yaml_compliant']}\n")

                # Cleanup
                if not os.getenv("KEEP_STORAGE") and os.path.exists(working_dir):
                    shutil.rmtree(working_dir)

    # Calculate enhanced aggregate metrics per model and variant
    print(f"\n{'=' * 80}")
    print("📊 Enhanced Aggregate Results")
    print(f"{'=' * 80}\n")

    model_aggregates = {}
    variant_aggregates = {}

    for model in models:
        model_size = parse_model_size(model)
        print(f"🎯 Model: {model} ({model_size}B)")
        print(f"{'-' * 50}")

        model_variants = {}
        for variant in prompt_variants:
            variant_results = [
                r
                for r in results
                if r["model"] == model and r["prompt_variant"] == variant
            ]

            if not variant_results:
                continue

            avg_entity_recall = sum(r["entity_recall"] for r in variant_results) / len(
                variant_results
            )
            avg_relation_accuracy = sum(
                r["relation_accuracy"] for r in variant_results
            ) / len(variant_results)
            avg_hallucination_rate = sum(
                r["hallucination_rate"] for r in variant_results
            ) / len(variant_results)
            avg_quality_score = sum(
                r["quality_preservation_score"] for r in variant_results
            ) / len(variant_results)
            avg_execution_time = sum(
                r["execution_time"] for r in variant_results
            ) / len(variant_results)
            yaml_compliance_rate = sum(
                1 for r in variant_results if r["yaml_compliant"]
            ) / len(variant_results)

            # Token metrics (if available)
            token_metrics = {}
            if track_tokens and any(
                r.get("total_tokens", 0) > 0 for r in variant_results
            ):
                total_tokens = sum(r.get("total_tokens", 0) for r in variant_results)
                total_cost = sum(
                    r.get("estimated_cost_dollars", 0) for r in variant_results
                )
                avg_efficiency = sum(
                    r.get("token_efficiency_score", 0) for r in variant_results
                ) / len(variant_results)

                token_metrics = {
                    "total_tokens": total_tokens,
                    "avg_tokens_per_test": total_tokens / len(variant_results),
                    "total_cost_dollars": total_cost,
                    "avg_token_efficiency": avg_efficiency,
                }

            variant_data = {
                "avg_entity_recall": avg_entity_recall,
                "avg_relation_accuracy": avg_relation_accuracy,
                "avg_hallucination_rate": avg_hallucination_rate,
                "avg_quality_score": avg_quality_score,
                "avg_execution_time": avg_execution_time,
                "yaml_compliance_rate": yaml_compliance_rate,
                "test_count": len(variant_results),
                **token_metrics,
            }

            model_variants[variant] = variant_data

            # Print variant results
            print(f"  📝 {variant.title()} Variant:")
            print(f"    Quality Score: {avg_quality_score:.3f}")
            print(f"    Entity Recall: {avg_entity_recall:.1%}")
            print(f"    Relation Accuracy: {avg_relation_accuracy:.1%}")
            print(f"    Hallucination Rate: {avg_hallucination_rate:.1%}")
            print(f"    YAML Compliance: {yaml_compliance_rate:.1%}")
            print(f"    Execution Time: {avg_execution_time:.2f}s")

            if token_metrics:
                print(
                    f"    Token Efficiency: {token_metrics['avg_token_efficiency']:.4f}"
                )
                print(f"    Avg Tokens: {token_metrics['avg_tokens_per_test']:.0f}")
                print(f"    Cost: ${token_metrics['total_cost_dollars']:.6f}")
            print()

        model_aggregates[model] = model_variants

    # Best variant recommendations
    print("🏆 Best Variant Recommendations:")
    print(f"{'=' * 50}")

    for model in models:
        print(f"\n{model}:")
        best_quality = max(
            (
                (variant, data["avg_quality_score"])
                for variant, data in model_aggregates[model].items()
            ),
            key=lambda x: x[1],
        )
        best_efficiency = max(
            (
                (variant, data.get("avg_token_efficiency", 0))
                for variant, data in model_aggregates[model].items()
            ),
            key=lambda x: x[1],
        )

        print(f"  Best Quality: {best_quality[0]} ({best_quality[1]:.3f})")
        print(f"  Most Efficient: {best_efficiency[0]} ({best_efficiency[1]:.4f})")

    # Save enhanced results
    output_data = {
        "timestamp": timestamp,
        "models_tested": models,
        "prompt_variants_tested": prompt_variants,
        "test_cases": [c["id"] for c in TEST_CASES],
        "individual_results": results,
        "model_aggregates": model_aggregates,
        "variant_aggregates": variant_aggregates,
        "config": {
            "track_tokens": track_tokens,
            "total_tests": len(models) * len(prompt_variants) * len(TEST_CASES),
        },
        "test_case_metadata": {
            c["id"]: {
                "complexity": c.get("complexity", "unknown"),
                "text_tokens_estimated": c.get("text_tokens_estimated", 0),
                "entities_expected": len(c["expected_entities"]),
                "relations_expected": len(c["expected_relations"]),
            }
            for c in TEST_CASES
        },
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Enhanced results saved to: {output_file}")
    print("\n🎯 Enhanced baseline audit complete!")
    print(
        f"📈 Summary: {len(results)} tests executed across {len(models)} models and {len(prompt_variants)} prompt variants"
    )

    return output_data


def main():
    parser = argparse.ArgumentParser(
        description="Run enhanced prompt baseline audit for 1.5B/7B model optimization"
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
        default="./audit_results/enhanced_prompt_baseline_audit.json",
        help="Output file path for results",
    )
    parser.add_argument(
        "--keep-storage",
        action="store_true",
        help="Do not delete the RAG storage directories after testing",
    )
    parser.add_argument(
        "--prompt-variants",
        type=str,
        default="standard",
        help="Comma-separated list of prompt variants to test (standard, lite, small, ultra_lite)",
    )
    parser.add_argument(
        "--no-token-tracking",
        action="store_true",
        help="Disable token usage tracking",
    )

    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",")]
    prompt_variants = [v.strip() for v in args.prompt_variants.split(",")]

    # Validate prompt variants
    valid_variants = {"standard", "lite", "small", "ultra_lite"}
    for variant in prompt_variants:
        if variant not in valid_variants:
            print(f"❌ Invalid prompt variant: {variant}")
            print(f"Valid variants: {', '.join(valid_variants)}")
            return

    if args.keep_storage:
        os.environ["KEEP_STORAGE"] = "True"

    track_tokens = not args.no_token_tracking

    asyncio.run(run_baseline_audit(models, args.output, prompt_variants, track_tokens))


if __name__ == "__main__":
    main()
