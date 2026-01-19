# Agent Memory - LightRAG Project

## Priority System
- **p0**: Highest priority - must be done first
- **p1**: Next-highest priority - do after p0 items complete
- **p2**: Lower priority - nice to have

## User Intent & Decisions
- **Core Focus**: Working system (BCBC PDF processing, graph creation, queries) > optimization
- **ACE Framework**: Start with minimal prototype
- **Langfuse**: Self-hosted (no cloud credentials needed)
- **MCP Integration**: Both client AND server modes; use cases TBD
- **Beads Sync**: Keep planning docs and beads issues in sync at all times

## ACE Framework Summary
The **Agentic Context Engineering (ACE)** framework optimizes LLM performance by dynamically evolving context (input instructions, memory, strategies) rather than modifying model weights.

### Core Architecture (3 Modular Roles)
1. **Generator**: Solves queries by producing a reasoning Trajectory using the existing Context Playbook
2. **Reflector**: Critiques the Generator's trajectory and execution results to distill concrete Insights (lessons from successes and errors)
3. **Curator**: Synthesizes Reflector's insights into compact Delta Context Items, merged into the Playbook

### Key Innovations
- **Incremental Delta Updates**: Small, localized, structured edits instead of full-context rewriting
- **Execution Feedback-Based Adaptation**: Self-improvement via natural execution feedback (code results, validation) rather than expensive ground-truth labels
- **Grow-and-Refine Principle**: Balance steady context expansion (appending insights) with redundancy control (de-duplication, updating existing bullets)

### Problems ACE Solves
- **Brevity bias**: Prioritizing short, generic prompts over detailed domain knowledge
- **Context collapse**: Iterative rewriting that erodes detailed knowledge over time

## MCP Integration
LightRAG MCP integration should support BOTH:
1. **MCP Server**: Expose LightRAG capabilities to other agents
2. **MCP Client**: Allow LightRAG to consume external MCP resources
