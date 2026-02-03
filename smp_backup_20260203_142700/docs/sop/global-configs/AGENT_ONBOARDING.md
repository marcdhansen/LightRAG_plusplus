# 🚀 Agent Onboarding & Standard Mission Protocol (SMP)

To initialize this project in a new environment or with a new agent (e.g., OpenCode, Claude CLI), follow these steps:

1. **Read Bootstrap Guide**: Immediately read `.agent/BOOTSTRAP.md` to understand project-specific initialization.
2. **Run Bootstrap Script**: Execute `./scripts/agent-init.sh` to automatically verify your toolchain and get up to speed on the mission state.

## 1. Anchor to Global Memory

Identify global configuration directories.
> "Read the Global Agent Rules in `~/.gemini/GEMINI.md` and follow the Standard Mission Protocol (SMP). Use the Global Index at `~/.gemini/GLOBAL_INDEX.md` as your primary navigation map."

## 2. Verify Tool Availability

Confirm the core toolchain is accessible:

```bash
which bd uv python git
```

*If `bd` is missing, run `bd onboard` or follow the guide in `~/.gemini/HOW_TO_USE_BEADS.md`.*

## 3. Mission Readiness & Coordination (Multi-Agent Protocol)

This project uses an automated **session coordination system** to prevent multiple agents from conflicting on the same task.

### Step A: Initialize Mission & Session

Run the enhanced bootstrap script. This will check tool availability, show active agent status, and prompt you to register your task.

```bash
./scripts/agent-init.sh
```

**What it does:**

1. **Tool Check**: Verifies `bd`, `uv`, `python`, `git`.
2. **Agent Status**: Shows who else is working and on what.
3. **Registration**: Prompts for your Task ID and description.
4. **Heartbeat**: Automatically starts a background heartbeat to keep your session active.
5. **Conflict Check**: Calls Flight Director PFC to ensure no one else is on your task.
6. **Persistence**: Ensures your session is labeled in Beads (`bd list`).

### Step B: Operational Rules

- **Never work on the same task ID** as another active agent.
- **Heartbeats are automatic** while your session is active.
- **Cleanup is mandatory**: Always run `./scripts/agent-end.sh` (included in RTB).

### Step C: Manual Controls (Fallback)

If you need to manage your session manually:

- `./scripts/agent-status.sh`: Check active/stale sessions.
- `./scripts/agent-start.sh --task-id <id>`: Start a new session.
- `./scripts/agent-end.sh`: End current session and stop heartbeat.

**Enhanced Features:**

- ✅ Comprehensive environment validation (tools, paths, Docker)
- ✅ Port conflict detection and reporting
- ✅ Automated service startup (Automem + Langfuse)
- ✅ Health check verification with retry logic
- ✅ Service auto-recovery (single restart attempt)
- ✅ Integration smoke testing (memory storage/retrieval)
- ✅ Detailed error reporting and troubleshooting guidance

**Fallback (basic mode):**

```bash
./scripts/agent-init.sh  # Original toolchain + PFC only
```

## 5. Connect to Project Brain

Read the following files to understand the mission status:

1. `.agent/rules/ROADMAP.md`: High-level navigation.
2. `.agent/rules/ImplementationPlan.md`: Technical breakdown.
3. Execute `bd ready`: To see current unblocked tasks.

### 📁 Updated Documentation Structure

**Important**: Documentation structure was reorganized for better organization:

```bash
docs/
├── sop/                     # SOP & Protocols (symbolic links to global sources)
│   ├── global-configs/    # → ~/.gemini/ (GEMINI.md, GLOBAL_INDEX.md, etc.)
│   ├── skills/            # → ../.agent/skills/
│   └── workspace/          # → workspace_docs/
├── project/                 # LightRAG-specific documentation
│   ├── test_inputs/      # Historical test documents (preserved)
│   ├── ARCHITECTURE.md
│   ├── EVALUATION.md
│   └── subsystems/
├── external/                # External references and PDFs
└── cross-ide/             # Cross-IDE and cross-agent compatibility
```

### 🔍 Key Navigation Changes

- **SOP Reference**: `docs/sop/global-configs/GEMINI.md` (symbolic link to `~/.gemini/GEMINI.md`)
- **Project Docs**: `docs/project/` (LightRAG-specific)
- **Test Data**: `docs/project/test_inputs/` (Historical test documents)
- **Comprehensive Index**: `docs/sop/global-configs/GLOBAL_INDEX.md` (symbolic link to `~/.gemini/GLOBAL_INDEX.md`)
- **Skills**: `docs/sop/skills/` (symbolic link to `../.agent/skills/`)

### 🎯 Critical Test Document Recovery

**Note**: All test documents were accidentally deleted during cleanup but completely restored from git history and properly organized in `docs/project/test_inputs/`. This demonstrates importance of content verification before deletion.

## 6. Standard Development Workflow (Spec-Driven TDD)

This project follows **spec-driven Test-Driven Development (TDD)**. All work must follow this workflow:

### A. Specification First
1. **Read the specification** for the feature/bug you're implementing
2. **Understand requirements** completely before writing any code
3. **Ask clarifying questions** if the specification is ambiguous

### B. Test-Driven Development
1. **Write failing tests** that match the specification requirements
2. **Run tests** to confirm they fail (red phase)
3. **Implement minimal code** to make tests pass (green phase)
4. **Refactor** while keeping tests passing (refactor phase)

### C. Quality Gates
Before any code is considered complete:

```bash
# Run all quality checks
pytest                    # Run tests
ruff check                # Lint code
ruff format               # Format code
mypy                      # Type checking (if applicable)
```

### D. Integration Verification
1. **Manual testing** for UI/API changes
2. **Integration tests** for cross-component features
3. **Performance tests** for critical paths (if applicable)

## 7. Standard Mission Loop (RTB)

You MUST execute the **Return To Base (RTB)** procedure before ending your session:

1. **Run quality gates** (tests, linters, formatters).
2. Update/Close Beads issues.
3. Execute `/reflect` to save session learnings to `~/.gemini/GEMINI.md`.
4. **Run `./scripts/agent-end.sh`** - Clean up your session lock file.
5. **Push LightRAG repository**:
   ```bash
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
6. **Push Global Memory (~/.gemini)**:
   ```bash
   cd ~/.gemini && git status
   cd ~/.gemini && git add -A && git commit -m "Session learnings and SOP updates"
   cd ~/.gemini && git push
   ```

## 8. Long-Term Memory (Automem)

This project uses **Automem** for graph+vector long-term memory across sessions.

### Quick Setup (Enhanced Bootstrap)

```bash
# Automem is automatically started and verified by enhanced-agent-init.sh
./scripts/enhanced-agent-init.sh
```

### Manual Setup (Fallback)

1. **Initialize Automem**: If not already running, navigate to `~/GitHub/verygoodplugins/automem` and run `make dev`.
2. **Verify Health**: Check service health at `http://localhost:8001/health`
3. **Contextual Awareness**: Query Automem at the start of a session for relevant patterns, preferences, and session-spanning context.
4. **Capture**: Ensure significant session learnings are stored in Automem during the `/reflect` phase.

### Authentication

- **API Token**: `AUTOMEM_API_TOKEN=test-token` (default)
- **Admin Token**: `ADMIN_API_TOKEN=test-admin-token` (default)
- **Health Check**: No authentication required

### Service Details

- **Flask API**: Port 8001 (health endpoint: `/health`)
- **FalkorDB**: Port 6380 (graph database)
- **Qdrant**: Port 6333 (vector database)

## 9. Observability (Langfuse)

This project uses **Langfuse** for tracing LLM calls and RAGAS evaluations.

### Quick Setup (Enhanced Bootstrap)

```bash
# Langfuse is automatically started and verified by enhanced-agent-init.sh
./scripts/enhanced-agent-init.sh
```

### Manual Setup (Fallback)

1. **Local Langfuse**: Navigate to `langfuse_docker/` and run `docker-compose up -d`.
2. **Verification**: Check health at `http://localhost:3000/api/public/health`
3. **Web UI Access**: <http://localhost:3000> with credentials `pk-lf-lightrag` / `sk-lf-lightrag`
4. **Trace Verification**: After running any query, check for new traces in Langfuse to ensure observability is operational.

### Service Details

- **Web UI**: Port 3000 (health: `/api/public/health`)
- **Worker**: Port 3030 (background processing)
- **PostgreSQL**: Port 5432 (primary storage)
- **Redis**: Port 6379 (job queue)

## 📚 Additional Documentation

- **📖 Service Setup Guide**: `SERVICE_SETUP.md` - Comprehensive service configuration and troubleshooting
- **🔧 Troubleshooting**: Check `SERVICE_SETUP.md` for common issues and solutions
- **🐳 Docker Reference**: Service-specific Docker commands and configuration
