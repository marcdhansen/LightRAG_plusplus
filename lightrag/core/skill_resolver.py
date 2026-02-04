"""
Universal Skill Resolver - Ensures agents can find and use required skills
Provides multiple fallback locations and graceful degradation strategies.
"""

import os
import sys
import json
from typing import Dict, Optional, List
from pathlib import Path


class SkillNotFoundError(Exception):
    """Raised when a skill cannot be found in any location."""

    pass


class UniversalSkillResolver:
    """
    Universal skill resolver that checks multiple locations with priority-based fallback.

    Priority Order:
    1. Global: ~/.gemini/antigravity/skills/ (primary)
    2. Local: .agent/skills/ (secondary)
    3. System: /usr/local/share/lightrag/skills/ (tertiary)
    4. Project: ./skills/ (fallback)
    """

    def __init__(self):
        self.skill_locations = [
            os.path.expanduser("~/.gemini/antigravity/skills/"),  # Global (primary)
            ".agent/skills/",  # Local (secondary)
            "/usr/local/share/lightrag/skills/",  # System-wide (tertiary)
            "./skills/",  # Project-local (fallback)
        ]
        self.skill_cache = {}
        self.fallback_strategies = {
            "return-to-base": self._manual_rtb_fallback,
            "reflect": self._manual_reflection_fallback,
            "mission-debriefing": self._manual_debrief_fallback,
            "planning": self._basic_planning_fallback,
            "show-next-task": self._task_list_fallback,
        }

    def find_skill(self, skill_name: str) -> Optional[Dict]:
        """
        Find skill with multiple fallback locations.

        Args:
            skill_name: Name of the skill to find

        Returns:
            Dict with skill info or None if not found
        """
        if skill_name in self.skill_cache:
            return self.skill_cache[skill_name]

        for priority, location in enumerate(self.skill_locations, 1):
            skill_info = self._check_skill_location(skill_name, location, priority)
            if skill_info:
                self.skill_cache[skill_name] = skill_info
                return skill_info

        return None

    def _check_skill_location(
        self, skill_name: str, location: str, priority: int
    ) -> Optional[Dict]:
        """Check if skill exists at a specific location."""
        skill_path = os.path.join(location, skill_name, "SKILL.md")
        script_path = os.path.join(location, skill_name, "scripts", f"{skill_name}.sh")

        # Check if path exists (handles symlinks correctly)
        if os.path.exists(skill_path) and os.path.exists(script_path):
            return {
                "skill_path": os.path.realpath(skill_path),
                "script_path": os.path.realpath(script_path),
                "location": location,
                "priority": priority,
                "location_type": self._get_location_type(location),
            }

        return None

    def _get_location_type(self, location: str) -> str:
        """Get human-readable location type."""
        if "gemini" in location:
            return "global"
        elif ".agent/skills" in location:
            return "local"
        elif "usr/local" in location:
            return "system"
        else:
            return "project"

    def require_skill(self, skill_name: str) -> Dict:
        """
        Get skill with multiple fallback strategies.

        Args:
            skill_name: Name of the skill to find

        Returns:
            Dict with skill info

        Raises:
            SkillNotFoundError: If skill cannot be found in any location
        """
        skill_info = self.find_skill(skill_name)
        if not skill_info:
            # Try fallback strategies
            if skill_name in self.fallback_strategies:
                print(f"⚠️ Skill '{skill_name}' not found, using fallback strategy")
                fallback_result = self.fallback_strategies[skill_name]()
                if fallback_result:
                    return fallback_result

            raise SkillNotFoundError(
                f"Skill '{skill_name}' not found in any location. "
                f"Searched: {self.skill_locations}"
            )

        return skill_info

    def get_fallback_plans(self, missing_skills: List[str]) -> Dict[str, str]:
        """Get fallback plans for missing skills."""
        plans = {}
        for skill in missing_skills:
            if skill in self.fallback_strategies:
                plans[skill] = f"Manual fallback available for {skill}"
            else:
                plans[skill] = f"No fallback available for {skill}"
        return plans

    def assess_mission_feasibility(
        self, required_skills: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Assess if mission is feasible with available skills.

        Returns:
            (feasible, missing_skills)
        """
        missing = []
        for skill in required_skills:
            if not self.find_skill(skill):
                missing.append(skill)

        return len(missing) == 0, missing

    def list_all_available_skills(self) -> Dict[str, List[Dict]]:
        """List all available skills across all locations."""
        available = {}

        for location in self.skill_locations:
            if os.path.exists(location):
                skills_in_location = []
                for item in os.listdir(location):
                    skill_path = os.path.join(location, item)
                    if os.path.isdir(skill_path):
                        skill_info = self._check_skill_location(item, location, 0)
                        if skill_info:
                            skills_in_location.append(skill_info)

                if skills_in_location:
                    available[location] = skills_in_location

        return available

    def _manual_rtb_fallback(self) -> Optional[Dict]:
        """Manual RTB fallback implementation."""
        return {
            "skill_path": "fallback:return-to-base",
            "script_path": "return-to-base.sh",
            "location": "builtin-fallback",
            "priority": 999,
            "location_type": "emergency",
            "description": "Manual RTB workflow - limited functionality",
        }

    def _manual_reflection_fallback(self) -> Optional[Dict]:
        """Manual reflection fallback implementation."""
        return {
            "skill_path": "fallback:reflect",
            "script_path": "reflect/scripts/fallback:reflect.sh",
            "location": "builtin-fallback",
            "priority": 999,
            "location_type": "emergency",
            "description": "Manual reflection template - basic functionality",
        }

    def _manual_debrief_fallback(self) -> Optional[Dict]:
        """Manual debriefing fallback implementation."""
        return {
            "skill_path": "fallback:mission-debriefing",
            "script_path": "fallback:mission-debriefing.sh",
            "location": "builtin-fallback",
            "priority": 999,
            "location_type": "emergency",
            "description": "Manual debriefing template - structured analysis",
        }

    def _basic_planning_fallback(self) -> Optional[Dict]:
        """Basic planning fallback implementation."""
        return {
            "skill_path": "fallback:planning",
            "script_path": "fallback:planning.sh",
            "location": "builtin-fallback",
            "priority": 999,
            "location_type": "emergency",
            "description": "Manual planning template - basic task analysis",
        }

    def _task_list_fallback(self) -> Optional[Dict]:
        """Task list fallback implementation."""
        return {
            "skill_path": "fallback:show-next-task",
            "script_path": "fallback:show-next-task.sh",
            "location": "builtin-fallback",
            "priority": 999,
            "location_type": "emergency",
            "description": "Manual task discovery - basic functionality",
        }


def test_skill_resolver():
    """Test the skill resolver functionality."""
    resolver = UniversalSkillResolver()

    print("🔍 Testing Universal Skill Resolver")
    print("=" * 50)

    # Test finding available skills
    print("\n📋 Available Skills:")
    available = resolver.list_all_available_skills()
    for location, skills in available.items():
        print(f"  {location} ({len(skills)} skills):")
        for skill in skills:
            print(f"    - {skill['skill_path']} ({skill['location_type']})")

    # Test finding specific skills
    test_skills = ["return-to-base", "reflect", "mission-debriefing"]
    print(f"\n🧪 Testing Skill Resolution for: {test_skills}")

    for skill in test_skills:
        try:
            skill_info = resolver.require_skill(skill)
            print(
                f"  ✅ {skill}: {skill_info['skill_path']} ({skill_info['location_type']})"
            )
        except SkillNotFoundError as e:
            print(f"  ❌ {skill}: {e}")

    # Test mission feasibility
    print(f"\n🎯 Mission Feasibility Test:")
    feasible, missing = resolver.assess_mission_feasibility(test_skills)
    print(f"  Feasible: {feasible}")
    if missing:
        print(f"  Missing: {missing}")
        fallback_plans = resolver.get_fallback_plans(missing)
        for skill, plan in fallback_plans.items():
            print(f"  {skill}: {plan}")


if __name__ == "__main__":
    test_skill_resolver()
