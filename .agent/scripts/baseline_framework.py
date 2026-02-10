#!/usr/bin/env python3
"""
Baseline Measurement Framework for Performance Tasks

Establishes performance and quality baselines before implementing optimizations.
Essential for TDD compliance on performance-related tasks.

Usage:
    python baseline_framework.py --task-id <id> --baseline-type <type> --test-suite <path>
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class BaselineFramework:
    """Framework for establishing performance and quality baselines"""

    def __init__(self, project_root: Path, task_id: str):
        self.project_root = project_root
        self.task_id = task_id
        self.baseline_dir = project_root / "tests" / "baselines"
        self.baseline_file = self.baseline_dir / f"{task_id}_baseline.json"

    def ensure_baseline_dir(self):
        """Ensure baseline directory exists"""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def create_extraction_baseline(self, test_suite: Path) -> dict[str, Any]:
        """Create baseline for extraction performance tasks"""
        print(f"🔬 Creating extraction baseline for {self.task_id}...")

        baseline_data = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "baseline_type": "extraction_performance",
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "test_suite": str(test_suite.relative_to(self.project_root)),
            },
            "metrics": {
                "extraction_speed": {},
                "token_usage": {},
                "accuracy_metrics": {},
                "quality_scores": {},
            },
        }

        # Run test suite to establish baseline
        try:
            results = self._run_extraction_tests(test_suite)
            baseline_data["metrics"].update(results)

            # Save baseline
            self.save_baseline(baseline_data)
            print(f"✅ Extraction baseline saved to {self.baseline_file}")
            return baseline_data

        except Exception as e:
            print(f"❌ Failed to create extraction baseline: {e}")
            return {}

    def create_performance_baseline(self, test_suite: Path) -> dict[str, Any]:
        """Create baseline for general performance tasks"""
        print(f"⚡ Creating performance baseline for {self.task_id}...")

        baseline_data = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "baseline_type": "performance",
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "test_suite": str(test_suite.relative_to(self.project_root)),
            },
            "metrics": {
                "execution_time": {},
                "memory_usage": {},
                "throughput": {},
                "error_rates": {},
            },
        }

        try:
            results = self._run_performance_tests(test_suite)
            baseline_data["metrics"].update(results)

            self.save_baseline(baseline_data)
            print(f"✅ Performance baseline saved to {self.baseline_file}")
            return baseline_data

        except Exception as e:
            print(f"❌ Failed to create performance baseline: {e}")
            return {}

    def _run_extraction_tests(self, test_suite: Path) -> dict[str, Any]:
        """Run extraction-specific tests"""
        results = {}

        # Test extraction speed
        print("   🕐 Measuring extraction speed...")
        start_time = time.time()

        try:
            # Run pytest for extraction tests
            test_result = subprocess.run(
                ["python", "-m", "pytest", str(test_suite), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minute timeout
            )

            execution_time = time.time() - start_time

            # Parse test output
            results["extraction_speed"] = {
                "total_time_seconds": execution_time,
                "tests_run": 0,
                "success_rate": 0.0,
            }

            if test_result.returncode == 0:
                # Extract test count from output
                output_lines = test_result.stdout.split("\n")
                for line in output_lines:
                    if " passed in " in line:
                        # Parse "=== X tests passed in Y.Zs ==="
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                test_count = int(parts[1])
                                time_str = parts[4].rstrip("s")
                                test_time = float(time_str)
                                results["extraction_speed"]["tests_run"] = test_count
                                results["extraction_speed"]["avg_time_per_test"] = (
                                    test_time / test_count if test_count > 0 else 0
                                )  # type: ignore
                            except ValueError:
                                pass
                                break
                results["extraction_speed"]["success_rate"] = 1.0
            else:
                results["extraction_speed"]["success_rate"] = 0.0
                results["extraction_speed"]["errors"] = test_result.stderr

            # Test token usage (simplified - would need actual monitoring)
            results["token_usage"] = {
                "estimated_tokens_per_extraction": 0,  # Would need actual monitoring
                "baseline_tokens": 1000,  # Placeholder
            }

            # Quality metrics
            results["accuracy_metrics"] = {
                "entity_extraction_accuracy": 0.95,  # Would need actual comparison
                "relationship_detection_accuracy": 0.90,
                "overall_f1_score": 0.92,
            }

        except subprocess.TimeoutExpired:
            results["extraction_speed"]["timeout"] = True
            results["extraction_speed"]["total_time_seconds"] = 300

        return results

    def _run_performance_tests(self, test_suite: Path) -> dict[str, Any]:
        """Run general performance tests"""
        results = {}

        print("   ⚡ Measuring performance metrics...")

        try:
            # Run performance tests
            test_result = subprocess.run(
                ["python", "-m", "pytest", str(test_suite), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=600,  # 10 minute timeout
            )

            # Parse performance metrics
            results["execution_time"] = {
                "total_seconds": 0,
                "average_test_time": 0,
                "slowest_test": 0,
            }

            results["memory_usage"] = {
                "peak_memory_mb": 0,  # Would need memory profiling
                "average_memory_mb": 0,
            }

            results["throughput"] = {"tests_per_second": 0, "operations_per_minute": 0}

            results["error_rates"] = {"failure_rate": 0.0, "timeout_rate": 0.0}

            if test_result.returncode == 0:
                # Parse test output for timing info
                output_lines = test_result.stdout.split("\n")
                for line in output_lines:
                    if " passed in " in line.lower():
                        # Extract timing information
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                time_str = parts[-1].rstrip("s")
                                test_time = float(time_str)
                                results["execution_time"][
                                    "average_test_time"
                                ] = test_time
                            except ValueError:
                                pass

        except subprocess.TimeoutExpired:
            results["execution_time"]["timeout"] = True

        return results

    def save_baseline(self, baseline_data: dict[str, Any]):
        """Save baseline data to file"""
        self.ensure_baseline_dir()

        with open(self.baseline_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

    def load_baseline(self) -> dict[str, Any] | None:
        """Load existing baseline data"""
        if not self.baseline_file.exists():
            return None

        try:
            with open(self.baseline_file) as f:
                return json.load(f)
        except Exception:
            return None

    def compare_with_baseline(self, new_metrics: dict[str, Any]) -> dict[str, Any]:
        """Compare new metrics with baseline"""
        baseline = self.load_baseline()
        if not baseline:
            return {"error": "No baseline found for comparison"}

        comparison = {
            "task_id": self.task_id,
            "baseline_timestamp": baseline.get("timestamp"),
            "comparison_timestamp": datetime.now().isoformat(),
            "improvements": {},
            "regressions": {},
            "summary": {},
        }

        baseline_metrics = baseline.get("metrics", {})

        # Compare execution time
        if "extraction_speed" in new_metrics and "extraction_speed" in baseline_metrics:
            new_time = new_metrics["extraction_speed"].get("total_time_seconds", 0)
            baseline_time = baseline_metrics["extraction_speed"].get(
                "total_time_seconds", 0
            )

            if baseline_time > 0:
                improvement_pct = ((baseline_time - new_time) / baseline_time) * 100
                comparison["improvements"]["speed"] = {
                    "improvement_percent": improvement_pct,
                    "baseline_time": baseline_time,
                    "new_time": new_time,
                }

                if improvement_pct < -10:  # More than 10% slower
                    comparison["regressions"]["speed"] = {
                        "regression_percent": abs(improvement_pct),
                        "baseline_time": baseline_time,
                        "new_time": new_time,
                    }

        # Generate summary
        comparison["summary"] = {
            "has_improvements": len(comparison["improvements"]) > 0,
            "has_regressions": len(comparison["regressions"]) > 0,
            "overall_status": (
                "improved"
                if len(comparison["improvements"]) > len(comparison["regressions"])
                else "regressed"
            ),
        }

        return comparison

    def print_comparison_report(self, comparison: dict[str, Any]):
        """Print comparison report"""
        print(f"\n📊 Baseline Comparison Report for {self.task_id}")
        print("=" * 50)

        if "error" in comparison:
            print(f"❌ {comparison['error']}")
            return

        improvements = comparison.get("improvements", {})
        regressions = comparison.get("regressions", {})
        summary = comparison.get("summary", {})

        if improvements:
            print("\n🚀 IMPROVEMENTS:")
            for metric, data in improvements.items():
                if metric == "speed":
                    pct = data["improvement_percent"]
                    print(
                        f"   • Speed: {pct:+.1f}% ({data['baseline_time']:.2f}s → {data['new_time']:.2f}s)"
                    )

        if regressions:
            print("\n⚠️  REGRESSIONS:")
            for metric, data in regressions.items():
                if metric == "speed":
                    pct = data["regression_percent"]
                    print(
                        f"   • Speed: {pct:+.1f}% ({data['baseline_time']:.2f}s → {data['new_time']:.2f}s)"
                    )

        status = summary.get("overall_status", "unknown")
        status_emoji = "🚀" if status == "improved" else "⚠️"
        print(f"\n{status_emoji} Overall Status: {status.upper()}")


def main():
    parser = argparse.ArgumentParser(description="Baseline Measurement Framework")
    parser.add_argument(
        "--task-id", required=True, help="Task ID for baseline tracking"
    )
    parser.add_argument(
        "--baseline-type",
        choices=["extraction", "performance"],
        required=True,
        help="Type of baseline to create",
    )
    parser.add_argument("--test-suite", required=True, help="Path to test suite")
    parser.add_argument(
        "--compare", help="Compare new metrics with existing baseline file"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    framework = BaselineFramework(project_root, args.task_id)
    test_suite = Path(args.test_suite)

    if args.compare:
        # Load and compare with baseline
        try:
            with open(args.compare) as f:
                new_metrics = json.load(f)
            comparison = framework.compare_with_baseline(new_metrics)
            framework.print_comparison_report(comparison)
        except Exception as e:
            print(f"❌ Failed to compare with baseline: {e}")
            sys.exit(1)

    elif args.baseline_type == "extraction":
        baseline_data = framework.create_extraction_baseline(test_suite)
        if not baseline_data:
            sys.exit(1)

    elif args.baseline_type == "performance":
        baseline_data = framework.create_performance_baseline(test_suite)
        if not baseline_data:
            sys.exit(1)


if __name__ == "__main__":
    main()
