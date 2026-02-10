#!/usr/bin/env python3
"""
Orchestrator Adaptive Bridge

Bridge between Orchestrator and Adaptive SOP system.
Provides dynamic rule checking for Orchestrator validation.
"""

import json
import sys
from pathlib import Path

# Add adaptive integration to path
sys.path.append(str(Path(__file__).parent))

from adaptive_orchestrator_integration import AdaptiveOrchestratorIntegration


def get_adaptive_rules():
    """Get current adaptive rules for Orchestrator"""
    integration = AdaptiveOrchestratorIntegration()
    return integration.adaptive_rules


def check_adaptive_compliance(phase: str) -> dict:
    """Check compliance using adaptive rules for specific phase"""
    integration = AdaptiveOrchestratorIntegration()
    rules = integration.adaptive_rules

    # Get current enforcement level
    enforcement_level = rules["current_enforcement_level"]
    level_config = rules["dynamic_rules"]["enforcement_levels"][enforcement_level]

    # Phase-specific checks
    if phase == "initialization":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"][
                "base_interval"
            ],
            "checks": {
                "tools_required": True,
                "workspace_integrity": True,
                "context_available": True,
                "adaptive_threshold": True,
            },
        }
    elif phase == "execution":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"][
                "base_interval"
            ],
            "checks": {
                "feature_branch": True,
                "beads_issue": True,
                "plan_approval": True,
                "tdd_compliance": True,
                "adaptive_threshold": True,
            },
        }
    elif phase == "finalization":
        return {
            "enforcement_level": enforcement_level,
            "blocking_enabled": level_config["blocking_enabled"],
            "violation_tolerance": level_config["violation_tolerance"],
            "monitoring_interval": rules["dynamic_rules"]["monitoring_frequency"][
                "base_interval"
            ],
            "checks": {
                "git_clean": True,
                "atomic_commits": True,
                "reflection_captured": True,
                "code_review": True,
                "adaptive_threshold": True,
            },
        }
    else:
        return {"error": f"Unknown phase: {phase}"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_adaptive_bridge.py <phase>")
        sys.exit(1)

    phase = sys.argv[1]
    result = check_adaptive_compliance(phase)
    print(json.dumps(result, indent=2))
