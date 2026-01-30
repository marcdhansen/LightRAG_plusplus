---
name: Librarian
description: A skill for maintaining the Global Documentation Index and ensuring progressive disclosure of materials.
---

# 📚 Librarian Skill

## Purpose

The Librarian is responsible for maintaining the `GLOBAL_INDEX.md` as the single source of truth for locating projects, rules, and memories across the system. It ensures "progressive disclosure" by allowing agents to start at the Index and drill down into specific contexts.

## 📍 Locations

- **Global Index**: `~/.gemini/GLOBAL_INDEX.md` (Primary)
- **Search Scope**: `~/.antigravity`, `~/.gemini`, `~/.claude`, `~/.beads`, `~/.codeium`, `~/.cursor`, `~/.opencode`

## 🛠️ Protocols

### 1. Index Maintenance

When invoked or when "cleanup" is requested:

1. **Read** `~/.gemini/GLOBAL_INDEX.md`.
2. **Scan** the Search Scope for:
    - Top-level config files (e.g., `GEMINI.md`, `CLAUDE.md`).
    - Project Roots (look for `.git`, `pyproject.toml`, or `ROADMAP.md`).
    - New Skills (`skills/*/SKILL.md`).
3. **Update** the Index with valid relative or absolute links to any new findings.
4. **Prune** broken links if files are deleted.

### 2. Progressive Disclosure

- Always link to the **File** (e.g., `ROADMAP.md`) rather than just the directory, if a clear entry point exists.
- Group links logically (Global Rules, Projects, Skills, Archives).

### 3. Self-Evolution

- If you find a `SELF_EVOLUTION.md` file in any searched directory, ensure it is linked in the Index.

## 🔍 Discovery Commands

Use these commands to find materials:

```bash
# Find global markdown rules
find ~/.gemini ~/.antigravity -maxdepth 2 -name "*.md"

# Find Skills
find ~/.gemini/antigravity/skills -name "SKILL.md"

# Find probable project roots (heuristic)
find ~/antigravity_lightrag -name "ROADMAP.md"
```
