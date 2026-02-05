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

from validation.extraction_validator import ExtractionValidator
from validation.gold_standard_manager import GoldStandardManager
from validation.milestone_validator import MilestoneValidator
from validation.models import ValidationResult

# Alias to avoid conflicts
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


@cli.group()
@click.option(
    "--tolerance",
    default=0.8,
    type=float,
    help="Fuzzy matching tolerance for validation (0.0-1.0)",
)
@click.pass_context
def extract(_ctx, tolerance):
    """Extraction validation commands"""
    pass


@extract.command()
@click.argument("input_text")
@click.option(
    "--gold-standard",
    required=True,
    help="Gold standard case ID to validate against",
)
@click.option(
    "--tolerance",
    type=float,
    help="Override default tolerance for this validation",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def validate_extraction(_ctx, input_text, gold_standard, tolerance, output):
    """Validate extraction against gold standard case"""

    async def run_validation():
        try:
            # Initialize validator and manager
            validator = ExtractionValidator(
                tolerance or _ctx.parent.params["tolerance"]
            )
            manager = GoldStandardManager()

            # Load gold standard case
            case = manager.get_case(gold_standard)
            if not case:
                click.echo(
                    f"❌ Gold standard case not found: {gold_standard}", err=True
                )
                sys.exit(1)

            click.echo(f"🔍 Validating extraction against: {case.name}")
            click.echo(
                f"📝 Input: {input_text[:100]}{'...' if len(input_text) > 100 else ''}"
            )

            # For now, create a mock extraction result
            # In a real implementation, this would call LightRAG extraction
            mock_extraction = {"entities": [], "relationships": []}

            # Run validation
            result = await validator.validate_against_gold_standard(
                mock_extraction, case.__dict__
            )

            # Output results
            if output == "json":
                output_data = {
                    "case_id": result.gold_case_id,
                    "passed": result.passed,
                    "overall_score": result.overall_score,
                    "entity_validation": {
                        "expected_count": result.entity_validation.expected_count,
                        "actual_count": result.entity_validation.actual_count,
                        "fuzzy_match_score": result.entity_validation.fuzzy_match_score,
                        "missing_entities": result.entity_validation.missing_entities,
                        "extra_entities": result.entity_validation.extra_entities,
                    },
                    "relationship_validation": {
                        "expected_count": result.relationship_validation.expected_count,
                        "actual_count": result.relationship_validation.actual_count,
                        "keyword_match_score": result.relationship_validation.keyword_match_score,
                        "missing_relationships": result.relationship_validation.missing_relationships,
                        "extra_relationships": result.relationship_validation.extra_relationships,
                    },
                    "structural_validation": {
                        "graph_connectivity": result.structural_validation.graph_connectivity,
                        "connected_components": result.structural_validation.connected_components,
                        "isolation_issues": result.structural_validation.isolation_issues,
                    },
                    "recommendations": result.recommendations,
                    "validation_duration_seconds": result.validation_duration_seconds,
                }
                click.echo(json.dumps(output_data, indent=2))
            else:
                output_extraction_validation_text(result)

            # Save result
            from validation.gold_standard_manager import ValidationResult

            validation_result = ValidationResult(
                case_id=result.gold_case_id,
                passed=result.passed,
                score=result.overall_score,
                entity_validation=result.entity_validation.__dict__,
                relationship_validation=result.relationship_validation.__dict__,
                structural_validation=result.structural_validation.__dict__,
                execution_time=result.validation_duration_seconds,
                timestamp=result.timestamp,
                recommendations=result.recommendations,
            )
            manager.save_validation_result(validation_result)

            # Exit with appropriate code
            sys.exit(0 if result.passed else 1)

        except Exception as e:
            click.echo(f"❌ Validation failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_validation())


@extract.command()
@click.argument("run1")
@click.argument("run2")
@click.option(
    "--tolerance",
    type=float,
    help="Override default tolerance for comparison",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def compare(_ctx, run1, run2, tolerance, output):
    """Compare two extraction results for regression"""

    async def run_comparison():
        try:
            validator = ExtractionValidator(
                tolerance or _ctx.parent.params["tolerance"]
            )

            click.echo("🔍 Comparing extraction results:")
            click.echo(f"   Run 1: {run1}")
            click.echo(f"   Run 2: {run2}")

            # Load extraction results from files (mock for now)
            # In real implementation, these would be JSON files with extraction results
            baseline_result = {"entities": [], "relationships": []}  # Mock
            current_result = {"entities": [], "relationships": []}  # Mock

            # Run comparison
            result = await validator.compare_extractions(
                baseline_result, current_result
            )

            # Output results
            if output == "json":
                output_data = {
                    "case_id": result.gold_case_id,
                    "passed": result.passed,
                    "overall_score": result.overall_score,
                    "entity_validation": {
                        "expected_count": result.entity_validation.expected_count,
                        "actual_count": result.entity_validation.actual_count,
                        "missing_entities": result.entity_validation.missing_entities,
                        "extra_entities": result.entity_validation.extra_entities,
                    },
                    "relationship_validation": {
                        "expected_count": result.relationship_validation.expected_count,
                        "actual_count": result.relationship_validation.actual_count,
                        "missing_relationships": result.relationship_validation.missing_relationships,
                        "extra_relationships": result.relationship_validation.extra_relationships,
                    },
                    "recommendations": result.recommendations,
                    "validation_duration_seconds": result.validation_duration_seconds,
                }
                click.echo(json.dumps(output_data, indent=2))
            else:
                output_extraction_validation_text(result)

            sys.exit(0 if result.passed else 1)

        except Exception as e:
            click.echo(f"❌ Comparison failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_comparison())


@extract.group()
def gold():
    """Gold standard test case management"""
    pass


@gold.command()
@click.option(
    "--tags",
    multiple=True,
    help="Filter by tags",
)
@click.option(
    "--difficulty",
    type=click.Choice(["easy", "medium", "hard"]),
    help="Filter by difficulty level",
)
@click.option(
    "--domain",
    help="Filter by domain",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of cases to show",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def list_cases(tags, difficulty, domain, limit, output):
    """List available gold standard cases"""

    try:
        manager = GoldStandardManager()
        cases = manager.list_cases(
            tags=list(tags) if tags else None,
            difficulty=difficulty,
            domain=domain,
            limit=limit,
        )

        if output == "json":
            cases_data = [
                {
                    "id": case.id,
                    "name": case.name,
                    "description": case.description,
                    "difficulty": case.difficulty,
                    "domain": case.domain,
                    "tags": case.tags,
                    "entity_count": len(case.expected_entities),
                    "relationship_count": len(case.expected_relationships),
                    "created_at": case.created_at.isoformat(),
                }
                for case in cases
            ]
            click.echo(json.dumps(cases_data, indent=2))
        else:
            if not cases:
                click.echo("📝 No gold standard cases found")
                return

            click.echo("🎯 Gold Standard Cases:")
            click.echo("-" * 60)

            for case in cases:
                click.echo(f"📋 {case.id}")
                click.echo(f"   Name: {case.name}")
                click.echo(f"   Description: {case.description}")
                click.echo(f"   Difficulty: {case.difficulty}")
                click.echo(f"   Domain: {case.domain}")
                click.echo(f"   Tags: {', '.join(case.tags) if case.tags else 'None'}")
                click.echo(f"   Entities: {len(case.expected_entities)}")
                click.echo(f"   Relationships: {len(case.expected_relationships)}")
                created_date = case.created_at
                if isinstance(created_date, str):
                    click.echo(f"   Created: {created_date[:10]}")
                else:
                    click.echo(f"   Created: {created_date.strftime('%Y-%m-%d')}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ Failed to list cases: {str(e)}", err=True)
        sys.exit(1)


@gold.command()
@click.option(
    "--name",
    required=True,
    help="Test case name",
)
@click.option(
    "--description",
    required=True,
    help="Test case description",
)
@click.option(
    "--text",
    required=True,
    help="Input text for extraction",
)
@click.option(
    "--entities",
    help="Expected entities (format: name:type,name:type)",
)
@click.option(
    "--relationships",
    help="Expected relationships (format: source->target:keywords)",
)
@click.option(
    "--tags",
    multiple=True,
    help="Tags for the test case",
)
@click.option(
    "--difficulty",
    type=click.Choice(["easy", "medium", "hard"]),
    default="medium",
    help="Difficulty level",
)
@click.option(
    "--domain",
    default="general",
    help="Domain category",
)
def add_case(
    name, description, text, entities, relationships, tags, difficulty, domain
):
    """Add a new gold standard test case"""

    try:
        manager = GoldStandardManager()

        # Parse entities
        expected_entities = []
        if entities:
            for entity_str in entities.split(","):
                parts = entity_str.strip().split(":")
                if len(parts) >= 2:
                    expected_entities.append(
                        {
                            "name": parts[0].strip(),
                            "type": parts[1].strip(),
                            "required": True,
                        }
                    )

        # Parse relationships
        expected_relationships = []
        if relationships:
            for rel_str in relationships.split(","):
                parts = rel_str.strip().split(":")
                if len(parts) >= 2:
                    rel_info = parts[1].strip()
                    arrow_parts = rel_info.split("->")
                    if len(arrow_parts) >= 2:
                        expected_relationships.append(
                            {
                                "source": arrow_parts[0].strip(),
                                "target": arrow_parts[1].strip(),
                                "keywords": parts[0].strip().split("|")
                                if "|" in parts[0]
                                else [parts[0].strip()],
                            }
                        )

        # Create case
        case = manager.create_case(
            name=name,
            description=description,
            text=text,
            expected_entities=expected_entities,
            expected_relationships=expected_relationships,
            tags=list(tags) if tags else ["structural"],
            difficulty=difficulty,
            domain=domain,
        )

        click.echo(f"✅ Created gold standard case: {case.id}")
        click.echo(f"   Name: {case.name}")
        click.echo(f"   Entities: {len(expected_entities)}")
        click.echo(f"   Relationships: {len(expected_relationships)}")

    except Exception as e:
        click.echo(f"❌ Failed to create case: {str(e)}", err=True)
        sys.exit(1)


@gold.command()
@click.argument("case_id")
def delete_case(case_id):
    """Delete a gold standard test case"""

    try:
        manager = GoldStandardManager()

        if manager.delete_case(case_id):
            click.echo(f"✅ Deleted gold standard case: {case_id}")
        else:
            click.echo(f"❌ Gold standard case not found: {case_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Failed to delete case: {str(e)}", err=True)
        sys.exit(1)


@gold.command()
def stats():
    """Show gold standard statistics"""

    try:
        manager = GoldStandardManager()
        stats = manager.get_statistics()

        click.echo("📊 Gold Standard Statistics:")
        click.echo("-" * 40)
        click.echo(f"Total Cases: {stats['total_cases']}")

        click.echo("\nBy Difficulty:")
        for difficulty, count in stats["by_difficulty"].items():
            click.echo(f"  {difficulty}: {count}")

        click.echo("\nBy Domain:")
        for domain, count in stats["by_domain"].items():
            click.echo(f"  {domain}: {count}")

        click.echo("\nBy Tags:")
        for tag, count in stats["by_tags"].items():
            click.echo(f"  {tag}: {count}")

        if stats["total_cases"] > 0:
            click.echo("\nAverages:")
            click.echo(f"  Entities per case: {stats['average_entities']:.1f}")
            click.echo(
                f"  Relationships per case: {stats['average_relationships']:.1f}"
            )

    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {str(e)}", err=True)
        sys.exit(1)


def output_extraction_validation_text(result) -> None:
    """Output extraction validation result in text format"""

    if result.passed:
        click.echo("✅ Extraction Validation PASSED")
    else:
        click.echo("❌ Extraction Validation FAILED")

    click.echo(f"📋 Case ID: {result.gold_case_id}")
    click.echo(f"⏱️  Duration: {result.validation_duration_seconds:.2f} seconds")
    click.echo(f"🕐 Timestamp: {result.timestamp}")
    click.echo(f"📊 Overall Score: {result.overall_score:.3f}")

    # Entity validation
    click.echo("\n🔹 Entity Validation:")
    click.echo(f"   Expected: {result.entity_validation.expected_count}")
    click.echo(f"   Actual: {result.entity_validation.actual_count}")
    click.echo(
        f"   Fuzzy Match Score: {result.entity_validation.fuzzy_match_score:.3f}"
    )
    click.echo(
        f"   Type Consistency: {result.entity_validation.type_consistency_score:.3f}"
    )

    if result.entity_validation.missing_entities:
        click.echo(
            f"   Missing Entities: {', '.join(result.entity_validation.missing_entities[:3])}"
        )
    if result.entity_validation.extra_entities:
        click.echo(
            f"   Extra Entities: {', '.join(result.entity_validation.extra_entities[:3])}"
        )

    # Relationship validation
    click.echo("\n🔗 Relationship Validation:")
    click.echo(f"   Expected: {result.relationship_validation.expected_count}")
    click.echo(f"   Actual: {result.relationship_validation.actual_count}")
    click.echo(
        f"   Keyword Match Score: {result.relationship_validation.keyword_match_score:.3f}"
    )

    if result.relationship_validation.missing_relationships:
        click.echo(
            f"   Missing Relationships: {', '.join(result.relationship_validation.missing_relationships[:2])}"
        )
    if result.relationship_validation.extra_relationships:
        click.echo(
            f"   Extra Relationships: {', '.join(result.relationship_validation.extra_relationships[:2])}"
        )

    # Structural validation
    click.echo("\n🏗️  Structural Validation:")
    click.echo(
        f"   Graph Connected: {'✅' if result.structural_validation.graph_connectivity else '❌'}"
    )
    click.echo(
        f"   Connected Components: {result.structural_validation.connected_components}"
    )
    click.echo(
        f"   Clustering Coefficient: {result.structural_validation.clustering_coefficient:.3f}"
    )

    if result.structural_validation.isolation_issues:
        click.echo(
            f"   Isolation Issues: {', '.join(result.structural_validation.isolation_issues[:2])}"
        )

    # Recommendations
    if result.recommendations:
        click.echo("\n💡 Recommendations:")
        for rec in result.recommendations:
            click.echo(f"   • {rec}")


if __name__ == "__main__":
    cli()
