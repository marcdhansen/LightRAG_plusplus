"""
DSPy Phase 2: Real-time Performance Monitoring

This module provides real-time monitoring and feedback collection for DSPy prompts
in production, enabling continuous optimization and automated decision-making.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from ..config import get_dspy_config
from ..optimizers.ab_integration import DSPyABIntegration


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics for a prompt variant."""

    variant: str
    model: str
    timestamp: datetime
    latency_ms: float
    success: bool
    quality_score: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class AlertConfig:
    """Configuration for performance alerts."""

    metric_name: str
    threshold: float
    comparison: str  # 'greater_than', 'less_than', 'absolute_change'
    window_minutes: int = 5
    min_samples: int = 10

    def is_triggered(self, current_value: float, baseline_value: float) -> bool:
        """Check if alert is triggered."""
        if self.comparison == "greater_than":
            return current_value > self.threshold
        elif self.comparison == "less_than":
            return current_value < self.threshold
        elif self.comparison == "absolute_change":
            return abs(current_value - baseline_value) > self.threshold
        return False


class RealTimeMonitor:
    """Real-time performance monitoring for DSPy prompts."""

    def __init__(self, window_size_minutes: int = 60):
        self.config = get_dspy_config()
        self.ab_integration = DSPyABIntegration()

        # Performance tracking
        self.window_size = timedelta(minutes=window_size_minutes)
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_metrics = defaultdict(lambda: defaultdict(list))

        # Alerting
        self.alert_configs: List[AlertConfig] = []
        self.alert_callbacks: List[Callable] = []
        self.baseline_metrics = {}

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitoring_active = False
        self.monitor_thread = None

        # Storage
        self.metrics_file = Path("realtime_metrics.jsonl")
        self.alerts_file = Path("performance_alerts.jsonl")

        self.logger = logging.getLogger(__name__)

    def add_metric(self, metrics: PerformanceMetrics):
        """Add a new performance metric to the monitoring buffer."""
        self.metrics_buffer[f"{metrics.variant}_{metrics.model}"].append(metrics)

        # Write to file for persistence
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")

        # Trigger alert checks
        self._check_alerts(metrics)

    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check if any alerts should be triggered."""
        if not self.alert_configs:
            return

        # Get recent metrics for this variant/model
        key = f"{metrics.variant}_{metrics.model}"
        recent_metrics = [
            m
            for m in self.metrics_buffer[key]
            if datetime.now() - m.timestamp <= timedelta(minutes=10)
        ]

        if len(recent_metrics) < 10:  # Need sufficient data
            return

        # Calculate current metrics
        current_stats = self._calculate_window_stats(recent_metrics)

        for alert_config in self.alert_configs:
            baseline_value = self.baseline_metrics.get(
                f"{key}_{alert_config.metric_name}", 0
            )

            if alert_config.metric_name in current_stats:
                current_value = current_stats[alert_config.metric_name]

                if alert_config.is_triggered(current_value, baseline_value):
                    alert_data = {
                        "timestamp": datetime.now().isoformat(),
                        "variant": metrics.variant,
                        "model": metrics.model,
                        "alert_config": asdict(alert_config),
                        "current_value": current_value,
                        "baseline_value": baseline_value,
                        "triggering_metric": metrics.to_dict(),
                    }

                    self._trigger_alert(alert_data)

    def _trigger_alert(self, alert_data: Dict[str, Any]):
        """Trigger performance alert."""
        # Write alert to file
        with open(self.alerts_file, "a") as f:
            f.write(json.dumps(alert_data) + "\n")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

        self.logger.warning(
            f"Performance alert triggered: {alert_data['variant']} on {alert_data['model']}"
        )

    def _calculate_window_stats(
        self, metrics: List[PerformanceMetrics]
    ) -> Dict[str, float]:
        """Calculate statistics for a window of metrics."""
        if not metrics:
            return {}

        successful_metrics = [m for m in metrics if m.success]

        stats = {
            "latency_mean": sum(m.latency_ms for m in successful_metrics)
            / len(successful_metrics)
            if successful_metrics
            else 0,
            "success_rate": len(successful_metrics) / len(metrics),
            "quality_mean": sum(m.quality_score or 0 for m in successful_metrics)
            / len(successful_metrics)
            if successful_metrics
            else 0,
            "throughput": len(metrics)
            / max(
                (m.timestamp - min(m.timestamp for m in metrics)).total_seconds() / 60,
                1,
            ),
        }

        return stats

    def get_current_performance(
        self,
        variant: Optional[str] = None,
        model: Optional[str] = None,
        window_minutes: int = 10,
    ) -> Dict[str, Any]:
        """Get current performance statistics."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        results = {}

        for key, metrics_deque in self.metrics_buffer.items():
            current_variant, current_model = key.split("_", 1)

            # Apply filters
            if variant and current_variant != variant:
                continue
            if model and current_model != model:
                continue

            # Filter by time window
            recent_metrics = [m for m in metrics_deque if m.timestamp >= cutoff_time]

            if recent_metrics:
                stats = self._calculate_window_stats(recent_metrics)
                results[key] = {
                    "variant": current_variant,
                    "model": current_model,
                    "sample_size": len(recent_metrics),
                    "window_minutes": window_minutes,
                    "stats": stats,
                }

        return results

    def add_alert_config(self, config: AlertConfig):
        """Add alert configuration."""
        self.alert_configs.append(config)
        self.logger.info(f"Added alert config for {config.metric_name}")

    def add_alert_callback(self, callback: Callable):
        """Add alert callback function."""
        self.alert_callbacks.append(callback)

    def set_baseline_metrics(self, baseline: Dict[str, float]):
        """Set baseline metrics for comparison."""
        self.baseline_metrics.update(baseline)
        self.logger.info(f"Updated baseline metrics with {len(baseline)} values")

    def start_monitoring(self, check_interval_seconds: int = 60):
        """Start real-time monitoring thread."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(check_interval_seconds,), daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Started real-time monitoring")

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped real-time monitoring")

    def _monitoring_loop(self, check_interval_seconds: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Perform periodic health checks
                self._perform_health_checks()

                # Cleanup old metrics
                self._cleanup_old_metrics()

                # Generate periodic reports
                self._generate_periodic_report()

                time.sleep(check_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval_seconds)

    def _perform_health_checks(self):
        """Perform health checks on monitored variants."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=5)

        for key, metrics_deque in self.metrics_buffer.items():
            # Check if we're receiving recent data
            recent_metrics = [m for m in metrics_deque if m.timestamp >= cutoff_time]

            if not recent_metrics:
                self.logger.warning(f"No recent data for {key} in last 5 minutes")

    def _cleanup_old_metrics(self):
        """Clean up old metrics beyond window size."""
        cutoff_time = datetime.now() - self.window_size

        for key, metrics_deque in self.metrics_buffer.items():
            while metrics_deque and metrics_deque[0].timestamp < cutoff_time:
                metrics_deque.popleft()

    def _generate_periodic_report(self):
        """Generate periodic performance report."""
        current_perf = self.get_current_performance()

        if current_perf:
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_variants": len(current_perf),
                "performance_summary": {},
            }

            for key, data in current_perf.items():
                stats = data["stats"]
                report["performance_summary"][key] = {
                    "latency": stats.get("latency_mean", 0),
                    "success_rate": stats.get("success_rate", 0),
                    "quality": stats.get("quality_mean", 0),
                    "throughput": stats.get("throughput", 0),
                    "sample_size": data["sample_size"],
                }

            # Save report
            report_file = Path(
                f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)


class PerformanceFeedbackCollector:
    """Collects feedback for real-time optimization."""

    def __init__(self):
        self.feedback_buffer = deque(maxlen=1000)
        self.optimization_candidates = []
        self.logger = logging.getLogger(__name__)

    def collect_feedback(
        self,
        variant: str,
        model: str,
        user_feedback: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ):
        """Collect user feedback on prompt performance."""
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "variant": variant,
            "model": model,
            "feedback": user_feedback,
            "context": context or {},
        }

        self.feedback_buffer.append(feedback_data)
        self._process_feedback(feedback_data)

    def _process_feedback(self, feedback_data: Dict[str, Any]):
        """Process feedback and identify optimization opportunities."""
        variant = feedback_data["variant"]
        feedback = feedback_data["feedback"]

        # Check for negative feedback patterns
        if feedback.get("rating", 5) <= 2 or feedback.get("helpful", True) is False:
            self.optimization_candidates.append(
                {
                    "variant": variant,
                    "reason": "negative_feedback",
                    "feedback_data": feedback_data,
                    "priority": "high",
                }
            )

        # Check for specific issues
        if "issues" in feedback:
            for issue in feedback["issues"]:
                if issue in ["hallucination", "irrelevant", "incomplete"]:
                    self.optimization_candidates.append(
                        {
                            "variant": variant,
                            "reason": f"issue_{issue}",
                            "feedback_data": feedback_data,
                            "priority": "medium",
                        }
                    )

    def get_optimization_candidates(self) -> List[Dict[str, Any]]:
        """Get variants that need optimization."""
        # Sort by priority and recency
        candidates = sorted(
            self.optimization_candidates,
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x["priority"]],
                x["feedback_data"]["timestamp"],
            ),
        )
        return candidates

    def clear_candidates(self):
        """Clear optimization candidates."""
        self.optimization_candidates.clear()


# Integration decorator for LightRAG
def monitor_performance(variant_getter: Callable):
    """Decorator to automatically monitor LightRAG prompt performance."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            variant = variant_getter(*args, **kwargs)
            model = kwargs.get("model", "default")

            try:
                result = func(*args, **kwargs)
                success = True
                quality_score = (
                    result.get("quality_score") if isinstance(result, dict) else None
                )
            except Exception as e:
                success = False
                quality_score = None
                result = {"error": str(e)}

            # Record metrics
            latency_ms = (time.time() - start_time) * 1000

            metrics = PerformanceMetrics(
                variant=variant,
                model=model,
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                success=success,
                quality_score=quality_score,
            )

            # Add to global monitor if available
            if hasattr(wrapper, "_monitor"):
                wrapper._monitor.add_metric(metrics)

            return result

        return wrapper

    return decorator


# Global monitor instance
_global_monitor: Optional[RealTimeMonitor] = None


def get_global_monitor() -> RealTimeMonitor:
    """Get or create global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = RealTimeMonitor()
    return _global_monitor


# Utility functions
def setup_default_alerts(monitor: RealTimeMonitor):
    """Set up default performance alerts."""
    alerts = [
        AlertConfig("latency_mean", 5000, "greater_than"),  # 5 second latency alert
        AlertConfig("success_rate", 0.9, "less_than"),  # 90% success rate alert
        AlertConfig("quality_mean", 0.7, "less_than"),  # 70% quality alert
        AlertConfig("success_rate", 0.1, "absolute_change"),  # 10% drop in success rate
    ]

    for alert in alerts:
        monitor.add_alert_config(alert)


def log_alert_callback(alert_data: Dict[str, Any]):
    """Default alert callback that logs to file."""
    log_file = Path("performance_alerts.log")
    with open(log_file, "a") as f:
        f.write(
            f"[{alert_data['timestamp']}] ALERT: {alert_data['variant']} on {alert_data['model']}\n"
        )
        f.write(f"  Metric: {alert_data['alert_config']['metric_name']}\n")
        f.write(f"  Current: {alert_data['current_value']:.3f}\n")
        f.write(f"  Baseline: {alert_data['baseline_value']:.3f}\n")
        f.write("\n")


# CLI interface
async def main():
    """Run real-time monitoring from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DSPy Real-time Performance Monitoring"
    )
    parser.add_argument(
        "--window-minutes", type=int, default=60, help="Monitoring window size"
    )
    parser.add_argument(
        "--check-interval", type=int, default=60, help="Health check interval"
    )
    parser.add_argument("--variant", type=str, help="Monitor specific variant")
    parser.add_argument("--model", type=str, help="Monitor specific model")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create monitor
    monitor = RealTimeMonitor(window_size_minutes=args.window_minutes)

    # Setup default alerts
    setup_default_alerts(monitor)
    monitor.add_alert_callback(log_alert_callback)

    # Start monitoring
    monitor.start_monitoring(check_interval_seconds=args.check_interval)

    print(f"🔍 Started real-time monitoring (window: {args.window_minutes} minutes)")
    print("Press Ctrl+C to stop")

    try:
        # Show current performance periodically
        while True:
            await asyncio.sleep(30)

            current_perf = monitor.get_current_performance(
                variant=args.variant, model=args.model, window_minutes=5
            )

            if current_perf:
                print(
                    f"\n📊 Current Performance ({datetime.now().strftime('%H:%M:%S')}):"
                )
                for key, data in current_perf.items():
                    stats = data["stats"]
                    print(f"  {key}:")
                    print(f"    Latency: {stats.get('latency_mean', 0):.1f}ms")
                    print(f"    Success: {stats.get('success_rate', 0):.1%}")
                    print(f"    Quality: {stats.get('quality_mean', 0):.2f}")
                    print(f"    Samples: {data['sample_size']}")

    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitoring...")
        monitor.stop_monitoring()
        print("✅ Monitoring stopped")


if __name__ == "__main__":
    asyncio.run(main())
