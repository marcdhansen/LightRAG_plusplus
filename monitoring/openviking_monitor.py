#!/usr/bin/env python3
"""
OpenViking Monitoring Dashboard
Real-time monitoring and alerting for OpenViking production deployment
"""

import asyncio
import json
import time
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text


class OpenVikingMonitor:
    def __init__(self, openviking_url: str = "http://localhost:8002"):
        self.console = Console()
        self.openviking_url = openviking_url
        self.alerts = []
        self.metrics_history = []
        self.start_time = datetime.now()

    async def check_health(self) -> Dict[str, Any]:
        """Check system health status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openviking_url}/health", timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "healthy",
                        "timestamp": data.get("timestamp"),
                        "version": data.get("version"),
                        "features": data.get("features", []),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                    }
        except Exception as e:
            return {"status": "down", "error": str(e), "response_time_ms": 0}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openviking_url}/performance/metrics", timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "timestamp": data.get("timestamp"),
                        "systems": data.get("systems", {}),
                        "summary": data.get("summary", {}),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                    }
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def test_endpoint_performance(self) -> Dict[str, Any]:
        """Test key endpoints performance"""
        endpoints = {
            "embeddings": {
                "method": "POST",
                "url": "/embeddings",
                "payload": {"text": "Performance test query"},
            },
            "skills": {
                "method": "POST",
                "url": "/skills/search",
                "payload": {"query": "performance test", "max_results": 5},
            },
            "conversation": {
                "method": "POST",
                "url": "/conversation",
                "payload": {
                    "session_id": f"monitor-test-{int(time.time())}",
                    "message": "Test message",
                    "role": "user",
                },
            },
        }

        results = {}

        async with httpx.AsyncClient() as client:
            for name, config in endpoints.items():
                try:
                    start_time = time.time()
                    if config["method"] == "POST":
                        response = await client.post(
                            f"{self.openviking_url}{config['url']}",
                            json=config["payload"],
                            timeout=10.0,
                        )
                    else:
                        response = await client.get(
                            f"{self.openviking_url}{config['url']}", timeout=10.0
                        )

                    response_time = (time.time() - start_time) * 1000

                    results[name] = {
                        "status_code": response.status_code,
                        "response_time_ms": response_time,
                        "success": 200 <= response.status_code < 400,
                        "endpoint": config["url"],
                    }
                except Exception as e:
                    results[name] = {
                        "error": str(e),
                        "response_time_ms": 0,
                        "success": False,
                        "endpoint": config["url"],
                    }

        return results

    def check_alerts(self, health: Dict, metrics: Dict, endpoints: Dict) -> List[Dict]:
        """Check for alerts based on thresholds"""
        alerts = []
        current_time = datetime.now()

        # Health alerts
        if health.get("status") != "healthy":
            alerts.append(
                {
                    "severity": "critical",
                    "type": "health",
                    "message": f"Health check failed: {health.get('error', 'Unknown')}",
                    "timestamp": current_time,
                }
            )

        # Response time alerts
        health_response_time = health.get("response_time_ms", 0)
        if health_response_time > 1000:  # 1 second threshold
            alerts.append(
                {
                    "severity": "warning",
                    "type": "response_time",
                    "message": f"Health endpoint slow: {health_response_time:.0f}ms",
                    "timestamp": current_time,
                }
            )

        # Endpoint performance alerts
        for name, data in endpoints.items():
            if not data.get("success", False):
                alerts.append(
                    {
                        "severity": "critical",
                        "type": "endpoint_failure",
                        "message": f"{name.title()} endpoint failed: {data.get('error', 'Unknown')}",
                        "timestamp": current_time,
                    }
                )
            elif data.get("response_time_ms", 0) > 5000:  # 5 second threshold
                alerts.append(
                    {
                        "severity": "warning",
                        "type": "slow_endpoint",
                        "message": f"{name.title()} endpoint slow: {data.get('response_time_ms', 0):.0f}ms",
                        "timestamp": current_time,
                    }
                )

        # Memory/Resource alerts
        if metrics and "summary" in metrics:
            summary = metrics["summary"]
            active_sessions = summary.get("active_sessions", 0)
            total_requests = summary.get("total_requests", 0)

            if active_sessions > 1000:
                alerts.append(
                    {
                        "severity": "warning",
                        "type": "high_sessions",
                        "message": f"High active sessions: {active_sessions}",
                        "timestamp": current_time,
                    }
                )

        return alerts

    def create_dashboard(
        self, health: Dict, metrics: Dict, endpoints: Dict, alerts: List
    ) -> Layout:
        """Create the monitoring dashboard layout"""
        layout = Layout()

        # Create header
        header_text = Text(
            f"OpenViking Production Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="bold blue",
        )
        header = Panel(header_text, style="bold white on blue")

        # Create tables for different sections
        # Health table
        health_table = Table(
            title="🏥 Health Status", show_header=True, header_style="bold magenta"
        )
        health_table.add_column("Metric", style="cyan")
        health_table.add_column("Value", style="green")

        status_style = "green" if health.get("status") == "healthy" else "red"
        health_table.add_row(
            "Status",
            f"[{status_style}]{health.get('status', 'Unknown').upper()}[/{status_style}]",
        )
        health_table.add_row(
            "Response Time", f"{health.get('response_time_ms', 0):.1f}ms"
        )
        health_table.add_row("Version", health.get("version", "Unknown"))
        health_table.add_row("Features", f"{len(health.get('features', []))} active")

        # Endpoints table
        endpoints_table = Table(
            title="🚀 Endpoint Performance",
            show_header=True,
            header_style="bold magenta",
        )
        endpoints_table.add_column("Endpoint", style="cyan")
        endpoints_table.add_column("Response Time", style="green")
        endpoints_table.add_column("Status", style="yellow")

        for name, data in endpoints.items():
            status = "✅" if data.get("success", False) else "❌"
            response_time = f"{data.get('response_time_ms', 0):.1f}ms"
            endpoints_table.add_row(name, response_time, status)

        # Metrics table
        metrics_table = Table(
            title="📊 System Metrics", show_header=True, header_style="bold magenta"
        )
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")

        if metrics and "summary" in metrics:
            summary = metrics["summary"]
            metrics_table.add_row(
                "Total Requests", f"{summary.get('total_requests', 0):,}"
            )
            metrics_table.add_row(
                "Active Sessions", f"{summary.get('active_sessions', 0):,}"
            )
            metrics_table.add_row("Cache Size", f"{summary.get('cache_size', 0):,}")
            metrics_table.add_row(
                "API Response Time", f"{metrics.get('response_time_ms', 0):.1f}ms"
            )

        # Alerts table
        alerts_table = Table(
            title="🚨 Active Alerts", show_header=True, header_style="bold magenta"
        )
        alerts_table.add_column("Severity", style="cyan")
        alerts_table.add_column("Type", style="yellow")
        alerts_table.add_column("Message", style="white")
        alerts_table.add_column("Time", style="dim")

        recent_alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)[:5]
        for alert in recent_alerts:
            severity_color = "red" if alert["severity"] == "critical" else "yellow"
            alerts_table.add_row(
                f"[{severity_color}]{alert['severity'].upper()}[/{severity_color}]",
                alert["type"],
                alert["message"],
                alert["timestamp"].strftime("%H:%M:%S"),
            )

        # Create layout sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=8),
        )

        layout["header"].update(Panel(header_text, style="bold white on blue"))
        layout["body"].split_row(Layout(name="left"), Layout(name="right"))

        layout["left"].split_column(Layout(name="health"), Layout(name="endpoints"))

        layout["right"].split_column(Layout(name="metrics"), Layout(name="alerts"))

        layout["footer"].update(
            Panel(
                f"Uptime: {datetime.now() - self.start_time} | Total Alerts: {len(alerts)} | Status: {'🟢 HEALTHY' if health.get('status') == 'healthy' else '🔴 UNHEALTHY'}",
                style="bold white on dark_blue",
            )
        )

        layout["health"].update(Panel(health_table, border_style="cyan"))
        layout["endpoints"].update(Panel(endpoints_table, border_style="green"))
        layout["metrics"].update(Panel(metrics_table, border_style="yellow"))
        layout["alerts"].update(Panel(alerts_table, border_style="red"))

        return layout

    async def monitor_loop(
        self, duration_minutes: int = 60, interval_seconds: int = 10
    ):
        """Main monitoring loop"""
        self.console.print(
            "🚀 [bold green]Starting OpenViking Production Monitor[/bold green]"
        )
        self.console.print(
            f"Monitoring for {duration_minutes} minutes, checking every {interval_seconds} seconds"
        )
        self.console.print("Press Ctrl+C to stop monitoring\n")

        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        try:
            with Live(refresh_per_second=1) as live:
                while datetime.now() < end_time:
                    # Collect metrics
                    health = await self.check_health()
                    metrics = await self.get_performance_metrics()
                    endpoints = await self.test_endpoint_performance()

                    # Check alerts
                    new_alerts = self.check_alerts(health, metrics, endpoints)
                    self.alerts.extend(new_alerts)

                    # Keep only recent alerts (last 50)
                    self.alerts = sorted(
                        self.alerts, key=lambda x: x["timestamp"], reverse=True
                    )[:50]

                    # Store metrics history
                    self.metrics_history.append(
                        {
                            "timestamp": datetime.now(),
                            "health": health,
                            "metrics": metrics,
                            "endpoints": endpoints,
                            "alerts_count": len(new_alerts),
                        }
                    )

                    # Keep only recent history (last 100 entries)
                    self.metrics_history = self.metrics_history[-100:]

                    # Update dashboard
                    dashboard = self.create_dashboard(
                        health, metrics, endpoints, self.alerts
                    )
                    live.update(dashboard)

                    await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            self.console.print(
                "\n⏹️  [bold yellow]Monitoring stopped by user[/bold yellow]"
            )

        # Generate summary report
        self.generate_summary_report()

    def generate_summary_report(self):
        """Generate monitoring summary report"""
        self.console.print("\n📋 [bold blue]Monitoring Summary Report[/bold blue]")
        self.console.print("=" * 50)

        if not self.metrics_history:
            self.console.print("❌ No monitoring data collected")
            return

        # Calculate statistics
        total_checks = len(self.metrics_history)
        healthy_checks = len(
            [h for h in self.metrics_history if h["health"].get("status") == "healthy"]
        )
        uptime_percentage = (
            (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        )

        # Average response times
        avg_health_response = (
            sum(h["health"].get("response_time_ms", 0) for h in self.metrics_history)
            / total_checks
            if total_checks > 0
            else 0
        )

        # Alert summary
        critical_alerts = len([a for a in self.alerts if a["severity"] == "critical"])
        warning_alerts = len([a for a in self.alerts if a["severity"] == "warning"])

        self.console.print(
            f"📊 Monitoring Period: {self.metrics_history[0]['timestamp']} to {self.metrics_history[-1]['timestamp']}"
        )
        self.console.print(
            f"🟢 Uptime: {uptime_percentage:.1f}% ({healthy_checks}/{total_checks} healthy checks)"
        )
        self.console.print(
            f"⚡ Average Health Response Time: {avg_health_response:.1f}ms"
        )
        self.console.print(
            f"🚨 Total Alerts: {len(self.alerts)} ({critical_alerts} critical, {warning_alerts} warnings)"
        )

        # Save detailed report
        report_data = {
            "monitoring_period": {
                "start": self.metrics_history[0]["timestamp"].isoformat()
                if self.metrics_history
                else None,
                "end": self.metrics_history[-1]["timestamp"].isoformat()
                if self.metrics_history
                else None,
                "duration_minutes": len(self.metrics_history) * 10 / 60
                if self.metrics_history
                else 0,
            },
            "uptime": {
                "percentage": uptime_percentage,
                "healthy_checks": healthy_checks,
                "total_checks": total_checks,
            },
            "performance": {"avg_health_response_ms": avg_health_response},
            "alerts": {
                "total": len(self.alerts),
                "critical": critical_alerts,
                "warnings": warning_alerts,
                "details": self.alerts,
            },
            "metrics_history": [
                {
                    "timestamp": h["timestamp"].isoformat(),
                    "health_status": h["health"].get("status"),
                    "response_time_ms": h["health"].get("response_time_ms", 0),
                    "alerts_count": h["alerts_count"],
                }
                for h in self.metrics_history[-20:]  # Last 20 entries
            ],
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"openviking_monitoring_report_{timestamp}.json", "w") as f:
            json.dump(report_data, f, indent=2)

        self.console.print(
            f"📄 Detailed report saved: openviking_monitoring_report_{timestamp}.json"
        )


async def main():
    """Main entry point"""
    import sys

    # Get monitoring duration from command line args
    duration_minutes = 10  # Default 10 minutes for demo
    if len(sys.argv) > 1:
        try:
            duration_minutes = int(sys.argv[1])
        except ValueError:
            print("Usage: python openviking_monitor.py [duration_minutes]")
            return 1

    monitor = OpenVikingMonitor()
    await monitor.monitor_loop(duration_minutes=duration_minutes, interval_seconds=5)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
