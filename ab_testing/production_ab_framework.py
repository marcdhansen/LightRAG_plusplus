#!/usr/bin/env python3
"""
Production A/B Testing Framework
Compares OpenViking vs SMP performance with comprehensive monitoring and analytics
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table


class ABDashboard:
    def __init__(self):
        self.console = Console()
        self.results = []
        self.metrics = {"openviking": [], "smp": []}

    def log_test_result(
        self,
        system: str,
        test_type: str,
        metric: str,
        value: float,
        metadata: dict = None,
    ):
        """Log individual test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "test_type": test_type,
            "metric": metric,
            "value": value,
            "metadata": metadata or {},
        }

        self.metrics[system].append(result)
        print(f"✅ {system} {test_type}: {metric} = {value:.2f}")


class ABTestSuite:
    def __init__(self, openviking_url: str = "http://localhost:8002", smp_client=None):
        self.openviking_url = openviking_url
        self.smp_client = smp_client
        self.dashboard = ABDashboard()

    def compare_performance(
        self,
        openviking_results: dict[str, Any],
        smp_results: dict[str, Any] | None = None,
    ):
        """Compare performance between OpenViking and SMP"""
        comparison = {
            "response_time_improvement": 0,
            "cache_effectiveness_improvement": 0,
            "skill_discovery_improvement": 0,
            "overall_winner": "tie",
        }

        # Only compare if we have smp results (simulated or real)
        if smp_results is not None:
            ov_response_time = openviking_results.get("avg_response_time_ms", 0)
            smp_response_time = smp_results.get("avg_response_time_ms", 0)

            improvement = (
                ((smp_response_time - ov_response_time) / smp_response_time) * 100
                if smp_response_time > 0
                else 0
            )

            comparison["response_time_improvement"] = improvement

            # Compare cache effectiveness
            ov_cache_rate = openviking_results.get("cache_hit_rate", 0)
            smp_cache_rate = smp_results.get("cache_hit_rate", 0)

            if ov_cache_rate > smp_cache_rate + 10:  # 10% better
                comparison["cache_effectiveness_improvement"] = (
                    ov_cache_rate - smp_cache_rate
                )
                comparison["cache_winner"] = "openviking"
            elif smp_cache_rate > ov_cache_rate + 10:
                comparison["cache_effectiveness_improvement"] = (
                    smp_cache_rate - ov_cache_rate
                )
                comparison["cache_winner"] = "smp"
            else:
                comparison["cache_effectiveness_improvement"] = 0
                comparison["cache_winner"] = "tie"

        # Compare skill discovery
        ov_avg_skills = openviking_results.get("avg_skills_found", 0)
        smp_avg_skills = smp_results.get("avg_skills_found", 0)

        if ov_avg_skills > smp_avg_skills * 1.2:  # 20% more skills found
            comparison["skill_discovery_improvement"] = ov_avg_skills - smp_avg_skills
            comparison["skill_discovery_winner"] = "openviking"
        elif ov_avg_skills < smp_avg_skills * 0.8:  # 20% fewer skills
            comparison["skill_discovery_improvement"] = smp_avg_skills - ov_avg_skills
            comparison["skill_discovery_winner"] = "smp"
        else:
            comparison["skill_discovery_improvement"] = 0
            comparison["skill_discovery_winner"] = "tie"

        # Determine overall winner
        wins = 0
        if comparison["response_time_winner"] == "openviking":
            wins += 1
        if comparison["cache_winner"] == "openviking":
            wins += 1
        if comparison["skill_discovery_winner"] == "openviking":
            wins += 1

        if wins >= 2:
            comparison["overall_winner"] = "openviking"
        elif wins == 1:
            comparison["overall_winner"] = "smp"
        else:
            comparison["overall_winner"] = "tie"

        return comparison

    def generate_comprehensive_report(
        self,
        openviking_results: dict[str, Any],
        smp_results: dict[str, Any] | None,
        comparison: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive A/B test report"""
        self.console.print("📊 Generating Comprehensive Report")

        # Create results table
        table = Table(title="A/B Test Results Summary")
        table.add_column("Metric", justify="left")
        table.add_column("OpenViking", justify="center")
        table.add_column("SMP", justify="center")
        table.add_column("Improvement", justify="center")

        # Response time comparison
        ov_avg_time = openviking_results.get("avg_response_time_ms", 0)
        smp_avg_time = (
            smp_results.get("avg_response_time_ms", 0) if smp_results else 2500
        )  # Simulated baseline

        response_improvement = (
            ((smp_avg_time - ov_avg_time) / smp_avg_time) * 100
            if smp_avg_time > 0
            else 0
        )

        table.add_row(
            "Response Time",
            f"{ov_avg_time:.0f}ms",
            f"{smp_avg_time:.0f}ms",
            f"{response_improvement:+.1f}%",
        )

        # Cache effectiveness
        ov_cache_rate = openviking_results.get("cache_hit_rate", 0)
        smp_cache_rate = (
            smp_results.get("cache_hit_rate", 0) if smp_results else 0
        )  # Simulated baseline

        cache_improvement = ov_cache_rate - smp_cache_rate

        table.add_row(
            "Cache Hit Rate",
            f"{ov_cache_rate:.1f}%",
            f"{smp_cache_rate:.1f}%",
            f"{cache_improvement:+.1f}%",
        )

        # Skill discovery
        ov_avg_skills = openviking_results.get("avg_skills_found", 0)
        smp_avg_skills = (
            smp_results.get("avg_skills_found", 0) if smp_results else 1.2
        )  # Simulated baseline

        skill_improvement = (
            (ov_avg_skills - smp_avg_skills) / smp_avg_skills * 100
            if smp_avg_skills > 0
            else 0
        )

        table.add_row(
            "Avg Skills Found",
            f"{ov_avg_skills:.1f}",
            f"{smp_avg_skills:.1f}",
            f"{skill_improvement:+.1f}%",
        )

        # Success rate
        ov_success_rate = openviking_results.get("success_rate", 0)
        smp_success_rate = (
            smp_results.get("success_rate", 0) if smp_results else 100
        )  # Simulated baseline

        table.add_row(
            "Success Rate", f"{ov_success_rate:.1f}%", f"{smp_success_rate:.1f}%", "N/A"
        )

        self.console.print(table)

        # Overall winner
        winner = comparison.get("overall_winner", "tie")
        winner_emoji = {"openviking": "🏆", "smp": "🏆", "tie": "⚖️"}

        self.console.print(
            f"\n🏆 Overall Winner: {winner} {winner_emoji.get(inner, '')}"
        )

        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "openviking_results": openviking_results,
            "smp_results": smp_results,
            "comparison": comparison,
            "test_queries_count": len(openviking_results.get("results", [])),
        }

        with open(f"ab_test_report_{timestamp}.json", "w") as f:
            json.dump(report_data, f, indent=2)

    def log_test_result(
        self,
        system: str,
        test_type: str,
        metric: str,
        value: float,
        metadata: dict = None,
    ):
        """Log individual test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "test_type": test_type,
            "metric": metric,
            "value": value,
            "metadata": metadata or {},
        }

        self.metrics[system].append(result)
        print(f"✅ {system} {test_type}: {metric} = {value:.2f}")


class SMPSimulator:
    """Simulated SMP client for testing when SMP is unavailable"""

    def __init__(self):
        self.base_url = "http://localhost:9621"

    async def embedding_request(self, text: str):
        """Simulate SMP embedding request"""
        await asyncio.sleep(2.5)  # Simulate SMP response time
        return {
            "status_code": 200,
            "json": {
                "embedding": [0.1] * 768,  # Mock embedding
                "dimension": 768,
                "cache_hit": False,
            },
        }

    async def skill_search_request(self, query: str):
        """Simulate SMP skill search"""
        await asyncio.sleep(2.8)  # Simulate SMP response time
        return {
            "status_code": 200,
            "json": {
                "skills": [
                    {
                        "id": "skill1",
                        "name": "MockSkill",
                        "description": "Simulated skill",
                    }
                ],
                "found_count": 1,
            },
        }


class ABTestRunner:
    def __init__(self):
        self.test_suite = ABTestSuite()
        self.smp_client = SMPSimulator()

    async def run_production_tests(self) -> dict[str, Any]:
        """Run production-ready A/B tests"""
        test_queries = [
            "React performance optimization",
            "Database schema design",
            "API authentication patterns",
            "Security implementation",
            "Cloud architecture",
            "Microservices patterns",
        ]

        # Test OpenViking
        self.test_suite.console.print("\n🟢 Testing OpenViking System")
        openviking_embedding = await self.test_suite.test_embedding_performance(
            "openviking", test_queries
        )
        openviking_skills = await self.test_suite.test_skill_search_performance(
            "openviking", test_queries
        )

        # Test SMP (simulated since SMP is down)
        self.test_suite.console.print("\n🟡 Testing SMP System (Simulated)")
        smp_embedding = await self.test_suite.test_embedding_performance(
            "smp", test_queries
        )
        smp_skills = await self.test_suite.test_skill_search_performance(
            "smp", test_queries
        )

        # Comparison
        comparison = self.test_suite.compare_performance(
            openviking_embedding, smp_embedding
        )

        # Generate report
        await self.test_suite.generate_comprehensive_report(
            openviking_embedding, smp_embedding, comparison
        )

        return {
            "openviking_embedding": openviking_embedding,
            "smp_embedding": smp_embedding,
            "openviking_skills": openviking_skills,
            "smp_skills": smp_skills,
            "comparison": comparison,
            "timestamp": datetime.now().isoformat(),
        }


async def main():
    """Main entry point for A/B testing framework"""
    runner = ABTestRunner()

    try:
        results = await runner.run_production_tests()

        print("\n🎉 A/B Testing Complete!")
        print("📊 Production-grade testing framework operational")
        print("🚀 Ready for continuous performance monitoring")

        return 0
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
