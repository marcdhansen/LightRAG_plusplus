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
from datetime import datetime
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
        self.threshold = 3
        self.detection_log = []
        self.config = self.load_config(config_path)

    def load_config(self, config_path: str | None) -> dict:
        """Load detection configuration"""
        default_config = {
            "threshold": 3,
            "terminology_patterns": [
                r"(?i)(phase\s+\d+|phased|multi-phase)",
                r"(?i)(hybrid\s+approach|pr\s+groups?|pr\s+group)",
                r"(?i)(implementation\s+group|deployment\s+group)",
                # CRITICAL: Add specific bypass incident patterns
                r"(?i)(3\s+pr\s+groups?|three\s+pr\s+groups?)",
                r"(?i)(multi-pr|multi\s+pr)",
                r"(?i)(ci/cd\s+resolution|ci_cd_p0)",
                r"(?i)(playbook|resolution\s+playbook)",
                r"(?i)(test\s+infrastructure|pre-commit\s+resilience|repository\s+renaming)",
                r"(?i)(coverage\s+artifacts|unit\s+test\s+configuration)",
                r"(?i)(network\s+resilience|ci\s+compatibility)",
                r"(?i)(lightrag\+\+|lightrag_plusplus|package\s+naming)",
                r"(?i)(p0\s+resolution|p0\s+issues|critical\s+fixes)",
            ],
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
            for doc_file in Path(".").rglob("*.md"):
                if any(
                    skip in str(doc_file)
                    for skip in [".git", "node_modules", "__pycache__"]
                ):
                    continue

                try:
                    with open(doc_file, encoding="utf-8") as f:
                        content = f.read(5000)  # Read first 5KB

                    for pattern in self.config["terminology_patterns"]:
                        matches = re.findall(pattern, content)
                        if matches:
                            indicators_found += min(len(matches), 2)  # Cap per file
                            print(f"     Found in {doc_file}: {len(matches)} matches")
                            break
                except Exception:
                    continue

        except Exception as e:
            print(f"     Warning: Could not scan documentation: {e}")

        self.indicators["terminology"] = min(indicators_found, 3)
        print(f"   📊 Terminology indicators: {self.indicators['terminology']}")
        return self.indicators["terminology"]

    def detect_bypass_incident_patterns(self) -> int:
        """CRITICAL: Detect specific patterns from the CI_CD_P0_RESOLUTION_PLAYBOOK.md bypass incident"""
        bypass_indicators = 0

        print("   🚨 CRITICAL: Analyzing for bypass incident patterns...")

        try:
            # Pattern 1: Check for CI_CD_P0_RESOLUTION_PLAYBOOK.md
            playbook_file = Path("CI_CD_P0_RESOLUTION_PLAYBOOK.md")
            if playbook_file.exists():
                bypass_indicators += 3  # Weight this heavily
                print(
                    "     🚨 CRITICAL: CI_CD_P0_RESOLUTION_PLAYBOOK.md found - BYPASS INCIDENT DETECTED"
                )

                # Check for specific bypass content
                try:
                    with open(playbook_file, encoding="utf-8") as f:
                        content = f.read()

                    # Look for specific bypass evidence
                    if "Hybrid Approach" in content and "PR groups" in content:
                        bypass_indicators += 2
                        print(
                            "     🚨 EVIDENCE: Hybrid Approach with PR groups confirmed"
                        )

                    if "3 PR groups" in content or "three PR groups" in content.lower():
                        bypass_indicators += 2
                        print("     🚨 EVIDENCE: 3 PR groups implementation confirmed")

                    if (
                        "lightrag-takq" in content
                        or "lightrag-lvd2" in content
                        or "lightrag-rdwu" in content
                    ):
                        bypass_indicators += 1
                        print(
                            "     🚨 EVIDENCE: P0 issue IDs from bypass incident found"
                        )

                except Exception as e:
                    print(f"     Warning: Could not analyze playbook content: {e}")

            # Pattern 2: Check for validation scripts created (bypass incident indicator)
            try:
                validation_script_patterns = [
                    "scripts/validate-ci-fixes.sh",
                    "scripts/validate-precommit-fixes.sh",
                    "scripts/validate-rename-fixes.sh",
                ]

                validation_scripts_found = []
                for script_pattern in validation_script_patterns:
                    script_path = Path(script_pattern)
                    if script_path.exists():
                        validation_scripts_found.append(script_pattern)
                        bypass_indicators += 1
                        print(
                            f"     🚨 EVIDENCE: Bypass validation script found: {script_pattern}"
                        )

                if len(validation_scripts_found) >= 3:
                    bypass_indicators += 3
                    print(
                        "     🚨 CRITICAL: All three bypass validation scripts found - EXACT MATCH"
                    )

            except Exception as e:
                print(f"     Warning: Could not check validation scripts: {e}")

        except Exception as e:
            print(f"     Warning: Bypass incident analysis failed: {e}")

        self.indicators["bypass_incident"] = bypass_indicators
        print(f"   🚨 Bypass incident indicators: {bypass_indicators}")
        return bypass_indicators

    def run_detection(self) -> dict:
        """Run complete multi-phase detection analysis"""
        print("🔍 Running multi-phase detection analysis...")

        # Initialize detection results
        results = {
            "timestamp": datetime.now().isoformat(),
            "indicators": {},
            "total_indicators": 0,
            "threshold": self.threshold,
            "is_multi_phase": False,
            "bypass_incident_detected": False,
        }

        try:
            # Run detection categories
            results["indicators"]["terminology"] = self.detect_terminology_indicators()
            results["indicators"]["bypass_incident"] = (
                self.detect_bypass_incident_patterns()
            )

            # Calculate total indicators
            results["total_indicators"] = sum(results["indicators"].values())

            # CRITICAL: Bypass incident detection overrides normal threshold
            bypass_indicators = results["indicators"].get("bypass_incident", 0)
            if bypass_indicators >= 3:  # High confidence bypass incident
                results["is_multi_phase"] = True
                results["bypass_incident_detected"] = True
                print(
                    "   🚨 CRITICAL: BYPASS INCIDENT PATTERNS DETECTED - AUTO-BLOCKING"
                )
            else:
                # Normal threshold logic for other cases
                results["is_multi_phase"] = (
                    results["total_indicators"] >= self.threshold
                )
                results["bypass_incident_detected"] = False

        except Exception as e:
            print(f"Error during detection: {e}", file=sys.stderr)
            results["error"] = str(e)

        return results


def main():
    """Main entry point"""
    detector = MultiPhaseDetector()
    results = detector.run_detection()

    # Output results
    print(f"\n📊 Detection Results:")
    print(f"   Total Indicators: {results['total_indicators']}")
    print(f"   Threshold: {results['threshold']}")
    print(f"   Multi-Phase Detected: {results['is_multi_phase']}")
    print(f"   Bypass Incident Detected: {results['bypass_incident_detected']}")

    if results["bypass_incident_detected"]:
        print("\n🚨 CRITICAL: BYPASS INCIDENT PATTERNS DETECTED")
        print("This matches the CI_CD_P0_RESOLUTION_PLAYBOOK.md bypass incident")
        print("IMMEDIATE ACTION REQUIRED: Create hand-off documents")
        exit(1)
    elif results["is_multi_phase"]:
        print("\n⚠️  Multi-phase patterns detected")
        print("Hand-off documents may be required")
        exit(1)
    else:
        print("\n✅ Clear - No multi-phase patterns detected")
        exit(0)


if __name__ == "__main__":
    main()
