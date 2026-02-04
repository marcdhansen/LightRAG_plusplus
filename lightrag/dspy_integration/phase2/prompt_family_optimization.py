"""
DSPy Phase 2: Extended Prompt Family Optimization

This module extends DSPy optimization to all prompt families beyond entity extraction,
including summarization, query processing, document analysis, and more.
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Type
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ..config import get_dspy_config
from ..generators.entity_extractor import DSPyEntityExtractor
from ..evaluators.prompt_evaluator import DSPyPromptEvaluator


class PromptFamily(Enum):
    """Different families of prompts in LightRAG."""

    ENTITY_EXTRACTION = "entity_extraction"
    SUMMARIZATION = "summarization"
    QUERY_PROCESSING = "query_processing"
    DOCUMENT_ANALYSIS = "document_analysis"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    ANSWER_GENERATION = "answer_generation"
    CONTEXT_COMPRESSION = "context_compression"
    QUESTION_REFORMULATION = "question_reformulation"


@dataclass
class PromptFamilyConfig:
    """Configuration for a prompt family."""

    family: PromptFamily
    base_prompts: Dict[str, str]  # model_name -> base_prompt
    dspy_variants: Dict[str, str]  # variant_name -> dspy_module_name
    optimization_targets: List[str]  # metrics to optimize
    evaluation_datasets: List[str]  # dataset names for evaluation
    optimization_schedule: str  # 'daily', 'weekly', 'monthly'


@dataclass
class OptimizationResult:
    """Result of prompt optimization."""

    family: PromptFamily
    variant_name: str
    model: str
    baseline_performance: Dict[str, float]
    optimized_performance: Dict[str, float]
    improvement_percentage: float
    optimization_time: timedelta
    sample_size: int
    confidence_score: float
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class PromptFamilyOptimizer:
    """Optimizes multiple prompt families using DSPy."""

    def __init__(self):
        self.dspy_config = get_dspy_config()
        self.evaluator = DSPyPromptEvaluator()
        self.logger = logging.getLogger(__name__)

        # Initialize prompt families
        self.families = self._initialize_families()
        self.optimization_history = {}
        self.active_optimizations = {}

    def _initialize_families(self) -> Dict[PromptFamily, PromptFamilyConfig]:
        """Initialize all prompt families with their configurations."""

        families = {
            PromptFamily.ENTITY_EXTRACTION: PromptFamilyConfig(
                family=PromptFamily.ENTITY_EXTRACTION,
                base_prompts={
                    "1.5b": "extract entities and relationships in tuple format",
                    "3b": "extract detailed entities and relationships",
                    "7b": "extract comprehensive entities with attributes",
                },
                dspy_variants={},
                optimization_targets=[
                    "entity_f1",
                    "relationship_f1",
                    "format_compliance",
                ],
                evaluation_datasets=[
                    "entity_extraction_test",
                    "relationship_validation",
                ],
                optimization_schedule="daily",
            ),
            PromptFamily.SUMMARIZATION: PromptFamilyConfig(
                family=PromptFamily.SUMMARIZATION,
                base_prompts={
                    "1.5b": "summarize the text briefly",
                    "3b": "summarize the text with key points",
                    "7b": "comprehensive summary with key insights",
                },
                dspy_variants={},
                optimization_targets=["rouge_l", "rouge_1", "rouge_2", "readability"],
                evaluation_datasets=["summarization_benchmark", "document_summaries"],
                optimization_schedule="daily",
            ),
            PromptFamily.QUERY_PROCESSING: PromptFamilyConfig(
                family=PromptFamily.QUERY_PROCESSING,
                base_prompts={
                    "1.5b": "process the query for retrieval",
                    "3b": "extract key concepts from query",
                    "7b": "comprehensive query understanding and expansion",
                },
                dspy_variants={},
                optimization_targets=[
                    "retrieval_precision",
                    "query_coverage",
                    "efficiency",
                ],
                evaluation_datasets=["query_logs", "retrieval_test_cases"],
                optimization_schedule="weekly",
            ),
            PromptFamily.DOCUMENT_ANALYSIS: PromptFamilyConfig(
                family=PromptFamily.DOCUMENT_ANALYSIS,
                base_prompts={
                    "1.5b": "analyze document structure",
                    "3b": "extract document themes and topics",
                    "7b": "comprehensive document analysis with insights",
                },
                dspy_variants={},
                optimization_targets=[
                    "topic_coverage",
                    "insight_quality",
                    "structure_detection",
                ],
                evaluation_datasets=["document_corpus", "analysis_benchmarks"],
                optimization_schedule="weekly",
            ),
            PromptFamily.RELATIONSHIP_EXTRACTION: PromptFamilyConfig(
                family=PromptFamily.RELATIONSHIP_EXTRACTION,
                base_prompts={
                    "1.5b": "extract relationships",
                    "3b": "extract detailed relationships",
                    "7b": "extract comprehensive relationship network",
                },
                dspy_variants={},
                optimization_targets=["relationship_f1", "precision", "recall"],
                evaluation_datasets=["relationship_test", "network_analysis"],
                optimization_schedule="daily",
            ),
            PromptFamily.ANSWER_GENERATION: PromptFamilyConfig(
                family=PromptFamily.ANSWER_GENERATION,
                base_prompts={
                    "1.5b": "answer based on context",
                    "3b": "detailed answer with sources",
                    "7b": "comprehensive answer with analysis",
                },
                dspy_variants={},
                optimization_targets=["accuracy", "completeness", "relevance"],
                evaluation_datasets=["qa_benchmark", "answer_quality_test"],
                optimization_schedule="daily",
            ),
            PromptFamily.CONTEXT_COMPRESSION: PromptFamilyConfig(
                family=PromptFamily.CONTEXT_COMPRESSION,
                base_prompts={
                    "1.5b": "compress context",
                    "3b": "summarize context efficiently",
                    "7b": "intelligent context compression",
                },
                dspy_variants={},
                optimization_targets=[
                    "compression_ratio",
                    "information_retention",
                    "efficiency",
                ],
                evaluation_datasets=[
                    "context_compression_test",
                    "retention_benchmarks",
                ],
                optimization_schedule="weekly",
            ),
            PromptFamily.QUESTION_REFORMULATION: PromptFamilyConfig(
                family=PromptFamily.QUESTION_REFORMULATION,
                base_prompts={
                    "1.5b": "reformulate question",
                    "3b": "improve question clarity",
                    "7b": "comprehensive question enhancement",
                },
                dspy_variants={},
                optimization_targets=[
                    "clarity_improvement",
                    "retrieval_boost",
                    "semantic_preservation",
                ],
                evaluation_datasets=[
                    "question_reformulation_test",
                    "clarity_benchmarks",
                ],
                optimization_schedule="monthly",
            ),
        }

        return families

    async def optimize_family(
        self,
        family: PromptFamily,
        models: Optional[List[str]] = None,
        optimizer_name: str = "BootstrapFewShot",
    ) -> List[OptimizationResult]:
        """Optimize all prompts for a specific family."""

        if models is None:
            models = ["1.5b", "3b", "7b"]

        family_config = self.families[family]
        results = []

        for model in models:
            try:
                # Get baseline performance
                baseline_prompt = family_config.base_prompts.get(model)
                if not baseline_prompt:
                    self.logger.warning(
                        f"No baseline prompt for {family.value} on {model}"
                    )
                    continue

                baseline_performance = await self._evaluate_baseline(
                    family, baseline_prompt, model
                )

                # Create DSPy-optimized variants
                variants = await self._create_dspy_variants(
                    family, baseline_prompt, model, optimizer_name
                )

                # Evaluate variants and select best
                best_variant, best_performance = await self._evaluate_variants(
                    family, variants, model, family_config.optimization_targets
                )

                # Calculate improvement
                improvement = self._calculate_improvement(
                    baseline_performance, best_performance
                )

                # Create result
                result = OptimizationResult(
                    family=family,
                    variant_name=best_variant,
                    model=model,
                    baseline_performance=baseline_performance,
                    optimized_performance=best_performance,
                    improvement_percentage=improvement,
                    optimization_time=timedelta(minutes=30),  # Placeholder
                    sample_size=100,  # Placeholder
                    confidence_score=0.85,  # Placeholder
                )

                results.append(result)

                # Update family configuration
                family_config.dspy_variants[f"{best_variant}_{model}"] = best_variant

                self.logger.info(
                    f"Optimized {family.value} for {model}: {improvement:.1%} improvement"
                )

            except Exception as e:
                self.logger.error(f"Failed to optimize {family.value} for {model}: {e}")
                continue

        # Store optimization history
        self.optimization_history[family.value] = {
            "results": [asdict(r) for r in results],
            "timestamp": datetime.now().isoformat(),
        }

        return results

    async def _evaluate_baseline(
        self, family: PromptFamily, prompt: str, model: str
    ) -> Dict[str, float]:
        """Evaluate baseline prompt performance."""

        # Create test data based on family
        test_data = await self._generate_test_data(family, sample_size=50)

        performance = {}

        for target_metric in self.families[family].optimization_targets:
            # Evaluate using appropriate method for the metric
            score = await self._evaluate_metric(
                family, prompt, model, test_data, target_metric
            )
            performance[target_metric] = score

        return performance

    async def _create_dspy_variants(
        self, family: PromptFamily, base_prompt: str, model: str, optimizer_name: str
    ) -> Dict[str, str]:
        """Create DSPy-optimized variants for a prompt family."""

        variants = {}

        # Create different DSPy modules based on family
        if family == PromptFamily.ENTITY_EXTRACTION:
            # Use existing entity extraction modules
            extractor = DSPyEntityExtractor()
            dspy_modules = extractor.create_dspy_modules()

            for module_name, module in dspy_modules.items():
                variants[f"dspy_{module_name}"] = module_name

        else:
            # Create family-specific modules
            variants.update(
                await self._create_family_specific_modules(
                    family, base_prompt, model, optimizer_name
                )
            )

        return variants

    async def _create_family_specific_modules(
        self, family: PromptFamily, base_prompt: str, model: str, optimizer_name: str
    ) -> Dict[str, str]:
        """Create DSPy modules for specific prompt families."""

        modules = {}

        if family == PromptFamily.SUMMARIZATION:
            modules.update(
                {
                    "dspy_sum_cot": f"cot_summarization_{optimizer_name}",
                    "dspy_sum_predict": f"predict_summarization_{optimizer_name}",
                    "dspy_sum_chain": f"chain_summarization_{optimizer_name}",
                }
            )

        elif family == PromptFamily.QUERY_PROCESSING:
            modules.update(
                {
                    "dspy_query_rewrite": f"query_rewrite_{optimizer_name}",
                    "dspy_query_expand": f"query_expand_{optimizer_name}",
                    "dspy_query_intent": f"query_intent_{optimizer_name}",
                }
            )

        elif family == PromptFamily.DOCUMENT_ANALYSIS:
            modules.update(
                {
                    "dspy_doc_structure": f"doc_structure_{optimizer_name}",
                    "dspy_doc_topics": f"doc_topics_{optimizer_name}",
                    "dspy_doc_insights": f"doc_insights_{optimizer_name}",
                }
            )

        elif family == PromptFamily.ANSWER_GENERATION:
            modules.update(
                {
                    "dspy_answer_rag": f"rag_answer_{optimizer_name}",
                    "dspy_answer_synthesis": f"answer_synthesis_{optimizer_name}",
                    "dspy_answer_verification": f"answer_verification_{optimizer_name}",
                }
            )

        return modules

    async def _evaluate_variants(
        self,
        family: PromptFamily,
        variants: Dict[str, str],
        model: str,
        target_metrics: List[str],
    ) -> Tuple[str, Dict[str, float]]:
        """Evaluate all variants and return the best one."""

        test_data = await self._generate_test_data(family, sample_size=100)

        best_variant = None
        best_performance = {}
        best_overall_score = 0

        for variant_name, module_name in variants.items():
            try:
                # Get DSPy prompt for this variant
                dspy_prompt = await self._get_dspy_prompt(module_name)
                if not dspy_prompt:
                    continue

                # Evaluate performance
                performance = {}
                for metric in target_metrics:
                    score = await self._evaluate_metric(
                        family, dspy_prompt, model, test_data, metric
                    )
                    performance[metric] = score

                # Calculate overall score (weighted average)
                overall_score = self._calculate_overall_score(performance, family)

                if overall_score > best_overall_score:
                    best_overall_score = overall_score
                    best_variant = variant_name
                    best_performance = performance

            except Exception as e:
                self.logger.error(f"Failed to evaluate variant {variant_name}: {e}")
                continue

        return best_variant, best_performance

    async def _generate_test_data(
        self, family: PromptFamily, sample_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate test data for a specific prompt family."""

        test_data = []

        if family == PromptFamily.ENTITY_EXTRACTION:
            # Generate entity extraction test data
            test_data = [
                {
                    "input": "Apple Inc. is a technology company headquartered in Cupertino, California. Tim Cook serves as the CEO.",
                    "expected": "(Apple Inc., TECHNOLOGY_COMPANY, headquartered in, Cupertino, California)\n(Tim Cook, PERSON, CEO_OF, Apple Inc.)",
                }
                for _ in range(sample_size)
            ]

        elif family == PromptFamily.SUMMARIZATION:
            # Generate summarization test data
            test_data = [
                {
                    "input": "The quick brown fox jumps over the lazy dog. This pangram contains all letters of the alphabet.",
                    "expected": "A pangram containing all alphabet letters describes a fox jumping over a dog.",
                }
                for _ in range(sample_size)
            ]

        elif family == PromptFamily.QUERY_PROCESSING:
            # Generate query processing test data
            test_data = [
                {
                    "input": "What companies did Tim Cook work for?",
                    "expected": ["Tim Cook", "companies", "work history"],
                }
                for _ in range(sample_size)
            ]

        else:
            # Generic test data for other families
            test_data = [
                {
                    "input": f"Test input for {family.value}",
                    "expected": "Expected output for test case",
                }
                for _ in range(sample_size)
            ]

        return test_data

    async def _evaluate_metric(
        self,
        family: PromptFamily,
        prompt: str,
        model: str,
        test_data: List[Dict[str, Any]],
        metric: str,
    ) -> float:
        """Evaluate a specific metric for a prompt."""

        if not test_data:
            return 0.0

        scores = []

        for test_case in test_data:
            try:
                # Run the prompt on test case
                result = await self._run_prompt(prompt, test_case["input"], model)

                # Calculate metric-specific score
                if metric in ["entity_f1", "relationship_f1", "precision", "recall"]:
                    # F1-score metrics
                    score = self._calculate_f1_score(
                        result, test_case.get("expected", "")
                    )
                elif metric in ["rouge_l", "rouge_1", "rouge_2"]:
                    # ROUGE metrics for summarization
                    score = self._calculate_rouge_score(
                        result, test_case.get("expected", ""), metric
                    )
                elif metric in ["accuracy", "completeness", "relevance"]:
                    # Quality metrics
                    score = self._calculate_quality_score(
                        result, test_case.get("expected", "")
                    )
                elif metric in ["efficiency", "compression_ratio", "readability"]:
                    # Performance metrics
                    score = self._calculate_performance_metric(result, metric)
                else:
                    # Default metric
                    score = self._calculate_generic_score(
                        result, test_case.get("expected", "")
                    )

                scores.append(score)

            except Exception as e:
                self.logger.warning(f"Failed to evaluate test case: {e}")
                scores.append(0.0)
                continue

        return sum(scores) / len(scores) if scores else 0.0

    async def _run_prompt(self, prompt: str, input_text: str, model: str) -> str:
        """Run a prompt and get the result."""
        # This would use the actual LLM through LightRAG
        # For now, return a simulated result
        return f"Simulated output for {input_text[:50]}..."

    def _calculate_f1_score(self, predicted: str, expected: str) -> float:
        """Calculate F1 score between predicted and expected."""
        # Simplified F1 calculation
        if not predicted or not expected:
            return 0.0

        # Tokenize and calculate precision/recall
        pred_tokens = set(predicted.lower().split())
        exp_tokens = set(expected.lower().split())

        intersection = pred_tokens.intersection(exp_tokens)

        if not intersection:
            return 0.0

        precision = len(intersection) / len(pred_tokens)
        recall = len(intersection) / len(exp_tokens)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def _calculate_rouge_score(
        self, predicted: str, expected: str, rouge_type: str
    ) -> float:
        """Calculate ROUGE score for summarization."""
        # Simplified ROUGE calculation
        if not predicted or not expected:
            return 0.0

        pred_tokens = predicted.lower().split()
        exp_tokens = expected.lower().split()

        if rouge_type == "rouge_1":
            # Unigram overlap
            pred_set = set(pred_tokens)
            exp_set = set(exp_tokens)
            intersection = pred_set.intersection(exp_set)
            score = len(intersection) / len(exp_set) if exp_set else 0.0

        elif rouge_type == "rouge_2":
            # Bigram overlap
            pred_bigrams = set(zip(pred_tokens[:-1], pred_tokens[1:]))
            exp_bigrams = set(zip(exp_tokens[:-1], exp_tokens[1:]))
            intersection = pred_bigrams.intersection(exp_bigrams)
            score = len(intersection) / len(exp_bigrams) if exp_bigrams else 0.0

        else:
            # Longest common subsequence (simplified)
            score = (
                self._calculate_lcs_length(pred_tokens, exp_tokens) / len(exp_tokens)
                if exp_tokens
                else 0.0
            )

        return score

    def _calculate_lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Calculate length of longest common subsequence."""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def _calculate_quality_score(self, predicted: str, expected: str) -> float:
        """Calculate quality score (accuracy, completeness, relevance)."""
        # Simplified quality calculation
        if not predicted:
            return 0.0

        # Length consistency (completeness)
        length_ratio = min(len(predicted) / max(len(expected), 1), 2.0) / 2.0

        # Keyword overlap (relevance)
        pred_words = set(predicted.lower().split())
        exp_words = set(expected.lower().split())
        overlap = len(pred_words.intersection(exp_words))
        keyword_ratio = overlap / len(exp_words) if exp_words else 0.0

        return (length_ratio + keyword_ratio) / 2.0

    def _calculate_performance_metric(self, result: str, metric: str) -> float:
        """Calculate performance-based metrics."""
        if metric == "efficiency":
            # Simulate efficiency based on length
            return min(1.0, 100 / max(len(result), 1))

        elif metric == "compression_ratio":
            # Simulate compression ratio
            return min(1.0, len(result) / 50)  # Target length 50 chars

        elif metric == "readability":
            # Simulate readability based on sentence structure
            sentences = result.split(".")
            avg_sentence_length = sum(len(s.split()) for s in sentences) / max(
                len(sentences), 1
            )
            return max(0.0, 1.0 - abs(avg_sentence_length - 15) / 15)

        return 0.5  # Default score

    def _calculate_generic_score(self, predicted: str, expected: str) -> float:
        """Calculate generic similarity score."""
        if not predicted or not expected:
            return 0.0

        pred_words = set(predicted.lower().split())
        exp_words = set(expected.lower().split())

        if not exp_words:
            return 0.0

        overlap = len(pred_words.intersection(exp_words))
        return overlap / len(exp_words)

    def _calculate_improvement(
        self, baseline: Dict[str, float], optimized: Dict[str, float]
    ) -> float:
        """Calculate percentage improvement over baseline."""

        improvements = []

        for metric, baseline_value in baseline.items():
            if metric in optimized:
                optimized_value = optimized[metric]

                if baseline_value > 0:
                    improvement = (optimized_value - baseline_value) / baseline_value
                    improvements.append(improvement)

        return sum(improvements) / len(improvements) if improvements else 0.0

    def _calculate_overall_score(
        self, performance: Dict[str, float], family: PromptFamily
    ) -> float:
        """Calculate overall score for a variant."""

        # Different weightings for different families
        if family == PromptFamily.ENTITY_EXTRACTION:
            weights = {
                "entity_f1": 0.4,
                "relationship_f1": 0.4,
                "format_compliance": 0.2,
            }
        elif family == PromptFamily.SUMMARIZATION:
            weights = {"rouge_l": 0.4, "rouge_1": 0.3, "rouge_2": 0.3}
        elif family == PromptFamily.QUERY_PROCESSING:
            weights = {
                "retrieval_precision": 0.5,
                "query_coverage": 0.3,
                "efficiency": 0.2,
            }
        else:
            # Default equal weighting
            metrics = list(performance.keys())
            weights = {metric: 1.0 / len(metrics) for metric in metrics}

        overall_score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in performance:
                overall_score += performance[metric] * weight
                total_weight += weight

        return overall_score / total_weight if total_weight > 0 else 0.0

    async def _get_dspy_prompt(self, module_name: str) -> Optional[str]:
        """Get DSPy prompt for a module name."""
        # This would retrieve the actual DSPy prompt
        # For now, return a simulated prompt
        return f"DSPy optimized prompt for {module_name}"

    async def optimize_all_families(
        self, models: Optional[List[str]] = None, parallel: bool = True
    ) -> Dict[PromptFamily, List[OptimizationResult]]:
        """Optimize all prompt families."""

        all_results = {}

        if parallel:
            # Run optimizations in parallel
            tasks = []
            for family in PromptFamily:
                task = self.optimize_family(family, models)
                tasks.append(task)

            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            for i, (family, result) in enumerate(zip(PromptFamily, results_list)):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to optimize {family.value}: {result}")
                    all_results[family] = []
                else:
                    all_results[family] = result

        else:
            # Run optimizations sequentially
            for family in PromptFamily:
                try:
                    results = await self.optimize_family(family, models)
                    all_results[family] = results
                except Exception as e:
                    self.logger.error(f"Failed to optimize {family.value}: {e}")
                    all_results[family] = []

        # Save results
        await self._save_optimization_results(all_results)

        return all_results

    async def _save_optimization_results(
        self, all_results: Dict[PromptFamily, List[OptimizationResult]]
    ):
        """Save optimization results to file."""

        results_data = {"timestamp": datetime.now().isoformat(), "families": {}}

        for family, results in all_results.items():
            results_data["families"][family.value] = {
                "family": family.value,
                "results": [asdict(r) for r in results],
                "total_results": len(results),
                "average_improvement": sum(r.improvement_percentage for r in results)
                / len(results)
                if results
                else 0,
            }

        # Save to file
        results_file = Path("prompt_family_optimization_results.json")
        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        self.logger.info(f"Optimization results saved to {results_file}")

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization history and performance."""

        summary = {
            "total_families": len(self.families),
            "families": {},
            "overall_stats": {
                "total_optimizations": 0,
                "average_improvement": 0.0,
                "best_improvement": 0.0,
                "optimization_frequency": {},
            },
        }

        all_improvements = []

        for family, family_config in self.families.items():
            family_summary = {
                "variants_count": len(family_config.dspy_variants),
                "optimization_targets": family_config.optimization_targets,
                "optimization_schedule": family_config.optimization_schedule,
                "latest_optimization": None,
            }

            if family.value in self.optimization_history:
                history = self.optimization_history[family.value]
                results = history.get("results", [])

                if results:
                    latest_result = results[-1]
                    family_summary["latest_optimization"] = {
                        "timestamp": history["timestamp"],
                        "improvement": latest_result["improvement_percentage"],
                        "variant": latest_result["variant_name"],
                    }

                    all_improvements.append(latest_result["improvement_percentage"])

            summary["families"][family.value] = family_summary

        # Calculate overall stats
        if all_improvements:
            summary["overall_stats"]["total_optimizations"] = len(all_improvements)
            summary["overall_stats"]["average_improvement"] = sum(
                all_improvements
            ) / len(all_improvements)
            summary["overall_stats"]["best_improvement"] = max(all_improvements)

        return summary


# CLI interface
async def main():
    """Run prompt family optimization from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DSPy Extended Prompt Family Optimization"
    )
    parser.add_argument(
        "--family",
        choices=[f.value for f in PromptFamily],
        help="Specific family to optimize",
    )
    parser.add_argument(
        "--models", nargs="+", default=["1.5b", "3b", "7b"], help="Models to optimize"
    )
    parser.add_argument(
        "--optimizer",
        choices=["BootstrapFewShot", "MIPROv2"],
        default="BootstrapFewShot",
        help="DSPy optimizer",
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Run optimizations in parallel"
    )
    parser.add_argument("--all", action="store_true", help="Optimize all families")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create optimizer
    optimizer = PromptFamilyOptimizer()

    if args.all:
        print("🚀 Starting optimization of all prompt families...")
        results = await optimizer.optimize_all_families(
            models=args.models, parallel=args.parallel
        )

        print(f"✅ Optimization completed!")
        for family, family_results in results.items():
            if family_results:
                avg_improvement = sum(
                    r.improvement_percentage for r in family_results
                ) / len(family_results)
                print(
                    f"  {family.value}: {len(family_results)} variants, avg {avg_improvement:.1%} improvement"
                )

        # Show summary
        summary = optimizer.get_optimization_summary()
        print(f"\n📊 Overall Statistics:")
        print(f"  Total families: {summary['total_families']}")
        print(
            f"  Average improvement: {summary['overall_stats']['average_improvement']:.1%}"
        )
        print(f"  Best improvement: {summary['overall_stats']['best_improvement']:.1%}")

    elif args.family:
        print(f"🎯 Optimizing family: {args.family}")
        family = PromptFamily(args.family)
        results = await optimizer.optimize_family(family, models=args.models)

        print(f"✅ Optimization completed for {args.family}!")
        for result in results:
            print(
                f"  {result.model}: {result.variant_name} ({result.improvement_percentage:.1%} improvement)"
            )

    else:
        print("❌ Please specify --family or --all")
        return

    print(f"📁 Detailed results saved to: prompt_family_optimization_results.json")


if __name__ == "__main__":
    asyncio.run(main())
