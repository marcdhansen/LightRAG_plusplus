#!/usr/bin/env python3
"""
Enhanced Session Heartbeat with SOP Monitoring Integration

Integrates real-time SOP compliance monitoring with the session heartbeat system.
Provides coordinated monitoring and compliance tracking across agent sessions.

Usage:
    python enhanced_sop_heartbeat.py --start
    python enhanced_sop_heartbeat.py --update
    python enhanced_sop_heartbeat.py --stop
    python enhanced_sop_heartbeat.py --status
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class EnhancedSOPHeartbeat:
    """Enhanced heartbeat system with SOP monitoring integration"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.locks_dir = self.script_dir.parent / "session_locks"
        self.logs_dir = self.script_dir.parent / "logs"
        self.config_dir = self.script_dir.parent / "config"

        # Ensure directories exist
        self.locks_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)

        # Agent info
        self.agent_id = os.environ.get("OPENCODE_AGENT_ID", "unknown")
        self.agent_name = os.environ.get(
            "OPENCODE_AGENT_NAME", os.environ.get("USER", "unknown")
        )
        self.session_id = os.environ.get("OPENCODE_SESSION_ID", str(int(time.time())))
        self.workspace = Path.cwd()
        self.pid = os.getpid()

        # Heartbeat configuration
        self.heartbeat_interval = 300  # 5 minutes
        self.sop_check_interval = 60  # 1 minute
        self.stale_threshold = 600  # 10 minutes

        # State
        self.running = False
        self.heartbeat_thread = None
        self.sop_monitor_thread = None
        self.lock_file = None

        # Find/create lock file
        self.setup_lock_file()

    def setup_lock_file(self):
        """Setup session lock file"""
        # Look for existing lock file
        for lock_file in self.locks_dir.glob(f"agent_{self.agent_id}_*.json"):
            try:
                with open(lock_file) as f:
                    lock_data = json.load(f)

                if lock_data.get("agent_id") == self.agent_id:
                    self.lock_file = lock_file
                    self.session_id = lock_data.get("session_id", self.session_id)
                    break
            except Exception:
                continue

        # Create new lock file if not found
        if not self.lock_file:
            lock_filename = f"agent_{self.agent_id}_{self.session_id}.json"
            self.lock_file = self.locks_dir / lock_filename
            self.create_lock_file()

    def create_lock_file(
        self, task_id: str = "unknown", task_desc: str = "unknown"
    ) -> bool:
        """Create new session lock file"""
        lock_data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "started_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
            "current_task": task_id,
            "task_description": task_desc,
            "pid": self.pid,
            "workspace": str(self.workspace),
            "heartbeat_interval": self.heartbeat_interval,
            "sop_monitoring": {
                "enabled": True,
                "check_interval": self.sop_check_interval,
                "last_check": None,
                "compliance_score": 100.0,
                "violation_count": 0,
                "monitor_pid": None,
            },
            "version": "2.0",
        }

        try:
            if not self.lock_file:
                print("❌ No lock file path available")
                return False

            with open(str(self.lock_file), "w") as f:
                json.dump(lock_data, f, indent=2)

            print(
                f"✅ Enhanced session lock created: {self.lock_file.name if self.lock_file else 'unknown'}"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to create lock file: {e}")
            return False

    def load_lock_data(self) -> dict[str, Any]:
        """Load current lock file data"""
        if not self.lock_file or not self.lock_file.exists():
            return {}

        try:
            with open(str(self.lock_file)) as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_lock_data(self, lock_data: dict[str, Any]) -> None:
        """Save lock file data"""
        if not self.lock_file:
            return
        try:
            if self.lock_file:
                with open(str(self.lock_file), "w") as f:
                    json.dump(lock_data, f, indent=2)
        except Exception:
            pass

    def update_heartbeat(self) -> None:
        """Update heartbeat in lock file"""
        lock_data = self.load_lock_data()
        lock_data["last_heartbeat"] = datetime.utcnow().isoformat()

        # Update SOP monitoring status
        sop_monitoring = lock_data.get("sop_monitoring", {})
        sop_monitoring["last_heartbeat"] = datetime.utcnow().isoformat()
        lock_data["sop_monitoring"] = sop_monitoring

        self.save_lock_data(lock_data)

    def check_sop_compliance(self) -> dict:
        """Check current SOP compliance status"""
        try:
            # Use real-time monitor to get status
            monitor_script = self.script_dir / "realtime_sop_monitor.py"
            if not monitor_script.exists():
                return {"compliance_score": 100.0, "violations": []}

            result = subprocess.run(
                [sys.executable, str(monitor_script), "--status"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                status = json.loads(result.stdout)
                return {
                    "compliance_score": status.get("compliance_score", 100.0),
                    "violation_count": status.get("violation_count", 0),
                    "is_blocked": status.get("should_block", False),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception:
            pass

        return {"compliance_score": 100.0, "violations": []}

    def sop_monitoring_loop(self):
        """Background SOP compliance monitoring loop"""
        print(f"🔍 Started SOP monitoring (interval: {self.sop_check_interval}s)")

        while self.running:
            try:
                # Check SOP compliance
                compliance_status = self.check_sop_compliance()

                # Update lock file with compliance status
                lock_data = self.load_lock_data()
                sop_monitoring = lock_data.get("sop_monitoring", {})
                sop_monitoring.update(
                    {
                        "last_check": compliance_status["timestamp"],
                        "compliance_score": compliance_status["compliance_score"],
                        "violation_count": compliance_status["violation_count"],
                        "is_blocked": compliance_status.get("is_blocked", False),
                    }
                )
                lock_data["sop_monitoring"] = sop_monitoring

                self.save_lock_data(lock_data)

                # Log significant changes
                if compliance_status.get("is_blocked"):
                    print(
                        f"🚫 SOP Block detected (score: {compliance_status['compliance_score']:.1f}%)"
                    )

                # Adaptive monitoring interval based on compliance
                compliance_score = compliance_status["compliance_score"]
                if compliance_score < 70:
                    # Monitor more frequently when compliance is low
                    sleep_interval = self.sop_check_interval // 2
                elif compliance_score > 90:
                    # Monitor less frequently when compliance is high
                    sleep_interval = self.sop_check_interval * 2
                else:
                    sleep_interval = self.sop_check_interval

                time.sleep(sleep_interval)

            except Exception as e:
                print(f"❌ SOP monitoring error: {e}")
                time.sleep(self.sop_check_interval)

    def heartbeat_loop(self):
        """Main heartbeat loop"""
        print(f"💓 Started heartbeat (interval: {self.heartbeat_interval}s)")

        while self.running:
            try:
                self.update_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                time.sleep(30)  # Short retry interval

    def start_monitoring(
        self, task_id: str = "unknown", task_desc: str = "unknown"
    ) -> None:
        """Start enhanced heartbeat with SOP monitoring"""
        if self.running:
            print("⚠️ Enhanced heartbeat already running")
            return

        # Update lock file with task info
        lock_data = self.load_lock_data()
        lock_data["current_task"] = task_id
        lock_data["task_description"] = task_desc
        lock_data["pid"] = self.pid
        self.save_lock_data(lock_data)

        self.running = True

        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(
            target=self.heartbeat_loop, daemon=True
        )
        self.heartbeat_thread.start()

        # Start SOP monitoring thread
        self.sop_monitor_thread = threading.Thread(
            target=self.sop_monitoring_loop, daemon=True
        )
        self.sop_monitor_thread.start()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        print(f"🚀 Enhanced SOP heartbeat started (session: {self.session_id})")
        print(f"📍 Monitoring workspace: {self.workspace}")
        print("🔍 SOP compliance monitoring: enabled")
        print(f"💓 Heartbeat interval: {self.heartbeat_interval}s")
        print(f"🔍 SOP check interval: {self.sop_check_interval}s")

    def stop_monitoring(self):
        """Stop enhanced heartbeat monitoring"""
        if not self.running:
            print("⚠️ Enhanced heartbeat not running")
            return

        self.running = False

        # Wait for threads to finish
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)

        if self.sop_monitor_thread and self.sop_monitor_thread.is_alive():
            self.sop_monitor_thread.join(timeout=5)

        # Update lock file with final status
        lock_data = self.load_lock_data()
        sop_monitoring = lock_data.get("sop_monitoring", {})
        sop_monitoring["enabled"] = False
        sop_monitoring["stopped_at"] = datetime.utcnow().isoformat()
        lock_data["sop_monitoring"] = sop_monitoring
        self.save_lock_data(lock_data)

        print(f"🛑 Enhanced SOP heartbeat stopped (session: {self.session_id})")

    def signal_handler(self, signum, _frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}, shutting down...")
        self.stop_monitoring()
        sys.exit(0)

    def get_status(self) -> dict:
        """Get current enhanced heartbeat status"""
        lock_data = self.load_lock_data()
        sop_monitoring = lock_data.get("sop_monitoring", {})

        status = {
            "session_info": {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "session_id": self.session_id,
                "workspace": str(self.workspace),
                "current_task": lock_data.get("current_task", "unknown"),
                "task_description": lock_data.get("task_description", "unknown"),
            },
            "heartbeat_status": {
                "running": self.running,
                "last_heartbeat": lock_data.get("last_heartbeat"),
                "heartbeat_interval": self.heartbeat_interval,
                "started_at": lock_data.get("started_at"),
            },
            "sop_monitoring_status": {
                "enabled": sop_monitoring.get("enabled", False),
                "last_check": sop_monitoring.get("last_check"),
                "compliance_score": sop_monitoring.get("compliance_score", 100.0),
                "violation_count": sop_monitoring.get("violation_count", 0),
                "is_blocked": sop_monitoring.get("is_blocked", False),
                "check_interval": sop_monitoring.get(
                    "check_interval", self.sop_check_interval
                ),
            },
        }

        return status

    def get_all_sessions_status(self) -> dict:
        """Get status of all active sessions"""
        sessions = []
        now = datetime.utcnow()

        for lock_file in self.locks_dir.glob("agent_*.json"):
            try:
                with open(lock_file) as f:
                    lock_data = json.load(f)

                # Check if session is still active
                last_heartbeat_str = lock_data.get("last_heartbeat")
                is_active = False
                age_seconds = 0.0
                if last_heartbeat_str:
                    last_heartbeat = datetime.fromisoformat(
                        last_heartbeat_str.replace("Z", "+00:00")
                    )
                    age_seconds = (now - last_heartbeat).total_seconds()
                    is_active = age_seconds < self.stale_threshold

                # Extract session info
                sop_monitoring = lock_data.get("sop_monitoring", {})

                session_info = {
                    "agent_id": lock_data.get("agent_id", "unknown"),
                    "agent_name": lock_data.get("agent_name", "unknown"),
                    "session_id": lock_data.get("session_id", "unknown"),
                    "current_task": lock_data.get("current_task", "unknown"),
                    "task_description": lock_data.get("task_description", "unknown"),
                    "is_active": is_active,
                    "last_heartbeat": last_heartbeat_str,
                    "age_seconds": age_seconds if "age_seconds" in locals() else 0,
                    "workspace": lock_data.get("workspace", "unknown"),
                    "sop_monitoring": {
                        "enabled": sop_monitoring.get("enabled", False),
                        "compliance_score": sop_monitoring.get(
                            "compliance_score", 100.0
                        ),
                        "violation_count": sop_monitoring.get("violation_count", 0),
                        "is_blocked": sop_monitoring.get("is_blocked", False),
                    },
                }

                sessions.append(session_info)

            except Exception as e:
                print(f"⚠️ Error reading session {lock_file}: {e}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s["is_active"]]),
            "sessions": sessions,
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced SOP Heartbeat")
    parser.add_argument("--start", action="store_true", help="Start enhanced heartbeat")
    parser.add_argument("--update", action="store_true", help="Update heartbeat only")
    parser.add_argument("--stop", action="store_true", help="Stop enhanced heartbeat")
    parser.add_argument("--status", action="store_true", help="Show heartbeat status")
    parser.add_argument(
        "--all-sessions", action="store_true", help="Show all sessions status"
    )
    parser.add_argument("--task-id", help="Current task ID")
    parser.add_argument("--task-desc", help="Current task description")
    parser.add_argument(
        "--heartbeat-interval", type=int, help="Heartbeat interval in seconds"
    )
    parser.add_argument(
        "--sop-interval", type=int, help="SOP check interval in seconds"
    )

    args = parser.parse_args()

    heartbeat = EnhancedSOPHeartbeat()

    # Override intervals if provided
    if args.heartbeat_interval:
        heartbeat.heartbeat_interval = args.heartbeat_interval

    if args.sop_interval:
        heartbeat.sop_check_interval = args.sop_interval

    if args.start:
        task_id = args.task_id or "unknown"
        task_desc = args.task_desc or "unknown"
        heartbeat.start_monitoring(task_id, task_desc)

        # Keep main thread alive
        try:
            while heartbeat.running:
                time.sleep(1)
        except KeyboardInterrupt:
            heartbeat.stop_monitoring()

    elif args.update:
        heartbeat.update_heartbeat()
        print("💓 Heartbeat updated")

    elif args.stop:
        heartbeat.stop_monitoring()

    elif args.all_sessions:
        status = heartbeat.get_all_sessions_status()
        print(json.dumps(status, indent=2))

    elif args.status:
        status = heartbeat.get_status()
        print(json.dumps(status, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
