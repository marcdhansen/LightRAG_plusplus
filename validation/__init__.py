"""
Incremental Validation System for LightRAG

Provides milestone-based validation with automated quality gates,
statistical significance testing, and rollback-safe deployment procedures.
"""

from .milestone_validator import MilestoneValidator
from .models import Milestone, ValidationResult, WorkflowState
from .workflow_orchestrator import MilestoneWorkflowOrchestrator

__version__ = "1.0.0"
__all__ = [
    "MilestoneValidator",
    "Milestone",
    "ValidationResult",
    "WorkflowState",
    "MilestoneWorkflowOrchestrator",
]
