#!/usr/bin/env python3
"""
Integration script for multi-phase detection with SOP evaluation
Enhances existing SOP evaluation pipeline with multi-phase detection
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the script directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from multi_phase_detector import MultiPhaseDetector
from sop_compliance_validator import SOPComplianceValidator


class SOPEvaluationEnhancer:
    """
    Integration with existing SOP evaluation pipeline
    """

    def __init__(self):
        self.multi_phase_detector = MultiPhaseDetector()
        self.sop_validator = SOPComplianceValidator()

    def enhanced_sop_evaluation(self) -> dict:
        """
        Enhanced SOP evaluation with multi-phase detection
        """
        print("🔍 Running enhanced SOP evaluation with multi-phase detection...")

        # Run standard SOP validation
        print("   📋 Running standard SOP validation...")
        try:
            sop_results = self.sop_validator.validate_all_sop_rules()
        except Exception as e:
            print(f"     Warning: SOP validation failed: {e}")
            sop_results = {"status": "error", "error": str(e)}

        # Add multi-phase detection
        print("   🔍 Running multi-phase detection...")
        multi_phase_results = self.multi_phase_detector.run_detection()

        # Combine results
        combined_results = {
            "timestamp": datetime.now().isoformat(),
            "standard_sop": sop_results,
            "multi_phase_detection": multi_phase_results,
            "overall_status": self.calculate_overall_status(
                sop_results, multi_phase_results
            ),
        }

        # Block if multi-phase detected
        if multi_phase_results["is_multi_phase"]:
            combined_results["block_reason"] = (
                "Multi-phase implementation detected - mandatory hand-off protocol required"
            )
            combined_results["remediation"] = self.generate_multi_phase_remediation(
                multi_phase_results
            )

        return combined_results

    def calculate_overall_status(
        self, sop_results: dict, multi_phase_results: dict
    ) -> str:
        """Calculate overall validation status"""

        # Check for blocking conditions
        if multi_phase_results["is_multi_phase"]:
            return "blocked_multi_phase"

        if sop_results.get("status") == "blocked":
            return "blocked_sop"

        if sop_results.get("status") == "passed":
            return "passed"

        return "unknown"

    def generate_multi_phase_remediation(self, multi_phase_results: dict) -> list:
        """Generate remediation steps for multi-phase detection"""
        remediation = [
            "🚨 MULTI-PHASE IMPLEMENTATION DETECTED",
            "",
            "🔧 Required Actions:",
            "1. Split work into single-phase tasks",
            "2. Use proper hand-off protocol between phases",
            "3. Create separate branches for each phase",
            "4. Document each phase separately",
            "",
            "📋 Detection Details:",
        ]

        for category, count in multi_phase_results["indicators"].items():
            if count > 0:
                remediation.append(f"   - {category}: {count} indicators")

        remediation.extend(
            [
                "",
                "💡 Recommended Approach:",
                "1. Create individual task for each phase",
                "2. Use /plan scope for each task separately",
                "3. Complete each phase with proper RTB",
                "4. Use beads to track phase dependencies",
            ]
        )

        return remediation

    def log_enhanced_evaluation(self, results: dict) -> None:
        """Log enhanced evaluation results"""
        log_dir = Path(".agent/logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"enhanced_sop_evaluation_{int(time.time())}.json"

        try:
            with open(log_file, "w") as f:
                json.dump(results, f, indent=2)

            print(f"   📝 Enhanced evaluation logged to: {log_file}")

        except Exception as e:
            print(f"   Warning: Could not log enhanced evaluation: {e}")


def main():
    """Main integration workflow"""
    print("🚨 Enhanced SOP Evaluation with Multi-Phase Detection")
    print("=" * 60)

    # Initialize enhancer
    enhancer = SOPEvaluationEnhancer()

    # Run enhanced evaluation
    results = enhancer.enhanced_sop_evaluation()

    # Output results
    print("\n📊 Enhanced Evaluation Results:")
    print(f"   Overall Status: {results['overall_status']}")

    # Show multi-phase detection results
    mp_results = results["multi_phase_detection"]
    print(
        f"   Multi-Phase: {'🚨 DETECTED' if mp_results['is_multi_phase'] else '✅ CLEAR'}"
    )
    print(f"   Indicators: {mp_results['total_indicators']}/{mp_results['threshold']}")

    # Show SOP results
    sop_results = results.get("standard_sop", {})
    if sop_results:
        print(f"   SOP Status: {sop_results.get('status', 'unknown')}")

    # Handle blocking conditions
    if results["overall_status"] == "blocked_multi_phase":
        print("\n🚨 BLOCKED: Multi-Phase Implementation Detected")
        print("🔧 Remediation:")
        for step in results["remediation"]:
            print(f"   {step}")

        enhancer.log_enhanced_evaluation(results)
        sys.exit(1)  # Block RTB

    elif results["overall_status"] == "blocked_sop":
        print("\n🚫 BLOCKED: SOP Validation Failed")
        print("💡 Run recommended skills and retry RTB")

        enhancer.log_enhanced_evaluation(results)
        sys.exit(1)  # Block RTB

    else:
        print("\n✅ Enhanced evaluation passed - RTB can proceed")

        enhancer.log_enhanced_evaluation(results)
        sys.exit(0)  # Allow RTB


if __name__ == "__main__":
    main()
