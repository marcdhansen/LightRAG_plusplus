#!/usr/bin/env python3
"""
Conditional Skill Detector
Context-aware if-then rule checking for skill requirements.
Automatically detects which skills should be used based on work context.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


class ConditionalSkillDetector:
    def __init__(self):
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.current_dir = Path.cwd()

    def check_session_context(self):
        """Check if this is a new session or context switch"""
        context = {
            "is_new_session": False,
            "is_context_switch": False,
            "hours_since_last_commit": 0,
            "last_directory": None,
            "current_directory": self.current_dir.name,
        }

        # Check git activity
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%at"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                last_commit_time = int(result.stdout.strip())
                current_time = int(datetime.now().timestamp())
                context["hours_since_last_commit"] = (
                    current_time - last_commit_time
                ) / 3600

                # New session if no commits in 24 hours
                context["is_new_session"] = context["hours_since_last_commit"] > 24
            else:
                context["is_new_session"] = True  # No git history
        except:
            context["is_new_session"] = True

        # Check for context switch (different directory)
        session_file = self.log_dir / "session_context.json"
        if session_file.exists():
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                    context["last_directory"] = session_data.get("last_directory")
                    context["is_context_switch"] = (
                        context["last_directory"] != context["current_directory"]
                    )
            except:
                pass

        # Save current session context
        self.save_session_context(context)

        return context

    def check_work_complexity(self):
        """Analyze work complexity based on changes and task type"""
        complexity = {
            "level": "low",
            "file_count": 0,
            "core_changes": False,
            "api_changes": False,
            "database_changes": False,
            "test_changes": False,
            "doc_changes": False,
            "high_risk_patterns": [],
        }

        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.returncode == 0:
                changed_files = [
                    f for f in result.stdout.strip().split("\n") if f.strip()
                ]
                complexity["file_count"] = len(changed_files)

                # Analyze file types and patterns
                for file in changed_files:
                    # Core file changes
                    if any(
                        pattern in file
                        for pattern in [
                            "lightrag/core.py",
                            "lightrag/operate.py",
                            "lightrag/__init__.py",
                        ]
                    ):
                        complexity["core_changes"] = True
                        complexity["high_risk_patterns"].append(
                            f"Core module modification: {file}"
                        )

                    # API changes
                    if any(
                        pattern in file for pattern in ["api/", "endpoint", "route"]
                    ):
                        complexity["api_changes"] = True
                        complexity["high_risk_patterns"].append(
                            f"API interface change: {file}"
                        )

                    # Database changes
                    if any(
                        pattern in file
                        for pattern in ["database/", "schema", "migration", "sql"]
                    ):
                        complexity["database_changes"] = True
                        complexity["high_risk_patterns"].append(
                            f"Database modification: {file}"
                        )

                    # Test files
                    if file.startswith("tests/") or file.endswith("_test.py"):
                        complexity["test_changes"] = True

                    # Documentation
                    if file.endswith(".md") or file.startswith("docs/"):
                        complexity["doc_changes"] = True

                # Determine complexity level
                if complexity["core_changes"] or complexity["database_changes"]:
                    complexity["level"] = "high"
                elif complexity["api_changes"] or complexity["file_count"] > 10:
                    complexity["level"] = "medium"
                elif complexity["file_count"] > 5:
                    complexity["level"] = "medium"
                else:
                    complexity["level"] = "low"

        except:
            pass

        return complexity

    def check_task_type(self):
        """Determine task type based on changed files and patterns"""
        task_type = {
            "type": "unknown",
            "categories": [],
            "requires_planning": False,
            "requires_devils_advocate": False,
            "requires_mission_briefing": False,
            "requires_testing": False,
        }

        complexity = self.check_work_complexity()

        # Determine task type
        if complexity["core_changes"] or complexity["api_changes"]:
            task_type["type"] = "feature_development"
            task_type["categories"].append("development")
            task_type["requires_planning"] = True
            task_type["requires_devils_advocate"] = True
            task_type["requires_testing"] = True

        elif complexity["database_changes"]:
            task_type["type"] = "database_change"
            task_type["categories"].append("database")
            task_type["requires_planning"] = True
            task_type["requires_devils_advocate"] = True
            task_type["requires_testing"] = True

        elif complexity["test_changes"] and not complexity["core_changes"]:
            task_type["type"] = "test_enhancement"
            task_type["categories"].append("testing")

        elif complexity["doc_changes"] and not complexity["core_changes"]:
            task_type["type"] = "documentation"
            task_type["categories"].append("documentation")

        elif complexity["file_count"] > 0:
            task_type["type"] = "bug_fix"
            task_type["categories"].append("maintenance")
            task_type["requires_testing"] = True

        return task_type

    def generate_skill_recommendations(self):
        """Generate skill recommendations based on context and complexity"""
        context = self.check_session_context()
        complexity = self.check_work_complexity()
        task_type = self.check_task_type()

        recommendations = {
            "mandatory_skills": [],
            "recommended_skills": [],
            "optional_skills": [],
            "conditional_requirements": [],
            "justifications": {},
        }

        # Always mandatory skills
        recommendations["mandatory_skills"] = [
            "planning (auto-prompted)",
            "return-to-base",
            "reflect",
            "mission-debriefing",
        ]

        # Mission-briefing requirements
        if context["is_new_session"]:
            recommendations["conditional_requirements"].append(
                {
                    "skill": "mission-briefing",
                    "reason": "new_session",
                    "justification": "New session detected - need current context and protocol highlights",
                }
            )
            recommendations["recommended_skills"].append("mission-briefing")
            recommendations["justifications"]["mission-briefing"] = (
                "New session - get current status and protocol highlights"
            )

        elif context["is_context_switch"]:
            recommendations["conditional_requirements"].append(
                {
                    "skill": "mission-briefing",
                    "reason": "context_switch",
                    "justification": "Context switch detected - need new area context",
                }
            )
            recommendations["recommended_skills"].append("mission-briefing")
            recommendations["justifications"]["mission-briefing"] = (
                "Context switch - get updated context for new work area"
            )

        # Devils-advocate requirements
        if complexity["level"] in ["high", "medium"] or complexity["core_changes"]:
            recommendations["conditional_requirements"].append(
                {
                    "skill": "devils-advocate",
                    "reason": "high_risk",
                    "justification": f"High complexity ({complexity['level']}) or core changes - critical thinking required",
                }
            )
            recommendations["recommended_skills"].append("devils-advocate")
            recommendations["justifications"]["devils-advocate"] = (
                f"High-risk work ({complexity['level']} complexity) - challenge assumptions and identify risks"
            )

        # Task-specific recommendations
        if task_type["requires_testing"] and not complexity["test_changes"]:
            recommendations["recommended_skills"].append("testing")
            recommendations["justifications"]["testing"] = (
                "Code changes detected - ensure comprehensive test coverage"
            )

        if task_type["type"] == "feature_development":
            recommendations["recommended_skills"].append("browser-manager")
            recommendations["justifications"]["browser-manager"] = (
                "Feature development - may need web testing/automation"
            )

        # Optional skills (always available)
        recommendations["optional_skills"] = [
            "ui (for frontend work)",
            "skill-making (for meta-work)",
            "process (for DevOps)",
            "openviking (alternative system)",
        ]

        return recommendations

    def save_session_context(self, context):
        """Save current session context"""
        session_file = self.log_dir / "session_context.json"
        session_data = {
            "last_directory": context["current_directory"],
            "last_commit_time": datetime.now().isoformat(),
            "session_id": os.environ.get("SESSION_ID", "unknown"),
        }

        try:
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)
        except:
            pass

    def display_recommendations(self, recommendations):
        """Display skill recommendations in user-friendly format"""
        print("🎯 Conditional Skill Requirements")
        print("=" * 50)

        # Conditional requirements
        if recommendations["conditional_requirements"]:
            print(f"\n📋 Conditionally Required Skills:")
            for req in recommendations["conditional_requirements"]:
                skill = req["skill"]
                reason = req["reason"]
                justification = req["justification"]
                print(f"  🎯 {skill}")
                print(f"     Reason: {justification}")

        # Recommended skills
        if recommendations["recommended_skills"]:
            print(f"\n💡 Recommended Skills:")
            for skill in recommendations["recommended_skills"]:
                if skill in recommendations["justifications"]:
                    justification = recommendations["justifications"][skill]
                    print(f"  💡 {skill}")
                    print(f"     Why: {justification}")
                else:
                    print(f"  💡 {skill}")

        # Always mandatory
        print(f"\n✅ Always Mandatory Skills:")
        for skill in recommendations["mandatory_skills"]:
            print(f"  ✅ {skill}")

        # Optional skills
        print(f"\n🔧 Optional Skills (use when helpful):")
        for skill in recommendations["optional_skills"]:
            print(f"  🔧 {skill}")

        print("\n" + "=" * 50)

    def save_recommendations(self, recommendations):
        """Save recommendations for analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rec_file = self.log_dir / f"skill_recommendations_{timestamp}.json"

        recommendations_data = {
            "timestamp": datetime.now().isoformat(),
            "session_context": self.check_session_context(),
            "work_complexity": self.check_work_complexity(),
            "task_type": self.check_task_type(),
            "recommendations": recommendations,
        }

        try:
            with open(rec_file, "w") as f:
                json.dump(recommendations_data, f, indent=2)
        except:
            pass

        return rec_file

    def run_detection(self):
        """Main conditional skill detection workflow"""
        print("🔍 Checking conditional skill requirements...")
        print("=" * 50)

        # Generate recommendations
        recommendations = self.generate_skill_recommendations()

        # Display to user
        self.display_recommendations(recommendations)

        # Save for analysis
        rec_file = self.save_recommendations(recommendations)

        print(f"\n💾 Recommendations saved: {rec_file}")

        # Log skill detection event
        self.log_skill_detection(recommendations)

        return 0

    def log_skill_detection(self, recommendations):
        """Log skill detection for analytics"""
        log_file = self.log_dir / "skill_detection.log"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "conditional_requirements_count": len(
                recommendations["conditional_requirements"]
            ),
            "recommended_skills_count": len(recommendations["recommended_skills"]),
            "complexity_level": self.check_work_complexity()["level"],
            "task_type": self.check_task_type()["type"],
        }

        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass


def main():
    detector = ConditionalSkillDetector()
    exit_code = detector.run_detection()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
