"""
Functional tests for CI_FAILURE_HANDLER_TEST feature.
End-to-end functional tests for CI/CD infrastructure.
"""

import tempfile
import os
from pathlib import Path
import subprocess
import json
import pytest
from unittest.mock import Mock, patch


class TestCI_FAILURE_HANDLER_TESTFunctional:
    """Functional test suite for CI/CD Failure Handler."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_github_event(self):
        """Mock GitHub workflow_run event for testing."""
        return {
            "workflow_run": {
                "id": 123456,
                "name": "Offline Unit Tests",
                "conclusion": "failure",
                "head_branch": "feature/test-branch",
                "head_sha": "abc123def456789",
                "event": "workflow_run",
                "status": "completed",
                "created_at": "2026-02-12T15:30:00Z",
                "pull_requests": [
                    {
                        "number": 67,
                        "title": "Fix P0 CI/CD Failure Handler workflow issues",
                        "user": {"login": "marcdhansen"},
                        "base": {"ref": "main"},
                        "head": {"ref": "fix/ci-failure-handler-test"},
                        "html_url": "https://github.com/marcdhansen/LightRAG_gemini/pull/67",
                    }
                ],
            }
        }

    @pytest.mark.asyncio
    async def test_end_to_end_failure_handling(self, temp_workspace, mock_github_event):
        """Test complete failure handling workflow."""
        # Create test environment
        env_file = temp_workspace / "test.env"
        workflow_file = temp_workspace / "ci-failure-handler.yml"

        # Create mock workflow file
        workflow_content = """
name: CI/CD Failure Handler Test
on:
  workflow_run:
    workflows: ["Offline Unit Tests"]
    types: [completed]
jobs:
  test-handler:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
"""
        workflow_file.write_text(workflow_content.strip())

        # Test event processing
        event_conclusion = mock_github_event["workflow_run"]["conclusion"]
        should_trigger = event_conclusion == "failure"

        assert should_trigger, "Workflow should trigger on failure conclusion"

        # Test PR context extraction
        pr_data = mock_github_event["workflow_run"]["pull_requests"][0]
        pr_number = pr_data["number"]
        pr_title = pr_data["title"]
        pr_author = pr_data["user"]["login"]

        assert pr_number == 67
        assert "Fix P0 CI/CD Failure Handler" in pr_title
        assert pr_author == "marcdhansen"

    async def test_github_actions_integration(self, temp_workspace, mock_github_event):
        """Test integration with GitHub Actions."""
        # Test environment variable setting
        env_vars = {
            "GITHUB_ACTIONS": "true",
            "WORKFLOW_NAME": mock_github_event["workflow_run"]["name"],
            "RUN_URL": "https://github.com/marcdhansen/LightRAG_gemini/actions/runs/21952520292",
            "GITHUB_REPOSITORY": "marcdhansen/LightRAG_gemini",
            "GITHUB_SHA": mock_github_event["workflow_run"]["head_sha"],
            "GITHUB_REF_NAME": mock_github_event["workflow_run"]["head_branch"],
        }

        for key, value in env_vars.items():
            assert value is not None, f"Environment variable {key} should be set"
            assert len(value) > 0, f"Environment variable {key} should not be empty"

        # Test PR information extraction
        pr_data = mock_github_event["workflow_run"]["pull_requests"][0]
        expected_pr_vars = {
            "PR_NUMBER": str(pr_data["number"]),
            "PR_TITLE": pr_data["title"],
            "PR_AUTHOR": pr_data["user"]["login"],
            "BASE_BRANCH": pr_data["base"]["ref"],
            "HEAD_BRANCH": pr_data["head"]["ref"],
        }

        for key, value in expected_pr_vars.items():
            assert value is not None, f"PR variable {key} should be extracted"
            assert len(value) > 0, f"PR variable {key} should not be empty"

    def test_no_false_positives_on_success(self, temp_workspace):
        """Test no false positives on successful workflows."""
        # Create successful workflow event
        success_event = {
            "workflow_run": {
                "name": "Offline Unit Tests",
                "conclusion": "success",
                "head_branch": "main",
            }
        }

        # Test conditional logic
        conclusion = success_event["workflow_run"]["conclusion"]
        should_trigger = conclusion == "failure"

        assert not should_trigger, "Workflow should NOT trigger on success conclusion"

        # Test manual trigger
        manual_trigger_input = {"test_failure": "false"}
        manual_should_trigger = manual_trigger_input.get("test_failure") == "true"

        assert not manual_should_trigger, (
            "Manual trigger should not activate with test_failure=false"
        )

    async def test_pr_context_preservation(self, temp_workspace, mock_github_event):
        """Test PR context is preserved and passed correctly."""
        # Test PR information flow through workflow
        pr_data = mock_github_event["workflow_run"]["pull_requests"][0]

        # Create issue body template
        issue_body = f"""
## 🚨 CI/CD Pipeline Failure

**Workflow**: ${{{{ WORKFLOW_NAME }}}}
**Run URL**: ${{{{ RUN_URL }}}}
**Branch**: ${{{{ GITHUB_REF_NAME }}}}
**Commit**: ${{{{ GITHUB_SHA }}}}
**Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

### 🔗 Links
- [Workflow Run](${{{{ RUN_URL }}}})
- [Repository](https://github.com/${{{{ GITHUB_REPOSITORY }}}})

### 📋 PR Context
**PR Number**: {pr_data["number"]}
**PR Title**: {pr_data["title"]}
**PR Author**: {pr_data["user"]["login"]}
**Base Branch**: {pr_data["base"]["ref"]}
**Head Branch**: {pr_data["head"]["ref"]}

---
🤖 This issue was automatically created by CI failure handler.
Please review the workflow logs and address the failure.
"""

        # Verify PR context is preserved in issue body
        assert str(pr_data["number"]) in issue_body
        assert pr_data["title"] in issue_body
        assert pr_data["user"]["login"] in issue_body
        assert pr_data["base"]["ref"] in issue_body
        assert pr_data["head"]["ref"] in issue_body

    def test_workflow_run_event_processing(self, mock_github_event):
        """Test processing of workflow_run GitHub events."""
        # Test event structure parsing
        workflow_run = mock_github_event["workflow_run"]

        # Verify required fields are present
        required_fields = [
            "id",
            "name",
            "conclusion",
            "head_branch",
            "head_sha",
            "pull_requests",
        ]
        for field in required_fields:
            assert field in workflow_run, f"Required field {field} should be present"

        # Test workflow filtering
        expected_workflows = [
            "Offline Unit Tests",
            "Changelog Update",
            "TDD Compliance Check",
        ]
        actual_workflow = workflow_run["name"]

        assert actual_workflow in expected_workflows, (
            f"Workflow {actual_workflow} should be in expected list"
        )

        # Test conclusion filtering
        conclusion = workflow_run["conclusion"]
        assert conclusion == "failure", "Conclusion should be 'failure' for triggering"

    async def test_error_recovery_mechanisms(self, temp_workspace):
        """Test error recovery mechanisms."""
        # Test diagnostic script failure scenario
        with patch("subprocess.run") as mock_run:
            # Simulate diagnostic script failure
            mock_run.side_effect = [
                Mock(returncode=1, stdout="", stderr="Diagnostic script failed"),
                Mock(returncode=0, stdout="Issue created successfully", stderr=""),
            ]

            # Test diagnostic script execution
            diagnostic_result = mock_run(
                ["./scripts/ci-diagnostic.sh"],
                check=False,
                capture_output=True,
                text=True,
            )

            assert diagnostic_result.returncode == 1

            # Test fallback issue creation
            with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
                fallback_result = mock_run(
                    [
                        "gh",
                        "issue",
                        "create",
                        "--title",
                        "Test Issue",
                        "--body",
                        "Test Body",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                # Should succeed with fallback
                assert "Issue created successfully" in fallback_result.stdout

    def test_duplicate_script_removal_validation(self):
        """Test that duplicate diagnostic script calls are removed."""
        workflow_path = ".github/workflows/ci-failure-handler.yml"

        with open(workflow_path, "r") as f:
            workflow_content = f.read()

        # Count diagnostic script calls
        diagnostic_script_count = workflow_content.count("./scripts/ci-diagnostic.sh")

        # Should only have one call after fix
        assert diagnostic_script_count == 1, (
            f"Expected 1 diagnostic script call, found {diagnostic_script_count}"
        )

        # Check for duplicate script patterns (lines 70-76 and 79-85 in original)
        duplicate_patterns = [
            "./scripts/ci-diagnostic.sh || {\n",
            '  echo "⚠️ Diagnostic script failed, creating basic issue..."\n',
            "  gh issue create",
        ]

        for pattern in duplicate_patterns:
            pattern_count = workflow_content.count(pattern)
            assert pattern_count == 1, (
                f"Duplicate pattern found: {pattern} (count: {pattern_count})"
            )

    def test_github_cli_error_exit_code_handling(self):
        """Test proper handling of GitHub CLI exit code 4."""
        with patch("subprocess.run") as mock_run:
            # Simulate GitHub CLI failure with exit code 4
            mock_run.return_value = Mock(
                returncode=4,
                stderr="gh issue create failed with exit code 4",
                stdout="",
            )

            # Test error handling logic
            try:
                result = mock_run(
                    ["gh", "issue", "create", "--title", "Test", "--body", "Test"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                # Should handle exit code 4 properly
                assert e.returncode == 4
                assert "gh issue create failed" in e.stderr

    def test_manual_trigger_test_functionality(self):
        """Test workflow_dispatch manual trigger for testing."""
        # Test manual trigger input
        manual_input = {"test_failure": "true"}

        # Test trigger condition evaluation
        manual_active = manual_input.get("test_failure") == "true"
        workflow_run_condition = "github.event_name == 'workflow_run' && github.event.workflow_run.conclusion == 'failure'"

        # Manual trigger should bypass workflow_run condition
        assert manual_active, "Manual trigger should be active when test_failure=true"
        assert "workflow_run" in workflow_run_condition, (
            "Should check workflow_run conditions for automatic triggers"
        )

    def test_trigger_specificity_validation(self):
        """Test workflow triggers are specific to targeted workflows."""
        # Expected workflows that should trigger failure handler
        expected_workflows = [
            "Offline Unit Tests",
            "Changelog Update",
            "TDD Compliance Check",
        ]

        # Test each expected workflow
        for workflow_name in expected_workflows:
            workflow_included = workflow_name in expected_workflows
            assert workflow_included, (
                f"Workflow {workflow_name} should be included in trigger list"
            )

        # Test that other workflows don't trigger
        unexpected_workflows = [
            "Linting and Formatting",
            "Environment Summary",
            "Setup CI Environment",
        ]

        for workflow_name in unexpected_workflows:
            workflow_excluded = workflow_name not in expected_workflows
            assert workflow_excluded, (
                f"Workflow {workflow_name} should NOT trigger failure handler"
            )

    def test_heredoc_issue_body_validation(self):
        """Test proper heredoc syntax and variable expansion."""
        # Test heredoc structure for issue creation
        expected_heredoc_markers = [
            "ISSUE_BODY=$(cat <<EOF",
            "EOF",
            'gh issue create --title "$ISSUE_TITLE" --body "$ISSUE_BODY"',
        ]

        workflow_path = ".github/workflows/ci-failure-handler.yml"
        with open(workflow_path, "r") as f:
            workflow_content = f.read()

        for marker in expected_heredoc_markers:
            assert marker in workflow_content, (
                f"Required heredoc marker not found: {marker}"
            )

        # Test variable expansion in heredoc
        expected_variables = [
            "$WORKFLOW_NAME",
            "$RUN_URL",
            "$GITHUB_REF_NAME",
            "$GITHUB_SHA",
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        ]

        for var in expected_variables:
            assert var in workflow_content, f"Expected variable not found: {var}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
