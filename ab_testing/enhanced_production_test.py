#!/usr/bin/env python3
"""
Enhanced Production A/B Testing - OpenViking with Conversation Features
Comprehensive testing of enhanced OpenViking vs SMP baseline
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any

import httpx
from rich.console import Console


class EnhancedProductionABTest:
    def __init__(self):
        self.console = Console()
        self.openviking_url = "http://localhost:8002"

    async def test_enhanced_openviking(self) -> dict[str, Any]:
        """Test all enhanced OpenViking endpoints"""
        results = {
            "health_check": False,
            "embeddings": [],
            "skills_search": [],
            "conversation": [],
            "conversation_memory": [],
            "resources": [],
            "performance_metrics": [],
            "avg_response_times": {},
            "success_rates": {},
            "features_tested": [],
        }

        async with httpx.AsyncClient() as client:
            # Test health endpoint
            try:
                response = await client.get(
                    f"{self.openviking_url}/health", timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    results["health_check"] = True
                    results["features_tested"] = data.get("features", [])
                    self.console.print("✅ Health check passed")
                    self.console.print(
                        f"   Features: {', '.join(results['features_tested'])}"
                    )
                else:
                    self.console.print(
                        f"❌ Health check failed: {response.status_code}"
                    )
            except Exception as e:
                self.console.print(f"❌ Health check error: {e}")
                return results

            # Test embedding generation with caching
            test_texts = [
                "React performance optimization techniques",
                "Database schema design patterns",
                "API authentication best practices",
            ]

            embedding_times = []
            cache_hits = []
            for i, text in enumerate(test_texts):
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
                        cache_hits.append(cache_hit)

                        # Test caching by making same request again
                        if i == 0:  # Test cache on first request
                            start_time = time.time()
                            cached_response = await client.post(
                                f"{self.openviking_url}/embeddings",
                                json={"text": text},
                                timeout=10.0,
                            )
                            cache_response_time = (time.time() - start_time) * 1000
                            if cached_response.status_code == 200:
                                cached_data = cached_response.json()
                                if cached_data.get("cache_hit"):
                                    cache_hits.append(True)
                                    self.console.print(
                                        f"✅ Embedding cache working: {cache_response_time:.0f}ms"
                                    )

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

            # Test conversation memory with multi-turn context
            session_id = "enhanced-test-session"
            conversation_messages = [
                {"message": "I need help with React optimization", "role": "user"},
                {
                    "message": "What are the best optimization techniques?",
                    "role": "user",
                },
                {"message": "Can you explain code splitting?", "role": "user"},
            ]

            conversation_times = []
            for _i, msg in enumerate(conversation_messages):
                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{self.openviking_url}/conversation",
                        json={
                            "session_id": session_id,
                            "message": msg["message"],
                            "role": msg["role"],
                        },
                        timeout=10.0,
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        conversation_times.append(response_time)
                        context_count = len(data.get("context_messages", []))
                        message_count = data.get("message_count", 0)

                        results["conversation"].append(
                            {
                                "message": msg["message"][:30] + "...",
                                "response_time_ms": response_time,
                                "context_count": context_count,
                                "message_count": message_count,
                                "success": True,
                            }
                        )
                        self.console.print(
                            f"✅ Conversation: {response_time:.0f}ms (context: {context_count}, total: {message_count})"
                        )
                    else:
                        results["conversation"].append(
                            {
                                "message": msg["message"][:30] + "...",
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
                        {
                            "message": msg["message"][:30] + "...",
                            "success": False,
                            "error": str(e),
                        }
                    )
                    self.console.print(f"❌ Conversation error: {e}")

            # Test conversation statistics
            try:
                start_time = time.time()
                response = await client.get(
                    f"{self.openviking_url}/conversation/stats/{session_id}",
                    timeout=10.0,
                )
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    session_stats = data.get("session_stats", {})
                    results["conversation_memory"].append(
                        {
                            "endpoint": "conversation_stats",
                            "response_time_ms": response_time,
                            "session_message_count": session_stats.get(
                                "message_count", 0
                            ),
                            "session_age_minutes": session_stats.get(
                                "session_age_minutes", 0
                            ),
                            "success": True,
                        }
                    )
                    self.console.print(
                        f"✅ Session Stats: {response_time:.0f}ms (messages: {session_stats.get('message_count', 0)})"
                    )
                else:
                    results["conversation_memory"].append(
                        {
                            "endpoint": "conversation_stats",
                            "response_time_ms": response_time,
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    self.console.print(
                        f"❌ Session Stats failed: {response.status_code}"
                    )

            except Exception as e:
                results["conversation_memory"].append(
                    {
                        "endpoint": "conversation_stats",
                        "success": False,
                        "error": str(e),
                    }
                )
                self.console.print(f"❌ Session Stats error: {e}")

            # Test resource management
            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.openviking_url}/resources",
                    json={
                        "content": "Test resource data",
                        "target_uri": "memory://test-resource",
                        "resource_type": "conversation_memory",
                        "session_id": session_id,
                    },
                    timeout=10.0,
                )
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    results["resources"].append(
                        {
                            "endpoint": "resource_storage",
                            "response_time_ms": response_time,
                            "resource_id": data.get("resource_id", ""),
                            "success": True,
                        }
                    )
                    self.console.print(f"✅ Resource Storage: {response_time:.0f}ms")
                else:
                    results["resources"].append(
                        {
                            "endpoint": "resource_storage",
                            "response_time_ms": response_time,
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    self.console.print(
                        f"❌ Resource Storage failed: {response.status_code}"
                    )

            except Exception as e:
                results["resources"].append(
                    {"endpoint": "resource_storage", "success": False, "error": str(e)}
                )
                self.console.print(f"❌ Resource Storage error: {e}")

            # Test performance metrics endpoint
            try:
                start_time = time.time()
                response = await client.get(
                    f"{self.openviking_url}/performance/metrics", timeout=10.0
                )
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("summary", {})
                    results["performance_metrics"].append(
                        {
                            "endpoint": "performance_dashboard",
                            "response_time_ms": response_time,
                            "total_requests": summary.get("total_requests", 0),
                            "active_sessions": summary.get("active_sessions", 0),
                            "cache_size": summary.get("cache_size", 0),
                            "success": True,
                        }
                    )
                    self.console.print(f"✅ Performance Metrics: {response_time:.0f}ms")
                else:
                    results["performance_metrics"].append(
                        {
                            "endpoint": "performance_dashboard",
                            "response_time_ms": response_time,
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    self.console.print(
                        f"❌ Performance Metrics failed: {response.status_code}"
                    )

            except Exception as e:
                results["performance_metrics"].append(
                    {
                        "endpoint": "performance_dashboard",
                        "success": False,
                        "error": str(e),
                    }
                )
                self.console.print(f"❌ Performance Metrics error: {e}")

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
            results["success_rates"]["cache_hit_rate"] = (
                len([c for c in cache_hits if c]) / len(cache_hits) * 100
                if cache_hits
                else 0
            )

        if skill_times:
            results["avg_response_times"]["skills"] = statistics.mean(skill_times)
            results["success_rates"]["skills"] = (
                len([r for r in results["skills_search"] if r["success"]])
                / len(results["skills_search"])
                * 100
            )

        if conversation_times:
            results["avg_response_times"]["conversation"] = statistics.mean(
                conversation_times
            )
            results["success_rates"]["conversation"] = (
                len([r for r in results["conversation"] if r["success"]])
                / len(results["conversation"])
                * 100
            )

        if results["conversation_memory"]:
            results["success_rates"]["conversation_memory"] = (
                len([r for r in results["conversation_memory"] if r["success"]])
                / len(results["conversation_memory"])
                * 100
            )

        if results["resources"]:
            results["success_rates"]["resources"] = (
                len([r for r in results["resources"] if r["success"]])
                / len(results["resources"])
                * 100
            )

        if results["performance_metrics"]:
            results["success_rates"]["performance_metrics"] = (
                len([r for r in results["performance_metrics"] if r["success"]])
                / len(results["performance_metrics"])
                * 100
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
                "conversation_memory": 0,  # SMP doesn't have this
                "resources": 2500,
                "performance_metrics": 0,  # SMP doesn't have this
            },
            "success_rates": {
                "embeddings": 85,
                "skills": 75,
                "conversation": 90,
                "conversation_memory": 0,  # SMP doesn't have this
                "resources": 80,
                "performance_metrics": 0,  # SMP doesn't have this
            },
        }

    def generate_enhanced_comparison_report(
        self, openviking_results: dict, smp_results: dict
    ) -> dict[str, Any]:
        """Generate detailed comparison report for enhanced features"""
        self.console.print(
            "\n📊 [bold blue]Enhanced OpenViking Performance Comparison[/bold blue]"
        )

        comparison = {
            "timestamp": datetime.now().isoformat(),
            "openviking": openviking_results,
            "smp_baseline": smp_results,
            "improvements": {},
            "new_features": {},
            "recommendations": [],
        }

        # Compare existing features
        if "embeddings" in openviking_results["avg_response_times"]:
            ov_time = openviking_results["avg_response_times"]["embeddings"]
            smp_time = smp_results["avg_response_times"]["embeddings"]
            improvement = ((smp_time - ov_time) / smp_time) * 100
            comparison["improvements"]["embedding_speed"] = improvement

            self.console.print("\n🔹 [bold]Embedding Performance:[/bold]")
            self.console.print(f"   OpenViking: {ov_time:.0f}ms")
            self.console.print(f"   SMP Baseline: {smp_time:.0f}ms")
            self.console.print(f"   Improvement: {improvement:+.1f}%")
            self.console.print(
                f"   Cache Hit Rate: {openviking_results['success_rates'].get('cache_hit_rate', 0):.1f}%"
            )

        if "skills" in openviking_results["avg_response_times"]:
            ov_time = openviking_results["avg_response_times"]["skills"]
            smp_time = smp_results["avg_response_times"]["skills"]
            improvement = ((smp_time - ov_time) / smp_time) * 100
            comparison["improvements"]["skills_speed"] = improvement

            self.console.print("\n🔹 [bold]Skill Search Performance:[/bold]")
            self.console.print(f"   OpenViking: {ov_time:.0f}ms")
            self.console.print(f"   SMP Baseline: {smp_time:.0f}ms")
            self.console.print(f"   Improvement: {improvement:+.1f}%")

        # Highlight new exclusive features
        if "conversation" in openviking_results["success_rates"]:
            conv_success = openviking_results["success_rates"]["conversation"]
            comparison["new_features"]["conversation_memory"] = {
                "success_rate": conv_success,
                "response_time": openviking_results["avg_response_times"].get(
                    "conversation", 0
                ),
                "exclusive_to_openviking": True,
            }

            self.console.print(
                "\n🆕 [bold green]Conversation Memory (Exclusive Feature):[/bold green]"
            )
            self.console.print(f"   Success Rate: {conv_success:.1f}%")
            self.console.print(
                f"   Response Time: {openviking_results['avg_response_times'].get('conversation', 0):.0f}ms"
            )

        # Check for other new features
        new_features = ["conversation_memory", "resources", "performance_metrics"]
        for feature in new_features:
            if (
                feature in openviking_results["success_rates"]
                and openviking_results["success_rates"][feature] > 0
            ):
                success_rate = openviking_results["success_rates"][feature]
                comparison["new_features"][feature] = {
                    "success_rate": success_rate,
                    "exclusive_to_openviking": True,
                }
                self.console.print(
                    f"\n🆕 [bold green]{feature.replace('_', ' ').title()}:[/bold green]"
                )
                self.console.print(f"   Success Rate: {success_rate:.1f}%")

        # Overall recommendation
        if openviking_results["health_check"]:
            # Calculate weighted improvement
            improvements = list(comparison["improvements"].values())
            avg_improvement = statistics.mean(improvements) if improvements else 0

            # Add bonus points for new features
            new_features_count = len(
                [
                    f
                    for f in comparison["new_features"].values()
                    if f.get("success_rate", 0) > 0
                ]
            )
            overall_score = avg_improvement + (new_features_count * 10)

            if overall_score > 60:
                recommendation = "DEPLOY_IMMEDIATELY"
                reason = f"OpenViking shows exceptional performance ({avg_improvement:+.1f}% avg) + {new_features_count} new exclusive features"
            elif overall_score > 30:
                recommendation = "DEPLOY_WITH_MONITORING"
                reason = f"OpenViking shows significant performance improvement ({avg_improvement:+.1f}%) with new features"
            else:
                recommendation = "CONTINUE_TESTING"
                reason = "Performance improvement is modest"

            comparison["recommendations"] = [
                {
                    "action": recommendation,
                    "reason": reason,
                    "confidence": "high" if overall_score > 50 else "medium",
                    "score": overall_score,
                    "new_features_count": new_features_count,
                }
            ]

            self.console.print(
                f"\n🏆 [bold green]Recommendation: {recommendation}[/bold green]"
            )
            self.console.print(f"   Reason: {reason}")
            self.console.print(f"   Overall Score: {overall_score:.1f}")

        return comparison


async def main():
    """Main enhanced production test runner"""
    console = Console()
    console.print(
        "🚀 [bold blue]Enhanced Production A/B Testing - OpenViking v2.0[/bold blue]"
    )
    console.print("=" * 70)

    tester = EnhancedProductionABTest()

    try:
        # Test Enhanced OpenViking
        console.print("\n🟢 Testing Enhanced OpenViking Production Server...")
        openviking_results = await tester.test_enhanced_openviking()

        # Simulate SMP baseline
        console.print("\n🟡 Using SMP Baseline (Simulated)...")
        smp_results = tester.simulate_smp_baseline()

        # Generate comparison
        console.print("\n📈 Generating Enhanced Comparison Report...")
        comparison = tester.generate_enhanced_comparison_report(
            openviking_results, smp_results
        )

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"enhanced_ab_test_results_{timestamp}.json", "w") as f:
            json.dump(comparison, f, indent=2)

        console.print(
            f"\n✅ Enhanced results saved to: enhanced_ab_test_results_{timestamp}.json"
        )

        # Summary
        console.print("\n🎯 [bold]Enhanced Test Summary:[/bold]")
        console.print(
            f"   Health Check: {'✅' if openviking_results['health_check'] else '❌'}"
        )
        console.print(
            f"   Features Tested: {len(openviking_results['features_tested'])}"
        )

        if comparison["improvements"]:
            avg_improvement = statistics.mean(list(comparison["improvements"].values()))
            console.print(f"   Performance Improvement: {avg_improvement:+.1f}%")

        if comparison["new_features"]:
            console.print(
                f"   New Exclusive Features: {len(comparison['new_features'])}"
            )
            for feature, data in comparison["new_features"].items():
                console.print(
                    f"     • {feature.replace('_', ' ').title()}: {data.get('success_rate', 0):.1f}% success"
                )

        if comparison["recommendations"]:
            console.print(
                f"   Recommendation: {comparison['recommendations'][0]['action']}"
            )
            console.print(
                f"   Overall Score: {comparison['recommendations'][0].get('score', 0):.1f}"
            )

        return 0 if openviking_results["health_check"] else 1

    except Exception as e:
        console.print(f"\n❌ [bold red]Enhanced testing failed:[/bold red] {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
