#!/usr/bin/env python3
"""
Real-time SOP Compliance Monitor

Enhanced monitoring system for continuous SOP compliance checking with adaptive intervals.
Integrates with existing adaptive SOP engine and provides real-time feedback.

Features:
- Adaptive monitoring intervals (15s-300s based on performance)
- Real-time violation detection and alerting
- Integration with session heartbeat system
- Configurable compliance thresholds
- Performance-based adaptation
"""

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import requests


class SOPComplianceMonitor:
    """Real-time SOP compliance monitoring with adaptive intervals."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or ".agent/config/realtime_monitor_config.json"
        self.config = self._load_config()

        # Initialize adaptive parameters
        self.current_interval = self.config["check_interval_seconds"]
        self.min_interval = self.config["adaptive_config"]["min_check_interval"]
        self.max_interval = self.config["adaptive_config"]["max_check_interval"]
        self.success_rate_threshold = self.config["adaptive_config"][
            "success_rate_threshold"
        ]

        # Performance tracking for adaptation
        self.performance_history = deque(
            maxlen=self.config["adaptive_config"]["violation_history_limit"]
        )
        self.violation_history = deque(maxlen=50)
        self.last_check_time = None

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.violation_callbacks = []

        # Logging
        self.logger = self._setup_logging()
        self.log_dir = Path(".agent/logs")
        self.log_dir.mkdir(exist_ok=True)

        # State persistence
        self.state_file = self.log_dir / "sop_monitor_state.json"
        self.violations_file = self.log_dir / "sop_violations.jsonl"

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config from {self.config_path}: {e}")
            # Return default configuration
            return {
                "check_interval_seconds": 30,
                "violation_threshold": 3,
                "adaptive_config": {
                    "min_check_interval": 15,
                    "max_check_interval": 300,
                    "violation_history_limit": 50,
                    "success_rate_threshold": 80,
                },
                "monitoring_checks": {
                    "git_status": True,
                    "session_locks": True,
                    "mandatory_skills": True,
                    "tdd_compliance": True,
                    "documentation_integrity": True,
                    "beads_connectivity": True,
                },
            }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the monitor."""
        logger = logging.getLogger("sop_compliance_monitor")
        logger.setLevel(logging.INFO)

        # Create handler if not exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def add_violation_callback(self, callback):
        """Add callback function for violation notifications."""
        self.violation_callbacks.append(callback)

    def _check_sop_compliance(self) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Perform comprehensive SOP compliance check."""
        violations = []
        check_results = {}

        # Git status check
        if self.config["monitoring_checks"]["git_status"]:
            git_status = self._check_git_status()
            check_results["git_status"] = git_status
            if not git_status["clean"]:
                violations.append("Git status is not clean")

        # Session locks check
        if self.config["monitoring_checks"]["session_locks"]:
            session_locks = self._check_session_locks()
            check_results["session_locks"] = session_locks
            if not session_locks["valid"]:
                violations.append("Session lock issues detected")

        # Mandatory skills check
        if self.config["monitoring_checks"]["mandatory_skills"]:
            mandatory_skills = self._check_mandatory_skills()
            check_results["mandatory_skills"] = mandatory_skills
            if not mandatory_skills["compliant"]:
                violations.extend(mandatory_skills["missing"])

        # TDD compliance check
        if self.config["monitoring_checks"]["tdd_compliance"]:
            tdd_compliance = self._check_tdd_compliance()
            check_results["tdd_compliance"] = tdd_compliance
            if not tdd_compliance["compliant"]:
                violations.extend(tdd_compliance["violations"])

        # Documentation integrity check
        if self.config["monitoring_checks"]["documentation_integrity"]:
            doc_integrity = self._check_documentation_integrity()
            check_results["documentation_integrity"] = doc_integrity
            if not doc_integrity["clean"]:
                violations.append("Documentation integrity issues")

        # Beads connectivity check
        if self.config["monitoring_checks"]["beads_connectivity"]:
            beads_connectivity = self._check_beads_connectivity()
            check_results["beads_connectivity"] = beads_connectivity
            if not beads_connectivity["connected"]:
                violations.append("Beads connectivity issues")

        is_compliant = len(violations) < self.config["violation_threshold"]
        return is_compliant, violations, check_results

    def _check_git_status(self) -> Dict[str, Any]:
        """Check git repository status."""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            is_clean = len(result.stdout.strip()) == 0
            return {
                "clean": is_clean,
                "changes": result.stdout.strip().split("\n") if not is_clean else [],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Git status check failed: {e}")
            return {
                "clean": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _check_session_locks(self) -> Dict[str, Any]:
        """Check session lock validity."""
        try:
            locks_dir = Path(".agent/session_locks")
            if not locks_dir.exists():
                return {"valid": True, "message": "No locks directory"}

            lock_files = list(locks_dir.glob("*.json"))
            now = datetime.now()
            stale_locks = []

            for lock_file in lock_files:
                try:
                    with open(lock_file) as f:
                        lock_data = json.load(f)

                    last_heartbeat = datetime.fromisoformat(
                        lock_data.get(
                            "last_heartbeat",
                            lock_data.get("created_at", now.isoformat()),
                        )
                    )

                    # Lock is stale if no heartbeat for 10 minutes
                    if (now - last_heartbeat).total_seconds() > 600:
                        stale_locks.append(lock_file.name)
                except Exception:
                    # Invalid lock file
                    stale_locks.append(lock_file.name)

            return {
                "valid": len(stale_locks) == 0,
                "stale_locks": stale_locks,
                "total_locks": len(lock_files),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Session locks check failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _check_mandatory_skills(self) -> Dict[str, Any]:
        """Check mandatory skills usage."""
        try:
            log_dir = Path(".agent/logs")
            missing_skills = []

            # Check reflection usage
            reflection_log = log_dir / "reflections.json"
            if not reflection_log.exists():
                missing_skills.append("No reflection log found")
            else:
                try:
                    with open(reflection_log) as f:
                        reflections = json.load(f)
                    if not reflections:
                        missing_skills.append("No reflections recorded")
                except Exception:
                    missing_skills.append("Invalid reflection log")

            # Check planning usage for development
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "diff", "--name-only"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Development changes detected, check for planning
                    planning_indicators = [
                        "PLAN_APPROVAL",
                        "task.md",
                        "implementation_plan.md",
                    ]
                    planning_found = any(
                        Path.cwd().rglob(indicator) for indicator in planning_indicators
                    )
                    if not planning_found:
                        missing_skills.append("Development without planning detected")
            except Exception:
                pass

            return {
                "compliant": len(missing_skills) == 0,
                "missing": missing_skills,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Mandatory skills check failed: {e}")
            return {
                "compliant": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _check_tdd_compliance(self) -> Dict[str, Any]:
        """Check TDD compliance."""
        try:
            tdd_script = Path(".agent/scripts/validate_tdd_compliance.sh")
            if not tdd_script.exists():
                return {
                    "compliant": False,
                    "violations": ["TDD validation script not found"],
                }

            # Check recent TDD validation
            tdd_log = Path(".agent/logs/tdd_validation.log")
            if tdd_log.exists():
                try:
                    stat = tdd_log.stat()
                    # Check if validation was run recently (within 2 hours)
                    if (time.time() - stat.st_mtime) < 7200:
                        with open(tdd_log) as f:
                            log_content = f.read()
                        if "✅ TDD compliance validated" in log_content:
                            return {
                                "compliant": True,
                                "violations": [],
                                "timestamp": datetime.now().isoformat(),
                            }
                        elif "❌ TDD compliance FAILED" in log_content:
                            return {
                                "compliant": False,
                                "violations": ["TDD validation failed"],
                                "timestamp": datetime.now().isoformat(),
                            }
                except Exception:
                    pass

            return {
                "compliant": False,
                "violations": ["TDD validation not current"],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"TDD compliance check failed: {e}")
            return {
                "compliant": False,
                "violations": [f"TDD check error: {e}"],
                "timestamp": datetime.now().isoformat(),
            }

    def _check_documentation_integrity(self) -> Dict[str, Any]:
        """Check documentation integrity (no duplicates)."""
        try:
            import subprocess

            result = subprocess.run(
                [".agent/scripts/verify_markdown_duplicates.sh"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "clean": result.returncode == 0,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Documentation integrity check failed: {e}")
            return {
                "clean": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _check_beads_connectivity(self) -> Dict[str, Any]:
        """Check beads system connectivity."""
        try:
            import subprocess

            result = subprocess.run(
                ["bd", "ready"], capture_output=True, text=True, timeout=10
            )
            return {
                "connected": result.returncode == 0,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Beads connectivity check failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _adapt_interval(self, is_compliant: bool, violations_count: int):
        """Adapt monitoring interval based on performance."""
        # Record performance
        self.performance_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "compliant": is_compliant,
                "violations": violations_count,
            }
        )

        # Calculate success rate over recent history
        if len(self.performance_history) >= 5:
            recent_checks = list(self.performance_history)[-10:]
            success_rate = (
                sum(1 for check in recent_checks if check["compliant"])
                / len(recent_checks)
                * 100
            )

            # Adapt interval based on success rate
            if success_rate >= self.success_rate_threshold:
                # High compliance, can increase interval (less frequent checks)
                new_interval = min(self.current_interval * 1.2, self.max_interval)
            else:
                # Low compliance, decrease interval (more frequent checks)
                new_interval = max(self.current_interval * 0.8, self.min_interval)

            if new_interval != self.current_interval:
                self.current_interval = new_interval
                self.logger.info(
                    f"Adapted monitoring interval to {self.current_interval:.1f}s "
                    f"(success rate: {success_rate:.1f}%)"
                )

    def _log_violation(self, violations: List[str], check_results: Dict[str, Any]):
        """Log violation details."""
        violation_entry = {
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "check_results": check_results,
            "interval": self.current_interval,
        }

        # Write to violations log
        with open(self.violations_file, "a") as f:
            f.write(json.dumps(violation_entry) + "\n")

        # Call violation callbacks
        for callback in self.violation_callbacks:
            try:
                callback(violation_entry)
            except Exception as e:
                self.logger.error(f"Violation callback failed: {e}")

    def _save_state(self):
        """Save current monitoring state."""
        state = {
            "monitoring_active": self.monitoring_active,
            "current_interval": self.current_interval,
            "last_check": self.last_check_time.isoformat()
            if self.last_check_time
            else None,
            "performance_history": list(self.performance_history),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load previous monitoring state."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file) as f:
                state = json.load(f)

            self.current_interval = state.get(
                "current_interval", self.config["check_interval_seconds"]
            )
            last_check = state.get("last_check")
            if last_check:
                self.last_check_time = datetime.fromisoformat(last_check)

            # Load performance history
            history_data = state.get("performance_history", [])
            self.performance_history.extend(
                [
                    {
                        "timestamp": entry["timestamp"],
                        "compliant": entry["compliant"],
                        "violations": entry["violations"],
                    }
                    for entry in history_data
                ]
            )
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")

    def _monitoring_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting real-time SOP compliance monitoring")
        self.logger.info(f"Initial check interval: {self.current_interval}s")

        while self.monitoring_active:
            try:
                start_time = time.time()

                # Perform compliance check
                is_compliant, violations, check_results = self._check_sop_compliance()

                # Record violation if any
                if not is_compliant:
                    self.violation_history.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "violations": violations,
                            "check_results": check_results,
                        }
                    )
                    self._log_violation(violations, check_results)

                    self.logger.warning(f"SOP violations detected: {len(violations)}")
                    for violation in violations:
                        self.logger.warning(f"  - {violation}")
                else:
                    self.logger.debug("SOP compliance check passed")

                # Adapt monitoring interval
                self._adapt_interval(is_compliant, len(violations))

                # Update state
                self.last_check_time = datetime.now()
                self._save_state()

                # Sleep until next check (accounting for check duration)
                check_duration = time.time() - start_time
                sleep_time = max(self.current_interval - check_duration, 1)
                time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.current_interval)

    def start_monitoring(self):
        """Start the real-time monitoring."""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        # Load previous state
        self._load_state()

        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitor_thread.start()

        self.logger.info("Real-time SOP compliance monitoring started")

    def stop_monitoring(self):
        """Stop the real-time monitoring."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)

        self.logger.info("Real-time SOP compliance monitoring stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "current_interval": self.current_interval,
            "last_check": self.last_check_time.isoformat()
            if self.last_check_time
            else None,
            "recent_violations": len(self.violation_history),
            "performance_history_size": len(self.performance_history),
            "config": self.config,
        }

    def get_recent_violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent violations."""
        return list(self.violation_history)[-limit:]


def main():
    """CLI interface for the SOP compliance monitor."""
    import argparse

    parser = argparse.ArgumentParser(description="Real-time SOP Compliance Monitor")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument(
        "--violations", action="store_true", help="Show recent violations"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run single compliance check"
    )

    args = parser.parse_args()

    monitor = SOPComplianceMonitor(args.config)

    if args.status:
        status = monitor.get_status()
        print(json.dumps(status, indent=2))
    elif args.violations:
        violations = monitor.get_recent_violations()
        print(json.dumps(violations, indent=2))
    elif args.test:
        is_compliant, violations, check_results = monitor._check_sop_compliance()
        print(f"Compliant: {is_compliant}")
        print(f"Violations: {violations}")
        print(f"Results: {json.dumps(check_results, indent=2)}")
    else:
        # Start monitoring
        monitor.start_monitoring()
        if not args.daemon:
            try:
                print(
                    "Real-time SOP compliance monitoring started. Press Ctrl+C to stop."
                )
                while monitor.monitoring_active:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitor.stop_monitoring()


if __name__ == "__main__":
    main()
