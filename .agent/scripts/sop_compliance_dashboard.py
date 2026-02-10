#!/usr/bin/env python3
"""
SOP Compliance Status Dashboard

Web-based dashboard for monitoring real-time SOP compliance across all agent sessions.
Provides visual interface for tracking compliance, violations, and system status.

Usage:
    python sop_compliance_dashboard.py --start --port 8080
    python sop_compliance_dashboard.py --status
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from flask import Flask, jsonify, render_template_string, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    render_template_string = None
    jsonify = None
    request = None
    print("⚠️ Flask not available - dashboard will run in CLI mode")


class SOPComplianceDashboard:
    """SOP Compliance Dashboard for real-time monitoring"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.logs_dir = self.script_dir.parent / "logs"
        self.config_dir = self.script_dir.parent / "config"
        self.locks_dir = self.script_dir.parent / "session_locks"
        self.blocks_dir = self.script_dir.parent / "blocks"

        # Dashboard configuration
        self.dashboard_config_file = self.config_dir / "dashboard_config.json"
        self.config = self.load_dashboard_config()

        # Data cache
        self.cache_timeout = 30  # seconds
        self.last_update = 0
        self.cached_data = {}

        # Initialize Flask if available
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)  # type: ignore
            self.setup_routes()

    def load_dashboard_config(self) -> dict:
        """Load dashboard configuration"""
        default_config = {
            "refresh_interval": 10,  # seconds
            "max_history_hours": 24,
            "alert_threshold": {"compliance_score": 70, "violation_count": 5},
            "display_options": {
                "show_inactive": False,
                "show_details": True,
                "compact_view": False,
            },
            "web": {"host": "localhost", "port": 8080, "debug": False},
        }

        if self.dashboard_config_file.exists():
            try:
                with open(self.dashboard_config_file) as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception:
                pass

        return default_config

    def save_dashboard_config(self):
        """Save dashboard configuration"""
        try:
            with open(self.dashboard_config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def get_monitor_status(self) -> dict:
        """Get real-time monitor status"""
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
        except Exception:
            pass

        return {"running": False}

    def get_blocking_status(self) -> dict:
        """Get blocking mechanism status"""
        try:
            blocker_script = self.script_dir / "sop_blocking_mechanism.py"
            if not blocker_script.exists():
                return {"is_blocked": False}

            result = subprocess.run(
                [sys.executable, str(blocker_script), "--status"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass

        return {"is_blocked": False}

    def get_adaptive_rules_status(self) -> dict:
        """Get adaptive rules status"""
        try:
            integration_script = (
                self.script_dir / "adaptive_orchestrator_integration.py"
            )
            if not integration_script.exists():
                return {"status": "unavailable"}

            result = subprocess.run(
                [sys.executable, str(integration_script), "--report"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass

        return {"status": "unavailable"}

    def get_all_sessions_status(self) -> dict:
        """Get status of all sessions"""
        try:
            heartbeat_script = self.script_dir / "enhanced_sop_heartbeat.py"
            if heartbeat_script.exists():
                result = subprocess.run(
                    [sys.executable, str(heartbeat_script), "--all-sessions"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    return json.loads(result.stdout)
        except Exception:
            pass

        # Fallback to manual session detection
        sessions = []
        now = datetime.utcnow()

        for lock_file in self.locks_dir.glob("agent_*.json"):
            try:
                with open(lock_file) as f:
                    lock_data = json.load(f)

                # Check if session is still active
                last_heartbeat_str = lock_data.get("last_heartbeat")
                is_active = False
                age_seconds = 0

                if last_heartbeat_str:
                    try:
                        last_heartbeat = datetime.fromisoformat(
                            last_heartbeat_str.replace("Z", "+00:00")
                        )
                        age_seconds = (now - last_heartbeat).total_seconds()
                        is_active = age_seconds < 600  # 10 minutes
                    except Exception:
                        pass

                sessions.append(
                    {
                        "agent_id": lock_data.get("agent_id", "unknown"),
                        "agent_name": lock_data.get("agent_name", "unknown"),
                        "session_id": lock_data.get("session_id", "unknown"),
                        "current_task": lock_data.get("current_task", "unknown"),
                        "task_description": lock_data.get(
                            "task_description", "unknown"
                        ),
                        "is_active": is_active,
                        "last_heartbeat": last_heartbeat_str,
                        "age_seconds": age_seconds,
                        "workspace": lock_data.get("workspace", "unknown"),
                        "sop_monitoring": lock_data.get("sop_monitoring", {}),
                    }
                )
            except Exception:
                continue

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s["is_active"]]),
            "sessions": sessions,
        }

    def get_violation_history(self, hours: int = 24) -> list[dict]:
        """Get violation history for specified hours"""
        violations = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Check monitor logs
        for log_file in self.logs_dir.glob("realtime_sop_monitor_*.log"):
            try:
                with open(log_file) as f:
                    for line in f:
                        if "VIOLATION" in line:
                            # Parse timestamp from log entry
                            try:
                                timestamp_str = line.split("[")[1].split("]")[0]
                                log_time = datetime.strptime(timestamp_str, "%H:%M:%S")
                                log_date = datetime.combine(
                                    datetime.fromtimestamp(
                                        log_file.stat().st_mtime
                                    ).date(),
                                    log_time.time(),
                                )

                                if log_date > cutoff_time:
                                    violations.append(
                                        {
                                            "timestamp": log_date.isoformat(),
                                            "source": "realtime_monitor",
                                            "details": line.strip(),
                                        }
                                    )
                            except Exception:
                                continue
            except Exception:
                continue

        # Check block history
        if self.blocks_dir and self.blocks_dir.exists():
            block_history_file = self.blocks_dir / "block_history.jsonl"
            if block_history_file.exists():
                try:
                    with open(block_history_file) as f:
                        for line in f:
                            if line.strip():
                                try:
                                    block_data = json.loads(line)
                                    block_time = datetime.fromisoformat(
                                        block_data["timestamp"]
                                    )
                                    if block_time > cutoff_time:
                                        violations.append(
                                            {
                                                "timestamp": block_time.isoformat(),
                                                "source": "blocking_mechanism",
                                                "severity": block_data.get(
                                                    "severity", "unknown"
                                                ),
                                                "reason": block_data.get(
                                                    "reason", "unknown"
                                                ),
                                                "violation_types": block_data.get(
                                                    "violation_types", []
                                                ),
                                            }
                                        )
                                except Exception:
                                    continue
                except Exception:
                    pass

        return sorted(violations, key=lambda x: x["timestamp"], reverse=True)

    def get_dashboard_data(self) -> dict:
        """Get comprehensive dashboard data"""
        current_time = time.time()

        # Use cache if fresh
        if current_time - self.last_update < self.cache_timeout and self.cached_data:
            return self.cached_data

        # Gather all data
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": {
                "monitor": self.get_monitor_status(),
                "blocker": self.get_blocking_status(),
                "adaptive_rules": self.get_adaptive_rules_status(),
            },
            "sessions": self.get_all_sessions_status(),
            "violations": self.get_violation_history(self.config["max_history_hours"]),
            "metrics": self.calculate_metrics(),
            "config": self.config,
        }

        # Update cache
        self.cached_data = dashboard_data
        self.last_update = current_time

        return dashboard_data

    def calculate_metrics(self) -> dict:
        """Calculate dashboard metrics"""
        sessions_data = self.get_all_sessions_status()
        self.get_monitor_status()

        metrics = {
            "compliance_scores": [],
            "active_agents": sessions_data.get("active_sessions", 0),
            "total_violations": len(self.get_violation_history(24)),
            "system_health": "good",
        }

        # Collect compliance scores
        for session in sessions_data.get("sessions", []):
            sop_monitoring = session.get("sop_monitoring", {})
            compliance_score = sop_monitoring.get("compliance_score", 100.0)
            metrics["compliance_scores"].append(compliance_score)

        # Calculate average compliance
        if metrics["compliance_scores"]:
            metrics["avg_compliance"] = sum(metrics["compliance_scores"]) / len(
                metrics["compliance_scores"]
            )
            metrics["min_compliance"] = min(metrics["compliance_scores"])
            metrics["max_compliance"] = max(metrics["compliance_scores"])
        else:
            metrics["avg_compliance"] = 100.0
            metrics["min_compliance"] = 100.0
            metrics["max_compliance"] = 100.0

        # Determine system health
        if (
            metrics["avg_compliance"]
            < self.config["alert_threshold"]["compliance_score"]
            or metrics["total_violations"]
            > self.config["alert_threshold"]["violation_count"]
        ):
            metrics["system_health"] = "warning"

        if metrics["avg_compliance"] < 50 or metrics["total_violations"] > 20:
            metrics["system_health"] = "critical"

        return metrics

    def setup_routes(self):
        """Setup Flask routes for web dashboard"""
        if not FLASK_AVAILABLE or not self.app:
            return

        @self.app.route("/")
        def index():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_HTML, config=self.config)  # type: ignore

        @self.app.route("/api/status")
        def api_status():
            """API endpoint for current status"""
            return jsonify(self.get_dashboard_data())  # type: ignore

        @self.app.route("/api/sessions")
        def api_sessions():
            """API endpoint for sessions"""
            return jsonify(self.get_all_sessions_status())  # type: ignore

        @self.app.route("/api/violations")
        def api_violations():
            """API endpoint for violations"""
            hours = request.args.get("hours", 24, type=int)  # type: ignore
            return jsonify(self.get_violation_history(hours))  # type: ignore

        @self.app.route("/api/metrics")
        def api_metrics():
            """API endpoint for metrics"""
            return jsonify(self.calculate_metrics())  # type: ignore

    def start_web_dashboard(self, host: str | None = None, port: int | None = None):
        """Start web dashboard"""
        if not FLASK_AVAILABLE or not self.app:
            print("❌ Flask not available - cannot start web dashboard")
            return False

        host = host or self.config["web"]["host"]
        port = port or self.config["web"]["port"]

        print("🚀 Starting SOP Compliance Dashboard")
        print(f"🌐 URL: http://{host}:{port}")
        print(f"📊 Refresh interval: {self.config['refresh_interval']}s")

        try:
            self.app.run(
                host=host, port=port, debug=self.config["web"]["debug"], threaded=True
            )
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
        except Exception as e:
            print(f"❌ Failed to start dashboard: {e}")
            return False

        return True

    def show_cli_dashboard(self):
        """Show CLI dashboard"""
        while True:
            try:
                data = self.get_dashboard_data()
                self.print_cli_dashboard(data)
                time.sleep(self.config["refresh_interval"])
            except KeyboardInterrupt:
                print("\n🛑 Dashboard stopped")
                break

    def print_cli_dashboard(self, data: dict):
        """Print dashboard to CLI"""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        print("=" * 80)
        print(
            f"🔍 SOP COMPLIANCE DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 80)
        print()

        # System Status
        print("📊 SYSTEM STATUS")
        print("-" * 40)
        monitor_status = data["system_status"]["monitor"]
        blocker_status = data["system_status"]["blocker"]

        print(
            f"Monitor: {'✅ Running' if monitor_status.get('running') else '❌ Stopped'}"
        )
        print(
            f"Blocking: {'🚫 Active' if blocker_status.get('is_blocked') else '✅ Clear'}"
        )
        print(
            f"Health: {self.get_health_emoji(data['metrics']['system_health'])} {data['metrics']['system_health'].upper()}"
        )
        print()

        # Sessions
        sessions_data = data["sessions"]
        print(
            f"👥 SESSIONS ({sessions_data['active_sessions']}/{sessions_data['total_sessions']} active)"
        )
        print("-" * 40)

        for session in sessions_data["sessions"][:10]:  # Show top 10
            if (
                not session["is_active"]
                and not self.config["display_options"]["show_inactive"]
            ):
                continue

            status_emoji = "💚" if session["is_active"] else "⚪"
            agent_name = session["agent_name"][:15]
            task = session["current_task"][:20]

            sop_monitoring = session.get("sop_monitoring", {})
            compliance = sop_monitoring.get("compliance_score", 100.0)
            compliance_emoji = self.get_compliance_emoji(compliance)

            print(
                f"{status_emoji} {agent_name:<15} {task:<20} {compliance_emoji} {compliance:5.1f}%"
            )

        print()

        # Recent Violations
        violations = data["violations"][:5]  # Show last 5
        print(f"⚠️  RECENT VIOLATIONS ({len(data['violations'])} total)")
        print("-" * 40)

        if violations:
            for violation in violations:
                timestamp = violation["timestamp"][-8:]  # Time only
                source = violation["source"][:15]
                details = violation.get("reason", violation.get("details", ""))[:40]
                print(f"🕐 {timestamp} {source:<15} {details}")
        else:
            print("✅ No violations in last 24h")

        print()
        print("Press Ctrl+C to exit")

    def get_health_emoji(self, health: str) -> str:
        """Get emoji for health status"""
        return {"good": "💚", "warning": "💛", "critical": "❤️"}.get(health, "❓")

    def get_compliance_emoji(self, score: float) -> str:
        """Get emoji for compliance score"""
        if score >= 90:
            return "💚"
        elif score >= 70:
            return "💛"
        else:
            return "❤️"


# HTML template for web dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOP Compliance Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .status-item { text-align: center; padding: 15px; border-radius: 8px; }
        .status-good { background: #d4edda; color: #155724; }
        .status-warning { background: #fff3cd; color: #856404; }
        .status-critical { background: #f8d7da; color: #721c24; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
        .compliance-good { color: #28a745; }
        .compliance-warning { color: #ffc107; }
        .compliance-critical { color: #dc3545; }
        .refresh-info { text-align: center; color: #666; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 SOP Compliance Dashboard</h1>
        <p>Real-time monitoring of Standard Operating Procedure compliance across all agent sessions</p>
    </div>

    <div class="status-grid">
        <div class="card">
            <h3>System Health</h3>
            <div id="system-health" class="status-item">Loading...</div>
        </div>
        <div class="card">
            <h3>Active Sessions</h3>
            <div id="active-sessions" class="status-item">Loading...</div>
        </div>
        <div class="card">
            <h3>Avg Compliance</h3>
            <div id="avg-compliance" class="status-item">Loading...</div>
        </div>
        <div class="card">
            <h3>Recent Violations</h3>
            <div id="violation-count" class="status-item">Loading...</div>
        </div>
    </div>

    <div class="card">
        <h2>👥 Active Sessions</h2>
        <table id="sessions-table">
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Task</th>
                    <th>Compliance</th>
                    <th>Status</th>
                    <th>Last Activity</th>
                </tr>
            </thead>
            <tbody id="sessions-tbody">
                <tr><td colspan="5">Loading sessions data...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>⚠️ Recent Violations</h2>
        <table id="violations-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Source</th>
                    <th>Severity</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody id="violations-tbody">
                <tr><td colspan="4">Loading violations data...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="refresh-info">
        <p>Auto-refresh every {{ config.refresh_interval }} seconds | Last updated: <span id="last-update">Loading...</span></p>
    </div>

    <script>
        let updateInterval = {{ config.refresh_interval * 1000 }};

        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(data.metrics);
                    updateSessions(data.sessions);
                    updateViolations(data.violations);
                    document.getElementById('last-update').textContent = new Date().toLocaleString();
                })
                .catch(error => console.error('Error updating dashboard:', error));
        }

        function updateSystemStatus(metrics) {
            const healthEl = document.getElementById('system-health');
            const sessionsEl = document.getElementById('active-sessions');
            const complianceEl = document.getElementById('avg-compliance');
            const violationsEl = document.getElementById('violation-count');

            healthEl.className = `status-item status-${metrics.system_health}`;
            healthEl.textContent = metrics.system_health.toUpperCase();

            sessionsEl.className = 'status-item status-good';
            sessionsEl.textContent = metrics.active_agents;

            const complianceClass = metrics.avg_compliance >= 90 ? 'good' :
                                 metrics.avg_compliance >= 70 ? 'warning' : 'critical';
            complianceEl.className = `status-item status-${complianceClass}`;
            complianceEl.textContent = `${metrics.avg_compliance.toFixed(1)}%`;

            violationsEl.className = 'status-item status-good';
            violationsEl.textContent = metrics.total_violations;
        }

        function updateSessions(sessions) {
            const tbody = document.getElementById('sessions-tbody');
            tbody.innerHTML = '';

            sessions.sessions.forEach(session => {
                const row = tbody.insertRow();
                const compliance = session.sop_monitoring.compliance_score || 100;
                const complianceClass = compliance >= 90 ? 'good' :
                                      compliance >= 70 ? 'warning' : 'critical';

                row.innerHTML = `
                    <td>${session.agent_name}</td>
                    <td>${session.current_task}</td>
                    <td class="compliance-${complianceClass}">${compliance.toFixed(1)}%</td>
                    <td>${session.is_active ? '💚 Active' : '⚪ Inactive'}</td>
                    <td>${new Date(session.last_heartbeat).toLocaleString()}</td>
                `;
            });
        }

        function updateViolations(violations) {
            const tbody = document.getElementById('violations-tbody');
            tbody.innerHTML = '';

            if (violations.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">✅ No violations in last 24h</td></tr>';
                return;
            }

            violations.slice(0, 20).forEach(violation => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${new Date(violation.timestamp).toLocaleString()}</td>
                    <td>${violation.source}</td>
                    <td>${violation.severity || 'N/A'}</td>
                    <td>${violation.reason || violation.details || 'N/A'}</td>
                `;
            });
        }

        // Initial update
        updateDashboard();

        // Set up auto-refresh
        setInterval(updateDashboard, updateInterval);
    </script>
</body>
</html>
"""


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SOP Compliance Dashboard")
    parser.add_argument("--start", action="store_true", help="Start dashboard")
    parser.add_argument("--cli", action="store_true", help="Start CLI dashboard")
    parser.add_argument("--host", default="localhost", help="Host for web dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port for web dashboard")
    parser.add_argument("--refresh", type=int, help="Refresh interval in seconds")
    parser.add_argument("--status", action="store_true", help="Show current status")

    args = parser.parse_args()

    dashboard = SOPComplianceDashboard()

    # Override config with command line args
    if args.refresh:
        dashboard.config["refresh_interval"] = args.refresh

    if args.status:
        data = dashboard.get_dashboard_data()
        print(json.dumps(data, indent=2))

    elif args.start and FLASK_AVAILABLE:
        dashboard.start_web_dashboard(args.host, args.port)

    elif args.cli:
        dashboard.show_cli_dashboard()

    else:
        if FLASK_AVAILABLE:
            print("🚀 Starting SOP Compliance Dashboard (Web mode)")
            dashboard.start_web_dashboard(args.host, args.port)
        else:
            print("📊 Starting SOP Compliance Dashboard (CLI mode)")
            dashboard.show_cli_dashboard()


if __name__ == "__main__":
    main()
