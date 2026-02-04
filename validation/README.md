# Incremental Validation System

The Incremental Validation System (IVS) provides milestone-based validation with automated quality gates, statistical significance testing, and rollback-safe deployment procedures for LightRAG.

## Overview

IVS validates changes incrementally through predefined milestones before allowing progression to production. It integrates with LightRAG's existing TDD gates, beads task management, git workflow, and A/B testing infrastructure.

## Milestones

The system uses a 5-phase milestone approach:

1. **Development Complete** - Code implementation and unit testing
2. **Integration Testing** - System integration validation  
3. **A/B Testing Validation** - Statistical significance testing
4. **Production Readiness** - Rollback capability verification
5. **Production Deployment** - Gradual traffic routing

## Installation

### Prerequisites

- Python 3.11+
- LightRAG project dependencies
- Access to beads database
- TDD gate configuration

### Setup

1. Install validation dependencies:
```bash
pip install -r requirements-validation.txt
```

2. Configure milestone settings:
```bash
# Edit milestone configuration
vim .agent/config/validation/milestone_config.yaml
```

3. Initialize the validation system:
```bash
python validation/scripts/example_usage.py
```

## Usage

### Command Line Interface

#### Validate a milestone:
```bash
python validation/cli.py validate development --task-ids lightrag-123 lightrag-456
```

#### Check workflow status:
```bash
python validation/cli.py status
```

#### Force advance (bypass prerequisites):
```bash
python validation/cli.py validate integration --force
```

#### Rollback a milestone:
```bash
python validation/cli.py rollback integration --reason "Performance regression"
```

#### List all milestones:
```bash
python validation/cli.py list-milestones
```

#### View validation history:
```bash
python validation/cli.py history --limit 10
```

### Programmatic Usage

```python
from validation.workflow_orchestrator import MilestoneWorkflowOrchestrator
from validation.milestone_validator import MilestoneValidator

# Initialize orchestrator
orchestrator = MilestoneWorkflowOrchestrator()

# Validate milestone
result = await orchestrator.advance_to_milestone(
    "development", 
    task_ids=["lightrag-123"]
)

if result.passed:
    print("Milestone validation passed!")
else:
    print(f"Validation failed: {result.blocking_issues}")
```

## Configuration

### Milestone Configuration

Edit `.agent/config/validation/milestone_config.yaml`:

```yaml
milestones:
  development:
    order: 1
    name: "Development Complete"
    description: "Code implementation and unit testing complete"
    success_criteria:
      coverage_threshold: 80
      unit_tests_passed: true
      tdd_gate_passed: true
    validation_steps:
      - tdd_gate_validation
      - unit_test_execution
      - code_quality_check
    blockers:
      - "TDD gate failure"
      - "Coverage below threshold"
```

### Success Criteria

Each milestone can define custom success criteria:

- `coverage_threshold`: Minimum test coverage percentage
- `unit_tests_passed`: All unit tests must pass
- `integration_tests_passed`: Integration tests must pass
- `ab_test_significance`: Statistical significance threshold (p-value)
- `rollback_test_passed`: Rollback procedure must work
- `load_test_passed`: Load tests must meet requirements

### Blocking Behavior

Configure automatic blocking when criteria fail:

```yaml
blocking_config:
  auto_block_on_failure: true
  notification_channels: [slack, email]
  emergency_bypass:
    allowed: true
    requires_approval: true
    max_bypasses_per_day: 2
```

## Integration Points

### TDD Gates

IVS integrates with the existing TDD gate system:

- Uses `.agent/scripts/tdd_gate_validator.py`
- Respects `.agent/config/tdd_config.yaml`
- Adapts thresholds based on milestone requirements

### Beads Task Management

Automatic integration with beads:

- Links validation results to task status
- Creates milestone-specific tasks
- Tracks dependencies between milestones
- Updates task status based on validation results

### A/B Testing

Statistical validation through A/B testing:

- Integrates with `ab_testing/production_ab_framework.py`
- Uses `ab_testing/statistical_analysis.py` for significance testing
- Supports multiple statistical test types
- Automated decision making based on results

### Git Workflow

Git integration for branch protection:

- Creates protected milestone branches
- Enforces milestone gates on PRs
- Tags successful milestone completions
- Maintains linear history requirements

## CI/CD Integration

### GitHub Actions

The system includes a GitHub Actions workflow (`.github/workflows/milestone_validation.yml`) that:

- Detects milestones from branch names
- Runs appropriate validation steps
- Blocks PRs when validation fails
- Updates beads task status
- Posts validation results as PR comments

### Workflow Triggers

```yaml
on:
  push:
    branches: [milestone-*, feature/*]
  pull_request:
    branches: [main, dev]
  workflow_dispatch:
    inputs:
      milestone:
        description: 'Milestone to validate'
        required: true
```

## Monitoring and Alerting

### Validation Metrics

The system tracks:

- Validation success rates
- Time spent in each milestone
- Common blocking issues
- Rollback frequency
- Performance trends

### Alerting

Configure notifications for:

- Validation failures
- Performance regressions
- Security vulnerabilities
- Resource exhaustion

### Dashboards

Built-in dashboards show:

- Milestone progress overview
- Validation metrics history
- System health status
- Performance trends

## Security

### Access Control

- Role-based access control
- Approval requirements for production
- Audit trail for all changes
- Emergency bypass logging

### Secrets Management

- Encrypted configuration
- Secret rotation policies
- Access audit logging
- Secure credential storage

## Troubleshooting

### Common Issues

#### Validation timeouts
```bash
# Increase timeout in configuration
global_settings:
  validation_timeout: 7200  # 2 hours
```

#### TDD gate failures
```bash
# Check TDD gate configuration
python .agent/scripts/tdd_gate_validator.py --verbose
```

#### Beads integration issues
```bash
# Check beads database status
bd status
bd sync
```

### Debug Mode

Enable debug logging:

```bash
python validation/cli.py validate development --verbose --debug
```

### Emergency Procedures

#### Emergency bypass
```bash
python validation/cli.py validate production --force --reason "Emergency fix"
```

#### Manual rollback
```bash
python validation/cli.py rollback production --reason "Critical bug" --user-id "admin"
```

## Development

### Running Tests

```bash
# Run validation system tests
pytest validation/tests/ -v

# Run with coverage
pytest validation/tests/ --cov=validation --cov-report=html
```

### Adding New Validation Steps

1. Define step in milestone configuration
2. Implement step in `milestone_validator.py`
3. Add criteria evaluation logic
4. Write tests for the new step

### Custom Milestones

Create custom milestones by adding to configuration:

```yaml
milestones:
  custom_feature:
    order: 6
    name: "Custom Feature Validation"
    description: "Custom validation for specific features"
    success_criteria:
      custom_test_passed: true
    validation_steps:
      - custom_validation_step
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the validation system on your changes
6. Submit a pull request

## License

This validation system is part of the LightRAG project and follows the same licensing terms.

## Support

For questions or issues:

1. Check the troubleshooting section
2. Review the configuration documentation
3. Check existing GitHub issues
4. Create a new issue with detailed information

## Roadmap

Future enhancements planned:

- Distributed validation across multiple agents
- Advanced machine learning for criteria evaluation
- Enhanced visualization and reporting
- Integration with additional monitoring systems
- Mobile app for milestone tracking
