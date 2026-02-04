"""
Core data models for the Incremental Validation System
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MilestoneStatus(str, Enum):
    """Status of a milestone"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ValidationStepStatus(str, Enum):
    """Status of individual validation steps"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SuccessCriteria:
    """Defines success criteria for a milestone"""

    coverage_threshold: float = 80.0
    unit_tests_passed: bool = True
    tdd_gate_passed: bool = True
    integration_tests_passed: bool = True
    ab_test_significance: float = 0.05
    performance_improvement: float = 0.05
    error_rate_limit: float = 0.01
    rollback_test_passed: bool = True
    load_test_passed: bool = True
    monitoring_configured: bool = True
    performance_benchmarks: dict[str, float] = field(default_factory=dict)
    custom_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationStep:
    """Individual validation step within a milestone"""

    name: str
    status: ValidationStepStatus = ValidationStepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float | None = None


@dataclass
class Milestone:
    """Definition of a milestone"""

    id: str
    name: str
    description: str
    order: int
    success_criteria: SuccessCriteria
    validation_steps: list[str]
    blockers: list[str]
    dependencies: list[str] = field(default_factory=list)
    required_for_progression: bool = True
    adaptive_thresholds: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of milestone validation"""

    milestone_id: str
    passed: bool
    criteria_results: dict[str, bool]
    step_results: list[ValidationStep]
    metrics: dict[str, Any]
    blocking_issues: list[str]
    recommendations: list[str]
    timestamp: datetime
    validation_duration_seconds: float
    task_ids: list[str] = field(default_factory=list)


@dataclass
class WorkflowState:
    """Current state of the milestone workflow"""

    current_milestone: str
    completed_milestones: list[str]
    blocked_milestones: list[str]
    validation_history: list[ValidationResult]
    last_updated: datetime
    workflow_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackTrigger:
    """Trigger for rollback procedures"""

    milestone_id: str
    reason: str
    trigger_type: str  # "manual", "automated", "emergency"
    user_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackResult:
    """Result of rollback execution"""

    success: bool
    rollback_id: str
    milestone_id: str
    previous_state: str
    timestamp: datetime
    duration_seconds: float
    error_message: str | None = None
    verification_required: bool = True


@dataclass
class ABTestConfig:
    """Configuration for A/B testing validation"""

    control_group_size: float = 0.5
    treatment_group_size: float = 0.5
    minimum_sample_size: int = 1000
    test_duration_minutes: int = 60
    confidence_level: float = 0.95
    significance_threshold: float = 0.05
    effect_size_threshold: float = 0.2


@dataclass
class ABValidationResult:
    """Result of A/B test validation"""

    statistical_significance: bool
    p_value: float
    effect_size: float
    confidence_interval: tuple
    control_mean: float
    treatment_mean: float
    sample_size_control: int
    sample_size_treatment: int
    test_passed: bool
    recommendation: str


@dataclass
class BlockingConfig:
    """Configuration for blocking behavior"""

    auto_block_on_failure: bool = True
    notification_channels: list[str] = field(default_factory=list)
    escalation_rules: dict[str, Any] = field(default_factory=dict)
    emergency_bypass: dict[str, Any] = field(default_factory=dict)


class ValidationError(Exception):
    """Base exception for validation errors"""

    pass


class MilestoneNotFoundError(ValidationError):
    """Raised when a milestone is not found"""

    pass


class ValidationBlockedError(ValidationError):
    """Raised when validation is blocked"""

    pass


class RollbackFailedError(ValidationError):
    """Raised when rollback fails"""

    pass
