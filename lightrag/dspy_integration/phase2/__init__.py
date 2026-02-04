"""
DSPy Phase 2: Production-Ready Optimization System

This module provides the main entry point for DSPy Phase 2 functionality,
integrating all components into a comprehensive production-ready optimization system.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .production_pipeline import ProductionDataPipeline
from .realtime_monitoring import RealTimeMonitor, get_global_monitor
from .prompt_replacement import PromptReplacementPipeline
from .ace_cot_integration import ACECoTIntegration
from .prompt_family_optimization import PromptFamilyOptimizer
from .realtime_optimizer import RealTimeOptimizer, OptimizationConfig


class DSPyPhase2Manager:
    """Main manager for DSPy Phase 2 integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize all components
        self.production_pipeline = ProductionDataPipeline()
        self.replacement_pipeline = PromptReplacementPipeline()
        self.ace_integration = ACECoTIntegration()
        self.family_optimizer = PromptFamilyOptimizer()

        # Initialize real-time components
        optimization_config = OptimizationConfig(
            enable_automatic_optimization=self.config.get(
                "enable_automatic_optimization", True
            ),
            performance_degradation_threshold=self.config.get(
                "performance_degradation_threshold", 0.15
            ),
            feedback_volume_threshold=self.config.get("feedback_volume_threshold", 50),
            optimization_interval_hours=self.config.get(
                "optimization_interval_hours", 24
            ),
        )

        self.realtime_optimizer = RealTimeOptimizer(optimization_config)
        self.global_monitor = get_global_monitor()

        # Integration status
        self.components_initialized = False
        self.production_ready = False

    async def initialize(self):
        """Initialize all DSPy Phase 2 components."""

        if self.components_initialized:
            return

        self.logger.info("🚀 Initializing DSPy Phase 2 components...")

        try:
            # Initialize production pipeline
            self.logger.info("📊 Setting up production data pipeline...")
            # Production pipeline is initialized in constructor

            # Initialize ACE integration
            self.logger.info("🧠 Setting up ACE CoT integration...")
            # ACE integration creates optimized modules automatically

            # Initialize family optimizer
            self.logger.info("🎯 Setting up prompt family optimizer...")
            # Family optimizer initializes families automatically

            # Setup real-time monitoring alerts
            self.logger.info("📡 Setting up real-time monitoring...")
            from .realtime_monitoring import setup_default_alerts, log_alert_callback

            setup_default_alerts(self.global_monitor)
            self.global_monitor.add_alert_callback(log_alert_callback)

            self.components_initialized = True
            self.logger.info("✅ DSPy Phase 2 components initialized successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize DSPy Phase 2: {e}")
            raise

    async def start_production_mode(self):
        """Start DSPy Phase 2 in production mode."""

        if not self.components_initialized:
            await self.initialize()

        if self.production_ready:
            return

        self.logger.info("🏭 Starting DSPy Phase 2 production mode...")

        try:
            # Start real-time optimizer
            await self.realtime_optimizer.start()

            # Start real-time monitoring
            self.global_monitor.start_monitoring(check_interval_seconds=60)

            self.production_ready = True
            self.logger.info("✅ DSPy Phase 2 production mode started successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to start production mode: {e}")
            raise

    async def stop_production_mode(self):
        """Stop DSPy Phase 2 production mode."""

        if not self.production_ready:
            return

        self.logger.info("⏹️ Stopping DSPy Phase 2 production mode...")

        try:
            # Stop real-time optimizer
            await self.realtime_optimizer.stop()

            # Stop monitoring
            self.global_monitor.stop_monitoring()

            self.production_ready = False
            self.logger.info("✅ DSPy Phase 2 production mode stopped")

        except Exception as e:
            self.logger.error(f"❌ Error stopping production mode: {e}")

    async def run_full_evaluation(
        self,
        hours_back: int = 24,
        optimize_families: bool = True,
        deploy_improvements: bool = False,
    ) -> Dict[str, Any]:
        """Run a complete DSPy Phase 2 evaluation cycle."""

        self.logger.info(f"🔄 Running full evaluation (last {hours_back} hours)...")

        results = {
            "evaluation_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "production_evaluation": None,
            "family_optimization": None,
            "ace_integration": None,
            "replacement_candidates": None,
            "deployments": None,
        }

        try:
            # Step 1: Production data evaluation
            self.logger.info("📊 Step 1: Production data evaluation...")
            prod_results = await self.production_pipeline.run_production_evaluation(
                hours_back=hours_back
            )
            results["production_evaluation"] = prod_results

            # Step 2: Prompt family optimization
            if optimize_families:
                self.logger.info("🎯 Step 2: Prompt family optimization...")
                from .prompt_family_optimization import PromptFamily

                family_results = await self.family_optimizer.optimize_all_families(
                    models=["1.5b", "3b", "7b"], parallel=True
                )
                results["family_optimization"] = {
                    family.value: [r.to_dict() for r in family_results]
                    for family, family_results in family_results.items()
                }

            # Step 3: Identify replacement candidates
            self.logger.info("🔄 Step 3: Identify replacement candidates...")
            candidates = (
                await self.replacement_pipeline.identify_replacement_candidates(
                    days_back=max(1, hours_back // 24)
                )
            )
            results["replacement_candidates"] = [c.to_dict() for c in candidates]

            # Step 4: Deploy improvements if requested
            if deploy_improvements and candidates:
                self.logger.info("🚀 Step 4: Deploy improvements...")
                deployed = await self.replacement_pipeline.run_automated_replacement(
                    days_back=max(1, hours_back // 24),
                    max_deployments=3,
                    auto_deploy=True,
                )
                results["deployments"] = deployed

            results["completed_at"] = datetime.now().isoformat()
            results["status"] = "completed"

            self.logger.info("✅ Full evaluation completed successfully")

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["completed_at"] = datetime.now().isoformat()

            self.logger.error(f"❌ Evaluation failed: {e}")

        # Save results
        await self._save_evaluation_results(results)

        return results

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""

        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {
                "initialized": self.components_initialized,
                "production_ready": self.production_ready,
            },
            "realtime_monitoring": self.global_monitor.get_current_performance(),
            "optimizer_status": self.realtime_optimizer.get_optimization_status(),
            "family_optimizer_summary": self.family_optimizer.get_optimization_summary(),
            "ace_integration": {
                "enabled": True,
                "modules_created": len(self.ace_integration.optimizer.cot_modules),
            },
        }

        return status

    async def add_production_feedback(
        self,
        variant: str,
        model: str,
        feedback_score: float,
        feedback_type: str = "quality",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add production feedback to the optimization system."""

        await self.realtime_optimizer.add_feedback(
            variant, model, feedback_score, feedback_type, metadata
        )

    async def add_production_metrics(
        self,
        variant: str,
        model: str,
        latency_ms: float,
        success: bool = True,
        quality_score: Optional[float] = None,
    ):
        """Add production metrics to the monitoring system."""

        from .realtime_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics(
            variant=variant,
            model=model,
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            success=success,
            quality_score=quality_score,
        )

        await self.realtime_optimizer.add_performance_metric(metrics)

    async def _save_evaluation_results(self, results: Dict[str, Any]):
        """Save evaluation results to file."""

        results_file = Path(f"dspy_phase2_evaluation_{results['evaluation_id']}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"📁 Evaluation results saved to {results_file}")

    def get_deployment_recommendations(self) -> List[Dict[str, Any]]:
        """Get deployment recommendations based on current analysis."""

        recommendations = []

        # Analyze recent performance
        current_perf = self.global_monitor.get_current_performance(window_minutes=30)

        for key, data in current_perf.items():
            stats = data.get("stats", {})

            # Check for performance issues
            success_rate = stats.get("success_rate", 1.0)
            latency = stats.get("latency_mean", 0)

            if success_rate < 0.9:
                recommendations.append(
                    {
                        "priority": "high",
                        "type": "performance",
                        "target": key,
                        "issue": f"Low success rate: {success_rate:.1%}",
                        "recommendation": "Optimize for reliability using DSPy",
                    }
                )

            if latency > 5000:  # 5 seconds
                recommendations.append(
                    {
                        "priority": "medium",
                        "type": "performance",
                        "target": key,
                        "issue": f"High latency: {latency:.0f}ms",
                        "recommendation": "Optimize for speed using DSPy",
                    }
                )

        # Add general recommendations
        if not recommendations:
            recommendations.append(
                {
                    "priority": "low",
                    "type": "maintenance",
                    "target": "system",
                    "issue": "No immediate issues detected",
                    "recommendation": "Continue monitoring and schedule regular optimization",
                }
            )

        return recommendations


# Global manager instance
_global_manager: Optional[DSPyPhase2Manager] = None


def get_dspy_phase2_manager(
    config: Optional[Dict[str, Any]] = None,
) -> DSPyPhase2Manager:
    """Get or create the global DSPy Phase 2 manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = DSPyPhase2Manager(config)
    return _global_manager


# CLI interface
async def main():
    """Run DSPy Phase 2 from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DSPy Phase 2 Production-Ready Optimization"
    )
    parser.add_argument("--init", action="store_true", help="Initialize components")
    parser.add_argument("--start", action="store_true", help="Start production mode")
    parser.add_argument("--stop", action="store_true", help="Stop production mode")
    parser.add_argument("--evaluate", action="store_true", help="Run full evaluation")
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of data to evaluate"
    )
    parser.add_argument(
        "--optimize", action="store_true", help="Optimize prompt families"
    )
    parser.add_argument("--deploy", action="store_true", help="Deploy improvements")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument(
        "--feedback",
        nargs=4,
        metavar=("VARIANT", "MODEL", "SCORE", "TYPE"),
        help="Add production feedback",
    )
    parser.add_argument(
        "--metrics",
        nargs=3,
        metavar=("VARIANT", "MODEL", "LATENCY"),
        help="Add production metrics",
    )
    parser.add_argument(
        "--recommendations", action="store_true", help="Show deployment recommendations"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Get manager
    manager = get_dspy_phase2_manager()

    try:
        if args.init:
            print("🔧 Initializing DSPy Phase 2 components...")
            await manager.initialize()
            print("✅ Components initialized successfully")

        elif args.start:
            print("🚀 Starting DSPy Phase 2 production mode...")
            await manager.start_production_mode()
            print("✅ Production mode started")

            try:
                while True:
                    await asyncio.sleep(60)
                    status = await manager.get_system_status()
                    print(
                        f"\n📊 Active optimizations: {status['optimizer_status']['active_optimizations']}"
                    )
            except KeyboardInterrupt:
                print("\n⏹️ Stopping production mode...")
                await manager.stop_production_mode()
                print("✅ Production mode stopped")

        elif args.stop:
            print("⏹️ Stopping DSPy Phase 2 production mode...")
            await manager.stop_production_mode()
            print("✅ Production mode stopped")

        elif args.evaluate:
            print(f"🔄 Running full evaluation (last {args.hours} hours)...")
            results = await manager.run_full_evaluation(
                hours_back=args.hours,
                optimize_families=args.optimize,
                deploy_improvements=args.deploy,
            )

            print(f"✅ Evaluation completed: {results['status']}")
            if results["production_evaluation"]:
                prod_eval = results["production_evaluation"]
                print(
                    f"📊 Production evaluation: {len(prod_eval.get('top_variants', []))} top variants"
                )
            if results["replacement_candidates"]:
                print(
                    f"🔄 Replacement candidates: {len(results['replacement_candidates'])}"
                )

        elif args.status:
            print("📊 DSPy Phase 2 System Status:")
            status = await manager.get_system_status()

            print(f"  Components Initialized: {status['components']['initialized']}")
            print(f"  Production Ready: {status['components']['production_ready']}")
            print(
                f"  Active Optimizations: {status['optimizer_status']['active_optimizations']}"
            )
            print(
                f"  Performance Baselines: {len(status['optimizer_status']['performance_baselines'])}"
            )
            print(f"  ACE Modules: {status['ace_integration']['modules_created']}")

        elif args.recommendations:
            print("💡 Deployment Recommendations:")
            recommendations = manager.get_deployment_recommendations()

            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. [{rec['priority'].upper()}] {rec['target']}")
                print(f"   Issue: {rec['issue']}")
                print(f"   Recommendation: {rec['recommendation']}")

        elif args.feedback:
            variant, model, score, feedback_type = args.feedback
            await manager.add_production_feedback(
                variant, model, float(score), feedback_type
            )
            print(f"✅ Added feedback: {variant} on {model} = {score}")

        elif args.metrics:
            variant, model, latency = args.metrics
            await manager.add_production_metrics(variant, model, float(latency))
            print(f"✅ Added metrics: {variant} on {model} = {latency}ms")

        else:
            print("❌ No action specified. Use --help for options.")

    except Exception as e:
        print(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    asyncio.run(main())
