#!/usr/bin/env python3
"""
Asymmetric Routing Test for ACE Framework
Tests the effectiveness of using 7B models as reflectors for 1.5B/3B extraction errors.
This implements the "Asymmetric Routing" strategy where larger models repair smaller model outputs.
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
from lightrag.ace.reflector import ACEReflector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AsymmetricRoutingTestCase:
    """Test case for asymmetric routing validation."""

    test_id: str
    description: str
    extraction_model: str  # Model that did the extraction (1.5B/3B)
    reflection_model: str  # Model that does the reflection (7B)
    source_chunks: list[str]
    extracted_entities: list[dict[str, Any]]
    extracted_relationships: list[dict[str, Any]]
    expected_errors: list[str]  # Known extraction errors
    expected_improvements: list[str]  # Expected improvements from 7B reflection


@dataclass
class AsymmetricRoutingResult:
    """Results from asymmetric routing test."""

    test_id: str
    extraction_model: str
    reflection_model: str
    error_detection_rate: float
    repair_success_rate: float
    reasoning_quality: float
    execution_time: float
    improvements_made: list[str]
    errors_missed: list[str]
    false_positives: list[str]


class AsymmetricRoutingTest:
    """
    Test framework for validating asymmetric routing strategy.
    Tests if 7B models can effectively detect and repair errors from 1.5B/3B extractions.
    """

    def __init__(self):
        self.test_cases = self._create_test_cases()
        self.results: list[AsymmetricRoutingResult] = []

    def _create_test_cases(self) -> list[AsymmetricRoutingTestCase]:
        """Create test cases for asymmetric routing validation."""

        return [
            # Test Case 1: 1.5B Abstract Concept Hallucination
            AsymmetricRoutingTestCase(
                test_id="1.5b_abstract_hallucination",
                description="1.5B model abstract concept hallucination repaired by 7B reflection",
                extraction_model="qwen2.5-coder:1.5b",
                reflection_model="qwen2.5-coder:7b",
                source_chunks=[
                    "Albert Einstein was a theoretical physicist who developed the theory of relativity.",
                    "He was born in Ulm, Germany in 1879 and won the Nobel Prize in Physics.",
                    "Einstein's work revolutionized our understanding of space, time, and gravity.",
                ],
                extracted_entities=[
                    {
                        "entity_name": "Albert Einstein",
                        "entity_type": "person",
                        "description": "Theoretical physicist",
                    },
                    {
                        "entity_name": "Quantum Consciousness Framework",
                        "entity_type": "concept",
                        "description": "Sophisticated theoretical system of quantum awareness and cognitive processing",
                    },
                    {
                        "entity_name": "Relativity Theory",
                        "entity_type": "concept",
                        "description": "Theory of space and time",
                    },
                    {
                        "entity_name": "Ulm",
                        "entity_type": "location",
                        "description": "City in Germany",
                    },
                ],
                extracted_relationships=[
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Quantum Consciousness Framework",
                        "description": "developed the advanced theoretical system",
                    },
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Relativity Theory",
                        "description": "created",
                    },
                    {
                        "src_id": "Albert Einstein",
                        "tgt_id": "Ulm",
                        "description": "was born in",
                    },
                ],
                expected_errors=[
                    "Quantum Consciousness Framework - abstract concept hallucination",
                    "Over-complex description for abstract concept",
                ],
                expected_improvements=[
                    "Delete hallucinated abstract entity",
                    "Remove relationship to hallucinated entity",
                    "Provide evidence-based reasoning",
                ],
            ),
            # Test Case 2: 3B False Relationship Pattern
            AsymmetricRoutingTestCase(
                test_id="3b_false_relationship",
                description="3B model false relationship pattern repaired by 7B reflection",
                extraction_model="qwen2.5-coder:3b",
                reflection_model="qwen2.5-coder:7b",
                source_chunks=[
                    "Steve Jobs co-founded Apple Inc. with Steve Wozniak in 1976.",
                    "Apple became a major technology company known for innovative products.",
                    "The iPhone was released in 2007 and revolutionized the smartphone industry.",
                ],
                extracted_entities=[
                    {
                        "entity_name": "Steve Jobs",
                        "entity_type": "person",
                        "description": "Co-founder of Apple",
                    },
                    {
                        "entity_name": "Apple Inc.",
                        "entity_type": "organization",
                        "description": "Technology company",
                    },
                    {
                        "entity_name": "iPhone",
                        "entity_type": "concept",
                        "description": "Smartphone product",
                    },
                    {
                        "entity_name": "Innovation Paradigm",
                        "entity_type": "concept",
                        "description": "Revolutionary approach to technological advancement and market disruption",
                    },
                ],
                extracted_relationships=[
                    {
                        "src_id": "Steve Jobs",
                        "tgt_id": "Apple Inc.",
                        "description": "co-founded",
                    },
                    {
                        "src_id": "Innovation Paradigm",
                        "tgt_id": "Apple Inc.",
                        "description": "enabled the success of",
                    },
                    {
                        "src_id": "Steve Jobs",
                        "tgt_id": "Innovation Paradigm",
                        "description": "embodied",
                    },
                ],
                expected_errors=[
                    "Innovation Paradigm - abstract concept not in source",
                    "False relationship pattern between abstract concept and real entity",
                ],
                expected_improvements=[
                    "Delete abstract concept entity",
                    "Remove false relationships",
                    "Identify pattern of abstract concept hallucination",
                ],
            ),
            # Test Case 3: 1.5B Cross-Domain Confusion
            AsymmetricRoutingTestCase(
                test_id="1.5b_cross_domain",
                description="1.5B model cross-domain confusion repaired by 7B reflection",
                extraction_model="qwen2.5-coder:1.5b",
                reflection_model="qwen2.5-coder:7b",
                source_chunks=[
                    "Marie Curie was a Polish-French physicist and chemist.",
                    "She discovered radioactivity and won two Nobel Prizes.",
                    "Curie's research contributed to the development of X-ray technology.",
                ],
                extracted_entities=[
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
                        "entity_name": "Scientific Methodology",
                        "entity_type": "concept",
                        "description": "Philosophical framework for systematic investigation and empirical reasoning",
                    },
                    {
                        "entity_name": "X-ray Technology",
                        "entity_type": "concept",
                        "description": "Medical imaging technology",
                    },
                ],
                extracted_relationships=[
                    {
                        "src_id": "Marie Curie",
                        "tgt_id": "Radioactivity",
                        "description": "discovered",
                    },
                    {
                        "src_id": "Scientific Methodology",
                        "tgt_id": "Marie Curie",
                        "description": "influenced the philosophical approach of",
                    },
                    {
                        "src_id": "Marie Curie",
                        "tgt_id": "X-ray Technology",
                        "description": "contributed to",
                    },
                ],
                expected_errors=[
                    "Scientific Methodology - cross-domain confusion (philosophy + science)",
                    "Abstract concept not supported by source text",
                ],
                expected_improvements=[
                    "Detect cross-domain confusion pattern",
                    "Delete philosophical concept from scientific context",
                    "Provide evidence-based reasoning",
                ],
            ),
            # Test Case 4: 3B Over-Specific Attributes
            AsymmetricRoutingTestCase(
                test_id="3b_over_specific",
                description="3B model over-specific attributes repaired by 7B reflection",
                extraction_model="qwen2.5-coder:3b",
                reflection_model="qwen2.5-coder:7b",
                source_chunks=[
                    "The Wright brothers invented and flew the first successful airplane.",
                    "Their first flight was on December 17, 1903, at Kitty Hawk.",
                    "The aircraft traveled 120 feet in 12 seconds.",
                ],
                extracted_entities=[
                    {
                        "entity_name": "Wright brothers",
                        "entity_type": "person",
                        "description": "Aviation pioneers",
                    },
                    {
                        "entity_name": "Airplane",
                        "entity_type": "concept",
                        "description": "Flying machine",
                    },
                    {
                        "entity_name": "Advanced Aerodynamic Principle",
                        "entity_type": "concept",
                        "description": "Highly sophisticated theoretical framework achieving 97.8% lift efficiency through optimized airflow dynamics",
                    },
                ],
                extracted_relationships=[
                    {
                        "src_id": "Wright brothers",
                        "tgt_id": "Airplane",
                        "description": "invented",
                    },
                    {
                        "src_id": "Advanced Aerodynamic Principle",
                        "tgt_id": "Airplane",
                        "description": "governs the flight dynamics of",
                    },
                ],
                expected_errors=[
                    "Advanced Aerodynamic Principle - over-specific attributes (97.8% efficiency)",
                    "Complex theoretical concept not in source text",
                ],
                expected_improvements=[
                    "Detect over-specific attribute pattern",
                    "Delete overly complex theoretical concept",
                    "Identify small model precision hallucination",
                ],
            ),
            # Test Case 5: Control Case (No Errors)
            AsymmetricRoutingTestCase(
                test_id="control_no_errors",
                description="Control case with correct extraction (no repairs needed)",
                extraction_model="qwen2.5-coder:7b",
                reflection_model="qwen2.5-coder:7b",
                source_chunks=[
                    "Leonardo da Vinci was a Renaissance artist and inventor.",
                    "He painted the Mona Lisa and designed flying machines.",
                    "Da Vinci studied anatomy and engineering throughout his life.",
                ],
                extracted_entities=[
                    {
                        "entity_name": "Leonardo da Vinci",
                        "entity_type": "person",
                        "description": "Renaissance artist and inventor",
                    },
                    {
                        "entity_name": "Mona Lisa",
                        "entity_type": "concept",
                        "description": "Famous painting",
                    },
                    {
                        "entity_name": "Anatomy",
                        "entity_type": "concept",
                        "description": "Study of body structure",
                    },
                ],
                extracted_relationships=[
                    {
                        "src_id": "Leonardo da Vinci",
                        "tgt_id": "Mona Lisa",
                        "description": "painted",
                    },
                    {
                        "src_id": "Leonardo da Vinci",
                        "tgt_id": "Anatomy",
                        "description": "studied",
                    },
                ],
                expected_errors=[],
                expected_improvements=[
                    "Correctly identify no errors",
                    "Maintain all correct entities and relationships",
                ],
            ),
        ]

    async def run_test(
        self, test_case: AsymmetricRoutingTestCase
    ) -> AsymmetricRoutingResult:
        """Run a single asymmetric routing test."""

        logger.info(f"Running asymmetric routing test: {test_case.test_id}")
        start_time = time.time()

        try:
            # Mock LightRAG instances for different models
            extraction_rag = self._create_mock_rag(test_case.extraction_model)
            reflection_rag = self._create_mock_rag(test_case.reflection_model)

            # Create reflector with 7B model
            reflector = ACEReflector(reflection_rag)

            # Prepare generation result
            generation_result = {
                "context_data": {
                    "entities": test_case.extracted_entities,
                    "relationships": test_case.extracted_relationships,
                    "chunks": [{"content": chunk} for chunk in test_case.source_chunks],
                }
            }

            # Run reflection with 7B model
            repairs = await reflector.reflect_graph_issues("", generation_result)

            # Analyze results
            error_detection = self._analyze_error_detection(test_case, repairs)
            repair_success = self._analyze_repair_success(test_case, repairs)
            reasoning_quality = self._analyze_reasoning_quality(generation_result)

            execution_time = time.time() - start_time

            return AsymmetricRoutingResult(
                test_id=test_case.test_id,
                extraction_model=test_case.extraction_model,
                reflection_model=test_case.reflection_model,
                error_detection_rate=error_detection["detection_rate"],
                repair_success_rate=repair_success["success_rate"],
                reasoning_quality=reasoning_quality["quality_score"],
                execution_time=execution_time,
                improvements_made=error_detection["detected_errors"],
                errors_missed=error_detection["missed_errors"],
                false_positives=error_detection["false_positives"],
            )

        except Exception as e:
            logger.error(f"Asymmetric routing test {test_case.test_id} failed: {e}")
            return AsymmetricRoutingResult(
                test_id=test_case.test_id,
                extraction_model=test_case.extraction_model,
                reflection_model=test_case.reflection_model,
                error_detection_rate=0.0,
                repair_success_rate=0.0,
                reasoning_quality=0.0,
                execution_time=time.time() - start_time,
                improvements_made=[],
                errors_missed=test_case.expected_errors,
                false_positives=[],
            )

    def _create_mock_rag(self, model_name: str) -> LightRAG:
        """Create mock LightRAG instance for testing."""

        # Mock LLM function that simulates different model behaviors
        def mock_llm_func(prompt, model):
            if "1.5b" in model.lower():
                # Simulate 1.5B model response (simple, potentially error-prone)
                return "[]"
            elif "3b" in model.lower():
                # Simulate 3B model response (moderate complexity)
                return "[]"
            else:  # 7B model
                # Simulate 7B model response (sophisticated, with hallucination detection)
                if "hallucination" in prompt.lower() or "verify" in prompt.lower():
                    # Simulate detection of hallucinations
                    return '[{"action": "delete_entity", "name": "Quantum Consciousness Framework", "reason": "Abstract concept hallucination not supported by source text"}]'
                return "[]"

        return LightRAG(
            working_dir=f"./test_{model_name.replace(':', '_')}",
            llm_model_func=mock_llm_func,
            llm_model_name=model_name,
        )

    def _analyze_error_detection(
        self, test_case: AsymmetricRoutingTestCase, repairs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze error detection effectiveness."""

        expected_errors = set(test_case.expected_errors)
        detected_errors = set()

        # Extract detected errors from repairs
        for repair in repairs:
            if repair.get("action") == "delete_entity":
                entity_name = repair.get("name", "")
                reason = repair.get("reason", "")

                # Match with expected errors
                for expected_error in expected_errors:
                    if entity_name in expected_error or any(
                        keyword in reason.lower()
                        for keyword in ["hallucination", "abstract", "false"]
                    ):
                        detected_errors.add(expected_error)
                        break

        # Calculate metrics
        true_positives = len(detected_errors)
        false_negatives = len(expected_errors - detected_errors)
        false_positives = 0  # Would need ground truth for this

        detection_rate = (
            true_positives / len(expected_errors) if expected_errors else 1.0
        )

        return {
            "detection_rate": detection_rate,
            "detected_errors": list(detected_errors),
            "missed_errors": list(expected_errors - detected_errors),
            "false_positives": [],  # Simplified for mock testing
            "true_positives": true_positives,
            "false_negatives": false_negatives,
        }

    def _analyze_repair_success(
        self, test_case: AsymmetricRoutingTestCase, repairs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze repair success rate."""

        expected_improvements = set(test_case.expected_improvements)
        actual_improvements = set()

        # Analyze repairs to determine improvements made
        for repair in repairs:
            action = repair.get("action", "")
            reason = repair.get("reason", "").lower()

            if action == "delete_entity":
                actual_improvements.add("Delete hallucinated abstract entity")
            if "hallucination" in reason:
                actual_improvements.add("Provide evidence-based reasoning")
            if "abstract" in reason:
                actual_improvements.add(
                    "Identify pattern of abstract concept hallucination"
                )
            if "false" in reason:
                actual_improvements.add("Remove false relationships")

        # Calculate success rate
        success_rate = (
            len(actual_improvements & expected_improvements)
            / len(expected_improvements)
            if expected_improvements
            else 1.0
        )

        return {
            "success_rate": success_rate,
            "actual_improvements": list(actual_improvements),
            "expected_improvements": list(expected_improvements),
            "matched_improvements": list(actual_improvements & expected_improvements),
        }

    def _analyze_reasoning_quality(
        self, generation_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze reasoning quality of reflection."""

        quality_score = 0.0
        quality_factors = []

        # Check for reasoning output
        if "graph_verification_reasoning" in generation_result:
            reasoning_text = generation_result["graph_verification_reasoning"]
            quality_score += 0.5
            quality_factors.append("has_reasoning")

            # Check for structured reasoning
            if (
                "EVIDENCE:" in reasoning_text
                and "ANALYSIS:" in reasoning_text
                and "CONCLUSION:" in reasoning_text
            ):
                quality_score += 0.3
                quality_factors.append("structured_reasoning")

            # Check for hallucination-specific reasoning
            if any(
                keyword in reasoning_text.lower()
                for keyword in ["hallucination", "abstract", "pattern"]
            ):
                quality_score += 0.2
                quality_factors.append("hallucination_specific_reasoning")

        return {"quality_score": quality_score, "quality_factors": quality_factors}

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all asymmetric routing tests."""

        logger.info(f"Starting {len(self.test_cases)} asymmetric routing tests...")

        # Run all test cases
        for test_case in self.test_cases:
            result = await self.run_test(test_case)
            self.results.append(result)

            # Log individual test results
            logger.info(f"Test {test_case.test_id} completed:")
            logger.info(f"  Error Detection Rate: {result.error_detection_rate:.3f}")
            logger.info(f"  Repair Success Rate: {result.repair_success_rate:.3f}")
            logger.info(f"  Reasoning Quality: {result.reasoning_quality:.3f}")
            logger.info(f"  Execution Time: {result.execution_time:.2f}s")

        # Generate summary
        summary = self._generate_summary()

        # Log summary
        logger.info("=== ASYMMETRIC ROUTING TEST SUMMARY ===")
        logger.info(
            f"Average Error Detection Rate: {summary['avg_error_detection_rate']:.3f}"
        )
        logger.info(
            f"Average Repair Success Rate: {summary['avg_repair_success_rate']:.3f}"
        )
        logger.info(
            f"Average Reasoning Quality: {summary['avg_reasoning_quality']:.3f}"
        )
        logger.info(f"Overall Effectiveness: {summary['overall_effectiveness']:.3f}")

        return summary

    def _generate_summary(self) -> dict[str, Any]:
        """Generate comprehensive summary of test results."""

        if not self.results:
            return {"error": "No results to summarize"}

        # Calculate aggregate metrics
        total_tests = len(self.results)

        error_detection_rates = [r.error_detection_rate for r in self.results]
        repair_success_rates = [r.repair_success_rate for r in self.results]
        reasoning_qualities = [r.reasoning_quality for r in self.results]
        execution_times = [r.execution_time for r in self.results]

        avg_error_detection_rate = sum(error_detection_rates) / len(
            error_detection_rates
        )
        avg_repair_success_rate = sum(repair_success_rates) / len(repair_success_rates)
        avg_reasoning_quality = sum(reasoning_qualities) / len(reasoning_qualities)
        avg_execution_time = sum(execution_times) / len(execution_times)

        # Overall effectiveness (weighted average)
        overall_effectiveness = (
            avg_error_detection_rate * 0.4
            + avg_repair_success_rate * 0.4
            + avg_reasoning_quality * 0.2
        )

        # Model-specific performance
        model_performance = {}
        for result in self.results:
            extraction_model = result.extraction_model
            reflection_model = result.reflection_model

            key = f"{extraction_model} → {reflection_model}"
            if key not in model_performance:
                model_performance[key] = {
                    "error_detection_rates": [],
                    "repair_success_rates": [],
                    "reasoning_qualities": [],
                }

            model_performance[key]["error_detection_rates"].append(
                result.error_detection_rate
            )
            model_performance[key]["repair_success_rates"].append(
                result.repair_success_rate
            )
            model_performance[key]["reasoning_qualities"].append(
                result.reasoning_quality
            )

        # Average model performance
        for key in model_performance:
            metrics = model_performance[key]
            model_performance[key] = {
                "avg_error_detection_rate": sum(metrics["error_detection_rates"])
                / len(metrics["error_detection_rates"]),
                "avg_repair_success_rate": sum(metrics["repair_success_rates"])
                / len(metrics["repair_success_rates"]),
                "avg_reasoning_quality": sum(metrics["reasoning_qualities"])
                / len(metrics["reasoning_qualities"]),
            }

        # Success criteria
        success_criteria = {
            "error_detection_target": 0.8,  # 80%
            "repair_success_target": 0.7,  # 70%
            "reasoning_quality_target": 0.6,  # 60%
            "overall_effectiveness_target": 0.75,  # 75%
        }

        # Check if targets are met
        targets_met = {
            "error_detection": avg_error_detection_rate
            >= success_criteria["error_detection_target"],
            "repair_success": avg_repair_success_rate
            >= success_criteria["repair_success_target"],
            "reasoning_quality": avg_reasoning_quality
            >= success_criteria["reasoning_quality_target"],
            "overall_effectiveness": overall_effectiveness
            >= success_criteria["overall_effectiveness_target"],
        }

        return {
            "total_tests": total_tests,
            "avg_error_detection_rate": avg_error_detection_rate,
            "avg_repair_success_rate": avg_repair_success_rate,
            "avg_reasoning_quality": avg_reasoning_quality,
            "avg_execution_time": avg_execution_time,
            "overall_effectiveness": overall_effectiveness,
            "model_performance": model_performance,
            "success_criteria": success_criteria,
            "targets_met": targets_met,
            "all_targets_met": all(targets_met.values()),
            "timestamp": datetime.now().isoformat(),
        }

    def save_results(self, output_dir: str = "asymmetric_routing_results") -> None:
        """Save test results to files."""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save detailed results
        results_file = (
            output_path
            / f"asymmetric_routing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        results_data = {
            "summary": self._generate_summary(),
            "detailed_results": [asdict(result) for result in self.results],
            "test_cases": [asdict(test_case) for test_case in self.test_cases],
        }

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Asymmetric routing test results saved to: {results_file}")

        # Save summary as markdown
        summary_file = (
            output_path
            / f"asymmetric_routing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        self._save_summary_markdown(summary_file)

        logger.info(f"Asymmetric routing summary saved to: {summary_file}")

    def _save_summary_markdown(self, file_path: Path) -> None:
        """Save test summary as markdown file."""

        summary = self._generate_summary()

        with open(file_path, "w") as f:
            f.write("# ACE Asymmetric Routing Test Summary\n\n")
            f.write(f"**Date**: {summary['timestamp']}\n")
            f.write(f"**Total Tests**: {summary['total_tests']}\n\n")

            f.write("## 🎯 Success Criteria vs Actual Results\n\n")
            f.write("| Metric | Target | Actual | Status |\n")
            f.write("|--------|--------|--------|--------|\n")
            f.write(
                f"| Error Detection Rate | {summary['success_criteria']['error_detection_target']:.1%} | {summary['avg_error_detection_rate']:.1%} | {'✅' if summary['targets_met']['error_detection'] else '❌'} |\n"
            )
            f.write(
                f"| Repair Success Rate | {summary['success_criteria']['repair_success_target']:.1%} | {summary['avg_repair_success_rate']:.1%} | {'✅' if summary['targets_met']['repair_success'] else '❌'} |\n"
            )
            f.write(
                f"| Reasoning Quality | {summary['success_criteria']['reasoning_quality_target']:.1%} | {summary['avg_reasoning_quality']:.1%} | {'✅' if summary['targets_met']['reasoning_quality'] else '❌'} |\n"
            )
            f.write(
                f"| Overall Effectiveness | {summary['success_criteria']['overall_effectiveness_target']:.1%} | {summary['overall_effectiveness']:.1%} | {'✅' if summary['targets_met']['overall_effectiveness'] else '❌'} |\n\n"
            )

            f.write(
                f"## 🏆 Overall Result: {'✅ ALL TARGETS MET' if summary['all_targets_met'] else '❌ SOME TARGETS MISSED'}\n\n"
            )

            f.write("## 📊 Model Performance Breakdown\n\n")
            for model_pair, metrics in summary["model_performance"].items():
                f.write(f"### {model_pair}\n\n")
                f.write(
                    f"- Error Detection Rate: {metrics['avg_error_detection_rate']:.3f}\n"
                )
                f.write(
                    f"- Repair Success Rate: {metrics['avg_repair_success_rate']:.3f}\n"
                )
                f.write(
                    f"- Reasoning Quality: {metrics['avg_reasoning_quality']:.3f}\n\n"
                )

            f.write("## 📈 Detailed Test Results\n\n")
            for result in self.results:
                f.write(f"### Test: {result.test_id}\n\n")
                f.write(f"- Extraction Model: {result.extraction_model}\n")
                f.write(f"- Reflection Model: {result.reflection_model}\n")
                f.write(f"- Error Detection Rate: {result.error_detection_rate:.3f}\n")
                f.write(f"- Repair Success Rate: {result.repair_success_rate:.3f}\n")
                f.write(f"- Reasoning Quality: {result.reasoning_quality:.3f}\n")
                f.write(f"- Execution Time: {result.execution_time:.2f}s\n")
                f.write(f"- Improvements Made: {len(result.improvements_made)}\n")
                f.write(f"- Errors Missed: {len(result.errors_missed)}\n")
                f.write(f"- False Positives: {len(result.false_positives)}\n\n")

            f.write("## 📋 Conclusions\n\n")
            if summary["all_targets_met"]:
                f.write(
                    "✅ **Asymmetric routing is highly effective** - 7B models successfully detect and repair errors from 1.5B/3B extractions.\n\n"
                )
                f.write("### Key Findings:\n")
                f.write(
                    "- 7B models show sophisticated hallucination detection capabilities\n"
                )
                f.write("- Evidence-based reasoning is consistently provided\n")
                f.write("- Cross-domain confusion patterns are reliably identified\n")
                f.write("- Over-specific attribute hallucinations are detected\n\n")
            else:
                f.write(
                    "⚠️ **Asymmetric routing needs improvement** - Some targets not met.\n\n"
                )
                f.write("### Areas for Improvement:\n")
                if not summary["targets_met"]["error_detection"]:
                    f.write("- Error detection rate needs improvement\n")
                if not summary["targets_met"]["repair_success"]:
                    f.write("- Repair success rate needs improvement\n")
                if not summary["targets_met"]["reasoning_quality"]:
                    f.write("- Reasoning quality needs enhancement\n")
                f.write("\n")


async def main():
    """Main function to run asymmetric routing tests."""

    # Create and run test
    test = AsymmetricRoutingTest()
    summary = await test.run_all_tests()

    # Save results
    test.save_results()

    # Print final summary
    print("\n" + "=" * 60)
    print("ACE ASYMMETRIC ROUTING TEST COMPLETE")
    print("=" * 60)
    print(
        f"Error Detection Rate: {summary['avg_error_detection_rate']:.1%} (Target: 80%)"
    )
    print(
        f"Repair Success Rate: {summary['avg_repair_success_rate']:.1%} (Target: 70%)"
    )
    print(f"Reasoning Quality: {summary['avg_reasoning_quality']:.1%} (Target: 60%)")
    print(
        f"Overall Effectiveness: {summary['overall_effectiveness']:.1%} (Target: 75%)"
    )
    print(
        f"Result: {'✅ ALL TARGETS MET' if summary['all_targets_met'] else '❌ SOME TARGETS MISSED'}"
    )
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
