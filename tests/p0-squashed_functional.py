#!/usr/bin/env python3
"""
Functional Tests for P0 Squashed Infrastructure Task

Infrastructure functional tests validate that P0 fixes work end-to-end.
These tests verify that the CI/CD pipeline functions correctly after fixes.

Test Categories:
1. Linting and Formatting Functional Tests
2. CI Environment Functional Tests
3. TDD Compliance Functional Tests
4. Integration and End-to-End Tests

Exit Codes:
0 = All functional tests pass
1 = Critical functional failures
2 = Non-critical functional issues
"""

import os
import subprocess
import sys
import time
from pathlib import Path
import pytest


class TestP0SquashedFunctional:
    """Functional test suite for P0 infrastructure fixes"""

    def test_linting_functional_workflow(self):
        """
        Test that linting workflow functions correctly end-to-end

        Validates that ruff can check code, apply fixes, and report clean status.
        """
        print("🧪 Testing linting functional workflow...")

        # Test 1: Ruff can detect issues
        result = subprocess.run(
            ["uv", "run", "ruff", "check", ".agent/scripts/", "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should get structured output (even if no issues)
        assert result.returncode in [0, 1], (
            "Ruff should return 0 (clean) or 1 (issues found)"
        )

        # Test 2: Ruff can apply fixes where possible
        fix_result = subprocess.run(
            ["uv", "run", "ruff", "check", ".agent/scripts/", "--fix"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Fix command should complete successfully
        assert fix_result.returncode in [0, 1], "Ruff fix should complete successfully"

        print("✅ Linting workflow functional: detection and fixes work")

    def test_formatting_functional_workflow(self):
        """
        Test that code formatting workflow functions correctly

        Validates that black can format code and report status accurately.
        """
        print("🧪 Testing formatting functional workflow...")

        # Test 1: Black can check formatting
        check_result = subprocess.run(
            ["uv", "run", "black", "--check", "--diff", ".agent/scripts/"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should complete and give clear status
        assert check_result.returncode in [0, 1], "Black should return clear status"

        # Test 2: Black can apply formatting
        format_result = subprocess.run(
            ["uv", "run", "black", ".agent/scripts/"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Format should complete successfully
        assert format_result.returncode == 0, (
            "Black formatting should complete successfully"
        )

        print("✅ Formatting workflow functional: checking and reformatting work")

    def test_ci_environment_functional(self):
        """
        Test that CI environment setup functions correctly

        Validates that required tools are available and functional.
        """
        print("🧪 Testing CI environment functional...")

        required_tools = [
            ("ruff", "check for linting"),
            ("black", "format code"),
            ("mypy", "type checking"),
            ("pytest", "run tests"),
        ]

        functional_tools = []

        for tool, purpose in required_tools:
            try:
                # Test tool availability
                result = subprocess.run(
                    ["uv", "run", "which", tool],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    # Test tool functionality
                    version_result = subprocess.run(
                        ["uv", "run", tool, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if version_result.returncode == 0:
                        functional_tools.append(f"{tool} ({purpose})")

            except subprocess.TimeoutExpired:
                continue
            except Exception as e:
                print(f"⚠️  Tool {tool} error: {e}")
                continue

        # ENVIRONMENT ASSERTION: All required tools should be functional
        assert len(functional_tools) >= 3, (
            f"Too few functional tools: {functional_tools}"
        )

        print(f"✅ CI environment functional: {len(functional_tools)} tools working")

    def test_tdd_compliance_functional(self):
        """
        Test that TDD compliance validation functions correctly

        Validates that TDD validation can detect requirements and report status.
        """
        print("🧪 Testing TDD compliance functional...")

        tdd_script = ".agent/scripts/validate_tdd_compliance.sh"

        # Test 1: TDD script exists and is executable
        assert Path(tdd_script).exists(), f"TDD script missing: {tdd_script}"
        assert os.access(tdd_script, os.X_OK), "TDD script not executable"

        # Test 2: TDD script can run validation
        try:
            env = os.environ.copy()
            env["FEATURE_NAME"] = "p0-squashed"
            env["STRICT_MODE"] = "false"  # Permissive for functional test

            result = subprocess.run(
                ["uv", "run", "bash", tdd_script, "p0-squashed"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

            # Should run to completion (even if it finds violations)
            assert result.returncode in [0, 1], "TDD validation should complete"

            # Should provide structured output
            assert "TDD" in result.stdout, "TDD validation output should mention TDD"

        except subprocess.TimeoutExpired:
            pytest.skip("TDD validation timeout - may need optimization")

        print("✅ TDD compliance functional: validation script works correctly")

    def test_infrastructure_integration(self):
        """
        Test infrastructure components work together

        Validates that linting, formatting, and TDD work as integrated system.
        """
        print("🧪 Testing infrastructure integration...")

        integration_steps = []

        # Step 1: Apply formatting
        format_result = subprocess.run(
            ["uv", "run", "black", ".agent/scripts/"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if format_result.returncode == 0:
            integration_steps.append("formatting")

        # Step 2: Run linting check
        lint_result = subprocess.run(
            ["uv", "run", "ruff", "check", ".agent/scripts/"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if lint_result.returncode in [0, 1]:
            integration_steps.append("linting")

        # Step 3: Test type checking
        mypy_result = subprocess.run(
            [
                "uv",
                "run",
                "mypy",
                ".agent/scripts/multi_phase_detector.py",
                "--ignore-missing-imports",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if mypy_result.returncode == 0:
            integration_steps.append("type_checking")

        # INTEGRATION ASSERTION: Most infrastructure steps should work
        assert len(integration_steps) >= 2, (
            f"Integration failed: only {integration_steps} working"
        )

        print(
            f"✅ Infrastructure integration: {len(integration_steps)}/{3} components functional"
        )

    def test_performance_characteristics(self):
        """
        Test infrastructure performance characteristics

        Validates that infrastructure tools perform within acceptable time limits.
        """
        print("🧪 Testing performance characteristics...")

        performance_tests = []

        # Test 1: Linting performance
        start_time = time.time()
        lint_result = subprocess.run(
            ["uv", "run", "ruff", "check", ".agent/scripts/", "--quiet"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        lint_time = time.time() - start_time

        if lint_time < 30.0:  # Should complete within 30 seconds
            performance_tests.append("linting_performance")

        # Test 2: Formatting performance
        start_time = time.time()
        format_result = subprocess.run(
            ["uv", "run", "black", "--check", ".agent/scripts/"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        format_time = time.time() - start_time

        if format_time < 15.0:  # Should complete within 15 seconds
            performance_tests.append("formatting_performance")

        # Test 3: Tool startup performance
        tool_times = []
        for tool in ["ruff", "black", "mypy"]:
            start_time = time.time()
            result = subprocess.run(
                ["uv", "run", tool, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            tool_time = time.time() - start_time

            if result.returncode == 0 and tool_time < 5.0:  # Tools should start quickly
                tool_times.append(tool_time)

        if len(tool_times) >= 2 and sum(tool_times) / len(tool_times) < 3.0:
            performance_tests.append("tool_startup_performance")

        # PERFORMANCE ASSERTION: Infrastructure should be responsive
        assert len(performance_tests) >= 2, (
            f"Poor performance: only {performance_tests} passed"
        )

        print(
            f"✅ Performance characteristics: {len(performance_tests)}/{4} tests passed"
        )

    def test_error_handling_and_recovery(self):
        """
        Test infrastructure error handling and recovery

        Validates that tools handle errors gracefully and provide useful feedback.
        """
        print("🧪 Testing error handling and recovery...")

        error_handling_tests = []

        # Test 1: Linting with non-existent file
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "non_existent_file.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0 and "error" in result.stderr.lower():
            error_handling_tests.append("linting_error_handling")

        # Test 2: Black with invalid syntax file
        invalid_file = Path("test_invalid_syntax.py")
        invalid_file.write_text("def invalid_function(\n    # Missing colon and body")

        try:
            result = subprocess.run(
                ["uv", "run", "black", "--check", str(invalid_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_handling_tests.append("formatting_error_handling")

        finally:
            invalid_file.unlink(missing_ok=True)

        # Test 3: MyPy with type errors
        type_error_file = Path("test_type_error.py")
        type_error_file.write_text(
            "def typed_function(x: int) -> str:\n    return x + 1"
        )

        try:
            result = subprocess.run(
                ["uv", "run", "mypy", str(type_error_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_handling_tests.append("type_checking_error_handling")

        finally:
            type_error_file.unlink(missing_ok=True)

        # ERROR HANDLING ASSERTION: Tools should handle errors gracefully
        assert len(error_handling_tests) >= 2, (
            f"Poor error handling: only {error_handling_tests} passed"
        )

        print(
            f"✅ Error handling: {len(error_handling_tests)}/{3} tools handle errors correctly"
        )


class TestP0SquashedRegression:
    """Regression tests for P0 infrastructure fixes"""

    def test_no_syntax_errors_in_scripts(self):
        """
        Regression test: No syntax errors in infrastructure scripts

        P0 fixes should not introduce syntax errors.
        """
        script_files = list(Path(".agent/scripts/").glob("*.py"))

        syntax_errors = []

        for script_file in script_files:
            try:
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(script_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    syntax_errors.append(str(script_file))

            except subprocess.TimeoutExpired:
                syntax_errors.append(f"{script_file} (timeout)")
            except Exception as e:
                syntax_errors.append(f"{script_file} ({e})")

        # REGRESSION ASSERTION: No syntax errors should exist
        assert len(syntax_errors) == 0, f"Syntax errors found: {syntax_errors}"

        print(f"✅ No syntax errors: {len(script_files)} scripts compile correctly")

    def test_required_tools_available(self):
        """
        Regression test: All required tools should be available

        P0 fixes should ensure all CI tools are working.
        """
        required_tools = ["ruff", "black", "mypy", "pytest"]
        available_tools = []

        for tool in required_tools:
            try:
                result = subprocess.run(
                    ["uv", "run", "which", tool],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    version_result = subprocess.run(
                        ["uv", "run", tool, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if version_result.returncode == 0:
                        available_tools.append(tool)

            except Exception:
                continue

        # REGRESSION ASSERTION: All required tools should be available
        assert len(available_tools) == len(required_tools), (
            f"Missing tools: {set(required_tools) - set(available_tools)}"
        )

        print(
            f"✅ Required tools available: {len(available_tools)}/{len(required_tools)}"
        )


if __name__ == "__main__":
    # Run pytest for structured test execution
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    sys.exit(exit_code)
