# Standard Operating Procedures (SOP)

This directory contains standard operating procedures and protocols for agents working on the LightRAG project.

## Structure

- **global-configs/** - Global configuration and rules (symbolic links to ~/.agent/)
- **skills/** - Agent skills and capabilities (symbolic link to ../.agent/skills/)
- **workspace/** - Workspace-specific documentation and procedures

## 🌐 **Symlink Exception for Skills & Commands**

**Critical Exception**: Skills and slash commands are exceptions to the normal `.agent` source-of-truth rule.

### **Why This Exception?**
- **Prevents Breakage**: Antigravity breaks if `~/.gemini` directory contains symlinks
- **Single Source**: Universal skills and commands maintained in `~/.gemini/antigravity/`
- **Multi-Tool Access**: Different IDEs/tools access same resources via symlinks

### **Skills Ecosystem**
```
Source of Truth:  ~/.gemini/antigravity/skills/
Access Points:
├── .agent/skills/ → ~/.gemini/antigravity/skills/ (Project)
├── ~/.config/opencode/skills/ → ~/.gemini/antigravity/skills/ (OpenCode)
└── ~/.claude/skills/ → ~/.gemini/antigravity/skills/ (Legacy)
```

### **Commands & Workflows Ecosystem**
```
Source of Truth:  ~/.gemini/antigravity/global_workflows/
Access Points:
├── ~/.agent/commands/ → ~/.gemini/antigravity/global_workflows/ (Agent)
├── ~/.config/opencode/commands/ → ~/.gemini/antigravity/global_workflows/ (OpenCode)
└── .agent/workflows/ → Project-specific commands (Local)
```

### **Documentation**
→ **[Quick Reference](../workspace/QUICK_REFERENCE.md)** - Daily essential skills & commands
→ **[Skills Ecosystem Guide](./SKILLS_ECOSYSTEM.md)** - Complete skills documentation
→ **[Commands Ecosystem Guide](./COMMANDS_ECOSYSTEM.md)** - Complete command reference

## Purpose

The SOP directory provides:

1. **Global Standards** - Cross-project protocols and configurations
2. **Agent Skills** - Standardized capabilities and workflows
3. **Workspace Rules** - Project-specific procedures and guidelines

## Usage

All agents must:

1. Read the appropriate SOP documents before starting work
2. Follow established protocols without deviation
3. Update procedures only when necessary and with proper justification
4. Maintain consistency across all work sessions
