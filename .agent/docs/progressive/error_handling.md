# Error Handling (Progressive Documentation)

**Context**: Troubleshooting errors and failures
**Workflow**: Error Recovery
**User Level**: {{USER_LEVEL}}
**Detail Level**: {{DETAIL_LEVEL}}

## Immediate Response Steps

### Step 1: Error Analysis
**Description**: Analyze the error to determine category and severity
**Command**: `./scripts/intelligent_preflight_analyzer.sh --analyze-error "$ERROR_MSG"`
**Critical**: Yes

### Step 2: Stabilize Session
**Description**: Stabilize current state to prevent further issues
**Command**: `./scripts/simplified_execution_coordinator.sh --action emergency`
**Critical**: Yes

### Step 3: Root Cause Investigation
**Description**: Investigate root cause based on error patterns
**Command**: `./scripts/adaptive_sop_engine.sh --action analyze --feedback error_log.json`
**Critical**: No

## Error Categories

### Critical System Errors
- Git repository corruption
- Disk space exhaustion
- Permission denied errors
- Process termination failures

**Immediate Actions**:
1. Stop all work activities
2. Preserve current state (git stash if possible)
3. Use emergency recovery mode
4. Document what led to the error

### Workflow Process Errors
- TDD gate failures
- SOP validation blocks
- Resource allocation failures
- Session lock conflicts

**Recovery Steps**:
1. Identify the specific failed check
2. Check error messages for guidance
3. Fix the underlying issue
4. Retry the failed step manually

### Performance and Timeout Errors
- Script timeouts
- Resource exhaustion
- Network connectivity issues
- System overload

**Resolution Strategies**:
1. Check system resources
2. Use fast mode to reduce load
3. Run problematic steps individually
4. Increase timeout limits if appropriate

## User Level Specific Guidance

### New Users
Systematic error resolution:
- Don't panic - errors are normal learning experiences
- Read error messages completely and carefully
- Use the error analysis script for guidance
- Ask for help if stuck after basic troubleshooting
- Document errors you encounter for future reference

### Intermediate Users
Efficient error resolution:
- Recognize common error patterns quickly
- Use appropriate recovery modes based on error type
- Know when to bypass vs. fix issues
- Maintain your own error resolution notes
- Share successful solutions with the community

### Advanced Users
Advanced troubleshooting:
- Diagnose complex or systemic issues
- Use logs and debugging tools effectively
- Identify patterns in recurring errors
- Contribute fixes to the system
- Help improve error messages and guidance

### Expert Users
System improvement:
- Analyze error patterns across the user base
- Propose system-level improvements
- Develop better error prevention mechanisms
- Create advanced debugging tools
- Mentor others in complex error resolution

## Error Prevention Strategies

### Proactive Measures
- Regular system maintenance
- Monitor resource usage
- Keep dependencies updated
- Use appropriate session modes
- Learn from others' experiences

### System Adaptations
The adaptive system learns from errors:
- Common failure points become more robust
- Error patterns trigger process improvements
- User feedback refines error messages
- Success patterns are reinforced

## Emergency Procedures

### When to Use Emergency Mode
- Critical system failures
- Time-sensitive urgent issues
- Multiple cascading failures
- Unknown error types

### Emergency Mode Process
1. Activate emergency coordinator
2. Perform only critical checks
3. Stabilize current state
4. Document emergency actions
5. Schedule full recovery session

### Post-Emergency Recovery
1. Analyze emergency trigger
2. Address root causes
3. Update error handling procedures
4. Share learnings with team
5. Improve prevention measures

## Feedback Integration

Every error should contribute to system improvement:
```bash
# Submit error feedback for learning
./scripts/adaptive_sop_engine.sh --action feedback --feedback error_report.json
```

### Feedback Template
```json
{
  "error_type": "category",
  "error_message": "specific message",
  "context": "what you were doing",
  "resolution": "how you fixed it",
  "prevention": "how to prevent it",
  "suggestions": "system improvements"
}
```

## Learning Resources

### Built-in Help
- Use `--help` flags on all scripts
- Check progressive documentation for your level
- Review session history for patterns
- Use analysis tools for insights

### Community Knowledge
- Check shared error resolution patterns
- Contribute your successful solutions
- Learn from others' experiences
- Participate in system improvements

## Continuous Improvement

The error handling system evolves continuously:
- Error patterns trigger automatic adaptations
- User feedback refines procedures
- Success rates measure effectiveness
- Process friction points are identified and addressed

Your experience with errors helps make the system more robust and user-friendly for everyone.
