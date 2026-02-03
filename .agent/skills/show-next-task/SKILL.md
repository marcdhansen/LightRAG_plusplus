---
name: show-next-task
description: Shows what to work on next in the LightRAG project by running beads ready and providing intelligent recommendations
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Show Next Task Skill

The `show-next-task` skill provides intelligent guidance on what to work on next in the LightRAG project. It answers the question "What should we work on next?" with actionable recommendations.

## Usage

```bash
/show-next-task
```

## Purpose

This skill performs comprehensive task analysis:
1. Runs `bd ready` to display all available tasks
2. Analyzes the task priority landscape (P0, P1, P2)
3. Provides intelligent recommendations based on project impact
4. Offers concrete next steps to get started immediately

## Implementation

The skill executes:

```bash
./.agent/skills/show-next-task/scripts/next.sh
```

## Workflow Analysis

The script performs intelligent analysis:

1. **Task Discovery**: Captures full `bd ready` output
2. **Priority Classification**: Categorizes tasks by priority level
3. **Impact Assessment**: Provides recommendations based on:
   - **P0 Tasks**: Critical blockers requiring immediate attention
   - **P1 Tasks**: High-impact work with clear deliverables  
   - **P2 Tasks**: Strategic work advancing project goals
4. **Action Planning**: Suggests specific commands to get started

## Response Format

The skill delivers:

1. **Complete Task List**: Full `bd ready` output for context
2. **Priority Analysis**: Task count breakdown (P0: X, P1: Y, P2: Z)
3. **Intelligent Recommendations**: Priority-based guidance with reasoning
4. **Concrete Next Steps**: Specific `bd` commands and git workflow steps
5. **Project Context Links**: Roadmap, docs, and session status resources

## Decision Logic

**P0 Available**: Immediate attention required
- Recommendation: Start with P0 tasks first
- Reasoning: These are blocking project progress

**P1 Only**: High-priority work
- Recommendation: Tackle P1 tasks for maximum impact
- Reasoning: High importance with clear deliverables

**P2 Only**: Strategic development
- Recommendation: Work on P2 tasks systematically
- Reasoning: Advance project goals methodically

## Integration

This skill integrates with:
- **Beads Task Management**: `bd ready` command for task discovery
- **LightRAG Protocols**: Project priorities and workflow standards
- **Agent Coordination**: Session status and multi-agent workflows
- **Git Operations**: Branch creation and task assignment workflows

## Example Output

```
🎯 What should we work on next in the LightRAG project?
=========================================================
📋 Current Available Tasks: [full bd ready output]
🤔 Agent's Analysis & Recommendations:
📊 Task Priority Breakdown: P0: 1, P1: 2, P2: 7
🚨 IMMEDIATE ATTENTION (P0 Tasks):
⚡ lightrag-ggt: Make SOP evaluation mandatory in RTB process
💡 Recommendation: Start with the P0 task(s) - they are blocking project progress.
🚀 Next Steps: • Start top task: `bd start lightrag-ggt`
```

## Error Handling

The skill gracefully handles:
- Beads daemon not running
- No ready tasks available
- Command execution failures
- Network connectivity issues