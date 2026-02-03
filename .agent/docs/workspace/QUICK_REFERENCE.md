# 🚀 LightRAG Quick Reference

**Purpose**: Essential skills and commands for daily productive work.  
**Target**: Immediate access to most commonly used capabilities.

---

## 🛠️ **Essential Skills (Daily Use)**

### **🧠 `/reflect` - Session Learning**
**Use When**: Ending work session or encountering new patterns  
**Purpose**: Capture learnings to prevent repeating mistakes

```bash
/reflect
```

### **🛬 `/rtb` - Return To Base** 
**Use When**: Finishing work (MANDATORY)  
**Purpose**: Complete session workflow with validation

```bash
/rtb
```

### **📋 `/next` - Task Discovery**
**Use When**: Starting work or needing next objective  
**Purpose**: Find available tasks and current priorities

```bash
/next
```

---

## ⚡ **Quick Workflows**

### **Start Work Session**
```bash
# 1. Discover tasks
/next

# 2. Start with highest priority task
bd ready

# 3. Work on task...
# (your implementation here)
```

### **End Work Session**  
```bash
# 1. Complete work
# (finish coding, testing, etc.)

# 2. Capture learnings
/reflect

# 3. Complete session validation
/rtb
```

### **When Stuck**
```bash
# Get next task or guidance
/next

# Capture what you learned from the problem
/reflect
```

---

## 🔧 **Tool-Specific Access**

### **Antigravity (Google AI IDE)**
- **Skills**: Available through agent skill system
- **Commands**: `/rtb`, `/reflect`, `/next`
- **Workflows**: Global + workspace-specific

### **OpenCode (Universal CLI)**
- **Skills**: `~/.config/opencode/skills/` → global skills
- **Commands**: `~/.config/opencode/commands/` → global workflows
- **Project**: `.opencode/commands/` for project-specific

---

## 📁 **Key File Locations**

### **Project Planning**
- `.agent/rules/ROADMAP.md` - Project roadmap
- `.agent/rules/ImplementationPlan.md` - Technical plan
- `task.md` - Current task details

### **Task Management**
```bash
bd ready          # Show available tasks
bd sync           # Save task state
bd close <id>     # Mark task complete
```

### **Session Management**
```bash
./scripts/agent-start.sh --task-id <id> --task-desc "description"
./scripts/agent-end.sh
```

---

## 🚨 **Critical Rules**

### **Mandatory Session End**
1. **Run `/reflect`** - Capture session learnings
2. **Run `/rtb`** - Complete validation workflow
3. **Never stop early** - Work incomplete until RTB succeeds

### **Task Management**
1. **Always have task ID** - Every action needs `bd` task
2. **Use `bd ready`** - See what needs doing
3. **Sync before ending** - `bd sync` before `/rtb`

### **Quality Gates**
- **Code changes** → Run linters/tests first
- **UI changes** → Verify in browser before ending
- **Documentation** → Check links and formatting

---

## 🆘 **Quick Troubleshooting**

### **Broken Skills/Commands**
```bash
# Check symlink integrity
ls -la .agent/skills/
ls -la ~/.config/opencode/skills/
ls -la ~/.config/opencode/commands/

# Fix if needed (see detailed guides)
```

### **RTB Validation Fails**
```bash
# Check for broken symlinks
python ~/.agent/scripts/validate_sop_consistency.py

# Common fixes:
bd sync           # Update task state
git status        # Check for uncommitted changes
```

### **Task Issues**
```bash
# Refresh task state
bd doctor --fix
bd sync
bd ready
```

---

## 📚 **Need More Detail?**

→ **[Skills Ecosystem Guide](./sop/SKILLS_ECOSYSTEM.md)** - Complete skills documentation  
→ **[Commands Ecosystem Guide](./sop/COMMANDS_ECOSYSTEM.md)** - Complete command reference  
→ **[Complete Symlink Ecosystem](./sop/COMPLETE_SYMLINK_ECOSYSTEM.md)** - Technical reference  

---

**Last Updated**: 2026-02-03  
**Part of**: LightRAG Three-Tier Documentation System (Tier 1 - Quick Reference)