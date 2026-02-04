#!/usr/bin/env python3
"""
Advanced Dashboard for A/B Testing Framework
Interactive web dashboard with real-time charts, experiment management, and detailed analytics
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


class ExperimentCreateRequest(BaseModel):
    """Request model for creating new experiments"""

    name: str
    description: str = ""
    variants: list[dict[str, Any]]
    traffic_split_type: str = "hash"
    sample_size: int = 1000
    confidence_level: float = 0.95
    duration_hours: int = 24


class ExperimentActionRequest(BaseModel):
    """Request model for experiment actions"""

    action: str  # "start", "pause", "stop", "delete"
    reason: str = ""


class AdvancedDashboard:
    """Advanced dashboard with full experiment management capabilities"""

    def __init__(self, monitoring_system):
        self.monitor = monitoring_system
        self.app = FastAPI(title="A/B Testing Advanced Dashboard")
        self.templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

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

        # Mount static files
        static_dir = Path(__file__).parent / "static"
        if not static_dir.exists():
            static_dir.mkdir(exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Create templates directory
        templates_dir = Path(__file__).parent / "templates"
        if not templates_dir.exists():
            templates_dir.mkdir(exist_ok=True)
            self._create_default_templates(templates_dir)

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse(
                "dashboard.html", {"request": request, "title": "A/B Testing Dashboard"}
            )

        @self.app.get("/api/experiments")
        async def get_experiments():
            """Get all experiments with detailed information"""
            experiments_data = {}
            for experiment_id in self.monitor.active_experiments:
                experiments_data[experiment_id] = self.monitor.get_experiment_summary(
                    experiment_id
                )

            return experiments_data

        @self.app.post("/api/experiments")
        async def create_experiment(request: ExperimentCreateRequest):
            """Create a new experiment"""
            try:
                # This would integrate with the comprehensive framework
                experiment_id = f"exp_{int(datetime.now().timestamp())}"

                self.monitor.register_experiment(
                    experiment_id,
                    {
                        "name": request.name,
                        "description": request.description,
                        "variants": request.variants,
                        "config": request.dict(),
                    },
                )

                return {"experiment_id": experiment_id, "status": "created"}

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/api/experiments/{experiment_id}")
        async def get_experiment(experiment_id: str):
            """Get specific experiment details"""
            experiment_data = self.monitor.get_experiment_summary(experiment_id)

            if "error" in experiment_data:
                raise HTTPException(status_code=404, detail=experiment_data["error"])

            return experiment_data

        @self.app.post("/api/experiments/{experiment_id}/action")
        async def experiment_action(
            experiment_id: str, request: ExperimentActionRequest
        ):
            """Perform action on experiment (start, stop, pause, delete)"""
            if experiment_id not in self.monitor.active_experiments:
                raise HTTPException(status_code=404, detail="Experiment not found")

            try:
                if request.action == "start":
                    self.monitor.active_experiments[experiment_id]["status"] = "running"
                elif request.action == "pause":
                    self.monitor.active_experiments[experiment_id]["status"] = "paused"
                elif request.action == "stop":
                    self.monitor.active_experiments[experiment_id]["status"] = (
                        "completed"
                    )
                elif request.action == "delete":
                    del self.monitor.active_experiments[experiment_id]
                else:
                    raise HTTPException(status_code=400, detail="Invalid action")

                return {
                    "status": "success",
                    "message": f"Action '{request.action}' completed",
                }

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/api/metrics/{experiment_id}/timeseries")
        async def get_metrics_timeseries(
            experiment_id: str, metric: str = "response_time_ms", hours: int = 24
        ):
            """Get time series data for specific metric"""

            cutoff_time = datetime.now() - timedelta(hours=hours)

            metrics = [
                m
                for m in self.monitor.recent_metrics
                if (
                    m.get("experiment_id") == experiment_id
                    and m.get("timestamp")
                    and datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
                    > cutoff_time
                )
            ]

            # Group by variant and time buckets
            time_buckets = {}
            for metric_entry in metrics:
                timestamp = datetime.fromisoformat(
                    metric_entry["timestamp"].replace("Z", "+00:00")
                )
                time_key = timestamp.replace(
                    minute=0, second=0, microsecond=0
                ).isoformat()
                variant = metric_entry.get("variant", "unknown")

                if time_key not in time_buckets:
                    time_buckets[time_key] = {}

                if variant not in time_buckets[time_key]:
                    time_buckets[time_key][variant] = []

                if metric in metric_entry:
                    time_buckets[time_key][variant].append(metric_entry[metric])

            # Calculate averages for each time bucket
            timeseries_data = []
            for time_key in sorted(time_buckets.keys()):
                time_bucket_data = {"timestamp": time_key}
                for variant in time_buckets[time_key]:
                    values = time_buckets[time_key][variant]
                    if values:
                        time_bucket_data[variant] = sum(values) / len(values)

                timeseries_data.append(time_bucket_data)

            return {"data": timeseries_data, "metric": metric}

        @self.app.get("/api/experiments/{experiment_id}/statistics")
        async def get_experiment_statistics(experiment_id: str):
            """Get detailed statistics for experiment"""

            experiment_metrics = [
                m
                for m in self.monitor.recent_metrics
                if m.get("experiment_id") == experiment_id
            ]

            if not experiment_metrics:
                return {"error": "No data available"}

            # Group by variant
            variant_data: dict[str, list[dict[str, Any]]] = {}
            for metric in experiment_metrics:
                variant = metric.get("variant", "unknown")
                if variant not in variant_data:
                    variant_data[variant] = []
                variant_data[variant].append(metric)

            # Calculate detailed statistics
            detailed_stats = {}
            for variant, metrics in variant_data.items():
                successful_metrics = [m for m in metrics if m.get("success", True)]
                failed_metrics = [m for m in metrics if not m.get("success", True)]
                response_times = [
                    m.get("response_time_ms", 0) for m in successful_metrics
                ]
                token_usage = [m.get("token_usage", 0) for m in successful_metrics]
                cache_hits = [m for m in metrics if m.get("cache_hit", False)]

                # Percentiles
                sorted_times = sorted(response_times)
                n = len(sorted_times)

                detailed_stats[variant] = {
                    "basic": {
                        "total_requests": len(metrics),
                        "successful_requests": len(successful_metrics),
                        "failed_requests": len(failed_metrics),
                        "success_rate": len(successful_metrics) / len(metrics) * 100
                        if metrics
                        else 0,
                        "error_rate": len(failed_metrics) / len(metrics) * 100
                        if metrics
                        else 0,
                    },
                    "response_time": {
                        "mean": sum(response_times) / len(response_times)
                        if response_times
                        else 0,
                        "median": sorted_times[n // 2] if n > 0 else 0,
                        "p90": sorted_times[int(n * 0.9)] if n > 0 else 0,
                        "p95": sorted_times[int(n * 0.95)] if n > 0 else 0,
                        "p99": sorted_times[int(n * 0.99)] if n > 0 else 0,
                        "min": min(response_times) if response_times else 0,
                        "max": max(response_times) if response_times else 0,
                    },
                    "other_metrics": {
                        "total_tokens": sum(token_usage),
                        "avg_tokens_per_request": sum(token_usage) / len(token_usage)
                        if token_usage
                        else 0,
                        "cache_hit_rate": len(cache_hits) / len(metrics) * 100
                        if metrics
                        else 0,
                    },
                    "time_distribution": self._create_time_distribution(response_times),
                }

            return {"experiment_id": experiment_id, "statistics": detailed_stats}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Enhanced WebSocket with multiple channel support"""
            await websocket.accept()
            self.monitor.websocket_connections.add(websocket)

            try:
                # Send initial data
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "initial_data",
                            "data": self.monitor.get_dashboard_data(),
                        }
                    )
                )

                # Handle messages
                while True:
                    message = await websocket.receive_text()
                    try:
                        data = json.loads(message)
                        if data.get("type") == "subscribe_experiment":
                            # Send experiment-specific updates
                            experiment_id = data.get("experiment_id")
                            if experiment_id:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "experiment_update",
                                            "experiment_id": experiment_id,
                                            "data": self.monitor.get_experiment_summary(
                                                experiment_id
                                            ),
                                        }
                                    )
                                )
                    except json.JSONDecodeError:
                        pass  # Ignore invalid JSON

            except WebSocketDisconnect:
                pass
            finally:
                self.monitor.websocket_connections.discard(websocket)

    def _create_time_distribution(self, response_times: list[float]) -> dict[str, int]:
        """Create time distribution histogram"""
        if not response_times:
            return {}

        # Define time buckets (in milliseconds)
        buckets = {
            "<100": 0,
            "100-500": 0,
            "500-1000": 0,
            "1000-2000": 0,
            "2000-5000": 0,
            ">5000": 0,
        }

        for time_ms in response_times:
            if time_ms < 100:
                buckets["<100"] += 1
            elif time_ms < 500:
                buckets["100-500"] += 1
            elif time_ms < 1000:
                buckets["500-1000"] += 1
            elif time_ms < 2000:
                buckets["1000-2000"] += 1
            elif time_ms < 5000:
                buckets["2000-5000"] += 1
            else:
                buckets[">5000"] += 1

        return buckets

    def _create_default_templates(self, templates_dir: Path):
        """Create default HTML templates"""

        # Main dashboard template
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        .metric-card { transition: all 0.3s ease; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .status-indicator { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .chart-container { position: relative; height: 300px; }
        .experiment-card { border-left: 4px solid #3b82f6; }
        .experiment-card.running { border-left-color: #10b981; }
        .experiment-card.paused { border-left-color: #f59e0b; }
        .experiment-card.completed { border-left-color: #6b7280; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center">
                    <i class="ri-flask-fill text-blue-600 text-2xl mr-3"></i>
                    <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="connection-status" class="flex items-center">
                        <div class="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                        <span class="text-sm text-gray-600">Connecting...</span>
                    </div>
                    <button onclick="refreshData()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        <i class="ri-refresh-line mr-2"></i>Refresh
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Metrics Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 bg-blue-100 rounded-lg">
                        <i class="ri-flask-line text-blue-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Active Experiments</p>
                        <p id="active-experiments" class="text-2xl font-bold text-gray-900">0</p>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 bg-green-100 rounded-lg">
                        <i class="ri-bar-chart-line text-green-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total Requests</p>
                        <p id="total-requests" class="text-2xl font-bold text-gray-900">0</p>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 bg-yellow-100 rounded-lg">
                        <i class="ri-alarm-warning-line text-yellow-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Active Alerts</p>
                        <p id="active-alerts" class="text-2xl font-bold text-gray-900">0</p>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 bg-purple-100 rounded-lg">
                        <i class="ri-percent-line text-purple-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Avg Success Rate</p>
                        <p id="avg-success-rate" class="text-2xl font-bold text-gray-900">0%</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create New Experiment -->
        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Experiment Management</h2>
                <button onclick="showCreateExperimentModal()" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
                    <i class="ri-add-line mr-2"></i>New Experiment
                </button>
            </div>
        </div>

        <!-- Experiments List -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div id="experiments-container" class="lg:col-span-2">
                <!-- Experiments will be populated here -->
            </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Response Time Trends</h3>
                <div class="chart-container">
                    <canvas id="response-time-chart"></canvas>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Success Rate Comparison</h3>
                <div class="chart-container">
                    <canvas id="success-rate-chart"></canvas>
                </div>
            </div>
        </div>
    </main>

    <!-- Create Experiment Modal -->
    <div id="create-experiment-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center min-h-screen p-4">
            <div class="bg-white rounded-lg max-w-2xl w-full p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Create New Experiment</h3>
                    <button onclick="hideCreateExperimentModal()" class="text-gray-400 hover:text-gray-600">
                        <i class="ri-close-line text-xl"></i>
                    </button>
                </div>

                <form id="create-experiment-form" onsubmit="createExperiment(event)">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Experiment Name</label>
                        <input type="text" id="experiment-name" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea id="experiment-description" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"></textarea>
                    </div>

                    <div class="mb-6">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Sample Size</label>
                        <input type="number" id="sample-size" value="1000" min="100" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>

                    <div class="flex justify-end space-x-3">
                        <button type="button" onclick="hideCreateExperimentModal()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                            Cancel
                        </button>
                        <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                            Create Experiment
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let dashboardData = null;
        let charts = {};

        // Initialize WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                updateConnectionStatus('connected');
                console.log('Connected to monitoring server');
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);

                if (message.type === 'initial_data') {
                    dashboardData = message.data;
                    updateDashboard();
                } else if (message.type === 'metric_update') {
                    handleMetricUpdate(message.data);
                } else if (message.type === 'alert') {
                    handleNewAlert(message.data);
                }
            };

            ws.onclose = function() {
                updateConnectionStatus('disconnected');
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = function() {
                updateConnectionStatus('error');
            };
        }

        function updateConnectionStatus(status) {
            const statusDiv = document.getElementById('connection-status');
            const indicators = {
                connected: '<div class="w-2 h-2 bg-green-500 rounded-full mr-2 status-indicator"></div><span class="text-sm text-green-600">Connected</span>',
                disconnected: '<div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div><span class="text-sm text-red-600">Disconnected</span>',
                error: '<div class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div><span class="text-sm text-yellow-600">Error</span>',
                connecting: '<div class="w-2 h-2 bg-gray-400 rounded-full mr-2"></div><span class="text-sm text-gray-600">Connecting...</span>'
            };

            statusDiv.innerHTML = indicators[status] || indicators.connecting;
        }

        function updateDashboard() {
            if (!dashboardData) return;

            // Update metrics overview
            document.getElementById('active-experiments').textContent = dashboardData.active_experiments || 0;
            document.getElementById('total-requests').textContent = dashboardData.total_metrics || 0;
            document.getElementById('active-alerts').textContent = dashboardData.active_alerts || 0;

            // Calculate average success rate
            let totalRequests = 0;
            let totalSuccess = 0;
            Object.values(dashboardData.experiments).forEach(exp => {
                if (exp.variant_stats) {
                    Object.values(exp.variant_stats).forEach(stats => {
                        totalRequests += stats.total_requests || 0;
                        totalSuccess += stats.successful_requests || 0;
                    });
                }
            });
            const avgSuccessRate = totalRequests > 0 ? (totalSuccess / totalRequests * 100).toFixed(1) : 0;
            document.getElementById('avg-success-rate').textContent = avgSuccessRate + '%';

            // Update experiments list
            updateExperimentsList();

            // Update charts
            updateCharts();
        }

        function updateExperimentsList() {
            const container = document.getElementById('experiments-container');
            container.innerHTML = '';

            Object.entries(dashboardData.experiments).forEach(([id, exp]) => {
                if (exp.error) return;

                const statusClass = exp.status === 'running' ? 'running' :
                                  exp.status === 'paused' ? 'paused' : 'completed';

                const experimentCard = document.createElement('div');
                experimentCard.className = `experiment-card ${statusClass} bg-white rounded-lg shadow p-6`;

                experimentCard.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">${id}</h3>
                            <p class="text-sm text-gray-600">Status: <span class="font-medium">${exp.status}</span></p>
                            <p class="text-sm text-gray-600">Duration: ${exp.duration_hours?.toFixed(1) || 0}h</p>
                        </div>
                        <div class="flex space-x-2">
                            ${exp.status === 'running' ?
                                `<button onclick="pauseExperiment('${id}')" class="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition text-sm">Pause</button>` :
                                ''
                            }
                            <button onclick="viewExperimentDetails('${id}')" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm">View</button>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <p class="text-gray-600">Total Requests</p>
                            <p class="font-semibold">${exp.total_requests || 0}</p>
                        </div>
                        <div>
                            <p class="text-gray-600">Success Rate</p>
                            <p class="font-semibold">${calculateAvgSuccessRate(exp).toFixed(1)}%</p>
                        </div>
                        <div>
                            <p class="text-gray-600">Avg Response</p>
                            <p class="font-semibold">${calculateAvgResponseTime(exp).toFixed(0)}ms</p>
                        </div>
                        <div>
                            <p class="text-gray-600">Variants</p>
                            <p class="font-semibold">${Object.keys(exp.variant_stats || {}).length}</p>
                        </div>
                    </div>
                `;

                container.appendChild(experimentCard);
            });
        }

        function calculateAvgSuccessRate(experiment) {
            if (!experiment.variant_stats) return 0;

            let totalRequests = 0;
            let totalSuccess = 0;

            Object.values(experiment.variant_stats).forEach(stats => {
                totalRequests += stats.total_requests || 0;
                totalSuccess += stats.successful_requests || 0;
            });

            return totalRequests > 0 ? (totalSuccess / totalRequests * 100) : 0;
        }

        function calculateAvgResponseTime(experiment) {
            if (!experiment.variant_stats) return 0;

            const responseTimes = Object.values(experiment.variant_stats)
                .map(stats => stats.avg_response_time_ms || 0)
                .filter(time => time > 0);

            return responseTimes.length > 0 ?
                responseTimes.reduce((a, b) => a + b) / responseTimes.length : 0;
        }

        function updateCharts() {
            // This would implement chart updates using Chart.js
            // For now, just create placeholder charts
            createResponseTimeChart();
            createSuccessRateChart();
        }

        function createResponseTimeChart() {
            const ctx = document.getElementById('response-time-chart').getContext('2d');

            if (charts.responseTime) {
                charts.responseTime.destroy();
            }

            charts.responseTime = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [1200, 1150, 1100, 1050, 1000],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Response Time (ms)'
                            }
                        }
                    }
                }
            });
        }

        function createSuccessRateChart() {
            const ctx = document.getElementById('success-rate-chart').getContext('2d');

            if (charts.successRate) {
                charts.successRate.destroy();
            }

            charts.successRate = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Success', 'Failed'],
                    datasets: [{
                        data: [95, 5],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function showCreateExperimentModal() {
            document.getElementById('create-experiment-modal').classList.remove('hidden');
        }

        function hideCreateExperimentModal() {
            document.getElementById('create-experiment-modal').classList.add('hidden');
            document.getElementById('create-experiment-form').reset();
        }

        async function createExperiment(event) {
            event.preventDefault();

            const formData = {
                name: document.getElementById('experiment-name').value,
                description: document.getElementById('experiment-description').value,
                sample_size: parseInt(document.getElementById('sample-size').value),
                variants: [
                    { name: 'control', type: 'control', traffic_percentage: 50 },
                    { name: 'treatment', type: 'treatment', traffic_percentage: 50 }
                ]
            };

            try {
                const response = await fetch('/api/experiments', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                if (response.ok) {
                    const result = await response.json();
                    hideCreateExperimentModal();
                    refreshData();

                    // Show success message
                    showNotification('Experiment created successfully!', 'success');
                } else {
                    throw new Error('Failed to create experiment');
                }
            } catch (error) {
                showNotification('Error creating experiment: ' + error.message, 'error');
            }
        }

        async function pauseExperiment(experimentId) {
            try {
                const response = await fetch(`/api/experiments/${experimentId}/action`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'pause' })
                });

                if (response.ok) {
                    refreshData();
                    showNotification('Experiment paused', 'info');
                }
            } catch (error) {
                showNotification('Error pausing experiment: ' + error.message, 'error');
            }
        }

        function viewExperimentDetails(experimentId) {
            // This would open a detailed view of the experiment
            console.log('Viewing details for:', experimentId);
            // For now, just refresh the data
            refreshData();
        }

        function refreshData() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    dashboardData = data;
                    updateDashboard();
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                });
        }

        function handleMetricUpdate(metricData) {
            // Handle real-time metric updates
            console.log('New metric:', metricData);
            // Update relevant UI elements
        }

        function handleNewAlert(alertData) {
            console.log('New alert:', alertData);
            // Display alert notification
            showNotification(`Alert: ${alertData.message}`, alertData.severity);
        }

        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 ${
                type === 'success' ? 'bg-green-500 text-white' :
                type === 'error' ? 'bg-red-500 text-white' :
                type === 'warning' ? 'bg-yellow-500 text-white' :
                'bg-blue-500 text-white'
            }`;
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
        });
    </script>
</body>
</html>
        """

        with open(templates_dir / "dashboard.html", "w") as f:
            f.write(dashboard_html)


# Integration function
def create_advanced_dashboard(monitoring_system):
    """Create and return advanced dashboard instance"""
    return AdvancedDashboard(monitoring_system)


if __name__ == "__main__":
    import asyncio

    from realtime_monitoring import create_monitoring_system

    async def demo_advanced_dashboard():
        """Demonstrate advanced dashboard"""

        monitor, server, terminal_monitor = create_monitoring_system()
        dashboard = create_advanced_dashboard(monitor)

        # Start monitoring server in background
        server_task = asyncio.create_task(server.start())

        print("Advanced dashboard started on http://localhost:8080")
        print("Features:")
        print("- Real-time experiment monitoring")
        print("- Interactive charts and analytics")
        print("- Experiment creation and management")
        print("- WebSocket-based live updates")
        print("\\nPress Ctrl+C to stop")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
            print("Advanced dashboard stopped")

    asyncio.run(demo_advanced_dashboard())
