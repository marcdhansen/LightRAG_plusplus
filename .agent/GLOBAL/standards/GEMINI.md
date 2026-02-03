# 🌐 Global Agent Rules: Standard Mission Protocol (SMP)

These rules define the universal behavior and operational standards for agents across all workspaces.

## 🛫 Pre-Flight Check (PFC)

**MANDATORY: Run at the start of every session.**

1. **Tool Check**: Verify all required tools (e.g., `bd`, `uv`, `docker`) are available.
2. **Context Check**: Read `.agent/rules/ROADMAP.md` and `.agent/rules/ImplementationPlan.md` to understand current state.
3. **Status Check**: Run `bd ready` to see active tasks.
4. **Issue Check**: Ensure a Beads issue exists for the current objective. If not, create one using `bd create`.
5. **Flight Director**: Use the `Flight Director` skill to verify that all PFC procedures are strictly followed. Run: `python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc`. **NOTE**: Approvals in `task.md` are only valid for 4 hours; stale timestamps will block takeoff.
6. **Navigation Check**: Verify readability of `~/.gemini/GLOBAL_INDEX.md` and confirm access to the current project's entry in the index.
7. **Markdown Check**: Run `markdownlint` on planning documents to ensure rendering integrity.
8. **Initialization**: Formulate the initial task list and announce the starting objective.
9. **Execution Handshake**: For high-impact or long-running tasks, explicitly list the next steps and wait for a "Go" signal before initiating execution.

## ✈️ In-Flight Operations (IFO)

**GUIDELINES: Operational standards during execution.**

1. **Autopilot**: Keep `task.md` updated as the living source of truth.
2. **Spec-Driven TDD**: Every functional change must start with a specification and a failing test case (Red phase) before implementation (Green phase).
3. **Turbulence**: If a step fails, investigate logs and documentation before asking the user.
4. **Black Box**: Record significant decisions in `implementation_plan.md` or `walkthrough.md`.
5. **Course Correction**: If the plan needs to change, switch to PLANNING mode and update artifacts first.
6. **UI Testing**: For code changes that affect the UI, the agent must test the state by running the browser and monitoring the output. Only after automatic UI validation should the user be asked to manually verify the UI.
7. **UI Integrity**: Use Playwright to verify any changes that affect the UI. This is a standard rule for UI modifications.
8. **Container Management**: If it is necessary to bring up containers, run Docker without Docker Desktop to minimize resource consumption (e.g., use CLI-based alternatives like OrbStack or Colima).
9. **Value-Driven Complexity Scaling**: For new feature development, prefer to begin with simple modifications. Only after the value of the new feature has been demonstrated will we proceed to more complex implementations.

## 🛬 Return To Base (RTB)

**MANDATORY: Run at the end of every session.**

1. **Beads Update**: File issues for remaining work and close finished ones.
2. **Quality Gates**: Proactively run all project-specific linters and tests.
    - **Python**: `uv run ruff check --fix .` and `uv run ruff format .`
    - **WebUI**: `cd lightrag_webui && bun run lint`
    - **Unified**: `pre-commit run --all-files`
3. **Flight Director Verification**: **CRITICAL**. Run the Flight Director RTB check to ensure everything is compliant.

    ```bash
    python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --rtb
    ```

    **BLOCKING**: Do NOT push or hand off if the Flight Director reports warnings or critical errors.
4. **Testing**: Run project-specific linters, tests, and `markdownlint` on all modified `.md` files. **MANDATORY**: All performance-related benchmarks must include latency/speed metrics in addition to accuracy metrics to enable speed-accuracy tradeoff analysis.
5. **Web UI Verification**: Run `bun run build` in `LightRAG/lightrag_webui` and verify the UI is functional if any frontend changes were made.
6. **Sync & Push**:

    ```bash
    bd sync
    git add .
    git commit -m "chore: save session work"
    git push
    ```

7. **Cleanup**: Delete any temporary files/directories created during the current task (e.g., `test_output.txt`, `debug_import.py`, orphaned logs) and close any browser tabs opened for testing.
8. **Flight Director**: Use the `Flight Director` skill to verify that all RTB procedures are strictly followed. Run: `python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --rtb`
9. **Verification**: Ensure `git status` shows up-to-date with origin.
10. **Handoff**: Provide a clear summary of what was done, **list specific Beads issues created**, what skills were used, any suggestions for skill management, and what should be done next.
11. **Self-Evolution**: Execute the `reflect` skill (e.g., `/reflect`) to analyze the session for "memories"—specific corrections, preferences, or tool friction—and update relevant `SKILL.md` files or global rules to permanently implement the "correct once, never again" philosophy.
12. **Clear Plan Approval**: Remove or neutralize the `## Approval` marker in `task.md` to prevent accidental auto-starts in the next session.
13. **Post-Mission Debrief**: Include a comprehensive debrief summary after all work is completed. This should cover:
    - **Process Review**: Successes and friction points in the development cycle.
    - **Lessons Learned**: Significant technical or strategic discoveries.
    - **Strategy Evolution**: Suggestions for rule modifications, skill improvements, or anti-pattern logging.

## 🏗️ 3-Tier Planning Strategy

1. **ROADMAP.md**: High-level navigation and current objective status (stored in `.agent/rules/`).
2. **ImplementationPlan.md**: Detailed technical breakdown and phase tracking (stored in `.agent/rules/`).
3. **Beads (`bd`)**: Granular task management and dependency tracking.

## 🧪 Spec-Driven TDD Protocol

All development MUST follow the Spec-Driven Test-Driven Development (TDD) cycle:

1. **Specification**: Define the objective, requirements, and success criteria in `task.md` or `ImplementationPlan.md`.
2. **Test Selection/Creation**:
    - Identify existing tests that should pass.
    - Create new test cases (Python `pytest` or WebUI `playwright`) that verify the new functionality or reproduce the bug.
    - **MANDATORY**: Run the tests and confirm they FAIL (Red phase).
3. **Implementation**: Write the minimum amount of code required to make the tests pass.
4. **Verification**: Run the tests and confirm they PASS (Green phase).
5. **Refactor**: Improve the code while ensuring tests remain green.
6. **Audit**: For LLM-based features, run benchmarks/audits to ensure no regression in quality (accuracy, latency).

## 🐚 Beads Field Manual

- `bd init`: Initialize Beads in a project.
- `bd ready`: List tasks with no unsatisfied blockers.
- `bd sync`: Flush current state to Git and push to remote.
- `bd doctor --fix`: Check and fix common database issues.
- **Protocol for Parallel Agents**:
    1. **Unique Assignment**: Explicitly assign issues using labels (e.g., `bd update <id> --set-labels agent:alpha`) to prevent overlap.
    2. **Frequent Sync**: Run `bd sync` at the start of PFC and end of RTB to maintain state consistency across agent instances.
    3. **Dependency Management**: Use `bd dep` to establish clear work orders, ensuring agents do not start tasks with unsatisfied blockers.
    4. **Health Maintenance**: Proactively run `bd doctor --fix` if any database locks or sync conflicts are detected.
- **Git Isolation for Parallel Agents**:
    1. **Branch-per-Task**: Each agent must work on a dedicated branch (e.g., `git checkout -b task/lightrag-123`).
    2. **Explicit Staging**: Never use `git add .`. Stage only the specific files modified (e.g., `git add tests/test_highlight.py`).
    3. **Worktree Strategy**: For simultaneous work on the same machine, use `bd worktree create <name>` to isolate filesystem changes.
- **Detailed Guide**: [HOW_TO_USE_BEADS.md](HOW_TO_USE_BEADS.md)

## 📝 Markdown Standards

- **Style Guides**: Always apply common Markdown style guides (e.g., consistent headers, list markers, and spacing).
- **Scannability**: Always place progress indicators (e.g., [x], [ ], ✅, ❌) on the **left** of the text.
- **Task Lists**: For checkboxes to render correctly, they **must** be part of a list (e.g., `- [ ]` or `* [x]`) and **must** have a space between the closing bracket `]` and the following text. They should not be used in headers.
- **Linting**: Use a markdown linter (e.g., `markdownlint`) to verify document integrity before finishing tasks. **Exception**: Relax MD013 (line-length) for lines containing Mermaid diagrams, complex tables, or long URLs where manual wrapping would degrade readability.

- **Path Portability**: Prefer **relative paths** (e.g., `../docs/foo.md`) over absolute paths (`/Users/...`) for internal links and images to ensure cross-workspace compatibility.

## 🧬 Self-Evolution Strategy

- **Preference Capture**: Always record user preferences (e.g., "beeps for input") in this file.
- **Anti-Pattern Logging**: Document sequences that lead to failure (e.g., "avoiding bd edit").
- **Proactive Improvement**: Fix broken links and formatting issues in planning docs without being asked.
- **Global Strategy**: Refer to [SELF_EVOLUTION_GLOBAL.md](SELF_EVOLUTION_GLOBAL.md) for universal patterns.
- **Nomenclature**: Refer to [MISSION_NOMENCLATURE.md](MISSION_NOMENCLATURE.md) for detailed definitions of mission terms (SMP, Sortie, ATO).
- **Atomic Start Protocol**: Never write a line of code or a plan without a specific Beads ID. When building compliance tools (like Flight Director), you must *manually* simulate the compliance check before starting work to avoid the "Bootstrap Paradox".

---

## Gemini Added Memories

- To start the LightRAG server in this project: 1. Build the WebUI: `cd LightRAG/lightrag_webui && bun run build`. 2. Sync Python dependencies: `cd LightRAG && uv sync --extra api`. 3. Start the server: `uv run lightrag-server`. The server defaults to <http://localhost:9621>.
- An automated test has passed ONLY when it has been automatically run and has passed successfully.
- Switched LightRAG LLM model to qwen2.5-coder:1.5b due to performance issues with 7b on the current system (Jan 19, 2026).
- The user prefers systematic Python test scripts integrated into the standard test suite (pytest) over ad-hoc shell scripts for verification tasks.
- For integration testing, start with the smallest file in `test_documents` and proceed to larger files sequentially to speed up the process.
- **System File Locations**:
  - Global Rules: `~/.gemini/GEMINI.md`
  - Global Workflows: `~/.gemini/antigravity/global_workflows/global-workflow.md`
  - Project Rules: Workspace root or `.agent/rules/`
  - Project Brain/Planning: `~/.gemini/antigravity/brain/PROJECT_ID/`
- **Preference**: ALWAYS search the web for potential solutions to tool errors (like `bd sync` failure) before asking the user to intervene.
- **Troubleshooting**: If `bd sync` fails (e.g., "git add failed" or "import requires SQLite storage backend"), manually run `git add .`, `git commit`, and `git push` to resolve the state mismatch, then run `bd doctor --fix` if needed.
- **Testing**: Local test environments with local LLMs often require significantly higher timeouts (120s-300s) than default configurations (30s).
- **Testing**: Increased `top_k` (e.g., 20) in retrieval tests improves recall reliability in crowded local vector stores.
- **WTU (Wrap This Up)**: When the user says "let's wrap this up" or "WTU", explicitly verify that all steps in the **Return To Base (RTB)** checklist (including Web UI verification) have been completed successfully before ending the session.
