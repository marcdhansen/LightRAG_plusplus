"""
DSPy Phase 2: Real-time Optimization Engine

This module implements real-time optimization of DSPy prompts based on production feedback,
creating a self-improving system that continuously adapts to changing conditions.
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import get_dspy_config
from .production_pipeline import ProductionDataPipeline
from .prompt_replacement import PromptReplacementPipeline
from .realtime_monitoring import PerformanceMetrics, RealTimeMonitor


class OptimizationTrigger(Enum):
    """Triggers for real-time optimization."""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    FEEDBACK_VOLUME = "feedback_volume"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    MODEL_DRIFT = "model_drift"
    DATA_SHIFT = "data_shift"


@dataclass
class OptimizationEvent:
    """An optimization event and its metadata."""

    event_id: str
    trigger: OptimizationTrigger
    prompt_family: str
    variant: str
    model: str
    performance_drop: float
    feedback_score: float
    timestamp: datetime
    optimization_started: datetime | None = None
    optimization_completed: datetime | None = None
    result: dict[str, Any] | None = None
    status: str = "pending"  # pending, running, completed, failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["trigger"] = self.trigger.value
        data["timestamp"] = self.timestamp.isoformat()
        if self.optimization_started:
            data["optimization_started"] = self.optimization_started.isoformat()
        if self.optimization_completed:
            data["optimization_completed"] = self.optimization_completed.isoformat()
        return data


@dataclass
class OptimizationConfig:
    """Configuration for real-time optimization."""

    enable_automatic_optimization: bool = True
    performance_degradation_threshold: float = 0.15  # 15% drop triggers optimization
    feedback_volume_threshold: int = 50  # 50 feedback items trigger optimization
    optimization_interval_hours: int = 24  # Minimum 24 hours between optimizations
    max_concurrent_optimizations: int = 3
    feedback_window_hours: int = 6  # Look at last 6 hours of feedback
    min_confidence_for_deployment: float = 0.8
    rollback_on_failure: bool = True
    optimization_timeout_minutes: int = 30


class RealTimeOptimizer:
    """Real-time optimization engine for DSPy prompts."""

    def __init__(self, config: OptimizationConfig | None = None):
        self.config = config or OptimizationConfig()
        self.dspy_config = get_dspy_config()

        # Components
        self.monitor = RealTimeMonitor()
        self.production_pipeline = ProductionDataPipeline()
        self.replacement_pipeline = PromptReplacementPipeline()

        # Optimization state
        self.active_optimizations: dict[str, OptimizationEvent] = {}
        self.optimization_history: deque = deque(maxlen=1000)
        self.feedback_buffer: deque = deque(maxlen=10000)

        # Performance baselines
        self.performance_baselines: dict[str, dict[str, float]] = {}
        self.last_optimization_times: dict[str, datetime] = {}

        # Optimization callbacks
        self.optimization_callbacks: list[Callable] = []

        # State tracking
        self.optimization_active = False
        self.scheduler_task: asyncio.Task | None = None

        self.logger = logging.getLogger(__name__)

        # Load existing state
        self._load_state()

    async def start(self):
        """Start the real-time optimization engine."""
        if self.optimization_active:
            return

        self.optimization_active = True

        # Start monitoring
        self.monitor.start_monitoring(check_interval_seconds=30)

        # Start optimization scheduler
        self.scheduler_task = asyncio.create_task(self._optimization_scheduler())

        self.logger.info("🚀 Real-time optimization engine started")

    async def stop(self):
        """Stop the real-time optimization engine."""
        if not self.optimization_active:
            return

        self.optimization_active = False

        # Stop monitoring
        self.monitor.stop_monitoring()

        # Cancel scheduler
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        self.logger.info("⏹️ Real-time optimization engine stopped")

    async def add_feedback(
        self,
        variant: str,
        model: str,
        feedback_score: float,
        feedback_type: str = "quality",
        metadata: dict[str, Any] | None = None,
    ):
        """Add user feedback to the optimization buffer."""

        feedback_data = {
            "timestamp": datetime.now(),
            "variant": variant,
            "model": model,
            "feedback_score": feedback_score,
            "feedback_type": feedback_type,
            "metadata": metadata or {},
        }

        self.feedback_buffer.append(feedback_data)

        # Check if this triggers optimization
        await self._check_feedback_triggers(variant, model)

    async def add_performance_metric(self, metrics: PerformanceMetrics):
        """Add performance metric and check for degradation."""

        # Add to monitor
        self.monitor.add_metric(metrics)

        # Check for performance degradation
        key = f"{metrics.variant}_{metrics.model}"
        await self._check_performance_degradation(key, metrics)

    async def _optimization_scheduler(self):
        """Main optimization scheduler loop."""
        while self.optimization_active:
            try:
                # Check scheduled optimizations
                await self._check_scheduled_optimizations()

                # Process pending optimizations
                await self._process_pending_optimizations()

                # Clean up old data
                await self._cleanup_old_data()

                # Sleep before next cycle
                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in optimization scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _check_performance_degradation(
        self, key: str, current_metrics: PerformanceMetrics
    ):
        """Check if performance has degraded enough to trigger optimization."""

        if not self.config.enable_automatic_optimization:
            return

        # Get current performance
        current_perf = self.monitor.get_current_performance(
            variant=current_metrics.variant,
            model=current_metrics.model,
            window_minutes=10,
        )

        if not current_perf or key not in current_perf:
            return

        perf_data = current_perf[key]["stats"]
        current_success_rate = perf_data.get("success_rate", 1.0)
        current_latency = perf_data.get("latency_mean", 0)

        # Check against baseline
        if key not in self.performance_baselines:
            # Establish baseline
            self.performance_baselines[key] = {
                "success_rate": current_success_rate,
                "latency": current_latency,
                "quality": current_metrics.quality_score or 0.5,
                "established_at": datetime.now(),
            }
            return

        baseline = self.performance_baselines[key]

        # Calculate performance drop
        success_rate_drop = max(0, (baseline["success_rate"] - current_success_rate))
        latency_increase = max(
            0, (current_latency - baseline["latency"]) / max(baseline["latency"], 1)
        )

        # Overall performance degradation
        performance_drop = (success_rate_drop + latency_increase) / 2

        if performance_drop >= self.config.performance_degradation_threshold:
            await self._trigger_optimization(
                trigger=OptimizationTrigger.PERFORMANCE_DEGRADATION,
                variant=current_metrics.variant,
                model=current_metrics.model,
                performance_drop=performance_drop,
                feedback_score=0.0,
            )

    async def _check_feedback_triggers(self, variant: str, model: str):
        """Check if feedback volume triggers optimization."""

        if not self.config.enable_automatic_optimization:
            return

        # Get recent feedback for this variant/model
        cutoff_time = datetime.now() - timedelta(
            hours=self.config.feedback_window_hours
        )
        recent_feedback = [
            f
            for f in self.feedback_buffer
            if f["variant"] == variant
            and f["model"] == model
            and f["timestamp"] >= cutoff_time
        ]

        if len(recent_feedback) >= self.config.feedback_volume_threshold:
            # Calculate average feedback score
            avg_score = sum(f["feedback_score"] for f in recent_feedback) / len(
                recent_feedback
            )

            # Only trigger if feedback is negative
            if avg_score < 0.5:
                await self._trigger_optimization(
                    trigger=OptimizationTrigger.FEEDBACK_VOLUME,
                    variant=variant,
                    model=model,
                    performance_drop=0.0,
                    feedback_score=avg_score,
                )

    async def _check_scheduled_optimizations(self):
        """Check for scheduled optimizations."""

        current_time = datetime.now()

        # Check each variant/model combination
        for key, _baseline in self.performance_baselines.items():
            variant, model = key.split("_", 1)

            # Check if optimization is due
            last_optimization = self.last_optimization_times.get(key)

            if (
                last_optimization is None
                or current_time - last_optimization
                >= timedelta(hours=self.config.optimization_interval_hours)
            ):
                await self._trigger_optimization(
                    trigger=OptimizationTrigger.SCHEDULED,
                    variant=variant,
                    model=model,
                    performance_drop=0.0,
                    feedback_score=0.0,
                )

    async def _trigger_optimization(
        self,
        trigger: OptimizationTrigger,
        variant: str,
        model: str,
        performance_drop: float,
        feedback_score: float,
    ):
        """Trigger an optimization event."""

        # Check if optimization is already in progress
        key = f"{variant}_{model}"
        if key in self.active_optimizations:
            return

        # Check rate limiting
        last_optimization = self.last_optimization_times.get(key)
        if last_optimization and datetime.now() - last_optimization < timedelta(
            hours=self.config.optimization_interval_hours
        ):
            return

        # Check concurrent optimization limit
        if len(self.active_optimizations) >= self.config.max_concurrent_optimizations:
            return

        # Create optimization event
        event_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_optimizations)}"

        event = OptimizationEvent(
            event_id=event_id,
            trigger=trigger,
            prompt_family=self._extract_family_from_variant(variant),
            variant=variant,
            model=model,
            performance_drop=performance_drop,
            feedback_score=feedback_score,
            timestamp=datetime.now(),
        )

        self.active_optimizations[key] = event

        self.logger.info(
            f"🔄 Triggered optimization: {trigger.value} for {variant} on {model} "
            f"(perf_drop: {performance_drop:.2%}, feedback: {feedback_score:.2f})"
        )

    def _extract_family_from_variant(self, variant: str) -> str:
        """Extract prompt family from variant name."""
        if "entity" in variant.lower():
            return "entity_extraction"
        elif "summariz" in variant.lower():
            return "summarization"
        elif "query" in variant.lower():
            return "query_processing"
        else:
            return "unknown"

    async def _process_pending_optimizations(self):
        """Process pending optimization events."""

        if not self.active_optimizations:
            return

        # Process in parallel (up to limit)
        tasks = []

        for key, event in list(self.active_optimizations.items()):
            if event.status == "pending":
                task = asyncio.create_task(self._execute_optimization(key, event))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_optimization(self, key: str, event: OptimizationEvent):
        """Execute a single optimization event."""

        event.status = "running"
        event.optimization_started = datetime.now()

        try:
            self.logger.info(f"🔧 Executing optimization {event.event_id}")

            # Step 1: Gather recent data
            recent_data = await self._gather_optimization_data(
                event.variant, event.model
            )

            # Step 2: Create optimization candidates
            candidates = await self._create_optimization_candidates(event, recent_data)

            # Step 3: Evaluate candidates
            best_candidate = await self._evaluate_optimization_candidates(
                event, candidates
            )

            # Step 4: Deploy if confident enough
            if (
                best_candidate
                and best_candidate["confidence"]
                >= self.config.min_confidence_for_deployment
            ):
                deployment_success = await self._deploy_optimization(
                    event, best_candidate
                )

                if deployment_success:
                    event.status = "completed"
                    event.result = best_candidate

                    # Update baseline
                    self._update_performance_baseline(key, best_candidate)

                    self.logger.info(
                        f"✅ Optimization {event.event_id} completed successfully"
                    )
                else:
                    event.status = "failed"
                    if self.config.rollback_on_failure:
                        await self._rollback_optimization(event)

                    self.logger.error(
                        f"❌ Optimization {event.event_id} deployment failed"
                    )
            else:
                event.status = "failed"
                event.result = {"reason": "Insufficient confidence for deployment"}

                self.logger.warning(
                    f"⚠️ Optimization {event.event_id} insufficient confidence"
                )

        except Exception as e:
            event.status = "failed"
            event.result = {"error": str(e)}

            if self.config.rollback_on_failure:
                await self._rollback_optimization(event)

            self.logger.error(f"💥 Optimization {event.event_id} failed: {e}")

        finally:
            event.optimization_completed = datetime.now()

            # Move from active to history
            self.optimization_history.append(event)
            del self.active_optimizations[key]

            # Update last optimization time
            self.last_optimization_times[key] = datetime.now()

            # Call callbacks
            await self._call_optimization_callbacks(event)

            # Save state
            await self._save_state()

    async def _gather_optimization_data(
        self, variant: str, model: str
    ) -> dict[str, Any]:
        """Gather recent data for optimization."""

        # Get recent performance metrics
        performance_data = self.monitor.get_current_performance(
            variant=variant, model=model, window_minutes=60
        )

        # Get recent feedback
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_feedback = [
            f
            for f in self.feedback_buffer
            if f["variant"] == variant
            and f["model"] == model
            and f["timestamp"] >= cutoff_time
        ]

        # Get production examples
        examples = await self.production_pipeline.collect_production_data(
            hours_back=24, models=[model]
        )

        return {
            "performance": performance_data,
            "feedback": recent_feedback,
            "examples": examples,
            "timestamp": datetime.now(),
        }

    async def _create_optimization_candidates(
        self, event: OptimizationEvent, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Create optimization candidates based on the trigger type."""

        candidates = []

        if event.trigger == OptimizationTrigger.PERFORMANCE_DEGRADATION:
            # Focus on performance improvement
            candidates.extend(await self._create_performance_candidates(event, data))

        elif event.trigger == OptimizationTrigger.FEEDBACK_VOLUME:
            # Focus on quality improvement
            candidates.extend(await self._create_quality_candidates(event, data))

        elif event.trigger == OptimizationTrigger.SCHEDULED:
            # Comprehensive optimization
            candidates.extend(await self._create_comprehensive_candidates(event, data))

        return candidates

    async def _create_performance_candidates(
        self, _event: OptimizationEvent, _data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Create candidates focused on performance improvement."""

        candidates = []

        # Candidate 1: Optimize for speed
        candidates.append(
            {
                "name": "speed_optimized",
                "type": "performance",
                "focus": "latency",
                "description": "Optimize prompt for faster execution",
                "expected_improvement": 0.2,
                "confidence": 0.7,
            }
        )

        # Candidate 2: Optimize for reliability
        candidates.append(
            {
                "name": "reliability_optimized",
                "type": "performance",
                "focus": "success_rate",
                "description": "Optimize prompt for higher success rate",
                "expected_improvement": 0.15,
                "confidence": 0.8,
            }
        )

        return candidates

    async def _create_quality_candidates(
        self, _event: OptimizationEvent, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Create candidates focused on quality improvement."""

        candidates = []

        # Analyze feedback to understand issues
        feedback_issues = self._analyze_feedback_issues(data["feedback"])

        # Candidate 1: Address most common feedback issue
        if feedback_issues:
            candidates.append(
                {
                    "name": "quality_feedback_driven",
                    "type": "quality",
                    "focus": feedback_issues["most_common"],
                    "description": f"Address {feedback_issues['most_common']} issues from user feedback",
                    "expected_improvement": 0.25,
                    "confidence": 0.85,
                }
            )

        # Candidate 2: General quality improvement
        candidates.append(
            {
                "name": "general_quality_optimized",
                "type": "quality",
                "focus": "overall_quality",
                "description": "General quality optimization based on feedback patterns",
                "expected_improvement": 0.15,
                "confidence": 0.75,
            }
        )

        return candidates

    async def _create_comprehensive_candidates(
        self, event: OptimizationEvent, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Create comprehensive optimization candidates."""

        candidates = []

        # Combine performance and quality approaches
        candidates.extend(await self._create_performance_candidates(event, data))
        candidates.extend(await self._create_quality_candidates(event, data))

        # Add a DSPy-optimized variant
        candidates.append(
            {
                "name": "dspy_reoptimized",
                "type": "dspy",
                "focus": "comprehensive",
                "description": "Full DSPy re-optimization with latest data",
                "expected_improvement": 0.3,
                "confidence": 0.9,
            }
        )

        return candidates

    def _analyze_feedback_issues(
        self, feedback: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze feedback to identify common issues."""

        if not feedback:
            return {"most_common": "none", "issues": []}

        # Extract issue types from feedback metadata
        issues = []
        for f in feedback:
            metadata = f.get("metadata", {})
            if "issues" in metadata:
                issues.extend(metadata["issues"])
            elif "issue_type" in metadata:
                issues.append(metadata["issue_type"])

        # Count occurrences
        issue_counts = defaultdict(int)
        for issue in issues:
            issue_counts[issue] += 1

        if not issue_counts:
            return {"most_common": "none", "issues": []}

        # Find most common
        most_common = max(issue_counts.items(), key=lambda x: x[1])

        return {
            "most_common": most_common[0],
            "issues": list(issue_counts.keys()),
            "counts": dict(issue_counts),
        }

    async def _evaluate_optimization_candidates(
        self, event: OptimizationEvent, candidates: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Evaluate optimization candidates and return the best one."""

        if not candidates:
            return None

        best_candidate = None
        best_score = 0

        for candidate in candidates:
            try:
                # Calculate candidate score
                score = self._calculate_candidate_score(event, candidate)
                candidate["calculated_score"] = score

                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            except Exception as e:
                self.logger.warning(
                    f"Failed to evaluate candidate {candidate['name']}: {e}"
                )
                continue

        return best_candidate

    def _calculate_candidate_score(
        self, event: OptimizationEvent, candidate: dict[str, Any]
    ) -> float:
        """Calculate score for an optimization candidate."""

        base_score = candidate.get("confidence", 0.5)
        expected_improvement = candidate.get("expected_improvement", 0.1)

        # Adjust based on trigger type
        if event.trigger == OptimizationTrigger.PERFORMANCE_DEGRADATION:
            if candidate["focus"] == "latency" or candidate["focus"] == "success_rate":
                base_score += 0.2
        elif event.trigger == OptimizationTrigger.FEEDBACK_VOLUME:
            if candidate["type"] == "quality":
                base_score += 0.2

        # Adjust based on expected improvement
        base_score += expected_improvement * 0.5

        # Adjust based on historical performance
        historical_success_rate = self._get_historical_success_rate(candidate["name"])
        base_score *= 1 + historical_success_rate

        return min(1.0, base_score)

    def _get_historical_success_rate(self, candidate_name: str) -> float:
        """Get historical success rate for a candidate type."""
        # Count successful vs failed optimizations for this candidate type
        successful = 0
        total = 0

        for event in self.optimization_history:
            if (
                event.result
                and event.result.get("name") == candidate_name
                and event.status == "completed"
            ):
                successful += 1
                total += 1

        return successful / max(total, 1) - 0.5  # Center around 0

    async def _deploy_optimization(
        self, event: OptimizationEvent, candidate: dict[str, Any]
    ) -> bool:
        """Deploy the optimization candidate."""

        try:
            # This would integrate with the actual deployment system
            # For now, simulate deployment

            # Simulate deployment time
            await asyncio.sleep(2)

            # Simulate deployment success
            success_prob = candidate.get("confidence", 0.7)

            import random

            if random.random() < success_prob:
                self.logger.info(
                    f"🚀 Deployed optimization {candidate['name']} for {event.variant} on {event.model}"
                )
                return True
            else:
                self.logger.warning(f"Deployment failed for {candidate['name']}")
                return False

        except Exception as e:
            self.logger.error(f"Deployment error: {e}")
            return False

    async def _rollback_optimization(self, event: OptimizationEvent):
        """Rollback a failed optimization."""

        try:
            self.logger.info(f"🔄 Rolling back optimization {event.event_id}")

            # Simulate rollback time
            await asyncio.sleep(1)

            self.logger.info(f"✅ Rollback completed for {event.event_id}")

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")

    def _update_performance_baseline(
        self, key: str, optimization_result: dict[str, Any]
    ):
        """Update performance baseline after successful optimization."""

        if key not in self.performance_baselines:
            return

        # Apply expected improvement to baseline
        improvement = optimization_result.get("expected_improvement", 0.1)
        baseline = self.performance_baselines[key]

        # Update baseline (conservative estimate)
        baseline["success_rate"] *= 1 + improvement * 0.8
        baseline["quality"] *= 1 + improvement * 0.8
        baseline["latency"] *= 1 - improvement * 0.5  # Latency should decrease

        baseline["updated_at"] = datetime.now()

        self.logger.info(f"Updated baseline for {key}: {improvement:.1%} improvement")

    async def _call_optimization_callbacks(self, event: OptimizationEvent):
        """Call registered optimization callbacks."""

        for callback in self.optimization_callbacks:
            try:
                await callback(event)
            except Exception as e:
                self.logger.error(f"Optimization callback failed: {e}")

    async def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues."""

        cutoff_time = datetime.now() - timedelta(hours=48)

        # Clean up old feedback
        initial_count = len(self.feedback_buffer)
        self.feedback_buffer = deque(
            (f for f in self.feedback_buffer if f["timestamp"] >= cutoff_time),
            maxlen=10000,
        )

        if len(self.feedback_buffer) < initial_count:
            self.logger.info(
                f"Cleaned up {initial_count - len(self.feedback_buffer)} old feedback items"
            )

    def add_optimization_callback(self, callback: Callable):
        """Add a callback to be called when optimization completes."""
        self.optimization_callbacks.append(callback)

    def get_optimization_status(self) -> dict[str, Any]:
        """Get current optimization status."""

        return {
            "active": self.optimization_active,
            "active_optimizations": len(self.active_optimizations),
            "pending_events": [
                e.to_dict()
                for e in self.active_optimizations.values()
                if e.status == "pending"
            ],
            "running_events": [
                e.to_dict()
                for e in self.active_optimizations.values()
                if e.status == "running"
            ],
            "total_history": len(self.optimization_history),
            "feedback_buffer_size": len(self.feedback_buffer),
            "performance_baselines": self.performance_baselines,
            "last_optimizations": {
                key: last_opt.isoformat()
                for key, last_opt in self.last_optimization_times.items()
            },
        }

    async def _save_state(self):
        """Save optimizer state to file."""

        state = {
            "timestamp": datetime.now().isoformat(),
            "config": asdict(self.config),
            "performance_baselines": self.performance_baselines,
            "last_optimization_times": {
                key: time.isoformat() if isinstance(time, datetime) else time
                for key, time in self.last_optimization_times.items()
            },
            "active_optimizations": {
                key: event.to_dict() for key, event in self.active_optimizations.items()
            },
            "optimization_history": [
                event.to_dict() for event in list(self.optimization_history)[-100:]
            ],  # Last 100
        }

        # Save to file
        state_file = Path("realtime_optimizer_state.json")
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def _load_state(self):
        """Load optimizer state from file."""

        state_file = Path("realtime_optimizer_state.json")
        if not state_file.exists():
            return

        try:
            with open(state_file) as f:
                state = json.load(f)

            # Restore performance baselines
            self.performance_baselines = state.get("performance_baselines", {})

            # Restore last optimization times
            last_opt_times = state.get("last_optimization_times", {})
            self.last_optimization_times = {
                key: datetime.fromisoformat(time) if isinstance(time, str) else time
                for key, time in last_opt_times.items()
            }

            # Restore active optimizations (if any)
            active_opts = state.get("active_optimizations", {})
            for key, event_data in active_opts.items():
                event = OptimizationEvent(**event_data)
                self.active_optimizations[key] = event

            # Restore optimization history
            history_data = state.get("optimization_history", [])
            for event_data in history_data:
                event_data["trigger"] = OptimizationTrigger(event_data["trigger"])
                event_data["timestamp"] = datetime.fromisoformat(
                    event_data["timestamp"]
                )
                if event_data.get("optimization_started"):
                    event_data["optimization_started"] = datetime.fromisoformat(
                        event_data["optimization_started"]
                    )
                if event_data.get("optimization_completed"):
                    event_data["optimization_completed"] = datetime.fromisoformat(
                        event_data["optimization_completed"]
                    )

                event = OptimizationEvent(**event_data)
                self.optimization_history.append(event)

            self.logger.info(
                f"Loaded optimizer state with {len(self.performance_baselines)} baselines"
            )

        except Exception as e:
            self.logger.error(f"Failed to load optimizer state: {e}")


# CLI interface
async def main():
    """Run real-time optimizer from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="DSPy Real-time Optimization Engine")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--start", action="store_true", help="Start the optimizer")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument(
        "--feedback",
        nargs=4,
        metavar=("VARIANT", "MODEL", "SCORE", "TYPE"),
        help="Add feedback (variant model score type)",
    )
    parser.add_argument(
        "--metrics",
        nargs=3,
        metavar=("VARIANT", "MODEL", "LATENCY"),
        help="Add performance metrics (variant model latency_ms)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message}s"
    )

    # Create optimizer
    optimizer = RealTimeOptimizer()

    if args.start:
        print("🚀 Starting real-time optimization engine...")
        await optimizer.start()

        try:
            while True:
                await asyncio.sleep(60)
                status = optimizer.get_optimization_status()
                print(
                    f"\n📊 Status: {status['active_optimizations']} active optimizations"
                )
        except KeyboardInterrupt:
            print("\n⏹️ Stopping optimizer...")
            await optimizer.stop()
            print("✅ Optimizer stopped")

    elif args.status:
        status = optimizer.get_optimization_status()
        print("📊 Real-time Optimizer Status:")
        print(f"  Active: {status['active']}")
        print(f"  Active Optimizations: {status['active_optimizations']}")
        print(f"  Feedback Buffer: {status['feedback_buffer_size']} items")
        print(f"  Performance Baselines: {len(status['performance_baselines'])}")
        print(f"  Total History: {status['total_history']} events")

    elif args.feedback:
        variant, model, score, feedback_type = args.feedback
        await optimizer.add_feedback(variant, model, float(score), feedback_type)
        print(f"✅ Added feedback: {variant} on {model} = {score}")

    elif args.metrics:
        variant, model, latency = args.metrics
        from datetime import datetime

        metrics = PerformanceMetrics(
            variant=variant,
            model=model,
            timestamp=datetime.now(),
            latency_ms=float(latency),
            success=True,
        )

        await optimizer.add_performance_metric(metrics)
        print(f"✅ Added performance metrics: {variant} on {model} = {latency}ms")

    else:
        print("❌ Please specify --start, --status, --feedback, or --metrics")
        return


if __name__ == "__main__":
    asyncio.run(main())
