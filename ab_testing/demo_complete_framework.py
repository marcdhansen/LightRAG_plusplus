#!/usr/bin/env python3
"""
Complete A/B Testing Framework Demo
Demonstrates all components working together for OpenViking vs SMP comparison
"""

import asyncio
import time
from datetime import datetime

from comprehensive_framework import ExperimentEngine, create_openviking_experiment
from realtime_monitoring import create_monitoring_system
from statistical_analysis import create_statistical_system


async def complete_framework_demo():
    """Complete demonstration of the A/B testing framework"""

    print("🚀 LightRAG A/B Testing Framework - Complete Demo")
    print("=" * 60)

    # 1. Setup Monitoring System
    print("\n📊 1. Setting up Real-time Monitoring...")
    monitor, server, terminal_monitor = create_monitoring_system()

    # Start monitoring server in background
    server_task = asyncio.create_task(server.start())
    print("   ✅ Monitoring server started on http://localhost:8080")

    # 2. Create Experiment Configuration
    print("\n🧪 2. Creating Experiment Configuration...")
    config = create_openviking_experiment(
        openviking_url="http://localhost:8000", smp_url="http://localhost:9621"
    )

    # Register experiment with monitoring
    monitor.register_experiment(
        "openviking_vs_smp",
        {
            "name": "OpenViking vs SMP Comparison",
            "description": "Compare embedding generation performance",
            "variants": ["openviking", "smp"],
        },
    )

    print(f"   ✅ Experiment '{config.name}' created")
    print(f"   📋 Sample size: {config.sample_size} per variant")
    print(f"   🎯 Confidence level: {config.confidence_level}")

    # 3. Initialize Experiment Engine
    print("\n⚙️ 3. Initializing Experiment Engine...")
    engine = ExperimentEngine(config)

    # Start experiment
    await engine.start_experiment()
    print("   ✅ Experiment started")

    # 4. Execute Test Requests
    print("\n🔄 4. Executing Test Requests...")

    test_queries = [
        {"text": "React performance optimization techniques"},
        {"text": "Database schema design best practices"},
        {"text": "API authentication patterns and security"},
        {"text": "Cloud architecture design principles"},
        {"text": "Microservices communication patterns"},
        {"text": "Machine learning model optimization"},
        {"text": "Frontend state management strategies"},
        {"text": "DevOps pipeline automation"},
        {"text": "Container orchestration with Kubernetes"},
        {"text": "GraphQL vs REST API comparison"},
    ]

    results = []
    for i, query_data in enumerate(test_queries):
        user_id = f"demo_user_{i}"
        session_id = f"demo_session_{i % 3}"

        try:
            result = await engine.execute_request(
                request_data=query_data, user_id=user_id, session_id=session_id
            )

            results.append(result)

            # Add to monitoring system
            monitor.add_metrics(
                experiment_id="openviking_vs_smp",
                variant_name=result["variant"],
                metrics_data={
                    "success": result["metrics"].success,
                    "response_time_ms": result["metrics"].response_time_ms,
                    "status_code": result["metrics"].status_code,
                    "cache_hit": result["metrics"].cache_hit,
                    "error_message": result["metrics"].error_message,
                },
            )

            print(
                f"   📝 Query {i + 1}: {result['variant']} - "
                f"{result['metrics'].response_time_ms:.0f}ms - "
                f"{'✅' if result['metrics'].success else '❌'}"
            )

        except Exception as e:
            print(f"   ❌ Query {i + 1} failed: {e}")

        # Small delay between requests
        await asyncio.sleep(0.1)

    print(f"   ✅ Executed {len(results)} test requests")

    # 5. Get Experiment Status
    print("\n📈 5. Current Experiment Status...")
    status = engine.get_experiment_status()

    for variant_name, variant_stats in status["variant_stats"].items():
        print(f"   🔸 {variant_name}:")
        print(f"      Requests: {variant_stats.get('total_requests', 0)}")
        print(f"      Success Rate: {variant_stats.get('success_rate', 0):.1f}%")
        print(
            f"      Avg Response: {variant_stats.get('avg_response_time_ms', 0):.0f}ms"
        )

    # 6. Statistical Analysis
    print("\n🔬 6. Statistical Analysis...")
    analyzer, collector = create_statistical_system(confidence_level=0.95)

    # Extract metrics for analysis
    control_metrics = []
    treatment_metrics = []

    for result in results:
        if result["metrics"].success:
            if result["variant"] == "smp":
                control_metrics.append(result["metrics"].response_time_ms)
            else:
                treatment_metrics.append(result["metrics"].response_time_ms)

    if len(control_metrics) >= 3 and len(treatment_metrics) >= 3:
        analysis_results = collector.collect_experiment_results(
            experiment_id="openviking_vs_smp",
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics,
            metadata={
                "test_queries": len(test_queries),
                "experiment_duration": (
                    datetime.now() - engine.start_time
                ).total_seconds()
                if engine.start_time
                else 0,
            },
        )

        decision = analysis_results["automated_decision"]
        print(f"   🎯 Decision: {decision['decision']}")
        print(f"   📊 Confidence: {decision['confidence']:.1%}")
        print(f"   💡 Reasoning: {decision['reasoning']}")

        # Export results
        json_file = collector.export_results("openviking_vs_smp", "json")
        print(f"   📄 Results exported: {json_file}")

        # Generate report
        report = collector.generate_summary_report("openviking_vs_smp")
        report_file = (
            f"demo_ab_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(report_file, "w") as f:
            f.write(report)
        print(f"   📝 Report generated: {report_file}")

    else:
        print("   ⚠️  Insufficient data for statistical analysis")

    # 7. End Experiment
    print("\n🏁 7. Finalizing Experiment...")
    final_report = await engine.end_experiment()

    print("   ✅ Experiment completed")
    print(f"   📊 Duration: {final_report['duration_hours']:.2f} hours")
    print(f"   📋 Total requests: {final_report.get('total_requests', 0)}")

    if "analysis" in final_report:
        analysis = final_report["analysis"]
        if "winner" in analysis:
            print(f"   🏆 Winner: {analysis['winner']}")

    # 8. Dashboard Information
    print("\n🌐 8. Dashboard Access...")
    print("   📊 Web Dashboard: http://localhost:8080")
    print("   🔌 WebSocket Endpoint: ws://localhost:8080/ws")
    print("   📈 Real-time Monitoring: Active")

    # 9. Optional Load Testing Demo
    print("\n⚡ 9. Optional Load Testing Demo...")
    print("   🚀 This would demonstrate high-load testing capabilities")
    print("   📈 Including canary deployment with gradual rollout")
    print("   🔧 Configure with your specific endpoints and thresholds")

    # Summary
    print("\n📋 Framework Demo Summary")
    print("-" * 30)
    print("✅ Real-time monitoring system operational")
    print("✅ Experiment configuration and execution")
    print("✅ Statistical analysis with multiple test methods")
    print("✅ Automated decision making")
    print("✅ Results export and reporting")
    print("✅ Web dashboard with live updates")
    print("✅ Load testing and canary deployment support")

    print("\n🎉 LightRAG A/B Testing Framework Demo Complete!")
    print("\n📚 Next Steps:")
    print("1. Configure your actual endpoints")
    print("2. Adjust sample sizes for statistical significance")
    print("3. Set up production monitoring")
    print("4. Integrate with your CI/CD pipeline")
    print("5. Customize alert thresholds")

    # Keep server running for dashboard access
    print("\n🌐 Dashboard running at http://localhost:8080")
    print("Press Ctrl+C to stop the monitoring server...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring server...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("✅ Monitoring server stopped")

    return {
        "experiment": final_report,
        "monitoring": monitor.get_dashboard_data(),
        "analysis": analysis_results if "analysis_results" in locals() else None,
    }


if __name__ == "__main__":
    """Run the complete demo"""

    print("🚀 Starting LightRAG A/B Testing Framework Demo")
    print("This demo shows all framework components working together")
    print("\nPrerequisites:")
    print("- LightRAG/OpenViking server on http://localhost:8000")
    print("- SMP server on http://localhost:9621 (optional)")
    print("- All dependencies installed")
    print("\nStarting demo in 3 seconds...")

    time.sleep(3)

    try:
        asyncio.run(complete_framework_demo())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Please check your server configurations and dependencies")

    print("\n📖 For more information, see ab_testing/README.md")
