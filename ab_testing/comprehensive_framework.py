#!/usr/bin/env python3
"""
Production-Grade A/B Testing Framework for LightRAG
Comprehensive system with real-time monitoring, statistical analysis, and automated decision making
"""

import asyncio
import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    SETUP = "setup"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class VariantType(str, Enum):
    CONTROL = "control"
    TREATMENT = "treatment"
    CANARY = "canary"


@dataclass
class ExperimentVariant:
    """Configuration for an experiment variant"""

    name: str
    type: VariantType
    traffic_percentage: float
    endpoint: str
    headers: dict[str, str] = None
    config: dict[str, Any] = None


@dataclass
class ExperimentMetrics:
    """Metrics collected for a single request"""

    response_time_ms: float
    status_code: int
    success: bool
    error_message: str = ""
    token_usage: int = 0
    cache_hit: bool = False
    custom_metrics: dict[str, float] = None


class ExperimentConfig(BaseModel):
    """Complete experiment configuration"""

    name: str = Field(..., description="Unique experiment name")
    description: str = Field("", description="Experiment description")
    variants: list[ExperimentVariant] = Field(..., description="Test variants")
    traffic_split_type: str = Field("hash", description="Traffic splitting method")
    sample_size: int = Field(1000, description="Target sample size per variant")
    confidence_level: float = Field(0.95, description="Statistical confidence level")
    min_effect_size: float = Field(0.05, description="Minimum detectable effect size")
    duration_hours: int = Field(24, description="Maximum experiment duration")
    auto_rollout_enabled: bool = Field(False, description="Enable automatic rollout")
    rollout_threshold: float = Field(
        0.9, description="Confidence threshold for rollout"
    )

    class Config:
        arbitrary_types_allowed = True


class MetricsCollector:
    """Real-time metrics collection and aggregation"""

    def __init__(self):
        self.logger = structlog.get_logger()
        self.metrics: list[dict[str, Any]] = []
        self.variant_metrics: dict[str, list[ExperimentMetrics]] = {}

    def record_metric(
        self, variant_name: str, request_id: str, metrics: ExperimentMetrics
    ):
        """Record metrics for a specific variant"""
        metric_record = {
            "timestamp": datetime.now().isoformat(),
            "variant": variant_name,
            "request_id": request_id,
            **asdict(metrics),
        }

        self.metrics.append(metric_record)

        if variant_name not in self.variant_metrics:
            self.variant_metrics[variant_name] = []
        self.variant_metrics[variant_name].append(metrics)

        self.logger.info(
            "metric_recorded",
            variant=variant_name,
            request_id=request_id,
            response_time=metrics.response_time_ms,
            success=metrics.success,
        )

    def get_variant_stats(self, variant_name: str) -> dict[str, Any]:
        """Calculate statistics for a specific variant"""
        if variant_name not in self.variant_metrics:
            return {}

        metrics = self.variant_metrics[variant_name]
        if not metrics:
            return {}

        successful_metrics = [m for m in metrics if m.success]

        stats = {
            "total_requests": len(metrics),
            "successful_requests": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(metrics) * 100,
            "avg_response_time_ms": statistics.mean(
                [m.response_time_ms for m in successful_metrics]
            )
            if successful_metrics
            else 0,
            "median_response_time_ms": statistics.median(
                [m.response_time_ms for m in successful_metrics]
            )
            if successful_metrics
            else 0,
            "p95_response_time_ms": self._percentile(
                [m.response_time_ms for m in successful_metrics], 95
            )
            if successful_metrics
            else 0,
            "total_tokens": sum([m.token_usage for m in successful_metrics]),
            "cache_hit_rate": sum([1 for m in metrics if m.cache_hit])
            / len(metrics)
            * 100
            if metrics
            else 0,
        }

        return stats

    def _percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def export_metrics(self, file_path: str):
        """Export all metrics to JSON file"""
        with open(file_path, "w") as f:
            json.dump(self.metrics, f, indent=2)

        # Also export summary statistics
        summary = {
            "export_timestamp": datetime.now().isoformat(),
            "total_records": len(self.metrics),
            "variant_stats": {
                variant: self.get_variant_stats(variant)
                for variant in self.variant_metrics.keys()
            },
        }

        summary_path = file_path.replace(".json", "_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)


class TrafficSplitter:
    """Intelligent traffic splitting for experiments"""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.logger = structlog.get_logger()

    def assign_variant(self, user_id: str, session_id: str = "") -> str:
        """Assign a user to a variant based on traffic splitting method"""
        if self.config.traffic_split_type == "hash":
            return self._hash_assignment(user_id, session_id)
        elif self.config.traffic_split_type == "random":
            return self._random_assignment()
        elif self.config.traffic_split_type == "round_robin":
            return self._round_robin_assignment()
        else:
            raise ValueError(
                f"Unknown traffic split type: {self.config.traffic_split_type}"
            )

    def _hash_assignment(self, user_id: str, session_id: str) -> str:
        """Consistent hash-based assignment"""
        hash_input = f"{user_id}:{session_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        cumulative_percentage = 0
        for variant in self.config.variants:
            cumulative_percentage += variant.traffic_percentage
            if hash_value % 100 < cumulative_percentage:
                return variant.name

        return self.config.variants[-1].name  # Fallback

    def _random_assignment(self) -> str:
        """Random assignment based on traffic percentages"""
        import random

        rand_value = random.uniform(0, 100)

        cumulative_percentage = 0
        for variant in self.config.variants:
            cumulative_percentage += variant.traffic_percentage
            if rand_value <= cumulative_percentage:
                return variant.name

        return self.config.variants[-1].name  # Fallback

    def _round_robin_assignment(self) -> str:
        """Round-robin assignment (simplified)"""
        # This would need state management for true round-robin
        return self._random_assignment()


class StatisticalAnalyzer:
    """Statistical analysis and significance testing"""

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.logger = structlog.get_logger()

    def compare_variants(
        self,
        control_metrics: list[ExperimentMetrics],
        treatment_metrics: list[ExperimentMetrics],
    ) -> dict[str, Any]:
        """Compare two variants using statistical tests"""

        if not control_metrics or not treatment_metrics:
            return {"error": "Insufficient data for analysis"}

        control_success = [m.success for m in control_metrics]
        treatment_success = [m.success for m in treatment_metrics]

        control_response_times = [
            m.response_time_ms for m in control_metrics if m.success
        ]
        treatment_response_times = [
            m.response_time_ms for m in treatment_metrics if m.success
        ]

        analysis = {
            "control_size": len(control_metrics),
            "treatment_size": len(treatment_metrics),
            "control_success_rate": sum(control_success) / len(control_success) * 100,
            "treatment_success_rate": sum(treatment_success)
            / len(treatment_success)
            * 100,
            "control_avg_response_time": statistics.mean(control_response_times)
            if control_response_times
            else 0,
            "treatment_avg_response_time": statistics.mean(treatment_response_times)
            if treatment_response_times
            else 0,
        }

        # Calculate improvements
        if analysis["control_success_rate"] > 0:
            analysis["success_rate_improvement"] = (
                (analysis["treatment_success_rate"] - analysis["control_success_rate"])
                / analysis["control_success_rate"]
                * 100
            )
        else:
            analysis["success_rate_improvement"] = 0

        if analysis["control_avg_response_time"] > 0:
            analysis["response_time_improvement"] = (
                (
                    analysis["control_avg_response_time"]
                    - analysis["treatment_avg_response_time"]
                )
                / analysis["control_avg_response_time"]
                * 100
            )
        else:
            analysis["response_time_improvement"] = 0

        # Statistical significance (simplified t-test)
        analysis["significance"] = self._calculate_significance(
            control_response_times, treatment_response_times
        )

        # Determine winner
        analysis["winner"] = self._determine_winner(analysis)

        return analysis

    def _calculate_significance(
        self, control_times: list[float], treatment_times: list[float]
    ) -> dict[str, Any]:
        """Calculate statistical significance (simplified implementation)"""
        if len(control_times) < 30 or len(treatment_times) < 30:
            return {
                "significant": False,
                "p_value": 1.0,
                "method": "insufficient_sample",
            }

        # Simplified t-test calculation
        from math import sqrt

        control_mean = statistics.mean(control_times)
        treatment_mean = statistics.mean(treatment_times)
        control_std = statistics.stdev(control_times) if len(control_times) > 1 else 0
        treatment_std = (
            statistics.stdev(treatment_times) if len(treatment_times) > 1 else 0
        )

        n1, n2 = len(control_times), len(treatment_times)

        if control_std == 0 and treatment_std == 0:
            return {"significant": False, "p_value": 1.0, "method": "no_variance"}

        # Pooled standard error
        pooled_se = sqrt(
            ((n1 - 1) * control_std**2 + (n2 - 1) * treatment_std**2)
            / (n1 + n2 - 2)
            * (1 / n1 + 1 / n2)
        )

        if pooled_se == 0:
            return {
                "significant": False,
                "p_value": 1.0,
                "method": "zero_standard_error",
            }

        t_statistic = (treatment_mean - control_mean) / pooled_se

        # Simplified p-value approximation (would use scipy.stats.t.cdf in production)
        abs_t = abs(t_statistic)
        if abs_t > 2.58:
            p_value = 0.01
        elif abs_t > 1.96:
            p_value = 0.05
        elif abs_t > 1.65:
            p_value = 0.10
        else:
            p_value = 0.20

        return {
            "significant": p_value < (1 - self.confidence_level),
            "p_value": p_value,
            "method": "t_test",
            "t_statistic": t_statistic,
        }

    def _determine_winner(self, analysis: dict[str, Any]) -> str:
        """Determine the winning variant based on analysis"""
        if not analysis.get("significant", False):
            return "no_significant_difference"

        # Primary metric: response time improvement
        response_improvement = analysis.get("response_time_improvement", 0)
        success_improvement = analysis.get("success_rate_improvement", 0)

        # Weighted decision
        weighted_score = response_improvement * 0.7 + success_improvement * 0.3

        if weighted_score > 5:  # 5% minimum improvement threshold
            return "treatment"
        elif weighted_score < -5:
            return "control"
        else:
            return "no_significant_difference"


class ExperimentEngine:
    """Main experiment orchestration engine"""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.status = ExperimentStatus.SETUP
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        self.metrics_collector = MetricsCollector()
        self.traffic_splitter = TrafficSplitter(config)
        self.statistical_analyzer = StatisticalAnalyzer(config.confidence_level)

        self.logger = structlog.get_logger()

    async def start_experiment(self) -> bool:
        """Start the experiment"""
        try:
            self.start_time = datetime.now()
            self.status = ExperimentStatus.RUNNING

            self.logger.info(
                "experiment_started",
                experiment=self.config.name,
                variants=[v.name for v in self.config.variants],
            )
            return True

        except Exception as e:
            self.logger.error("experiment_start_failed", error=str(e))
            self.status = ExperimentStatus.FAILED
            return False

    async def execute_request(
        self, request_data: dict[str, Any], user_id: str, session_id: str = ""
    ) -> dict[str, Any]:
        """Execute a request through the experiment"""
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Experiment not running, current status: {self.status}")

        # Assign variant
        variant_name = self.traffic_splitter.assign_variant(user_id, session_id)
        variant = next(
            (v for v in self.config.variants if v.name == variant_name), None
        )

        if not variant:
            raise ValueError(f"Variant not found: {variant_name}")

        # Execute request
        request_id = f"{int(time.time() * 1000)}_{hash(user_id) % 10000}"
        start_time = time.time()

        try:
            # Make HTTP request to variant endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    variant.endpoint, json=request_data, headers=variant.headers or {}
                )

                response_time = (time.time() - start_time) * 1000

                # Extract response data
                response_data = (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )

                # Record metrics
                metrics = ExperimentMetrics(
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    success=response.status_code == 200,
                    token_usage=response_data.get("token_usage", 0),
                    cache_hit=response_data.get("cache_hit", False),
                    error_message=""
                    if response.status_code == 200
                    else f"HTTP {response.status_code}",
                )

                self.metrics_collector.record_metric(variant_name, request_id, metrics)

                return {
                    "variant": variant_name,
                    "request_id": request_id,
                    "response_data": response_data,
                    "metrics": metrics,
                }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            metrics = ExperimentMetrics(
                response_time_ms=response_time,
                status_code=0,
                success=False,
                error_message=str(e),
            )

            self.metrics_collector.record_metric(variant_name, request_id, metrics)

            return {
                "variant": variant_name,
                "request_id": request_id,
                "error": str(e),
                "metrics": metrics,
            }

    def get_experiment_status(self) -> dict[str, Any]:
        """Get current experiment status and statistics"""
        variant_stats = {}
        for variant in self.config.variants:
            variant_stats[variant.name] = self.metrics_collector.get_variant_stats(
                variant.name
            )

        status_data = {
            "experiment_name": self.config.name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_hours": (datetime.now() - self.start_time).total_seconds() / 3600
            if self.start_time
            else 0,
            "variant_stats": variant_stats,
            "total_requests": sum(
                stats.get("total_requests", 0) for stats in variant_stats.values()
            ),
        }

        # Check if experiment should end
        if self.status == ExperimentStatus.RUNNING:
            total_requests = status_data["total_requests"]
            target_requests = self.config.sample_size * len(self.config.variants)
            duration = status_data["duration_hours"]

            if (
                total_requests >= target_requests
                or duration >= self.config.duration_hours
            ):
                status_data["should_end"] = True
            else:
                status_data["should_end"] = False

        return status_data

    async def end_experiment(self) -> dict[str, Any]:
        """End experiment and generate final analysis"""
        self.status = ExperimentStatus.COMPLETED
        self.end_time = datetime.now()

        # Generate final analysis
        variant_names = [v.name for v in self.config.variants]
        if len(variant_names) >= 2:
            control_name = variant_names[0]
            treatment_name = variant_names[1]

            control_metrics = self.metrics_collector.variant_metrics.get(
                control_name, []
            )
            treatment_metrics = self.metrics_collector.variant_metrics.get(
                treatment_name, []
            )

            analysis = self.statistical_analyzer.compare_variants(
                control_metrics, treatment_metrics
            )
        else:
            analysis = {"error": "Need at least 2 variants for comparison"}

        # Export metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"ab_experiment_{self.config.name}_{timestamp}.json"
        self.metrics_collector.export_metrics(export_path)

        final_report = {
            "experiment": self.config.name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": (self.end_time - self.start_time).total_seconds() / 3600
            if self.start_time and self.end_time
            else 0,
            "analysis": analysis,
            "metrics_export": export_path,
            "variant_stats": {
                variant.name: self.metrics_collector.get_variant_stats(variant.name)
                for variant in self.config.variants
            },
        }

        self.logger.info(
            "experiment_completed",
            experiment=self.config.name,
            winner=analysis.get("winner", "unknown"),
        )

        return final_report


# Convenience functions for creating common experiment configurations
def create_openviking_experiment(
    openviking_url: str = "http://localhost:8000",
    smp_url: str = "http://localhost:9621",
) -> ExperimentConfig:
    """Create a standard OpenViking vs SMP experiment"""

    variants = [
        ExperimentVariant(
            name="openviking",
            type=VariantType.TREATMENT,
            traffic_percentage=50.0,
            endpoint=f"{openviking_url}/embeddings",
            headers={"Content-Type": "application/json"},
        ),
        ExperimentVariant(
            name="smp",
            type=VariantType.CONTROL,
            traffic_percentage=50.0,
            endpoint=f"{smp_url}/embeddings",
            headers={"Content-Type": "application/json"},
        ),
    ]

    return ExperimentConfig(
        name="openviking_vs_smp",
        description="Compare OpenViking vs SMP embedding performance",
        variants=variants,
        sample_size=500,
        confidence_level=0.95,
        min_effect_size=0.05,
        duration_hours=24,
        auto_rollout_enabled=False,
    )


if __name__ == "__main__":
    import asyncio

    async def demo_experiment():
        """Demonstration of the A/B testing framework"""

        # Create experiment configuration
        config = create_openviking_experiment()

        # Initialize experiment engine
        engine = ExperimentEngine(config)

        # Start experiment
        await engine.start_experiment()

        # Simulate some requests
        test_requests = [
            {"text": "React performance optimization"},
            {"text": "Database schema design"},
            {"text": "API authentication patterns"},
            {"text": "Security implementation"},
            {"text": "Cloud architecture"},
        ]

        for i, request_data in enumerate(test_requests):
            result = await engine.execute_request(
                request_data=request_data,
                user_id=f"user_{i}",
                session_id=f"session_{i % 3}",
            )
            print(
                f"Request {i + 1}: Variant={result['variant']}, Success={result['metrics'].success}"
            )

        # Get status
        status = engine.get_experiment_status()
        print(f"Experiment Status: {json.dumps(status, indent=2)}")

        # End experiment
        final_report = await engine.end_experiment()
        print(f"Final Report: {json.dumps(final_report, indent=2)}")

    asyncio.run(demo_experiment())
