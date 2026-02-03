---
name: next
description: Shortcut for asking the agent to show what to work on next in the LightRAG project.
disable-model-invocation: true
---

# Next Task Shortcut Skill

The `next` skill is a user-friendly shortcut for asking the agent to show what task to work on next in the LightRAG project.

## Usage

```bash
/next
```

## Purpose

When you use `/next`, it's a shortcut way of asking:
> "Please show me what to work on next in the LightRAG project"

This skill interprets your request and prompts the agent to execute the actual task discovery using the `/show-next-task` skill.

## Agent Response

When the agent receives this `/next` request, it should:

1. **Acknowledge the task discovery request**
2. **Execute the `/show-next-task` skill** to get intelligent recommendations
3. **Display the results** with analysis and concrete next steps

## Example Interaction

**User**: `/next`

**Agent**: 
```
I'll show you what to work on next in the LightRAG project...

[Agent executes /show-next-task skill]

🎯 What should we work on next in the LightRAG project?
=========================================================
📊 Task Priority Breakdown: P0: 1, P1: 2, P2: 7
🚨 IMMEDIATE ATTENTION (P0 Tasks):
⚡ lightrag-ggt: Make SOP evaluation mandatory in RTB process
💡 Recommendation: Start with the P0 task(s) - they are blocking project progress.
🚀 Next Steps: • Start top task: `bd start lightrag-ggt`
```

## Integration

This shortcut skill works with:
- `/show-next-task` - The actual task discovery execution skill
- Beads task management system
- LightRAG project protocols
- Agent session workflows

## Benefits

- **Quick access**: Simple `/next` command instead of typing the full request
- **Clear intent**: Unambiguous way to request task discovery
- **Agent coordination**: Lets the agent handle the intelligent analysis
- **User-friendly**: Natural way to start a work session