#!/usr/bin/env python3
"""
Adaptive SOP Rules Integration with Orchestrator

Integrates real-time monitoring with the Orchestrator system for dynamic SOP enforcement.
Provides adaptive rule management based on session patterns and compliance history.

Usage:
    python adaptive_orchestrator_integration.py --integrate
    python adaptive_orchestrator_integration.py --get-rules
    python adaptive_orchestrator_integration.py --update-rules
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class AdaptiveOrchestratorIntegration:
    """Integration between adaptive SOP engine and Orchestrator system"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.orchestrator_dir = Path.home() / ".gemini/antigravity/skills/Orchestrator"
        self.config_dir = self.script_dir.parent / "config"
        self.logs_dir = self.script_dir.parent / "logs"

        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Configuration files
        self.adaptive_rules_file = self.config_dir / "adaptive_sop_rules.json"
        self.integration_log = self.logs_dir / "adaptive_orchestrator_integration.log"

        # Load current configuration
        self.adaptive_rules = self.load_adaptive_rules()

    def load_adaptive_rules(self) -> dict:
        """Load adaptive SOP rules configuration"""
        default_rules = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "dynamic_rules": {
                "monitoring_frequency": {
                    "base_interval": 30,
                    "min_interval": 15,
                    "max_interval": 300,
                    "adaptation_factor": 0.1,
                    "success_rate_threshold": 80,
                },
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
            "current_enforcement_level": "standard",
            "performance_metrics": {
                "success_rate": 100.0,
                "avg_compliance_score": 100.0,
                "violation_frequency": 0.0,
                "false_positive_rate": 0.0,
            },
            "learning_data": {
                "session_history": [],
                "violation_patterns": {},
                "effectiveness_metrics": {},
            },
        }

        if self.adaptive_rules_file.exists():
            try:
                with open(self.adaptive_rules_file) as f:
                    user_rules = json.load(f)
                default_rules.update(user_rules)
            except Exception as e:
                self.log_message("ERROR", f"Failed to load adaptive rules: {e}")

        return default_rules

    def save_adaptive_rules(self):
        """Save adaptive SOP rules configuration"""
        try:
            self.adaptive_rules["last_updated"] = datetime.now().isoformat()
            with open(self.adaptive_rules_file, "w") as f:
                json.dump(self.adaptive_rules, f, indent=2)
        except Exception as e:
            self.log_message("ERROR", f"Failed to save adaptive rules: {e}")

    def log_message(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{level} {timestamp}] {message}"

        # Write to log file
        try:
            with open(self.integration_log, "a") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass

        # Also print to stdout
        print(f"🔗 {log_entry}")

    def get_session_performance_metrics(self) -> dict:
        """Get performance metrics from adaptive SOP engine"""
        try:
            engine_script = self.script_dir / "adaptive_sop_engine.sh"
            if not engine_script.exists():
                return {"success_rate": 100.0, "total_sessions": 0}

            result = subprocess.run(
                [str(engine_script), "--action", "analyze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                analysis = json.loads(result.stdout)
                metrics = analysis.get("metrics", {})
                return {
                    "success_rate": metrics.get("success_rate", 100.0),
                    "total_sessions": metrics.get("total_sessions", 0),
                    "failed_sessions": metrics.get("failed_sessions", 0),
                    "fast_mode_usage_rate": metrics.get("fast_mode_usage_rate", 0),
                }
        except Exception as e:
            self.log_message("ERROR", f"Failed to get performance metrics: {e}")

        return {"success_rate": 100.0, "total_sessions": 0}

    def get_realtime_monitor_status(self) -> dict:
        """Get current real-time monitor status"""
        try:
            monitor_script = self.script_dir / "realtime_sop_monitor.py"
            if not monitor_script.exists():
                return {"running": False}

            result = subprocess.run(
                [sys.executable, str(monitor_script), "--status"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            self.log_message("ERROR", f"Failed to get monitor status: {e}")

        return {"running": False}

    def calculate_adaptive_adjustments(self) -> dict:
        """Calculate adaptive rule adjustments based on current performance"""
        metrics = self.get_session_performance_metrics()
        monitor_status = self.get_realtime_monitor_status()

        current_rules = self.adaptive_rules["dynamic_rules"]
        adjustments = {}

        # Adjust monitoring frequency based on success rate
        success_rate = metrics.get("success_rate", 100.0)
        if success_rate < 80:
            # Increase monitoring frequency for low success rates
            new_interval = max(
                current_rules["monitoring_frequency"]["min_interval"],
                int(current_rules["monitoring_frequency"]["base_interval"] * 0.7),
            )
            adjustments["monitoring_interval"] = new_interval
            adjustments["reason"] = (
                f"Low success rate ({success_rate:.1f}%) - increased monitoring"
            )
        elif success_rate > 95:
            # Decrease monitoring frequency for high success rates
            new_interval = min(
                current_rules["monitoring_frequency"]["max_interval"],
                int(current_rules["monitoring_frequency"]["base_interval"] * 1.3),
            )
            adjustments["monitoring_interval"] = new_interval
            adjustments["reason"] = (
                f"High success rate ({success_rate:.1f}%) - optimized monitoring"
            )

        # Adjust enforcement level based on compliance score
        compliance_score = monitor_status.get("compliance_score", 100.0)
        current_level = self.adaptive_rules["current_enforcement_level"]

        if compliance_score < 60 and current_level != "strict":
            adjustments["enforcement_level"] = "strict"
            adjustments["reason"] = (
                f"Low compliance score ({compliance_score:.1f}%) - strict enforcement"
            )
        elif compliance_score > 85 and current_level == "strict":
            adjustments["enforcement_level"] = "standard"
            adjustments["reason"] = (
                f"High compliance score ({compliance_score:.1f}%) - relaxed to standard"
            )
        elif compliance_score < 75 and current_level == "permissive":
            adjustments["enforcement_level"] = "standard"
            adjustments["reason"] = (
                f"Moderate compliance score ({compliance_score:.1f}%) - standard enforcement"
            )

        # Adjust violation thresholds based on patterns
        violation_count = monitor_status.get("violation_count", 0)
        if violation_count > current_rules["violation_thresholds"]["base_threshold"]:
            # Increase threshold if too many violations (likely too strict)
            new_threshold = min(
                current_rules["violation_thresholds"]["max_threshold"],
                int(current_rules["violation_thresholds"]["base_threshold"] * 1.2),
            )
            adjustments["violation_threshold"] = new_threshold
            adjustments["reason"] = (
                f"High violation count ({violation_count}) - adjusted threshold"
            )

        return adjustments

    def apply_adaptive_adjustments(self, adjustments: dict):
        """Apply calculated adaptive adjustments"""
        if not adjustments:
            return

        self.log_message(
            "ADAPTIVE", f"Applying adjustments: {adjustments.get('reason', 'Unknown')}"
        )

        # Apply monitoring interval adjustment
        if "monitoring_interval" in adjustments:
            new_interval = adjustments["monitoring_interval"]
            self.adaptive_rules["dynamic_rules"]["monitoring_frequency"][
                "base_interval"
            ] = new_interval
            self.log_message(
                "ADAPTIVE", f"Updated monitoring interval to {new_interval}s"
            )

        # Apply enforcement level adjustment
        if "enforcement_level" in adjustments:
            new_level = adjustments["enforcement_level"]
            self.adaptive_rules["current_enforcement_level"] = new_level
            self.log_message("ADAPTIVE", f"Updated enforcement level to {new_level}")

        # Apply violation threshold adjustment
        if "violation_threshold" in adjustments:
            new_threshold = adjustments["violation_threshold"]
            self.adaptive_rules["dynamic_rules"]["violation_thresholds"][
                "base_threshold"
            ] = new_threshold
            self.log_message(
                "ADAPTIVE", f"Updated violation threshold to {new_threshold}"
            )

        # Save updated rules
        self.save_adaptive_rules()

    def integrate_with_orchestrator(self) -> bool:
        """Integrate adaptive rules with Orchestrator system"""
        self.log_message("INFO", "Starting integration with Orchestrator system")

        # Check if Orchestrator is available
        if not self.orchestrator_dir.exists():
            self.log_message("ERROR", "Orchestrator skill not found")
            return False

        orchestrator_script = (
            self.orchestrator_dir / "scripts" / "check_protocol_compliance.py"
        )
        if not orchestrator_script.exists():
            self.log_message("ERROR", "Orchestrator compliance script not found")
            return False

        # Calculate and apply adaptive adjustments
        adjustments = self.calculate_adaptive_adjustments()
        self.apply_adaptive_adjustments(adjustments)

        # Create integration bridge for Orchestrator
        self.create_orchestrator_bridge()

        self.log_message("INFO", "Integration with Orchestrator completed")
        return True

    def create_orchestrator_bridge(self):
        """Create bridge script for Orchestrator integration"""
        bridge_script = self.script_dir / "orchestrator_adaptive_bridge.py"

        bridge_content = '''#!/usr/bin/env python3
"""
Orchestrator Adaptive Bridge

Bridge between Orchestrator and Adaptive SOP system.
Provides dynamic rule checking for Orchestrator validation.
"""

import json
import sys
from pathlib import Path

# Add adaptive integration to path
sys.path.append(str(Path(__file__).parent))

from adaptive_orchestrator_integration import AdaptiveOrchestratorIntegration

def get_adaptive_rules():
    """Get current adaptive rules for Orchestrator"""
    integration = AdaptiveOrchestratorIntegration()
    return integration.adaptive_rules

def check_adaptive_compliance(phase: str) -> dict:
    """Check compliance using adaptive rules for specific phase"""
    integration = AdaptiveOrchestratorIntegration()
    rules = integration.adaptive_rules

    # Get current enforcement level
    enforcement_level = rules["current_enforcement_level"]
    level_config = rules["dynamic_rules"]["enforcement_levels"][enforcement_level]

    # Phase-specific checks
    if phase == "initialization":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"]["base_interval"],
            "checks": {
                "tools_required": True,
                "workspace_integrity": True,
                "context_available": True,
                "adaptive_threshold": True
            }
        }
    elif phase == "execution":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"]["base_interval"],
            "checks": {
                "feature_branch": True,
                "beads_issue": True,
                "plan_approval": True,
                "tdd_compliance": True,
                "adaptive_threshold": True
            }
        }
    elif phase == "finalization":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"]["base_interval"],
            "checks": {
                "git_clean": True,
                "atomic_commits": True,
                "reflection_captured": True,
                "code_review": True,
                "adaptive_threshold": True
            }
        }
    else:
        return {"error": f"Unknown phase: {phase}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_adaptive_bridge.py <phase>")
        sys.exit(1)

    phase = sys.argv[1]
    result = check_adaptive_compliance(phase)
    print(json.dumps(result, indent=2))
'''

        try:
            with open(bridge_script, "w") as f:
                f.write(bridge_content)

            # Make bridge script executable
            os.chmod(bridge_script, 0o755)

            self.log_message("INFO", f"Created Orchestrator bridge: {bridge_script}")
        except Exception as e:
            self.log_message("ERROR", f"Failed to create bridge script: {e}")

    def get_current_rules(self) -> dict:
        """Get current adaptive rules"""
        return self.adaptive_rules

    def update_rules_from_patterns(self) -> bool:
        """Update rules based on learned patterns"""
        try:
            # Get session history from adaptive SOP engine
            engine_script = self.script_dir / "adaptive_sop_engine.sh"
            if not engine_script.exists():
                return False

            result = subprocess.run(
                [str(engine_script), "--action", "analyze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return False

            analysis = json.loads(result.stdout)

            # Extract patterns and recommendations
            patterns = analysis.get("patterns", {})
            recommendations = analysis.get("recommendations", [])

            # Update learning data
            learning_data = self.adaptive_rules["learning_data"]
            learning_data["session_history"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": analysis.get("metrics", {}),
                    "patterns": patterns,
                    "recommendations": recommendations,
                }
            )

            # Keep only last 50 session records
            if len(learning_data["session_history"]) > 50:
                learning_data["session_history"] = learning_data["session_history"][
                    -50:
                ]

            # Update performance metrics
            metrics = analysis.get("metrics", {})
            self.adaptive_rules["performance_metrics"].update(
                {
                    "success_rate": metrics.get("success_rate", 100.0),
                    "avg_compliance_score": self.get_realtime_monitor_status().get(
                        "compliance_score", 100.0
                    ),
                }
            )

            # Save updated rules
            self.save_adaptive_rules()

            self.log_message("INFO", "Updated rules from learned patterns")
            return True

        except Exception as e:
            self.log_message("ERROR", f"Failed to update rules from patterns: {e}")
            return False

    def generate_compliance_report(self) -> dict:
        """Generate comprehensive compliance report"""
        metrics = self.get_session_performance_metrics()
        monitor_status = self.get_realtime_monitor_status()
        rules = self.adaptive_rules

        report = {
            "timestamp": datetime.now().isoformat(),
            "adaptive_rules_version": rules["version"],
            "current_enforcement_level": rules["current_enforcement_level"],
            "performance_metrics": metrics,
            "monitor_status": monitor_status,
            "compliance_trends": {
                "success_rate_trend": self.calculate_trend(
                    [
                        s.get("metrics", {}).get("success_rate", 100)
                        for s in rules["learning_data"]["session_history"][-10:]
                    ]
                ),
                "compliance_score_trend": self.calculate_trend(
                    [
                        s.get("compliance_score", 100)
                        for s in rules["learning_data"]["session_history"][-10:]
                    ]
                ),
            },
            "adaptive_adjustments": self.calculate_adaptive_adjustments(),
            "recommendations": self.generate_recommendations(metrics, monitor_status),
        }

        return report

    def calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return "stable"

        recent = values[-3:] if len(values) >= 3 else values
        older = values[-6:-3] if len(values) >= 6 else values[: len(values) // 2]

        if not older:
            return "stable"

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 5:
            return "improving"
        elif recent_avg < older_avg - 5:
            return "declining"
        else:
            return "stable"

    def generate_recommendations(
        self, metrics: dict, monitor_status: dict
    ) -> list[str]:
        """Generate recommendations based on current state"""
        recommendations = []

        success_rate = metrics.get("success_rate", 100.0)
        compliance_score = monitor_status.get("compliance_score", 100.0)
        violation_count = monitor_status.get("violation_count", 0)

        if success_rate < 80:
            recommendations.append("Consider increasing preflight check thoroughness")
            recommendations.append("Review and simplify complex SOP steps")

        if compliance_score < 70:
            recommendations.append("Increase monitoring frequency")
            recommendations.append("Provide additional training on SOP requirements")

        if violation_count > 5:
            recommendations.append("Review violation patterns for process improvements")
            recommendations.append("Consider adjusting violation thresholds")

        if success_rate > 95 and compliance_score > 90:
            recommendations.append(
                "Consider relaxing enforcement level to improve efficiency"
            )

        return recommendations


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Orchestrator Integration")
    parser.add_argument(
        "--integrate", action="store_true", help="Integrate with Orchestrator"
    )
    parser.add_argument(
        "--get-rules", action="store_true", help="Get current adaptive rules"
    )
    parser.add_argument(
        "--update-rules", action="store_true", help="Update rules from patterns"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate compliance report"
    )

    args = parser.parse_args()

    integration = AdaptiveOrchestratorIntegration()

    if args.integrate:
        success = integration.integrate_with_orchestrator()
        sys.exit(0 if success else 1)

    elif args.get_rules:
        rules = integration.get_current_rules()
        print(json.dumps(rules, indent=2))

    elif args.update_rules:
        success = integration.update_rules_from_patterns()
        sys.exit(0 if success else 1)

    elif args.report:
        report = integration.generate_compliance_report()
        print(json.dumps(report, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
