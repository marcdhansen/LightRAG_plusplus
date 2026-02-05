#!/usr/bin/env python3
"""
TDD Gate Validator for AutoFlightDirector

Strict TDD validation that blocks commits when test requirements are not met.
Supports emergency bypass with justification.

Usage:
    python tdd_gate_validator.py [--bypass-justification "reason"] [--task-id <id>]
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import yaml, but make it optional
try:
    import yaml
except ImportError:
    yaml = None


# Integration with Adaptive SOP System
def get_adaptive_tdd_config():
    """Get TDD configuration recommendations from adaptive system"""
    try:
        script_dir = Path(__file__).parent
        engine_script = script_dir / "adaptive_sop_engine.sh"

        if engine_script.exists():
            result = subprocess.run(
                [str(engine_script), "--action", "analyze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                analysis = json.loads(result.stdout)
                return analysis.get("recommendations", [])
    except Exception as e:
        print(f"Warning: Could not get adaptive TDD config: {e}", file=sys.stderr)

    return []


def record_tdd_performance(performance_data):
    """Record TDD gate performance for adaptive learning"""
    try:
        script_dir = Path(__file__).parent
        learn_dir = script_dir.parent / "learn"
        learn_dir.mkdir(exist_ok=True)

        performance_file = learn_dir / "tdd_performance.jsonl"

        with open(performance_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "performance": performance_data,
                    }
                )
                + "\n"
            )
    except Exception as e:
        print(f"Warning: Could not record TDD performance: {e}", file=sys.stderr)


class TDDValidator:
    """Comprehensive TDD validation for task compliance"""

    def __init__(self, project_root: Path, bypass_justification: str | None = None):
        self.project_root = project_root
        self.bypass_justification = bypass_justification
        self.config = self._load_tdd_config()

    def _load_tdd_config(self) -> dict:
        """Load TDD configuration from various sources"""
        config_file = self.project_root / ".agent" / "config" / "tdd_config.yaml"

        default_config = {
            "tdd_gates": {
                "enabled": True,
                "coverage_threshold": 80,
                "unit_tests_required": True,
                "integration_tests_for_complex_tasks": True,
                "baseline_required_for_performance_tasks": True,
                "max_complexity_without_tests": 3,
            },
            "task_complexity_thresholds": {"simple": 3, "medium": 7, "complex": 10},
            "performance_task_patterns": [
                r".*optimization.*",
                r".*benchmark.*",
                r".*performance.*",
                r".*speed.*",
                r".*extraction.*prompt.*",
            ],
        }

        if config_file.exists():
            try:
                with open(config_file) as f:
                    if yaml is not None:
                        user_config = yaml.safe_load(f) or {}
                    else:
                        # Simple YAML parser fallback
                        user_config = {}
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Failed to load TDD config: {e}")

        return default_config

    def validate_task_tdd_readiness(self, task_id: str | None = None) -> dict[str, Any]:
        """Main validation entry point"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {},  # type: Dict[str, Any]
            "bypass_used": bool(self.bypass_justification),
        }

        # Emergency bypass check
        if self.bypass_justification:
            result["warnings"].append(
                f"Emergency bypass used: {self.bypass_justification}"
            )
            return result

        # Get current task information
        task_info = self._get_current_task_info(task_id)
        result["task_info"] = task_info

        if not self.config["tdd_gates"]["enabled"]:
            result["warnings"].append("TDD gates are disabled in configuration")
            return result

        # Core TDD validations
        self._validate_test_file_existence(result)
        self._validate_test_quality(result)
        self._validate_test_coverage(result)
        self._validate_task_specific_requirements(result, task_info)

        result["valid"] = len(result["errors"]) == 0

        return result

    def _get_current_task_info(self, task_id: str | None = None) -> dict:
        """Get information about current task"""
        task_info = {
            "id": task_id,
            "type": "unknown",
            "complexity": 5,
            "files_modified": [],
        }

        # Try to get from Beads if task_id provided
        if task_id:
            try:
                result = subprocess.run(
                    ["bd", "show", task_id, "--json"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )
                if result.returncode == 0:
                    task_data = json.loads(result.stdout)
                    task_info.update(
                        {
                            "title": task_data.get("title", ""),
                            "description": task_data.get("description", ""),
                            "labels": task_data.get("labels", []),
                            "priority": task_data.get("priority", "P2"),
                        }
                    )
            except Exception:
                pass

        # Analyze git changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD^", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.stdout:
                task_info["files_modified"] = result.stdout.strip().split("\n")
        except Exception:
            pass

        # Determine task type and complexity
        task_info.update(self._classify_task(task_info))

        return task_info

    def _classify_task(self, task_info: dict) -> dict:
        """Classify task type and complexity based on patterns"""
        title = task_info.get("title", "").lower()
        description = task_info.get("description", "").lower()
        files = task_info.get("files_modified", [])

        # Task type classification
        task_type = "standard"
        complexity = 5

        # Performance task detection
        perf_patterns = self.config["performance_task_patterns"]
        if any(
            re.match(pattern, title) or re.match(pattern, description)
            for pattern in perf_patterns
        ):
            task_type = "performance"
            complexity += 2

        # File-based complexity analysis
        for file_path in files:
            if "lightrag/" in file_path and file_path.endswith(".py"):
                try:
                    with open(self.project_root / file_path) as f:
                        content = f.read()
                        tree = ast.parse(content)
                        # Simple complexity based on AST nodes
                        complexity += len(
                            [
                                node
                                for node in ast.walk(tree)
                                if isinstance(node, ast.FunctionDef | ast.ClassDef)
                            ]
                        )
                except Exception:
                    pass

        return {
            "type": task_type,
            "complexity": min(
                complexity, self.config["task_complexity_thresholds"]["complex"]
            ),
            "requires_baseline": task_type == "performance",
            "requires_integration_tests": complexity
            > self.config["task_complexity_thresholds"]["simple"],
        }

    def _validate_test_file_existence(self, result: dict):
        """Validate that test files exist for modified code"""
        modified_py_files = [
            f
            for f in result["task_info"]["files_modified"]
            if f.startswith("lightrag/") and f.endswith(".py")
        ]

        if not modified_py_files:
            return

        test_files = set()
        for py_file in modified_py_files:
            # Expected test file paths
            test_file_candidates = [
                f"tests/test_{Path(py_file).stem}.py",
                f"tests/{Path(py_file).parent.name}/test_{Path(py_file).stem}.py",
                f"test_{Path(py_file).stem}.py",
            ]

            for candidate in test_file_candidates:
                if (self.project_root / candidate).exists():
                    test_files.add(candidate)
                    break
            else:
                result["errors"].append(
                    f"No test file found for {py_file}. Expected: {', '.join(test_file_candidates)}"
                )

        result["metrics"]["test_files_found"] = len(test_files)
        result["metrics"]["source_files_modified"] = len(modified_py_files)

    def _validate_test_quality(self, result: dict):
        """Validate test file quality and structure"""
        test_files = self._find_test_files()

        if not test_files:
            result["errors"].append("No test files found in the repository")
            return

        quality_metrics = {
            "files_analyzed": 0,
            "test_functions": 0,
            "assertions": 0,
            "quality_score": 0,
        }

        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                    tree = ast.parse(content)

                    # Count test functions
                    test_functions = [
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name.startswith("test_")
                    ]
                    quality_metrics["test_functions"] += len(test_functions)

                    # Count assertions (simple heuristic)
                    quality_metrics["assertions"] += content.count("assert")
                    quality_metrics["files_analyzed"] += 1

                    # Basic quality checks
                    for func in test_functions:
                        if len(func.body) < 2:
                            result["warnings"].append(
                                f"Test function {test_file.name}::{func.name} appears empty or minimal"
                            )

            except Exception as e:
                result["warnings"].append(
                    f"Could not analyze test file {test_file}: {e}"
                )

        # Calculate quality score
        if quality_metrics["test_functions"] > 0:
            assertions_per_test = (
                quality_metrics["assertions"] / quality_metrics["test_functions"]
            )
            if assertions_per_test < 2:
                result["warnings"].append(
                    f"Low assertion density: {assertions_per_test:.1f} assertions per test"
                )
            quality_metrics["quality_score"] = int(min(100, assertions_per_test * 25))

        result["metrics"]["test_quality"] = quality_metrics

    def _validate_test_coverage(self, result: dict):
        """Validate test coverage meets threshold"""
        try:
            # Try to run coverage report
            coverage_file = self.project_root / ".coverage"
            if not coverage_file.exists():
                result["warnings"].append(
                    "No .coverage file found. Run: pytest --cov=lightrag"
                )
                return

            coverage_result = subprocess.run(
                ["coverage", "report", "--format=json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if coverage_result.returncode == 0:
                coverage_data = json.loads(coverage_result.stdout)
                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )

                result["metrics"]["coverage_percent"] = total_coverage
                threshold = self.config["tdd_gates"]["coverage_threshold"]

                if total_coverage < threshold:
                    result["errors"].append(
                        f"Test coverage {total_coverage:.1f}% below required threshold {threshold}%"
                    )
            else:
                result["warnings"].append("Could not parse coverage report")

        except Exception as e:
            result["warnings"].append(f"Coverage validation failed: {e}")

    def _validate_task_specific_requirements(self, result: dict, task_info: dict):
        """Validate requirements based on task type"""

        # Performance tasks require baseline measurements
        if task_info.get("requires_baseline", False):
            baseline_file = (
                self.project_root
                / "tests"
                / "baselines"
                / f"{task_info['id']}_baseline.json"
            )
            if not baseline_file.exists():
                result["errors"].append(
                    f"Performance task requires baseline measurements. "
                    f"Expected: {baseline_file.relative_to(self.project_root)}"
                )
            else:
                result["metrics"]["baseline_found"] = True

        # Complex tasks require integration tests
        if task_info.get("requires_integration_tests", False):
            integration_tests = list(
                self.project_root.glob("tests/**/test_*integration*.py")
            )
            if not integration_tests:
                result["errors"].append(
                    f"Complex task (complexity {task_info['complexity']}) requires integration tests"
                )
            else:
                result["metrics"]["integration_tests_found"] = len(integration_tests)

    def _find_test_files(self) -> list[Path]:
        """Find all test files in the repository"""
        test_patterns = ["tests/test_*.py", "tests/**/test_*.py", "test_*.py"]

        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))

        return test_files

    def print_results(self, validation_result: dict):
        """Print validation results in a formatted way"""
        if validation_result["bypass_used"]:
            print(f"⚠️  EMERGENCY BYPASS ACTIVATED: {self.bypass_justification}")
            return

        if validation_result["valid"]:
            print("✅ TDD validation PASSED")
            return

        print("❌ TDD validation FAILED")

        if validation_result["errors"]:
            print("\n🚫 ERRORS (must be fixed):")
            for error in validation_result["errors"]:
                print(f"  • {error}")

        if validation_result["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in validation_result["warnings"]:
                print(f"  • {warning}")

        if validation_result["metrics"]:
            print("\n📊 METRICS:")
            for key, value in validation_result["metrics"].items():
                print(f"  • {key}: {value}")


def is_ci_environment():
    """Check if running in CI environment"""
    return (
        os.environ.get("GITHUB_ACTIONS") == "true"
        or os.environ.get("CI") == "true"
        or os.environ.get("CONTINUOUS_INTEGRATION") == "true"
    )


def main():
    parser = argparse.ArgumentParser(description="TDD Gate Validator")
    parser.add_argument("--bypass-justification", help="Emergency bypass justification")
    parser.add_argument("--task-id", help="Specific task ID to validate")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--ci-mode", action="store_true", help="Force CI mode")

    args = parser.parse_args()

    # Determine if we're in CI environment
    in_ci = args.ci_mode or is_ci_environment()

    if in_ci:
        print("🤖 Running in CI environment")

    project_root = Path(args.project_root).resolve()
    validator = TDDValidator(project_root, args.bypass_justification)

    result = validator.validate_task_tdd_readiness(args.task_id)
    validator.print_results(result)

    if not result["valid"]:
        if in_ci:
            print("💡 CI Failure - Check workflow logs for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
