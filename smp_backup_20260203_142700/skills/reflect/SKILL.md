---
name: reflect
description: Analyzes the current conversation history to extract lessons, user preferences, and corrections, then updates relevant SKILL.md files to prevent repeating mistakes.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Reflect & Improve

## Goal

Implement the "correct once, never again" philosophy by analyzing the current session for "memories"—specific corrections, coding preferences, or logic improvements—and permanently documenting them into the relevant `SKILL.md` files. This ensures that every mission contributes to the system's collective intelligence.

## 🛠️ Tools & Scripts

### 1. `enhanced_reflect_system.py` (Primary System)

Comprehensive reflection system integrating PFC/RTB diagnostics with conversation analysis.

**Usage**:

```bash
# Full comprehensive analysis (recommended)
python scripts/enhanced_reflect_system.py --comprehensive conversation.log

# Flight diagnostics only
python scripts/enhanced_reflect_system.py --flight-diagnostics

# Generate Post-Mission Debrief
python scripts/enhanced_reflect_system.py --debrief debrief.md

# Show pending learnings
python scripts/enhanced_reflect_system.py --pending-learnings
```

### 2. `reflect_assistant.py` (Utility)

Helper script for basic memory discovery and rule auditing.

**Usage**:

```bash
# Discover potential memories from a conversation log
python scripts/reflect_assistant.py discover conversation.log

# Audit a proposed rule for conflicts
python scripts/reflect_assistant.py audit "Always use YAML" .
```

### 3. `skill_version_manager.py` (Version Management)

Tag-based versioning and rollback system for skill files.

**Usage**:

```bash
# Create a learning tag
python scripts/skill_version_manager.py tag --skill SkillName --description "Learning description"

# List all versions
python scripts/skill_version_manager.py list

# Rollback to previous version of skill
python scripts/skill_version_manager.py rollback-previous --skill Reflect
```

### 4. `proactive_improvements.py` (Proactive Suggestions)

Analyzes patterns across learnings, flight diagnostics, and code to suggest proactive improvements.

**Usage**:

```bash
# Full pattern analysis and suggestion generation
python scripts/proactive_improvements.py analyze

# Show top suggestions
python scripts/proactive_improvements.py suggest
```

## Workflow

### 1. Pre-Reflection Diagnostic

Before performing reflection, run the **PFC/RTB Analysis**:

- Run `python scripts/enhanced_reflect_system.py --flight-diagnostics`.
- Identify recurring failures (e.g., `beads sync` issues, `lint` errors).
- Document these as "Process Improvement" learnings.

### 2. Session Analysis

**Automated**: Use `enhanced_reflect_system.py --comprehensive conversation.log`.

**Manual**: Scan the conversation history to identify:

- **Corrections**: Direct feedback like "No," "Wrong," or "Actually, use Y."
- **Preferences**: Coding style or architectural choices.
- **Success Patterns**: Approaches that worked particularly well.
- **Tool Friction**: Moments where tools were slow, buggy, or inefficient.

### 3. Categorization & Priority

Classify findings:

- **CRITICAL**: Process failures (PFC/RTB) or safety violations.
- **HIGH**: Explicit user preferences or recurring coding errors.
- **MEDIUM**: General improvements or performance optimizations.

### 4. Skill Application

1. **Locate Target**: Find the relevant `SKILL.md` (e.g., `graph/SKILL.md` for RAG changes).
2. **Propose Update**: Formulate a clear, imperative rule (e.g., "Always validate X before Y").
3. **Draft Updates**: Use the `learnings` layer to track proposed changes.
4. **Execute**: Update the file and create a version tag using `skill_version_manager.py`.

### 5. Post-Mission Debrief (RTB)

Include a mandatory debrief summary in the final response:

- Use `enhanced_reflect_system.py --debrief debrief.md` to format the report.
- Summarize successes, friction points, and strategy evolution.

## 📋 Mission Reflection Template

Use this structure when performing a "/reflect" during or after a mission:

- **Objective**: [Issue ID / Task Name]
- **Outcome**: [Success / Partial / Failure]
- **Diagnostics (PFC/RTB)**:
  - [e.g., "RTB Warning: Uncommitted changes"]
  - [e.g., "Success: All tests passed"]
- **Tool/Process Friction**: [e.g., "bd doctor required after every sync"]
- **Strategy Evolution**: [e.g., "Hard-code YAML for Ollama models"]
- **Applied Memories**: [List of SKILL.md files updated]

## 🧬 Self-Evolution Strategy (ACE Integration)

The LightRAG ACE reflector helps drive this work:

- **Graph Quality**: Insights from `ACEReflector` identify data extraction patterns that need codified rules.
- **Continuous Learning**: Every `ACE` repair is a candidate for a new general rule in `coding-standards`.
- **Systematic Growth**: Use `proactive_improvements.py` to analyze patterns across missions.
