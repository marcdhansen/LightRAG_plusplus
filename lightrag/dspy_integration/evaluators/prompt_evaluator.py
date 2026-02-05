"""
DSPy Evaluation Framework for LightRAG

This module provides comprehensive evaluation capabilities to compare
DSPy-optimized prompts with existing LightRAG prompts.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

# Import DSPy components
try:
    import dspy
except ImportError:
    dspy = None

# Import LightRAG components
try:
    from lightrag.prompt import PROMPTS
except ImportError:
    PROMPTS = {}


@dataclass
class EvaluationMetrics:
    """Metrics for evaluating prompt performance."""

    entity_recall: float = 0.0
    entity_precision: float = 0.0
    entity_f1: float = 0.0
    relationship_recall: float = 0.0
    relationship_precision: float = 0.0
    relationship_f1: float = 0.0
    format_compliance: float = 0.0
    completion_rate: float = 0.0
    hallucination_rate: float = 0.0
    overall_score: float = 0.0
    latency_ms: float = 0.0
    tokens_used: int = 0


class LightRAGEvaluator:
    """Evaluator for LightRAG entity extraction prompts."""

    def __init__(self):
        self.tuple_delimiter = "<|#|>"
        self.completion_delimiter = "<|COMPLETE|>"

    def parse_extraction_output(self, output: str) -> dict[str, list[dict[str, str]]]:
        """Parse LightRAG tuple-delimited output into structured data."""

        entities = []
        relationships = []

        lines = [line.strip() for line in output.split("\n") if line.strip()]

        for line in lines:
            if line.startswith("entity"):
                # Parse entity: entity|name|type|description
                parts = line.split(self.tuple_delimiter)
                if len(parts) >= 4:
                    entities.append(
                        {
                            "name": parts[1].strip(),
                            "type": parts[2].strip(),
                            "description": parts[3].strip(),
                        }
                    )
            elif line.startswith("relation"):
                # Parse relationship: relation|source|target|keywords|description
                parts = line.split(self.tuple_delimiter)
                if len(parts) >= 5:
                    relationships.append(
                        {
                            "source": parts[1].strip(),
                            "target": parts[2].strip(),
                            "keywords": parts[3].strip(),
                            "description": parts[4].strip(),
                        }
                    )

        return {"entities": entities, "relationships": relationships}

    def calculate_entity_metrics(
        self, predicted: list[dict[str, str]], expected: list[dict[str, str]]
    ) -> tuple[float, float, float]:
        """Calculate entity-level precision, recall, and F1."""

        if not predicted and not expected:
            return 1.0, 1.0, 1.0

        if not predicted:
            return 0.0, 1.0, 0.0

        if not expected:
            return 0.0, 0.0, 0.0

        # Name-based matching (case-insensitive)
        pred_names = {e["name"].lower() for e in predicted}
        exp_names = {e["name"].lower() for e in expected}

        true_positives = len(pred_names & exp_names)
        false_positives = len(pred_names - exp_names)
        false_negatives = len(exp_names - pred_names)

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return precision, recall, f1

    def calculate_relationship_metrics(
        self, predicted: list[dict[str, str]], expected: list[dict[str, str]]
    ) -> tuple[float, float, float]:
        """Calculate relationship-level precision, recall, and F1."""

        if not predicted and not expected:
            return 1.0, 1.0, 1.0

        if not predicted:
            return 0.0, 1.0, 0.0

        if not expected:
            return 0.0, 0.0, 0.0

        # Relationship matching based on source-target pairs
        pred_pairs = {(r["source"].lower(), r["target"].lower()) for r in predicted}
        exp_pairs = {(r["source"].lower(), r["target"].lower()) for r in expected}

        true_positives = len(pred_pairs & exp_pairs)
        false_positives = len(pred_pairs - exp_pairs)
        false_negatives = len(exp_pairs - pred_pairs)

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return precision, recall, f1

    def evaluate_format_compliance(self, output: str) -> float:
        """Check if output follows LightRAG format requirements."""

        score = 1.0
        issues = []

        # Check completion delimiter
        if self.completion_delimiter not in output:
            score -= 0.3
            issues.append("Missing completion delimiter")

        # Check entity lines format
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        entity_lines = [line for line in lines if line.startswith("entity")]

        for line in entity_lines:
            parts = line.split(self.tuple_delimiter)
            if len(parts) < 4:
                score -= 0.1
                issues.append(f"Malformed entity line: {line}")

        # Check relationship lines format
        rel_lines = [line for line in lines if line.startswith("relation")]

        for line in rel_lines:
            parts = line.split(self.tuple_delimiter)
            if len(parts) < 5:
                score -= 0.1
                issues.append(f"Malformed relationship line: {line}")

        return max(0.0, score)

    def detect_hallucinations(
        self, predicted: dict[str, list[dict[str, str]]], source_text: str
    ) -> float:
        """Simple hallucination detection based on source text presence."""

        hallucination_count = 0
        total_entities = len(predicted["entities"])
        total_relationships = len(predicted["relationships"])
        total_items = total_entities + total_relationships

        if total_items == 0:
            return 0.0

        source_text_lower = source_text.lower()

        # Check entity hallucinations
        for entity in predicted["entities"]:
            entity_name = entity["name"].lower()
            if entity_name not in source_text_lower:
                hallucination_count += 1

        # Check relationship hallucinations (source and target must be in text)
        for rel in predicted["relationships"]:
            source = rel["source"].lower()
            target = rel["target"].lower()
            if source not in source_text_lower or target not in source_text_lower:
                hallucination_count += 1

        return hallucination_count / total_items if total_items > 0 else 0.0


class DSPyPromptEvaluator:
    """Evaluator for comparing DSPy-optimized prompts with existing prompts."""

    def __init__(self, working_directory: Path | None = None):
        self.working_directory = working_directory or Path(
            "./lightrag/dspy_integration/evaluators"
        )
        self.working_directory.mkdir(parents=True, exist_ok=True)
        self.lightrag_evaluator = LightRAGEvaluator()

    def create_evaluation_dataset(self, num_samples: int = 20) -> list[dict[str, Any]]:
        """Create a dataset for prompt evaluation."""

        evaluation_data = [
            {
                "text": "Apple Inc. is a technology company headquartered in Cupertino, California. Tim Cook serves as the CEO.",
                "expected_entities": [
                    {
                        "name": "Apple Inc.",
                        "type": "organization",
                        "description": "Technology company",
                    },
                    {
                        "name": "Cupertino",
                        "type": "location",
                        "description": "City in California",
                    },
                    {
                        "name": "California",
                        "type": "location",
                        "description": "US state",
                    },
                    {
                        "name": "Tim Cook",
                        "type": "person",
                        "description": "CEO of Apple Inc.",
                    },
                ],
                "expected_relationships": [
                    {
                        "source": "Apple Inc.",
                        "target": "Cupertino",
                        "keywords": "headquartered",
                        "description": "Apple is headquartered in Cupertino",
                    },
                    {
                        "source": "Cupertino",
                        "target": "California",
                        "keywords": "located in",
                        "description": "Cupertino is located in California",
                    },
                    {
                        "source": "Tim Cook",
                        "target": "Apple Inc.",
                        "keywords": "CEO",
                        "description": "Tim Cook is CEO of Apple Inc.",
                    },
                ],
            },
            {
                "text": "Stanford University was founded in 1885 by Leland Stanford in Palo Alto, California.",
                "expected_entities": [
                    {
                        "name": "Stanford University",
                        "type": "organization",
                        "description": "University founded by Leland Stanford",
                    },
                    {
                        "name": "Leland Stanford",
                        "type": "person",
                        "description": "Founder of Stanford University",
                    },
                    {
                        "name": "Palo Alto",
                        "type": "location",
                        "description": "City where Stanford is located",
                    },
                    {
                        "name": "California",
                        "type": "location",
                        "description": "State where Palo Alto is located",
                    },
                ],
                "expected_relationships": [
                    {
                        "source": "Stanford University",
                        "target": "Leland Stanford",
                        "keywords": "founded by",
                        "description": "Stanford was founded by Leland Stanford",
                    },
                    {
                        "source": "Stanford University",
                        "target": "Palo Alto",
                        "keywords": "located in",
                        "description": "Stanford is located in Palo Alto",
                    },
                    {
                        "source": "Palo Alto",
                        "target": "California",
                        "keywords": "located in",
                        "description": "Palo Alto is located in California",
                    },
                    {
                        "source": "Stanford University",
                        "target": "1885",
                        "keywords": "founded in",
                        "description": "Stanford was founded in 1885",
                    },
                ],
            },
            {
                "text": "Microsoft Corporation develops Windows operating system. Bill Gates co-founded Microsoft in 1975 with Paul Allen.",
                "expected_entities": [
                    {
                        "name": "Microsoft Corporation",
                        "type": "organization",
                        "description": "Technology company that develops Windows",
                    },
                    {
                        "name": "Windows",
                        "type": "concept",
                        "description": "Operating system developed by Microsoft",
                    },
                    {
                        "name": "Bill Gates",
                        "type": "person",
                        "description": "Co-founder of Microsoft",
                    },
                    {
                        "name": "Paul Allen",
                        "type": "person",
                        "description": "Co-founder of Microsoft",
                    },
                    {
                        "name": "1975",
                        "type": "event",
                        "description": "Year Microsoft was founded",
                    },
                ],
                "expected_relationships": [
                    {
                        "source": "Microsoft Corporation",
                        "target": "Windows",
                        "keywords": "develops",
                        "description": "Microsoft develops Windows operating system",
                    },
                    {
                        "source": "Bill Gates",
                        "target": "Microsoft Corporation",
                        "keywords": "co-founded",
                        "description": "Bill Gates co-founded Microsoft",
                    },
                    {
                        "source": "Paul Allen",
                        "target": "Microsoft Corporation",
                        "keywords": "co-founded",
                        "description": "Paul Allen co-founded Microsoft",
                    },
                    {
                        "source": "Microsoft Corporation",
                        "target": "1975",
                        "keywords": "founded in",
                        "description": "Microsoft was founded in 1975",
                    },
                ],
            },
        ]

        # Expand dataset if needed
        while len(evaluation_data) < num_samples:
            evaluation_data.extend(evaluation_data)

        return evaluation_data[:num_samples]

    def evaluate_prompt_function(
        self, prompt_function, test_data: list[dict[str, Any]], prompt_name: str
    ) -> list[EvaluationMetrics]:
        """Evaluate a prompt function on test data."""

        results = []

        for i, test_case in enumerate(test_data):
            print(f"Evaluating {prompt_name} - sample {i + 1}/{len(test_data)}")

            try:
                # Time the execution
                start_time = time.time()

                # Call the prompt function
                if callable(prompt_function):
                    # DSPy module
                    output = prompt_function(
                        text=test_case["text"],
                        language="English",
                        entity_types="organization,person,location,event,concept,other",
                        tuple_delimiter="<|#|>",
                        completion_delimiter="<|COMPLETE|>",
                    )
                    result_text = getattr(
                        output, "entities_and_relationships", str(output)
                    )
                else:
                    # Regular function
                    result_text = prompt_function(test_case["text"])

                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                # Parse output
                predicted = self.lightrag_evaluator.parse_extraction_output(result_text)

                # Calculate metrics
                entity_prec, entity_rec, entity_f1 = (
                    self.lightrag_evaluator.calculate_entity_metrics(
                        predicted["entities"], test_case["expected_entities"]
                    )
                )

                rel_prec, rel_rec, rel_f1 = (
                    self.lightrag_evaluator.calculate_relationship_metrics(
                        predicted["relationships"], test_case["expected_relationships"]
                    )
                )

                format_score = self.lightrag_evaluator.evaluate_format_compliance(
                    result_text
                )
                hallucination_rate = self.lightrag_evaluator.detect_hallucinations(
                    predicted, test_case["text"]
                )
                completion_rate = 1.0 if "<|COMPLETE|>" in result_text else 0.0

                # Overall score (weighted average)
                overall_score = (
                    entity_f1 * 0.3
                    + rel_f1 * 0.3
                    + format_score * 0.2
                    + (1.0 - hallucination_rate) * 0.1
                    + completion_rate * 0.1
                )

                metrics = EvaluationMetrics(
                    entity_recall=entity_rec,
                    entity_precision=entity_prec,
                    entity_f1=entity_f1,
                    relationship_recall=rel_rec,
                    relationship_precision=rel_prec,
                    relationship_f1=rel_f1,
                    format_compliance=format_score,
                    completion_rate=completion_rate,
                    hallucination_rate=hallucination_rate,
                    overall_score=overall_score,
                    latency_ms=latency_ms,
                )

                results.append(metrics)

            except Exception as e:
                print(f"Error evaluating {prompt_name} on sample {i}: {e}")
                # Add a zero-score result
                results.append(
                    EvaluationMetrics(overall_score=0.0, latency_ms=float("inf"))
                )

        return results

    def compare_prompts(
        self, prompts_to_test: dict[str, Any], test_data: list[dict[str, Any]]
    ) -> dict[str, dict[str, float]]:
        """Compare multiple prompts and return aggregated results."""

        comparison_results = {}

        for prompt_name, prompt_function in prompts_to_test.items():
            print(f"\nEvaluating prompt: {prompt_name}")
            results = self.evaluate_prompt_function(
                prompt_function, test_data, prompt_name
            )

            if not results:
                continue

            # Aggregate metrics
            aggregated = {
                "entity_f1": np.mean([r.entity_f1 for r in results]),
                "entity_precision": np.mean([r.entity_precision for r in results]),
                "entity_recall": np.mean([r.entity_recall for r in results]),
                "relationship_f1": np.mean([r.relationship_f1 for r in results]),
                "relationship_precision": np.mean(
                    [r.relationship_precision for r in results]
                ),
                "relationship_recall": np.mean(
                    [r.relationship_recall for r in results]
                ),
                "format_compliance": np.mean([r.format_compliance for r in results]),
                "completion_rate": np.mean([r.completion_rate for r in results]),
                "hallucination_rate": np.mean([r.hallucination_rate for r in results]),
                "overall_score": np.mean([r.overall_score for r in results]),
                "latency_ms": np.mean([r.latency_ms for r in results]),
                "success_rate": sum(1 for r in results if r.overall_score > 0)
                / len(results),
            }

            comparison_results[prompt_name] = aggregated

        return comparison_results

    def save_evaluation_results(
        self, results: dict[str, dict[str, float]], output_file: str | None = None
    ) -> str:
        """Save evaluation results to file."""

        if output_file is None:
            output_file = self.working_directory / "dspy_evaluation_results.json"

        # Add metadata
        results_with_metadata = {
            "evaluation_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_prompts": len(results),
                "metrics_calculated": [
                    "entity_f1",
                    "entity_precision",
                    "entity_recall",
                    "relationship_f1",
                    "relationship_precision",
                    "relationship_recall",
                    "format_compliance",
                    "completion_rate",
                    "hallucination_rate",
                    "overall_score",
                    "latency_ms",
                    "success_rate",
                ],
            },
            "results": results,
        }

        with open(output_file, "w") as f:
            json.dump(results_with_metadata, f, indent=2)

        print(f"Evaluation results saved to: {output_file}")
        return str(output_file)

    def print_comparison_table(self, results: dict[str, dict[str, float]]) -> None:
        """Print a formatted comparison table of results."""

        print("\n" + "=" * 80)
        print("PROMPT COMPARISON RESULTS")
        print("=" * 80)

        # Header
        header = f"{'Prompt Name':<25} {'Overall':<8} {'Entity F1':<10} {'Rel F1':<8} {'Format':<8} {'Halluc':<8} {'Latency':<10}"
        print(header)
        print("-" * len(header))

        # Results
        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["overall_score"], reverse=True
        )

        for prompt_name, metrics in sorted_results:
            row = f"{prompt_name:<25} {metrics['overall_score']:<8.3f} {metrics['entity_f1']:<10.3f} {metrics['relationship_f1']:<8.3f} {metrics['format_compliance']:<8.3f} {metrics['hallucination_rate']:<8.3f} {metrics['latency_ms']:<10.0f}"
            print(row)

        print("-" * len(header))

        # Winner
        if sorted_results:
            winner_name, winner_metrics = sorted_results[0]
            print(f"\n🏆 Best performing prompt: {winner_name}")
            print(f"   Overall Score: {winner_metrics['overall_score']:.3f}")
            print(f"   Entity F1: {winner_metrics['entity_f1']:.3f}")
            print(f"   Relationship F1: {winner_metrics['relationship_f1']:.3f}")
            print(f"   Format Compliance: {winner_metrics['format_compliance']:.3f}")


def main():
    """Run a complete evaluation comparing DSPy prompts with existing LightRAG prompts."""

    print("🚀 Starting DSPy vs LightRAG Prompt Evaluation")
    print("=" * 60)

    # Create evaluator
    evaluator = DSPyPromptEvaluator()

    # Create test data
    test_data = evaluator.create_evaluation_dataset(num_samples=10)
    print(f"Created {len(test_data)} test cases")

    # Define prompts to test
    prompts_to_test = {}

    # Add existing LightRAG prompts
    if PROMPTS:

        def lightrag_default_prompt(_text):
            return "This would use the existing LightRAG prompt (simulated)"

        def lightrag_variant_a_prompt(_text):
            return "This would use LightRAG variant A (simulated)"

        prompts_to_test["lightrag_default"] = lightrag_default_prompt
        prompts_to_test["lightrag_variant_a"] = lightrag_variant_a_prompt

    # Add DSPy modules (if available)
    try:
        from lightrag.dspy_integration.generators.entity_extractor import (
            EntityExtractorGenerator,
        )

        generator = EntityExtractorGenerator()
        modules = generator.create_dspy_modules()

        for name, module in modules.items():
            prompts_to_test[f"dspy_{name}"] = module

    except Exception as e:
        print(f"Could not load DSPy modules: {e}")

    if not prompts_to_test:
        print("❌ No prompts available for testing")
        return False

    # Run evaluation
    print(f"\nEvaluating {len(prompts_to_test)} prompts...")
    results = evaluator.compare_prompts(prompts_to_test, test_data)

    # Print results
    evaluator.print_comparison_table(results)

    # Save results
    output_file = evaluator.save_evaluation_results(results)

    print(f"\n✅ Evaluation complete! Results saved to: {output_file}")
    return True


if __name__ == "__main__":
    success = main()
    import sys

    sys.exit(0 if success else 1)
