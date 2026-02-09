#!/usr/bin/env python3
"""
Interactive Compliance Dashboard

Web-based and CLI dashboard for real-time SOP compliance monitoring.
Provides visual interface for monitoring compliance status across all agent sessions.

Features:
- Real-time compliance status display
- Interactive violation tracking
- Historical performance metrics
- Configurable alerts and notifications
- CLI fallback when web interface unavailable
"""

import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from flask import Flask, render_template_string, jsonify, request
    import socketio

    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

from realtime_sop_monitor import SOPComplianceMonitor


class ComplianceDashboard:
    """Interactive compliance dashboard with web and CLI interfaces."""

    def __init__(
        self, monitor: Optional[SOPComplianceMonitor] = None, port: int = 8080
    ):
        self.monitor = monitor or SOPComplianceMonitor()
        self.port = port
        self.web_available = WEB_AVAILABLE

        # Dashboard state
        self.dashboard_active = False
        self.web_thread = None
        self.cli_thread = None
        self.shutdown_event = threading.Event()

        # Performance data
        self.historical_data = []
        self.alert_threshold = 70  # Compliance percentage

        # Setup logging
        self.logger = logging.getLogger("compliance_dashboard")

    def _setup_web_interface(self):
        """Setup Flask web interface if available."""
        if not self.web_available:
            return None

        app = Flask(__name__)
        sio = socketio.Server(cors_allowed_origins="*", async_mode="threading")
        app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

        # HTML template for dashboard
        DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SOP Compliance Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .status-card { padding: 20px; border-radius: 8px; text-align: center; }
        .status-good { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .status-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .chart-container { margin: 20px 0; }
        .violations { max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; }
        .violation-item { padding: 10px; border-bottom: 1px solid #eee; }
        .violation-last { border-bottom: none; }
        .timestamp { font-size: 0.8em; color: #666; }
        .metric { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .label { font-size: 0.9em; color: #666; }
        .refresh-info { text-align: center; margin: 20px 0; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ SOP Compliance Dashboard</h1>
            <div class="refresh-info" id="refreshInfo">Real-time updates enabled</div>
        </div>
        
        <div class="status-grid">
            <div class="status-card" id="overallStatus">
                <div class="label">Overall Compliance</div>
                <div class="metric" id="overallMetric">--%</div>
            </div>
            <div class="status-card" id="monitoringStatus">
                <div class="label">Monitoring Status</div>
                <div class="metric" id="monitoringMetric">--</div>
            </div>
            <div class="status-card" id="violationStatus">
                <div class="label">Recent Violations</div>
                <div class="metric" id="violationMetric">--</div>
            </div>
            <div class="status-card" id="intervalStatus">
                <div class="label">Check Interval</div>
                <div class="metric" id="intervalMetric">--s</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="complianceChart" width="400" height="200"></canvas>
        </div>
        
        <h3>📋 Recent Violations</h3>
        <div class="violations" id="violationsList">
            <div class="violation-item">Loading violations...</div>
        </div>
    </div>

    <script>
        const socket = io();
        const ctx = document.getElementById('complianceChart').getContext('2d');
        
        const complianceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Compliance %',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Compliance %'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
        
        function updateDashboard(data) {
            // Update status cards
            const overallEl = document.getElementById('overallStatus');
            const overallMetric = document.getElementById('overallMetric');
            const compliance = data.overall_compliance || 0;
            
            overallMetric.textContent = compliance.toFixed(1) + '%';
            if (compliance >= 90) {
                overallEl.className = 'status-card status-good';
            } else if (compliance >= 70) {
                overallEl.className = 'status-card status-warning';
            } else {
                overallEl.className = 'status-card status-danger';
            }
            
            document.getElementById('monitoringMetric').textContent = data.monitoring_active ? 'Active' : 'Inactive';
            document.getElementById('violationMetric').textContent = data.recent_violations || 0;
            document.getElementById('intervalMetric').textContent = (data.current_interval || 0).toFixed(1) + 's';
            
            // Update monitoring status
            const monitoringEl = document.getElementById('monitoringStatus');
            if (data.monitoring_active) {
                monitoringEl.className = 'status-card status-good';
            } else {
                monitoringEl.className = 'status-card status-danger';
            }
            
            // Update violations list
            const violationsList = document.getElementById('violationsList');
            if (data.recent_violation_details && data.recent_violation_details.length > 0) {
                violationsList.innerHTML = data.recent_violation_details.map(v => 
                    `<div class="violation-item violation-last">
                        <strong>Violations:</strong> ${v.violations.join(', ')}
                        <div class="timestamp">${new Date(v.timestamp).toLocaleString()}</div>
                    </div>`
                ).join('');
            } else {
                violationsList.innerHTML = '<div class="violation-item violation-last">No recent violations</div>';
            }
            
            // Update chart
            if (data.historical_data) {
                const now = new Date();
                complianceChart.data.labels.push(now.toLocaleTimeString());
                complianceChart.data.datasets[0].data.push(compliance);
                
                // Keep only last 20 data points
                if (complianceChart.data.labels.length > 20) {
                    complianceChart.data.labels.shift();
                    complianceChart.data.datasets[0].data.shift();
                }
                
                complianceChart.update('none');
            }
        }
        
        socket.on('compliance_update', updateDashboard);
        
        // Request initial data
        socket.on('connect', () => {
            socket.emit('request_update');
        });
        
        // Auto-refresh every 30 seconds if socket fails
        setInterval(() => {
            if (socket.disconnected) {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(updateDashboard)
                    .catch(console.error);
            }
        }, 30000);
    </script>
</body>
</html>
        """

        @app.route("/")
        def dashboard():
            """Serve main dashboard page."""
            return render_template_string(DASHBOARD_TEMPLATE)

        @app.route("/api/status")
        def api_status():
            """API endpoint for current status."""
            return jsonify(self._get_dashboard_data())

        @sio.event
        def connect():
            """Handle client connection."""
            sio.emit("compliance_update", self._get_dashboard_data())

        @sio.event
        def request_update():
            """Handle update request."""
            sio.emit("compliance_update", self._get_dashboard_data())

        return app, sio

    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        # Get monitor status
        monitor_status = self.monitor.get_status()

        # Calculate overall compliance
        recent_violations = self.monitor.get_recent_violations(10)
        compliance_percentage = max(0, 100 - (len(recent_violations) * 10))

        return {
            "overall_compliance": compliance_percentage,
            "monitoring_active": monitor_status["monitoring_active"],
            "current_interval": monitor_status["current_interval"],
            "recent_violations": len(recent_violations),
            "recent_violation_details": [
                {"timestamp": v["timestamp"], "violations": v["violations"]}
                for v in recent_violations[-5:]
            ],
            "historical_data": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _web_server_loop(self, app, sio):
        """Web server main loop."""
        if not app:
            return

        try:
            # Run with eventlet if available for better performance
            import eventlet

            eventlet.monkey_patch()
            eventlet.wsgi.server(eventlet.listen(("", self.port)), app)
        except ImportError:
            # Fallback to standard Flask server
            app.run(host="0.0.0.0", port=self.port, debug=False, threaded=True)
        except Exception as e:
            self.logger.error(f"Web server error: {e}")

    def _cli_dashboard_loop(self):
        """CLI dashboard main loop."""
        print("🛡️ SOP Compliance Dashboard (CLI Mode)")
        print("=" * 60)
        print("Press Ctrl+C to exit")
        print()

        while not self.shutdown_event.is_set():
            try:
                # Clear screen
                os.system("clear" if os.name == "posix" else "cls")

                # Get dashboard data
                data = self._get_dashboard_data()

                # Display dashboard
                print("🛡️ SOP Compliance Dashboard (CLI Mode)")
                print("=" * 60)
                print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()

                # Status cards
                compliance = data["overall_compliance"]
                status_symbol = (
                    "✅" if compliance >= 90 else "⚠️" if compliance >= 70 else "❌"
                )

                print(f"📊 Overall Compliance: {status_symbol} {compliance:.1f}%")
                print(
                    f"🔄 Monitoring Status: {'Active' if data['monitoring_active'] else 'Inactive'}"
                )
                print(f"📋 Recent Violations: {data['recent_violations']}")
                print(f"⏱️  Check Interval: {data['current_interval']:.1f}s")
                print()

                # Recent violations
                print("📋 Recent Violations:")
                print("-" * 40)
                if data["recent_violation_details"]:
                    for violation in data["recent_violation_details"][-3:]:
                        timestamp = datetime.fromisoformat(
                            violation["timestamp"]
                        ).strftime("%H:%M:%S")
                        print(f"⏰ {timestamp}")
                        for v in violation["violations"]:
                            print(f"  ❌ {v}")
                        print()
                else:
                    print("✅ No recent violations")
                    print()

                # Performance metrics
                print("📈 Performance Metrics:")
                print("-" * 40)
                monitor_status = self.monitor.get_status()
                print(
                    f"📊 Performance History: {monitor_status['performance_history_size']} checks"
                )
                print(f"🔧 Config: Adaptive intervals enabled")
                print(
                    f"🌐 Web Interface: Available at http://localhost:{self.port}"
                    if self.web_available
                    else "🌐 Web Interface: Not available (missing Flask)"
                )
                print()

                # Wait for next update
                self.shutdown_event.wait(10)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"CLI dashboard error: {e}")
                self.shutdown_event.wait(5)

    def _broadcast_updates(self, sio):
        """Broadcast updates to connected web clients."""
        if not sio:
            return

        while self.dashboard_active and not self.shutdown_event.is_set():
            try:
                data = self._get_dashboard_data()
                sio.emit("compliance_update", data)
                self.shutdown_event.wait(5)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Broadcast error: {e}")
                self.shutdown_event.wait(5)

    def start_dashboard(self, mode: str = "auto"):
        """Start the dashboard.

        Args:
            mode: 'auto', 'web', or 'cli'
        """
        if self.dashboard_active:
            self.logger.warning("Dashboard already active")
            return

        self.dashboard_active = True

        # Determine mode
        if mode == "auto":
            if self.web_available:
                mode = "web"
            else:
                mode = "cli"
                print("⚠️ Flask not available, falling back to CLI mode")

        if mode == "web":
            self._start_web_dashboard()
        elif mode == "cli":
            self._start_cli_dashboard()
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def _start_web_dashboard(self):
        """Start web-based dashboard."""
        app, sio = self._setup_web_interface()

        if not app:
            print("❌ Web interface not available")
            return

        # Start broadcast thread
        broadcast_thread = threading.Thread(
            target=self._broadcast_updates, args=(sio,), daemon=True
        )
        broadcast_thread.start()

        # Start web server
        print(f"🌐 Starting web dashboard on http://localhost:{self.port}")
        print("📊 Real-time compliance monitoring enabled")
        print("🔄 Press Ctrl+C to stop")

        try:
            self._web_server_loop(app, sio)
        except KeyboardInterrupt:
            print("\n🛑 Stopping web dashboard...")
        finally:
            self.stop_dashboard()

    def _start_cli_dashboard(self):
        """Start CLI-based dashboard."""
        cli_thread = threading.Thread(target=self._cli_dashboard_loop, daemon=True)
        cli_thread.start()

        try:
            cli_thread.join()
        except KeyboardInterrupt:
            print("\n🛑 Stopping CLI dashboard...")
        finally:
            self.stop_dashboard()

    def stop_dashboard(self):
        """Stop the dashboard."""
        self.dashboard_active = False
        self.shutdown_event.set()

        # Stop monitoring if we started it
        if (
            hasattr(self.monitor, "monitoring_active")
            and self.monitor.monitoring_active
        ):
            self.monitor.stop_monitoring()

        print("✅ Dashboard stopped")


def main():
    """CLI interface for the compliance dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Compliance Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    parser.add_argument(
        "--mode", choices=["auto", "web", "cli"], default="auto", help="Dashboard mode"
    )
    parser.add_argument(
        "--monitor-only", action="store_true", help="Start monitor without dashboard"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create monitor
    monitor = SOPComplianceMonitor()

    if args.monitor_only:
        print("🔍 Starting SOP compliance monitor only...")
        monitor.start_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            monitor.stop_monitoring()
    else:
        # Create and start dashboard
        dashboard = ComplianceDashboard(monitor, args.port)

        # Setup signal handlers
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, stopping dashboard...")
            dashboard.stop_dashboard()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start monitor if not already running
        if not monitor.monitoring_active:
            monitor.start_monitoring()

        # Start dashboard
        dashboard.start_dashboard(args.mode)


if __name__ == "__main__":
    main()
