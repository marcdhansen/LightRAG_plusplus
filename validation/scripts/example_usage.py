#!/usr/bin/env python3
"""
Example usage of the Incremental Validation System
Demonstrates how to integrate with existing LightRAG workflows
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.milestone_validator import MilestoneValidator
from validation.workflow_orchestrator import MilestoneWorkflowOrchestrator


async def example_basic_validation():
    """Example: Basic milestone validation"""
    print("🎯 Example 1: Basic Milestone Validation")
    print("=" * 50)

    orchestrator = MilestoneWorkflowOrchestrator()

    # Validate development milestone
    result = await orchestrator.advance_to_milestone(
        "development", task_ids=["lightrag-123", "lightrag-456"]
    )

    print(f"Milestone: {result.milestone_id}")
    print(f"Passed: {result.passed}")
    print(f"Duration: {result.validation_duration_seconds:.1f}s")

    if result.blocking_issues:
        print("Blocking issues:")
        for issue in result.blocking_issues:
            print(f"  - {issue}")

    if result.recommendations:
        print("Recommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")

    print()


async def example_workflow_status():
    """Example: Check workflow status"""
    print("📊 Example 2: Workflow Status Check")
    print("=" * 50)

    orchestrator = MilestoneWorkflowOrchestrator()

    # Get workflow summary
    summary = orchestrator.get_workflow_summary()
    print(f"Progress: {summary['progress_percentage']:.1f}%")
    print(f"Current milestone: {summary['current_milestone']}")
    print(f"Completed: {summary['completed_milestones']}/{summary['total_milestones']}")

    # Get detailed milestone status
    status = orchestrator.get_milestone_status()
    print("\nMilestone Details:")
    for _milestone_id, data in status.items():
        print(f"  {data['order']}. {data['name']} - {data['status']}")

    print()


async def example_force_advance():
    """Example: Force advance to milestone"""
    print("⚡ Example 3: Force Advance to Milestone")
    print("=" * 50)

    orchestrator = MilestoneWorkflowOrchestrator()

    # Force advance to integration milestone
    result = await orchestrator.advance_to_milestone(
        "integration", force=True, task_ids=["lightrag-789"]
    )

    print(f"Force advanced to {result.milestone_id}")
    print(f"Result: {'PASSED' if result.passed else 'FAILED'}")
    print()


async def example_rollback():
    """Example: Rollback a milestone"""
    print("🔄 Example 4: Rollback Milestone")
    print("=" * 50)

    orchestrator = MilestoneWorkflowOrchestrator()

    # Reset integration milestone
    await orchestrator.reset_milestone(
        "integration", reason="Performance regression detected", user_id="developer-1"
    )

    print("Rolled back integration milestone")
    print()


async def example_validation_history():
    """Example: Get validation history"""
    print("📜 Example 5: Validation History")
    print("=" * 50)

    orchestrator = MilestoneWorkflowOrchestrator()

    history = orchestrator.get_validation_history(limit=5)

    if not history:
        print("No validation history found")
    else:
        print("Recent validations:")
        for entry in history:
            status = "✅ PASSED" if entry["passed"] else "❌ FAILED"
            print(f"  {status} {entry['milestone_id']} - {entry['timestamp']}")
            print(f"    Duration: {entry['duration_seconds']:.1f}s")

    print()


async def example_tdd_integration():
    """Example: Integration with existing TDD gates"""
    print("🧪 Example 6: TDD Gate Integration")
    print("=" * 50)

    validator = MilestoneValidator()

    # Get milestone details
    development_milestone = validator.get_milestone("development")
    if development_milestone:
        print(f"Milestone: {development_milestone.name}")
        print(f"Description: {development_milestone.description}")
        print(f"Validation steps: {', '.join(development_milestone.validation_steps)}")
        print(
            f"Blockers: {len(development_milestone.blockers)} blocking issues defined"
        )
        print(
            f"Success criteria: {len(development_milestone.success_criteria.__dict__)} criteria"
        )

    print()


async def example_milestone_listing():
    """Example: List all available milestones"""
    print("📋 Example 7: List All Milestones")
    print("=" * 50)

    validator = MilestoneValidator()
    milestones = validator.list_milestones()

    print("Available milestones:")
    for milestone in milestones:
        required = (
            " (required)" if milestone.required_for_progression else " (optional)"
        )
        deps = (
            f" [deps: {', '.join(milestone.dependencies)}]"
            if milestone.dependencies
            else ""
        )
        print(f"  {milestone.order}. {milestone.id}{required}{deps}")
        print(f"     {milestone.name}")
        print(f"     {milestone.description}")

    print()


async def main():
    """Run all examples"""
    print("🚀 Incremental Validation System Examples")
    print("=" * 60)
    print()

    try:
        await example_basic_validation()
        await example_workflow_status()
        await example_force_advance()
        await example_rollback()
        await example_validation_history()
        await example_tdd_integration()
        await example_milestone_listing()

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
