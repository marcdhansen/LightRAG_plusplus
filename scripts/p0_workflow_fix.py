#!/usr/bin/env python3
"""
P0 Workflow Violation Fix - Complete Solution
Implements comprehensive workflow validation to prevent agents from skipping phase completion.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class WorkflowViolationFixer:
    """
    Complete solution for P0 workflow violation issue.

    Addresses the critical problem where agents start new phases without properly
    completing current phases, violating Orchestrator-enforced workflow sequencing.
    """

    def __init__(self):
        self.session_locks_dir = Path(".agent/session_locks")
        self.override_requests_dir = Path(".agent/override_requests")
        self.phase_completion_dir = Path(".agent/phase_completion")

        # Ensure directories exist
        self.override_requests_dir.mkdir(exist_ok=True)
        self.phase_completion_dir.mkdir(exist_ok=True)

    def check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available."""
        try:
            result = subprocess.run([tool, "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def get_current_phase_state(self) -> dict[str, Any]:
        """Get comprehensive current phase state."""
        state = {
            "git_status": "clean",
            "active_locks": [],
            "uncommitted_changes": False,
            "current_phase": "ready",
        }

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                changes = result.stdout.strip()
                if changes:
                    state["git_status"] = "dirty"
                    state["uncommitted_changes"] = True
                    state["current_phase"] = "work_in_progress"
        except:
            pass

        # Check active session locks
        if self.session_locks_dir.exists():
            current_time = time.time()
            lock_files = list(self.session_locks_dir.glob("*.json"))

            for lock_file in lock_files:
                if lock_file.stat().st_mtime > (
                    current_time - 3600
                ):  # Active within last hour
                    try:
                        with open(lock_file) as f:
                            lock_data = json.load(f)
                        state["active_locks"].append(
                            {
                                "file": lock_file.name,
                                "agent": lock_data.get("agent_name", "unknown"),
                                "task": lock_data.get("current_task", "unknown"),
                                "session": lock_data.get("session_id", "unknown"),
                            }
                        )
                    except:
                        state["active_locks"].append(
                            {
                                "file": lock_file.name,
                                "agent": "unknown",
                                "task": "unknown",
                                "session": "unknown",
                            }
                        )

        if state["active_locks"]:
            state["current_phase"] = "active_session"

        return state

    def check_phase_completion_requirements(self) -> tuple[bool, list[str]]:
        """Check all phase completion requirements."""
        violations = []
        state = self.get_current_phase_state()

        # Requirement 1: No uncommitted changes
        if state["uncommitted_changes"]:
            violations.append(
                "Uncommitted changes exist - must commit all work before phase transition"
            )

        # Requirement 2: No active session locks (or proper cleanup)
        if state["active_locks"]:
            for lock in state["active_locks"]:
                violations.append(
                    f"Active session lock: {lock['agent']} working on '{lock['task']}' "
                    f"({lock['file']}) - must complete current session"
                )

        # Requirement 3: Check for proper phase documentation
        phase_completion_file = self.phase_completion_dir / "current_phase_status.json"
        if phase_completion_file.exists():
            try:
                with open(phase_completion_file) as f:
                    phase_data = json.load(f)
                if phase_data.get("status") != "completed":
                    violations.append(
                        f"Current phase '{phase_data.get('phase', 'unknown')}' not marked as completed"
                    )
            except:
                violations.append("Unable to read phase completion status")

        return len(violations) == 0, violations

    def create_phase_completion_record(
        self, phase: str, completion_summary: str
    ) -> bool:
        """Create a phase completion record."""
        record = {
            "phase": phase,
            "status": "completed",
            "completion_time": time.time(),
            "completion_summary": completion_summary,
            "git_commit": self._get_current_commit(),
            "agent": os.environ.get("OPENCODE_AGENT_NAME", "unknown"),
        }

        try:
            phase_completion_file = (
                self.phase_completion_dir / "current_phase_status.json"
            )
            with open(phase_completion_file, "w") as f:
                json.dump(record, f, indent=2)
            return True
        except:
            return False

    def _get_current_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "unknown"

    def request_phase_transition_override(
        self, from_phase: str, to_phase: str, reason: str
    ) -> tuple[bool, str]:
        """
        Request an override for phase transition with manager approval requirement.

        This addresses the P0 issue by requiring explicit manager approval for
        any phase transition bypass.
        """
        override_id = f"phase_override_{int(time.time())}"
        override_file = self.override_requests_dir / f"{override_id}.json"

        override_request = {
            "id": override_id,
            "type": "phase_transition_override",
            "from_phase": from_phase,
            "to_phase": to_phase,
            "reason": reason,
            "requested_by": os.environ.get("OPENCODE_AGENT_NAME", "agent"),
            "timestamp": time.time(),
            "status": "pending_manager_approval",
            "requires_manager_approval": True,
            "approved_by": None,
            "approval_timestamp": None,
            "violation_type": "P0_workflow_violation",
        }

        try:
            with open(override_file, "w") as f:
                json.dump(override_request, f, indent=2)

            return False, (
                f"🚨 P0 PHASE TRANSITION OVERRIDE REQUESTED\n"
                f"Override ID: {override_id}\n"
                f"From: {from_phase} → To: {to_phase}\n"
                f"Reason: {reason}\n"
                f"Status: PENDING MANAGER APPROVAL\n"
                f"⚠️ CRITICAL: WORK BLOCKED until manager approval\n"
                f"Manager command: python scripts/p0_workflow_fix.py --approve-override {override_id}"
            )
        except Exception as e:
            return False, f"Failed to create override request: {e}"

    def approve_phase_transition_override(
        self, override_id: str, manager_id: str = "manager"
    ) -> tuple[bool, str]:
        """Approve a phase transition override (manager only)."""
        override_file = self.override_requests_dir / f"{override_id}.json"

        if not override_file.exists():
            return False, f"Override request {override_id} not found"

        try:
            with open(override_file) as f:
                override_request = json.load(f)

            if override_request.get("status") == "approved":
                return False, f"Override {override_id} already approved"

            # Update with approval
            override_request["status"] = "approved"
            override_request["approved_by"] = manager_id
            override_request["approval_timestamp"] = time.time()

            with open(override_file, "w") as f:
                json.dump(override_request, f, indent=2)

            return (
                True,
                f"✅ P0 Phase transition override {override_id} approved by {manager_id}",
            )
        except Exception as e:
            return False, f"Failed to approve override: {e}"

    def enforce_phase_gates(self, target_phase: str) -> tuple[bool, str]:
        """
        Enforce phase gates to prevent workflow violations.

        This is the core enforcement mechanism for the P0 issue.
        """
        # Check current phase completion
        completion_ok, violations = self.check_phase_completion_requirements()

        if not completion_ok:
            # Create override request for P0 violation
            current_state = self.get_current_phase_state()
            reason = f"P0 workflow violation: {'; '.join(violations)}"

            return self.request_phase_transition_override(
                from_phase=current_state["current_phase"],
                to_phase=target_phase,
                reason=reason,
            )

        return (
            True,
            f"✅ Phase transition to {target_phase} approved - all requirements met",
        )

    def run_comprehensive_validation(self) -> tuple[bool, str]:
        """Run comprehensive P0 workflow validation."""
        print("🚨 P0 WORKFLOW VIOLATION PREVENTION SYSTEM")
        print("=" * 60)
        print()

        # Get current state
        state = self.get_current_phase_state()
        print(f"Current Phase: {state['current_phase']}")
        print(f"Git Status: {state['git_status']}")
        print(f"Active Locks: {len(state['active_locks'])}")
        print()

        # Check phase completion
        completion_ok, violations = self.check_phase_completion_requirements()

        if violations:
            print("❌ P0 WORKFLOW VIOLATION DETECTED:")
            for violation in violations:
                print(f"   • {violation}")
            print()
            print("🚨 CRITICAL: This violates the Universal Agent Protocol")
            print("🚨 Phase-based development sequence enforcement compromised")
            print()
            print("REQUIRED ACTIONS:")
            print("1. Complete current phase finalization")
            print("2. Commit and push all changes")
            print("3. Close current session locks")
            print("4. Use proper phase transition procedures")
            print("5. Request manager override for emergency bypass only")
            print()
            return False, "P0 WORKFLOW VIOLATION - WORK BLOCKED"

        print("✅ P0 WORKFLOW VALIDATION PASSED")
        print("All phase completion requirements satisfied")
        print("Safe to proceed with new work")
        return True, "P0 VALIDATION PASSED"

    def show_comprehensive_status(self) -> str:
        """Show comprehensive workflow status."""
        state = self.get_current_phase_state()
        completion_ok, violations = self.check_phase_completion_requirements()

        status_lines = [
            "🚨 P0 WORKFLOW VIOLATION PREVENTION STATUS",
            "=" * 50,
            "",
            f"Current Phase: {state['current_phase']}",
            f"Git Status: {state['git_status']}",
            f"Uncommitted Changes: {state['uncommitted_changes']}",
            f"Active Session Locks: {len(state['active_locks'])}",
            "",
            "Phase Completion Requirements:",
            f"  Status: {'✅ PASSED' if completion_ok else '❌ FAILED'}",
        ]

        if violations:
            status_lines.append("  Violations:")
            for violation in violations:
                status_lines.append(f"    ❌ {violation}")

        if state["active_locks"]:
            status_lines.append("")
            status_lines.append("Active Session Locks:")
            for lock in state["active_locks"]:
                status_lines.append(
                    f"  🔒 {lock['agent']} working on '{lock['task']}' ({lock['file']})"
                )

        # Check for pending overrides
        if self.override_requests_dir.exists():
            override_files = list(
                self.override_requests_dir.glob("phase_override_*.json")
            )
            if override_files:
                status_lines.append("")
                status_lines.append("Pending Phase Transition Overrides:")
                for override_file in override_files:
                    try:
                        with open(override_file) as f:
                            override_data = json.load(f)
                        status = override_data.get("status", "unknown")
                        from_phase = override_data.get("from_phase", "unknown")
                        to_phase = override_data.get("to_phase", "unknown")
                        status_lines.append(f"  🔄 {from_phase} → {to_phase}: {status}")
                    except:
                        status_lines.append(f"  🔄 {override_file.name}: error reading")

        return "\n".join(status_lines)


def main():
    """Main entry point."""
    fixer = WorkflowViolationFixer()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--validate":
            # Run comprehensive validation
            success, message = fixer.run_comprehensive_validation()
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--status":
            # Show comprehensive status
            print(fixer.show_comprehensive_status())
            sys.exit(0)

        elif command == "--enforce-gate":
            # Enforce phase gate for target phase
            if len(sys.argv) < 3:
                print(
                    "Usage: python scripts/p0_workflow_fix.py --enforce-gate <target_phase>"
                )
                sys.exit(1)
            target_phase = sys.argv[2]
            success, message = fixer.enforce_phase_gates(target_phase)
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--approve-override":
            # Approve override (manager only)
            if len(sys.argv) < 3:
                print(
                    "Usage: python scripts/p0_workflow_fix.py --approve-override <override_id>"
                )
                sys.exit(1)
            override_id = sys.argv[2]
            success, message = fixer.approve_phase_transition_override(override_id)
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--complete-phase":
            # Complete current phase
            if len(sys.argv) < 4:
                print(
                    "Usage: python scripts/p0_workflow_fix.py --complete-phase <phase> <summary>"
                )
                sys.exit(1)
            phase = sys.argv[2]
            summary = " ".join(sys.argv[3:])
            success = fixer.create_phase_completion_record(phase, summary)
            if success:
                print(f"✅ Phase '{phase}' marked as completed")
                sys.exit(0)
            else:
                print(f"❌ Failed to complete phase '{phase}'")
                sys.exit(1)

        else:
            print(
                "Usage: python scripts/p0_workflow_fix.py [--validate|--status|--enforce-gate|--approve-override|--complete-phase]"
            )
            sys.exit(1)

    else:
        # Default: run comprehensive validation
        success, message = fixer.run_comprehensive_validation()
        print(message)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
