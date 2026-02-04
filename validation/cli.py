"""
Command Line Interface for Incremental Validation System
"""

import asyncio
import json
import sys
from pathlib import Path

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.milestone_validator import MilestoneValidator
from validation.models import ValidationResult
from validation.workflow_orchestrator import MilestoneWorkflowOrchestrator


@click.group()
@click.option(
    "--config",
    default=".agent/config/validation/milestone_config.yaml",
    help="Path to milestone configuration file",
)
@click.pass_context
def cli(ctx, config):
    """Incremental Validation System CLI"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.argument("milestone")
@click.option("--force", is_flag=True, help="Force validation despite blockers")
@click.option("--task-ids", multiple=True, help="Specific task IDs to validate")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def validate(_ctx, milestone, force, task_ids, output):
    """Validate milestone against success criteria"""

    async def run_validation():
        try:
            orchestrator = MilestoneWorkflowOrchestrator()

            click.echo(f"🔍 Validating milestone: {milestone}")
            if force:
                click.echo("⚠️  Force mode enabled - bypassing prerequisite checks")

            # Convert task_ids tuple to list
            task_list = list(task_ids) if task_ids else None

            # Run validation
            result = await orchestrator.advance_to_milestone(
                milestone, force=force, task_ids=task_list
            )

            # Output results
            if output == "json":
                output_json(result)
            else:
                output_text(result)

            # Exit with appropriate code
            sys.exit(0 if result.passed else 1)

        except Exception as e:
            click.echo(f"❌ Validation failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_validation())


@cli.command()
@click.argument("milestone", required=False)
@click.option("--dry-run", is_flag=True, help="Show what would be blocked")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def status(_ctx, milestone, dry_run, output):
    """Show milestone validation status and blockers"""

    try:
        orchestrator = MilestoneWorkflowOrchestrator()

        if milestone:
            # Status for specific milestone
            status_data = orchestrator.get_milestone_status(milestone)
            if output == "json":
                click.echo(json.dumps(status_data, indent=2))
            else:
                click.echo(f"📍 Milestone: {milestone}")
                if milestone in status_data:
                    data = status_data[milestone]
                    click.echo(f"   Name: {data['name']}")
                    click.echo(f"   Status: {data['status']}")
                    click.echo(f"   Order: {data['order']}")
                    click.echo(f"   Required: {data['required_for_progression']}")
                else:
                    click.echo(f"❌ Milestone not found: {milestone}")
        else:
            # Overall workflow status
            summary = orchestrator.get_workflow_summary()
            milestone_status = orchestrator.get_milestone_status()

            if output == "json":
                output_data = {"summary": summary, "milestones": milestone_status}
                click.echo(json.dumps(output_data, indent=2))
            else:
                output_workflow_status(summary, milestone_status, dry_run)

    except Exception as e:
        click.echo(f"❌ Status check failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("milestone")
@click.option("--reason", required=True, help="Rollback reason")
@click.option("--user-id", help="User ID triggering rollback")
@click.pass_context
def rollback(_ctx, milestone, reason, user_id):
    """Trigger manual rollback for milestone"""

    async def run_rollback():
        try:
            orchestrator = MilestoneWorkflowOrchestrator()

            click.echo(f"🔄 Rolling back milestone: {milestone}")
            click.echo(f"📝 Reason: {reason}")

            await orchestrator.reset_milestone(milestone, reason, user_id)

            click.echo("✅ Rollback completed successfully")

        except Exception as e:
            click.echo(f"❌ Rollback failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_rollback())


@cli.command()
@click.option("--limit", default=10, help="Number of recent validations to show")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def history(_ctx, limit, output):
    """Show validation history"""

    try:
        orchestrator = MilestoneWorkflowOrchestrator()
        history_data = orchestrator.get_validation_history(limit)

        if output == "json":
            click.echo(json.dumps(history_data, indent=2))
        else:
            if not history_data:
                click.echo("📝 No validation history found")
                return

            click.echo("📜 Recent Validation History:")
            click.echo("-" * 50)

            for entry in reversed(history_data):
                status = "✅ PASSED" if entry["passed"] else "❌ FAILED"
                click.echo(f"{status} {entry['milestone_id']} - {entry['timestamp']}")
                click.echo(f"   Duration: {entry['duration_seconds']:.1f}s")
                if entry["blocking_issues_count"] > 0:
                    click.echo(f"   Blocking Issues: {entry['blocking_issues_count']}")
                if entry["recommendations_count"] > 0:
                    click.echo(f"   Recommendations: {entry['recommendations_count']}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ History retrieval failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def list_milestones(_ctx):
    """List all available milestones"""

    try:
        validator = MilestoneValidator()
        milestones = validator.list_milestones()

        click.echo("🎯 Available Milestones:")
        click.echo("-" * 40)

        for milestone in milestones:
            status = "📋" if milestone.required_for_progression else "🔹"
            click.echo(f"{status} {milestone.order}. {milestone.id}")
            click.echo(f"   {milestone.name}")
            click.echo(f"   {milestone.description}")
            if milestone.dependencies:
                click.echo(f"   Dependencies: {', '.join(milestone.dependencies)}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Failed to list milestones: {str(e)}", err=True)
        sys.exit(1)


def output_text(result: ValidationResult) -> None:
    """Output validation result in text format"""

    if result.passed:
        click.echo("✅ Validation PASSED")
    else:
        click.echo("❌ Validation FAILED")

    click.echo(f"📍 Milestone: {result.milestone_id}")
    click.echo(f"⏱️  Duration: {result.validation_duration_seconds:.1f} seconds")
    click.echo(f"🕐 Timestamp: {result.timestamp}")

    if result.task_ids:
        click.echo(f"📋 Task IDs: {', '.join(result.task_ids)}")

    # Show criteria results
    click.echo("\n📊 Criteria Results:")
    for criteria, passed in result.criteria_results.items():
        status = "✅" if passed else "❌"
        click.echo(f"  {status} {criteria}")

    # Show blocking issues
    if result.blocking_issues:
        click.echo("\n🚫 Blocking Issues:")
        for issue in result.blocking_issues:
            click.echo(f"  • {issue}")

    # Show recommendations
    if result.recommendations:
        click.echo("\n💡 Recommendations:")
        for rec in result.recommendations:
            click.echo(f"  • {rec}")

    # Show step results
    click.echo("\n🔧 Validation Steps:")
    for step in result.step_results:
        status_icon = {
            "passed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "running": "🔄",
            "pending": "⏳",
        }.get(step.status.value, "❓")

        click.echo(f"  {status_icon} {step.name}")
        if step.duration_seconds:
            click.echo(f"     Duration: {step.duration_seconds:.1f}s")
        if step.error_message:
            click.echo(f"     Error: {step.error_message}")


def output_json(result: ValidationResult) -> None:
    """Output validation result in JSON format"""

    result_data = {
        "milestone_id": result.milestone_id,
        "passed": result.passed,
        "timestamp": result.timestamp.isoformat(),
        "validation_duration_seconds": result.validation_duration_seconds,
        "task_ids": result.task_ids,
        "criteria_results": result.criteria_results,
        "blocking_issues": result.blocking_issues,
        "recommendations": result.recommendations,
        "step_results": [
            {
                "name": step.name,
                "status": step.status.value,
                "duration_seconds": step.duration_seconds,
                "error_message": step.error_message,
                "metrics": step.metrics,
            }
            for step in result.step_results
        ],
    }

    click.echo(json.dumps(result_data, indent=2))


def output_workflow_status(
    summary: dict, milestone_status: dict, dry_run: bool
) -> None:
    """Output workflow status in text format"""

    click.echo("🎯 Workflow Status Summary")
    click.echo("=" * 40)
    click.echo(f"📊 Progress: {summary['progress_percentage']:.1f}%")
    click.echo(f"📍 Current: {summary['current_milestone']}")
    click.echo(
        f"✅ Completed: {summary['completed_milestones']}/{summary['total_milestones']}"
    )

    if summary["blocked_milestones"] > 0:
        click.echo(f"🚫 Blocked: {summary['blocked_milestones']}")

    click.echo(f"🕐 Last Updated: {summary['last_updated']}")

    click.echo("\n📋 Milestone Details:")
    for _milestone_id, data in milestone_status.items():
        status_icons = {
            "not_started": "⏳",
            "in_progress": "🔄",
            "validating": "🔍",
            "passed": "✅",
            "failed": "❌",
            "blocked": "🚫",
        }

        icon = status_icons.get(data["status"], "❓")
        required = " (required)" if data["required_for_progression"] else ""

        click.echo(f"  {icon} {data['order']}. {data['name']}{required}")
        click.echo(f"     Status: {data['status']}")
        click.echo(f"     {data['description']}")

    if dry_run:
        click.echo("\n⚠️  Dry run mode - no actual validation performed")


if __name__ == "__main__":
    cli()
