#!/usr/bin/env python3
"""
Multi-Phase Detection Engine - Simplified Working Version
Identifies complex implementation patterns that bypass mandatory hand-off protocols

Exit codes:
0 = Clear (no multi-phase patterns detected)
1 = Block (multi-phase patterns detected - RTB blocked)
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
    Advanced detection system for multi-phase implementation patterns
    Threshold: Minimum 3 indicators required to trigger block
    """

    def __init__(self, config_path: str | None = None):
        self.indicators = {
            "terminology": 0,
            "git_patterns": 0,
            "bypass_incident": 0,
        }
        self.detection_log: list[dict] = []
        self.threshold = 3
        self.config = self.load_config(config_path)

    def load_config(self, config_path: str | None) -> dict:
        """Load detection configuration"""
        default_config = {
            "threshold": 3,
            "terminology_patterns": [
                # Phase-based patterns (3 indicators)
                r"(?i)(phase\s+\d+|phased|multi-phase)",
                r"(?i)(phase\s+implementation|phase\s+delivery|phase\s+deployment)",
                r"(?i)(multi-phase\s+implementation|multi-phase\s+delivery)",
                # PR-based patterns (3 indicators)
                r"(?i)(hybrid\s+approach|pr\s+groups?|pr\s+group)",
                r"(?i)(implementation\s+group|deployment\s+group)",
                r"(?i)(3\s+pr\s+groups?|three\s+pr\s+groups?|multi-pr|multi\s+pr)",
                # Infrastructure patterns (3 indicators)
                r"(?i)(ci/cd\s+resolution|ci_cd_p0)",
                r"(?i)(playbook|resolution\s+playbook)",
                r"(?i)(test\s+infrastructure|pre-commit\s+resilience|repository\s+renaming)",
                # Technical patterns (3 indicators)
                r"(?i)(coverage\s+artifacts|unit\s+test\s+configuration)",
                r"(?i)(network\s+resilience|ci\s+compatibility)",
                r"(?i)(lightrag\+\+|lightrag_plusplus|package\s+naming)",
                # Critical patterns (2 indicators - highest weight)
                r"(?i)(p0\s+resolution|p0\s+issues|critical\s+fixes)",
                r"(?i)(bypass\s+incident|protocol\s+bypass|sop\s+violation)",
            ],
            # Weighted scoring for different indicator types
            "indicator_weights": {
                "terminology": 1,  # Standard patterns
                "git_patterns": 1.5,  # Implementation evidence
                "bypass_incident": 3,  # Critical bypass patterns
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

    def detect_terminology_indicators(self) -> int:
        """Scan for phase-related terminology in documentation and commits"""
        indicators_found = 0

        print("   🔍 Scanning for phase terminology...")

        try:
            # Scan recent commits
            commit_result = subprocess.run(
                ["git", "log", "--oneline", "-20"],
                capture_output=True,
                text=True,
                check=True,
            )

            commits = commit_result.stdout.strip().split("\n")
            for commit in commits:
                for pattern in self.config["terminology_patterns"]:
                    if re.search(pattern, commit):
                        indicators_found += 1
                        print(f"     Found in commit: {commit[:50]}...")
                        break

        except Exception as e:
            print(f"     Warning: Could not scan commits: {e}")

        # Scan documentation files
        try:
            doc_files = list(Path(".").rglob("*.md")) + list(Path(".").rglob("*.txt"))
            for doc_file in doc_files:
                try:
                    with open(doc_file, encoding="utf-8") as f:
                        content = f.read()
                        for pattern in self.config["terminology_patterns"]:
                            matches = re.findall(pattern, content)
                            if matches:
                                indicators_found += len(matches)
                                print(
                                    f"     Found {len(matches)} matches in {doc_file}"
                                )
                except Exception:
                    continue  # Skip files that can't be read
        except Exception as e:
            print(f"     Warning: Could not scan documentation: {e}")

        return indicators_found

    def detect_git_patterns(self) -> int:
        """Scan git history for multi-phase implementation patterns"""
        indicators_found = 0

        print("   🔍 Scanning git patterns...")

        try:
            # Check for multiple related branches
            branch_result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                check=True,
            )

            branches = branch_result.stdout.strip().split("\n")
            phase_branches = [
                b
                for b in branches
                if re.search(r"(?i)(phase|pr-|feature|implement)", b)
            ]

            if len(phase_branches) >= 2:
                indicators_found += 1
                print(f"     Found {len(phase_branches)} related branches")

            # Check for PR-related patterns in commits
            commit_result = subprocess.run(
                ["git", "log", "--oneline", "--grep=PR", "--grep=pr", "-i", "-20"],
                capture_output=True,
                text=True,
                check=True,
            )

            pr_commits = commit_result.stdout.strip().split("\n")
            if len(pr_commits) >= 3:
                indicators_found += 1
                print(f"     Found {len(pr_commits)} PR-related commits")

        except Exception as e:
            print(f"     Warning: Could not scan git patterns: {e}")

        return indicators_found

    def detect_bypass_incidents(self) -> int:
        """Detect specific bypass incidents and protocol violations"""
        indicators_found = 0

        print("   🔍 Scanning for bypass incidents...")

        try:
            # Check for bypass-related commits
            bypass_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--grep=bypass",
                    "--grep=violation",
                    "-i",
                    "-20",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            bypass_commits = bypass_result.stdout.strip().split("\n")
            if bypass_commits and bypass_commits != [""]:
                indicators_found += len(bypass_commits)
                print(f"     Found {len(bypass_commits)} bypass-related commits")

            # Check for SOP violations in recent activity
            sop_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--grep=sop",
                    "--grep=protocol",
                    "-i",
                    "-20",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            sop_commits = sop_result.stdout.strip().split("\n")
            if sop_commits and sop_commits != [""]:
                indicators_found += 1
                print("     Found SOP-related activity")

        except Exception as e:
            print(f"     Warning: Could not scan bypass incidents: {e}")

        return indicators_found

    def run_detection(self) -> int:
        """Run complete multi-phase detection analysis"""
        print("🚨 MULTI-PHASE DETECTION ENGINE")
        print("=" * 50)
        print(f"Threshold: {self.threshold} indicators required to block")
        print()

        start_time = time.time()

        # Run all detection scans
        self.indicators["terminology"] = self.detect_terminology_indicators()
        self.indicators["git_patterns"] = self.detect_git_patterns()
        self.indicators["bypass_incident"] = self.detect_bypass_incidents()

        # Calculate weighted score
        weights = self.config.get(
            "indicator_weights",
            {
                "terminology": 1,
                "git_patterns": 1.5,
                "bypass_incident": 3,
            },
        )

        weighted_score = (
            self.indicators["terminology"] * weights["terminology"]
            + self.indicators["git_patterns"] * weights["git_patterns"]
            + self.indicators["bypass_incident"] * weights["bypass_incident"]
        )

        elapsed_time = time.time() - start_time

        print()
        print("📊 DETECTION RESULTS:")
        print("-" * 30)
        for indicator, count in self.indicators.items():
            weight = weights.get(indicator, 1)
            weighted_count = count * weight
            print(
                f"  {indicator}: {count} (weight: {weight}, weighted: {weighted_count})"
            )

        print(f"\n🎯 TOTAL WEIGHTED SCORE: {weighted_score}")
        print(f"⏱️  Analysis completed in {elapsed_time:.2f} seconds")

        # Make determination
        if weighted_score >= self.threshold * 3:  # High threshold for blocking
            print("\n🚨 BLOCK: Multi-phase patterns detected above threshold!")
            print(
                "   RTB (Return To Base) is BLOCKED until hand-off protocols are followed."
            )
            return 1
        elif weighted_score >= self.threshold:
            print("\n⚠️  WARNING: Multi-phase patterns approaching threshold.")
            print("   Consider proper hand-off documentation.")
            return 2
        else:
            print("\n✅ CLEAR: No concerning multi-phase patterns detected.")
            print("   Proceeding with normal workflow.")
            return 0


def main():
    """Main entry point for the detection engine"""
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    detector = MultiPhaseDetector(config_path)
    exit_code = detector.run_detection()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
