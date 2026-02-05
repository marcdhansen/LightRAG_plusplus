#!/usr/bin/env python3
"""
Continual Evolution Reflector
Automation/simplicity balance reflection for every mission.
Analyzes and evolves SOP based on real usage patterns and agent feedback.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ContinualEvolutionReflector:
    def __init__(self):
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = os.environ.get(
            "SESSION_ID", f"session_{int(datetime.now().timestamp())}"
        )

    def analyze_automation_effectiveness(self):
        """Analyze how automation helped or hindered this mission"""
        effectiveness = {
            "automation_helpful": 0,
            "automation_hindering": 0,
            "missing_automation": 0,
            "over_automation": 0,
            "specific_feedback": [],
        }

        # Analyze git activity patterns
        try:
            # Check commit patterns (too many small commits vs too few large ones)
            result = subprocess.run(
                ["git", "log", '--since="24 hours ago"', "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                commits = (
                    result.stdout.strip().split("\n") if result.stdout.strip() else []
                )
                if len(commits) > 10:
                    effectiveness["automation_hindering"] += 1
                    effectiveness["specific_feedback"].append(
                        "Too many small commits - consider automated commit grouping"
                    )
                elif len(commits) < 2:
                    effectiveness["missing_automation"] += 1
                    effectiveness["specific_feedback"].append(
                        "Too few commits - consider more frequent automated reminders"
                    )
        except Exception:
            pass

        # Analyze TDD gate interactions
        tdd_log = self.log_dir / "tdd_interactions.log"
        if tdd_log.exists():
            try:
                with open(tdd_log) as f:
                    tdd_data = json.load(f)
                    if tdd_data.get("warnings_ignored", 0) > 3:
                        effectiveness["automation_hindering"] += 1
                        effectiveness["specific_feedback"].append(
                            "TDD warnings frequently ignored - consider less intrusive automation"
                        )
                    if tdd_data.get("helpful_blocks", 0) > 2:
                        effectiveness["automation_helpful"] += 1
                        effectiveness["specific_feedback"].append(
                            "TDD blocks prevented issues - automation working well"
                        )
            except Exception:
                pass

        return effectiveness

    def analyze_simplicity_balance(self):
        """Analyze if SOP complexity was appropriate for this mission"""
        balance = {
            "too_complex": 0,
            "too_simple": 0,
            "just_right": 0,
            "complexity_indicators": [],
            "simplification_opportunities": [],
        }

        # Analyze skill usage patterns
        skill_logs = {
            "mission_briefing": self.log_dir / "mission_briefing.log",
            "devils_advocate": self.log_dir / "devils_advocate.log",
            "planning": self.log_dir / "planning.log",
        }

        used_skills = []
        for skill, log_file in skill_logs.items():
            if log_file.exists():
                try:
                    stat = log_file.stat()
                    age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
                    if age_hours < 6:  # Used this session
                        used_skills.append(skill)
                except Exception:
                    pass

        # Check if too many skills were used
        if len(used_skills) > 4:
            balance["too_complex"] += 1
            balance["complexity_indicators"].append(
                f"Too many skills used ({len(used_skills)}) - consider streamlining"
            )
        elif len(used_skills) < 2:
            balance["too_simple"] += 1
            balance["simplification_opportunities"].append(
                "Very few skills used - may have missed helpful guidance"
            )
        else:
            balance["just_right"] += 1

        # Analyze documentation access patterns
        doc_access_log = self.log_dir / "documentation_access.log"
        if doc_access_log.exists():
            try:
                with open(doc_access_log) as f:
                    doc_data = json.load(f)
                    if (
                        doc_data.get("deep_dives", 0)
                        > doc_data.get("quick_refs", 0) * 3
                    ):
                        balance["too_complex"] += 1
                        balance["complexity_indicators"].append(
                            "Frequent deep documentation dives - SOP may be too complex"
                        )
            except Exception:
                pass

        return balance

    def identify_friction_points(self):
        """Identify specific friction points in this mission"""
        friction_points = {
            "process_friction": [],
            "tool_friction": [],
            "decision_friction": [],
            "automation_friction": [],
        }

        # Analyze git patterns for process friction
        try:
            # Check for rollback patterns
            result = subprocess.run(
                ["git", "log", '--since="24 hours ago"', "--grep=revert", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0 and len(result.stdout.strip()) > 0:
                friction_points["process_friction"].append(
                    "Code rollbacks detected - may indicate insufficient planning"
                )
        except Exception:
            pass

        # Analyze error patterns in logs
        error_log = self.log_dir / "error_patterns.log"
        if error_log.exists():
            try:
                with open(error_log) as f:
                    errors = json.load(f)
                    for error in errors:
                        if "TDD" in error.get("context", ""):
                            friction_points["automation_friction"].append(
                                f"TDD automation issue: {error.get('message', 'Unknown')}"
                            )
                        elif "skill" in error.get("context", ""):
                            friction_points["tool_friction"].append(
                                f"Skill execution issue: {error.get('message', 'Unknown')}"
                            )
            except Exception:
                pass

        return friction_points

    def generate_evolution_questions(self):
        """Generate specific evolution questions for this mission"""
        questions = {
            "automation_questions": [
                "At what point did automation become more complex than helpful?",
                "Which automated checks felt like bureaucratic overhead vs valuable guidance?",
                "Was there too much automation (agents felt constrained) or too little (agents felt lost)?",
                "If you could add/remove one automated check, what would it be?",
                "Did automation help you focus on the task or distract you from it?",
            ],
            "simplicity_questions": [
                "Which SOP steps felt like they had the highest cognitive load?",
                "Were there moments when you didn't know which skill to use next?",
                "Did you find yourself wishing for simpler or more detailed guidance?",
                "At what point did SOP documentation feel overwhelming vs insufficient?",
                "Which conditional rules were unclear or hard to follow?",
            ],
            "process_questions": [
                "What parts of the workflow felt smooth vs clunky?",
                "Were there decision points where automation should have helped but didn't?",
                "Did the conditional skill requirements feel appropriate for your work?",
                "Were there moments when you ignored SOP because it was easier than following it?",
                "What process improvements would have made this mission more efficient?",
            ],
        }

        return questions

    def generate_evolution_recommendations(self):
        """Generate specific recommendations for SOP evolution"""
        effectiveness = self.analyze_automation_effectiveness()
        balance = self.analyze_simplicity_balance()
        friction = self.identify_friction_points()

        recommendations = {
            "automation_adjustments": [],
            "simplicity_improvements": [],
            "process_enhancements": [],
            "priority_changes": [],
        }

        # Automation recommendations
        if effectiveness["automation_hindering"] > effectiveness["automation_helpful"]:
            recommendations["automation_adjustments"].append(
                "REDUCE automation - current level is creating friction"
            )
        elif effectiveness["missing_automation"] > 0:
            recommendations["automation_adjustments"].append(
                "ADD automation - missing helpful automated checks"
            )

        if effectiveness["over_automation"] > 0:
            recommendations["automation_adjustments"].append(
                "SIMPLIFY automation - some checks are over-engineered"
            )

        # Simplicity recommendations
        if balance["too_complex"] > balance["too_simple"]:
            recommendations["simplicity_improvements"].append(
                "STREAMLINE SOP - reduce cognitive load complexity"
            )
        elif balance["too_simple"] > 0:
            recommendations["simplicity_improvements"].append(
                "ENHANCE SOP - add more guidance for complex tasks"
            )

        # Process recommendations
        if friction["process_friction"]:
            recommendations["process_enhancements"].append(
                "IMPROVE workflow automation - reduce process friction points"
            )

        if friction["tool_friction"]:
            recommendations["process_enhancements"].append(
                "FIX tool integration issues - improve skill reliability"
            )

        if friction["decision_friction"]:
            recommendations["process_enhancements"].append(
                "ADD decision support - clarify conditional skill requirements"
            )

        # Priority adjustments based on friction
        if len(friction["process_friction"]) > 2:
            recommendations["priority_changes"].append(
                "ELEVATE process automation to HIGH priority"
            )

        if len(friction["automation_friction"]) > 2:
            recommendations["priority_changes"].append(
                "ELEVATE tool reliability to HIGH priority"
            )

        return recommendations

    def create_evolution_reflection(self):
        """Create comprehensive evolution reflection"""
        questions = self.generate_evolution_questions()
        recommendations = self.generate_evolution_recommendations()

        reflection = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "automation_effectiveness": self.analyze_automation_effectiveness(),
            "simplicity_balance": self.analyze_simplicity_balance(),
            "friction_points": self.identify_friction_points(),
            "evolution_questions": questions,
            "recommendations": recommendations,
            "next_sop_version": self.suggest_sop_version_changes(recommendations),
        }

        return reflection

    def suggest_sop_version_changes(self, recommendations):
        """Suggest specific SOP version changes based on recommendations"""
        version_changes = {
            "major_changes": [],
            "minor_changes": [],
            "patch_changes": [],
            "rationale": [],
        }

        # Determine change levels
        if any(
            "REDUCE" in rec for rec in recommendations.get("automation_adjustments", [])
        ):
            version_changes["major_changes"].append(
                "Reduce automation complexity across SOP"
            )

        if any(
            "STREAMLINE" in rec
            for rec in recommendations.get("simplicity_improvements", [])
        ):
            version_changes["major_changes"].append(
                "Streamline SOP documentation and process"
            )

        if any(
            "ADD" in rec for rec in recommendations.get("automation_adjustments", [])
        ):
            version_changes["minor_changes"].append(
                "Add targeted automation for missing coverage"
            )

        if any(
            "IMPROVE" in rec for rec in recommendations.get("process_enhancements", [])
        ):
            version_changes["patch_changes"].append(
                "Process improvements and bug fixes"
            )

        # Generate rationale
        if version_changes["major_changes"]:
            version_changes["rationale"].append(
                "Major changes needed based on significant friction or complexity issues"
            )

        if version_changes["minor_changes"]:
            version_changes["rationale"].append(
                "Minor improvements to enhance agent experience and effectiveness"
            )

        return version_changes

    def save_evolution_reflection(self, reflection):
        """Save evolution reflection for analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON for analysis
        json_file = self.log_dir / f"evolution_reflection_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(reflection, f, indent=2)

        # Save summary for immediate action
        summary_file = self.log_dir / f"evolution_summary_{timestamp}.md"
        summary_content = self.format_summary_markdown(reflection)
        with open(summary_file, "w") as f:
            f.write(summary_content)

        return json_file, summary_file

    def format_summary_markdown(self, reflection):
        """Format evolution reflection as markdown"""
        md = []

        md.append("# 🔄 Continual Evolution Reflection")
        md.append(f"**Session**: {reflection['session_id']}")
        md.append(f"**Generated**: {reflection['timestamp']}")
        md.append("")

        # Key Findings
        md.append("## 🔍 Key Findings")

        effectiveness = reflection["automation_effectiveness"]
        if effectiveness["automation_helpful"] > effectiveness["automation_hindering"]:
            md.append("✅ **Automation**: Generally helpful and effective")
        elif (
            effectiveness["automation_hindering"] > effectiveness["automation_helpful"]
        ):
            md.append("⚠️ **Automation**: Creating friction, needs adjustment")
        else:
            md.append("📊 **Automation**: Mixed results, needs optimization")

        balance = reflection["simplicity_balance"]
        if balance["just_right"] > 0:
            md.append("✅ **Simplicity**: Well-balanced for this mission")
        elif balance["too_complex"] > balance["too_simple"]:
            md.append("⚠️ **Simplicity**: Too complex, needs streamlining")
        elif balance["too_simple"] > balance["too_complex"]:
            md.append("💡 **Simplicity**: Could be enhanced with more guidance")

        md.append("")

        # Friction Points
        friction = reflection["friction_points"]
        if any(friction.values()):
            md.append("## ⚠️ Friction Points Identified")

            for category, points in friction.items():
                if points:
                    md.append(f"### {category.replace('_', ' ').title()}")
                    for point in points:
                        md.append(f"- {point}")
            md.append("")

        # Top Recommendations
        recommendations = reflection["recommendations"]
        if any(recommendations.values()):
            md.append("## 🎯 Top Recommendations")

            for category, recs in recommendations.items():
                if recs:
                    md.append(f"### {category.replace('_', ' ').title()}")
                    for rec in recs[:2]:  # Show top 2
                        md.append(f"- {rec}")
            md.append("")

        # SOP Evolution Suggestions
        version_changes = reflection["next_sop_version"]
        if any(version_changes.values()):
            md.append("## 🚀 SOP Evolution Suggestions")

            if version_changes["major_changes"]:
                md.append("### Major Changes")
                for change in version_changes["major_changes"]:
                    md.append(f"- **{change}**")

            if version_changes["minor_changes"]:
                md.append("### Minor Changes")
                for change in version_changes["minor_changes"]:
                    md.append(f"- {change}")

            if version_changes["rationale"]:
                md.append("### Rationale")
                for rationale in version_changes["rationale"]:
                    md.append(f"- {rationale}")

        md.append("")
        md.append("---")
        md.append(
            "*This evolution reflection will inform the next cycle of SOP improvements.*"
        )

        return "\n".join(md)

    def run_evolution_reflection(self):
        """Main evolution reflection workflow"""
        print("🔄 Running Continual Evolution Reflection...")
        print("=" * 60)

        # Create reflection
        reflection = self.create_evolution_reflection()

        # Save reflection
        json_file, summary_file = self.save_evolution_reflection(reflection)

        # Display summary
        print(self.format_summary_markdown(reflection))

        print("\n💾 Evolution reflection saved:")
        print(f"   JSON: {json_file}")
        print(f"   Summary: {summary_file}")

        # Update evolution analytics
        self.update_evolution_analytics(reflection)

        return 0

    def update_evolution_analytics(self, reflection):
        """Update long-term evolution analytics"""
        analytics_file = self.log_dir / "evolution_analytics.json"

        analytics = {
            "total_reflections": 0,
            "automation_effectiveness_trend": [],
            "simplicity_balance_trend": [],
            "common_friction_points": {},
            "recommendation_patterns": {},
        }

        # Load existing analytics
        if analytics_file.exists():
            try:
                with open(analytics_file) as f:
                    analytics = json.load(f)
            except Exception:
                pass

        # Update with new reflection
        analytics["total_reflections"] += 1

        # Track trends
        effectiveness = reflection["automation_effectiveness"]
        analytics["automation_effectiveness_trend"].append(
            {
                "timestamp": reflection["timestamp"],
                "helpful_score": effectiveness["automation_helpful"],
                "hindering_score": effectiveness["automation_hindering"],
            }
        )

        balance = reflection["simplicity_balance"]
        analytics["simplicity_balance_trend"].append(
            {
                "timestamp": reflection["timestamp"],
                "too_complex": balance["too_complex"],
                "too_simple": balance["too_simple"],
                "just_right": balance["just_right"],
            }
        )

        # Track common friction points
        friction = reflection["friction_points"]
        for category, points in friction.items():
            if category not in analytics["common_friction_points"]:
                analytics["common_friction_points"][category] = {}

            for point in points:
                point_key = point[:50]  # Truncate for key
                analytics["common_friction_points"][category][point_key] = (
                    analytics["common_friction_points"][category].get(point_key, 0) + 1
                )

        # Save updated analytics
        try:
            with open(analytics_file, "w") as f:
                json.dump(analytics, f, indent=2)
        except Exception:
            pass


def main():
    reflector = ContinualEvolutionReflector()
    exit_code = reflector.run_evolution_reflection()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
