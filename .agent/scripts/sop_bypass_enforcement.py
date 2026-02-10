#!/usr/bin/env python3
"""
SOP Bypass Vulnerability Patches - Protocol Compliance Enforcement Gate
Prevents manual bypass of mandatory hand-off protocols and SOP violations

Exit codes:
0 = Clear (no bypass attempts detected)
1 = Block (bypass attempt detected - work blocked)
2 = Warning (potential bypass patterns detected)
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SOPBypassPatch:
    """
    Security enforcement system for SOP compliance
    Detects and blocks bypass attempts with mandatory protocol enforcement
    """

    def __init__(self, config_path: str | None = None):
        self.violations = []
        self.enforcement_log = []
        self.config = self.load_config(config_path)
        self.session_start = datetime.now()

    def load_config(self, config_path: str | None) -> dict:
        """Load enforcement configuration"""
        default_config = {
            "enforcement_mode": "strict",  # strict, warning, monitor
            "bypass_patterns": [
                # Direct bypass attempts
                r"(?i)(skip.*handoff|bypass.*protocol|ignore.*sop)",
                r"(?i)(manual.*override|force.*continue|proceed.*without)",
                # Workaround attempts
                r"(?i)(workaround.*handoff|alternative.*to.*handoff|skip.*phase)",
                r"(?i)(temporary.*bypass|emergency.*skip|urgent.*override)",
                # Documentation manipulation
                r"(?i)(fake.*handoff|template.*handoff|placeholder.*handoff)",
                r"(?i)(minimal.*handoff|incomplete.*handoff|partial.*handoff)",
                # Process violations
                r"(?i)(merge.*without.*review|push.*without.*approval|commit.*without.*test)",
                r"(?i)(disable.*check|ignore.*warning|suppress.*error)",
                # Critical security violations
                r"(?i)(delete.*log|clear.*history|hide.*evidence|cover.*track)",
                r"(?i)(circumvent.*security|bypass.*enforcement|evade.*detection)",
            ],
            "mandatory_handoff_sections": [
                "Executive Summary",
                "Technical Context",
                "Knowledge Transfer",
                "Navigation & Onboarding",
                "Quality & Validation",
            ],
            "handoff_quality_thresholds": {
                "min_executive_summary_words": 300,
                "min_technical_context_sections": 5,
                "min_knowledge_transfer_sections": 5,
                "min_navigation_sections": 5,
                "required_subsections": 15,
            },
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config: {e}", file=sys.stderr)

        return default_config

    def detect_bypass_attempts(self) -> int:
        """Scan for bypass attempt patterns in recent activity"""
        bypass_count = 0

        print("   🔍 Scanning for bypass attempt patterns...")

        try:
            # Check recent commits for bypass patterns
            commit_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--grep=bypass",
                    "--grep=skip",
                    "--grep=override",
                    "-10",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            bypass_commits = commit_result.stdout.strip().split("\n")
            for commit in bypass_commits:
                if commit.strip():
                    bypass_count += 1
                    self.violations.append(
                        {
                            "type": "commit_bypass",
                            "evidence": commit,
                            "timestamp": datetime.now().isoformat(),
                            "severity": "high",
                        }
                    )
                    print(f"     🚨 Bypass pattern in commit: {commit[:50]}...")

        except Exception as e:
            print(f"     Warning: Could not scan commits: {e}")

        # Check for suspicious file modifications
        try:
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            modified_files = status_result.stdout.strip().split("\n")
            for file_line in modified_files:
                if file_line.strip():
                    file_path = file_line[3:]  # Remove status prefix

                    # Check for suspicious patterns in modified files
                    if self._check_file_for_bypass_patterns(file_path):
                        bypass_count += 1
                        self.violations.append(
                            {
                                "type": "file_bypass",
                                "evidence": f"Suspicious patterns in {file_path}",
                                "timestamp": datetime.now().isoformat(),
                                "severity": "medium",
                            }
                        )
                        print(f"     ⚠️  Suspicious patterns in: {file_path}")

        except Exception as e:
            print(f"     Warning: Could not check file status: {e}")

        print(f"   📊 Bypass attempts detected: {bypass_count}")
        return bypass_count

    def _check_file_for_bypass_patterns(self, file_path: str) -> bool:
        """Check if file contains bypass patterns"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read(2000)  # Read first 2KB

            for pattern in self.config["bypass_patterns"]:
                if re.search(pattern, content):
                    return True
        except Exception:
            pass
        return False

    def enforce_mandatory_handoff_verification(self) -> dict:
        """Enforce mandatory hand-off document verification"""
        handoff_status = {"verified": False, "issues": [], "quality_score": 0}

        print("   🔍 Enforcing mandatory hand-off verification...")

        # Check if hand-off documents exist
        handoff_dir = Path(".agent/handoffs")
        if not handoff_dir.exists():
            handoff_status["issues"].append("Hand-off directory does not exist")
            self.violations.append(
                {
                    "type": "missing_handoff_dir",
                    "evidence": "No .agent/handoffs directory found",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "critical",
                }
            )
            return handoff_status

        # Find hand-off documents
        handoff_files = list(handoff_dir.rglob("*-handoff.md"))
        if not handoff_files:
            handoff_status["issues"].append("No hand-off documents found")
            self.violations.append(
                {
                    "type": "missing_handoff_docs",
                    "evidence": "No *-handoff.md files found",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "critical",
                }
            )
            return handoff_status

        # Verify each hand-off document
        for handoff_file in handoff_files:
            doc_issues = self._verify_handoff_document(handoff_file)
            handoff_status["issues"].extend(doc_issues)

        # Calculate quality score
        total_issues = len(handoff_status["issues"])
        handoff_status["quality_score"] = max(0, 100 - (total_issues * 5))
        handoff_status["verified"] = total_issues == 0

        print(
            f"   📊 Hand-off verification: {len(handoff_files)} docs, {total_issues} issues"
        )
        return handoff_status

    def _verify_handoff_document(self, handoff_file: Path) -> list:
        """Verify individual hand-off document quality"""
        issues = []
        thresholds = self.config["handoff_quality_thresholds"]

        try:
            with open(handoff_file, encoding="utf-8") as f:
                content = f.read()

            # Check required sections
            for section in self.config["mandatory_handoff_sections"]:
                if not re.search(f"^#+ {section}", content, re.MULTILINE):
                    issues.append(f"Missing required section: {section}")

            # Check executive summary length
            exec_summary_match = re.search(
                r"^#+ Executive Summary$(.+?)^#+", content, re.MULTILINE | re.DOTALL
            )
            if exec_summary_match:
                word_count = len(exec_summary_match.group(1).split())
                if word_count < thresholds["min_executive_summary_words"]:
                    issues.append(
                        f"Executive Summary too short: {word_count} words (min: {thresholds['min_executive_summary_words']})"
                    )

            # Check for placeholder content
            placeholder_patterns = [
                r"(?i)(todo|tbd|placeholder|coming soon|fill this in)",
                r"(?i)(example|template|sample|dummy content)",
            ]

            for pattern in placeholder_patterns:
                if re.search(pattern, content):
                    issues.append(f"Contains placeholder content: {pattern}")
                    break

        except Exception as e:
            issues.append(f"Could not read hand-off file: {e}")

        return issues

    def create_audit_trail(self, results: dict) -> str:
        """Create comprehensive audit trail for enforcement actions"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_duration": str(datetime.now() - self.session_start),
            "enforcement_mode": self.config["enforcement_mode"],
            "results": results,
            "violations": self.violations,
            "violations_count": len(self.violations),
            "risk_assessment": self._assess_risk_level(),
        }

        # Store audit trail
        audit_dir = Path(".agent/logs/security_audit")
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_file = (
            audit_dir
            / f"sop_enforcement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            with open(audit_file, "w") as f:
                json.dump(audit_entry, f, indent=2)
            print(f"   📝 Audit trail created: {audit_file}")
            return str(audit_file)
        except Exception as e:
            print(f"     Warning: Could not create audit trail: {e}")
            return ""

    def _assess_risk_level(self) -> str:
        """Assess overall risk level based on violations"""
        if not self.violations:
            return "LOW"

        critical_count = sum(
            1 for v in self.violations if v.get("severity") == "critical"
        )
        high_count = sum(1 for v in self.violations if v.get("severity") == "high")

        if critical_count > 0:
            return "CRITICAL"
        elif high_count > 2:
            return "HIGH"
        elif len(self.violations) > 5:
            return "MEDIUM"
        else:
            return "LOW"

    def run_enforcement(self) -> dict:
        """Run complete SOP bypass enforcement check"""
        print("🛡️ Running SOP Bypass Vulnerability Enforcement...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "bypass_attempts": 0,
            "handoff_verified": False,
            "violations_detected": False,
            "risk_level": "LOW",
            "enforcement_action": "ALLOW",
            "audit_trail": "",
        }

        try:
            # Run enforcement checks
            results["bypass_attempts"] = self.detect_bypass_attempts()
            handoff_status = self.enforce_mandatory_handoff_verification()
            results["handoff_verified"] = handoff_status["verified"]
            results["handoff_quality_score"] = handoff_status["quality_score"]

            # Determine enforcement action
            violations_count = len(self.violations)
            results["violations_detected"] = violations_count > 0
            results["violations_count"] = violations_count
            results["risk_level"] = self._assess_risk_level()

            # Apply enforcement logic
            if self.config["enforcement_mode"] == "strict":
                if violations_count > 0 or not results["handoff_verified"]:
                    results["enforcement_action"] = "BLOCK"
                else:
                    results["enforcement_action"] = "ALLOW"
            elif self.config["enforcement_mode"] == "warning":
                if violations_count > 0:
                    results["enforcement_action"] = "WARN"
                else:
                    results["enforcement_action"] = "ALLOW"
            else:  # monitor mode
                results["enforcement_action"] = "MONITOR"

            # Create audit trail
            results["audit_trail"] = self.create_audit_trail(results)

        except Exception as e:
            print(f"Error during enforcement: {e}", file=sys.stderr)
            results["error"] = str(e)
            results["enforcement_action"] = "ERROR"

        return results


def main():
    """Main entry point"""
    enforcer = SOPBypassPatch()
    results = enforcer.run_enforcement()

    # Output results
    print("\n🛡️ SOP Bypass Enforcement Results:")
    print(f"   Bypass Attempts: {results['bypass_attempts']}")
    print(f"   Hand-off Verified: {results['handoff_verified']}")
    print(f"   Violations Detected: {results['violations_detected']}")
    print(f"   Risk Level: {results['risk_level']}")
    print(f"   Enforcement Action: {results['enforcement_action']}")

    if results.get("violations_count", 0) > 0:
        print("\n🚨 Security Violations Found:")
        for violation in enforcer.violations:
            severity_icon = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "🔸",
                "low": "🔹",
            }.get(violation.get("severity", "low"), "🔹")
            print(
                f"   {severity_icon} {violation.get('type', 'unknown')}: {violation.get('evidence', 'no evidence')}"
            )

    if results["enforcement_action"] == "BLOCK":
        print("\n🚫 WORK BLOCKED - Security violations detected")
        print("   Fix all violations before proceeding")
        print("   Follow mandatory SOP protocols")
        exit(1)
    elif results["enforcement_action"] == "WARN":
        print("\n⚠️  WARNING - Security issues detected")
        print("   Address violations before continuing")
        exit(2)
    elif results["enforcement_action"] == "ERROR":
        print("\n❌ ERROR - Enforcement system failure")
        exit(2)
    else:
        print("\n✅ WORK ALLOWED - No security violations detected")
        exit(0)


if __name__ == "__main__":
    main()
