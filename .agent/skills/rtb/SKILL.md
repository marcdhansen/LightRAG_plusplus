---
name: rtb
description: User shortcut to ask the agent to perform Return To Base (RTB) workflow
disable-model-invocation: false
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Return To Base (RTB) Shortcut Skill

The `rtb` skill is a user-friendly shortcut for asking the agent to perform a Return To Base workflow.

## Usage

```bash
/rtb
```

## Purpose

When you use `/rtb`, it's a shortcut way of asking:
> "Please perform Return To Base checks and complete the session workflow"

This skill interprets your request and prompts the agent to execute the actual RTB workflow using the `/return-to-base` skill.

## Agent Response

When the agent receives this `/rtb` request, it should:

1. **Acknowledge the RTB request**
2. **Execute the `/return-to-base` skill** to perform the actual workflow
3. **Report the results** of the RTB process

## Example Interaction

**User**: `/rtb`

**Agent**:
```
I'll perform a Return To Base workflow for you. Let me run the RTB process...

[Agent executes /return-to-base skill]

✅ RTB workflow completed successfully!
- All changes committed and pushed
- Quality gates passed
- Session cleanup complete
```

## Integration

This shortcut skill works with:
- `/return-to-base` - The actual RTB execution skill
- LightRAG session protocols
- Git workflow automation
- Multi-agent coordination

## Benefits

- **Quick access**: Simple `/rtb` command instead of typing the full request
- **Clear intent**: Unambiguous way to request session completion
- **Agent coordination**: Lets the agent handle the actual RTB execution
- **User-friendly**: Natural way to end a work session
