# Pre-Flight Check (Progressive Documentation)

**Context**: Before starting work  
**Workflow**: Planning/Preparation  
**User Level**: {{USER_LEVEL}}  
**Detail Level**: {{DETAIL_LEVEL}}

## Essential Steps

### Step 1: Intelligent Analysis
**Description**: Run smart preflight analysis based on context and history
**Command**: `./scripts/intelligent_preflight_analyzer.sh {{SESSION_TYPE}}`
**Critical**: Yes

### Step 2: Session Lock
**Description**: Acquire session lock to prevent conflicts
**Command**: `./scripts/enhanced_session_locks.sh --acquire`
**Critical**: Yes

### Step 3: Resource Allocation
**Description**: Allocate safe resources for the planned work
**Command**: `./scripts/allocate_safe_resources.sh`
**Critical**: No

## Important Notes

- The intelligent analyzer adapts checks based on your session type and history
- Emergency sessions skip most checks except critical ones
- Fast mode skips optional optimization steps
- Learning mode enables adaptation based on your patterns

## Common Scenarios

### New User (First Time)
- Full preflight analysis with all checks
- Detailed explanations for each step
- Learning mode enabled by default

### Emergency Session
- Only critical checks run
- Minimal overhead for urgent situations
- Post-emergency analysis scheduled

### Quick Session
- Essential checks only
- Optimized for speed and efficiency
- Fast mode recommended

## Troubleshooting

**Issue**: Preflight check fails
- Check the specific error message
- Run individual checks manually for debugging
- Consider emergency mode if urgent

**Issue**: Resource allocation fails
- Check system resources (disk space, memory)
- Close other applications and retry
- Use maintenance mode for system cleanup

## User Level Customization

### New Users
Focus on understanding why each check matters:
- Read descriptions carefully
- Use `--verbose` flag for detailed output
- Don't skip optional checks initially

### Intermediate Users
Balance efficiency with thoroughness:
- Use fast mode for routine tasks
- Keep optional checks for important work
- Monitor success rates and patterns

### Advanced Users
Optimize for your specific workflow:
- Customize check frequencies via config
- Use session-specific modes
- Contribute feedback for system improvement

### Expert Users
Teach and improve the system:
- Provide detailed feedback on failures
- Suggest optimizations based on patterns
- Help evolve SOPs based on experience