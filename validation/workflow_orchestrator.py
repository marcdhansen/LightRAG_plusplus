"""
Milestone Workflow Orchestrator
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .milestone_validator import MilestoneValidator
from .models import Milestone, MilestoneStatus, ValidationResult, WorkflowState


class MilestoneWorkflowOrchestrator:
    """Orchestrates milestone progression and validation"""

    def __init__(self, workflow_file: str = ".agent/state/workflow_state.json"):
        self.project_root = Path.cwd()
        self.workflow_file = self.project_root / workflow_file
        self.validator = MilestoneValidator()
        self.current_state = self._load_workflow_state()

    def _load_workflow_state(self) -> WorkflowState:
        """Load current workflow state from file"""
        if self.workflow_file.exists():
            try:
                with open(self.workflow_file) as f:
                    data = json.load(f)
                    return WorkflowState(
                        current_milestone=data.get("current_milestone", "development"),
                        completed_milestones=data.get("completed_milestones", []),
                        blocked_milestones=data.get("blocked_milestones", []),
                        validation_history=[],
                        last_updated=datetime.fromisoformat(
                            data.get("last_updated", datetime.now().isoformat())
                        ),
                        workflow_id=data.get(
                            "workflow_id", f"workflow_{datetime.now().timestamp()}"
                        ),
                        metadata=data.get("metadata", {}),
                    )
            except (json.JSONDecodeError, KeyError):
                pass

        # Create initial state
        return WorkflowState(
            current_milestone="development",
            completed_milestones=[],
            blocked_milestones=[],
            validation_history=[],
            last_updated=datetime.now(),
            workflow_id=f"workflow_{datetime.now().timestamp()}",
        )

    def _save_workflow_state(self) -> None:
        """Save workflow state to file"""
        self.workflow_file.parent.mkdir(parents=True, exist_ok=True)

        state_data = {
            "current_milestone": self.current_state.current_milestone,
            "completed_milestones": self.current_state.completed_milestones,
            "blocked_milestones": self.current_state.blocked_milestones,
            "validation_history": [
                {
                    "milestone_id": result.milestone_id,
                    "passed": result.passed,
                    "criteria_results": result.criteria_results,
                    "blocking_issues": result.blocking_issues,
                    "timestamp": result.timestamp.isoformat(),
                    "validation_duration_seconds": result.validation_duration_seconds,
                    "task_ids": result.task_ids,
                }
                for result in self.current_state.validation_history
            ],
            "last_updated": self.current_state.last_updated.isoformat(),
            "workflow_id": self.current_state.workflow_id,
            "metadata": self.current_state.metadata,
        }

        with open(self.workflow_file, "w") as f:
            json.dump(state_data, f, indent=2)

    async def advance_to_milestone(
        self,
        target_milestone: str,
        force: bool = False,
        task_ids: list[str] | None = None,
    ) -> ValidationResult:
        """
        Advance workflow to target milestone
        Blocks if intermediate milestones not validated (unless forced)
        """
        target = self.validator.get_milestone(target_milestone)
        if not target:
            raise ValueError(f"Target milestone not found: {target_milestone}")

        # Check if we can advance to this milestone
        if not force:
            await self._validate_prerequisite_milestones(target)

        # Validate the target milestone
        validation_result = await self.validator.validate_milestone(
            target_milestone, task_ids
        )

        # Update state based on validation result
        if validation_result.passed:
            self.current_state.completed_milestones.append(target_milestone)
            if target_milestone in self.current_state.blocked_milestones:
                self.current_state.blocked_milestones.remove(target_milestone)

            # Move to next milestone if available
            next_milestone = self.validator.get_next_milestone(target_milestone)
            if next_milestone:
                self.current_state.current_milestone = next_milestone.id
        else:
            self.current_state.blocked_milestones.append(target_milestone)

        # Add to validation history
        self.current_state.validation_history.append(validation_result)
        self.current_state.last_updated = datetime.now()

        # Save state
        self._save_workflow_state()

        return validation_result

    async def validate_current_milestone(
        self, task_ids: list[str] | None = None
    ) -> ValidationResult:
        """Validate current milestone against success criteria"""
        return await self.advance_to_milestone(
            self.current_state.current_milestone,
            force=True,  # Already at current milestone
            task_ids=task_ids,
        )

    async def _validate_prerequisite_milestones(
        self, target_milestone: Milestone
    ) -> None:
        """Validate that all prerequisite milestones are completed"""
        for dep_id in target_milestone.dependencies:
            if dep_id not in self.current_state.completed_milestones:
                raise ValueError(f"Prerequisite milestone not completed: {dep_id}")

        # Check that all previous milestones (by order) are completed
        for milestone in self.validator.list_milestones():
            if milestone.order >= target_milestone.order:
                break
            if (
                milestone.required_for_progression
                and milestone.id not in self.current_state.completed_milestones
            ):
                raise ValueError(
                    f"Required prerequisite milestone not completed: {milestone.id}"
                )

    def get_milestone_status(self, milestone_id: str | None = None) -> dict[str, Any]:
        """Get current status of milestones"""
        milestones = self.validator.list_milestones()
        status = {}

        for milestone in milestones:
            if milestone_id and milestone.id != milestone_id:
                continue

            if milestone.id in self.current_state.completed_milestones:
                status_str = MilestoneStatus.PASSED
            elif milestone.id in self.current_state.blocked_milestones:
                status_str = MilestoneStatus.BLOCKED
            elif milestone.id == self.current_state.current_milestone:
                status_str = MilestoneStatus.IN_PROGRESS
            else:
                status_str = MilestoneStatus.NOT_STARTED

            status[milestone.id] = {
                "name": milestone.name,
                "description": milestone.description,
                "order": milestone.order,
                "status": status_str,
                "required_for_progression": milestone.required_for_progression,
            }

        return status if milestone_id else status

    def get_workflow_summary(self) -> dict[str, Any]:
        """Get summary of current workflow state"""
        milestones = self.validator.list_milestones()
        total_milestones = len(milestones)
        completed = len(self.current_state.completed_milestones)
        blocked = len(self.current_state.blocked_milestones)

        progress_percentage = (
            (completed / total_milestones) * 100 if total_milestones > 0 else 0
        )

        return {
            "workflow_id": self.current_state.workflow_id,
            "current_milestone": self.current_state.current_milestone,
            "progress_percentage": round(progress_percentage, 1),
            "total_milestones": total_milestones,
            "completed_milestones": completed,
            "blocked_milestones": blocked,
            "last_updated": self.current_state.last_updated.isoformat(),
        }

    def get_validation_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent validation history"""
        history = self.current_state.validation_history[-limit:]
        return [
            {
                "milestone_id": result.milestone_id,
                "passed": result.passed,
                "timestamp": result.timestamp.isoformat(),
                "duration_seconds": result.validation_duration_seconds,
                "blocking_issues_count": len(result.blocking_issues),
                "recommendations_count": len(result.recommendations),
            }
            for result in history
        ]

    async def reset_milestone(
        self, milestone_id: str, reason: str, user_id: str | None = None
    ) -> None:
        """Reset a milestone (for testing or recovery)"""
        if milestone_id in self.current_state.completed_milestones:
            self.current_state.completed_milestones.remove(milestone_id)

        if milestone_id not in self.current_state.blocked_milestones:
            self.current_state.blocked_milestones.append(milestone_id)

        # Add reset metadata
        self.current_state.metadata[f"reset_{milestone_id}"] = {
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }

        self.current_state.last_updated = datetime.now()
        self._save_workflow_state()
