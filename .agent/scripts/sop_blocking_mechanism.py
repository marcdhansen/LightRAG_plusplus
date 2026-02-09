#!/usr/bin/env python3
"""
Automated SOP Blocking Mechanism with Git Hook Integration

Provides automated blocking of git operations when SOP violations are detected.
Integrates with git hooks to enforce compliance at critical points.

Features:
- Git hook integration (pre-commit, pre-push)
- Automated violation detection
- Configurable blocking policies
- Emergency override mechanism
- Detailed violation reporting
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from sop_compliance_validator import SOPComplianceValidator
from adaptive_enforcement_engine import AdaptiveEnforcementEngine


class SOPBlockingMechanism:
    """Automated blocking mechanism for SOP violations."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or ".agent/config/realtime_monitor_config.json"
        self.config = self._load_config()

        # Initialize components
        self.sop_validator = SOPComplianceValidator()
        self.enforcement_engine = AdaptiveEnforcementEngine()

        # State and logging
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.blocking_log = self.log_dir / "sop_blocking.log"
        self.emergency_file = Path(".agent/emergency_override.json")

        # Setup logging
        self.logger = self._setup_logging()

    def _load_config(self) -> Dict[str, Any]:
        """Load blocking configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            return {
                "blocking_enabled": True,
                "blocking_config": {
                    "block_duration_minutes": 10,
                    "auto_unblock": True,
                    "critical_only": False,
                },
                "critical_violations": [
                    "git_status_dirty",
                    "session_lock_missing",
                    "mandatory_skills_missing",
                    "tdd_compliance_failed",
                ],
            }

    def _setup_logging(self):
        """Setup logging for blocking mechanism."""
        import logging

        logger = logging.getLogger("sop_blocking")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _check_emergency_override(self) -> Tuple[bool, str]:
        """Check for emergency override."""
        if not self.emergency_file.exists():
            return False, "No emergency override file found"

        try:
            with open(self.emergency_file) as f:
                override = json.load(f)

            # Check if override is valid
            now = datetime.now()
            override_time = datetime.fromisoformat(override["timestamp"])

            # Emergency overrides expire after 2 hours
            if now - override_time > timedelta(hours=2):
                return False, "Emergency override expired (2h limit)"

            # Check for required fields
            required_fields = ["approved_by", "reason", "timestamp", "issue_id"]
            if not all(field in override for field in required_fields):
                return False, "Invalid emergency override format"

            return True, f"Valid emergency override by {override['approved_by']}"

        except Exception as e:
            return False, f"Invalid emergency override file: {e}"

    def _log_blocking_event(
        self, operation: str, violations: List[str], blocked: bool, reason: str = ""
    ):
        """Log blocking event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "violations": violations,
            "blocked": blocked,
            "reason": reason,
            "user": os.environ.get("USER", "unknown"),
            "enforcement_level": self.enforcement_engine.config.get(
                "current_enforcement_level", "standard"
            ),
        }

        # Write to blocking log
        with open(self.blocking_log, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Log to console
        self.logger.info(
            f"SOP Blocking Event: {operation} {'BLOCKED' if blocked else 'ALLOWED'}"
        )
        if blocked:
            self.logger.warning(f"Violations: {', '.join(violations)}")
            self.logger.warning(f"Reason: {reason}")

    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except Exception as e:
            self.logger.error(f"Failed to get staged files: {e}")
            return []

    def _get_changed_files(self) -> List[str]:
        """Get list of changed files (including unstaged)."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except Exception as e:
            self.logger.error(f"Failed to get changed files: {e}")
            return []

    def _check_critical_file_changes(self, files: List[str]) -> List[str]:
        """Check for changes to critical files."""
        critical_patterns = [
            "lightrag/core.py",
            "lightrag/operate.py",
            ".agent/config/",
            ".agent/scripts/",
            "package.json",
            "requirements.txt",
            "Makefile",
        ]

        critical_changes = []
        for file_path in files:
            for pattern in critical_patterns:
                if pattern in file_path or file_path.startswith(pattern):
                    critical_changes.append(file_path)
                    break

        return critical_changes

    def should_block_operation(
        self, operation: str, context: Dict[str, Any] = None
    ) -> Tuple[bool, List[str], str]:
        """Determine if operation should be blocked."""
        context = context or {}

        # Check if blocking is enabled
        if not self.config.get("blocking_enabled", True):
            return False, [], "Blocking disabled in configuration"

        # Check emergency override
        emergency_allowed, emergency_reason = self._check_emergency_override()
        if emergency_allowed:
            return False, [], f"Emergency override: {emergency_reason}"

        # Perform SOP compliance check
        compliance_results = self.sop_validator.validate_all_sop_rules()

        # Extract violations
        violations = []

        # Mandatory skills violations
        mandatory_skills = compliance_results.get("mandatory_skills", {})
        if not mandatory_skills.get("all_passed", False):
            violations.append("mandatory_skills_missing")

        # Conditional rule violations
        conditional_rules = compliance_results.get("conditional_rules", {})
        if conditional_rules.get("critical_violations", 0) > 0:
            violations.append("conditional_rule_violations")

        # Workflow integrity violations
        workflow_integrity = compliance_results.get("workflow_integrity", {})
        if not workflow_integrity.get("git_clean", True):
            violations.append("git_status_dirty")

        if not workflow_integrity.get("beads_ready", True):
            violations.append("beads_connectivity")

        if not workflow_integrity.get("no_duplicate_docs", True):
            violations.append("documentation_integrity")

        # Check for critical violations
        critical_violations = [
            v for v in violations if v in self.config.get("critical_violations", [])
        ]

        # Use adaptive enforcement engine
        should_block = False
        block_reason = ""

        for violation in violations:
            enforce, reason = self.enforcement_engine.should_enforce_violation(
                violation, context
            )
            if enforce:
                should_block = True
                block_reason = reason
                break

        # Additional checks for specific operations
        if operation == "pre-push":
            # For pre-push, be more strict about critical files
            changed_files = self._get_changed_files()
            critical_changes = self._check_critical_file_changes(changed_files)

            if critical_changes and not workflow_integrity.get("git_clean", True):
                should_block = True
                block_reason = "Critical file changes with unclean git status"

        return should_block, violations, block_reason

    def pre_commit_check(self) -> int:
        """Git pre-commit hook check."""
        print("🔍 Running SOP compliance pre-commit check...")

        # Get staged files
        staged_files = self._get_staged_files()
        if not staged_files:
            print("✅ No files staged, skipping check")
            return 0

        print(f"📁 Checking {len(staged_files)} staged files...")

        # Determine if operation should be blocked
        should_block, violations, reason = self.should_block_operation(
            "pre-commit", {"staged_files": staged_files}
        )

        if should_block:
            print("\n" + "=" * 60)
            print("❌ SOP COMPLIANCE CHECK FAILED - COMMIT BLOCKED")
            print("=" * 60)
            print(f"\n🚨 Reason: {reason}")
            print(f"\n📋 Violations detected:")
            for violation in violations:
                print(f"  • {violation}")

            print("\n💡 To resolve:")
            print("  1. Fix the violations listed above")
            print("  2. Stage your changes again")
            print("  3. Retry the commit")
            print("\n🆘 For emergencies only:")
            print("  Create emergency override with project lead approval")

            # Log blocking event
            self._log_blocking_event("pre-commit", violations, True, reason)

            return 1
        else:
            print("✅ SOP compliance check passed")

            # Log successful check
            self._log_blocking_event("pre-commit", [], False, "No violations")

            return 0

    def pre_push_check(self) -> int:
        """Git pre-push hook check."""
        print("🔍 Running SOP compliance pre-push check...")

        # Determine if operation should be blocked
        should_block, violations, reason = self.should_block_operation(
            "pre-push", {"operation": "push"}
        )

        if should_block:
            print("\n" + "=" * 60)
            print("❌ SOP COMPLIANCE CHECK FAILED - PUSH BLOCKED")
            print("=" * 60)
            print(f"\n🚨 Reason: {reason}")
            print(f"\n📋 Violations detected:")
            for violation in violations:
                print(f"  • {violation}")

            print("\n💡 To resolve:")
            print("  1. Fix the violations listed above")
            print("  2. Commit your fixes")
            print("  3. Retry the push")
            print("\n🆘 For emergencies only:")
            print("  Create emergency override with project lead approval")

            # Log blocking event
            self._log_blocking_event("pre-push", violations, True, reason)

            return 1
        else:
            print("✅ SOP compliance check passed")

            # Log successful check
            self._log_blocking_event("pre-push", [], False, "No violations")

            return 0

    def install_git_hooks(self) -> int:
        """Install git hooks for automated blocking."""
        hooks_dir = Path(".git/hooks")

        if not hooks_dir.exists():
            print("❌ Not in a git repository")
            return 1

        # Get script path
        script_path = Path(__file__).resolve()

        # Pre-commit hook
        pre_commit_hook = f"""#!/bin/sh
# SOP Compliance Pre-commit Hook
python3 "{script_path}" pre-commit
exit $?
"""

        # Pre-push hook
        pre_push_hook = f"""#!/bin/sh
# SOP Compliance Pre-push Hook  
python3 "{script_path}" pre-push
exit $?
"""

        # Write hooks
        try:
            pre_commit_file = hooks_dir / "pre-commit"
            pre_push_file = hooks_dir / "pre-push"

            # Backup existing hooks
            if pre_commit_file.exists():
                pre_commit_file.rename(pre_commit_file.with_suffix(".backup"))

            if pre_push_file.exists():
                pre_push_file.rename(pre_push_file.with_suffix(".backup"))

            # Write new hooks
            with open(pre_commit_file, "w") as f:
                f.write(pre_commit_hook)

            with open(pre_push_file, "w") as f:
                f.write(pre_push_hook)

            # Make hooks executable
            os.chmod(pre_commit_file, 0o755)
            os.chmod(pre_push_file, 0o755)

            print("✅ Git hooks installed successfully:")
            print(f"  • pre-commit hook: {pre_commit_file}")
            print(f"  • pre-push hook: {pre_push_file}")
            print(
                "\n🔄 Hooks will automatically block operations that violate SOP compliance"
            )

            return 0

        except Exception as e:
            print(f"❌ Failed to install git hooks: {e}")
            return 1

    def uninstall_git_hooks(self) -> int:
        """Uninstall git hooks."""
        hooks_dir = Path(".git/hooks")

        if not hooks_dir.exists():
            print("❌ Not in a git repository")
            return 1

        try:
            pre_commit_file = hooks_dir / "pre-commit"
            pre_push_file = hooks_dir / "pre-push"

            # Remove hooks
            if pre_commit_file.exists():
                pre_commit_file.unlink()
                print(f"🗑️  Removed pre-commit hook")

            if pre_push_file.exists():
                pre_push_file.unlink()
                print(f"🗑️  Removed pre-push hook")

            # Restore backups if they exist
            pre_commit_backup = pre_commit_file.with_suffix(".backup")
            pre_push_backup = pre_push_file.with_suffix(".backup")

            if pre_commit_backup.exists():
                pre_commit_backup.rename(pre_commit_file)
                print(f"🔄 Restored pre-commit backup")

            if pre_push_backup.exists():
                pre_push_backup.rename(pre_push_file)
                print(f"🔄 Restored pre-push backup")

            print("✅ Git hooks uninstalled successfully")

            return 0

        except Exception as e:
            print(f"❌ Failed to uninstall git hooks: {e}")
            return 1

    def get_blocking_status(self) -> Dict[str, Any]:
        """Get current blocking status and statistics."""
        # Read recent blocking events
        recent_events = []
        if self.blocking_log.exists():
            try:
                with open(self.blocking_log) as f:
                    lines = f.readlines()

                for line in lines[-50:]:  # Last 50 events
                    try:
                        event = json.loads(line.strip())
                        recent_events.append(event)
                    except:
                        continue
            except Exception:
                pass

        # Calculate statistics
        total_events = len(recent_events)
        blocked_events = sum(1 for e in recent_events if e.get("blocked", False))
        allowed_events = total_events - blocked_events

        # Get most recent events
        recent_blocked = [e for e in recent_events if e.get("blocked", False)][-5:]

        return {
            "blocking_enabled": self.config.get("blocking_enabled", True),
            "enforcement_level": self.enforcement_engine.config.get(
                "current_enforcement_level", "standard"
            ),
            "statistics": {
                "total_checks": total_events,
                "blocked_operations": blocked_events,
                "allowed_operations": allowed_events,
                "block_rate": (blocked_events / total_events * 100)
                if total_events > 0
                else 0,
            },
            "recent_blocks": recent_blocked,
            "emergency_override_available": self.emergency_file.exists(),
            "last_update": datetime.now().isoformat(),
        }


def main():
    """CLI interface for SOP blocking mechanism."""
    import argparse

    parser = argparse.ArgumentParser(description="Automated SOP Blocking Mechanism")
    parser.add_argument(
        "operation",
        choices=[
            "pre-commit",
            "pre-push",
            "install-hooks",
            "uninstall-hooks",
            "status",
        ],
        help="Operation to perform",
    )
    parser.add_argument("--config", help="Path to configuration file")

    args = parser.parse_args()

    # Create blocking mechanism
    blocker = SOPBlockingMechanism(args.config)

    # Execute operation
    if args.operation == "pre-commit":
        exit_code = blocker.pre_commit_check()
    elif args.operation == "pre-push":
        exit_code = blocker.pre_push_check()
    elif args.operation == "install-hooks":
        exit_code = blocker.install_git_hooks()
    elif args.operation == "uninstall-hooks":
        exit_code = blocker.uninstall_git_hooks()
    elif args.operation == "status":
        status = blocker.get_blocking_status()
        print(json.dumps(status, indent=2))
        exit_code = 0
    else:
        print(f"Unknown operation: {args.operation}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
