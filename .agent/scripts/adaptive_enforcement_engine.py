#!/usr/bin/env python3
"""
Adaptive Enforcement Rules Engine

Intelligent enforcement system that learns from performance patterns and adapts
SOP enforcement rules to reduce false positives and improve compliance.

Features:
- Performance pattern analysis
- Dynamic rule adaptation
- False positive reduction
- Context-aware enforcement
- Learning from historical data
"""

import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple


class ViolationPattern(NamedTuple):
    """Represents a violation pattern."""

    violation_type: str
    frequency: float
    false_positive_rate: float
    impact_score: float
    context_factors: list[str]
    last_seen: datetime


class PerformanceMetrics(NamedTuple):
    """Performance metrics for rule evaluation."""

    compliance_rate: float
    false_positive_rate: float
    violation_frequency: float
    agent_satisfaction: float
    workflow_impact: float


class AdaptiveEnforcementEngine:
    """Adaptive enforcement rules engine with learning capabilities."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or ".agent/config/adaptive_sop_rules.json"
        self.config = self._load_config()

        # Learning data storage
        self.violation_history = deque(maxlen=1000)
        self.pattern_analysis = defaultdict(list)
        self.rule_effectiveness = {}
        self.agent_feedback = deque(maxlen=500)

        # Performance tracking
        self.performance_window = timedelta(hours=24)
        self.learning_interval = timedelta(hours=6)
        self.last_learning_update = datetime.now()

        # State persistence
        self.state_file = Path(".agent/logs/adaptive_enforcement_state.json")
        self.patterns_file = Path(".agent/logs/violation_patterns.json")

        # Setup logging
        self.logger = logging.getLogger("adaptive_enforcement")
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)

        # Load existing state
        self._load_state()

    def _load_config(self) -> dict[str, Any]:
        """Load adaptive enforcement configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load adaptive config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "dynamic_rules": {
                "violation_thresholds": {
                    "base_threshold": 3,
                    "max_threshold": 10,
                    "adaptation_rate": 1.5,
                    "decay_rate": 0.9,
                },
                "compliance_scoring": {
                    "base_score": 100,
                    "critical_penalty": 25,
                    "high_penalty": 15,
                    "medium_penalty": 10,
                    "low_penalty": 5,
                    "recovery_rate": 0.1,
                },
                "enforcement_levels": {
                    "permissive": {
                        "blocking_enabled": False,
                        "alerts_only": True,
                        "violation_tolerance": 5,
                    },
                    "standard": {
                        "blocking_enabled": True,
                        "alerts_only": False,
                        "violation_tolerance": 3,
                    },
                    "strict": {
                        "blocking_enabled": True,
                        "alerts_only": False,
                        "violation_tolerance": 1,
                        "immediate_block": True,
                    },
                },
            },
            "learning_settings": {
                "min_samples": 20,
                "confidence_threshold": 0.8,
                "adaptation_sensitivity": 0.5,
                "pattern_recognition_window": 100,
            },
        }

    def _load_state(self):
        """Load previous enforcement state."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)

                # Load violation history
                for entry in state.get("violation_history", []):
                    self.violation_history.append(
                        {
                            **entry,
                            "timestamp": datetime.fromisoformat(entry["timestamp"]),
                        }
                    )

                # Load rule effectiveness
                self.rule_effectiveness = state.get("rule_effectiveness", {})

                # Load agent feedback
                for feedback in state.get("agent_feedback", []):
                    self.agent_feedback.append(
                        {
                            **feedback,
                            "timestamp": datetime.fromisoformat(feedback["timestamp"]),
                        }
                    )

            except Exception as e:
                self.logger.error(f"Failed to load enforcement state: {e}")

    def _save_state(self):
        """Save current enforcement state."""
        try:
            state = {
                "violation_history": [
                    {**v, "timestamp": v["timestamp"].isoformat()}
                    for v in self.violation_history
                ],
                "rule_effectiveness": self.rule_effectiveness,
                "agent_feedback": [
                    {**f, "timestamp": f["timestamp"].isoformat()}
                    for f in self.agent_feedback
                ],
                "last_learning_update": self.last_learning_update.isoformat(),
                "timestamp": datetime.now().isoformat(),
            }

            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save enforcement state: {e}")

    def record_violation(self, violation_type: str, context: dict[str, Any]):
        """Record a SOP violation for pattern analysis."""
        violation_entry = {
            "timestamp": datetime.now(),
            "violation_type": violation_type,
            "context": context,
            "enforced": True,
            "severity": self._get_violation_severity(violation_type),
        }

        self.violation_history.append(violation_entry)

        # Check if learning update is needed
        if datetime.now() - self.last_learning_update > self.learning_interval:
            self._update_learning_models()

    def record_agent_feedback(
        self, violation_id: str, was_false_positive: bool, context: dict[str, Any]
    ):
        """Record agent feedback on violation enforcement."""
        feedback_entry = {
            "timestamp": datetime.now(),
            "violation_id": violation_id,
            "was_false_positive": was_false_positive,
            "context": context,
            "agent_satisfaction": 1.0 if not was_false_positive else 0.0,
        }

        self.agent_feedback.append(feedback_entry)

    def _get_violation_severity(self, violation_type: str) -> str:
        """Get severity level for violation type."""
        severity_mapping = {
            "git_status_dirty": "critical",
            "session_lock_missing": "critical",
            "mandatory_skills_missing": "high",
            "tdd_compliance_failed": "high",
            "documentation_integrity": "medium",
            "beads_connectivity": "low",
        }
        return severity_mapping.get(violation_type, "medium")

    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics."""
        if not self.violation_history:
            return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

        # Get recent violations (last 24 hours)
        cutoff_time = datetime.now() - self.performance_window
        recent_violations = [
            v for v in self.violation_history if v["timestamp"] > cutoff_time
        ]

        if not recent_violations:
            return PerformanceMetrics(100.0, 0.0, 0.0, 0.0, 0.0)

        # Calculate compliance rate (fewer violations = higher compliance)
        total_possible_checks = 288  # Assuming 5-minute intervals over 24 hours
        compliance_rate = max(
            0, 100 - (len(recent_violations) / total_possible_checks * 100)
        )

        # Calculate false positive rate from agent feedback
        recent_feedback = [
            f for f in self.agent_feedback if f["timestamp"] > cutoff_time
        ]

        if recent_feedback:
            false_positive_rate = (
                sum(1 for f in recent_feedback if f["was_false_positive"])
                / len(recent_feedback)
                * 100
            )
        else:
            false_positive_rate = 0.0

        # Calculate violation frequency
        violation_frequency = len(recent_violations) / 24.0  # violations per hour

        # Calculate agent satisfaction from feedback
        if recent_feedback:
            agent_satisfaction = (
                sum(f["agent_satisfaction"] for f in recent_feedback)
                / len(recent_feedback)
                * 100
            )
        else:
            agent_satisfaction = 100.0

        # Calculate workflow impact (based on critical violations)
        critical_violations = sum(
            1 for v in recent_violations if v["severity"] == "critical"
        )
        workflow_impact = (
            (critical_violations / len(recent_violations)) * 100
            if recent_violations
            else 0
        )

        return PerformanceMetrics(
            compliance_rate=round(compliance_rate, 2),
            false_positive_rate=round(false_positive_rate, 2),
            violation_frequency=round(violation_frequency, 2),
            agent_satisfaction=round(agent_satisfaction, 2),
            workflow_impact=round(workflow_impact, 2),
        )

    def _analyze_violation_patterns(self) -> list[ViolationPattern]:
        """Analyze patterns in violation data."""
        patterns = []
        violation_types = defaultdict(list)

        # Group violations by type
        for violation in self.violation_history:
            violation_types[violation["violation_type"]].append(violation)

        # Analyze each violation type
        for vtype, violations in violation_types.items():
            if len(violations) < 3:  # Need minimum data
                continue

            # Calculate frequency
            time_span = max(v["timestamp"] for v in violations) - min(
                v["timestamp"] for v in violations
            )
            frequency = len(violations) / max(
                time_span.total_seconds() / 3600, 1
            )  # per hour

            # Calculate false positive rate
            violation_ids = [f"violation_{i}" for i in range(len(violations))]
            matching_feedback = [
                f for f in self.agent_feedback if f["violation_id"] in violation_ids
            ]

            if matching_feedback:
                false_positive_rate = (
                    sum(1 for f in matching_feedback if f["was_false_positive"])
                    / len(matching_feedback)
                    * 100
                )
            else:
                false_positive_rate = 0.0

            # Calculate impact score
            severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 1}
            impact_score = sum(
                severity_weights[v["severity"]] for v in violations
            ) / len(violations)

            # Extract context factors
            context_factors = []
            for violation in violations[-10:]:  # Last 10 violations
                ctx = violation.get("context", {})
                context_factors.extend(ctx.keys())

            context_factors = list(set(context_factors))

            patterns.append(
                ViolationPattern(
                    violation_type=vtype,
                    frequency=round(frequency, 3),
                    false_positive_rate=round(false_positive_rate, 2),
                    impact_score=round(impact_score, 2),
                    context_factors=context_factors,
                    last_seen=max(v["timestamp"] for v in violations),
                )
            )

        return sorted(patterns, key=lambda p: p.impact_score, reverse=True)

    def _calculate_adaptive_threshold(
        self, violation_type: str, base_threshold: int
    ) -> int:
        """Calculate adaptive threshold for violation type."""
        patterns = self._analyze_violation_patterns()

        # Find pattern for this violation type
        pattern = next(
            (p for p in patterns if p.violation_type == violation_type), None
        )

        if not pattern:
            return base_threshold

        # Adapt threshold based on false positive rate
        if pattern.false_positive_rate > 30:  # High false positive rate
            # Increase tolerance (less strict)
            adaptive_threshold = min(
                int(base_threshold * 1.5),
                self.config["dynamic_rules"]["violation_thresholds"]["max_threshold"],
            )
        elif (
            pattern.false_positive_rate < 5 and pattern.frequency > 2
        ):  # Low false positives, high frequency
            # Decrease tolerance (more strict)
            adaptive_threshold = max(int(base_threshold * 0.8), 1)
        else:
            adaptive_threshold = base_threshold

        return adaptive_threshold

    def _update_learning_models(self):
        """Update learning models based on accumulated data."""
        self.logger.info("Updating adaptive enforcement learning models")

        # Analyze performance metrics
        metrics = self._calculate_performance_metrics()

        # Analyze violation patterns
        patterns = self._analyze_violation_patterns()

        # Update rule effectiveness
        for rule_name, _rule_config in self.config["dynamic_rules"][
            "enforcement_levels"
        ].items():
            effectiveness_score = self._evaluate_rule_effectiveness(rule_name, metrics)
            self.rule_effectiveness[rule_name] = effectiveness_score

        # Adapt enforcement level based on performance
        current_enforcement = self.config.get("current_enforcement_level", "standard")

        if metrics.false_positive_rate > 25 and metrics.agent_satisfaction < 70:
            # Too many false positives, switch to permissive
            new_enforcement = "permissive"
        elif metrics.compliance_rate < 60 and metrics.violation_frequency > 5:
            # Low compliance, switch to strict
            new_enforcement = "strict"
        else:
            new_enforcement = "standard"

        if new_enforcement != current_enforcement:
            self.logger.info(
                f"Adapting enforcement level: {current_enforcement} -> {new_enforcement}"
            )
            self.config["current_enforcement_level"] = new_enforcement

        # Save updated patterns
        try:
            patterns_data = [
                {
                    "violation_type": p.violation_type,
                    "frequency": p.frequency,
                    "false_positive_rate": p.false_positive_rate,
                    "impact_score": p.impact_score,
                    "context_factors": p.context_factors,
                    "last_seen": p.last_seen.isoformat(),
                }
                for p in patterns
            ]

            with open(self.patterns_file, "w") as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save patterns: {e}")

        # Update learning timestamp
        self.last_learning_update = datetime.now()
        self._save_state()

    def _evaluate_rule_effectiveness(
        self, rule_name: str, metrics: PerformanceMetrics
    ) -> float:
        """Evaluate effectiveness of a specific rule."""
        self.config["dynamic_rules"]["enforcement_levels"][rule_name]

        # Calculate effectiveness score based on multiple factors
        compliance_weight = 0.4
        false_positive_weight = 0.3
        satisfaction_weight = 0.3

        # Higher compliance is better
        compliance_score = metrics.compliance_rate / 100.0

        # Lower false positives are better
        false_positive_score = max(0, 1.0 - metrics.false_positive_rate / 100.0)

        # Higher agent satisfaction is better
        satisfaction_score = metrics.agent_satisfaction / 100.0

        effectiveness = (
            compliance_score * compliance_weight
            + false_positive_score * false_positive_weight
            + satisfaction_score * satisfaction_weight
        )

        return round(effectiveness, 3)

    def should_enforce_violation(
        self, violation_type: str, context: dict[str, Any]
    ) -> tuple[bool, str]:
        """Determine if a violation should be enforced based on adaptive rules."""
        current_enforcement = self.config.get("current_enforcement_level", "standard")
        enforcement_config = self.config["dynamic_rules"]["enforcement_levels"][
            current_enforcement
        ]

        # Check if blocking is enabled
        if not enforcement_config["blocking_enabled"]:
            return False, f"Blocking disabled in {current_enforcement} enforcement mode"

        # Get adaptive threshold
        base_threshold = enforcement_config["violation_tolerance"]
        adaptive_threshold = self._calculate_adaptive_threshold(
            violation_type, base_threshold
        )

        # Count recent violations of this type
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_similar_violations = sum(
            1
            for v in self.violation_history
            if (v["violation_type"] == violation_type and v["timestamp"] > cutoff_time)
        )

        if recent_similar_violations < adaptive_threshold:
            return (
                False,
                f"Threshold not met ({recent_similar_violations} < {adaptive_threshold})",
            )

        # Context-aware enforcement
        if self._should_suppress_violation(violation_type, context):
            return False, "Context-aware suppression triggered"

        return (
            True,
            f"Enforcement approved ({current_enforcement} mode, threshold: {adaptive_threshold})",
        )

    def _should_suppress_violation(
        self, violation_type: str, context: dict[str, Any]
    ) -> bool:
        """Check if violation should be suppressed based on context."""
        # Emergency mode suppression
        if context.get("emergency_mode", False):
            return True

        # Maintenance mode suppression for non-critical violations
        if context.get("maintenance_mode", False):
            severity = self._get_violation_severity(violation_type)
            if severity in ["low", "medium"]:
                return True

        # Agent coordination suppression
        if context.get("coordination_mode", False):
            if violation_type in ["beads_connectivity", "documentation_integrity"]:
                return True

        return False

    def get_enforcement_recommendations(self) -> list[dict[str, Any]]:
        """Get recommendations for enforcement improvements."""
        recommendations = []
        metrics = self._calculate_performance_metrics()
        patterns = self._analyze_violation_patterns()

        # High false positive rate recommendations
        if metrics.false_positive_rate > 25:
            high_fp_patterns = [p for p in patterns if p.false_positive_rate > 30]
            if high_fp_patterns:
                recommendations.append(
                    {
                        "type": "false_positive_reduction",
                        "priority": "high",
                        "description": f"High false positive rate ({metrics.false_positive_rate:.1f}%)",
                        "suggestion": "Consider adjusting thresholds or rules for: "
                        + ", ".join(p.violation_type for p in high_fp_patterns[:3]),
                        "impact": "medium",
                    }
                )

        # Low compliance recommendations
        if metrics.compliance_rate < 70:
            recommendations.append(
                {
                    "type": "compliance_improvement",
                    "priority": "high",
                    "description": f"Low compliance rate ({metrics.compliance_rate:.1f}%)",
                    "suggestion": "Consider stricter enforcement or additional training",
                    "impact": "high",
                }
            )

        # Agent satisfaction recommendations
        if metrics.agent_satisfaction < 75:
            recommendations.append(
                {
                    "type": "satisfaction_improvement",
                    "priority": "medium",
                    "description": f"Low agent satisfaction ({metrics.agent_satisfaction:.1f}%)",
                    "suggestion": "Review enforcement policies and reduce friction",
                    "impact": "medium",
                }
            )

        # High-impact pattern recommendations
        high_impact_patterns = [p for p in patterns if p.impact_score > 7]
        if high_impact_patterns:
            recommendations.append(
                {
                    "type": "pattern_intervention",
                    "priority": "medium",
                    "description": "High-impact violation patterns detected",
                    "suggestion": "Focus on root cause analysis for: "
                    + ", ".join(p.violation_type for p in high_impact_patterns[:2]),
                    "impact": "high",
                }
            )

        return sorted(
            recommendations,
            key=lambda r: (
                {"high": 0, "medium": 1, "low": 2}[r["priority"]],
                r["impact"],
            ),
        )

    def get_adaptive_config(self) -> dict[str, Any]:
        """Get current adaptive configuration."""
        return {
            "current_enforcement_level": self.config.get(
                "current_enforcement_level", "standard"
            ),
            "performance_metrics": self._calculate_performance_metrics()._asdict(),
            "rule_effectiveness": self.rule_effectiveness,
            "learning_status": {
                "last_update": self.last_learning_update.isoformat(),
                "total_violations": len(self.violation_history),
                "total_feedback": len(self.agent_feedback),
                "patterns_analyzed": len(self._analyze_violation_patterns()),
            },
            "recommendations": self.get_enforcement_recommendations(),
        }


def main():
    """CLI interface for adaptive enforcement engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Enforcement Rules Engine")
    parser.add_argument("--test", action="store_true", help="Run enforcement test")
    parser.add_argument(
        "--recommendations", action="store_true", help="Show recommendations"
    )
    parser.add_argument("--status", action="store_true", help="Show enforcement status")
    parser.add_argument("--violation", type=str, help="Test violation enforcement")

    args = parser.parse_args()

    engine = AdaptiveEnforcementEngine()

    if args.status:
        config = engine.get_adaptive_config()
        print(json.dumps(config, indent=2))
    elif args.recommendations:
        recommendations = engine.get_enforcement_recommendations()
        print(json.dumps(recommendations, indent=2))
    elif args.violation:
        should_enforce, reason = engine.should_enforce_violation(args.violation, {})
        print(f"Violation: {args.violation}")
        print(f"Should enforce: {should_enforce}")
        print(f"Reason: {reason}")
    elif args.test:
        # Test with sample violations
        engine.record_violation("git_status_dirty", {"test": True})
        engine.record_agent_feedback("test_violation", False, {"test": True})

        metrics = engine._calculate_performance_metrics()
        print("Test metrics:", metrics._asdict())

        recommendations = engine.get_enforcement_recommendations()
        print("Recommendations:", json.dumps(recommendations, indent=2))
    else:
        print("Adaptive Enforcement Rules Engine")
        print("Use --help to see available options")


if __name__ == "__main__":
    main()
