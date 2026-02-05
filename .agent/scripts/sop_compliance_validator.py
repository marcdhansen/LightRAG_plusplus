#!/usr/bin/env python3
"""
SOP Compliance Validator
Blocks RTB completion on SOP violations with user override option.

Exit codes:
0 = Pass (SOP compliance validated)
1 = Block (SOP violations - fix required)
2 = Override (SOP violations overridden with justification)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# Integration with Adaptive SOP Engine
def get_sop_recommendations():
    """Get recommendations from adaptive SOP engine"""
    try:
        script_dir = Path(__file__).parent
        engine_script = script_dir / "adaptive_sop_engine.sh"

        if engine_script.exists():
            result = subprocess.run(
                [str(engine_script), "--action", "analyze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
    except Exception as e:
        print(f"Warning: Could not get SOP recommendations: {e}", file=sys.stderr)

    return {"recommendations": [], "metrics": {}}


def record_sop_evaluation(evaluation_data):
    """Record SOP evaluation for adaptive learning"""
    try:
        script_dir = Path(__file__).parent
        learn_dir = script_dir.parent / "learn"
        learn_dir.mkdir(exist_ok=True)

        evaluation_file = learn_dir / "sop_evaluations.jsonl"

        with open(evaluation_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "evaluation": evaluation_data,
                    }
                )
                + "\n"
            )
    except Exception as e:
        print(f"Warning: Could not record SOP evaluation: {e}", file=sys.stderr)


class SOPComplianceValidator:
    def __init__(self):
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.violations = []
        self.warnings = []

    def validate_all_sop_rules(self):
        """Comprehensive SOP rule validation"""
        compliance_results = {
            "mandatory_skills": self.check_mandatory_skills(),
            "conditional_rules": self.check_conditional_rules(),
            "workflow_integrity": self.check_workflow_integrity(),
            "timestamp": datetime.now().isoformat(),
        }

        # Determine if there are blocking violations
        has_blockers = (
            not compliance_results["mandatory_skills"].get("all_passed", False)
            or compliance_results["conditional_rules"].get("critical_violations", 0) > 0
        )

        if has_blockers:
            compliance_results["status"] = "blocked"
        else:
            compliance_results["status"] = "passed"

        return compliance_results

    def check_mandatory_skills(self):
        """Verify all mandatory skills were invoked"""
        mandatory_checks = {}

        # Check planning was used (development tasks)
        mandatory_checks["planning_used"] = self.check_planning_used()

        # Check return-to-base was initiated
        mandatory_checks["rtb_initiated"] = self.check_rtb_initiated()

        # Check reflection was used (look for recent reflection)
        mandatory_checks["reflect_used"] = self.check_reflect_used()

        # Check FlightDirector validations
        mandatory_checks["flight_director_used"] = self.check_flight_director_used()

        # Determine overall pass status
        mandatory_checks["all_passed"] = all(
            [
                mandatory_checks["planning_used"],
                mandatory_checks["rtb_initiated"],
                mandatory_checks["reflect_used"],
            ]
        )

        return mandatory_checks

    def check_conditional_rules(self):
        """Verify if-then rules were followed"""
        conditional_results = {}

        # Check if mission-briefing was required and used
        conditional_results["mission_briefing_required"] = (
            self.should_have_used_briefing()
        )
        conditional_results["mission_briefing_used"] = (
            self.check_briefing_used()
            if conditional_results["mission_briefing_required"]
            else True
        )

        # Check if devils-advocate was required and used
        conditional_results["devils_advocate_required"] = (
            self.should_have_used_devils_advocate()
        )
        conditional_results["devils_advocate_used"] = (
            self.check_devils_advocate_used()
            if conditional_results["devils_advocate_required"]
            else True
        )

        # Count critical violations
        critical_violations = 0
        if (
            conditional_results["mission_briefing_required"]
            and not conditional_results["mission_briefing_used"]
        ):
            critical_violations += 1
            self.violations.append(
                "Mission-briefing required but not used (new session or context switch)"
            )

        if (
            conditional_results["devils_advocate_required"]
            and not conditional_results["devils_advocate_used"]
        ):
            critical_violations += 1
            self.violations.append(
                "Devils-advocate required but not used (core changes or high-risk decisions)"
            )

        conditional_results["critical_violations"] = critical_violations

        return conditional_results

    def check_workflow_integrity(self):
        """Check workflow and project integrity"""
        integrity_checks = {}

        # Git status
        integrity_checks["git_clean"] = self.check_git_status_clean()

        # Beads connectivity
        integrity_checks["beads_ready"] = self.check_beads_ready()

        # Documentation integrity
        integrity_checks["no_duplicate_docs"] = self.check_no_duplicate_docs()

        return integrity_checks

    def should_have_used_briefing(self):
        """Check if mission-briefing should have been used"""
        # Check if new session (no git activity in 24 hours)
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%at"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return True  # No git history = new session

            last_commit_time = int(result.stdout.strip())
            current_time = int(time.time())
            hours_since_commit = (current_time - last_commit_time) / 3600

            if hours_since_commit > 24:
                return True
        except Exception:
            return True  # Error = assume new session

        # Check for context switch (different working directory)
        current_dir = Path.cwd().name
        session_log = self.log_dir / "session_context.json"

        if session_log.exists():
            with open(session_log) as f:
                session_data = json.load(f)
                if session_data.get("last_directory") != current_dir:
                    return True

        return False

    def should_have_used_devils_advocate(self):
        """Check if devils-advocate should have been used"""
        try:
            # Get changed files in current session
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.returncode != 0:
                return False

            changed_files = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            # Check for core changes
            core_files = [
                f
                for f in changed_files
                if any(
                    pattern in f
                    for pattern in [
                        "lightrag/core.py",
                        "lightrag/operate.py",
                        "database/schema",
                        "api/",
                    ]
                )
            ]

            if core_files:
                self.violations.append("Core changes detected without devils-advocate")
                return True

        except Exception:
            pass

        return False

    def check_planning_used(self):
        """Check if planning was used for development tasks"""
        # Look for planning artifacts or recent planning usage
        planning_indicators = [".agent/logs/planning_", "PLAN_APPROVAL", "task.md"]

        for indicator in planning_indicators:
            if (Path.cwd() / indicator).exists() or list(Path.cwd().rglob(indicator)):
                return True

        # Check if this is a development task (vs documentation, etc.)
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                changed_files = result.stdout.strip().split("\n")
                dev_files = [
                    f for f in changed_files if f.endswith(".py") or f.endswith(".js")
                ]
                return len(dev_files) > 0
        except Exception:
            pass

        return False

    def check_rtb_initiated(self):
        """Check if RTB process was initiated (always true when this script runs)"""
        return True  # This script only runs during RTB initiation

    def check_reflect_used(self):
        """Check if reflection was used in current session"""
        reflection_log = self.log_dir / "reflections.json"
        if reflection_log.exists():
            try:
                with open(reflection_log) as f:
                    reflections = json.load(f)
                    if reflections:
                        last_reflection = max(
                            reflections, key=lambda x: x.get("timestamp", 0)
                        )
                        last_time = last_reflection.get("timestamp", 0)
                        current_time = time.time()
                        # Check if reflection was within last 4 hours
                        return (current_time - last_time) < 14400
            except Exception:
                pass

        return False

    def check_flight_director_used(self):
        """Check if FlightDirector validations were performed"""
        flight_log = self.log_dir / "flight_director.log"
        if flight_log.exists():
            try:
                stat = flight_log.stat()
                # Check if modified within last session
                current_time = time.time()
                file_time = stat.st_mtime
                return (current_time - file_time) < 21600  # 6 hours
            except Exception:
                pass

        return False

    def check_briefing_used(self):
        """Check if mission-briefing was used"""
        briefing_log = self.log_dir / "mission_briefing.log"
        if briefing_log.exists():
            try:
                stat = briefing_log.stat()
                current_time = time.time()
                file_time = stat.st_mtime
                return (current_time - file_time) < 14400  # 4 hours
            except Exception:
                pass

        return False

    def check_devils_advocate_used(self):
        """Check if devils-advocate was used"""
        da_log = self.log_dir / "devils_advocate.log"
        if da_log.exists():
            try:
                stat = da_log.stat()
                current_time = time.time()
                file_time = stat.st_mtime
                return (current_time - file_time) < 14400  # 4 hours
            except Exception:
                pass

        return False

    def check_git_status_clean(self):
        """Check if git status is clean"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            return len(result.stdout.strip()) == 0
        except Exception:
            return False

    def check_beads_ready(self):
        """Check if beads system is ready"""
        try:
            result = subprocess.run(
                ["bd", "ready"], capture_output=True, text=True, check=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_no_duplicate_docs(self):
        """Check for duplicate markdown files"""
        try:
            result = subprocess.run(
                [".agent/scripts/verify_markdown_duplicates.sh"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return True  # Assume no duplicates if script fails

    def handle_user_override(self):
        """Handle user override with justification"""
        print("\n" + "=" * 60)
        print("⚠️  SOP VIOLATIONS DETECTED - RTB BLOCKED")
        print("=" * 60)

        print("\n📋 Violations detected:")
        for violation in self.violations:
            print(f"  ❌ {violation}")

        print("\n🎯 Options:")
        print("  1. Fix violations and retry RTB")
        print("  2. Override with justification (requires explanation)")

        while True:
            try:
                choice = input("\nChoose option [1/2]: ").strip()
                if choice in ["1", "2"]:
                    break
                print("Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n❌ RTB cancelled")
                return {"status": "cancelled", "rtb_allowed": False}

        if choice == "1":
            return {"status": "blocked", "rtb_allowed": False}

        elif choice == "2":
            print("\n📝 Override requires justification:")
            while True:
                try:
                    justification = input(
                        "Justification for override (20+ chars): "
                    ).strip()
                    if len(justification) < 20:
                        print(
                            "❌ Justification too brief - please explain why override is needed"
                        )
                        continue
                    break
                except KeyboardInterrupt:
                    print("\n❌ RTB cancelled")
                    return {"status": "cancelled", "rtb_allowed": False}

            # Log override
            self.log_override(self.violations, justification)

            print("\n✅ Override logged - RTB will proceed")
            return {"status": "overridden", "rtb_allowed": True}

    def log_override(self, violations, justification):
        """Log override for future analysis"""
        override_log = self.log_dir / "sop_overrides.json"

        override_entry = {
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "justification": justification,
            "session_id": os.environ.get("SESSION_ID", "unknown"),
        }

        overrides = []
        if override_log.exists():
            try:
                with open(override_log) as f:
                    overrides = json.load(f)
            except Exception:
                pass

        overrides.append(override_entry)

        try:
            with open(override_log, "w") as f:
                json.dump(overrides, f, indent=2)
        except Exception:
            pass  # Don't fail RTB if logging fails

    def run_validation(self):
        """Main validation workflow"""
        print("🔍 Validating complete SOP compliance...")

        # Run all checks
        compliance_results = self.validate_all_sop_rules()

        # Save results for analysis
        results_file = self.log_dir / f"sop_validation_{int(time.time())}.json"
        try:
            with open(results_file, "w") as f:
                json.dump(compliance_results, f, indent=2)
        except Exception:
            pass

        if compliance_results["status"] == "passed":
            print("✅ SOP compliance validated - RTB proceeding")
            return 0

        # Handle violations with override option
        override_result = self.handle_user_override()

        if override_result["status"] == "blocked":
            print("\n❌ RTB BLOCKED - Fix violations before proceeding")
            print("💡 Run recommended skills and retry RTB")
            return 1
        elif override_result["status"] == "overridden":
            print("\n⚠️ SOP violations overridden with justification")
            return 2
        elif override_result["status"] == "cancelled":
            return 1
        else:
            return 1


def main():
    validator = SOPComplianceValidator()
    exit_code = validator.run_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
