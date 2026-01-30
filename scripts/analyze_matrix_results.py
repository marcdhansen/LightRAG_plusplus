#!/usr/bin/env python3
"""
Performance Matrix Analysis Script

Analyzes performance matrix test results to generate insights and recommendations
for timing vs score trade-offs in RRF implementation.
"""

import json
import sys
from pathlib import Path
from typing import Any


def analyze_results(results_file: Path) -> dict[str, Any]:
    """Analyze performance matrix results and generate recommendations"""

    with open(results_file) as f:
        data = json.load(f)

    results = data.get("results", [])
    analysis = data.get("analysis", {})

    print("📊 PERFORMANCE MATRIX ANALYSIS")
    print("=" * 50)

    # Configuration summary
    print("\n🎯 CONFIGURATION PERFORMANCE")
    print("-" * 30)
    for config_name, config_analysis in analysis.get("summary", {}).items():
        print(f"\n{config_name}:")

        if "error" in config_analysis:
            print(f"  ❌ Status: {config_analysis['error']}")
        else:
            print(f"  ✅ Success Rate: {config_analysis.get('success_rate', 0):.1f}%")
            print(
                f"  ⏱️  Avg Query Time: {config_analysis.get('avg_query_time', 0):.1f}s"
            )
            print(f"  🎯 Avg Precision: {config_analysis.get('avg_precision', 0):.3f}")

            if "time_vs_expected" in config_analysis:
                print(f"  ⏰ Timing: {config_analysis['time_vs_expected']}")
            if "precision_vs_baseline" in config_analysis:
                print(f"  📈 Precision: {config_analysis['precision_vs_baseline']}")

            if "time_improvement" in config_analysis:
                print(f"  ⚡ Speed: {config_analysis['time_improvement']:+.1f}%")
            if "precision_improvement" in config_analysis:
                print(
                    f"  🎯 Precision: {config_analysis['precision_improvement']:+.1f}%"
                )

    # Trade-off analysis
    print("\n🔄 SPEED VS PRECISION TRADE-OFFS")
    print("-" * 30)

    recommendations = analysis.get("recommendations", [])
    if recommendations:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("\n💡 RECOMMENDATIONS: No specific recommendations")

    # Overall insights
    print("\n📈 OVERALL INSIGHTS")
    print("-" * 30)
    total_tests = len(results)
    successful_tests = len([r for r in results if r.get("success", False)])

    print(f"  📊 Total Tests: {total_tests}")
    print(f"  ✅ Successful Tests: {successful_tests}")
    print(f"  ❌ Failed Tests: {total_tests - successful_tests}")
    print(f"  📈 Overall Success Rate: {successful_tests / total_tests * 100:.1f}%")

    # Find best performing configuration
    best_config = None
    best_score = 0

    for config_name, config_analysis in analysis.get("summary", {}).items():
        if config_analysis.get("avg_precision", 0) > best_score:
            best_score = config_analysis.get("avg_precision", 0)
            best_config = config_name

    if best_config:
        print(f"  🏆 Best Configuration: {best_config}")
        print(f"  🎯 Best Precision: {best_score:.3f}")

    return {
        "best_config": best_config,
        "best_score": best_score,
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "analysis": analysis,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_matrix_results.py <results_file>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)

    insights = analyze_results(results_file)

    # Save insights summary
    insights_file = results_file.parent / "matrix_insights.json"
    with open(insights_file, "w") as f:
        json.dump(insights, f, indent=2)

    print(f"\n💾 Analysis insights saved to: {insights_file}")


if __name__ == "__main__":
    main()
