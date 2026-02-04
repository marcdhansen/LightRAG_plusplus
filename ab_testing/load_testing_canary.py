#!/usr/bin/env python3
"""
Load Testing and Canary Deployment Support for A/B Testing Framework
High-performance load testing with gradual rollout capabilities and automated safety checks
"""

import asyncio
import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
import numpy as np


class CanaryStage(str, Enum):
    """Canary deployment stages"""

    PREPARATION = "preparation"
    INITIAL_TRAFFIC = "initial_traffic"
    GRADUAL_INCREASE = "gradual_increase"
    MONITORING = "monitoring"
    STABILIZATION = "stabilization"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class LoadTestStatus(str, Enum):
    """Load test status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""

    concurrent_users: int = 100
    requests_per_second: int = 50
    duration_seconds: int = 300  # 5 minutes
    ramp_up_time: int = 30  # 30 seconds to full load
    payload_template: dict[str, Any] = None
    endpoints: list[str] = None
    headers: dict[str, str] = None
    timeout: float = 30.0
    retry_attempts: int = 3


@dataclass
class CanaryConfig:
    """Configuration for canary deployment"""

    initial_traffic_percentage: float = 5.0
    max_traffic_percentage: float = 100.0
    traffic_increment: float = 10.0
    monitoring_duration_minutes: int = 5
    stability_threshold: float = 0.95  # 95% success rate required
    rollback_on_failure: bool = True
    auto_promote: bool = True
    max_error_rate: float = 0.05  # 5% max error rate
    max_response_time_ms: float = 5000.0


@dataclass
class LoadTestResult:
    """Results from load testing"""

    status: LoadTestStatus
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    duration_seconds: float
    errors: list[dict[str, Any]]
    timestamps: list[float]
    response_times: list[float]


@dataclass
class CanaryMetrics:
    """Metrics for canary deployment monitoring"""

    timestamp: datetime
    traffic_percentage: float
    total_requests: int
    successful_requests: int
    avg_response_time_ms: float
    error_rate: float
    stage: CanaryStage


class LoadTestRunner:
    """High-performance load testing engine"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.status = LoadTestStatus.PENDING
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None

    async def run_load_test(self, test_name: str = "load_test") -> LoadTestResult:
        """Execute load test with specified configuration"""
        self.status = LoadTestStatus.RUNNING
        self.start_time = time.time()

        print(f"🚀 Starting load test: {test_name}")
        print(f"   Concurrent users: {self.config.concurrent_users}")
        print(f"   Target RPS: {self.config.requests_per_second}")
        print(f"   Duration: {self.config.duration_seconds}s")

        try:
            # Prepare payloads
            payloads = self._prepare_payloads()

            # Create session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.config.concurrent_users + 10,
                limit_per_host=self.config.concurrent_users,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=self.config.headers or {}
            ) as session:
                # Execute load test
                results = await self._execute_load_test(session, payloads)

            self.status = LoadTestStatus.COMPLETED
            return results

        except Exception as e:
            self.status = LoadTestStatus.FAILED
            print(f"❌ Load test failed: {e}")
            raise

        finally:
            self.end_time = time.time()

    def _prepare_payloads(self) -> list[dict[str, Any]]:
        """Prepare request payloads"""
        if self.config.payload_template:
            # Generate variations of the template
            payloads = []
            for i in range(self.config.concurrent_users):
                payload = self.config.payload_template.copy()
                # Add variation (e.g., different user IDs, queries)
                if "text" in payload:
                    payload["text"] = f"{payload['text']} (user_{i})"
                payloads.append(payload)
            return payloads
        else:
            # Default payloads for LightRAG embedding requests
            return [
                {"text": f"Test query {i}: React performance optimization techniques"}
                for i in range(self.config.concurrent_users)
            ]

    async def _execute_load_test(
        self, session: aiohttp.ClientSession, payloads: list[dict[str, Any]]
    ) -> LoadTestResult:
        """Execute the actual load test"""
        endpoints = self.config.endpoints or ["http://localhost:8000/embeddings"]

        # Prepare concurrent tasks
        tasks = []
        request_results = []

        # Calculate timing for rate limiting
        request_interval = 1.0 / self.config.requests_per_second
        total_requests = self.config.requests_per_second * self.config.duration_seconds

        print(f"   Target total requests: {total_requests}")

        # Create semaphore for concurrent users limit
        semaphore = asyncio.Semaphore(self.config.concurrent_users)

        async def make_request(
            request_id: int, payload: dict[str, Any]
        ) -> dict[str, Any]:
            async with semaphore:
                # Rate limiting
                await asyncio.sleep(request_id * request_interval)

                endpoint = endpoints[request_id % len(endpoints)]
                start_time = time.time()

                for attempt in range(self.config.retry_attempts):
                    try:
                        async with session.post(endpoint, json=payload) as response:
                            response_time = (time.time() - start_time) * 1000
                            response_data = await response.json()

                            return {
                                "request_id": request_id,
                                "success": response.status == 200,
                                "status_code": response.status,
                                "response_time_ms": response_time,
                                "timestamp": start_time,
                                "endpoint": endpoint,
                                "response_data": response_data,
                                "error": None,
                            }

                    except Exception as e:
                        if attempt == self.config.retry_attempts - 1:
                            response_time = (time.time() - start_time) * 1000
                            return {
                                "request_id": request_id,
                                "success": False,
                                "status_code": 0,
                                "response_time_ms": response_time,
                                "timestamp": start_time,
                                "endpoint": endpoint,
                                "response_data": None,
                                "error": str(e),
                            }
                        else:
                            await asyncio.sleep(
                                0.1 * (attempt + 1)
                            )  # Exponential backoff

        # Start requests gradually (ramp-up)
        ramp_up_interval = self.config.ramp_up_time / self.config.concurrent_users
        for i in range(total_requests):
            payload = payloads[i % len(payloads)]
            task = asyncio.create_task(make_request(i, payload))
            tasks.append(task)

            # Stagger starts for ramp-up
            if i < self.config.concurrent_users:
                await asyncio.sleep(ramp_up_interval)

        # Wait for all requests to complete
        print("   Executing requests...")
        request_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = [
            r
            for r in request_results
            if isinstance(r, dict) and r.get("success", False)
        ]
        failed_results = [
            r
            for r in request_results
            if isinstance(r, dict) and not r.get("success", False)
        ]
        [r for r in request_results if isinstance(r, Exception)]

        response_times = [r["response_time_ms"] for r in successful_results]
        timestamps = [r["timestamp"] for r in request_results if isinstance(r, dict)]

        # Calculate metrics
        total_requests = len(request_results)
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        actual_duration = time.time() - self.start_time

        result = LoadTestResult(
            status=self.status,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=statistics.mean(response_times)
            if response_times
            else 0,
            p95_response_time_ms=np.percentile(response_times, 95)
            if response_times
            else 0,
            p99_response_time_ms=np.percentile(response_times, 99)
            if response_times
            else 0,
            requests_per_second=successful_requests / actual_duration
            if actual_duration > 0
            else 0,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            duration_seconds=actual_duration,
            errors=[
                {"error": r["error"], "request_id": r["request_id"]}
                for r in failed_results
                if r.get("error")
            ],
            timestamps=timestamps,
            response_times=response_times,
        )

        # Print summary
        print("📊 Load Test Results:")
        print(f"   Total requests: {total_requests}")
        print(
            f"   Successful: {successful_requests} ({successful_requests / total_requests * 100:.1f}%)"
        )
        print(
            f"   Failed: {failed_requests} ({failed_requests / total_requests * 100:.1f}%)"
        )
        print(f"   RPS achieved: {result.requests_per_second:.1f}")
        print(f"   Avg response time: {result.avg_response_time_ms:.0f}ms")
        print(f"   P95 response time: {result.p95_response_time_ms:.0f}ms")
        print(f"   P99 response time: {result.p99_response_time_ms:.0f}ms")

        return result


class CanaryDeployer:
    """Canary deployment with gradual traffic management and automated safety checks"""

    def __init__(self, config: CanaryConfig, endpoints: dict[str, str]):
        self.config = config
        self.endpoints = endpoints  # {"control": "url", "treatment": "url"}
        self.current_stage = CanaryStage.PREPARATION
        self.current_traffic_percentage = 0.0
        self.metrics_history: list[CanaryMetrics] = []
        self.start_time = None

    async def execute_canary_deployment(
        self, test_duration_seconds: int = 3600
    ) -> dict[str, Any]:
        """Execute complete canary deployment process"""
        self.start_time = datetime.now()
        print("🚀 Starting Canary Deployment")

        try:
            # Stage 1: Preparation
            await self._stage_preparation()

            # Stage 2: Initial traffic (5%)
            await self._stage_initial_traffic()

            # Stage 3: Gradual increase
            await self._stage_gradual_increase(test_duration_seconds)

            # Stage 4: Final monitoring and decision
            await self._stage_final_monitoring()

            return {
                "status": "success",
                "final_stage": self.current_stage,
                "final_traffic_percentage": self.current_traffic_percentage,
                "metrics": self._get_deployment_summary(),
            }

        except Exception as e:
            print(f"❌ Canary deployment failed: {e}")
            if self.config.rollback_on_failure:
                await self._rollback()
            return {
                "status": "failed",
                "error": str(e),
                "final_stage": self.current_stage,
            }

    async def _stage_preparation(self):
        """Preparation stage: verify endpoints are healthy"""
        self.current_stage = CanaryStage.PREPARATION
        print("📋 Stage 1: Preparation")

        # Health check both endpoints
        for name, endpoint in self.endpoints.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{endpoint}/health", timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            print(f"   ✅ {name} endpoint healthy")
                        else:
                            raise Exception(
                                f"{name} endpoint unhealthy: HTTP {response.status}"
                            )
            except Exception as e:
                print(f"   ❌ {name} endpoint check failed: {e}")
                raise

        print("   ✅ All endpoints healthy")

    async def _stage_initial_traffic(self):
        """Initial traffic stage: direct small percentage to treatment"""
        self.current_stage = CanaryStage.INITIAL_TRAFFIC
        self.current_traffic_percentage = self.config.initial_traffic_percentage

        print(f"🎯 Stage 2: Initial Traffic ({self.current_traffic_percentage:.1f}%)")

        # Monitor for specified duration
        await self._monitor_stage(self.config.monitoring_duration_minutes * 60)

        # Check if metrics are acceptable
        if not self._check_safety_thresholds():
            raise Exception("Safety thresholds not met during initial traffic")

        print("   ✅ Initial traffic stage completed successfully")

    async def _stage_gradual_increase(self, total_duration: int):
        """Gradual increase stage: slowly increase traffic to treatment"""
        self.current_stage = CanaryStage.GRADUAL_INCREASE
        print("📈 Stage 3: Gradual Traffic Increase")

        target_percentage = min(self.config.max_traffic_percentage, 100.0)
        increments_needed = int(
            (target_percentage - self.current_traffic_percentage)
            / self.config.traffic_increment
        )

        stage_duration = total_duration - (
            self.config.monitoring_duration_minutes * 60 * 2
        )  # Reserve time for monitoring

        if increments_needed > 0:
            increment_duration = stage_duration / increments_needed

            for _i in range(increments_needed):
                self.current_traffic_percentage = min(
                    self.current_traffic_percentage + self.config.traffic_increment,
                    target_percentage,
                )

                print(
                    f"   Increasing traffic to {self.current_traffic_percentage:.1f}%"
                )

                # Monitor this level
                await self._monitor_stage(increment_duration)

                # Check safety thresholds
                if not self._check_safety_thresholds():
                    print(
                        f"   ⚠️ Safety thresholds not met at {self.current_traffic_percentage:.1f}% traffic"
                    )
                    if self.config.rollback_on_failure:
                        await self._rollback()
                        return
                    else:
                        break

        print(
            f"   ✅ Gradual increase completed at {self.current_traffic_percentage:.1f}% traffic"
        )

    async def _stage_final_monitoring(self):
        """Final monitoring stage: decide on promotion"""
        self.current_stage = CanaryStage.MONITORING
        print("🔍 Stage 4: Final Monitoring")

        # Extended monitoring period
        await self._monitor_stage(self.config.monitoring_duration_minutes * 60)

        # Make final decision
        if self._check_safety_thresholds() and self.config.auto_promote:
            print("   ✅ Metrics look good - promoting to 100% traffic")
            self.current_traffic_percentage = 100.0
            self.current_stage = CanaryStage.COMPLETED
        elif self._check_safety_thresholds():
            print("   ⚠️ Metrics acceptable but auto-promote disabled")
            self.current_stage = CanaryStage.STABILIZATION
        else:
            print("   ❌ Metrics below thresholds - rolling back")
            await self._rollback()

    async def _monitor_stage(self, duration_seconds: int):
        """Monitor current traffic level for specified duration"""
        print(f"   Monitoring for {duration_seconds / 60:.1f} minutes...")

        start_time = time.time()
        stage_requests = 0
        stage_errors = 0
        stage_response_times = []

        # Simulate traffic at current percentage
        while time.time() - start_time < duration_seconds:
            # Determine if this request goes to treatment
            import random

            is_treatment = random.uniform(0, 100) < self.current_traffic_percentage

            endpoint = (
                self.endpoints["treatment"]
                if is_treatment
                else self.endpoints["control"]
            )

            try:
                request_start = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint,
                        json={"text": "Canary deployment test query"},
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as response:
                        response_time = (time.time() - request_start) * 1000
                        stage_response_times.append(response_time)
                        stage_requests += 1

                        if response.status != 200:
                            stage_errors += 1

            except Exception:
                stage_errors += 1
                stage_requests += 1

            # Wait between requests
            await asyncio.sleep(0.1)

        # Record metrics
        error_rate = stage_errors / stage_requests if stage_requests > 0 else 0
        avg_response_time = (
            statistics.mean(stage_response_times) if stage_response_times else 0
        )

        metrics = CanaryMetrics(
            timestamp=datetime.now(),
            traffic_percentage=self.current_traffic_percentage,
            total_requests=stage_requests,
            successful_requests=stage_requests - stage_errors,
            avg_response_time_ms=avg_response_time,
            error_rate=error_rate,
            stage=self.current_stage,
        )

        self.metrics_history.append(metrics)

        print(
            f"   📊 Stage metrics: {stage_requests} requests, {error_rate:.1%} error rate, {avg_response_time:.0f}ms avg response"
        )

    def _check_safety_thresholds(self) -> bool:
        """Check if current metrics meet safety thresholds"""
        if not self.metrics_history:
            return False

        recent_metrics = self.metrics_history[-5:]  # Check last 5 data points
        avg_error_rate = statistics.mean([m.error_rate for m in recent_metrics])
        avg_response_time = statistics.mean(
            [m.avg_response_time_ms for m in recent_metrics]
        )

        error_rate_ok = avg_error_rate <= self.config.max_error_rate
        response_time_ok = avg_response_time <= self.config.max_response_time_ms

        print(
            f"   Safety check: Error rate {avg_error_rate:.1%} (threshold: {self.config.max_error_rate:.1%}) {'✅' if error_rate_ok else '❌'}"
        )
        print(
            f"   Safety check: Response time {avg_response_time:.0f}ms (threshold: {self.config.max_response_time_ms:.0f}ms) {'✅' if response_time_ok else '❌'}"
        )

        return error_rate_ok and response_time_ok

    async def _rollback(self):
        """Rollback to control"""
        self.current_stage = CanaryStage.ROLLED_BACK
        self.current_traffic_percentage = 0.0
        print("🔄 Rolling back to control endpoint")

    def _get_deployment_summary(self) -> dict[str, Any]:
        """Get deployment summary"""
        if not self.metrics_history:
            return {}

        return {
            "total_duration_minutes": (datetime.now() - self.start_time).total_seconds()
            / 60,
            "final_traffic_percentage": self.current_traffic_percentage,
            "total_requests": sum(m.total_requests for m in self.metrics_history),
            "total_errors": sum(
                m.total_requests - m.successful_requests for m in self.metrics_history
            ),
            "overall_error_rate": sum(m.error_rate for m in self.metrics_history)
            / len(self.metrics_history),
            "avg_response_time_ms": statistics.mean(
                [m.avg_response_time_ms for m in self.metrics_history]
            ),
            "metrics_history": [asdict(m) for m in self.metrics_history],
        }


class DeploymentOrchestrator:
    """Orchestrates load testing and canary deployment together"""

    def __init__(self):
        self.load_test_runner = None
        self.canary_deployer = None

    async def run_full_deployment_test(
        self,
        load_test_config: LoadTestConfig,
        canary_config: CanaryConfig,
        endpoints: dict[str, str],
    ) -> dict[str, Any]:
        """Run complete deployment pipeline: load test + canary deployment"""

        print("🚀 Starting Full Deployment Pipeline")
        print("=" * 50)

        results = {
            "load_test": None,
            "canary_deployment": None,
            "overall_status": "running",
        }

        try:
            # Phase 1: Load Testing
            print("\n📊 Phase 1: Load Testing")
            self.load_test_runner = LoadTestRunner(load_test_config)
            load_test_result = await self.load_test_runner.run_load_test(
                "pre_deployment_test"
            )
            results["load_test"] = asdict(load_test_result)

            # Check if load test passed basic thresholds
            if load_test_result.error_rate > 0.1:  # 10% error rate threshold
                raise Exception(
                    f"Load test failed with {load_test_result.error_rate:.1%} error rate"
                )

            print("✅ Load test passed - proceeding to canary deployment")

            # Phase 2: Canary Deployment
            print("\n🎯 Phase 2: Canary Deployment")
            self.canary_deployer = CanaryDeployer(canary_config, endpoints)
            canary_result = await self.canary_deployer.execute_canary_deployment()
            results["canary_deployment"] = canary_result

            if canary_result["status"] == "success":
                results["overall_status"] = "success"
                print("✅ Full deployment pipeline completed successfully")
            else:
                results["overall_status"] = "failed"
                print("❌ Deployment pipeline failed during canary stage")

        except Exception as e:
            results["overall_status"] = "failed"
            results["error"] = str(e)
            print(f"❌ Deployment pipeline failed: {e}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"deployment_pipeline_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Results saved to: {results_file}")

        return results


# Convenience functions
def create_lightrag_load_test_config(
    openviking_url: str = "http://localhost:8000",
    concurrent_users: int = 50,
    duration_seconds: int = 180,
) -> LoadTestConfig:
    """Create load test config for LightRAG"""

    return LoadTestConfig(
        concurrent_users=concurrent_users,
        requests_per_second=min(concurrent_users * 2, 100),
        duration_seconds=duration_seconds,
        endpoints=[f"{openviking_url}/embeddings"],
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )


def create_lightrag_canary_config() -> CanaryConfig:
    """Create canary config for LightRAG deployment"""

    return CanaryConfig(
        initial_traffic_percentage=5.0,
        max_traffic_percentage=100.0,
        traffic_increment=10.0,
        monitoring_duration_minutes=5,
        stability_threshold=0.95,
        rollback_on_failure=True,
        auto_promote=True,
        max_error_rate=0.05,
        max_response_time_ms=3000.0,
    )


if __name__ == "__main__":
    import asyncio

    async def demo_deployment_pipeline():
        """Demonstrate load testing and canary deployment"""

        orchestrator = DeploymentOrchestrator()

        # Create configurations
        load_test_config = create_lightrag_load_test_config(
            concurrent_users=20, duration_seconds=60
        )
        canary_config = create_lightrag_canary_config()

        # Define endpoints
        endpoints = {
            "control": "http://localhost:9621/embeddings",  # SMP
            "treatment": "http://localhost:8000/embeddings",  # OpenViking
        }

        # Run full pipeline
        results = await orchestrator.run_full_deployment_test(
            load_test_config, canary_config, endpoints
        )

        print(f"\n🎉 Pipeline completed with status: {results['overall_status']}")

        return results

    asyncio.run(demo_deployment_pipeline())
