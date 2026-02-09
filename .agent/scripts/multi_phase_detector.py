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
        self.detection_log = []
        self.threshold = 3
        self.detection_log = []
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

    def detect_git_patterns(self) -> int:
        """Analyze git history for implementation trail patterns"""
        git_indicators = 0

        print("   🔍 Analyzing git implementation patterns...")

        try:
            # Check for multi-branch activity
            branch_result = subprocess.run(
                ["git", "branch", "-a"], capture_output=True, text=True, check=True
            )
            branches = len([b for b in branch_result.stdout.split("\n") if b.strip()])
            if branches > 3:
                git_indicators += 1
                print(f"     Multiple branches detected: {branches}")

            # Check for recent multi-commits
            commit_result = subprocess.run(
                ["git", "log", "--oneline", "--since='1 week ago'"],
                capture_output=True,
                text=True,
                check=True,
            )
            recent_commits = len(
                [c for c in commit_result.stdout.split("\n") if c.strip()]
            )
            if recent_commits > 10:
                git_indicators += 1
                print(f"     High commit activity: {recent_commits} commits in 1 week")

            # Check for merge patterns
            merge_result = subprocess.run(
                ["git", "log", "--merges", "--oneline", "-10"],
                capture_output=True,
                text=True,
                check=True,
            )
            merge_commits = len(
                [m for m in merge_result.stdout.split("\n") if m.strip()]
            )
            if merge_commits > 2:
                git_indicators += 1
                print(f"     Multiple merge commits: {merge_commits}")

            # Check for phase-related commit messages
            phase_commit_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--grep=phase",
                    "--grep=multi-phase",
                    "--grep=hybrid",
                    "--oneline",
                    "-10",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            phase_commits = len(
                [p for p in phase_commit_result.stdout.split("\n") if p.strip()]
            )
            if phase_commits > 3:
                git_indicators += 1
                print(f"     Phase-related commits: {phase_commits}")

        except Exception as e:
            print(f"     Warning: Git analysis failed: {e}")

        self.indicators["git_patterns"] = min(git_indicators, 3)
        print(f"   📊 Git pattern indicators: {self.indicators['git_patterns']}")
        return self.indicators["git_patterns"]

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
            results["indicators"]["git_patterns"] = self.detect_git_patterns()
            results["indicators"]["bypass_incident"] = (
                self.detect_bypass_incident_patterns()
            )

            # Calculate weighted score
            weights = self.config.get(
                "indicator_weights",
                {"terminology": 1, "git_patterns": 1.5, "bypass_incident": 3},
            )

            weighted_score = 0
            for indicator_type, count in results["indicators"].items():
                weight = weights.get(indicator_type, 1)
                weighted_score += count * weight
                self.detection_log.append(
                    {
                        "type": indicator_type,
                        "count": count,
                        "weight": weight,
                        "contribution": count * weight,
                    }
                )

            results["total_indicators"] = sum(results["indicators"].values())
            results["weighted_score"] = round(weighted_score, 2)
            results["detection_log"] = self.detection_log

            # CRITICAL: Bypass incident detection overrides normal threshold
            bypass_indicators = results["indicators"].get("bypass_incident", 0)
            if bypass_indicators >= 3:  # High confidence bypass incident
                results["is_multi_phase"] = True
                results["bypass_incident_detected"] = True
                results["risk_level"] = "CRITICAL"
                print(
                    "   🚨 CRITICAL: BYPASS INCIDENT PATTERNS DETECTED - AUTO-BLOCKING"
                )
            elif weighted_score >= self.threshold * 2:  # Weighted threshold
                results["is_multi_phase"] = True
                results["bypass_incident_detected"] = False
                results["risk_level"] = "HIGH"
                print(
                    f"   ⚠️  MULTI-PHASE PATTERNS DETECTED (Score: {weighted_score:.1f})"
                )
            else:
                results["is_multi_phase"] = False
                results["bypass_incident_detected"] = False
                results["risk_level"] = "LOW"

        except Exception as e:
            print(f"Error during detection: {e}", file=sys.stderr)
            results["error"] = str(e)

        return results


def main():
    """Main entry point"""
    detector = MultiPhaseDetector()
    results = detector.run_detection()

    # Output results
    print(f"\n📊 Enhanced Detection Results:")
    print(f"   Total Indicators: {results['total_indicators']}")
    print(f"   Weighted Score: {results.get('weighted_score', 0)}")
    print(f"   Threshold: {results['threshold']}")
    print(f"   Risk Level: {results.get('risk_level', 'UNKNOWN')}")
    print(f"   Multi-Phase Detected: {results['is_multi_phase']}")
    print(f"   Bypass Incident Detected: {results['bypass_incident_detected']}")

    # Show detailed breakdown
    print(f"\n📋 Indicator Breakdown:")
    detection_log = results.get("detection_log", [])
    for indicator_type, count in results["indicators"].items():
        weight_info = next(
            (w for w in detection_log if w["type"] == indicator_type), {}
        )
        contribution = weight_info.get("contribution", 0)
        print(
            f"   {indicator_type.replace('_', ' ').title()}: {count} (Contribution: {contribution:.1f})"
        )

    if results["bypass_incident_detected"]:
        print("\n🚨 CRITICAL: BYPASS INCIDENT PATTERNS DETECTED")
        print("This matches the CI_CD_P0_RESOLUTION_PLAYBOOK.md bypass incident")
        print("IMMEDIATE ACTION REQUIRED: Create hand-off documents")
        print("WORK BLOCKED until compliance requirements met")
        exit(1)
    elif results["is_multi_phase"]:
        print("\n⚠️  Multi-phase patterns detected")
        print("Hand-off documents are required before proceeding")
        print("Follow Multi-Phase Hand-off Protocol")
        exit(1)
    else:
        print("\n✅ Clear - No multi-phase patterns detected")
        print("Work may proceed without hand-off requirements")
        exit(0)


if __name__ == "__main__":
    main()
