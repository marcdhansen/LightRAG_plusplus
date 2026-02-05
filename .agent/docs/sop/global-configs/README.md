# Global Configuration Links

This directory contains symbolic links to the global configuration files and standards maintained in `~/.agent/`.

## Linked Files

- **[GEMINI.md](GEMINI.md)** → `~/.agent/docs/sop/GEMINI.md` - Global Agent Rules (SMP)
- **[COLLABORATION.md](COLLABORATION.md)** → `~/.agent/docs/sop/COLLABORATION.md` - Multi-agent collaboration
- **[AGENT_ONBOARDING.md](AGENT_ONBOARDING.md)** → `~/.agent/docs/sop/AGENT_ONBOARDING.md` - Universal onboarding guide
- **[tdd-workflow.md](tdd-workflow.md)** → `~/.agent/docs/sop/tdd-workflow.md` - Universal TDD workflow
- **[MISSION_NOMENCLATURE.md](MISSION_NOMENCLATURE.md)** → `~/.agent/docs/sop/MISSION_NOMENCLATURE.md` - Universal terminology
- **[SELF_EVOLUTION_GLOBAL.md](SELF_EVOLUTION_GLOBAL.md)** → `~/.agent/docs/sop/SELF_EVOLUTION_GLOBAL.md` - Global self-evolution strategy
- **[CROSS_COMPATIBILITY.md](CROSS_COMPATIBILITY.md)** → `~/.agent/docs/sop/CROSS_COMPATIBILITY.md` - Multi-IDE compatibility
- **[HOW_TO_USE_BEADS.md](HOW_TO_USE_BEADS.md)** → `~/.agent/docs/sop/HOW_TO_USE_BEADS.md` - Beads usage guide

## Linked Directories

- **[skills/](skills/)** → `.agent/skills/` → `~/.gemini/antigravity/skills/` - Global agent capabilities (symlink chain to universal source)

## 🌐 **Skills & Commands Symlink Ecosystem**

**Critical Note**: Skills and commands use a special symlink architecture where `~/.gemini/antigravity/` is the universal source of truth.

### **Skills Access Points**

```
Project Access:      .agent/skills/ → ~/.gemini/antigravity/skills/
OpenCode Global:     ~/.config/opencode/skills/ → ~/.gemini/antigravity/skills/
```

### **Commands & Workflows Access Points**

```
Agent Global:        ~/.agent/commands/ → ~/.gemini/antigravity/global_workflows/
OpenCode Global:     ~/.config/opencode/commands/ → ~/.gemini/antigravity/global_workflows/
Workspace-Specific:  .agent/workflows/ → Project-local commands
```

### **Why This Structure?**

- Prevents Antigravity breakage (symlinks in `~/.gemini` cause failures)
- Maintains single source of truth for universal capabilities
- Enables multi-tool access to same resources
- Preserves cross-agent compatibility

## Purpose

These symbolic links ensure that:

1. **Single Source of Truth** - Global standards are maintained in one location
2. **Automatic Updates** - Changes to global standards immediately reflect in all workspaces
3. **Consistent Access** - Same file paths across all workspaces
4. **Easy Navigation** - Local access to global protocols

## Usage

Agents should:

1. **Read Global Standards** - Access through these local links for convenience
2. **Follow Universal Protocols** - Apply global rules to workspace-specific work
3. **Contribute Back** - Suggest improvements to global standards through proper channels
4. **Maintain Links** - Ensure symbolic links remain functional and up-to-date
