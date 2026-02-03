# 🤖 LightRAG Project AGENTS.md

Welcome to the LightRAG project. This repository supports **dual agent systems**: the traditional **Standard Mission Protocol (SMP)** and the enhanced **OpenViking** system.

## 🚀 Getting Started

Before you write any code:

1. **Read Universal Protocol**: [~/.agent/AGENTS.md](~/.agent/AGENTS.md)
2. **Project Bootstrap**: Open `.agent/BOOTSTRAP.md` (project-specific setup)
3. **Initialize Session**: Run `./scripts/agent-init.sh` in your terminal

## 🔗 **Project Navigation**

- **Global Index**: [~/.agent/docs/GLOBAL_INDEX.md](~/.agent/docs/GLOBAL_INDEX.md) ← Master navigation hub
- **Project Rules**: [.agent/rules/ROADMAP.md](rules/ROADMAP.md) ← LightRAG-specific roadmap
- **Project Skills**: [.agent/skills/](skills/) ← Symlink to global skills (→ ~/.gemini/antigravity/skills/)
- **Session Locks**: [.agent/session_locks/](session_locks/) ← Current active sessions

## 🔒 **Project-Specific Protocols**

- **TDD Gates**: Automated test-driven development enforcement
- **Quality Assurance**: Project-specific validation and linting
- **Multi-Agent Coordination**: Session locks and branch protection
- **Integration Testing**: Cross-component validation procedures

---

*Project-specific configuration layered on top of universal protocols.*

## 🧭 Project Navigation

- **Roadmap**: `.agent/rules/ROADMAP.md`
- **Current Phase**: `.agent/rules/ImplementationPlan.md`
- **Tasks**: Run `bd ready` to see what needs to be done.

## 🤖 Agent System Selection

This project supports **dual agent systems**:

### SMP (Standard Mission Protocol)
- **Location**: Traditional file-based skills in `.agent/skills/`
- **Use Case**: Established workflows, maximum compatibility
- **Integration**: LightRAG on port :9621

### OpenViking (Enhanced System)
- **Location**: AI-powered agent with dynamic skills
- **Use Case**: Token efficiency, conversation memory, faster responses
- **Integration**: LightRAG on port :9622
- **Documentation**: `.agent/skills/openviking/SKILL.md`

**Quick Setup**:
```bash
# For OpenViking
export OPENAI_API_KEY=your-key-here
./openviking/scripts/manage.sh start

# For SMP (default)
./scripts/agent-init.sh
```

## 🛡️ Protocol

- Always run a **Pre-Flight Check (PFC)** before starting.
- Always run a **Return To Base (RTB)** check before finishing using `/rtb`.
- Capture your learnings using the `/reflect` skill.

*For global standards and system-wide documentation, see `~/.gemini/GLOBAL_INDEX.md`.*

## Landing the Plane (Session Completion)

**When ending a work session**, use `/rtb` to automate the complete workflow. Work is NOT complete until `git push` succeeds.

**AUTOMATED WORKFLOW:**

```bash
/rtb
```

The `/rtb` command automatically handles:

1. **Validation** - Checks git status, beads, quality gates, session locks
2. **SOP Evaluation** - **MANDATORY**: Evaluates Standard Operating Procedure effectiveness (PFC compliance, process friction) - BLOCKS RTB if failed
   - **Auto-captures learnings** using reflect system for continuous improvement
3. **Uncommitted changes** - Handles commit/stash/discard workflows
4. **Quality gates** - Runs tests, linters, builds (if configured)
5. **Git operations** - Pull, sync, push with proper verification
6. **Session cleanup** - Removes locks, temp files, stale branches
7. **Global memory sync** - Commits and pushes `~/.gemini` changes

**MANUAL STEPS (if needed):**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Verify markdown integrity** - Check and remove duplicate markdown files using hashes
4. **Update issue status** - Close finished work, update in-progress items
5. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   # LightRAG repository
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"

   # Global memory (~/.gemini)
   cd ~/.gemini && git status
   cd ~/.gemini && git add -A && git commit -m "Session learnings and SOP updates"
   cd ~/.gemini && git push
   ```

6. **Clean up** - Clear stashes, prune remote branches
7. **Verify** - All changes committed AND pushed
8. **Hand off** - Provide context for next session

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

**Agent System Coordination:**
- SMP and OpenViking agents can work simultaneously
- Use different task IDs to prevent conflicts
- Each system maintains its own session coordination
- Check both systems' status when available

**If your lock isn't being detected:**
- Ensure `AGENT_LOCK_FILE` environment variable is set, or
- The lock file follows the naming pattern: `agent_<id>_<session>.json`

### Database Configuration for Multi-Agent

**SQLite Mode**: This project uses beads with SQLite (`no-db: false` in `.beads/config.yaml`) for:
- **ACID guarantees** - Prevents data corruption during concurrent task updates
- **Better performance** - Faster queries for complex task management
- **Automatic sync** - SQLite database syncs with JSONL via git

**Important**: Always run `bd sync` before and after working to ensure all agents have the latest task state from git. The SQLite database is gitignored, but the JSONL files (`.beads/issues.jsonl`) are tracked in git and serve as the source of truth.

## 📚 Documentation Resources

### .agent Directory Structure

The `.agent/` directory contains organized documentation for cross-agent collaboration:

```
.agent/
├── docs/
│   ├── sop/                    # Standard Operating Procedures
│   │   ├── global-configs/     # → ~/.gemini/ (global standards)
│   │   ├── skills/            # → ~/.gemini/antigravity/skills/
│   │   └── workspace/         # Workspace-specific docs
│   ├── workspace/              # Workspace documentation
│   │   ├── TODO.md            # Current project tasks
│   │   └── legacy_todo.md     # Historical TODO items
│   └── troubleshooting/        # Troubleshooting guides
│       └── beads_sync_issues.md  # Beads sync problems & solutions
├── skills/                     # Symlink → ~/.gemini/antigravity/skills/
└── rules/                      # Project rules and roadmaps
```

### Key Resources

- **Current Tasks**: `.agent/docs/workspace/TODO.md` - Check before starting work
- **Troubleshooting**: `.agent/docs/troubleshooting/` - Known issues and solutions
- **Skills**: `.agent/skills/` - Available agent capabilities
- **Global Standards**: `~/.gemini/GLOBAL_INDEX.md` - System-wide documentation

## 🛠️ Troubleshooting

### Common Issues

For comprehensive troubleshooting guides, see `.agent/docs/troubleshooting/`:

- **Bead Sync Issues**: `.agent/docs/troubleshooting/beads_sync_issues.md` - Complete guide to Beads synchronization problems
- **Disk I/O Errors**: Use `bd --sandbox <command>` for environment sandbox restrictions

### Beads Disk I/O Error

If you encounter `sqlite3: disk I/O error` when running `bd` commands, it is likely due to environment sandbox restrictions on parent directories (global/workspace registries). Use the `--sandbox` flag to restrict Beads to the local repository:

```bash
bd --sandbox <command>
```

Alternatively, ensure the Beads daemon (`bd daemon start`) is running with proper permissions.

---

## 📝 Markdown Integrity Verification

**MANDATORY:** All agents must verify markdown file integrity before ending a session. This prevents duplicate documentation and confusion.

### How It Works

The RTB workflow automatically runs `.agent/scripts/verify_markdown_duplicates.sh` which:

1. **Calculates SHA-256 hashes** for all `.md` files (excluding `.git`, `node_modules`, `venv`)
2. **Groups identical files** by hash value
3. **Keeps the shortest path** file in each duplicate group
4. **Removes duplicates** automatically or interactively

### Manual Usage

```bash
# Auto-remove duplicates (keeps shortest path files)
.agent/scripts/verify_markdown_duplicates.sh

# Interactive review before removal
.agent/scripts/verify_markdown_duplicates.sh --interactive
```

### Blocking Behavior

- **RTB will fail** if duplicate markdown files are detected
- **Session cannot end** until duplicates are resolved
- **Auto-removal is safe** - keeps the most accessible file (shortest path)

---

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
- **RTB is BLOCKED** by duplicate markdown files - must resolve before session end
