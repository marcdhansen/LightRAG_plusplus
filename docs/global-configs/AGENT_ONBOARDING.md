# 🚀 Agent Onboarding & Standard Mission Protocol (SMP)

To initialize this project in a new environment or with a new agent (e.g., OpenCode, Claude CLI), follow these steps:

1. **Read the Bootstrap Guide**: Immediately read `.agent/BOOTSTRAP.md` to understand project-specific initialization.
2. **Run the Bootstrap Script**: Execute `./scripts/agent-init.sh` to automatically verify your toolchain and get up to speed on the mission state.

## 1. Anchor to Global Memory

Identify the global configuration directories.
> "Read the Global Agent Rules in `~/.gemini/GEMINI.md` and follow the Standard Mission Protocol (SMP). Use the Global Index at `~/.gemini/GLOBAL_INDEX.md` as your primary navigation map."

## 2. Verify Tool Availability

Confirm the core toolchain is accessible:

```bash
which bd uv python git
```

*If `bd` is missing, run `bd onboard` or follow the guide in `~/.gemini/HOW_TO_USE_BEADS.md`.*

## 3. Initialize Mission Readiness (PFC)

Run the **Pre-Flight Check (PFC)** to align with the current project state:

```bash
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc
```

### ⚡ Enhanced Turbo-Bootstrap (Recommended)

You can automate the complete onboarding process including service startup and verification:

```bash
./scripts/enhanced-agent-init.sh
```

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

## 4. Connect to Project Brain

Read the following files to understand the mission status:

1. `.agent/rules/ROADMAP.md`: High-level navigation.
2. `.agent/rules/ImplementationPlan.md`: Technical breakdown.
3. Execute `bd ready`: To see current unblocked tasks.

## 5. Standard Mission Loop (RTB)

You MUST execute the **Return To Base (RTB)** procedure before ending your session:

1. Run project-specific linters/tests.
2. Update/Close Beads issues.
3. Execute `/reflect` to save session learnings to `~/.gemini/GEMINI.md`.
4. Run `bd sync` and `git push`.

## 6. Long-Term Memory (Automem)

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

## 7. Observability (Langfuse)

This project uses **Langfuse** for tracing LLM calls and RAGAS evaluations.

### Quick Setup (Enhanced Bootstrap)
```bash
# Langfuse is automatically started and verified by enhanced-agent-init.sh
./scripts/enhanced-agent-init.sh
```

### Manual Setup (Fallback)
1. **Local Langfuse**: Navigate to `langfuse_docker/` and run `docker-compose up -d`.
2. **Verification**: Check health at `http://localhost:3000/api/public/health`
3. **Web UI Access**: http://localhost:3000 with credentials `pk-lf-lightrag` / `sk-lf-lightrag`
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
