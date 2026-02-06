#!/usr/bin/env python3
"""
Phase 1 Baseline Testing for 1.5B/7B Model Optimization

This script runs comprehensive baseline testing using the enhanced audit framework
on the generated small model test dataset to establish quality baselines.

Usage:
    python run_phase1_baseline.py [--models MODEL_LIST] [--dataset DATASET_PATH] [--variants VARIANTS]
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from run_prompt_baseline_audit import run_baseline_audit


def load_test_dataset(dataset_path: str):
    """Load test cases from dataset file."""
    with open(dataset_path) as f:
        dataset = json.load(f)

    return dataset["test_cases"], dataset.get("metadata", {})


async def run_phase1_baseline(
    models: list[str], dataset_path: str, prompt_variants: list[str], output_file: str
):
    """
    Run Phase 1 baseline testing for 1.5B/7B model optimization.
    """

    print("🚀 Phase 1: Baseline Testing for 1.5B/7B Model Optimization")
    print("=" * 70)

    # Load test dataset
    test_cases, dataset_metadata = load_test_dataset(dataset_path)

    print("📊 Dataset Loaded:")
    print(f"   Total test cases: {len(test_cases)}")
    print(f"   Dataset path: {dataset_path}")

    if dataset_metadata:
        print(
            f"   Complexity distribution: {dataset_metadata.get('complexity_distribution', {})}"
        )
        print(
            f"   Domain distribution: {dataset_metadata.get('domain_distribution', {})}"
        )
        print(
            f"   Difficulty distribution: {dataset_metadata.get('difficulty_distribution', {})}"
        )

    print("\n🎯 Testing Configuration:")
    print(f"   Models: {models}")
    print(f"   Prompt variants: {prompt_variants}")
    print(f"   Total tests: {len(models) * len(prompt_variants) * len(test_cases)}")

    # Create results directory
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run baseline audit with our test cases
    # We'll temporarily replace the TEST_CASES in the audit script
    import run_prompt_baseline_audit

    original_test_cases = run_prompt_baseline_audit.TEST_CASES
    run_prompt_baseline_audit.TEST_CASES = test_cases

    try:
        results = await run_baseline_audit(models, output_file, prompt_variants)
    finally:
        # Restore original test cases
        run_prompt_baseline_audit.TEST_CASES = original_test_cases

    # Add dataset metadata to results
    results["dataset_metadata"] = dataset_metadata
    results["phase"] = "1_baseline"
    results["models"] = models
    results["prompt_variants"] = prompt_variants

    # Save enhanced results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ Phase 1 baseline testing completed!")
    print(f"📁 Results saved to: {output_file}")

    # Print key findings
    print("\n🎯 Key Findings:")

    for model in models:
        if model in results.get("model_aggregates", {}):
            model_data = results["model_aggregates"][model]

            # Find best performing variant for this model
            best_variant = None
            best_score = 0.0

            for variant, variant_data in model_data.items():
                quality_score = variant_data.get("avg_quality_score", 0.0)
                if quality_score > best_score:
                    best_score = quality_score
                    best_variant = variant

            if best_variant:
                variant_data = model_data[best_variant]
                print(f"\n  {model}:")
                print(f"    Best variant: {best_variant}")
                print(
                    f"    Quality score: {variant_data.get('avg_quality_score', 0):.3f}"
                )
                print(
                    f"    Entity recall: {variant_data.get('avg_entity_recall', 0):.1%}"
                )
                print(
                    f"    Relation accuracy: {variant_data.get('avg_relation_accuracy', 0):.1%}"
                )
                print(
                    f"    Execution time: {variant_data.get('avg_execution_time', 0):.2f}s"
                )

                if variant_data.get("total_tokens", 0) > 0:
                    print(
                        f"    Token efficiency: {variant_data.get('avg_token_efficiency', 0):.4f}"
                    )
                    print(
                        f"    Total cost: ${variant_data.get('total_cost_dollars', 0):.6f}"
                    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run Phase 1 baseline testing for 1.5B/7B model optimization"
    )

    parser.add_argument(
        "--models",
        type=str,
        default="qwen2.5-coder:1.5b,qwen2.5-coder:7b",
        help="Comma-separated list of models to test",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="./test_datasets/small_model_test_dataset.json",
        help="Path to test dataset JSON file",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./audit_results/phase1_baseline_results.json",
        help="Output file path for results",
    )

    parser.add_argument(
        "--variants",
        type=str,
        default="standard,small,lite",
        help="Comma-separated list of prompt variants to test",
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.dataset):
        print(f"❌ Dataset file not found: {args.dataset}")
        sys.exit(1)

    models = [m.strip() for m in args.models.split(",")]
    prompt_variants = [v.strip() for v in args.variants.split(",")]

    # Validate prompt variants
    valid_variants = {"standard", "lite", "small", "ultra_lite", "optimized"}
    for variant in prompt_variants:
        if variant not in valid_variants:
            print(f"❌ Invalid prompt variant: {variant}")
            print(f"Valid variants: {', '.join(valid_variants)}")
            sys.exit(1)

    # Run baseline testing
    asyncio.run(run_phase1_baseline(models, args.dataset, prompt_variants, args.output))


if __name__ == "__main__":
    main()
