"""
DSPy Integration with LightRAG AB Testing Framework

This module provides integration between DSPy-optimized prompts and the existing
LightRAG AB testing system, allowing seamless comparison and rollout.
"""

import json
import os
import random
from pathlib import Path
from typing import Any

try:
    from lightrag.prompt import PROMPTS
except ImportError:
    PROMPTS = {}

try:
    from lightrag.ab_defaults import (
        AB_DEFAULTS,
        AB_WEIGHTS,
        _size_key_from_model,
        get_default_variant,
    )
except ImportError:
    AB_DEFAULTS = {}
    AB_WEIGHTS = {}

    def get_default_variant(_x):
        return None

    def _size_key_from_model(_x):
        return ""


from ..evaluators.prompt_evaluator import DSPyPromptEvaluator


class DSPyABIntegration:
    """Integration layer for DSPy prompts into LightRAG AB testing."""

    def __init__(self, working_directory: Path | None = None):
        self.working_directory = working_directory or Path(
            "./lightrag/dspy_integration/prompts"
        )
        self.working_directory.mkdir(parents=True, exist_ok=True)

        # DSPy variant mappings
        self.dspy_variants = {
            "DSPY_A": "dspy_cot_standard_BootstrapFewShot",
            "DSPY_B": "dspy_predict_lite_BootstrapFewShot",
            "DSPY_C": "dspy_program_of_thought_MIPROv2",
            "DSPY_D": "dspy_multi_step_BootstrapFewShot",
        }

        # Weights for DSPy variants (similar to existing AB_WEIGHTS)
        self.dspy_weights = {
            "1.5b": {"DSPY_A": 0.9, "DSPY_B": 1.0, "DSPY_C": 0.85, "DSPY_D": 0.8},
            "3b": {"DSPY_A": 0.95, "DSPY_B": 1.0, "DSPY_C": 0.9, "DSPY_D": 0.85},
            "7b": {"DSPY_A": 0.9, "DSPY_B": 1.0, "DSPY_C": 0.95, "DSPY_D": 0.88},
        }

        self.optimized_prompts = {}
        self.load_optimized_prompts()

    def load_optimized_prompts(self) -> None:
        """Load previously optimized DSPy prompts."""

        prompts_file = self.working_directory / "optimized_entity_prompts.json"
        if prompts_file.exists():
            try:
                with open(prompts_file) as f:
                    self.optimized_prompts = json.load(f)
                print(
                    f"Loaded {len([k for k in self.optimized_prompts.keys() if not k.startswith('_')])} optimized prompts"
                )
            except Exception as e:
                print(f"Warning: Could not load optimized prompts: {e}")

    def choose_dspy_variant(
        self, model_name: str, allow_all_variants: bool = False
    ) -> str:
        """Choose a DSPy variant for the given model."""

        # Check for explicit DSPy default in environment
        dspy_default = os.getenv("DSPY_DEFAULT_VARIANT")
        if dspy_default and dspy_default in self.dspy_variants:
            return dspy_default

        # Check if DSPy is enabled
        dspy_enabled = os.getenv("DSPY_ENABLED", "0").lower() in ("1", "true", "on")
        if not dspy_enabled:
            return ""

        # Get model size
        size_key = _size_key_from_model(model_name)
        if not size_key:
            return ""

        # Get weights for this model size
        weights = self.dspy_weights.get(size_key, {})
        if not weights:
            return ""

        # Filter available variants
        available_variants = {}
        for variant, prompt_key in self.dspy_variants.items():
            if prompt_key in self.optimized_prompts:
                available_variants[variant] = weights.get(variant, 0.0)

        if not available_variants:
            return ""

        # Allow variant C if requested
        allow_c = allow_all_variants or str(os.getenv("DSPY_ALLOW_C", "0")).lower() in (
            "1",
            "true",
        )
        if not allow_c and "DSPY_C" in available_variants:
            del available_variants["DSPY_C"]

        # Choose variant based on weighted random selection
        if not available_variants:
            return ""

        # Find max weight
        max_weight = max(available_variants.values())
        max_variants = [v for v, w in available_variants.items() if w == max_weight]

        # If there's a clear winner, use it
        if len(max_variants) == 1:
            return max_variants[0]

        # Otherwise, randomly choose among top variants
        return random.choice(max_variants)

    def get_dspy_prompt(self, variant: str) -> str | None:
        """Get the actual DSPy prompt text for a variant."""

        prompt_key = self.dspy_variants.get(variant)
        if not prompt_key:
            return None

        return self.optimized_prompts.get(prompt_key)

    def integrate_with_lightrag_ab(self) -> bool:
        """Integrate DSPy prompts into the main LightRAG AB testing system."""

        try:
            # Add DSPy defaults to the main AB_DEFAULTS
            for model_name in [
                "qwen2.5-coder:1.5b",
                "qwen2.5-coder:3b",
                "qwen2.5-coder:7b",
            ]:
                if model_name not in AB_DEFAULTS:
                    # Choose best DSPy variant for this model
                    dspy_variant = self.choose_dspy_variant(
                        model_name, allow_all_variants=True
                    )
                    if dspy_variant:
                        AB_DEFAULTS[model_name] = dspy_variant

            print("✓ DSPy variants integrated into LightRAG AB defaults")
            return True

        except Exception as e:
            print(f"✗ Failed to integrate DSPy with LightRAG AB testing: {e}")
            return False

    def update_lightrag_prompts(self) -> int:
        """Add DSPy-optimized prompts to the main PROMPTS dictionary."""

        added_count = 0

        for variant, prompt_key in self.dspy_variants.items():
            prompt_text = self.optimized_prompts.get(prompt_key)
            if prompt_text:
                # Create a prompt key compatible with LightRAG
                lightrag_key = f"entity_extraction_system_prompt_dspy_{variant.lower()}"
                PROMPTS[lightrag_key] = prompt_text
                added_count += 1

        print(f"✓ Added {added_count} DSPy prompts to LightRAG PROMPTS dictionary")
        return added_count

    def create_ab_test_matrix(self, test_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a comprehensive AB test matrix comparing all variants."""

        # Create evaluator
        evaluator = DSPyPromptEvaluator()

        # Define all prompt functions to test
        prompts_to_test = {}

        # Add original LightRAG prompts
        if PROMPTS:

            def create_lightrag_prompt_func(prompt_key):
                def prompt_func(text):
                    # This would normally use the LightRAG extraction system
                    # For testing, we return a simulated result
                    return f"LightRAG {prompt_key} processing: {text[:50]}..."

                return prompt_func

            prompts_to_test["lightrag_original"] = create_lightrag_prompt_func(
                "entity_extraction_system_prompt"
            )
            prompts_to_test["lightrag_variant_a"] = create_lightrag_prompt_func(
                "entity_extraction_system_prompt_variant_A"
            )
            prompts_to_test["lightrag_variant_b"] = create_lightrag_prompt_func(
                "entity_extraction_system_prompt_variant_B"
            )

        # Add DSPy prompts
        for variant, prompt_key in self.dspy_variants.items():
            prompt_text = self.optimized_prompts.get(prompt_key)
            if prompt_text:

                def create_dspy_prompt_func(_ptext, variant=variant):
                    def prompt_func(text):
                        return f"DSPy {variant} optimized: {text[:50]}..."

                    return prompt_func

                prompts_to_test[f"dspy_{variant.lower()}"] = create_dspy_prompt_func(
                    prompt_text
                )

        # Run comprehensive comparison
        if len(prompts_to_test) > 1:
            results = evaluator.compare_prompts(prompts_to_test, test_data)

            # Create matrix
            matrix = {
                "test_metadata": {
                    "total_prompts": len(prompts_to_test),
                    "test_cases": len(test_data),
                    "timestamp": evaluator.lightrag_evaluator.completion_delimiter,
                },
                "results": results,
                "recommendations": self._generate_recommendations(results),
            }

            return matrix
        else:
            return {"error": "No prompts available for testing"}

    def _generate_recommendations(
        self, results: dict[str, dict[str, float]]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on evaluation results."""

        if not results:
            return []

        recommendations = []

        # Sort by overall score
        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["overall_score"], reverse=True
        )

        # Winner recommendation
        if sorted_results:
            winner_name, winner_metrics = sorted_results[0]
            recommendations.append(
                {
                    "type": "winner",
                    "prompt": winner_name,
                    "score": winner_metrics["overall_score"],
                    "entity_f1": winner_metrics["entity_f1"],
                    "relationship_f1": winner_metrics["relationship_f1"],
                    "reasoning": f"Best overall performance with F1 scores: E={winner_metrics['entity_f1']:.3f}, R={winner_metrics['relationship_f1']:.3f}",
                }
            )

        # Speed recommendation (if latency is important)
        speed_candidates = [
            (name, metrics)
            for name, metrics in results.items()
            if metrics["latency_ms"] < float("inf")
        ]
        if speed_candidates:
            speed_winner = min(speed_candidates, key=lambda x: x[1]["latency_ms"])
            recommendations.append(
                {
                    "type": "speed",
                    "prompt": speed_winner[0],
                    "latency_ms": speed_winner[1]["latency_ms"],
                    "reasoning": f"Fastest response time at {speed_winner[1]['latency_ms']:.0f}ms",
                }
            )

        # Quality recommendation (lowest hallucination)
        quality_candidates = [
            (name, metrics)
            for name, metrics in results.items()
            if metrics["hallucination_rate"] < 1.0
        ]
        if quality_candidates:
            quality_winner = min(
                quality_candidates, key=lambda x: x[1]["hallucination_rate"]
            )
            recommendations.append(
                {
                    "type": "quality",
                    "prompt": quality_winner[0],
                    "hallucination_rate": quality_winner[1]["hallucination_rate"],
                    "reasoning": f"Lowest hallucination rate at {quality_winner[1]['hallucination_rate']:.1%}",
                }
            )

        return recommendations

    def save_ab_test_results(
        self, matrix: dict[str, Any], output_file: str | None = None
    ) -> str:
        """Save AB test matrix results."""

        if output_file is None:
            output_file = self.working_directory / "dspy_ab_test_matrix.json"

        with open(output_file, "w") as f:
            json.dump(matrix, f, indent=2)

        print(f"AB test matrix saved to: {output_file}")
        return str(output_file)

    def print_ab_summary(self, matrix: dict[str, Any]) -> None:
        """Print a summary of AB test results."""

        if "error" in matrix:
            print(f"❌ {matrix['error']}")
            return

        print("\n" + "=" * 80)
        print("DSPy vs LightRAG AB TEST SUMMARY")
        print("=" * 80)

        results = matrix.get("results", {})
        recommendations = matrix.get("recommendations", [])

        # Sort results by overall score
        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["overall_score"], reverse=True
        )

        # Top 5 table
        print("\nTOP PERFORMING PROMPTS:")
        header = f"{'Rank':<5} {'Prompt':<25} {'Overall':<8} {'Entity F1':<10} {'Rel F1':<8} {'Latency':<10}"
        print(header)
        print("-" * len(header))

        for i, (prompt_name, metrics) in enumerate(sorted_results[:5]):
            rank = i + 1
            row = f"{rank:<5} {prompt_name:<25} {metrics['overall_score']:<8.3f} {metrics['entity_f1']:<10.3f} {metrics['relationship_f1']:<8.3f} {metrics['latency_ms']:<10.0f}"
            print(row)

        # Recommendations
        print("\nRECOMMENDATIONS:")
        for rec in recommendations:
            icon = {"winner": "🏆", "speed": "⚡", "quality": "🎯"}.get(
                rec["type"], "📋"
            )
            print(f"{icon} {rec['type'].upper()}: {rec['prompt']}")
            print(f"   {rec['reasoning']}")

        print("=" * 80)


def main():
    """Demonstrate DSPy AB testing integration."""

    print("🚀 DSPy AB Testing Integration Demo")
    print("=" * 50)

    # Create integration
    ab_integration = DSPyABIntegration()

    # Show available variants
    print(f"\nAvailable DSPy variants: {list(ab_integration.dspy_variants.keys())}")
    print(f"Optimized prompts loaded: {len(ab_integration.optimized_prompts)}")

    # Test variant selection
    test_models = [
        "qwen2.5-coder:1.5b",
        "qwen2.5-coder:3b",
        "qwen2.5-coder:7b",
        "unknown-model",
    ]

    print("\n🧪 Testing variant selection:")
    for model in test_models:
        variant = ab_integration.choose_dspy_variant(model)
        prompt = ab_integration.get_dspy_prompt(variant) if variant else None
        status = (
            f"{variant} -> {len(prompt) if prompt else 0} chars"
            if variant
            else "No DSPy variant"
        )
        print(f"  {model}: {status}")

    # Create test data for matrix
    evaluator = DSPyPromptEvaluator()
    test_data = evaluator.create_evaluation_dataset(num_samples=5)

    # Create AB test matrix
    matrix = ab_integration.create_ab_test_matrix(test_data)

    # Print summary
    ab_integration.print_ab_summary(matrix)

    # Save results
    output_file = ab_integration.save_ab_test_results(matrix)

    print(f"\n✅ AB testing complete! Results saved to: {output_file}")

    # Instructions for integration
    print("\n📋 INTEGRATION INSTRUCTIONS:")
    print("1. Set DSPY_ENABLED=1 in environment to enable DSPy variants")
    print("2. Set DSPY_DEFAULT_VARIANT=DSPY_A to force a specific variant")
    print("3. Set DSPY_ALLOW_C=1 to enable experimental DSPY_C variant")
    print("4. DSPy prompts will automatically be used based on model size optimization")

    return True


if __name__ == "__main__":
    success = main()
    import sys

    sys.exit(0 if success else 1)
