# 🤖 .agent - Primary Agent Interface

**Purpose**: Main entry point for all agent coordination, skills, and documentation in the LightRAG workspace.

## 🚀 Quick Start

**For Agents New to This Workspace:**
1. Read [Global Standards](GLOBAL/standards/) for system-wide rules
2. Check [Current Tasks](workspace/docs/workspace/TODO.md) for available work
3. Use [Skills Directory](../docs/navigation/SKILL_DIRECTORY.md) to find capabilities

**Immediate Navigation:**
- [📋 Current Tasks](workspace/docs/workspace/TODO.md) - What needs to be done
- [🗺️ Global Index](GLOBAL/index/GLOBAL_INDEX.md) - All documentation
- [🔧 Troubleshooting](docs/troubleshooting/) - Common issues and solutions
- [📚 Skills](skills/) - Available agent capabilities

## 📁 Directory Structure

### 🌐 Global Standards ([GLOBAL/](GLOBAL/))
- **[standards/](GLOBAL/standards/)** - System-wide rules and protocols
  - [GEMINI.md](GLOBAL/standards/GEMINI.md) - Global agent rules
  - [AGENT_ONBOARDING.md](GLOBAL/standards/AGENT_ONBOARDING.md) - Onboarding guide
  - [HOW_TO_USE_BEADS.md](GLOBAL/standards/HOW_TO_USE_BEADS.md) - Task management
  - [MISSION_NOMENCLATURE.md](GLOBAL/standards/MISSION_NOMENCLATURE.md) - Terms & definitions
- **[index/](GLOBAL/index/)** - Master documentation index
- **[sop/](GLOBAL/sop/)** - Standard operating procedures

### 🏗️ Workspace Coordination ([workspace/](workspace/))
- **[docs/](workspace/docs/)** - Workspace-specific documentation
  - [TODO.md](workspace/docs/workspace/TODO.md) - Current tasks and backlog
- **[skills/](skills/)** - Workspace-specific skills
- **[config/](config/)** - Workspace configuration

### 🔧 Agent Operations
- **[scripts/](scripts/)** - Coordination and automation scripts
- **[session_locks/](session_locks/)** - Multi-agent session management
- **[rules/](rules/)** - Project roadmaps and rules

## 🤝 Multi-Agent Coordination

### Session Management
```bash
# Start a session (always do this first)
./scripts/agent-start.sh --task-id <issue-id> --task-desc "Brief description"

# Check who's working
./scripts/agent-status.sh

# End your session
./scripts/agent-end.sh
```

### Task Management
```bash
# See available tasks
bd ready

# Close completed task
bd close <issue-id> -r "Done"
```

## 📚 Documentation Navigation

**Layered Documentation System:**
1. **[Quick Reference](../docs/quick/)** - One-page summaries (50 lines max)
2. **[Standard Documentation](../docs/standard/)** - Complete guides (500 lines max)
3. **[Detailed Content](../docs/detailed/)** - In-depth specifications (no limit)

**Navigation Guides:**
- [🗺️ Quick Start](../docs/navigation/QUICK_START.md) - How to find anything
- [🎯 Skill Directory](../docs/navigation/SKILL_DIRECTORY.md) - Skills by category
- [🔍 Troubleshooting Map](../docs/navigation/TROUBLESHOOTING_MAP.md) - Decision trees

## 🗃️ Archive Access

**Historical Content:**
- [Benchmarks](../archive/benchmarks/) - Performance benchmarks and results
- [Audits](../archive/audits/) - Audit results and reports
- [Profiling](../archive/profiling/) - Model profiling history
- [Legacy](../archive/legacy/) - Archived documentation

## ⚡ Progressive Disclosure

**Context Optimization Rules:**
1. **Quick tasks**: Load only `docs/quick/` + relevant skill overview
2. **Standard tasks**: Add `docs/standard/` sections as needed
3. **Deep research**: Access `docs/detailed/` for specific questions

**File Size Guidelines:**
- Quick: < 50 lines, 1-2 minutes read
- Standard: < 500 lines, 5-10 minutes read
- Detailed: No limit, reference as needed

## 🔄 Integration with Global System

**Single Source of Truth:**
- `.agent/` is primary interface for workspace agents
- `~/.gemini/` provides global standards (linked from .agent)
- All documentation reachable from [GLOBAL_INDEX.md](GLOBAL/index/GLOBAL_INDEX.md)

**Backward Compatibility:**
- Symlinks maintain existing references
- Global content available in both locations
- Migration path documented for existing workflows

---

**💡 Tips for Agents:**
- Always start here before diving into specific tasks
- Use the layered documentation to manage context efficiently
- Check session locks before starting new work
- Update TODO.md when identifying new tasks or issues

**🛠️ For the Librarian:**
- This structure enables progressive disclosure
- Archive keeps root directory clean while preserving history
- Navigation guides reduce context overwhelm
- Single interface eliminates .gemini/.agent confusion
