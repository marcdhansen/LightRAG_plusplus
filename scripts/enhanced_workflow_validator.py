#!/usr/bin/env python3
"""
Enhanced workflow validator with override restrictions for P0 workflow violation fix.
Prevents agents from skipping phase completion and requires manager approval for overrides.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


class WorkflowValidator:
    """Enhanced workflow validator with override restrictions."""

    def __init__(self):
        self.session_locks_dir = Path(".agent/session_locks")
        self.override_requests_dir = Path(".agent/override_requests")
        self.override_requests_dir.mkdir(exist_ok=True)

    def check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available."""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def get_current_phase(self) -> str:
        """Determine the current phase from git status and session state."""
        # Check for session lock files
        if self.session_locks_dir.exists():
            lock_files = list(self.session_locks_dir.glob("*.json"))
            if lock_files:
                return "active_session"

        # Check git status for phase indicators
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
                    return "work_in_progress"
        except:
            pass

        return "ready"

    def check_phase_completion(self) -> tuple[bool, str]:
        """Check if current phase is properly completed before allowing new work."""
        current_phase = self.get_current_phase()

        if current_phase == "active_session":
            # Check for uncommitted changes
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return (
                        False,
                        "Uncommitted changes exist - must complete current phase before starting new work",
                    )
            except:
                pass

        return True, "Phase completion validated"

    def check_active_session_locks(self) -> list[str]:
        """Check for active session locks that would block new work."""
        violations = []

        if not self.session_locks_dir.exists():
            return violations

        current_time = time.time()
        lock_files = list(self.session_locks_dir.glob("*.json"))

        for lock_file in lock_files:
            # Check if lock is recent (within last hour)
            if lock_file.stat().st_mtime > (current_time - 3600):
                try:
                    with open(lock_file) as f:
                        lock_data = json.load(f)

                    agent_name = lock_data.get("agent", "unknown")
                    task_desc = lock_data.get("task_desc", "unknown task")

                    violations.append(
                        f"Active session lock: {agent_name} working on '{task_desc}' ({lock_file.name})"
                    )
                except:
                    violations.append(f"Active session lock: {lock_file.name}")

        return violations

    def check_beads_assignment(self) -> list[str]:
        """Check if agent is properly assigned to beads tasks."""
        violations = []

        if not self.check_tool_available("bd"):
            return violations

        try:
            result = subprocess.run(
                ["bd", "ready"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                # Look for P0 issues that might need assignment
                if "P0" in result.stdout:
                    violations.append(
                        "P0 work exists - ensure proper task assignment before starting"
                    )
        except:
            pass

        return violations

    def request_override(
        self, reason: str, requested_by: str = "agent"
    ) -> tuple[bool, str]:
        """Request an override with manager approval requirement."""
        override_id = f"override_{int(time.time())}"
        override_file = self.override_requests_dir / f"{override_id}.json"

        override_request = {
            "id": override_id,
            "requested_by": requested_by,
            "reason": reason,
            "timestamp": time.time(),
            "status": "pending_manager_approval",
            "requires_manager_approval": True,
            "approved_by": None,
            "approval_timestamp": None,
        }

        try:
            with open(override_file, "w") as f:
                json.dump(override_request, f, indent=2)

            return False, (
                f"🚨 OVERRIDE REQUEST CREATED: {override_id}\n"
                f"Reason: {reason}\n"
                f"Status: Pending manager approval\n"
                f"⚠️ WORK BLOCKED until manager approval\n"
                f"Manager command: python scripts/minimal_workflow_validator.py --approve-override {override_id}"
            )
        except Exception as e:
            return False, f"Failed to create override request: {e}"

    def approve_override(
        self, override_id: str, manager_id: str = "manager"
    ) -> tuple[bool, str]:
        """Approve an override request (manager only)."""
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

            return True, f"✅ Override {override_id} approved by {manager_id}"
        except Exception as e:
            return False, f"Failed to approve override: {e}"

    def check_override_approval(self, override_id: str) -> tuple[bool, str]:
        """Check if an override has been approved."""
        override_file = self.override_requests_dir / f"{override_id}.json"

        if not override_file.exists():
            return False, f"Override request {override_id} not found"

        try:
            with open(override_file) as f:
                override_request = json.load(f)

            if override_request.get("status") == "approved":
                return (
                    True,
                    f"Override {override_id} approved by {override_request.get('approved_by')}",
                )
            else:
                return False, f"Override {override_id} pending manager approval"
        except Exception as e:
            return False, f"Failed to check override status: {e}"

    def run_workflow_validation(self, allow_override: bool = False) -> tuple[bool, str]:
        """Run enhanced workflow validation with override restrictions."""
        violations = []

        # Check 1: Phase completion
        phase_ok, phase_msg = self.check_phase_completion()
        if not phase_ok:
            violations.append(f"Phase completion violation: {phase_msg}")

        # Check 2: Active session locks
        session_violations = self.check_active_session_locks()
        violations.extend(session_violations)

        # Check 3: Beads assignment
        beads_violations = self.check_beads_assignment()
        violations.extend(beads_violations)

        if violations:
            if allow_override:
                # Create override request
                reason = "; ".join(violations)
                override_ok, override_msg = self.request_override(reason)
                return False, override_msg
            else:
                return False, "🚨 WORKFLOW VIOLATION DETECTED:\n" + "\n".join(
                    f"❌ {v}" for v in violations
                )

        return True, "✅ All workflow gates passed - safe to proceed"

    def show_status(self) -> str:
        """Show current workflow status."""
        status_lines = ["📊 WORKFLOW STATUS", "=" * 30]

        # Current phase
        current_phase = self.get_current_phase()
        status_lines.append(f"Current Phase: {current_phase}")

        # Phase completion
        phase_ok, phase_msg = self.check_phase_completion()
        status_lines.append(
            f"Phase Completion: {'✅' if phase_ok else '❌'} {phase_msg}"
        )

        # Active locks
        session_violations = self.check_active_session_locks()
        if session_violations:
            status_lines.append("Active Locks:")
            for violation in session_violations:
                status_lines.append(f"  ❌ {violation}")
        else:
            status_lines.append("Active Locks: ✅ None")

        # Beads status
        beads_violations = self.check_beads_assignment()
        if beads_violations:
            status_lines.append("Beads Assignment:")
            for violation in beads_violations:
                status_lines.append(f"  ⚠️ {violation}")
        else:
            status_lines.append("Beads Assignment: ✅ Clear")

        # Pending overrides
        if self.override_requests_dir.exists():
            override_files = list(self.override_requests_dir.glob("override_*.json"))
            if override_files:
                status_lines.append("Pending Overrides:")
                for override_file in override_files:
                    try:
                        with open(override_file) as f:
                            override_data = json.load(f)
                        status = override_data.get("status", "unknown")
                        status_lines.append(f"  🔄 {override_file.name}: {status}")
                    except:
                        status_lines.append(f"  🔄 {override_file.name}: error reading")

        return "\n".join(status_lines)


def main():
    """Main entry point."""
    validator = WorkflowValidator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--init":
            # Run initialization check
            success, message = validator.run_workflow_validation()
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--status":
            # Show status
            print(validator.show_status())
            sys.exit(0)

        elif command == "--request-override":
            # Request override
            reason = (
                " ".join(sys.argv[2:])
                if len(sys.argv) > 2
                else "Workflow violation detected"
            )
            success, message = validator.request_override(reason)
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--approve-override":
            # Approve override (manager only)
            if len(sys.argv) < 3:
                print(
                    "Usage: python minimal_workflow_validator.py --approve-override <override_id>"
                )
                sys.exit(1)
            override_id = sys.argv[2]
            success, message = validator.approve_override(override_id)
            print(message)
            sys.exit(0 if success else 1)

        elif command == "--check-override":
            # Check override status
            if len(sys.argv) < 3:
                print(
                    "Usage: python minimal_workflow_validator.py --check-override <override_id>"
                )
                sys.exit(1)
            override_id = sys.argv[2]
            success, message = validator.check_override_approval(override_id)
            print(message)
            sys.exit(0 if success else 1)

        else:
            print(
                "Usage: python minimal_workflow_validator.py [--init|--status|--request-override|--approve-override|--check-override]"
            )
            sys.exit(1)

    else:
        # Default: run workflow validation
        success, message = validator.run_workflow_validation()
        print(message)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
