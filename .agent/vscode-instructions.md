# 💻 VS Code Agent Bridge: Standard Mission Protocol (SMP)

To ensure consistency across VS Code extensions (Roo Code, Cursor, Copilot), please follow these standards:

## 🧭 Navigation

- The **Global Index** is at `~/.gemini/GLOBAL_INDEX.md`.
- Project status is in `.agent/rules/ROADMAP.md`.

## 🛠️ Tooling

- **MANDATORY**: Use the terminal to run `./scripts/agent-init.sh` at the start of a session.
- **Task Tracking**: Do not use `TODO` comments. Use `bd` (Beads) for all task management.
- **Paths**: Use **Relative Paths** in all documentation. Do not use absolute paths starting with `/Users/`.

## 🚀 Mission Loop

A session is only complete after running the **Return To Base (RTB)** check:

```bash
python ~/.gemini/antigravity/skills/flight-director/scripts/check_flight_readiness.py --rtb
```

If you encounter permission errors in `~/.gemini`, please refer to the troubleshooting section in `~/.gemini/CROSS_COMPATIBILITY.md`.
