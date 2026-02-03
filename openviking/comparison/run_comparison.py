#!/usr/bin/env python3
"""
A/B Performance Comparison Framework
SMP vs OpenViking Performance Testing

Measures skill discovery efficiency, token usage, and response quality
between the current SMP system and OpenViking integration.
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement"""

    system: str  # 'smp' or 'openviking'
    scenario: str
    query: str
    response_time_ms: float
    token_usage: int
    success: bool
    error_message: str | None = None
    response_length: int = 0
    skill_discovery_time_ms: float = 0.0
    skills_found: int = 0


@dataclass
class ComparisonResult:
    """Aggregated comparison results"""

    scenario: str
    smp_avg_response_time: float
    openviking_avg_response_time: float
    smp_avg_tokens: int
    openviking_avg_tokens: int
    response_time_improvement: float  # percentage
    token_efficiency_improvement: float  # percentage
    smp_success_rate: float
    openviking_success_rate: float
    winner: str  # 'smp', 'openviking', or 'tie'
    statistical_significance: float = 0.0


class PerformanceComparator:
    """Main comparison engine"""

    def __init__(self):
        self.console = Console()
        self.setup_logging()

        # URLs from environment
        self.smp_url = os.getenv("SMP_AGENT_URL", "http://lightrag-main:9621")
        self.openviking_url = os.getenv(
            "OPENVIKING_AGENT_URL", "http://lightrag-experimental:9622"
        )
        self.results_dir = Path(os.getenv("COMPARISON_RESULTS_DIR", "/data/results"))

        self.metrics: list[PerformanceMetric] = []
        self.results: list[ComparisonResult] = []

        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Setup structured logging"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        self.log = structlog.get_logger()

    def load_test_scenarios(self) -> list[dict[str, Any]]:
        """Load test scenarios from configuration file"""
        scenarios_file = Path("/app/scenarios/test_scenarios.json")

        if not scenarios_file.exists():
            self.log.warning("Test scenarios file not found, using default scenarios")
            return self.get_default_scenarios()

        try:
            with open(scenarios_file) as f:
                return json.load(f)
        except Exception as e:
            self.log.error("Failed to load scenarios", error=str(e))
            return self.get_default_scenarios()

    def get_default_scenarios(self) -> list[dict[str, Any]]:
        """Default test scenarios for comparison"""
        return [
            {
                "name": "Skill Discovery - Complex",
                "queries": [
                    "Find skills for optimizing React performance",
                    "What tools help with database schema migrations?",
                    "I need to implement authentication in my API",
                    "How do I set up CI/CD for microservices?",
                    "Best practices for TypeScript error handling",
                ],
                "category": "skill_discovery",
                "expected_skills": [
                    "Librarian",
                    "PerformanceOptimizer",
                    "SecurityExpert",
                ],
            },
            {
                "name": "Token Efficiency - Long Context",
                "queries": [
                    "I'm building a comprehensive e-commerce platform with user authentication, product catalog, shopping cart, payment processing, order management, inventory tracking, and admin dashboard. What's the best approach?",
                    "Explain microservices architecture for a large-scale social media application including user feeds, messaging, notifications, media storage, and analytics.",
                    "I need to migrate a monolithic application to microservices. The current system handles user management, business logic, data processing, reporting, and API endpoints.",
                ],
                "category": "token_efficiency",
                "context_length": "long",
            },
            {
                "name": "Response Quality - Technical",
                "queries": [
                    "What are the key differences between GraphQL and REST APIs?",
                    "Explain event-driven architecture patterns",
                    "How does Kubernetes container orchestration work?",
                    "What are database indexing strategies for performance?",
                    "Compare SQL vs NoSQL databases for different use cases",
                ],
                "category": "response_quality",
            },
            {
                "name": "Speed - Simple Queries",
                "queries": [
                    "How to create a Python virtual environment?",
                    "Install npm packages globally",
                    "Git commit best practices",
                    "Docker basic commands",
                    "HTTP status codes cheat sheet",
                ],
                "category": "response_speed",
            },
        ]

    async def execute_query(
        self, system: str, query: str, scenario: str
    ) -> PerformanceMetric:
        """Execute single query against specified system"""

        url = self.smp_url if system == "smp" else self.openviking_url

        start_time = time.time()
        skill_discovery_start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepare request payload
                payload = {"query": query, "stream": False, "include_metrics": True}

                response = await client.post(
                    f"{url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                response_time = (time.time() - start_time) * 1000
                skill_discovery_time = (time.time() - skill_discovery_start) * 1000

                if response.status_code == 200:
                    data = response.json()

                    # Extract metrics from response
                    token_usage = data.get("token_usage", {}).get("total", 0)
                    response_text = data.get("response", "")
                    skills_found = len(data.get("skills_used", []))

                    return PerformanceMetric(
                        system=system,
                        scenario=scenario,
                        query=query,
                        response_time_ms=response_time,
                        token_usage=token_usage,
                        success=True,
                        response_length=len(response_text),
                        skill_discovery_time_ms=skill_discovery_time,
                        skills_found=skills_found,
                    )
                else:
                    return PerformanceMetric(
                        system=system,
                        scenario=scenario,
                        query=query,
                        response_time_ms=response_time,
                        token_usage=0,
                        success=False,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}",
                    )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return PerformanceMetric(
                system=system,
                scenario=scenario,
                query=query,
                response_time_ms=response_time,
                token_usage=0,
                success=False,
                error_message=str(e),
            )

    async def run_scenario_comparison(
        self, scenario: dict[str, Any]
    ) -> ComparisonResult:
        """Run comparison for a single scenario"""

        scenario_name = scenario["name"]
        queries = scenario["queries"]
        scenario.get("category", "general")

        self.log.info(
            "Running scenario comparison", scenario=scenario_name, queries=len(queries)
        )

        # Collect metrics for both systems
        smp_metrics = []
        openviking_metrics = []

        with Progress() as progress:
            total_tasks = len(queries) * 2  # Both systems
            task = progress.add_task(f"Testing {scenario_name}...", total=total_tasks)

            # Test SMP system
            for query in queries:
                metric = await self.execute_query("smp", query, scenario_name)
                smp_metrics.append(metric)
                self.metrics.append(metric)
                progress.update(task, advance=1)

            # Test OpenViking system
            for query in queries:
                metric = await self.execute_query("openviking", query, scenario_name)
                openviking_metrics.append(metric)
                self.metrics.append(metric)
                progress.update(task, advance=1)

        # Calculate aggregates
        return self.calculate_comparison_results(
            scenario_name, smp_metrics, openviking_metrics
        )

    def calculate_comparison_results(
        self,
        scenario: str,
        smp_metrics: list[PerformanceMetric],
        openviking_metrics: list[PerformanceMetric],
    ) -> ComparisonResult:
        """Calculate aggregated comparison results"""

        # Filter successful responses
        smp_successful = [m for m in smp_metrics if m.success]
        openviking_successful = [m for m in openviking_metrics if m.success]

        # Calculate averages
        smp_avg_response = (
            statistics.mean([m.response_time_ms for m in smp_successful])
            if smp_successful
            else float("inf")
        )
        openviking_avg_response = (
            statistics.mean([m.response_time_ms for m in openviking_successful])
            if openviking_successful
            else float("inf")
        )

        smp_avg_tokens = (
            statistics.mean([m.token_usage for m in smp_successful])
            if smp_successful
            else 0
        )
        openviking_avg_tokens = (
            statistics.mean([m.token_usage for m in openviking_successful])
            if openviking_successful
            else 0
        )

        # Calculate improvements
        response_time_improvement = (
            ((smp_avg_response - openviking_avg_response) / smp_avg_response * 100)
            if smp_avg_response > 0
            else 0
        )
        token_efficiency_improvement = (
            ((smp_avg_tokens - openviking_avg_tokens) / smp_avg_tokens * 100)
            if smp_avg_tokens > 0
            else 0
        )

        # Calculate success rates
        smp_success_rate = len(smp_successful) / len(smp_metrics) * 100
        openviking_success_rate = (
            len(openviking_successful) / len(openviking_metrics) * 100
        )

        # Determine winner
        winner = "tie"
        if response_time_improvement > 5 and token_efficiency_improvement > 5:
            winner = "openviking"
        elif response_time_improvement < -5 or token_efficiency_improvement < -5:
            winner = "smp"

        return ComparisonResult(
            scenario=scenario,
            smp_avg_response_time=smp_avg_response,
            openviking_avg_response_time=openviking_avg_response,
            smp_avg_tokens=int(smp_avg_tokens),
            openviking_avg_tokens=int(openviking_avg_tokens),
            response_time_improvement=response_time_improvement,
            token_efficiency_improvement=token_efficiency_improvement,
            smp_success_rate=smp_success_rate,
            openviking_success_rate=openviking_success_rate,
            winner=winner,
        )

    def generate_report(self) -> str:
        """Generate comprehensive comparison report"""

        report = f"""
# SMP vs OpenViking Performance Comparison Report

**Generated**: {datetime.now().isoformat()}
**Total Tests**: {len(self.metrics)} queries per system
**Scenarios**: {len(self.results)}

## Executive Summary

"""

        # Overall winner
        openviking_wins = sum(1 for r in self.results if r.winner == "openviking")
        smp_wins = sum(1 for r in self.results if r.winner == "smp")
        sum(1 for r in self.results if r.winner == "tie")

        if openviking_wins > smp_wins:
            report += "🏆 **OpenViking shows overall better performance**\n\n"
        elif smp_wins > openviking_wins:
            report += "🏆 **SMP shows overall better performance**\n\n"
        else:
            report += "⚖️ **Performance is comparable between systems**\n\n"

        # Results table
        report += "## Detailed Results\n\n"
        report += "| Scenario | SMP Response Time | OpenViking Response Time | Improvement | SMP Tokens | OpenViking Tokens | Token Efficiency | Winner |\n"
        report += "|----------|------------------|-------------------------|-------------|------------|-------------------|------------------|--------|\n"

        for result in self.results:
            report += f"| {result.scenario} | {result.smp_avg_response_time:.1f}ms | {result.openviking_avg_response_time:.1f}ms | {result.response_time_improvement:+.1f}% | {result.smp_avg_tokens} | {result.openviking_avg_tokens} | {result.token_efficiency_improvement:+.1f}% | {result.winner.upper()} |\n"

        # Performance analysis
        report += "\n\n## Performance Analysis\n\n"

        # Response time analysis
        smp_times = [
            r.smp_avg_response_time
            for r in self.results
            if r.smp_avg_response_time != float("inf")
        ]
        openviking_times = [
            r.openviking_avg_response_time
            for r in self.results
            if r.openviking_avg_response_time != float("inf")
        ]

        overall_improvement = 0
        if smp_times and openviking_times:
            avg_smp_time = statistics.mean(smp_times)
            avg_openviking_time = statistics.mean(openviking_times)
            overall_improvement = (
                (avg_smp_time - avg_openviking_time) / avg_smp_time * 100
            )

            report += "### Response Time Performance\n"
            report += f"- **SMP Average**: {avg_smp_time:.1f}ms\n"
            report += f"- **OpenViking Average**: {avg_openviking_time:.1f}ms\n"
            report += f"- **Overall Improvement**: {overall_improvement:+.1f}%\n\n"

        # Token efficiency analysis
        smp_tokens = [r.smp_avg_tokens for r in self.results if r.smp_avg_tokens > 0]
        openviking_tokens = [
            r.openviking_avg_tokens for r in self.results if r.openviking_avg_tokens > 0
        ]

        token_improvement = 0
        if smp_tokens and openviking_tokens:
            avg_smp_tokens = statistics.mean(smp_tokens)
            avg_openviking_tokens = statistics.mean(openviking_tokens)
            token_improvement = (
                (avg_smp_tokens - avg_openviking_tokens) / avg_smp_tokens * 100
            )

            report += "### Token Efficiency\n"
            report += f"- **SMP Average**: {int(avg_smp_tokens)} tokens\n"
            report += f"- **OpenViking Average**: {int(avg_openviking_tokens)} tokens\n"
            report += f"- **Overall Improvement**: {token_improvement:+.1f}%\n\n"

        # Success rate analysis
        smp_success = statistics.mean([r.smp_success_rate for r in self.results])
        openviking_success = statistics.mean(
            [r.openviking_success_rate for r in self.results]
        )

        report += "### Success Rate\n"
        report += f"- **SMP Success Rate**: {smp_success:.1f}%\n"
        report += f"- **OpenViking Success Rate**: {openviking_success:.1f}%\n\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if openviking_wins > smp_wins:
            report += "✅ **Proceed with OpenViking deployment** - Shows measurable improvements\n"
            if token_improvement > 10:
                report += "🚀 **Significant token savings achieved** - Cost-effective upgrade\n"
            if overall_improvement > 10:
                report += (
                    "⚡ **Performance gains substantial** - Better user experience\n"
                )
        elif smp_wins > openviking_wins:
            report += (
                "⚠️ **Maintain SMP system** - OpenViking needs further optimization\n"
            )
            report += "🔧 **Consider OpenViking improvements before deployment**\n"
        else:
            report += "🤔 **Performance equivalent** - Consider other factors like maintainability\n"

        report += "\n## Technical Details\n\n"
        report += "- **Test Environment**: Docker containers\n"
        report += f"- **SMP Endpoint**: {self.smp_url}\n"
        report += f"- **OpenViking Endpoint**: {self.openviking_url}\n"
        report += f"- **Total Queries Tested**: {len(self.metrics) // 2}\n"
        report += f"- **Test Duration**: {datetime.now().isoformat()}\n"

        return report

    async def run_comparison(self):
        """Main comparison workflow"""
        self.log.info("Starting SMP vs OpenViking performance comparison")

        try:
            # Load test scenarios
            scenarios = self.load_test_scenarios()
            self.console.print(f"📋 Loaded {len(scenarios)} test scenarios")

            # Verify both systems are available
            await self.verify_systems()

            # Run scenario comparisons
            with Progress() as progress:
                overall_task = progress.add_task(
                    "Running comparison scenarios...", total=len(scenarios)
                )

                for scenario in scenarios:
                    try:
                        result = await self.run_scenario_comparison(scenario)
                        self.results.append(result)
                        progress.update(overall_task, advance=1)

                    except Exception as e:
                        self.log.error(
                            "Scenario failed",
                            scenario=scenario.get("name", "unknown"),
                            error=str(e),
                        )
                        progress.update(overall_task, advance=1)

            # Generate and save report
            report = self.generate_report()

            # Save report
            report_path = (
                self.results_dir
                / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )
            with open(report_path, "w") as f:
                f.write(report)

            # Save raw metrics
            metrics_path = (
                self.results_dir
                / f"raw_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            metrics_data = [asdict(metric) for metric in self.metrics]
            with open(metrics_path, "w") as f:
                json.dump(metrics_data, f, indent=2)

            # Display results
            self.display_results()

            self.console.print(f"\n📄 **Report saved**: {report_path}")
            self.console.print(f"📊 **Raw metrics saved**: {metrics_path}")

            return True

        except Exception as e:
            self.log.error("Comparison failed", error=str(e), exc_info=True)
            self.console.print(f"❌ **Comparison failed**: {str(e)}")
            return False

    async def verify_systems(self):
        """Verify both SMP and OpenViking systems are available"""
        self.log.info("Verifying system availability")

        for system_name, url in [
            ("SMP", self.smp_url),
            ("OpenViking", self.openviking_url),
        ]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        self.console.print(f"✅ {system_name} system healthy")
                    else:
                        self.console.print(
                            f"⚠️ {system_name} system responding with status {response.status_code}"
                        )
            except Exception as e:
                self.console.print(f"❌ {system_name} system unavailable: {str(e)}")
                raise

    def display_results(self):
        """Display results summary in rich table"""
        table = Table(title="Performance Comparison Summary")
        table.add_column("Scenario", style="cyan")
        table.add_column("SMP (ms)", justify="right")
        table.add_column("OpenViking (ms)", justify="right")
        table.add_column("Improvement", justify="right")
        table.add_column("Tokens SMP", justify="right")
        table.add_column("Tokens OV", justify="right")
        table.add_column("Winner", style="bold")

        for result in self.results:
            winner_style = {"smp": "blue", "openviking": "green", "tie": "yellow"}.get(
                result.winner, "white"
            )

            table.add_row(
                result.scenario,
                f"{result.smp_avg_response_time:.1f}",
                f"{result.openviking_avg_response_time:.1f}",
                f"{result.response_time_improvement:+.1f}%",
                str(result.smp_avg_tokens),
                str(result.openviking_avg_tokens),
                f"[{winner_style}]{result.winner.upper()}[/{winner_style}]",
            )

        self.console.print(table)


async def main():
    """Main entry point"""
    comparator = PerformanceComparator()

    try:
        success = await comparator.run_comparison()
        return 0 if success else 1
    except KeyboardInterrupt:
        comparator.console.print("\n⚠️ Comparison interrupted")
        return 130
    except Exception as e:
        comparator.console.print(f"❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    import os
    import sys

    sys.exit(asyncio.run(main()))
