# Task: Update 'reflect' skill to include standard mission processes (lightrag-982)

## Status: IN_PROGRESS

### Objective

Update the `reflect` skill to formalize the analysis of PFC/RTB checks, logs, and user feedback as part of the self-evolution loop. This ensures that process improvements and mission-specific learnings are captured and applied systematically.

### Tasks

- [x] **Analyze**: Review `FlightDirector/SKILL.md` and `GEMINI.md` for required mission outputs.
- [x] **Define**: Create a structured "Mission Reflection" template within `Reflect/SKILL.md`.
- [x] **Enhance**: Update the `Workflow` in `Reflect/SKILL.md` to include PFC/RTB analysis and cross-session debriefing.
- [x] **Debrief**: Implement the "Post-Mission Debrief" generation step.
- [x] **Verify**: Ensure the updated skill aligns with the Standard Mission Protocol (SMP).
- [x] **Suggest (Lrag-983)**: Propose script-based discovery and conflict detection.
- [x] **Infrastructure**: Create `scripts/reflect_assistant.py` stub for automated memory discovery.
- [ ] **Versioning (Lrag-985)**: Implement git-based rollback mechanism for skill files.

### Steps

1. [x] Run PFC and identify current objective (`lightrag-982`).
2. [x] Analyze `Reflect/SKILL.md` and identify gaps in mission diagnostic integration.
3. [x] Propose updates to `Reflect/SKILL.md`.
4. [x] Apply updates to `Reflect/SKILL.md`.
5. [x] Update `ImplementationPlan.md` and `ROADMAP.md`.
6. [ ] Perform RTB and final debrief.
