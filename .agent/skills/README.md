# Local Skills Access Point

This directory provides project-level access to global skills through the symlink ecosystem.

## 🔗 **Source of Truth**
**Global Skills Location**: `~/.gemini/antigravity/skills/`

## 📁 **Symlink Structure**
```
.agent/skills/ → ~/.gemini/antigravity/skills/
```

## 🛠️ **Available Skills**

→ See [**Skills Ecosystem Guide**](../docs/sop/SKILLS_ECOSYSTEM.md) for complete documentation

### **Quick Reference**
- **`reflect`** - Session reflection and learning capture
- **`return-to-base`** - RTB procedures and validation
- **`show-next-task`** - Task discovery and assignment
- **`openviking`** - Enhanced agent system
- **`process`** - Process management
- **`testing`** - Testing protocols
- **`ui`** - UI operations

## 🚀 **Usage Examples**

### **Load a Skill**
```bash
# Using the skill system (depends on tool/agent)
/skill reflect
/skill return-to-base
```

### **Skill Documentation**
Each skill directory contains:
- `SKILL.md` - Main skill documentation
- `scripts/` - Optional automation scripts
- `examples/` - Usage examples (if available)

## 🔧 **Troubleshooting**

### **Broken Symlink**
If this README appears inaccessible:
```bash
# Verify symlink integrity
ls -la .agent/skills/

# Recreate if necessary
rm .agent/skills
ln -s ~/.gemini/antigravity/skills/ .agent/skills/
```

### **Access Issues**
For detailed troubleshooting, see [**Skills Ecosystem Guide**](../docs/sop/SKILLS_ECOSYSTEM.md#troubleshooting).

---

**Last Updated**: 2026-02-03  
**Part of**: LightRAG Symlink Ecosystem