#!/usr/bin/env python3
"""
Multi-Phase Detection Engine - FIXED VERSION
Identifies complex implementation patterns that bypass mandatory hand-off protocols

FIX: Only scan recent commits (session work), not all historical documentation.
This prevents false positives from keyword matches in old docs.

Exit codes:
0 = Clear (no multi-phase patterns detected)
1 = Block (multi-phase patterns detected - Finalization blocked)
2 = Warning (patterns detected but below threshold)
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path


class MultiPhaseDetector:
    """
    Detection system for multi-phase implementation patterns.
    FIXED: Only scans recent commits, not all documentation.
    """

    def __init__(self, config_path: str | None = None, recent_commits: int = 10):
        self.indicators = {
            "separate_branches": 0,
            "multiple_prs": 0,
            "handoff_docs": 0,
        }
        self.detection_log: list[dict] = []
        self.threshold = 3  # Require 3 DISTINCT indicators
        self.recent_commits = recent_commits
        self.config = self.load_config(config_path)

    def load_config(self, config_path: str | None) -> dict:
        """Load detection configuration"""
        default_config = {
            "threshold": 3,
            "recent_commits": 10,
            "patterns": {
                "separate_branches": [
                    r"feature/[\w-]+",
                    r"agent/[\w-]+",
                    r"fix/[\w-]+",
                    r"chore/[\w-]+",
                ],
                "multiple_prs": [
                    r"\bPR\b",
                    r"\bpr\b",
                    r"pull request",
                ],
                "handoff_docs": [
                    r"handoff",
                    r"phase\d+",
                    r"stage\d+",
                ],
            },
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(
                    f"Warning: Could not load config from {config_path}: {e}",
                    file=sys.stderr,
                )

        return default_config

    def get_recent_commit_messages(self) -> list[str]:
        """Get recent commit messages for analysis"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{self.recent_commits}", "--format=%s %b"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")
        except Exception as e:
            print(f"Warning: Could not get recent commits: {e}")
            return []

    def get_recent_commit_files(self) -> list[str]:
        """Get list of files changed in recent commits"""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{self.recent_commits}",
                    "--name-only",
                    "--pretty=format:",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            return list(set(files))  # Deduplicate
        except Exception as e:
            print(f"Warning: Could not get recent commit files: {e}")
            return []

    def detect_separate_branches(self) -> int:
        """Check if commits come from multiple different branch types"""
        print("   🔍 Checking for separate branches in recent work...")

        try:
            result = subprocess.run(
                ["git", "log", f"-{self.recent_commits}", "--format=%D"],
                capture_output=True,
                text=True,
                check=True,
            )

            branches = result.stdout.strip().split("\n")
            branch_types = set()

            for branch_line in branches:
                # Extract branch names from reflog
                if "feature/" in branch_line:
                    branch_types.add("feature")
                if "agent/" in branch_line:
                    branch_types.add("agent")
                if "fix/" in branch_line or "bugfix/" in branch_line:
                    branch_types.add("fix")
                if "chore/" in branch_line:
                    branch_types.add("chore")
                if "docs/" in branch_line:
                    branch_types.add("docs")

            if len(branch_types) >= 2:
                print(
                    f"     ✅ Found {len(branch_types)} different branch types: {branch_types}"
                )
                return 1
            else:
                print(f"     ✅ Single branch type: {branch_types}")
                return 0

        except Exception as e:
            print(f"     Warning: {e}")
            return 0

    def detect_multiple_prs(self) -> int:
        """Check if recent work involves multiple PRs"""
        print("   🔍 Checking for multiple PRs in recent work...")

        recent_msgs = self.get_recent_commit_messages()

        # Look for PR merge patterns
        pr_keywords = 0
        for msg in recent_msgs:
            if re.search(r"\bPR\b", msg, re.IGNORECASE):
                pr_keywords += 1

        if pr_keywords >= 2:
            print(f"     ✅ Found {pr_keywords} PR-related commits")
            return 1
        else:
            print(f"     ✅ No multiple PRs detected")
            return 0

    def detect_handoff_docs(self) -> int:
        """Check if hand-off documents were created in recent work"""
        print("   🔍 Checking for hand-off documentation...")

        recent_files = self.get_recent_commit_files()

        # Check for hand-off related files
        handoff_files = [
            f for f in recent_files if "handoff" in f.lower() or "hand-off" in f.lower()
        ]

        if handoff_files:
            print(
                f"     ✅ Found {len(handoff_files)} hand-off documents: {handoff_files[:3]}"
            )
            return 1

        # Also check commit messages
        recent_msgs = self.get_recent_commit_messages()
        handoff_in_msgs = 0
        for msg in recent_msgs:
            if re.search(r"handoff|handover|phase\d+|stage\d+", msg, re.IGNORECASE):
                handoff_in_msgs += 1

        if handoff_in_msgs >= 2:
            print(
                f"     ✅ Found {handoff_in_msgs} phase/handoff references in commits"
            )
            return 1

        print(f"     ✅ No hand-off documents detected")
        return 0

    def run_detection(self) -> int:
        """Run complete multi-phase detection analysis"""
        print("🚨 MULTI-PHASE DETECTION ENGINE (FIXED)")
        print("=" * 50)
        print(f"Scanning last {self.recent_commits} commits only")
        print(f"Threshold: {self.threshold} distinct indicators required")
        print()

        start_time = time.time()

        # Run all detection scans
        self.indicators["separate_branches"] = self.detect_separate_branches()
        self.indicators["multiple_prs"] = self.detect_multiple_prs()
        self.indicators["handoff_docs"] = self.detect_handoff_docs()

        # Count distinct indicators (not weighted sum)
        distinct_count = sum(1 for v in self.indicators.values() if v > 0)

        elapsed_time = time.time() - start_time

        print()
        print("📊 DETECTION RESULTS:")
        print("-" * 30)
        for indicator, count in self.indicators.items():
            status = "🚨" if count > 0 else "✅"
            print(f"  {status} {indicator}: {count}")

        print(f"\n🎯 DISTINCT INDICATORS: {distinct_count}/{self.threshold}")
        print(f"⏱️  Analysis completed in {elapsed_time:.2f} seconds")

        # Make determination based on DISTINCT indicators, not weighted sum
        if distinct_count >= self.threshold:
            print("\n🚨 BLOCK: Multiple multi-phase indicators detected!")
            print(
                "   Finalization blocked until proper hand-off protocols are followed."
            )
            return 1
        elif distinct_count >= 2:
            print("\n⚠️  WARNING: Some multi-phase indicators detected.")
            print("   Consider proper hand-off documentation.")
            return 2
        else:
            print("\n✅ CLEAR: No multi-phase patterns detected in recent work.")
            print("   Proceeding with normal workflow.")
            return 0


def main():
    """Main entry point for the detection engine"""
    config_path = None
    recent_commits = 10

    # Parse arguments
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--commits" and i + 2 < len(sys.argv):
            try:
                recent_commits = int(sys.argv[i + 2])
            except ValueError:
                pass
        elif not arg.startswith("-"):
            config_path = arg

    detector = MultiPhaseDetector(config_path, recent_commits)
    exit_code = detector.run_detection()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
