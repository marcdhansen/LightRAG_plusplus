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

## 👥 Multi-Agent Coordination

When multiple agents work on this project simultaneously, coordination is essential to prevent conflicts and duplicate work.

### Session Lock System

We use a **session lock system** to track which agents are currently active and what they're working on.

#### Starting a Session

When you begin work, create a session lock:

```bash
./scripts/agent-start.sh --task-id <issue-id> --task-desc "Brief description"
```

**Example:**
```bash
./scripts/agent-start.sh --task-id lightrag-8g4 --task-desc "Implement automatic citation generation"
```

This creates a lock file in `.agent/session_locks/` containing:
- Agent identity and session info
- Current task being worked on
- Heartbeat timestamps
- Process ID for tracking

#### Checking Agent Activity

To see who else is working on the project:

```bash
./scripts/agent-status.sh
```

This shows:
- Active agents and their current tasks
- Session duration and last heartbeat
- Stale sessions (no heartbeat > 10 minutes)
- Lock file locations

#### Ending a Session

When you finish working, clean up your lock:

```bash
./scripts/agent-end.sh
```

This removes your session lock and shows a summary of your work session.

### Best Practices

1. **Always start with `agent-start.sh`** - This signals to other agents that you're active
2. **Check `agent-status.sh` before starting** - See if others are working to avoid conflicts
3. **End with `agent-end.sh`** - Clean up your lock when done (or it becomes stale after 10 min)
4. **Work on separate tasks** - Coordinate via `bd ready` to pick different issues
5. **Use separate branches** - Each agent should work on their own branch: `agent/<name>/task-<id>`

### Coordination Workflow

```bash
# 1. Check who's working
./scripts/agent-status.sh

# 2. Start your session
./scripts/agent-start.sh --task-id lightrag-993 --task-desc "Implement feature X"

# 3. Do your work...
bd ready                    # See available tasks
# ... work on your task ...
bd close lightrag-993 -r "Done"  # Close the issue

# 4. End your session
./scripts/agent-end.sh

# 5. Complete landing protocol (git push, etc.)
```

### Troubleshooting Coordination

**If you see a stale lock (>10 min old):**
- The agent may have crashed or forgot to run `agent-end.sh`
- You can safely ignore it or delete it: `rm .agent/session_locks/<stale-lock>.json`

**If you see an active agent working on your task:**
- Coordinate with them before proceeding
- Consider picking a different task from `bd ready`
- Or work on a different branch to avoid conflicts

**If your lock isn't being detected:**
- Ensure `AGENT_LOCK_FILE` environment variable is set, or
- The lock file follows the naming pattern: `agent_<id>_<session>.json`

### Database Configuration for Multi-Agent

**SQLite Mode**: This project uses beads with SQLite (`no-db: false` in `.beads/config.yaml`) for:
- **ACID guarantees** - Prevents data corruption during concurrent task updates
- **Better performance** - Faster queries for complex task management
- **Automatic sync** - SQLite database syncs with JSONL via git

**Important**: Always run `bd sync` before and after working to ensure all agents have the latest task state from git. The SQLite database is gitignored, but the JSONL files (`.beads/issues.jsonl`) are tracked in git and serve as the source of truth.

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
