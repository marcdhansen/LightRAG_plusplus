# 🤖 AGENTS.md

Welcome to the LightRAG project. This repository uses the **Standard Mission Protocol (SMP)** for agentic collaboration.

## 🚀 Getting Started

Before you write any code:

1. **Read the Bootstrap Guide**: Open `.agent/BOOTSTRAP.md`.
2. **Initialize your session**: Run `./scripts/agent-init.sh` in your terminal.

## 🧭 Project Navigation

- **Roadmap**: `.agent/rules/ROADMAP.md`
- **Current Phase**: `.agent/rules/ImplementationPlan.md`
- **Tasks**: Run `bd ready` to see what needs to be done.

## 🛡️ Protocol

- Always run a **Pre-Flight Check (PFC)** before starting.
- Always run a **Return To Base (RTB)** check before finishing.
- Capture your learnings using the `/reflect` skill.

*For global standards and system-wide documentation, see `~/.gemini/GLOBAL_INDEX.md`.*

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

## 🛠️ Troubleshooting

### Beads Disk I/O Error

If you encounter `sqlite3: disk I/O error` when running `bd` commands, it is likely due to environment sandbox restrictions on parent directories (global/workspace registries). Use the `--sandbox` flag to restrict Beads to the local repository:

```bash
bd --sandbox <command>
```

Alternatively, ensure the Beads daemon (`bd daemon start`) is running with proper permissions.

---

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
