#!/usr/bin/env python3
"""
TDD Metadata Enhancer for Beads Tasks

Enhances existing Beads tasks with TDD requirements and metadata.

Usage:
    python tdd_metadata_enhancer.py --task-id <id> --tdd-requirements <json>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class TDDMetadataEnhancer:
    """Enhances Beads tasks with TDD metadata"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def enhance_task_metadata(
        self, task_id: str, tdd_requirements: dict[str, Any]
    ) -> bool:
        """Enhance task metadata with TDD requirements"""
        try:
            # Get current task data
            result = subprocess.run(
                ["bd", "show", task_id, "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                print(f"❌ Failed to get task {task_id}: {result.stderr}")
                return False

            task_data = json.loads(result.stdout)

            # Add TDD metadata
            if "metadata" not in task_data:
                task_data["metadata"] = {}

            task_data["metadata"]["tdd_requirements"] = tdd_requirements

            # Add default test requirements if not specified
            default_requirements = {
                "unit_tests_required": True,
                "integration_tests_required": tdd_requirements.get("complexity", 5) > 7,
                "coverage_threshold": 80,
                "baseline_required": tdd_requirements.get("is_performance_task", False),
                "test_plan_status": "required",
            }

            # Merge with user-provided requirements
            for key, value in default_requirements.items():
                if key not in tdd_requirements:
                    task_data["metadata"]["tdd_requirements"][key] = value

            # Update task with enhanced metadata
            update_command = [
                "bd",
                "update",
                task_id,
                "--metadata",
                json.dumps(task_data.get("metadata", {})),
            ]

            result = subprocess.run(
                update_command, capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode != 0:
                print(f"❌ Failed to update task metadata: {result.stderr}")
                return False

            print(f"✅ Enhanced task {task_id} with TDD requirements")
            return True

        except Exception as e:
            print(f"❌ Failed to enhance task metadata: {e}")
            return False

    def create_default_tdd_requirements(
        self, task_title: str, task_description: str
    ) -> dict[str, Any]:
        """Create default TDD requirements based on task characteristics"""

        # Determine if this is a performance task
        performance_keywords = [
            "optimization",
            "benchmark",
            "performance",
            "speed",
            "extraction.*prompt",
            "lite.*extraction",
        ]

        is_performance = any(
            keyword in task_title.lower() or keyword in task_description.lower()
            for keyword in performance_keywords
        )

        # Estimate complexity based on title/description
        complexity_indicators = [
            ("implement", 3),
            ("add", 2),
            ("fix", 2),
            ("refactor", 4),
            ("optimize", 5),
            ("create", 3),
        ]

        base_complexity = 5
        for indicator, score in complexity_indicators:
            if indicator in task_title.lower():
                base_complexity = max(base_complexity, score)

        return {
            "is_performance_task": is_performance,
            "complexity": base_complexity,
            "unit_tests_required": True,
            "integration_tests_required": base_complexity > 7,
            "coverage_threshold": 80,
            "baseline_required": is_performance,
            "test_plan_status": "required",
        }

    def list_tasks_enhancement_status(self) -> bool:
        """List TDD enhancement status for all tasks"""
        try:
            result = subprocess.run(
                ["bd", "list", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                print(f"❌ Failed to list tasks: {result.stderr}")
                return False

            tasks = json.loads(result.stdout) if result.stdout else []

            print("📋 TDD Enhancement Status")
            print("=" * 40)

            enhanced_count = 0
            for task in tasks:
                metadata = task.get("metadata", {})
                tdd_reqs = metadata.get("tdd_requirements", {})

                if tdd_reqs:
                    enhanced_count += 1
                    status_emoji = "✅"
                    complexity = tdd_reqs.get("complexity", "unknown")
                    baseline_req = tdd_reqs.get("baseline_required", False)
                    status = f"TDD Complete (C:{complexity}, Baseline:{baseline_req})"
                else:
                    status_emoji = "⚠️"
                    status = "TDD Not Configured"

                print(f"{status_emoji} {task['id']}: {status}")
                print(f"     {task['title']}")

            print(f"\nSummary: {enhanced_count}/{len(tasks)} tasks have TDD metadata")
            return True

        except Exception as e:
            print(f"❌ Failed to list tasks: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="TDD Metadata Enhancer for Beads")
    parser.add_argument("--task-id", help="Task ID to enhance")
    parser.add_argument("--tdd-requirements", help="JSON string with TDD requirements")
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect TDD requirements from task title/description",
    )
    parser.add_argument(
        "--list-status",
        action="store_true",
        help="List TDD enhancement status for all tasks",
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    enhancer = TDDMetadataEnhancer(project_root)

    if args.list_status:
        success = enhancer.list_tasks_enhancement_status()
        sys.exit(0 if success else 1)

    if not args.task_id:
        print("❌ --task-id is required")
        sys.exit(1)

    if args.auto_detect:
        # Get task details and auto-detect requirements
        try:
            result = subprocess.run(
                ["bd", "show", args.task_id, "--json"],
                capture_output=True,
                text=True,
                cwd=project_root,
            )

            if result.returncode != 0:
                print(f"❌ Failed to get task {args.task_id}: {result.stderr}")
                sys.exit(1)

            task_data = json.loads(result.stdout)
            tdd_requirements = enhancer.create_default_tdd_requirements(
                task_data.get("title", ""), task_data.get("description", "")
            )
        except Exception as e:
            print(f"❌ Failed to auto-detect requirements: {e}")
            sys.exit(1)
    elif args.tdd_requirements:
        try:
            tdd_requirements = json.loads(args.tdd_requirements)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON for TDD requirements: {e}")
            sys.exit(1)
    else:
        print("❌ Either --tdd-requirements or --auto-detect is required")
        sys.exit(1)

    success = enhancer.enhance_task_metadata(args.task_id, tdd_requirements)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
