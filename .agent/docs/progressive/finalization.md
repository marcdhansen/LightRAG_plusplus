# Finalization (Progressive Documentation)

**Context**: Completing work session
**Workflow**: Review/Completion
**User Level**: {{USER_LEVEL}}
**Detail Level**: {{DETAIL_LEVEL}}

## Essential Steps

### Step 1: Final Validation
**Description**: Comprehensive quality and compliance checks
**Command**: `./scripts/sop_compliance_validator.py --critical-only`
**Critical**: Yes

### Step 2: Sync Changes
**Description**: Push all committed changes to remote repository
**Command**: `git push`
**Critical**: Yes

### Step 3: Session Cleanup
**Description**: Release resources and clean up session locks
**Command**: `./scripts/release_resources.sh`
**Critical**: No

## Important Notes

- Finalization is MANDATORY before ending any work session
- Work is NOT complete until `git push` succeeds
- All critical checks must pass for successful Finalization
- The system adapts checks based on your work patterns

## Common Scenarios

### Standard Completion
- Full validation and cleanup process
- Documentation integrity checks
- Performance metrics collection
- Session learnings recorded

### Emergency Finalization
- Critical checks only
- Minimal cleanup
- Post-emergency analysis scheduled
- Full cleanup on next session

### Quick Finalization
- Essential validations only
- Fast cleanup process
- Background optimization tasks
- Learnings still collected

## User Level Customization

### New Users
Complete process with guidance:
- Read all validation messages carefully
- Don't bypass checks without understanding why
- Review session summary before completion
- Ask for help if checks fail repeatedly

### Intermediate Users
Balance thoroughness with efficiency:
- Use fast mode for routine completions
- Pay attention to new failure patterns
- Review session metrics periodically
- Provide feedback on process improvements

### Advanced Users
Optimize for your workflow:
- Customize validation thresholds
- Use emergency mode appropriately
- Monitor system performance impact
- Contribute to process evolution

### Expert Users
Lead system improvements:
- Identify patterns in validation failures
- Suggest optimizations to reduce friction
- Help refine critical vs. optional checks
- Mentor others in Finalization best practices

## Troubleshooting

**Finalization Blocked by Critical Issues**
- Fix the specific issues mentioned
- Use `/rtb --override` only in emergencies
- Document why override was necessary
- Address issues in next session

**Git Push Fails**
- Check network connectivity
- Resolve merge conflicts locally
- Force push only as last resort
- Verify remote repository access

**Resource Cleanup Issues**
- Check for locked files or processes
- Use `--force` flag for stubborn locks
- Manual cleanup if script fails
- Report persistent issues for system improvement

## Quality Gates

The system enforces these quality gates:

### Critical (Cannot Bypass)
- Uncommitted changes must be handled
- Git status must be clean or justified
- Session locks must be released
- Critical test suites must pass

### Important (Can Override with Justification)
- Documentation integrity
- Code quality metrics
- Performance benchmarks
- Security scans

### Optional (Adaptive Based on Patterns)
- Style consistency checks
- Documentation completeness
- Test coverage metrics
- Build optimization

## Session Learnings

Every Finalization session contributes to system learning:
- Success patterns are reinforced
- Failure points trigger process evolution
- User preferences are recorded
- Performance metrics optimize future sessions

The adaptive SOP engine uses this data to:
- Adjust check frequencies
- Optimize workflow steps
- Personalize user experience
- Evolve SOPs continuously
