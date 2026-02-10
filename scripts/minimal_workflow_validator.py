#!/usr/bin/env python3
"""
Minimal protocol compliance checker for P0 workflow violation fix.
Addresses the critical issue where agents skip phase completion before starting new work.
"""

import subprocess
import sys
from pathlib import Path


def check_tool_available(tool: str) -> bool:
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


def get_current_phase() -> str:
    """Determine the current phase from git status and session state."""
    # Check for session lock files
    session_locks_dir = Path(".agent/session_locks")
    if session_locks_dir.exists():
        lock_files = list(session_locks_dir.glob("*.json"))
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


def check_phase_completion() -> tuple[bool, str]:
    """Check if current phase is properly completed before allowing new work."""
    current_phase = get_current_phase()

    if current_phase == "active_session":
        # Check if there are uncommitted changes
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
                    "❌ PHASE COMPLETION VIOLATION: Uncommitted changes exist - must complete current phase before starting new work",
                )
        except:
            pass

    return True, "✅ Phase completion validated"


def check_workflow_gates() -> tuple[bool, str]:
    """Enforce workflow gates to prevent phase skipping."""
    gates = []

    # Gate 1: Check for proper phase completion
    phase_ok, phase_msg = check_phase_completion()
    if not phase_ok:
        gates.append(phase_msg)

    # Gate 2: Check for active session locks
    session_locks_dir = Path(".agent/session_locks")
    if session_locks_dir.exists():
        lock_files = list(session_locks_dir.glob("*.json"))
        if lock_files:
            # Check if any lock is recent (within last hour)
            import time

            current_time = time.time()
            for lock_file in lock_files:
                if lock_file.stat().st_mtime > (current_time - 3600):
                    gates.append(
                        f"❌ ACTIVE SESSION LOCK: {lock_file.name} - must complete current session before starting new work"
                    )

    # Gate 3: Check for beads issues in progress
    if check_tool_available("bd"):
        try:
            result = subprocess.run(
                ["bd", "ready"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                # If there are P0 issues, this might be a workflow violation
                if "P0" in result.stdout and "work" in result.stdout.lower():
                    gates.append(
                        "⚠️ P0 WORK EXISTS: Ensure you're assigned to this task before starting"
                    )
        except:
            pass

    if gates:
        return False, "\n".join(gates)

    return True, "✅ All workflow gates passed"


def run_workflow_validation() -> bool:
    """Run workflow validation to prevent phase skipping violations."""
    print("🚨 WORKFLOW VIOLATION PREVENTION SYSTEM")
    print("=" * 50)
    print()

    # Check workflow gates
    gates_ok, gates_msg = check_workflow_gates()
    print(f"Workflow Gates: {gates_msg}")
    print()

    if not gates_ok:
        print("❌ WORKFLOW VIOLATION DETECTED")
        print("Agents must complete current phase before starting new work.")
        print()
        print("REQUIRED ACTIONS:")
        print("1. Complete any pending phase finalization")
        print("2. Commit and push all changes")
        print("3. Close or update current session locks")
        print("4. Use proper phase transition procedures")
        print()
        return False

    print("✅ WORKFLOW VALIDATION PASSED")
    print("Safe to proceed with new work.")
    return True


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--init":
            # Run initialization check
            success = run_workflow_validation()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--status":
            # Run status check
            gates_ok, gates_msg = check_workflow_gates()
            print(f"Status: {gates_msg}")
            sys.exit(0 if gates_ok else 1)
        else:
            print("Usage: python minimal_compliance_checker.py [--init|--status]")
            sys.exit(1)
    else:
        # Default: run workflow validation
        success = run_workflow_validation()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
