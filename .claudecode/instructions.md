# 🤖 Claude Code: Standard Mission Protocol (SMP) Bridge

This project follows the **Standard Mission Protocol (SMP)**. As an agent, you must adhere to the following workflow:

## 1. Initialization

Read `.agent/BOOTSTRAP.md` immediately upon entering the project. It points to the global onboarding guide.

## 2. Command Execution

Prefer shell commands over ad-hoc file exploration:

- Run `./scripts/agent-init.sh` to bootstrap.
- Use `bd ready` to see active tasks.
- Run PFC using `python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc`.

## 3. Planning & Documentation

Maintain the 3-Tier planning strategy:

1. `ROADMAP.md`
2. `ImplementationPlan.md`
3. Beads (`bd`) for granular tasks.

## 4. Return To Base (RTB)

Before concluding any task:

1. Run project tests and linters.
2. Update Beads issues.
3. Perform a `/reflect` (or use `reflect_assistant.py`) to capture learnings.
4. `bd sync` and `git push`.

Refer to `~/.gemini/GLOBAL_INDEX.md` for the system map.
