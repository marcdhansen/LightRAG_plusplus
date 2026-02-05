"""
TDD Test Suite for CI/CD Permanent Fix feature
Test-driven development for implementing core functionality
"""

import os
import sys
from pathlib import Path

import pytest
import yaml

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCICDWorkflowValidation:
    """Test CI/CD workflow configuration and validation"""

    def test_linting_workflow_exists(self):
        """Test that linting.yaml workflow exists and is valid"""
        workflow_path = project_root / ".github" / "workflows" / "linting.yaml"
        assert workflow_path.exists(), "Linting workflow file should exist"

        # Validate YAML syntax
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
            assert "name" in workflow, "Workflow should have a name"
            assert "jobs" in workflow, "Workflow should have jobs"

    def test_ci_setup_workflow_exists(self):
        """Test that ci-setup.yml workflow exists and is valid"""
        workflow_path = project_root / ".github" / "workflows" / "ci-setup.yml"
        assert workflow_path.exists(), "CI setup workflow file should exist"

        # Validate YAML syntax
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
            assert "name" in workflow, "Workflow should have a name"
            assert "jobs" in workflow, "Workflow should have jobs"

    def test_python_version_configuration(self):
        """Test that workflows use correct Python version"""
        linting_path = project_root / ".github" / "workflows" / "linting.yaml"
        with open(linting_path) as f:
            workflow = yaml.safe_load(f)

            # Check for Python version specification
            jobs = workflow.get("jobs", {})
            lint_job = jobs.get("lint-and-format", {})
            strategy = lint_job.get("strategy", {})
            matrix = strategy.get("matrix", {})
            python_versions = matrix.get("python-version", [])

            assert python_versions, "Python version should be specified"
            assert any("3.12" in str(version) for version in python_versions), (
                "Should use Python 3.12"
            )


class TestPreCommitHooks:
    """Test pre-commit hook functionality and configuration"""

    def test_precommit_config_exists(self):
        """Test that pre-commit config exists and is valid"""
        config_path = project_root / ".pre-commit-config.yaml"
        assert config_path.exists(), "Pre-commit config should exist"

        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "repos" in config, "Pre-commit config should have repos"

    def test_custom_hooks_exist(self):
        """Test that custom hooks scripts exist"""
        hooks_dir = project_root / "scripts" / "hooks"

        required_hooks = [
            "tdd-compliance-check.sh",
            "beads-sync-check.sh",
            "webui-lint-check.sh",
        ]

        for hook in required_hooks:
            hook_path = hooks_dir / hook
            assert hook_path.exists(), f"Hook script {hook} should exist"
            assert os.access(hook_path, os.X_OK), f"Hook {hook} should be executable"

    def test_tdd_validation_hook_ci_support(self):
        """Test that TDD validation hook supports CI environment"""
        hook_path = project_root / "scripts" / "hooks" / "tdd-compliance-check.sh"
        with open(hook_path) as f:
            content = f.read()
            assert "GITHUB_ACTIONS" in content, (
                "Should check for GitHub Actions environment"
            )
            assert "CI" in content, "Should check for CI environment variable"


class TestDiagnosticTools:
    """Test diagnostic and debugging tools"""

    def test_diagnostic_script_exists(self):
        """Test that CI diagnostic script exists and is executable"""
        diagnostic_path = project_root / "scripts" / "ci-diagnostic.sh"
        assert diagnostic_path.exists(), "CI diagnostic script should exist"
        assert os.access(diagnostic_path, os.X_OK), (
            "Diagnostic script should be executable"
        )

    def test_debug_info_script_exists(self):
        """Test that debug info collection script exists"""
        debug_path = project_root / "scripts" / "collect-ci-debug-info.sh"
        assert debug_path.exists(), "Debug info script should exist"
        assert os.access(debug_path, os.X_OK), "Debug info script should be executable"

    def test_troubleshooting_documentation_exists(self):
        """Test that troubleshooting documentation exists"""
        doc_path = project_root / "docs" / "ci-troubleshooting.md"
        assert doc_path.exists(), "Troubleshooting documentation should exist"

        with open(doc_path) as f:
            content = f.read()
            assert "Common Issues" in content, "Should document common issues"
            assert "Solutions" in content, "Should provide solutions"


class TestErrorHandling:
    """Test error handling and resilience"""

    def test_ci_bypass_logic(self):
        """Test CI bypass logic in hooks"""
        hooks = [
            "tdd-compliance-check.sh",
            "beads-sync-check.sh",
            "webui-lint-check.sh",
        ]

        for hook in hooks:
            hook_path = project_root / "scripts" / "hooks" / hook
            with open(hook_path) as f:
                content = f.read()
                # Should have CI environment detection
                has_ci_check = any(
                    env_var in content for env_var in ["GITHUB_ACTIONS", "CI"]
                )
                assert has_ci_check, f"Hook {hook} should detect CI environment"

    def test_timeout_handling(self):
        """Test timeout handling in scripts"""
        beads_hook = project_root / "scripts" / "hooks" / "beads-sync-check.sh"
        with open(beads_hook) as f:
            content = f.read()
            assert "timeout" in content, (
                "Should have timeout handling for long operations"
            )

    def test_graceful_degradation(self):
        """Test graceful degradation when dependencies are missing"""
        tdd_hook = project_root / "scripts" / "hooks" / "tdd-compliance-check.sh"
        with open(tdd_hook) as f:
            content = f.read()
            assert "set +e" in content, "Should not exit on error for resilience"
            assert "WARNING" in content or "⚠️" in content, (
                "Should provide warnings instead of failing"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
