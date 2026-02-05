#!/usr/bin/env python3
"""
Implementation Readiness Validator
Single unified validator for minimal implementation requirements
"""

import json
import subprocess
import sys
from pathlib import Path


class ImplementationReadinessValidator:
    def __init__(self, repo_root: str | None = None):
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from tdd_config.yaml"""
        config_path = self.repo_root / ".agent" / "config" / "tdd_config.yaml"

        if not config_path.exists():
            # Default config if file doesn't exist
            return {
                "implementation_ready": {
                    "enabled": True,
                    "require_beads": True,
                    "require_feature_branch": True,
                    "block_direct_main_edits": True,
                }
            }

        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)
            return config.get("implementation_ready", {})
        except ImportError:
            print("WARNING: PyYAML not installed, using defaults")
            return {
                "implementation_ready": {
                    "enabled": True,
                    "require_beads": True,
                    "require_feature_branch": True,
                    "block_direct_main_edits": True,
                }
            }
        except Exception as e:
            print(f"WARNING: Error loading config: {e}, using defaults")
            return {
                "implementation_ready": {
                    "enabled": True,
                    "require_beads": True,
                    "require_feature_branch": True,
                    "block_direct_main_edits": True,
                }
            }

    def check_beads_issue_exists(self) -> tuple[bool, str]:
        """Check if beads issue exists and is properly configured"""
        try:
            # Check if beads directory exists
            beads_dir = self.repo_root / ".beads"
            if not beads_dir.exists():
                return False, "Beads directory not found"

            # Check for current task or recent issues
            current_file = beads_dir / "current.json"
            issues_file = beads_dir / "issues.jsonl"

            if current_file.exists():
                with open(current_file) as f:
                    current = json.load(f)
                    if current.get("id"):
                        return True, f"Current task: {current['id']}"

            # Check database for any in-progress issues using bd command
            try:
                result = subprocess.run(
                    ["bd", "list", "--status", "in_progress", "--limit", "1", "--json"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Parse JSON output from bd
                    in_progress_issues = json.loads(result.stdout)
                    if in_progress_issues:  # List is not empty
                        issue = in_progress_issues[0]
                        issue_id = issue.get("id", "unknown")
                        issue_title = issue.get("title", "untitled")
                        return (
                            True,
                            f"In-progress task: {issue_id} - {issue_title[:50]}...",
                        )
            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                subprocess.SubprocessError,
            ):
                # Fallback to file-based check if bd command fails
                pass

            if issues_file.exists():
                with open(issues_file) as f:
                    # Check last few lines for any open issues
                    lines = f.readlines()[-20:]  # Last 20 lines
                    for line in lines:
                        if line.strip():
                            try:
                                issue = json.loads(line.strip())
                                if issue.get("status") in ["open", "in_progress"]:
                                    return True, f"Available issue: {issue['id']}"
                            except json.JSONDecodeError:
                                continue

            return False, "No active beads issues found"

        except Exception as e:
            return False, f"Error checking beads: {str(e)}"

    def check_not_main_for_code_changes(self) -> tuple[bool, str]:
        """Check if not on main branch for code changes"""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return False, "Not in a git repository"

            current_branch = result.stdout.strip()

            # Check if this is a protected branch
            protected_branches = ["main", "master", "develop", "dev"]
            if current_branch in protected_branches:
                return False, f"On protected branch '{current_branch}'"

            # Check if there are code changes (not just docs)
            diff_result = subprocess.run(
                ["git", "diff", "--name-only", "--cached", "HEAD~1"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if diff_result.returncode == 0:
                changed_files = diff_result.stdout.strip().split("\n")
                code_files = [f for f in changed_files if self._is_code_file(f)]

                if code_files:
                    return True, f"Feature branch '{current_branch}' with code changes"
                else:
                    # Only documentation changes - branch check less critical
                    return (
                        True,
                        f"Feature branch '{current_branch}' with documentation changes",
                    )

            return True, f"Feature branch '{current_branch}'"

        except subprocess.TimeoutExpired:
            return False, "Git command timeout"
        except Exception as e:
            return False, f"Error checking git branch: {str(e)}"

    def _is_code_file(self, filepath: str) -> bool:
        """Determine if file is code vs documentation"""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".go",
            ".rs",
            ".rb",
            ".php",
        }
        doc_extensions = {".md", ".rst", ".txt", ".doc", ".pdf"}

        # Check file extension
        ext = Path(filepath).suffix.lower()
        if ext in code_extensions:
            return True
        if ext in doc_extensions:
            return False

        # Check path patterns
        if any(
            pattern in filepath.lower() for pattern in ["doc", "readme", "changelog"]
        ):
            return False
        if any(
            pattern in filepath.lower() for pattern in ["src", "lib", "test", "scripts"]
        ):
            return True

        # Default to code if unclear
        return True

    def validate_all(self) -> tuple[bool, str, dict]:
        """Run all validations and return combined result"""
        if not self.config.get("enabled", True):
            return True, "Implementation readiness validation disabled", {}

        results = {}
        all_passed = True

        # Check beads issue if required
        if self.config.get("require_beads", True):
            beads_ok, beads_msg = self.check_beads_issue_exists()
            results["beads_issue"] = {"passed": beads_ok, "message": beads_msg}
            if not beads_ok:
                all_passed = False

        # Check feature branch if required
        if self.config.get("require_feature_branch", True):
            branch_ok, branch_msg = self.check_not_main_for_code_changes()
            results["feature_branch"] = {"passed": branch_ok, "message": branch_msg}
            if not branch_ok:
                all_passed = False

        # Generate summary message
        if all_passed:
            summary = "✅ Ready for implementation"
        else:
            failed_checks = [
                name for name, result in results.items() if not result["passed"]
            ]
            summary = f"❌ Blocking issues: {', '.join(failed_checks)}"

        return all_passed, summary, results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate implementation readiness")
    parser.add_argument("--repo-root", help="Repository root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    validator = ImplementationReadinessValidator(args.repo_root)
    passed, message, results = validator.validate_all()

    if args.json:
        print(
            json.dumps(
                {"passed": passed, "message": message, "results": results}, indent=2
            )
        )
    elif args.quiet:
        print(message)
        sys.exit(0 if passed else 1)
    else:
        print("=== Implementation Readiness Check ===")
        for check_name, result in results.items():
            status = "✅" if result["passed"] else "❌"
            print(
                f"{status} {check_name.replace('_', ' ').title()}: {result['message']}"
            )
        print(f"\n{message}")
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
