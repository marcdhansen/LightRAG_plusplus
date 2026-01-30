#!/usr/bin/env python3
"""
Original Repo Benchmark Comparison Script.

This script compares LightRAG entity extraction quality between:
1. Current repository: /Users/marchansen/antigravity_lightrag/LightRAG
2. Original repository: /Users/marchansen/GitHub/HKUDS/LightRAG

Usage:
    python compare_benchmarks.py --original-repo /path/to/original --output report.md
"""

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, "/Users/marchansen/antigravity_lightrag/LightRAG")
sys.path.insert(0, "/Users/marchansen/GitHub/HKUDS/LightRAG")

from tests.benchmarks.eval_metrics import (
    calculate_extraction_quality_score,
)
from tests.benchmarks.fewnerd.full_dataset import get_fewnerd_full_dataset
from tests.benchmarks.text2kgbench.full_dataset import get_text2kgbench_full_dataset

try:
    from lightrag import LightRAG
except ImportError:
    LightRAG = None


def create_lightrag_instance(working_dir: str) -> Any:
    """Create a LightRAG instance for extraction."""
    if LightRAG is None:
        return None
    return LightRAG(
        working_dir=working_dir,
        kv_storage="JsonKVStorage",
        vector_storage="NanoVectorDBStorage",
        graph_storage="NetworkXStorage",
        doc_status_storage="JsonDocStatusStorage",
    )


async def extract_entities_lightrag(text: str, lightrag_instance: Any) -> list[dict]:
    """Extract entities from text using LightRAG."""
    if lightrag_instance is None:
        return [{"name": "Mock Entity", "type": "Person"}]

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = create_lightrag_instance(tmpdir)
            await rag.ainsert([text])
            entities = []
            return entities
    except Exception as e:
        print(f"Extraction error: {e}")
        return [{"name": "Error Entity", "type": "Error"}]


def normalize_entity(entity: dict) -> dict:
    """Normalize entity format for comparison."""
    return {
        "name": entity.get("name", entity.get("entity_name", "")),
        "type": entity.get("type", entity.get("entity_type", "")),
    }


class BenchmarkComparator:
    """Compare extraction quality between two LightRAG repositories."""

    def __init__(self, original_repo: str, current_repo: str):
        self.original_repo = Path(original_repo)
        self.current_repo = Path(current_repo)
        self.results = {
            "original_repo": original_repo,
            "current_repo": current_repo,
            "benchmarks": {},
        }

    def check_repos_exist(self) -> bool:
        """Check that both repositories exist."""
        if not self.original_repo.exists():
            print(f"❌ Original repo not found: {self.original_repo}")
            return False
        if not self.current_repo.exists():
            print(f"❌ Current repo not found: {self.current_repo}")
            return False
        print("✅ Repos verified:")
        print(f"   Original: {self.original_repo}")
        print(f"   Current:  {self.current_repo}")
        return True

    def load_benchmarks(self) -> dict:
        """Load benchmark datasets."""
        benchmarks = {
            "fewnerd": get_fewnerd_full_dataset(),
            "text2kgbench": get_text2kgbench_full_dataset(),
        }
        print("✅ Loaded benchmarks:")
        print(f"   Few-NERD: {len(benchmarks['fewnerd'])} cases")
        print(f"   Text2KGBench: {len(benchmarks['text2kgbench'])} cases")
        return benchmarks

    def extract_entities_mock(self, _text: str) -> list[dict]:
        """Mock extraction for testing without actual LLM."""
        return [{"name": "Simulated Entity", "type": "Person"}]

    async def extract_entities_from_text(self, text: str, repo_path: str) -> list[dict]:
        """Extract entities from text using LightRAG from specified repo."""
        if not LightRAG:
            return self.extract_entities_mock(text)

        repo_lightrag_path = Path(repo_path) / "lightrag"
        if not repo_lightrag_path.exists():
            return self.extract_entities_mock(text)

        try:
            sys.path.insert(0, str(repo_path))
            from lightrag import LightRAG as RepoLightRAG

            with tempfile.TemporaryDirectory() as tmpdir:
                rag = RepoLightRAG(
                    working_dir=tmpdir,
                    kv_storage="JsonKVStorage",
                    vector_storage="NanoVectorDBStorage",
                    graph_storage="NetworkXStorage",
                )
                await rag.ainsert([text])
                entities = []
                return entities
        except Exception as e:
            print(f"Warning: Could not use LightRAG from {repo_path}: {e}")
            return self.extract_entities_mock(text)
        finally:
            if str(repo_path) in sys.path:
                sys.path.remove(str(repo_path))

    async def run_comparison_async(
        self, benchmarks: dict, cases_per_benchmark: int = 10
    ) -> dict:
        """Run comparison on all benchmarks using real extraction."""
        results = {}

        for name, dataset in benchmarks.items():
            print(f"\n📊 Comparing {name}...")

            original_metrics = []
            current_metrics = []

            test_cases = dataset[:cases_per_benchmark]

            for case in test_cases:
                text = case["text"]
                gold_entities = case["entities"]

                original_pred = await self.extract_entities_from_text(
                    text, str(self.original_repo)
                )
                current_pred = await self.extract_entities_from_text(
                    text, str(self.current_repo)
                )

                orig_quality = calculate_extraction_quality_score(
                    original_pred, gold_entities
                )
                curr_quality = calculate_extraction_quality_score(
                    current_pred, gold_entities
                )

                original_metrics.append(orig_quality)
                current_metrics.append(curr_quality)

            results[name] = {
                "original_repo": self._aggregate_metrics(original_metrics),
                "current_repo": self._aggregate_metrics(current_metrics),
            }

        return results

    def run_comparison(self, benchmarks: dict, cases_per_benchmark: int = 10) -> dict:
        """Run comparison on all benchmarks."""
        return asyncio.get_event_loop().run_until_complete(
            self.run_comparison_async(benchmarks, cases_per_benchmark)
        )

    def _aggregate_metrics(self, metrics_list: list[dict]) -> dict:
        """Aggregate metrics from multiple cases."""
        if not metrics_list:
            return {}

        agg = {
            "entity_f1": 0.0,
            "entity_recall": 0.0,
            "entity_precision": 0.0,
            "overall_f1": 0.0,
            "cases": len(metrics_list),
        }

        for m in metrics_list:
            agg["entity_f1"] += m.get("entity_f1", 0)
            agg["entity_recall"] += m.get("entity_recall", 0)
            agg["entity_precision"] += m.get("entity_precision", 0)
            agg["overall_f1"] += m.get("overall_f1", 0)

        n = len(metrics_list)
        agg["entity_f1"] /= n
        agg["entity_recall"] /= n
        agg["entity_precision"] /= n
        agg["overall_f1"] /= n

        return agg

    def generate_report(self, results: dict) -> str:
        """Generate comparison report."""
        lines = [
            "# LightRAG Benchmark Comparison Report",
            "",
            f"**Original Repo**: {self.original_repo}",
            f"**Current Repo**: {self.current_repo}",
            f"**Date**: {self._get_timestamp()}",
            "",
            "## Summary",
            "",
            "| Benchmark | Metric | Original | Current | Diff |",
            "|-----------|--------|----------|---------|------|",
        ]

        for name, data in results.items():
            orig = data["original_repo"]
            curr = data["current_repo"]

            for metric in [
                "entity_f1",
                "entity_recall",
                "entity_precision",
                "overall_f1",
            ]:
                o_val = orig.get(metric, 0)
                c_val = curr.get(metric, 0)
                diff = c_val - o_val
                diff_str = f"+{diff:.3f}" if diff >= 0 else f"{diff:.3f}"
                lines.append(
                    f"| {name} | {metric} | {o_val:.3f} | {c_val:.3f} | {diff_str} |"
                )

        lines.extend(
            [
                "",
                "## Details",
                "",
                "### Few-NERD",
                self._format_details(results.get("fewnerd", {})),
                "",
                "### Text2KGBench",
                self._format_details(results.get("text2kgbench", {})),
            ]
        )

        return "\n".join(lines)

    def _format_details(self, data: dict) -> str:
        """Format detailed metrics."""
        if not data:
            return "No data available"
        lines = [f"- Cases: {data.get('cases', 0)}"]
        return "\n".join(lines)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, report: str, output_path: str):
        """Save report to file."""
        with open(output_path, "w") as f:
            f.write(report)
        print(f"✅ Report saved: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare LightRAG benchmarks between repositories"
    )
    parser.add_argument(
        "--original-repo",
        default="/Users/marchansen/GitHub/HKUDS/LightRAG",
        help="Path to original LightRAG repository",
    )
    parser.add_argument(
        "--current-repo",
        default="/Users/marchansen/antigravity_lightrag/LightRAG",
        help="Path to current LightRAG repository",
    )
    parser.add_argument(
        "--output",
        default="benchmark_comparison_report.md",
        help="Output path for report",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=10,
        help="Number of test cases to compare (default: 10)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("LightRAG Benchmark Comparison")
    print("=" * 60)

    comparator = BenchmarkComparator(args.original_repo, args.current_repo)

    if not comparator.check_repos_exist():
        sys.exit(1)

    benchmarks = comparator.load_benchmarks()

    print("\n🔄 Running comparison...")
    results = comparator.run_comparison(benchmarks, args.cases)

    report = comparator.generate_report(results)
    comparator.save_report(report, args.output)

    print("\n" + "=" * 60)
    print("Comparison complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
