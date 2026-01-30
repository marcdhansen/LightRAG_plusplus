---
name: reflect
description: Analyzes the current conversation history to extract lessons, user preferences, and corrections, then updates relevant SKILL.md files to prevent repeating mistakes.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Reflect & Improve

## Goal

Implement the "correct once, never again" philosophy by analyzing the current session for "memories"—specific corrections, coding preferences, or logic improvements—and permanently documenting them into the relevant `SKILL.md` files.

## 🛠️ Tools & Scripts

### 1. `enhanced_reflect_system.py` (Enhanced System)

Comprehensive reflection system integrating PFC/RTB diagnostics with conversation analysis.

**Usage**:

```bash
# Full comprehensive analysis (recommended)
python scripts/enhanced_reflect_system.py --comprehensive conversation.log

# Flight diagnostics only
python scripts/enhanced_reflect_system.py --flight-diagnostics

# Conversation analysis only
python scripts/enhanced_reflect_system.py --analyze-conversation conversation.log

# Show pending learnings
python scripts/enhanced_reflect_system.py --pending-learnings
```

### 2. `ace_integration_bridge.py` (ACE Integration)

Bridge between ACE reflector outputs and Reflect skill workflow.

**Usage**:

```bash
# Test ACE integration
python scripts/ace_integration_bridge.py test
```

### 3. `skill_version_manager.py` (Version Management)

Tag-based versioning and rollback system for skill files.

**Usage**:

```bash
# Create a learning tag
python scripts/skill_version_manager.py tag --skill SkillName --description "Learning description"

# List all versions
python scripts/skill_version_manager.py list

# List versions for specific skill
python scripts/skill_version_manager.py list --skill Reflect

# Rollback to previous version of skill
python scripts/skill_version_manager.py rollback-previous --skill Reflect

# Rollback to specific tag
python scripts/skill_version_manager.py rollback --tag learning_20260130_004834_reflect

# Compare versions
python scripts/skill_version_manager.py compare --tag learning_20260130_004834_reflect

# Clean up old tags (keep latest 20)
python scripts/skill_version_manager.py cleanup --keep 20
```

### 4. `proactive_improvements.py` (Proactive Suggestions)

Analyzes patterns across learnings, flight diagnostics, and code to suggest proactive improvements.

**Usage**:

```bash
# Full pattern analysis and suggestion generation
python scripts/proactive_improvements.py analyze

# Show top suggestions
python scripts/proactive_improvements.py suggest

# Track suggestion outcome
python scripts/proactive_improvements.py track --suggestion-id "Focus area" --outcome implemented --notes "Successfully implemented"
```

### 2. `reflect_assistant.py` (Legacy)

Helper script for basic memory discovery and rule auditing.

**Usage**:

```bash
# Discover potential memories from a conversation log
python scripts/reflect_assistant.py discover conversation.log

# Audit a proposed rule for conflicts
python scripts/reflect_assistant.py audit "Always use YAML" .
```

## Workflow

### 1. Analyze the Session

**Enhanced Approach**: Use `enhanced_reflect.py --comprehensive conversation.log` for automated analysis.

**Manual Analysis**: Scan the conversation history (system prompts, user inputs, and your outputs) to identify:

* **Corrections:** Instances where the user said "No," "Wrong," "Don't do X," or "Actually, use Y."
* **Preferences:** Explicit instructions regarding coding style, naming conventions, or output formats (e.g., "Use `const` instead of `var`," "Always check for SQL injections").
* **Success Patterns:** Approaches that elicited positive feedback.
* **Mission Diagnostics (Automatically Analyzed):**
  * **PFC/RTB Failures:** Enhanced system automatically analyzes `FlightDirector` outputs for patterns (e.g., beads sync issues, missing documentation, git uncommitted changes).
  * **Tool Friction:** Note instances where tools failed or were used inefficiently (e.g., repetitive `ls` calls when `Glob` would have worked).
  * **Cleanup Oversights:** Identify temporary files or processes that were not properly terminated during RTB.

**Learnings Layer**: All significant findings are automatically stored in `~/.gemini/learnings/pending_learnings.json` for review and application.

**ACE Integration**: Graph quality insights from ACE reflector are automatically captured via `ace_integration_bridge.py` and stored as high-priority learnings.

### 2. Categorize Findings

Classify identified items by confidence level:

* **High Confidence:** Explicit user instructions or hard rules (e.g., "Never use default HTML buttons").
* **Medium Confidence:** Implicit patterns that worked well during the session or mission diagnostic findings.
* **Low Confidence:** Observations that may require user verification before codifying.

### 3. Locate Target Skills

Identify which existing skill governs the relevant domain.

* Use file listing tools to find the correct skill directory (e.g., if the correction was about React components, locate `react/SKILL.md` or `frontend/SKILL.md`).
* If no specific skill exists, propose creating a new one or adding to a general `coding-standards` skill.
* **Process Improvements:** Updates to `FlightDirector/SKILL.md` or global SOP in `GEMINI.md`.

### 4. Propose Updates

Formulate an update that integrates the new learning into the target `SKILL.md`.

* **Do not** delete existing instructions unless they explicitly conflict with the new learning.
* **Do** use clear, imperative language (e.g., "Always validate inputs for X").
* **Present the Change:** Show the user a summary or diff of the proposed changes. Ask: "I have identified the following improvements. Shall I apply these changes?"

### 5. Execution & Versioning

**Enhanced Approach**: Use learnings layer for safe, tracked updates with version management.

1. **Review Learnings**: Check pending learnings with `enhanced_reflect_system.py --pending-learnings`
2. **Apply Updates**: High-confidence learnings can be applied automatically or with user approval
3. **Learnings Layer**: Changes are tracked in `~/.gemini/learnings/applied_learnings.json` with timestamps
4. **Skill Update**: Use the `Edit` tool to modify the target `SKILL.md` file
5. **Version Management**: Use `skill_version_manager.py` to create tagged versions: `python scripts/skill_version_manager.py tag --skill SkillName --description "Learning description"`
6. **Rollback Safety**: Automatic backup tags created before rollbacks for safe experimentation

**Tag-Based Versioning**: Each learning gets a unique tag `learning_YYYYMMDD_HHMMSS_skillname` with full rollback capability.

## Examples

**User:** "/reflect"
**Model:** "I noticed that earlier you corrected my use of `var`, preferring `const` and `let`. I also see you prefer arrow functions for components. I propose updating `javascript/SKILL.md` with these rules. Shall I proceed?"

**User:** "/reflect The button styles were wrong."
**Model:** "Understood. Scanning session for button style corrections... I see you requested `rounded-md` and `px-4`. I will add this to the 'UI Guidelines' section of `frontend/SKILL.md`."

### 6. ACE Integration

The LightRAG ACE reflector (`lightrag/ace/reflector.py`) feeds into the broader Reflect skill workflow:

* **Graph Quality Reflection**: ACE reflector analyzes RAG/graph quality issues
* **Learning Integration**: ACE reflection outputs are automatically stored as high-priority learnings
* **Cross-Domain Learning**: Graph quality insights may inform broader coding practices and patterns
* **Quality Standards**: ACE findings help establish data quality standards for other skills

### 7. Post-Mission Debrief

At the conclusion of a task or session (RTB):

1. **Summarize Work**: Provide a clear list of what was accomplished (Beads issues closed).
2. **Execution Stats**: Note any tool failures, significant latencies, or repetitive steps.
3. **Lessons Learned**: Highlight key discoveries or pattern shifts (automatically captured in learnings layer).
4. **ACE Insights**: Include any graph quality lessons from ACE reflector analysis.
5. **Strategy Evolution**: Propose rule updates for `GEMINI.md` or other skills.
6. **Next Steps**: Explicitly list specific Beads issues created or remaining.
7. **Review Learnings**: Check `enhanced_reflect_system.py --pending-learnings` for any missed insights.
8. **Proactive Review**: Run `proactive_improvements.py analyze` to identify systemic improvement opportunities.

## 📋 Mission Reflection Template

Use this structure when performing a "/reflect" during or after a mission:

* **Objective**: [Issue ID] - [Brief Summary]
* **Mission Outcome**: [Success / Partial / Failure]
* **Tool Friction**: [e.g., "bd sync failed due to git add", "markdownlint not in path"]
* **Process Gaps**: [e.g., "No check for X before step Y"]
* **Strategy Evolution**: [e.g., "Always use YAML for extraction with small models"]
* **Proposed Updates**: [List of SKILL.md or GEMINI.md changes]

### 8. Continuous Improvement Loop

**Proactive Pattern Analysis**: Run `proactive_improvements.py suggest` regularly to:
- Identify recurring issues before they become problems
- Spot trending topics needing specialized attention
- Find opportunities for automated improvements
- Track learning application effectiveness

**Feedback Integration**: Use `proactive_improvements.py track` to record outcomes and refine suggestion quality over time.

## Vision & Future Improvements

1. **Auto-detection of "Skill Gaps"**: Automatically identify tasks that took an unusual number of steps or manual corrections, flagging them as candidates for new skill creation.
2. **Versioning & Rollbacks**: Integrate with Git to track changes to `SKILL.md` files, allowing easy rollback of "learned" preferences that turn out to be context-specific rather than global rules.
3. **Cross-Mission Synthesis**: Develop a mechanism to analyze patterns across multiple recent sessions to identify long-term behavioral trends rather than just session-local ones.
4. **Librarian Interaction**: Coordinate with the `Librarian` skill to ensure that new rules are placed in the most relevant architectural or process document.
5. **Conflict Resolution**: Implement a "Rule Audit" to detect when a newly identified preference conflicts with existing instructions in `GEMINI.md` or other skills.
6. **Rule Tiering**: Categorize rules into `Strict` (Non-negotiable), `Guideline` (Default but flexible), and `Example` (Illustrative only).
