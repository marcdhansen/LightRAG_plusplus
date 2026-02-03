# 🏗️ Cross-IDE & Cross-Agent Compatibility Design

This document outlines the architectural decisions and standards that ensure the Standard Mission Protocol (SMP) and agentic workflows remain consistent regardless of the Integrated Development Environment (IDE) or the specific AI Agent (Gemini, Claude, etc.) being used.

## 🎯 Core Principles

1. **Shell-Obsessed Tooling**: All critical operations (testing, linting, task management) must be executable via a standard terminal (Zsh/Bash). If a tool requires a GUI or an IDE-specific plugin to function, it is not SMP-compliant.
2. **Home-Anchored Globals**: All cross-project configuration and "skills" must reside in `~/.gemini/` or `~/.antigravity/`. This ensures that even if an IDE creates its own isolated sandbox, the agent can still reach the core mission logic.
3. **Markdown as the "Common Tongue"**: Standard Github-flavored Markdown is the only approved format for planning and documentation. This ensures perfect readability for LLMs across different providers.
4. **Path Portability**: All internal documentation links must use **relative paths**. Absolute paths (e.g., `/Users/marchansen/...`) are considered "Toxic Paths" because they break when the workspace is moved or when accessed by an agent with a different home root.

## 🛠️ Implementation Standards

### 1. Unified Directory Structure

| Location | Purpose | Accessibility |
| :--- | :--- | :--- |
| `~/.gemini/` | Global Rules, Skills, and Index | Cross-IDE / Cross-Agent |
| `.agent/rules/` | Project-specific Roadmap & Plan | Project-local |
| `.beads/` | Task Database (JSONL/SQLite) | Git-versioned / Sync-able |

### 2. The Flight Director (Process Neutrality)

The **Flight Director** skill is implemented as a standalone Python suite (`~/.gemini/antigravity/skills/FlightDirector/`). Instead of relying on IDE "hooks," it is invoked via the standard Python interpreter. This allows any agent capable of running shell commands to perform rigorous Pre-Flight (PFC) and Return-To-Base (RTB) validation.

### 3. Beads Task Management

By using **Beads** (`bd`) with a Git-backed JSONL database (`.beads/issues.jsonl`), we eliminate the need for centralized project management software.

- **IDE A** (e.g., VS Code) can run `bd ready`.
- **Agent B** (e.g., Claude CLI) can run `bd sync`.
- **Developer C** can view the state in a simple text editor.

### 4. Skill Portability

Each skill in `~/.gemini/antigravity/skills/` contains a `SKILL.md` file. This follows a standardized format that includes:

- **YAML Frontmatter**: For programmatic meta-data.
- **Markdown Instructions**: For agent consumption.
- **Python/Shell Scripts**: For automated execution.

This format is understood by both Gemini and other modern agentic frameworks.

## 🚀 Onboarding a New IDE or Agent

To initialize the Standard Mission Protocol (SMP) in a new environment (e.g., OpenCode, Claude), follow the standalone guide:

- **[Agent Onboarding Guide](AGENT_ONBOARDING.md)**: A copyable instruction set for bootstrapping new agents.

## 🧬 Self-Evolution Sync

The `reflect` skill is designed to update these global files directly. When an agent "learns" a new preference or fixes a tool friction point, it updates `~/.gemini/GEMINI.md`. This update immediately becomes available to **all other agents and IDEs** working on the same machine.

## 🛰️ Troubleshooting & Fallback Protocols

### 1. Permission Denied (`index.lock` or `git`) in `~/.gemini`

Some agents may be restricted from modifying the global home directory directly.

- **Problem**: `fatal: Unable to create '.../index.lock': Operation not permitted`.
- **Protocol**:
    1. Update the files on disk (the agent MUST be able to write).
    2. Document the change in the session handoff.
    3. If the agent cannot commit, the user should perform a manual `git commit` in `~/.gemini` at the end of the session.

### 2. Orphaned Processes

If the `agent-init.sh` or a task fails, background processes (like the `beads` daemon or local LLM servers) might be left hanging.

- **Protocol**: Use the `Quality Analyst` skill to identify and prune orphaned binary bloat and temporary files during the RTB phase.

## 🔗 Navigation

- **[Global Index](GLOBAL_INDEX.md)**: The entry point for the entire system.
- **[Standard Mission Protocol](GEMINI.md)**: The universal workflow definitions.
- **[Mission Nomenclature](MISSION_NOMENCLATURE.md)**: The shared vocabulary.
- **[Beads Field Manual](HOW_TO_USE_BEADS.md)**: How to manage tasks across agents.
