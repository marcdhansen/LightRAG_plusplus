#!/usr/bin/env python3
"""
Production A/B Testing - Real OpenViking Test
Tests the actual deployed OpenViking server against simulated SMP baseline
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any

import httpx
from rich.console import Console


class ProductionABTest:
    def __init__(self):
        self.console = Console()
        self.openviking_url = "http://localhost:8002"

    async def test_openviking_endpoints(self) -> dict[str, Any]:
        """Test all OpenViking endpoints"""
        results = {
            "health_check": False,
            "embeddings": [],
            "skills_search": [],
            "conversation": [],
            "avg_response_times": {},
            "success_rates": {},
        }

        async with httpx.AsyncClient() as client:
            # Test health endpoint
            try:
                response = await client.get(
                    f"{self.openviking_url}/health", timeout=5.0
                )
                if response.status_code == 200:
                    results["health_check"] = True
                    self.console.print("✅ Health check passed")
                else:
                    self.console.print(
                        f"❌ Health check failed: {response.status_code}"
                    )
            except Exception as e:
                self.console.print(f"❌ Health check error: {e}")
                return results

            # Test embedding generation
            test_texts = [
                "React performance optimization techniques",
                "Database schema design patterns",
                "API authentication best practices",
            ]

            embedding_times = []
            for text in test_texts:
                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{self.openviking_url}/embeddings",
                        json={"text": text},
                        timeout=10.0,
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        embedding_times.append(response_time)
                        cache_hit = data.get("cache_hit", False)
                        results["embeddings"].append(
                            {
                                "text": text[:30] + "...",
                                "response_time_ms": response_time,
                                "cache_hit": cache_hit,
                                "embedding_dim": data.get("dimension", 0),
                                "success": True,
                            }
                        )
                        self.console.print(
                            f"✅ Embedding: {response_time:.0f}ms (cache: {cache_hit})"
                        )
                    else:
                        results["embeddings"].append(
                            {
                                "text": text[:30] + "...",
                                "response_time_ms": response_time,
                                "success": False,
                                "error": f"HTTP {response.status_code}",
                            }
                        )
                        self.console.print(
                            f"❌ Embedding failed: {response.status_code}"
                        )

                except Exception as e:
                    results["embeddings"].append(
                        {"text": text[:30] + "...", "success": False, "error": str(e)}
                    )
                    self.console.print(f"❌ Embedding error: {e}")

            # Test skill search
            skill_queries = [
                "React optimization",
                "security patterns",
                "database design",
            ]

            skill_times = []
            for query in skill_queries:
                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{self.openviking_url}/skills/search",
                        json={"query": query, "max_results": 5},
                        timeout=10.0,
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        skill_times.append(response_time)
                        results["skills_search"].append(
                            {
                                "query": query,
                                "response_time_ms": response_time,
                                "skills_found": data.get("found_count", 0),
                                "success": True,
                            }
                        )
                        self.console.print(
                            f"✅ Skills: {response_time:.0f}ms (found: {data.get('found_count', 0)})"
                        )
                    else:
                        results["skills_search"].append(
                            {
                                "query": query,
                                "response_time_ms": response_time,
                                "success": False,
                                "error": f"HTTP {response.status_code}",
                            }
                        )
                        self.console.print(f"❌ Skills failed: {response.status_code}")

                except Exception as e:
                    results["skills_search"].append(
                        {"query": query, "success": False, "error": str(e)}
                    )
                    self.console.print(f"❌ Skills error: {e}")

            # Test conversation memory
            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.openviking_url}/conversation",
                    json={
                        "session_id": "test-session-1",
                        "message": "Hello, can you help with React optimization?",
                        "role": "user",
                    },
                    timeout=10.0,
                )
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    results["conversation"].append(
                        {
                            "message": "test message",
                            "response_time_ms": response_time,
                            "session_id": data.get("session_id"),
                            "success": True,
                        }
                    )
                    self.console.print(f"✅ Conversation: {response_time:.0f}ms")
                else:
                    results["conversation"].append(
                        {
                            "message": "test message",
                            "response_time_ms": response_time,
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    self.console.print(
                        f"❌ Conversation failed: {response.status_code}"
                    )

            except Exception as e:
                results["conversation"].append(
                    {"message": "test message", "success": False, "error": str(e)}
                )
                self.console.print(f"❌ Conversation error: {e}")

        # Calculate averages and success rates
        if embedding_times:
            results["avg_response_times"]["embeddings"] = statistics.mean(
                embedding_times
            )
            results["success_rates"]["embeddings"] = (
                len([r for r in results["embeddings"] if r["success"]])
                / len(results["embeddings"])
                * 100
            )

        if skill_times:
            results["avg_response_times"]["skills"] = statistics.mean(skill_times)
            results["success_rates"]["skills"] = (
                len([r for r in results["skills_search"] if r["success"]])
                / len(results["skills_search"])
                * 100
            )

        if results["conversation"]:
            results["avg_response_times"]["conversation"] = results["conversation"][0][
                "response_time_ms"
            ]
            results["success_rates"]["conversation"] = (
                100 if results["conversation"][0]["success"] else 0
            )

        return results

    def simulate_smp_baseline(self) -> dict[str, Any]:
        """Simulate SMP baseline performance"""
        return {
            "health_check": True,
            "avg_response_times": {
                "embeddings": 2500,  # SMP typically slower
                "skills": 2800,
                "conversation": 3200,
            },
            "success_rates": {"embeddings": 85, "skills": 75, "conversation": 90},
        }

    def generate_comparison_report(
        self, openviking_results: dict, smp_results: dict
    ) -> dict[str, Any]:
        """Generate detailed comparison report"""
        self.console.print("\n📊 [bold blue]Performance Comparison Report[/bold blue]")

        comparison = {
            "timestamp": datetime.now().isoformat(),
            "openviking": openviking_results,
            "smp_baseline": smp_results,
            "improvements": {},
            "recommendations": [],
        }

        # Compare embeddings
        if "embeddings" in openviking_results["avg_response_times"]:
            ov_time = openviking_results["avg_response_times"]["embeddings"]
            smp_time = smp_results["avg_response_times"]["embeddings"]
            improvement = ((smp_time - ov_time) / smp_time) * 100
            comparison["improvements"]["embedding_speed"] = improvement

            self.console.print("\n🔹 [bold]Embedding Performance:[/bold]")
            self.console.print(f"   OpenViking: {ov_time:.0f}ms")
            self.console.print(f"   SMP Baseline: {smp_time:.0f}ms")
            self.console.print(f"   Improvement: {improvement:+.1f}%")

        # Compare skills
        if "skills" in openviking_results["avg_response_times"]:
            ov_time = openviking_results["avg_response_times"]["skills"]
            smp_time = smp_results["avg_response_times"]["skills"]
            improvement = ((smp_time - ov_time) / smp_time) * 100
            comparison["improvements"]["skills_speed"] = improvement

            self.console.print("\n🔹 [bold]Skill Search Performance:[/bold]")
            self.console.print(f"   OpenViking: {ov_time:.0f}ms")
            self.console.print(f"   SMP Baseline: {smp_time:.0f}ms")
            self.console.print(f"   Improvement: {improvement:+.1f}%")

        # Overall recommendation
        if openviking_results["health_check"]:
            avg_improvement = (
                statistics.mean(list(comparison["improvements"].values()))
                if comparison["improvements"]
                else 0
            )

            if avg_improvement > 50:
                recommendation = "DEPLOY_IMMEDIATELY"
                reason = "OpenViking shows >50% performance improvement"
            elif avg_improvement > 20:
                recommendation = "DEPLOY_WITH_MONITORING"
                reason = "OpenViking shows significant performance improvement"
            else:
                recommendation = "CONTINUE_TESTING"
                reason = "Performance improvement is modest"

            comparison["recommendations"] = [
                {
                    "action": recommendation,
                    "reason": reason,
                    "confidence": "high" if avg_improvement > 30 else "medium",
                }
            ]

            self.console.print(
                f"\n🏆 [bold green]Recommendation: {recommendation}[/bold green]"
            )
            self.console.print(f"   Reason: {reason}")

        return comparison


async def main():
    """Main production test runner"""
    console = Console()
    console.print("🚀 [bold blue]Production A/B Testing - OpenViking[/bold blue]")
    console.print("=" * 60)

    tester = ProductionABTest()

    try:
        # Test OpenViking
        console.print("\n🟢 Testing OpenViking Production Server...")
        openviking_results = await tester.test_openviking_endpoints()

        # Simulate SMP baseline
        console.print("\n🟡 Using SMP Baseline (Simulated)...")
        smp_results = tester.simulate_smp_baseline()

        # Generate comparison
        console.print("\n📈 Generating Comparison Report...")
        comparison = tester.generate_comparison_report(openviking_results, smp_results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"production_ab_test_results_{timestamp}.json", "w") as f:
            json.dump(comparison, f, indent=2)

        console.print(
            f"\n✅ Results saved to: production_ab_test_results_{timestamp}.json"
        )

        # Summary
        console.print("\n🎯 [bold]Test Summary:[/bold]")
        console.print(
            f"   Health Check: {'✅' if openviking_results['health_check'] else '❌'}"
        )

        if comparison["improvements"]:
            avg_improvement = statistics.mean(list(comparison["improvements"].values()))
            console.print(
                f"   Average Performance Improvement: {avg_improvement:+.1f}%"
            )

        if comparison["recommendations"]:
            console.print(
                f"   Recommendation: {comparison['recommendations'][0]['action']}"
            )

        return 0 if openviking_results["health_check"] else 1

    except Exception as e:
        console.print(f"\n❌ [bold red]Testing failed:[/bold red] {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
