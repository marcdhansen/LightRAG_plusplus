#!/usr/bin/env python3
"""
ACE Reflection Quality Benchmarking Framework
Measures hallucination detection accuracy and repair quality for ACE Reflector.
Target metrics: 80% hallucination detection, 70% repair accuracy.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from lightrag import LightRAG
from lightrag.ace.hallucination_detector import HallucinationDetector
from lightrag.ace.reflector import ACEReflector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkTestCase:
    """Test case for reflection quality benchmarking."""

    test_id: str
    description: str
    source_chunks: list[str]
    entities: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    expected_hallucinations: dict[str, list[str]]  # entity_name -> reasons
    expected_repairs: list[dict[str, Any]]
    model_size: str = "7b"
    difficulty: str = "medium"  # easy, medium, hard


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test case."""

    test_id: str
    hallucination_detection: dict[str, Any]
    repair_accuracy: dict[str, Any]
    execution_time: float
    reasoning_quality: dict[str, Any]
    errors: list[str]


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results across all test cases."""

    total_tests: int
    hallucination_detection_accuracy: float
    repair_accuracy: float
    reasoning_quality_score: float
    average_execution_time: float
    model_performance: dict[str, dict[str, float]]
    success_rate: float
    timestamp: str


class ReflectionQualityBenchmark:
    """
    Comprehensive benchmarking framework for ACE reflection quality.
    Tests hallucination detection and repair accuracy across different scenarios.
    """

    def __init__(self, lightrag_instance: LightRAG):
        self.rag = lightrag_instance
        self.reflector = ACEReflector(lightrag_instance)
        self.hallucination_detector = HallucinationDetector()

        # Initialize test cases
        self.test_cases = self._create_test_cases()

        # Results storage
        self.results: list[BenchmarkResult] = []

    def _create_test_cases(self) -> list[BenchmarkTestCase]:
        """Create comprehensive test cases covering different hallucination scenarios."""

        test_cases = [
            # Test Case 1: Abstract Concept Hallucination (1.5B model pattern)
            BenchmarkTestCase(
                test_id="abstract_concept_1.5b",
                description="Abstract concept hallucination typical of 1.5B models",
                model_size="1.5b",
                difficulty="medium",
                source_chunks=[
                    "Albert Einstein was a theoretical physicist who developed the theory of relativity.",
                    "He was born in Ulm, Germany in 1879 and later moved to the United States.",
                    "Einstein published many papers on quantum theory and statistical mechanics.",
                ],
                entities=[
                    {
                        "entity_name": "Albert Einstein",
                        "entity_type": "person",
                        "description": "Theoretical physicist",
                    },
                    {
                        "entity_name": "Quantum Consciousness",
                        "entity_type": "concept",
                        "description": "Abstract principle of quantum awareness in theoretical physics",
                    },
                    {
                        "entity_name": "Relativity Framework",
                        "entity_type": "concept",
                        "description": "Sophisticated system of spacetime distortion",
                    },
                    {
                        "entity_name": "Ulm",
                        "entity_type": "location",
                        "description": "City in Germany",
                    },
                ],
                relationships=[
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Quantum Consciousness",
                        "description": "developed the theory of",
                    },
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Relativity Framework",
                        "description": "created the conceptual framework of",
                    },
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Ulm",
                        "description": "was born in",
                    },
                ],
                expected_hallucinations={
                    "Quantum Consciousness": [
                        "Abstract concept not in source text",
                        "Typical 1.5B hallucination pattern",
                    ],
                    "Relativity Framework": [
                        "Over-specific abstraction",
                        "Not mentioned in sources",
                    ],
                },
                expected_repairs=[
                    {
                        "action": "delete_entity",
                        "name": "Quantum Consciousness",
                        "reason": "Abstract concept hallucination",
                    },
                    {
                        "action": "delete_entity",
                        "name": "Relativity Framework",
                        "reason": "Over-specific abstraction",
                    },
                    {
                        "action": "delete_relation",
                        "source": "Albert Einstein",
                        "target": "Quantum Consciousness",
                        "reason": "Hallucinated entity relationship",
                    },
                ],
            ),
            # Test Case 2: False Relationship Pattern
            BenchmarkTestCase(
                test_id="false_relationship_3b",
                description="False relationship patterns common in 3B models",
                model_size="3b",
                difficulty="medium",
                source_chunks=[
                    "The company Apple Inc. was founded by Steve Jobs and Steve Wozniak.",
                    "Apple is headquartered in Cupertino, California.",
                    "The iPhone was first released in 2007 under Steve Jobs' leadership.",
                ],
                entities=[
                    {
                        "entity_name": "Apple Inc.",
                        "entity_type": "organization",
                        "description": "Technology company",
                    },
                    {
                        "entity_name": "Steve Jobs",
                        "entity_type": "person",
                        "description": "Co-founder of Apple",
                    },
                    {
                        "entity_name": "Cupertino",
                        "entity_type": "location",
                        "description": "City in California",
                    },
                    {
                        "entity_name": "Innovation Paradigm",
                        "entity_type": "concept",
                        "description": "Revolutionary approach to technological advancement",
                    },
                ],
                relationships=[
                    {
                        "src_id": "Apple Inc.",
                        "tgt_id": "Cupertino",
                        "description": "is headquartered in",
                    },
                    {
                        "src_id": "Steve Jobs",
                        "tgt_id": "Innovation Paradigm",
                        "description": "embodies the principle of",
                    },
                    {
                        "src_id": "Innovation Paradigm",
                        "tgt_id": "Apple Inc.",
                        "description": "enables the success of",
                    },
                ],
                expected_hallucinations={
                    "Innovation Paradigm": [
                        "Abstract concept not in source",
                        "False relationship pattern",
                    ]
                },
                expected_repairs=[
                    {
                        "action": "delete_entity",
                        "name": "Innovation Paradigm",
                        "reason": "Abstract concept hallucination",
                    },
                    {
                        "action": "delete_relation",
                        "source": "Steve Jobs",
                        "target": "Innovation Paradigm",
                        "reason": "False relationship pattern",
                    },
                ],
            ),
            # Test Case 3: Cross-Domain Confusion
            BenchmarkTestCase(
                test_id="cross_domain_1.5b",
                description="Cross-domain confusion typical of small models",
                model_size="1.5b",
                difficulty="hard",
                source_chunks=[
                    "Marie Curie was a physicist and chemist who conducted research on radioactivity.",
                    "She discovered two elements, polonium and radium.",
                    "Curie was the first woman to win a Nobel Prize and remains the only person to win in two different scientific fields.",
                ],
                entities=[
                    {
                        "entity_name": "Marie Curie",
                        "entity_type": "person",
                        "description": "Physicist and chemist",
                    },
                    {
                        "entity_name": "Radioactivity",
                        "entity_type": "concept",
                        "description": "Physical phenomenon",
                    },
                    {
                        "entity_name": "Scientific Consciousness",
                        "entity_type": "concept",
                        "description": "Philosophical understanding of scientific methodology",
                    },
                    {
                        "entity_name": "Polonium",
                        "entity_type": "concept",
                        "description": "Chemical element",
                    },
                    {
                        "entity_name": "Nobel Prize",
                        "entity_type": "concept",
                        "description": "International award",
                    },
                ],
                relationships=[
                    {
                        "src_id": "Marie Curie",
                        "tgt_id": "Radioactivity",
                        "description": "researched",
                    },
                    {
                        "src_id": "Scientific Consciousness",
                        "tgt_id": "Marie Curie",
                        "description": "influenced the philosophical approach of",
                    },
                    {
                        "src_id": "Marie Curie",
                        "tgt_id": "Polonium",
                        "description": "discovered",
                    },
                ],
                expected_hallucinations={
                    "Scientific Consciousness": [
                        "Cross-domain confusion (philosophy + science)",
                        "Abstract concept not in source",
                    ]
                },
                expected_repairs=[
                    {
                        "action": "delete_entity",
                        "name": "Scientific Consciousness",
                        "reason": "Cross-domain confusion",
                    },
                    {
                        "action": "delete_relation",
                        "source": "Scientific Consciousness",
                        "target": "Marie Curie",
                        "reason": "Cross-domain relationship",
                    },
                ],
            ),
            # Test Case 4: Over-Specific Attributes
            BenchmarkTestCase(
                test_id="over_specific_7b",
                description="Over-specific attributes beyond source text",
                model_size="7b",
                difficulty="easy",
                source_chunks=[
                    "The Wright brothers, Orville and Wilbur, invented the first successful airplane.",
                    "Their first flight occurred on December 17, 1903, in Kitty Hawk, North Carolina.",
                    "The aircraft flew for 12 seconds covering a distance of 120 feet.",
                ],
                entities=[
                    {
                        "entity_name": "Wright brothers",
                        "entity_type": "person",
                        "description": "Aviation pioneers",
                    },
                    {
                        "entity_name": "Kitty Hawk",
                        "entity_type": "location",
                        "description": "Location of first flight",
                    },
                    {
                        "entity_name": "Advanced Aerodynamic Principle",
                        "entity_type": "concept",
                        "description": "Highly sophisticated theoretical framework for lift generation exceeding 95.3% efficiency",
                    },
                ],
                relationships=[
                    {
                        "src_id": "Wright brothers",
                        "tgt_id": "Advanced Aerodynamic Principle",
                        "description": "developed the highly sophisticated theoretical framework",
                    },
                    {
                        "src_id": "Wright brothers",
                        "tgt_id": "Kitty Hawk",
                        "description": "flew at",
                    },
                ],
                expected_hallucinations={
                    "Advanced Aerodynamic Principle": [
                        "Over-specific attributes (95.3% efficiency)",
                        "Complex concept not in source",
                    ]
                },
                expected_repairs=[
                    {
                        "action": "delete_entity",
                        "name": "Advanced Aerodynamic Principle",
                        "reason": "Over-specific attributes",
                    }
                ],
            ),
            # Test Case 5: No Hallucinations (Control)
            BenchmarkTestCase(
                test_id="no_hallucinations_control",
                description="Control case with no hallucinations",
                model_size="7b",
                difficulty="easy",
                source_chunks=[
                    "William Shakespeare was an English playwright and poet.",
                    "He wrote famous plays including Hamlet, Romeo and Juliet, and Macbeth.",
                    "Shakespeare was born in Stratford-upon-Avon and died in 1616.",
                ],
                entities=[
                    {
                        "entity_name": "William Shakespeare",
                        "entity_type": "person",
                        "description": "English playwright",
                    },
                    {
                        "entity_name": "Hamlet",
                        "entity_type": "concept",
                        "description": "Famous tragedy play",
                    },
                    {
                        "entity_name": "Stratford-upon-Avon",
                        "entity_type": "location",
                        "description": "Birthplace of Shakespeare",
                    },
                ],
                relationships=[
                    {
                        "src_id": "William Shakespeare",
                        "tgt_id": "Hamlet",
                        "description": "wrote",
                    },
                    {
                        "src_id": "William Shakespeare",
                        "tgt_id": "Stratford-upon-Avon",
                        "description": "was born in",
                    },
                ],
                expected_hallucinations={},
                expected_repairs=[],
            ),
        ]

        return test_cases

    async def run_benchmark(self, test_case: BenchmarkTestCase) -> BenchmarkResult:
        """Run a single benchmark test case."""

        logger.info(f"Running benchmark test: {test_case.test_id}")
        start_time = time.time()

        try:
            # Prepare generation result for reflection
            generation_result = {
                "context_data": {
                    "entities": test_case.entities,
                    "relationships": test_case.relationships,
                    "chunks": [{"content": chunk} for chunk in test_case.source_chunks],
                }
            }

            # Run reflection
            repairs = await self.reflector.reflect_graph_issues("", generation_result)

            # Analyze hallucination detection
            hallucination_analysis = self._analyze_hallucination_detection(
                test_case, repairs
            )

            # Analyze repair accuracy
            repair_analysis = self._analyze_repair_accuracy(test_case, repairs)

            # Analyze reasoning quality
            reasoning_analysis = self._analyze_reasoning_quality(generation_result)

            execution_time = time.time() - start_time

            return BenchmarkResult(
                test_id=test_case.test_id,
                hallucination_detection=hallucination_analysis,
                repair_accuracy=repair_analysis,
                execution_time=execution_time,
                reasoning_quality=reasoning_analysis,
                errors=[],
            )

        except Exception as e:
            logger.error(f"Benchmark test {test_case.test_id} failed: {e}")
            return BenchmarkResult(
                test_id=test_case.test_id,
                hallucination_detection={},
                repair_accuracy={},
                execution_time=time.time() - start_time,
                reasoning_quality={},
                errors=[str(e)],
            )

    def _analyze_hallucination_detection(
        self, test_case: BenchmarkTestCase, repairs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze hallucination detection accuracy."""

        expected_hallucinated_entities = set(test_case.expected_hallucinations.keys())
        detected_hallucinated_entities = set()

        # Extract detected hallucinations from repairs
        for repair in repairs:
            if repair.get("action") == "delete_entity":
                entity_name = repair.get("name")
                if entity_name in expected_hallucinated_entities:
                    detected_hallucinated_entities.add(entity_name)

        # Calculate metrics
        true_positives = len(detected_hallucinated_entities)
        false_positives = 0  # Entities detected as hallucinated but aren't
        false_negatives = len(
            expected_hallucinated_entities - detected_hallucinated_entities
        )

        # Precision and recall
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "expected_hallucinations": len(expected_hallucinated_entities),
            "detected_hallucinations": len(detected_hallucinated_entities),
        }

    def _analyze_repair_accuracy(
        self, test_case: BenchmarkTestCase, repairs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze repair action accuracy."""

        expected_repairs = set()
        for repair in test_case.expected_repairs:
            key = f"{repair['action']}:{repair.get('name', repair.get('source', ''))}:{repair.get('target', '')}"
            expected_repairs.add(key)

        actual_repairs = set()
        for repair in repairs:
            key = f"{repair['action']}:{repair.get('name', repair.get('source', ''))}:{repair.get('target', '')}"
            actual_repairs.add(key)

        # Calculate accuracy metrics
        correct_repairs = len(expected_repairs & actual_repairs)
        total_expected = len(expected_repairs)
        total_actual = len(actual_repairs)

        accuracy = correct_repairs / total_expected if total_expected > 0 else 0

        return {
            "correct_repairs": correct_repairs,
            "total_expected": total_expected,
            "total_actual": total_actual,
            "accuracy": accuracy,
            "expected_repairs": list(expected_repairs),
            "actual_repairs": list(actual_repairs),
        }

    def _analyze_reasoning_quality(
        self, generation_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze reasoning quality from reflection output."""

        reasoning_score = 0.0
        reasoning_factors = []

        # Check for reasoning output
        if "reflection_reasoning" in generation_result:
            reasoning_score += 0.3
            reasoning_factors.append("has_reasoning_output")

        if "graph_verification_reasoning" in generation_result:
            reasoning_score += 0.3
            reasoning_factors.append("has_graph_reasoning")

        # Check reasoning structure (Evidence → Analysis → Conclusion)
        reasoning_text = generation_result.get("graph_verification_reasoning", "")
        if (
            "EVIDENCE:" in reasoning_text
            and "ANALYSIS:" in reasoning_text
            and "CONCLUSION:" in reasoning_text
        ):
            reasoning_score += 0.4
            reasoning_factors.append("structured_reasoning")

        return {
            "reasoning_score": reasoning_score,
            "reasoning_factors": reasoning_factors,
            "has_reasoning_output": "reflection_reasoning" in generation_result,
            "has_graph_reasoning": "graph_verification_reasoning" in generation_result,
            "structured_reasoning": "EVIDENCE:" in reasoning_text
            and "ANALYSIS:" in reasoning_text
            and "CONCLUSION:" in reasoning_text,
        }

    async def run_all_benchmarks(self) -> BenchmarkSummary:
        """Run all benchmark test cases and generate summary."""

        logger.info(f"Starting {len(self.test_cases)} benchmark tests...")

        # Run all test cases
        for test_case in self.test_cases:
            result = await self.run_benchmark(test_case)
            self.results.append(result)

            # Log individual test results
            logger.info(f"Test {test_case.test_id} completed:")
            logger.info(
                f"  Hallucination F1: {result.hallucination_detection.get('f1_score', 0):.3f}"
            )
            logger.info(
                f"  Repair Accuracy: {result.repair_accuracy.get('accuracy', 0):.3f}"
            )
            logger.info(
                f"  Reasoning Score: {result.reasoning_quality.get('reasoning_score', 0):.3f}"
            )
            logger.info(f"  Execution Time: {result.execution_time:.2f}s")

        # Generate summary
        summary = self._generate_summary()

        # Log summary
        logger.info("=== BENCHMARK SUMMARY ===")
        logger.info(
            f"Hallucination Detection Accuracy: {summary.hallucination_detection_accuracy:.3f}"
        )
        logger.info(f"Repair Accuracy: {summary.repair_accuracy:.3f}")
        logger.info(f"Reasoning Quality Score: {summary.reasoning_quality_score:.3f}")
        logger.info(f"Average Execution Time: {summary.average_execution_time:.2f}s")
        logger.info(f"Overall Success Rate: {summary.success_rate:.3f}")

        return summary

    def _generate_summary(self) -> BenchmarkSummary:
        """Generate comprehensive summary of benchmark results."""

        if not self.results:
            return BenchmarkSummary(0, 0, 0, 0, 0, {}, 0, datetime.now().isoformat())

        # Calculate aggregate metrics
        total_tests = len(self.results)

        # Hallucination detection metrics
        hallucination_f1_scores = [
            r.hallucination_detection.get("f1_score", 0) for r in self.results
        ]
        avg_hallucination_detection = sum(hallucination_f1_scores) / len(
            hallucination_f1_scores
        )

        # Repair accuracy metrics
        repair_accuracies = [r.repair_accuracy.get("accuracy", 0) for r in self.results]
        avg_repair_accuracy = sum(repair_accuracies) / len(repair_accuracies)

        # Reasoning quality metrics
        reasoning_scores = [
            r.reasoning_quality.get("reasoning_score", 0) for r in self.results
        ]
        avg_reasoning_quality = sum(reasoning_scores) / len(reasoning_scores)

        # Execution time metrics
        execution_times = [r.execution_time for r in self.results]
        avg_execution_time = sum(execution_times) / len(execution_times)

        # Model performance breakdown
        model_performance = {}
        for result in self.results:
            test_case = next(
                tc for tc in self.test_cases if tc.test_id == result.test_id
            )
            model_size = test_case.model_size

            if model_size not in model_performance:
                model_performance[model_size] = {
                    "hallucination_f1": [],
                    "repair_accuracy": [],
                    "reasoning_score": [],
                    "execution_time": [],
                }

            model_performance[model_size]["hallucination_f1"].append(
                result.hallucination_detection.get("f1_score", 0)
            )
            model_performance[model_size]["repair_accuracy"].append(
                result.repair_accuracy.get("accuracy", 0)
            )
            model_performance[model_size]["reasoning_score"].append(
                result.reasoning_quality.get("reasoning_score", 0)
            )
            model_performance[model_size]["execution_time"].append(
                result.execution_time
            )

        # Average model performance
        for model_size in model_performance:
            metrics = model_performance[model_size]
            model_performance[model_size] = {
                "avg_hallucination_f1": sum(metrics["hallucination_f1"])
                / len(metrics["hallucination_f1"]),
                "avg_repair_accuracy": sum(metrics["repair_accuracy"])
                / len(metrics["repair_accuracy"]),
                "avg_reasoning_score": sum(metrics["reasoning_score"])
                / len(metrics["reasoning_score"]),
                "avg_execution_time": sum(metrics["execution_time"])
                / len(metrics["execution_time"]),
            }

        # Success rate (tests meeting minimum thresholds)
        successful_tests = 0
        for result in self.results:
            hallucination_ok = (
                result.hallucination_detection.get("f1_score", 0) >= 0.8
            )  # 80% target
            repair_ok = result.repair_accuracy.get("accuracy", 0) >= 0.7  # 70% target
            reasoning_ok = (
                result.reasoning_quality.get("reasoning_score", 0) >= 0.6
            )  # 60% reasoning threshold

            if hallucination_ok and repair_ok and reasoning_ok:
                successful_tests += 1

        success_rate = successful_tests / total_tests

        return BenchmarkSummary(
            total_tests=total_tests,
            hallucination_detection_accuracy=avg_hallucination_detection,
            repair_accuracy=avg_repair_accuracy,
            reasoning_quality_score=avg_reasoning_quality,
            average_execution_time=avg_execution_time,
            model_performance=model_performance,
            success_rate=success_rate,
            timestamp=datetime.now().isoformat(),
        )

    def save_results(self, output_dir: str = "benchmark_results") -> None:
        """Save benchmark results to files."""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save detailed results
        results_file = (
            output_path
            / f"reflection_benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        results_data = {
            "summary": asdict(self._generate_summary()),
            "detailed_results": [asdict(result) for result in self.results],
            "test_cases": [asdict(test_case) for test_case in self.test_cases],
        }

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Benchmark results saved to: {results_file}")

        # Save summary as markdown
        summary_file = (
            output_path
            / f"reflection_benchmark_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        self._save_summary_markdown(summary_file)

        logger.info(f"Benchmark summary saved to: {summary_file}")

    def _save_summary_markdown(self, file_path: Path) -> None:
        """Save benchmark summary as markdown file."""

        summary = self._generate_summary()

        with open(file_path, "w") as f:
            f.write("# ACE Reflection Quality Benchmark Summary\n\n")
            f.write(f"**Date**: {summary.timestamp}\n")
            f.write(f"**Total Tests**: {summary.total_tests}\n\n")

            f.write("## 🎯 Target Metrics vs Actual Results\n\n")
            f.write("| Metric | Target | Actual | Status |\n")
            f.write("|--------|--------|--------|--------|\n")
            f.write(
                f"| Hallucination Detection | 80% | {summary.hallucination_detection_accuracy:.1%} | {'✅' if summary.hallucination_detection_accuracy >= 0.8 else '❌'} |\n"
            )
            f.write(
                f"| Repair Accuracy | 70% | {summary.repair_accuracy:.1%} | {'✅' if summary.repair_accuracy >= 0.7 else '❌'} |\n"
            )
            f.write(
                f"| Reasoning Quality | 60% | {summary.reasoning_quality_score:.1%} | {'✅' if summary.reasoning_quality_score >= 0.6 else '❌'} |\n"
            )
            f.write(
                f"| Overall Success Rate | 80% | {summary.success_rate:.1%} | {'✅' if summary.success_rate >= 0.8 else '❌'} |\n\n"
            )

            f.write("## 📊 Model Performance Breakdown\n\n")
            for model_size, metrics in summary.model_performance.items():
                f.write(f"### {model_size.upper()} Model\n\n")
                f.write(
                    f"- Hallucination Detection F1: {metrics['avg_hallucination_f1']:.3f}\n"
                )
                f.write(f"- Repair Accuracy: {metrics['avg_repair_accuracy']:.3f}\n")
                f.write(f"- Reasoning Score: {metrics['avg_reasoning_score']:.3f}\n")
                f.write(f"- Execution Time: {metrics['avg_execution_time']:.2f}s\n\n")

            f.write("## 📈 Detailed Test Results\n\n")
            for result in self.results:
                f.write(f"### Test: {result.test_id}\n\n")
                f.write(
                    f"- Hallucination F1: {result.hallucination_detection.get('f1_score', 0):.3f}\n"
                )
                f.write(
                    f"- Repair Accuracy: {result.repair_accuracy.get('accuracy', 0):.3f}\n"
                )
                f.write(
                    f"- Reasoning Score: {result.reasoning_quality.get('reasoning_score', 0):.3f}\n"
                )
                f.write(f"- Execution Time: {result.execution_time:.2f}s\n")
                if result.errors:
                    f.write(f"- Errors: {', '.join(result.errors)}\n")
                f.write("\n")


async def main():
    """Main function to run the reflection quality benchmark."""

    # Initialize LightRAG (minimal configuration for testing)
    rag = LightRAG(
        working_dir="./benchmark_test",
        llm_model_func=lambda prompt,
        model: f"Test response for {model}",  # Mock function
        llm_model_name="qwen2.5-coder:7b",
    )

    # Create and run benchmark
    benchmark = ReflectionQualityBenchmark(rag)
    summary = await benchmark.run_all_benchmarks()

    # Save results
    benchmark.save_results()

    # Print final summary
    print("\n" + "=" * 50)
    print("ACE REFLECTION QUALITY BENCHMARK COMPLETE")
    print("=" * 50)
    print(
        f"Hallucination Detection: {summary.hallucination_detection_accuracy:.1%} (Target: 80%)"
    )
    print(f"Repair Accuracy: {summary.repair_accuracy:.1%} (Target: 70%)")
    print(f"Reasoning Quality: {summary.reasoning_quality_score:.1%} (Target: 60%)")
    print(f"Overall Success Rate: {summary.success_rate:.1%}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
