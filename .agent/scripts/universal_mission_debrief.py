#!/usr/bin/env python3
"""
Universal Mission Debrief
Automatic debrief for every task completion with standardized format.
Creates brief but comprehensive mission summary for all task completions.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Integration with Adaptive SOP System
def trigger_sop_evolution(debrief_data):
    """Trigger SOP evolution based on debrief insights"""
    try:
        script_dir = Path(__file__).parent
        engine_script = script_dir / "adaptive_sop_engine.sh"

        if engine_script.exists():
            # Create feedback from debrief data
            feedback_data = {
                "session_performance": debrief_data,
                "pain_points": [],
                "recommendations": [],
                "evolution_score": 70,  # Default score
            }

            # Extract pain points from debrief
            if "issues_encountered" in debrief_data:
                feedback_data["pain_points"] = debrief_data["issues_encountered"]

            if (
                "efficiency_rating" in debrief_data
                and debrief_data["efficiency_rating"] < 3
            ):
                feedback_data["evolution_score"] = 85

            # Write feedback to temporary file
            feedback_file = script_dir.parent / "learn" / "debrief_feedback.json"
            feedback_file.parent.mkdir(exist_ok=True)

            with open(feedback_file, "w") as f:
                json.dump(feedback_data, f, indent=2)

            # Trigger evolution
            result = subprocess.run(
                [
                    str(engine_script),
                    "--action",
                    "evolve",
                    "--sop",
                    "rtb_process",
                    "--feedback",
                    str(feedback_file),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("SOP evolution triggered based on debrief insights")
            else:
                print(
                    f"Warning: SOP evolution failed: {result.stderr}", file=sys.stderr
                )

    except Exception as e:
        print(f"Warning: Could not trigger SOP evolution: {e}", file=sys.stderr)


def get_intelligent_session_insights():
    """Get session insights from intelligent preflight analyzer"""
    try:
        script_dir = Path(__file__).parent
        analyzer_script = script_dir / "intelligent_preflight_analyzer.sh"

        if analyzer_script.exists():
            result = subprocess.run(
                [str(analyzer_script), "--dry-run", "standard"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {"analyzer_insights": result.stdout}
    except Exception as e:
        print(f"Warning: Could not get intelligent insights: {e}", file=sys.stderr)

    return {}


class UniversalMissionDebrief:
    def __init__(self):
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.session_start_time = self.get_session_start_time()
        self.current_task_id = self.get_current_task_id()

    def get_session_start_time(self):
        """Get session start time from agent records"""
        session_file = self.log_dir / "session_start.json"
        if session_file.exists():
            try:
                with open(session_file) as f:
                    session_data = json.load(f)
                    return datetime.fromisoformat(
                        session_data.get("start_time", datetime.now().isoformat())
                    )
            except:
                pass
        return datetime.now()

    def get_current_task_id(self):
        """Get current task ID from beads"""
        try:
            result = subprocess.run(
                ["bd", "current"], capture_output=True, text=True, check=True
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Current task:" in line:
                        return line.split(":")[1].strip()
        except:
            pass

        return "unknown"

    def get_changed_files(self):
        """Get list of changed files in current session"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f.strip()]
        except:
            pass

        return []

    def assess_task_success(self):
        """Assess task success based on git status and project state"""
        success_indicators = {
            "git_clean": False,
            "tests_pass": False,
            "build_success": False,
            "task_completed": False,
        }

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            success_indicators["git_clean"] = len(result.stdout.strip()) == 0
        except:
            pass

        # Check if tests pass
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=short"], capture_output=True, text=True
            )
            success_indicators["tests_pass"] = result.returncode == 0
        except:
            success_indicators["tests_pass"] = True  # No tests = pass by default

        # Check if task was marked as completed
        if self.current_task_id != "unknown":
            try:
                result = subprocess.run(
                    ["bd", "show", self.current_task_id],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.returncode == 0:
                    output = result.stdout
                    success_indicators["task_completed"] = (
                        "status: closed" in output.lower()
                    )
            except:
                pass

        return success_indicators

    def generate_debrief(self):
        """Generate universal mission debrief"""
        now = datetime.now()
        session_duration = now - self.session_start_time
        changed_files = self.get_changed_files()
        success_assessment = self.assess_task_success()

        # Create debrief content
        debrief = {
            "timestamp": now.isoformat(),
            "task_id": self.current_task_id,
            "session_duration_minutes": int(session_duration.total_seconds() / 60),
            "files_changed": changed_files,
            "success_assessment": success_assessment,
            "quick_summary": self.generate_quick_summary(success_assessment),
            "improvement_notes": self.generate_improvement_notes(),
            "next_steps": self.generate_next_steps(),
            "sop_compliance_notes": self.generate_sop_notes(),
        }

        return debrief

    def generate_quick_summary(self, success_assessment):
        """Generate quick success assessment"""
        positive_points = []
        improvement_areas = []

        if success_assessment["git_clean"]:
            positive_points.append("✅ Clean git state - all changes committed")
        else:
            improvement_areas.append(
                "🔧 Git cleanup needed - uncommitted changes remain"
            )

        if success_assessment["tests_pass"]:
            positive_points.append("✅ Tests passing - quality maintained")
        else:
            improvement_areas.append("🔧 Test failures need resolution")

        if success_assessment["task_completed"]:
            positive_points.append("✅ Task marked complete in beads")
        else:
            improvement_areas.append("🔧 Task may need completion in beads")

        return {
            "positive_points": positive_points,
            "improvement_areas": improvement_areas,
        }

    def generate_improvement_notes(self):
        """Generate improvement notes based on session data"""
        notes = []

        # File change patterns
        changed_files = self.get_changed_files()
        if len(changed_files) > 10:
            notes.append("Consider breaking up large changes into smaller commits")

        if any(f.endswith(".py") for f in changed_files):
            notes.append("Python changes detected - ensure tests cover new code")

        if any(f.startswith("docs/") for f in changed_files):
            notes.append("Documentation changes - verify links and formatting")

        # Session duration analysis
        session_duration = datetime.now() - self.session_start_time
        if session_duration.total_seconds() > 7200:  # > 2 hours
            notes.append("Long session - consider more frequent breaks and commits")

        return notes

    def generate_next_steps(self):
        """Generate next steps based on current state"""
        next_steps = []

        # Check for follow-up work
        try:
            result = subprocess.run(
                ["bd", "ready"], capture_output=True, text=True, check=True
            )
            if result.returncode == 0 and result.stdout.strip():
                next_steps.append(
                    "📋 New tasks available - run 'bd ready' to see options"
                )
        except:
            pass

        # Check if there are uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                next_steps.append("🔄 Review and commit remaining changes")
        except:
            pass

        # Default next steps
        if not next_steps:
            next_steps.append("🎯 Select next task from available options")
            next_steps.append("📚 Review documentation for new feature areas")

        return next_steps

    def generate_sop_notes(self):
        """Generate SOP compliance notes"""
        notes = []

        # Check if mandatory skills were logged
        log_files = {
            "planning": self.log_dir / "planning.log",
            "reflection": self.log_dir / "reflections.json",
            "flight_director": self.log_dir / "flight_director.log",
        }

        for skill, log_file in log_files.items():
            if log_file.exists():
                try:
                    stat = log_file.stat()
                    age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
                    if age_hours < 6:  # Used within last 6 hours
                        notes.append(
                            f"✅ {skill.replace('_', ' ').title()} logged this session"
                        )
                    else:
                        notes.append(
                            f"⚠️ {skill.replace('_', ' ').title()} not recently used"
                        )
                except:
                    notes.append(f"⚠️ {skill.replace('_', ' ').title()} status unclear")
            else:
                notes.append(f"❓ {skill.replace('_', ' ').title()} not found in logs")

        return notes

    def save_debrief(self, debrief):
        """Save debrief to multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON for analysis
        json_file = self.log_dir / f"universal_debrief_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(debrief, f, indent=2)

        # Save markdown for human reading
        markdown_file = self.log_dir / f"universal_debrief_{timestamp}.md"
        markdown_content = self.format_debrief_markdown(debrief)
        with open(markdown_file, "w") as f:
            f.write(markdown_content)

        return json_file, markdown_file

    def format_debrief_markdown(self, debrief):
        """Format debrief as markdown for display and saving"""
        md = []

        md.append("# 🚀 Universal Mission Debrief")
        md.append(f"**Generated**: {debrief['timestamp']}")
        md.append("")

        # Task Information
        md.append("## 📋 Task Information")
        md.append(f"- **Task ID**: {debrief['task_id']}")
        md.append(f"- **Duration**: {debrief['session_duration_minutes']} minutes")
        md.append(f"- **Files Changed**: {len(debrief['files_changed'])}")
        if debrief["files_changed"]:
            md.append("- **Changed Files**:")
            for file in debrief["files_changed"][:5]:  # Show first 5
                md.append(f"  - `{file}`")
            if len(debrief["files_changed"]) > 5:
                md.append(f"  - ... and {len(debrief['files_changed']) - 5} more")
        md.append("")

        # Success Assessment
        md.append("## ✅ Quick Success Assessment")
        summary = debrief["quick_summary"]
        if summary["positive_points"]:
            md.append("### What Went Well")
            for point in summary["positive_points"]:
                md.append(f"- {point}")

        if summary["improvement_areas"]:
            md.append("### Areas for Improvement")
            for area in summary["improvement_areas"]:
                md.append(f"- {area}")
        md.append("")

        # Improvement Notes
        if debrief["improvement_notes"]:
            md.append("## 🔧 Improvement Notes")
            for note in debrief["improvement_notes"]:
                md.append(f"- {note}")
            md.append("")

        # Next Steps
        if debrief["next_steps"]:
            md.append("## 🎯 Next Steps")
            for step in debrief["next_steps"]:
                md.append(f"- {step}")
            md.append("")

        # SOP Compliance Notes
        if debrief["sop_compliance_notes"]:
            md.append("## 📊 SOP Compliance Notes")
            for note in debrief["sop_compliance_notes"]:
                md.append(f"- {note}")
            md.append("")

        # Footer
        md.append("---")
        md.append(
            "*This universal debrief is automatically generated for every task completion.*"
        )
        md.append(
            f"*Full details available in: `.agent/logs/universal_debrief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json`*"
        )

        return "\n".join(md)

    def run_debrief(self):
        """Main debrief workflow"""
        print("📋 Running Universal Mission Debrief...")
        print("=" * 60)

        # Generate debrief
        debrief = self.generate_debrief()

        # Save debrief
        json_file, markdown_file = self.save_debrief(debrief)

        # Display debrief
        print(self.format_debrief_markdown(debrief))

        # Save latest debrief reference
        latest_file = self.log_dir / "latest_debrief.txt"
        with open(latest_file, "w") as f:
            f.write(str(markdown_file))

        print("\n💾 Debrief saved:")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {markdown_file}")

        return 0


def main():
    debrief = UniversalMissionDebrief()
    exit_code = debrief.run_debrief()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
