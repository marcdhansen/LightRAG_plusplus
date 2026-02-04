#!/usr/bin/env python3
"""
Real-time Monitoring System for A/B Testing Framework
WebSocket-based monitoring with live metrics streaming and alerts
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


@dataclass
class MonitoringAlert:
    """Alert configuration and data"""

    alert_id: str
    type: str  # "error_rate", "response_time", "sample_size", etc.
    variant: str
    threshold: float
    current_value: float
    message: str
    severity: str  # "info", "warning", "critical"
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "timestamp": self.timestamp.isoformat()}


class RealTimeMonitor:
    """Real-time monitoring and alerting system"""

    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.logger = structlog.get_logger()

        # Metrics storage
        self.recent_metrics: list[dict[str, Any]] = []
        self.active_experiments: dict[str, Any] = {}
        self.alerts: list[MonitoringAlert] = []

        # WebSocket connections
        self.websocket_connections: set[WebSocket] = set()

        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "response_time_p95": 5000,  # 5 seconds
            "success_rate_min": 0.9,  # 90% minimum success rate
            "sample_size_min": 100,  # Minimum samples for reliability
        }

        self.console = Console()

    def register_experiment(
        self, experiment_id: str, experiment_config: dict[str, Any]
    ):
        """Register an experiment for monitoring"""
        self.active_experiments[experiment_id] = {
            "config": experiment_config,
            "start_time": datetime.now(),
            "last_update": datetime.now(),
            "status": "running",
        }

        self.logger.info("experiment_registered", experiment_id=experiment_id)

    def add_metrics(
        self, experiment_id: str, variant_name: str, metrics_data: dict[str, Any]
    ):
        """Add new metrics data and process alerts"""

        metric_entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": experiment_id,
            "variant": variant_name,
            **metrics_data,
        }

        # Add to recent metrics buffer
        self.recent_metrics.append(metric_entry)

        # Keep buffer size manageable
        if len(self.recent_metrics) > self.buffer_size:
            self.recent_metrics = self.recent_metrics[-self.buffer_size :]

        # Update experiment last update time
        if experiment_id in self.active_experiments:
            self.active_experiments[experiment_id]["last_update"] = datetime.now()

        # Check for alerts
        self._check_alerts(experiment_id, variant_name, metrics_data)

        # Broadcast to WebSocket clients
        asyncio.create_task(self._broadcast_update(metric_entry))

        self.logger.debug(
            "metrics_added", experiment=experiment_id, variant=variant_name
        )

    def _check_alerts(
        self, experiment_id: str, variant_name: str, metrics_data: dict[str, Any]
    ):
        """Check metrics against alert thresholds"""

        # Error rate alert
        if not metrics_data.get("success", True):
            recent_variant_metrics = [
                m
                for m in self.recent_metrics[-100:]  # Last 100 metrics
                if m.get("variant") == variant_name
                and m.get("experiment_id") == experiment_id
            ]

            if recent_variant_metrics:
                error_rate = sum(
                    1 for m in recent_variant_metrics if not m.get("success", True)
                ) / len(recent_variant_metrics)

                if error_rate > self.alert_thresholds["error_rate"]:
                    alert = MonitoringAlert(
                        alert_id=f"error_rate_{experiment_id}_{variant_name}_{int(datetime.now().timestamp())}",
                        type="error_rate",
                        variant=variant_name,
                        threshold=self.alert_thresholds["error_rate"],
                        current_value=error_rate,
                        message=f"High error rate detected: {error_rate:.1%}",
                        severity="critical" if error_rate > 0.2 else "warning",
                        timestamp=datetime.now(),
                    )
                    self.add_alert(alert)

        # Response time alert
        response_time = metrics_data.get("response_time_ms", 0)
        if response_time > self.alert_thresholds["response_time_p95"]:
            alert = MonitoringAlert(
                alert_id=f"response_time_{experiment_id}_{variant_name}_{int(datetime.now().timestamp())}",
                type="response_time",
                variant=variant_name,
                threshold=self.alert_thresholds["response_time_p95"],
                current_value=response_time,
                message=f"High response time: {response_time:.0f}ms",
                severity="warning",
                timestamp=datetime.now(),
            )
            self.add_alert(alert)

    def add_alert(self, alert: MonitoringAlert):
        """Add a new alert and broadcast it"""
        self.alerts.append(alert)

        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        # Broadcast alert
        asyncio.create_task(self._broadcast_alert(alert.to_dict()))

        self.logger.warning(
            "alert_generated",
            alert_id=alert.alert_id,
            type=alert.type,
            variant=alert.variant,
            severity=alert.severity,
        )

    def get_experiment_summary(self, experiment_id: str) -> dict[str, Any]:
        """Get comprehensive summary of experiment performance"""

        if experiment_id not in self.active_experiments:
            return {"error": "Experiment not found"}

        # Filter metrics for this experiment
        experiment_metrics = [
            m for m in self.recent_metrics if m.get("experiment_id") == experiment_id
        ]

        if not experiment_metrics:
            return {
                "experiment_id": experiment_id,
                "status": "no_data",
                "metrics_count": 0,
            }

        # Group by variant
        variant_data: dict[str, list[dict[str, Any]]] = {}
        for metric in experiment_metrics:
            variant = metric.get("variant", "unknown")
            if variant not in variant_data:
                variant_data[variant] = []
            variant_data[variant].append(metric)

        # Calculate statistics for each variant
        variant_stats = {}
        for variant, metrics in variant_data.items():
            successful_metrics = [m for m in metrics if m.get("success", True)]
            response_times = [m.get("response_time_ms", 0) for m in successful_metrics]

            variant_stats[variant] = {
                "total_requests": len(metrics),
                "successful_requests": len(successful_metrics),
                "success_rate": len(successful_metrics) / len(metrics) * 100
                if metrics
                else 0,
                "avg_response_time_ms": sum(response_times) / len(response_times)
                if response_times
                else 0,
                "p95_response_time_ms": self._percentile(response_times, 95)
                if response_times
                else 0,
                "error_rate": (len(metrics) - len(successful_metrics))
                / len(metrics)
                * 100
                if metrics
                else 0,
                "last_request": max(m.get("timestamp", "") for m in metrics)
                if metrics
                else None,
            }

        # Recent alerts for this experiment
        recent_alerts = [
            alert
            for alert in self.alerts[-20:]  # Last 20 alerts
            if experiment_id in alert.alert_id
        ]

        return {
            "experiment_id": experiment_id,
            "status": self.active_experiments[experiment_id]["status"],
            "start_time": self.active_experiments[experiment_id][
                "start_time"
            ].isoformat(),
            "duration_hours": (
                datetime.now() - self.active_experiments[experiment_id]["start_time"]
            ).total_seconds()
            / 3600,
            "total_requests": sum(
                variant["total_requests"] for variant in variant_stats.values()
            ),
            "variant_stats": variant_stats,
            "recent_alerts": [
                alert.to_dict() for alert in recent_alerts[-5:]
            ],  # Last 5 alerts
            "last_update": self.active_experiments[experiment_id][
                "last_update"
            ].isoformat(),
        }

    def _percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def _broadcast_update(self, metric_data: dict[str, Any]):
        """Broadcast metric update to all WebSocket clients"""
        if not self.websocket_connections:
            return

        message = json.dumps({"type": "metric_update", "data": metric_data})

        # Send to all connected clients
        disconnected_clients = set()
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected_clients.add(websocket)

        # Remove disconnected clients
        self.websocket_connections -= disconnected_clients

    async def _broadcast_alert(self, alert_data: dict[str, Any]):
        """Broadcast alert to all WebSocket clients"""
        if not self.websocket_connections:
            return

        message = json.dumps({"type": "alert", "data": alert_data})

        # Send to all connected clients
        disconnected_clients = set()
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected_clients.add(websocket)

        # Remove disconnected clients
        self.websocket_connections -= disconnected_clients

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive dashboard data"""

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "active_experiments": len(self.active_experiments),
            "total_metrics": len(self.recent_metrics),
            "active_alerts": len([a for a in self.alerts if a.severity == "critical"]),
            "experiments": {},
        }

        for experiment_id in self.active_experiments:
            dashboard_data["experiments"][experiment_id] = self.get_experiment_summary(
                experiment_id
            )

        return dashboard_data

    def create_rich_dashboard(self) -> Layout:
        """Create Rich dashboard layout for terminal display"""
        layout = Layout()

        # Create header
        header = Panel(
            f"[bold blue]A/B Testing Real-time Monitor[/bold blue]\n"
            f"Active Experiments: {len(self.active_experiments)} | "
            f"Total Metrics: {len(self.recent_metrics)} | "
            f"Critical Alerts: {len([a for a in self.alerts if a.severity == 'critical'])}",
            title="🔍 LightRAG A/B Testing",
            border_style="blue",
        )

        layout.split_column(
            Layout(header, size=3),
            Layout(name="body"),
        )

        # Create experiment tables
        tables_html = []
        for experiment_id in self.active_experiments:
            summary = self.get_experiment_summary(experiment_id)

            if "error" not in summary and summary.get("metrics_count", 0) > 0:
                table = Table(title=f"Experiment: {experiment_id}")
                table.add_column("Variant", style="cyan")
                table.add_column("Requests", justify="right")
                table.add_column("Success Rate", justify="right")
                table.add_column("Avg Response (ms)", justify="right")
                table.add_column("P95 Response (ms)", justify="right")

                for variant_name, stats in summary.get("variant_stats", {}).items():
                    table.add_row(
                        variant_name,
                        str(stats.get("total_requests", 0)),
                        f"{stats.get('success_rate', 0):.1f}%",
                        f"{stats.get('avg_response_time_ms', 0):.0f}",
                        f"{stats.get('p95_response_time_ms', 0):.0f}",
                    )

                tables_html.append(table)

        if tables_html:
            layout["body"].split_column(*[Layout(table) for table in tables_html])
        else:
            layout["body"].update(
                Panel("No experiment data available", border_style="yellow")
            )

        return layout


class MonitoringServer:
    """FastAPI server for monitoring dashboard and WebSocket streaming"""

    def __init__(
        self, monitor: RealTimeMonitor, host: str = "0.0.0.0", port: int = 8080
    ):
        self.monitor = monitor
        self.app = FastAPI(title="A/B Testing Monitor")
        self.host = host
        self.port = port

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()

        # Mount static files if available
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(static_dir)), name="static"
            )

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/api/dashboard")
        async def get_dashboard():
            """Get dashboard data"""
            return self.monitor.get_dashboard_data()

        @self.app.get("/api/experiment/{experiment_id}")
        async def get_experiment(experiment_id: str):
            """Get specific experiment data"""
            return self.monitor.get_experiment_summary(experiment_id)

        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get recent alerts"""
            return {"alerts": [alert.to_dict() for alert in self.monitor.alerts[-50:]]}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.monitor.websocket_connections.add(websocket)

            try:
                # Send initial dashboard data
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "initial_data",
                            "data": self.monitor.get_dashboard_data(),
                        }
                    )
                )

                # Keep connection alive
                while True:
                    await websocket.receive_text()

            except WebSocketDisconnect:
                pass
            finally:
                self.monitor.websocket_connections.discard(websocket)

        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard_html():
            """Serve dashboard HTML"""
            return self._get_dashboard_html()

    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>A/B Testing Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2196F3; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert.critical { background: #ffebee; border-left: 4px solid #f44336; }
        .alert.warning { background: #fff3e0; border-left: 4px solid #ff9800; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-good { background: #4caf50; }
        .status-warning { background: #ff9800; }
        .status-critical { background: #f44336; }
        .experiment-section { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 LightRAG A/B Testing Monitor</h1>
        <div id="status">Connecting to monitoring server...</div>
    </div>

    <div id="metrics-overview">
        <div class="metric-card">
            <h3>Active Experiments: <span id="active-experiments">0</span></h3>
        </div>
        <div class="metric-card">
            <h3>Total Metrics: <span id="total-metrics">0</span></h3>
        </div>
        <div class="metric-card">
            <h3>Critical Alerts: <span id="critical-alerts">0</span></h3>
        </div>
    </div>

    <div id="alerts-section">
        <h2>🚨 Recent Alerts</h2>
        <div id="alerts-list">No alerts</div>
    </div>

    <div id="experiments-section">
        <h2>🧪 Active Experiments</h2>
        <div id="experiments-list">No experiments</div>
    </div>

    <script>
        let ws;
        let dashboardData = null;

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById('status').innerHTML =
                    '<span class="status-indicator status-good"></span>Connected to monitoring server';
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);

                if (message.type === 'initial_data') {
                    dashboardData = message.data;
                    updateDashboard();
                } else if (message.type === 'metric_update') {
                    // Handle real-time metric updates
                    updateMetricDisplay(message.data);
                } else if (message.type === 'alert') {
                    // Handle new alerts
                    addAlert(message.data);
                }
            };

            ws.onclose = function() {
                document.getElementById('status').innerHTML =
                    '<span class="status-indicator status-warning"></span>Disconnected. Reconnecting...';
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = function() {
                document.getElementById('status').innerHTML =
                    '<span class="status-indicator status-critical"></span>Connection error';
            };
        }

        function updateDashboard() {
            if (!dashboardData) return;

            // Update overview metrics
            document.getElementById('active-experiments').textContent = dashboardData.active_experiments;
            document.getElementById('total-metrics').textContent = dashboardData.total_metrics;
            document.getElementById('critical-alerts').textContent = dashboardData.active_alerts;

            // Update experiments
            updateExperimentsList(dashboardData.experiments);
        }

        function updateExperimentsList(experiments) {
            const container = document.getElementById('experiments-list');
            container.innerHTML = '';

            Object.entries(experiments).forEach(([id, data]) => {
                if (data.error) return;

                const experimentDiv = document.createElement('div');
                experimentDiv.className = 'experiment-section';

                let html = `<h3>Experiment: ${id}</h3>`;
                html += `<p>Status: ${data.status} | Duration: ${data.duration_hours.toFixed(1)}h | Total Requests: ${data.total_requests}</p>`;

                if (data.variant_stats && Object.keys(data.variant_stats).length > 0) {
                    html += '<table><tr><th>Variant</th><th>Requests</th><th>Success Rate</th><th>Avg Response</th><th>P95 Response</th></tr>';

                    Object.entries(data.variant_stats).forEach(([variant, stats]) => {
                        html += `<tr>
                            <td>${variant}</td>
                            <td>${stats.total_requests}</td>
                            <td>${stats.success_rate.toFixed(1)}%</td>
                            <td>${stats.avg_response_time_ms.toFixed(0)}ms</td>
                            <td>${stats.p95_response_time_ms.toFixed(0)}ms</td>
                        </tr>`;
                    });

                    html += '</table>';
                }

                experimentDiv.innerHTML = html;
                container.appendChild(experimentDiv);
            });
        }

        function updateMetricDisplay(metricData) {
            // Update real-time metric displays
            console.log('New metric:', metricData);
        }

        function addAlert(alertData) {
            const alertsList = document.getElementById('alerts-list');

            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${alertData.severity}`;
            alertDiv.innerHTML = `
                <strong>${alertData.type}</strong> - ${alertData.variant}: ${alertData.message}
                <br><small>${new Date(alertData.timestamp).toLocaleString()}</small>
            `;

            alertsList.insertBefore(alertDiv, alertsList.firstChild);

            // Keep only last 10 alerts visible
            while (alertsList.children.length > 10) {
                alertsList.removeChild(alertsList.lastChild);
            }
        }

        // Initialize
        connectWebSocket();
    </script>
</body>
</html>
        """

    async def start(self):
        """Start the monitoring server"""
        import uvicorn

        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


class TerminalMonitor:
    """Terminal-based monitoring with Rich display"""

    def __init__(self, monitor: RealTimeMonitor, refresh_interval: float = 2.0):
        self.monitor = monitor
        self.refresh_interval = refresh_interval
        self.console = Console()
        self.live = None

    def start_monitoring(self):
        """Start terminal monitoring"""
        self.live = Live(refresh_per_second=1 / self.refresh_interval)
        self.live.start()

        try:
            while True:
                layout = self.monitor.create_rich_dashboard()
                self.live.update(layout)
                import time

                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            if self.live:
                self.live.stop()
            print("\\nMonitoring stopped by user")

    def stop_monitoring(self):
        """Stop terminal monitoring"""
        if self.live:
            self.live.stop()


# Integration function to connect with main framework
def create_monitoring_system() -> tuple[
    RealTimeMonitor, MonitoringServer, TerminalMonitor
]:
    """Create a complete monitoring system"""

    monitor = RealTimeMonitor()
    server = MonitoringServer(monitor)
    terminal_monitor = TerminalMonitor(monitor)

    return monitor, server, terminal_monitor


if __name__ == "__main__":
    import asyncio

    async def demo_monitoring():
        """Demonstrate monitoring system"""

        monitor, server, terminal_monitor = create_monitoring_system()

        # Start monitoring server in background
        server_task = asyncio.create_task(server.start())

        # Register a demo experiment
        monitor.register_experiment(
            "demo_experiment",
            {"name": "Demo A/B Test", "variants": ["control", "treatment"]},
        )

        # Simulate some metrics
        for i in range(50):
            monitor.add_metrics(
                experiment_id="demo_experiment",
                variant_name="control" if i % 2 == 0 else "treatment",
                metrics_data={
                    "success": i % 10 != 0,  # 90% success rate
                    "response_time_ms": 800 + (i % 5) * 200,  # 800-1800ms range
                },
            )
            await asyncio.sleep(0.1)

        print("Monitoring server started on http://localhost:8080")
        print("Press Ctrl+C to stop")

        # Wait for interrupt
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
            print("Monitoring stopped")

    asyncio.run(demo_monitoring())
