# Mission Nomenclature Reference

This document serves as a glossary and conceptual guide for the aviation metaphors used in the **Standard Mission Protocol (SMP)** and broader system operations.

## Glossary of Terms

- **PFC (Pre-Flight Checklist)**: Initialization and safety checks before starting a mission.
- **IFO (In Flight Operations)**: The core execution loop of the mission.
- **RTB (Return To Base)**: Final verification, cleanup, and handoff.
- **SMP (Standard Mission Protocol)**: The entire process from PFC to RTB.
- **WTU (Wrap This Up)**: Trigger to audit the SMP and ensure all steps are complete before ending the session.

## Mission Context

- **Air Tasking Order (ATO)**: The Roadmap / Backlog / Daily Operations List.
- **Mission**: A Single Agent Session (The "Sortie" concept).
  - *Context*: One operational cycle (Start -> PFC -> IFO -> RTB -> Stop).
- **Mission Profile**: The Implementation Plan / Technical Plan.
- **Formation**: Multi-Agent / User-Agent Collaboration.

## Special Mission Types (CAP)

- **Combat Air Patrol (CAP)**: Defensive missions.
  - *BARCAP (Barrier CAP)*: Setting up linting/type-checking gates.
  - *MiGCAP*: Active debugging/hunting specific bugs.
- **Angel Flight**: Specific helpful tasks or "good samaritan" cleanups.
- **Parabolic Flight**: Scientific research or spikes.

## Usage

- "What is today's **ATO**?" (What are we doing today?)
- "Starting **Mission** for issue #123." (Starting a session)
- "Define the **Mission Profile**." (Create the plan)
- "Beginning **PFC**." (Starting checks)
- "Running a **BARCAP** mission." (setting up tests)
- "**WTU** - let's **RTB**." (Audit and finish)
