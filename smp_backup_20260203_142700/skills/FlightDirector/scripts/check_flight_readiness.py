#!/usr/bin/env python3
"""
Pre-Flight Check (PFC) for AutoFlightDirector
Enhanced with TDD Gate validation
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and return stdout+stderr. Raises error on failure."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            cwd=cwd,
        )
        return result.stdout, result.returncode
    except Exception:
        return None, 1


def check_session_conflicts():
    """Check for agent session conflicts."""
    print("\n🔍 Agent Session Coordination Check...")
    active_sessions = []
    session_dir = Path.cwd().parent.parent / ".agent" / "session_locks"

    if session_dir.exists():
        for lock_file in session_dir.glob("*.json"):
            try:
                with open(lock_file) as f:
                    data = json.load(f)
                active_sessions.append(
                    f"{data.get('agent', 'unknown')} on {data.get('task_desc', 'unknown task')}"
                )
            except:
                pass

    if active_sessions:
        print("⚠️  Active agents detected:")
        for session in active_sessions:
            print(f"   • {session}")
        print("📋 Run './scripts/agent-status.sh' for details.")
    else:
        print("✅ No active agent conflicts detected.")


def check_workspace_isolation():
    """Check if workspace is properly isolated."""
    print("\n🗂️  Workspace Isolation Check...")

    # Check if we're on main/master branch
    try:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True
        )
        branch = branch_result.stdout.strip()

        if branch in ["main", "master"]:
            print("❌ DANGER: You are on main/master branch!")
            print("   Create a feature branch before starting work.")
        else:
            print(f"✅ Workspace Isolated: Branch '{branch}'")
    except:
        print("⚠️  Could not determine git branch.")

    # Check worktree isolation
    worktree_path = Path.cwd()
    repo_root = worktree_path

    try:
        git_dir_result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=worktree_path,
        )
        if git_dir_result.returncode == 0:
            git_dir = Path(git_dir_result.stdout.strip())
            if not git_dir.is_absolute():
                git_dir = worktree_path / git_dir

            # Check if this is a worktree
            worktree_file = git_dir / "worktrees"
            if worktree_file.exists():
                print(f"✅ Git Worktree: DETECTED at {worktree_path.name}")
            else:
                print(f"✅ Git Repository: OK at {worktree_path.name}")
    except:
        print("⚠️  Could not verify git structure.")


def check_pfc():
    """Pre-Flight Check: Verify Beads issue, Task artifact, and Sessions."""
    print("🛫 Initiating Pre-Flight Check (PFC)...")
    errors = []

    # 1. Multi-Agent Coordination
    check_session_conflicts()
    check_workspace_isolation()

    # 2. Check Beads
    bd_check, code = run_command("bd ready")
    if bd_check is None or code != 0:
        errors.append(
            "❌ Beads (`bd`) check failed. Is beads installed and initialized?"
        )
    else:
        print("✅ Beads System: ONLINE")

    # 2. Check Task Artifacts
    cwd = Path.cwd()
    task_file = cwd / "task.md"
    if not task_file.exists():
        errors.append("❌ `task.md` missing in current directory.")
    else:
        print("✅ `task.md`: FOUND")

    rules_dir = cwd / ".agent" / "rules"
    if not rules_dir.exists():
        errors.append(
            "❌ `.agent/rules/` directory missing. Planning documents required."
        )
    else:
        roadmap = rules_dir / "ROADMAP.md"
        plan = rules_dir / "ImplementationPlan.md"
        if not roadmap.exists():
            errors.append("❌ `ROADMAP.md` missing in .agent/rules/")
        if not plan.exists():
            errors.append("❌ `ImplementationPlan.md` missing in .agent/rules/")
        if roadmap.exists() and plan.exists():
            print("✅ Planning Documents: FOUND")

    # 3. Check for Plan Approval in task.md
    if task_file.exists():
        import re

        try:
            with open(task_file) as f:
                content = f.read()

            # Look for approval timestamp
            approval_match = re.search(
                r"Plan\s+Approved:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", content
            )
            if not approval_match:
                errors.append(
                    "❌ Mission Plan Approval required. "
                    "Add 'Plan Approved: YYYY-MM-DD HH:MM' to task.md"
                )
            else:
                approval_time = datetime.strptime(
                    approval_match.group(1), "%Y-%m-%d %H:%M"
                )
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                age_hours = (now - approval_time).total_seconds() / 3600
                if age_hours > 4:
                    errors.append(
                        f"❌ Mission Plan Approval is STALE ({age_hours:.1f} hours old). "
                        "Please re-review the plan and update the timestamp in `task.md` to authorize the current session."
                    )
                else:
                    print(
                        f"✅ Mission Plan: APPROVED (Freshness: {age_hours:.1f} hours)"
                    )
        except ValueError:
            errors.append(
                "❌ Mission Plan Approval format INVALID. Use 'YYYY-MM-DD HH:MM' format."
            )

    # 4. TDD Validation Gate
    print("\n🔬 TDD Gate Validation...")
    # Use current directory (should be project root or worktree)
    base_dir = Path.cwd()

    # Try different possible locations for the TDD validator
    tdd_validator_paths = [
        base_dir / ".agent" / "scripts" / "tdd_gate_validator.py",
        base_dir.parent / ".agent" / "scripts" / "tdd_gate_validator.py",
        base_dir.parent.parent / ".agent" / "scripts" / "tdd_gate_validator.py",
    ]

    tdd_validator_path = None
    for path in tdd_validator_paths:
        if path.exists():
            tdd_validator_path = path
            break

    if tdd_validator_path:
        try:
            tdd_result = subprocess.run(
                ["python", str(tdd_validator_path)],
                capture_output=True,
                text=True,
                cwd=base_dir,
            )
            if tdd_result.returncode != 0:
                errors.append("❌ TDD Gate validation FAILED")
                for line in tdd_result.stderr.strip().split("\n"):
                    if line.strip():
                        errors.append(f"   {line}")
            else:
                print("✅ TDD Gate: PASSED")
        except Exception as e:
            errors.append(f"❌ TDD Gate validation ERROR: {e}")
    else:
        errors.append(
            "❌ TDD Gate validator not found at .agent/scripts/tdd_gate_validator.py"
        )

    if errors:
        print("\n🛑 PFC FAILED:")
        for e in errors:
            print(f"   {e}")
        sys.exit(1)
    else:
        print("\n✅ PFC PASSED. You are clear for takeoff.")


def get_temp_artifacts():
    """Returns a list of matching temporary artifacts."""
    temp_patterns = [
        "rag_storage_*",
        "test_output.txt",
        "debug_*.py",
        "testing_server_autostart.log",
        "temp",
        "test_ace_curator*",
        "tests/rag_storage_*",
    ]
    found = []
    for pattern in temp_patterns:
        matches = glob.glob(pattern)
        found.extend(matches)
    return found


def get_bloat_patterns(base_dir):
    """Returns aggressive bloat patterns for given directory."""
    patterns = [
        # Large binary files
        "**/*.log",
        "**/*.cache",
        "**/cache/**",
        "**/tmp/**",
        # Build artifacts
        "**/__pycache__/**",
        "**/build/**",
        "**/dist/**",
        "*.egg-info/**",
        # Test outputs
        "test_output/**",
        "test_*.json",
        # Temporary files
        "temp/**",
        "tmp/**",
        "**/.pytest_cache/**",
        "**/.coverage",
        "**/htmlcov/**",
    ]
    return [os.path.join(base_dir, p) for p in patterns]


def check_temp_cleanup():
    """Check for temporary artifacts that should be cleaned up."""
    print("\n🧹 Temporary Artifact Cleanup Check...")

    # Check for temporary files
    temp_files = get_temp_artifacts()
    if temp_files:
        print(f"⚠️  Found {len(temp_files)} temporary artifacts:")
        for f in temp_files:
            print(f"   • {f}")
        print("   Consider cleaning these up.")
    else:
        print("✅ No problematic temporary artifacts found.")

    # Check for bloat
    bloat_patterns = get_bloat_patterns(".")
    bloat_files = []
    for pattern in bloat_patterns:
        matches = glob.glob(pattern)
        bloat_files.extend(matches)

    if bloat_files:
        print(f"⚠️  Found {len(bloat_files)} bloat files:")
        for f in bloat_files[:10]:  # Show first 10
            print(f"   • {f}")
        if len(bloat_files) > 10:
            print(f"   ... and {len(bloat_files) - 10} more")
        print("   Consider adding to .gitignore or cleaning up.")
    else:
        print("✅ No significant bloat detected.")


def check_git_status():
    """Check git repository status."""
    print("\n📊 Git Repository Status Check...")

    try:
        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        )
        changed_files = [
            line for line in status_result.stdout.split("\n") if line.strip()
        ]

        if changed_files:
            print(f"⚠️  {len(changed_files)} uncommitted changes:")
            for change in changed_files[:5]:  # Show first 5
                print(f"   {change}")
            if len(changed_files) > 5:
                print(f"   ... and {len(changed_files) - 5} more")
            print("   Consider committing or stashing changes.")
        else:
            print("✅ Working directory clean.")

        # Check for recent commits
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"], capture_output=True, text=True
        )
        if log_result.returncode == 0:
            commits = log_result.stdout.strip().split("\n")
            print(f"✅ Recent commits: {len(commits)} in local history")

    except Exception as e:
        print(f"⚠️  Could not check git status: {e}")


def main():
    parser = argparse.ArgumentParser(description="Flight Director Pre-Flight Check")
    parser.add_argument("--pfc", action="store_true", help="Run Pre-Flight Check")

    args = parser.parse_args()

    if args.pfc:
        check_pfc()
        check_temp_cleanup()
        check_git_status()
    else:
        print("Use --pfc to run Pre-Flight Check")


if __name__ == "__main__":
    main()
