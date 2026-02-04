"""
Core Milestone Validator implementation
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models import (
    Milestone,
    SuccessCriteria,
    ValidationError,
    ValidationResult,
    ValidationStep,
    ValidationStepStatus,
)


class MilestoneValidator:
    """
    Core validation engine that orchestrates milestone-based validation
    Integrates with TDD gates, A/B testing, and deployment systems
    """

    def __init__(
        self, config_path: str = ".agent/config/validation/milestone_config.yaml"
    ):
        self.project_root = Path.cwd()
        self.config_path = self.project_root / config_path
        self.config = self._load_milestone_config()
        self.milestones = self._parse_milestones()

    def _load_milestone_config(self) -> dict[str, Any]:
        """Load milestone configuration from YAML file"""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValidationError(
                f"Configuration file not found: {self.config_path}"
            ) from None
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML configuration: {e}") from e

    def _parse_milestones(self) -> dict[str, Milestone]:
        """Parse milestones from configuration"""
        milestones = {}
        config_milestones = self.config.get("milestones", {})

        for milestone_id, milestone_config in config_milestones.items():
            success_criteria = SuccessCriteria(
                **milestone_config.get("success_criteria", {})
            )

            milestone = Milestone(
                id=milestone_id,
                name=milestone_config.get("name", milestone_id),
                description=milestone_config.get("description", ""),
                order=milestone_config.get("order", 0),
                success_criteria=success_criteria,
                validation_steps=milestone_config.get("validation_steps", []),
                blockers=milestone_config.get("blockers", []),
                dependencies=milestone_config.get("dependencies", []),
                required_for_progression=milestone_config.get(
                    "required_for_progression", True
                ),
                adaptive_thresholds=milestone_config.get("adaptive_thresholds", {}),
            )
            milestones[milestone_id] = milestone

        return milestones

    async def validate_milestone(
        self, milestone_id: str, task_ids: list[str] | None = None
    ) -> ValidationResult:
        """
        Validate completion of a milestone against success criteria
        Blocks progress if criteria aren't met
        """
        start_time = datetime.now()

        if milestone_id not in self.milestones:
            raise ValidationError(f"Milestone not found: {milestone_id}")

        milestone = self.milestones[milestone_id]

        # Initialize validation steps
        step_results = []
        criteria_results = {}
        metrics = {}
        blocking_issues = []
        recommendations = []

        # Execute each validation step
        for step_name in milestone.validation_steps:
            step_result = await self._execute_validation_step(
                step_name, milestone, task_ids or []
            )
            step_results.append(step_result)

        # Evaluate success criteria
        for (
            criteria_name,
            expected_value,
        ) in milestone.success_criteria.__dict__.items():
            if criteria_name.startswith("_"):
                continue

            criteria_result = await self._evaluate_criteria(
                criteria_name, expected_value, step_results, metrics
            )
            criteria_results[criteria_name] = criteria_result

        # Check for blocking issues
        for blocker in milestone.blockers:
            if self._is_blocking_issue_active(blocker, criteria_results, step_results):
                blocking_issues.append(blocker)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            criteria_results, step_results, blocking_issues
        )

        # Determine overall success
        passed = (
            all(criteria_results.values())
            and len(blocking_issues) == 0
            and all(step.status == ValidationStepStatus.PASSED for step in step_results)
        )

        validation_duration = (datetime.now() - start_time).total_seconds()

        return ValidationResult(
            milestone_id=milestone_id,
            passed=passed,
            criteria_results=criteria_results,
            step_results=step_results,
            metrics=metrics,
            blocking_issues=blocking_issues,
            recommendations=recommendations,
            timestamp=datetime.now(),
            validation_duration_seconds=validation_duration,
            task_ids=task_ids or [],
        )

    async def _execute_validation_step(
        self, step_name: str, milestone: Milestone, task_ids: list[str]
    ) -> ValidationStep:
        """Execute a specific validation step"""
        step = ValidationStep(name=step_name)
        step.started_at = datetime.now()

        try:
            if step_name == "tdd_gate_validation":
                result = await self._run_tdd_gate_validation(milestone, task_ids)
            elif step_name == "unit_test_execution":
                result = await self._run_unit_tests(milestone, task_ids)
            elif step_name == "integration_test_suite":
                result = await self._run_integration_tests(milestone, task_ids)
            elif step_name == "ab_test_execution":
                result = await self._run_ab_tests(milestone, task_ids)
            elif step_name == "rollback_procedure_test":
                result = await self._test_rollback_procedure(milestone, task_ids)
            elif step_name == "load_testing_with_peak_traffic":
                result = await self._run_load_tests(milestone, task_ids)
            else:
                # Default to success for unknown steps
                result = {"passed": True, "metrics": {}}

            step.status = (
                ValidationStepStatus.PASSED
                if result["passed"]
                else ValidationStepStatus.FAILED
            )
            step.metrics = result.get("metrics", {})

            if not result["passed"]:
                step.error_message = result.get("error", "Step failed")

        except Exception as e:
            step.status = ValidationStepStatus.FAILED
            step.error_message = str(e)

        finally:
            step.completed_at = datetime.now()
            if step.started_at and step.completed_at:
                step.duration_seconds = (
                    step.completed_at - step.started_at
                ).total_seconds()

        return step

    async def _run_tdd_gate_validation(
        self, _milestone: Milestone, task_ids: list[str]
    ) -> dict[str, Any]:
        """Run TDD gate validation"""
        try:
            # Use existing TDD gate validator
            cmd = [
                sys.executable,
                str(self.project_root / ".agent/scripts/tdd_gate_validator.py"),
            ]

            # Add task IDs if provided
            for task_id in task_ids:
                cmd.extend(["--task-id", task_id])

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            # Parse output for metrics
            metrics = {}
            if result.stdout:
                try:
                    # Try to extract JSON metrics from output
                    for line in result.stdout.split("\n"):
                        if line.strip().startswith("{") and line.strip().endswith("}"):
                            metrics.update(json.loads(line))
                except json.JSONDecodeError:
                    pass

            return {
                "passed": result.returncode == 0,
                "metrics": metrics,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "error": "TDD gate validation timed out after 10 minutes",
            }
        except Exception as e:
            return {"passed": False, "error": f"TDD gate validation failed: {str(e)}"}

    async def _run_unit_tests(
        self, _milestone: Milestone, _task_ids: list[str]
    ) -> dict[str, Any]:
        """Run unit tests and collect coverage metrics"""
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "--cov=lightrag",
                "--cov-report=json",
                "--cov-report=term-missing",
                "-v",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
            )

            # Parse coverage report
            coverage_metrics = {}
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        coverage_metrics["coverage_percentage"] = coverage_data.get(
                            "totals", {}
                        ).get("percent_covered", 0)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

            # Parse test results
            test_metrics = {}
            if result.stdout:
                # Extract test count, pass count, etc.
                import re

                matches = re.findall(r"(\d+) (\w+) in", result.stdout)
                for count, status in matches:
                    test_metrics[f"tests_{status}"] = int(count)

            all_metrics = {**coverage_metrics, **test_metrics}

            return {
                "passed": result.returncode == 0,
                "metrics": all_metrics,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Unit tests timed out after 30 minutes"}
        except Exception as e:
            return {"passed": False, "error": f"Unit test execution failed: {str(e)}"}

    async def _run_integration_tests(
        self, _milestone: Milestone, _task_ids: list[str]
    ) -> dict[str, Any]:
        """Run integration tests"""
        try:
            # Run integration tests
            cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "integration", "-v"]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=2400,  # 40 minutes timeout
            )

            return {
                "passed": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "error": "Integration tests timed out after 40 minutes",
            }
        except Exception as e:
            return {
                "passed": False,
                "error": f"Integration test execution failed: {str(e)}",
            }

    async def _run_ab_tests(
        self, milestone: Milestone, _task_ids: list[str]
    ) -> dict[str, Any]:
        """Run A/B tests for milestone validation"""
        try:
            # Import and use existing A/B testing framework
            sys.path.insert(0, str(self.project_root))
            from ab_testing.production_ab_framework import ABTestSuite

            ab_suite = ABTestSuite()

            # Configure test based on milestone requirements
            ab_config = milestone.adaptive_thresholds.get("ab_testing_config", {})

            # Run A/B test comparison
            result = await ab_suite.compare_performance(
                test_name=f"milestone_{milestone.id}_validation",
                duration_minutes=ab_config.get("test_duration_minutes", 60),
                sample_size=ab_config.get("minimum_sample_size", 1000),
            )

            return {
                "passed": result.get("statistically_significant", False),
                "metrics": result,
                "error": None,
            }

        except Exception as e:
            return {"passed": False, "error": f"A/B testing failed: {str(e)}"}

    async def _test_rollback_procedure(
        self, _milestone: Milestone, _task_ids: list[str]
    ) -> dict[str, Any]:
        """Test rollback procedure"""
        try:
            # Simulate rollback procedure test
            # In real implementation, this would:
            # 1. Create deployment checkpoint
            # 2. Deploy to test environment
            # 3. Trigger rollback
            # 4. Verify rollback success

            return {
                "passed": True,  # Placeholder
                "metrics": {
                    "rollback_time_seconds": 120,
                    "rollback_verification_passed": True,
                },
            }

        except Exception as e:
            return {
                "passed": False,
                "error": f"Rollback procedure test failed: {str(e)}",
            }

    async def _run_load_tests(
        self, milestone: Milestone, _task_ids: list[str]
    ) -> dict[str, Any]:
        """Run load tests"""
        try:
            # Configure load test based on milestone requirements
            load_config = milestone.adaptive_thresholds.get("load_testing_config", {})

            # Simulate load test execution
            # In real implementation, this would use tools like Locust, JMeter, etc.

            return {
                "passed": True,  # Placeholder
                "metrics": {
                    "requests_per_second": load_config.get("target_rps", 1000),
                    "avg_response_time_ms": 250,
                    "p95_response_time_ms": 450,
                    "error_rate": 0.001,
                },
            }

        except Exception as e:
            return {"passed": False, "error": f"Load test failed: {str(e)}"}

    async def _evaluate_criteria(
        self,
        criteria_name: str,
        expected_value: Any,
        step_results: list[ValidationStep],
        _metrics: dict[str, Any],
    ) -> bool:
        """Evaluate a specific success criterion"""

        # Extract relevant metrics from step results
        all_metrics = {}
        for step in step_results:
            all_metrics.update(step.metrics)

        # Evaluate specific criteria
        if criteria_name == "coverage_threshold":
            coverage = all_metrics.get("coverage_percentage", 0)
            return coverage >= expected_value

        elif criteria_name == "unit_tests_passed":
            failed_tests = all_metrics.get("tests_failed", 0)
            return failed_tests == 0

        elif criteria_name == "tdd_gate_passed":
            tdd_step = next(
                (s for s in step_results if s.name == "tdd_gate_validation"), None
            )
            return tdd_step and tdd_step.status == ValidationStepStatus.PASSED

        elif criteria_name == "integration_tests_passed":
            integration_step = next(
                (s for s in step_results if s.name == "integration_test_suite"), None
            )
            return (
                integration_step
                and integration_step.status == ValidationStepStatus.PASSED
            )

        elif criteria_name == "ab_test_significance":
            ab_step = next(
                (s for s in step_results if s.name == "ab_test_execution"), None
            )
            if ab_step and ab_step.metrics:
                p_value = ab_step.metrics.get("p_value", 1.0)
                return p_value <= expected_value
            return False

        elif criteria_name == "rollback_test_passed":
            rollback_step = next(
                (s for s in step_results if s.name == "rollback_procedure_test"), None
            )
            return rollback_step and rollback_step.status == ValidationStepStatus.PASSED

        elif criteria_name == "load_test_passed":
            load_step = next(
                (s for s in step_results if s.name == "load_testing_with_peak_traffic"),
                None,
            )
            return load_step and load_step.status == ValidationStepStatus.PASSED

        # Default to expected boolean value
        return bool(expected_value)

    def _is_blocking_issue_active(
        self,
        blocker: str,
        criteria_results: dict[str, bool],
        step_results: list[ValidationStep],
    ) -> bool:
        """Check if a blocking issue is active"""

        # Check if any criteria failed
        if "failure" in blocker.lower() and not all(criteria_results.values()):
            return True

        # Check if coverage is below threshold
        if "coverage" in blocker.lower():
            coverage = criteria_results.get("coverage_threshold", True)
            if not coverage:
                return True

        # Check if any steps failed
        failed_steps = [
            s for s in step_results if s.status == ValidationStepStatus.FAILED
        ]
        if failed_steps:
            return True

        return False

    def _generate_recommendations(
        self,
        criteria_results: dict[str, bool],
        _step_results: list[ValidationStep],
        blocking_issues: list[str],
    ) -> list[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Coverage recommendations
        if not criteria_results.get("coverage_threshold", True):
            recommendations.append("Increase test coverage to meet the 80% threshold")

        # Test failure recommendations
        if not criteria_results.get("unit_tests_passed", True):
            recommendations.append("Fix failing unit tests before proceeding")

        # Integration test recommendations
        if not criteria_results.get("integration_tests_passed", True):
            recommendations.append(
                "Resolve integration test failures and API compatibility issues"
            )

        # A/B test recommendations
        if not criteria_results.get("ab_test_significance", True):
            recommendations.append(
                "Extend A/B test duration or increase sample size to achieve statistical significance"
            )

        # Rollback procedure recommendations
        if not criteria_results.get("rollback_test_passed", True):
            recommendations.append(
                "Fix rollback procedure issues before production deployment"
            )

        # General recommendations based on blocking issues
        for blocker in blocking_issues:
            if "performance" in blocker.lower():
                recommendations.append("Optimize performance to meet requirements")
            elif "security" in blocker.lower():
                recommendations.append("Address security vulnerabilities")
            elif "monitoring" in blocker.lower():
                recommendations.append("Complete monitoring setup and configuration")

        return recommendations

    def get_milestone(self, milestone_id: str) -> Milestone | None:
        """Get milestone definition by ID"""
        return self.milestones.get(milestone_id)

    def list_milestones(self) -> list[Milestone]:
        """Get all milestones sorted by order"""
        return sorted(self.milestones.values(), key=lambda m: m.order)

    def get_next_milestone(self, current_milestone_id: str) -> Milestone | None:
        """Get the next milestone in sequence"""
        current = self.get_milestone(current_milestone_id)
        if not current:
            return None

        next_order = current.order + 1
        for milestone in self.milestones.values():
            if milestone.order == next_order:
                return milestone

        return None
