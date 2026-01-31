import argparse
import glob
import json
import os
import shutil
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
        return result.stdout.strip(), result.returncode
    except Exception:
        return None, 1


def check_session_conflicts():
    """Verify no other active agent is working on the same task."""
    print("👥 Checking for multi-agent session conflicts...")
    locks_dir = Path(".agent/session_locks")
    if not locks_dir.exists():
        return

    now = datetime.now(timezone.utc)
    stale_threshold = 600  # 10 minutes

    current_lock = None
    all_locks = []

    for lock_path in locks_dir.glob("*.json"):
        try:
            with open(lock_path) as f:
                data = json.load(f)
                data["_path"] = lock_path
                all_locks.append(data)
                # Check if this is the current process or its parent (shell)
                # Note: agent-start.sh runs in a shell, then starts the agent.
                # In most cases, the agent process itself won't be the one in the lock
                # unless it's running heartbeats.
                # However, we can use the environment variable AGENT_LOCK_FILE if set.
                if os.environ.get("AGENT_LOCK_FILE") == str(lock_path):
                    current_lock = data
        except (json.JSONDecodeError, OSError):
            continue

    if not current_lock:
        # Fallback: find freshest lock for this user if no env var
        user_locks = [
            lock_item
            for lock_item in all_locks
            if lock_item.get("agent_name") == os.environ.get("USER")
        ]
        if user_locks:
            current_lock = max(user_locks, key=lambda x: x.get("started_at", ""))

    if not current_lock:
        print("   ℹ️  No current session lock found. Skipping conflict check.")
        return

    current_task = current_lock.get("current_task")
    if current_task == "unknown":
        print("   ℹ️  Current task is 'unknown'. Skipping conflict check.")
        return

    conflicts = []
    for lock in all_locks:
        if lock["_path"] == current_lock["_path"]:
            continue

        if lock.get("current_task") == current_task:
            # Check if active
            hb_str = lock.get("last_heartbeat")
            try:
                hb_time = datetime.fromisoformat(hb_str.replace("Z", "+00:00"))
                if (now - hb_time).total_seconds() < stale_threshold:
                    conflicts.append(lock)
            except (ValueError, TypeError):
                continue

    if conflicts:
        print(f"\n🛑 CONFLICT DETECTED: Another agent is working on {current_task}:")
        for c in conflicts:
            print(f"   - Agent: {c.get('agent_name')} (PID: {c.get('pid')})")
            print(f"     Last heartbeat: {c.get('last_heartbeat')}")
        print("\nPlease coordinate with the other agent or choose a different task.")
        sys.exit(1)
    else:
        print(f"✅ No session conflicts found for task {current_task}.")


def check_workspace_isolation():
    """Ensure the agent is on a dedicated task branch and path."""
    print("🛤️  Checking workspace isolation...")
    branch, code = run_command("git rev-parse --abbrev-ref HEAD")
    if code != 0 or not branch:
        return

    # Check for shared feature branch (anti-pattern)
    if branch in ("main", "master", "develop", "staging"):
        print(f"❌ ERROR: Do NOT work directly on '{branch}'. Create a task branch.")
        sys.exit(1)

    # Check session locks for other agents on THIS branch
    locks_dir = Path(".agent/session_locks")
    if locks_dir.exists():
        current_pid = os.getpid()
        now = datetime.now(timezone.utc)
        for lock_path in locks_dir.glob("*.json"):
            try:
                with open(lock_path) as f:
                    lock = json.load(f)
                    # Skip self
                    if lock.get("pid") == current_pid:
                        continue
                    # Check if lock is active
                    hb_str = lock.get("last_heartbeat")
                    hb_time = datetime.fromisoformat(hb_str.replace("Z", "+00:00"))
                    if (now - hb_time).total_seconds() < 600:
                        # Shared Branch Check
                        if lock.get("current_branch") == branch:
                            print(
                                f"🛑 ISOLATION FAILURE: Agent {lock.get('agent_name')} is already active on branch '{branch}'."
                            )
                            print(
                                "   Use a separate branch and worktree for this task."
                            )
                            sys.exit(1)
                        # Shared Path Check
                        if lock.get("current_path") == str(Path.cwd()):
                            print(
                                f"🛑 ISOLATION FAILURE: Agent {lock.get('agent_name')} is already active in this directory."
                            )
                            print(
                                "   Use 'bd worktree create' to prepare an isolated workspace."
                            )
                            sys.exit(1)
            except Exception:
                continue

    print(f"✅ Workspace Isolated: Branch '{branch}' | Path '{Path.cwd().name}'")


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

        with open(task_file) as f:
            content = f.read()
            # Look for Approval marker with timestamp
            # Format: ## Approval: [User Sign-off at 2026-01-31 15:44]
            pattern = r"## Approval: \[User Sign-off at ([\d\-\s:]+)\]"
            match = re.search(pattern, content)

            if not match:
                errors.append(
                    "❌ Mission Plan NOT APPROVED. Add '## Approval: [User Sign-off at YYYY-MM-DD HH:MM...]' to `task.md` before starting implementation."
                )
            else:
                try:
                    approval_time_str = match.group(1).strip()
                    approval_time = datetime.strptime(
                        approval_time_str, "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)

                    # Check if the approval is "fresh" (e.g., within the last 4 hours)
                    # This prevents stale approvals from previous sessions being reused.
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
        "**/temp/**",
        "**/__pycache__/**",
        "*.pyc",
        "*.pyo",
        # Browser profiles and large data
        "**/.mozilla/**",
        "**/.chrome/**",
        "**/.google-chrome/**",
        "**/chromium/**",
        # Build artifacts
        "**/node_modules/**",
        "**/build/**",
        "**/dist/**",
        "**/target/**",
        "**/venv/**",
        "**/env/**",
        "**/.venv/**",
        # Large temporary files (>10MB)
        "**/*.tmp",
        "**/*.temp",
        "**/*.bak",
        "**/*.old",
        "**/*.swp",
        "**/.DS_Store",
        # Package manager caches
        "**/pip-cache/**",
        "**/uv-cache/**",
        "**/npm-cache/**",
        "**/.cargo/registry/cache/**",
    ]

    found = []
    for pattern in patterns:
        matches = glob.glob(os.path.join(base_dir, pattern), recursive=True)
        found.extend(matches)

    # Also find large files (>10MB) that aren't in git
    try:
        for root, _dirs, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) > 10 * 1024 * 1024:  # >10MB
                        found.append(file_path)
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass

    return found


def clean_bloat_aggressively():
    """Aggressively clean bloat from global config directories."""
    print("🔥 Performing aggressive bloat removal...")

    global_dirs = [
        os.path.expanduser("~/.gemini"),
        os.path.expanduser("~/.antigravity"),
    ]

    total_removed = 0
    total_size_saved = 0

    for base_dir in global_dirs:
        if not os.path.exists(base_dir):
            continue

        print(f"   🧹 Scanning {base_dir}...")
        bloat_items = get_bloat_patterns(base_dir)

        if not bloat_items:
            print(f"   ✅ No bloat found in {base_dir}")
            continue

        for item in bloat_items:
            try:
                path = Path(item)
                size_before = 0

                if path.exists():
                    if path.is_file():
                        size_before = path.stat().st_size
                        path.unlink()
                    elif path.is_dir():
                        # Calculate directory size
                        for root, _dirs, files in os.walk(item):
                            for file in files:
                                try:
                                    size_before += os.path.getsize(
                                        os.path.join(root, file)
                                    )
                                except (OSError, PermissionError):
                                    continue
                        shutil.rmtree(path)

                    total_removed += 1
                    total_size_saved += size_before
                    print(f"   🗑️  Removed: {item} ({size_before / 1024 / 1024:.1f}MB)")

            except (OSError, PermissionError) as e:
                print(f"   ❌ Failed to remove {item}: {e}")

    print(
        f"   ✅ Bloat removal complete: {total_removed} items, {total_size_saved / 1024 / 1024:.1f}MB freed"
    )
    return total_removed, total_size_saved


def clean_artifacts():
    """Purges detected temporary artifacts."""
    artifacts = get_temp_artifacts()
    if not artifacts:
        print("✅ No temporary artifacts found to clean.")
        return

    print("🧹 Cleaning temporary artifacts...")
    for art in artifacts:
        path = Path(art)
        try:
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   Deleted directory: {art}")
            else:
                path.unlink()
                print(f"   Deleted file: {art}")
        except Exception as e:
            print(f"   ❌ Failed to delete {art}: {e}")


def check_rtb_session():
    """Ensure the session lock is properly closed."""
    lock_file = os.environ.get("AGENT_LOCK_FILE")
    if lock_file and os.path.exists(lock_file):
        print(
            "⚠️  Session lock still exists. Please run `./scripts/agent-end.sh` before handoff."
        )
        # We don't exit(1) here yet, as RTB might be run mid-session for validation,
        # but the main RTB check will report it as a warning.
        return False
    return True


def check_rtb():
    """Return To Base: Verify Git, Beads, and Cleanup."""
    print("🛬 Initiating Return To Base (RTB) Check...")
    warnings = []
    critical_errors = []

    # Check session
    if not check_rtb_session():
        warnings.append("⚠️  Session lock still active. Use `agent-end.sh` to close it.")

    # 0. Aggressive Bloat Removal (Always executed)
    print("🔥 Aggressive Bloat Removal Phase...")
    removed_items, size_saved = clean_bloat_aggressively()
    if removed_items == 0:
        print("✅ Aggressive Bloat Removal: NO BLOAT FOUND")
    else:
        print(
            f"✅ Aggressive Bloat Removal: CLEANED {removed_items} items ({size_saved / 1024 / 1024:.1f}MB)"
        )

    # 1. Git Status
    git_status, code = run_command("git status --porcelain")
    if git_status is None:
        critical_errors.append("❌ Git Status Check FAILED. Is this a git repo?")
    elif git_status.strip():
        warnings.append(f"⚠️ Git Repository has uncommitted changes:\n{git_status}")
    else:
        print("✅ Git Repository: CLEAN")

    # 2. Cleanup Check
    found_temp = get_temp_artifacts()
    if found_temp:
        warnings.append(
            f"⚠️ Temporary artifacts found (Run with --clean to purge):\n   {', '.join(found_temp)}"
        )
    else:
        print("✅ Cleanup: NO TEMPORARY ARTIFACTS FOUND")

    # 3. Markdown Lint
    mdlint_path, code = run_command("which markdownlint")
    if mdlint_path:
        # Check task.md and .agent/rules/
        lint_cmd = "markdownlint task.md .agent/rules/*.md"
        lint_out, lint_code = run_command(lint_cmd)
        if lint_code != 0:
            # Filter MD013 if needed, or just report
            warnings.append(f"⚠️ Markdown Lint issues found:\n{lint_out}")
        else:
            print("✅ Markdown Lint: PASSED")
    else:
        print("ℹ️ markdownlint not found. Skipping lint check.")

    # 4. Code Quality (pre-commit)
    print("📋 Checking code quality (pre-commit)...")
    pc_out, pc_code = run_command("pre-commit run --all-files")
    if pc_code != 0:
        # Pre-commit failed. We should provide a summary.
        warnings.append(
            f"⚠️ Pre-commit checks failed! Please fix linting/formatting:\n{pc_out}"
        )
    else:
        print("✅ Pre-commit checks: PASSED")

    # 4.5 Documentation Coverage
    doc_check_script = Path("scripts/check_docs_coverage.py")
    if doc_check_script.exists():
        print("📋 Checking documentation coverage & portability...")
        doc_out, doc_code = run_command("python3 scripts/check_docs_coverage.py")
        if doc_code != 0:
            warnings.append(f"⚠️ Documentation coverage issues found:\n{doc_out}")
        else:
            print("✅ Documentation Coverage: PASSED")

    # 5. WebUI Lint Check
    webui_dir = Path("lightrag_webui")
    if webui_dir.exists():
        print("📋 Checking WebUI code quality...")
        lint_out, lint_code = run_command("cd lightrag_webui && bun run lint")
        if lint_code != 0:
            warnings.append(f"⚠️ WebUI Lint Checks failed!\n{lint_out}")
        else:
            print("✅ WebUI Lint: PASSED")

    # 5. Beads Status
    bd_list, code = run_command("bd list --limit 5")
    if code == 0 and bd_list:
        print(f"ℹ️ Recent Tasks:\n{bd_list}")
        print(
            "   (Did you close your task? Did you list NEW issues created in your Handoff?)"
        )

    if critical_errors:
        print("\n🛑 RTB FAILED (CRITICAL):")
        for e in critical_errors:
            print(f"   {e}")
        sys.exit(1)
    elif warnings:
        print("\n⚠️ RTB WARNINGS (Please address before final handoff):")
        for w in warnings:
            print(f"   {w}")
        sys.exit(1)
    else:
        print("\n✅ RTB PASSED. Ready for handoff.")


def main():
    parser = argparse.ArgumentParser(description="Flight Director: SMP Enforcement")
    parser.add_argument("--pfc", action="store_true", help="Run Pre-Flight Check")
    parser.add_argument("--rtb", action="store_true", help="Run Return To Base Check")
    parser.add_argument(
        "--clean", action="store_true", help="Purge temporary artifacts"
    )
    parser.add_argument(
        "--clean-bloat",
        action="store_true",
        help="Perform aggressive bloat removal from global config directories",
    )

    args = parser.parse_args()

    if args.clean:
        clean_artifacts()

    if args.clean_bloat:
        clean_bloat_aggressively()

    if args.pfc:
        check_pfc()
    elif args.rtb:
        check_rtb()
    elif not args.clean and not args.clean_bloat:
        parser.print_help()


if __name__ == "__main__":
    main()
