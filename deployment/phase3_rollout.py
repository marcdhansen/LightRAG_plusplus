#!/usr/bin/env python3
"""
OpenViking Phase 3 Rollout Automation
Automated gradual traffic routing from SMP to OpenViking
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import httpx
from rich.console import Console
from rich.table import Table


class Phase3Rollout:
    def __init__(self, router_url: str = "http://localhost:8003"):
        self.console = Console()
        self.router_url = router_url
        self.smp_url = "http://localhost:9621"
        self.openviking_url = "http://localhost:8002"
        self.rollout_phases = [
            {"name": "10%", "openviking_percentage": 10, "duration_minutes": 10},
            {"name": "25%", "openviking_percentage": 25, "duration_minutes": 15},
            {"name": "50%", "openviking_percentage": 50, "duration_minutes": 20},
            {"name": "75%", "openviking_percentage": 75, "duration_minutes": 20},
            {"name": "100%", "openviking_percentage": 100, "duration_minutes": 30},
        ]
        self.metrics_history = []

    async def check_system_health(self, _system_name: str, url: str) -> dict[str, Any]:
        """Check health of a specific system"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "healthy": True,
                        "status": data.get("status", "unknown"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "version": data.get("version", "unknown"),
                        "features": data.get("features", []),
                    }
                else:
                    return {
                        "healthy": False,
                        "error": f"HTTP {response.status_code}",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                    }
        except Exception as e:
            return {"healthy": False, "error": str(e), "response_time_ms": 0}

    async def get_router_status(self) -> dict[str, Any]:
        """Get current router status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.router_url}/traffic/status", timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            self.console.print(f"❌ Error getting router status: {e}")
        return {}

    async def set_traffic_split(self, openviking_percentage: int, reason: str) -> bool:
        """Set traffic split percentage"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.router_url}/traffic/split",
                    json={
                        "openviking_percentage": openviking_percentage,
                        "reason": reason,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return True
                else:
                    self.console.print(
                        f"❌ Failed to set traffic split: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.console.print(f"❌ Error setting traffic split: {e}")
            return False

    async def generate_test_traffic(
        self, duration_minutes: int, requests_per_minute: int = 10
    ):
        """Generate test traffic to both systems"""
        self.console.print(
            f"🔄 Generating test traffic: {requests_per_minute} requests/minute for {duration_minutes} minutes"
        )

        test_end = datetime.now() + timedelta(minutes=duration_minutes)
        request_count = 0
        success_count = 0

        async with httpx.AsyncClient() as client:
            while datetime.now() < test_end:
                try:
                    # Test conversation endpoint
                    response = await client.post(
                        f"{self.router_url}/proxy",
                        json={
                            "endpoint": "/conversation",
                            "method": "POST",
                            "body": {
                                "session_id": f"test-session-{request_count}",
                                "message": f"Test message {request_count}",
                                "role": "user",
                            },
                        },
                        timeout=30.0,
                    )

                    request_count += 1
                    if 200 <= response.status_code < 400:
                        success_count += 1

                    # Test embedding endpoint
                    await asyncio.sleep(1)

                    response = await client.post(
                        f"{self.router_url}/proxy",
                        json={
                            "endpoint": "/embeddings",
                            "method": "POST",
                            "body": {"text": f"Test embedding text {request_count}"},
                        },
                        timeout=30.0,
                    )

                    request_count += 1
                    if 200 <= response.status_code < 400:
                        success_count += 1

                except Exception as e:
                    self.console.print(f"⚠️ Traffic generation error: {e}")

                # Wait to maintain rate
                await asyncio.sleep(60 / requests_per_minute)

        return {
            "total_requests": request_count,
            "successful_requests": success_count,
            "success_rate": (success_count / request_count * 100)
            if request_count > 0
            else 0,
        }

    async def monitor_performance(self, duration_minutes: int) -> dict[str, Any]:
        """Monitor performance during a phase"""
        self.console.print(
            f"📊 Monitoring performance for {duration_minutes} minutes..."
        )

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        metrics_samples = []

        while datetime.now() < end_time:
            try:
                # Get router metrics
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.router_url}/metrics", timeout=10.0
                    )
                    if response.status_code == 200:
                        metrics = response.json()
                        metrics_samples.append(
                            {
                                "timestamp": datetime.now(),
                                "traffic_split": metrics.get("traffic_split", {}),
                                "performance": metrics.get("performance", {}),
                                "systems_health": metrics.get("systems_health", {}),
                            }
                        )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.console.print(f"⚠️ Monitoring error: {e}")
                await asyncio.sleep(30)

        # Calculate averages
        if metrics_samples:
            avg_response_times = {}
            success_rates = {}

            for system in ["smp", "openviking"]:
                response_times = []
                successes = []

                for sample in metrics_samples:
                    perf = sample.get("performance", {}).get(system, {})
                    if perf:
                        response_times.append(perf.get("avg_response_time_ms", 0))
                        successes.append(perf.get("success_rate", 0))

                if response_times:
                    avg_response_times[system] = sum(response_times) / len(
                        response_times
                    )
                if successes:
                    success_rates[system] = sum(successes) / len(successes)

            return {
                "duration_minutes": duration_minutes,
                "samples_count": len(metrics_samples),
                "avg_response_times": avg_response_times,
                "success_rates": success_rates,
                "samples": metrics_samples[-10:],  # Keep last 10 samples
            }

        return {"error": "No metrics collected"}

    async def run_phase(self, phase: dict[str, Any]) -> dict[str, Any]:
        """Run a single rollout phase"""
        phase_name = phase["name"]
        openviking_percentage = phase["openviking_percentage"]
        duration_minutes = phase["duration_minutes"]

        self.console.print(f"\n🚀 Starting Phase: {phase_name} OpenViking Traffic")
        self.console.print(f"   Duration: {duration_minutes} minutes")

        # Set traffic split
        success = await self.set_traffic_split(
            openviking_percentage, f"Phase {phase_name} rollout"
        )

        if not success:
            return {
                "phase": phase_name,
                "status": "failed",
                "error": "Failed to set traffic split",
            }

        # Verify the change
        await asyncio.sleep(5)
        status = await self.get_router_status()
        actual_split = status.get("traffic_split", {}).get("openviking", 0)

        if actual_split != openviking_percentage:
            return {
                "phase": phase_name,
                "status": "failed",
                "error": f"Traffic split not applied. Expected: {openviking_percentage}%, Actual: {actual_split}%",
            }

        self.console.print(
            f"✅ Traffic split set: SMP={100 - openviking_percentage}%, OpenViking={openviking_percentage}%"
        )

        # Monitor performance
        performance = await self.monitor_performance(duration_minutes)

        # Generate some test traffic
        traffic_results = await self.generate_test_traffic(min(5, duration_minutes))

        return {
            "phase": phase_name,
            "status": "completed",
            "traffic_split": {
                "smp": 100 - openviking_percentage,
                "openviking": openviking_percentage,
            },
            "performance": performance,
            "traffic_test": traffic_results,
            "duration_minutes": duration_minutes,
        }

    def display_rollout_summary(self, results: list[dict[str, Any]]):
        """Display rollout summary"""
        self.console.print("\n📋 [bold blue]Phase 3 Rollout Summary[/bold blue]")
        self.console.print("=" * 50)

        # Create summary table
        table = Table(title="Rollout Phase Results")
        table.add_column("Phase", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Traffic Split", style="yellow")
        table.add_column("Duration", style="blue")
        table.add_column("Performance", style="magenta")

        for result in results:
            phase = result.get("phase", "Unknown")
            status = result.get("status", "Unknown")
            status_emoji = "✅" if status == "completed" else "❌"

            split = result.get("traffic_split", {})
            split_text = f"SMP:{split.get('smp', 0)}% OV:{split.get('openviking', 0)}%"

            duration = f"{result.get('duration_minutes', 0)}min"

            perf = result.get("performance", {})
            if "error" not in perf:
                avg_times = perf.get("avg_response_times", {})
                ov_time = avg_times.get("openviking", 0)
                smp_time = avg_times.get("smp", 0)
                perf_text = f"OV:{ov_time:.0f}ms SMP:{smp_time:.0f}ms"
            else:
                perf_text = "No data"

            table.add_row(
                phase, f"{status_emoji} {status}", split_text, duration, perf_text
            )

        self.console.print(table)

        # Overall status
        completed_phases = len([r for r in results if r.get("status") == "completed"])
        total_phases = len(results)

        self.console.print(
            f"\n🎯 Overall Progress: {completed_phases}/{total_phases} phases completed"
        )

        if completed_phases == total_phases:
            self.console.print(
                "🎉 [bold green]ROLLOUT SUCCESSFUL - OpenViking now at 100% traffic![/bold green]"
            )

            # Show final performance comparison
            final_result = results[-1] if results else {}
            final_perf = final_result.get("performance", {})
            if "error" not in final_perf and "avg_response_times" in final_perf:
                times = final_perf["avg_response_times"]
                if "openviking" in times and "smp" in times:
                    improvement = (
                        (times.get("smp", 0) - times.get("openviking", 0))
                        / times.get("smp", 1)
                    ) * 100
                    self.console.print(
                        f"\n📈 Final Performance: {improvement:+.1f}% improvement with OpenViking"
                    )

    async def pre_rollout_checks(self) -> bool:
        """Perform pre-rollout health checks"""
        self.console.print("🔍 [bold yellow]Pre-Rollout Health Checks[/bold yellow]")

        # Check router
        router_health = await self.check_system_health(
            "Traffic Router", self.router_url
        )
        if not router_health["healthy"]:
            self.console.print(
                f"❌ Traffic Router unhealthy: {router_health.get('error')}"
            )
            return False
        self.console.print(f"✅ Traffic Router: {router_health['status']}")

        # Check OpenViking
        openviking_health = await self.check_system_health(
            "OpenViking", self.openviking_url
        )
        if not openviking_health["healthy"]:
            self.console.print(
                f"❌ OpenViking unhealthy: {openviking_health.get('error')}"
            )
            return False
        self.console.print(
            f"✅ OpenViking: {openviking_health['status']} v{openviking_health['version']}"
        )

        # Check SMP
        smp_health = await self.check_system_health("SMP", self.smp_url)
        if not smp_health["healthy"]:
            self.console.print(
                f"⚠️ SMP unhealthy (fallback mode): {smp_health.get('error')}"
            )
        else:
            self.console.print(
                f"✅ SMP: {smp_health['status']} v{smp_health['version']}"
            )

        return True

    async def run_rollout(self, phases_to_run: list[str] = None):
        """Run the complete rollout process"""
        self.console.print(
            "🚀 [bold blue]OpenViking Phase 3 Rollout Automation[/bold blue]"
        )
        self.console.print("=" * 60)

        # Pre-rollout checks
        if not await self.pre_rollout_checks():
            self.console.print("❌ Pre-rollout checks failed. Aborting rollout.")
            return False

        # Filter phases if specified
        phases = self.rollout_phases
        if phases_to_run:
            [phase["name"] for phase in self.rollout_phases]
            phases = [
                phase for phase in self.rollout_phases if phase["name"] in phases_to_run
            ]

        if not phases:
            self.console.print("❌ No valid phases specified")
            return False

        self.console.print(f"\n📋 Rollout Plan: {len(phases)} phases")
        for phase in phases:
            self.console.print(
                f"   • {phase['name']} - {phase['duration_minutes']} minutes"
            )

        # Run each phase
        results = []

        for phase in phases:
            try:
                result = await self.run_phase(phase)
                results.append(result)

                if result["status"] != "completed":
                    self.console.print(
                        f"❌ Phase {phase['name']} failed. Stopping rollout."
                    )
                    break

                # Brief pause between phases
                if phase != phases[-1]:
                    self.console.print("⏸️ Brief pause before next phase...")
                    await asyncio.sleep(10)

            except Exception as e:
                self.console.print(f"❌ Error in phase {phase['name']}: {e}")
                results.append(
                    {"phase": phase["name"], "status": "failed", "error": str(e)}
                )
                break

        # Display summary
        self.display_rollout_summary(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"phase3_rollout_results_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2)

        self.console.print(
            f"\n💾 Results saved to: phase3_rollout_results_{timestamp}.json"
        )

        # Return success if all phases completed
        return all(r.get("status") == "completed" for r in results)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OpenViking Phase 3 Rollout Automation"
    )
    parser.add_argument(
        "--phases", nargs="+", help="Specific phases to run (e.g., '10%' '25%')"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick rollout with shorter durations"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run without actual traffic changes"
    )

    args = parser.parse_args()

    rollout = Phase3Rollout()

    if args.quick:
        # Use shorter durations for quick testing
        for phase in rollout.rollout_phases:
            phase["duration_minutes"] = min(2, phase["duration_minutes"])

    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual traffic changes will be made")
        rollout.router_url = "http://localhost:9999"  # Invalid URL for dry run

    success = await rollout.run_rollout(args.phases)

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
