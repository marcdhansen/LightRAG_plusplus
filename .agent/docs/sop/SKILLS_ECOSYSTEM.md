# 🧠 Skills Ecosystem Guide

**Purpose**: Complete documentation of the LightRAG skills system and access points.
**Target**: Advanced users needing comprehensive skills understanding.
**Ecosystem Tier**: Tier 2 - Detailed Guide (separate ecosystem document)

---

## 🌐 **Skills Symlink Ecosystem**

### **Source of Truth**
```
~/.gemini/antigravity/skills/  ← Universal Global Skills Repository
```

### **Access Points (Symlinks)**
```
Project Access:      .agent/skills/ → ~/.gemini/antigravity/skills/
OpenCode Global:     ~/.config/opencode/skills/ → ~/.gemini/antigravity/skills/
Claude Compatible:   ~/.claude/skills/ → ~/.gemini/antigravity/skills/ (legacy)
```

### **Why This Structure?**
- **Prevents Breakage**: Antigravity breaks if `~/.gemini` contains symlinks
- **Single Source**: Global skills maintained in one location
- **Multi-Tool Access**: Different IDEs/tools access same skills via symlinks
- **Cross-Agent Compatibility**: All agents use same skill definitions

---

## 🛠️ **Available Skills (Complete Catalog)**

### **🔍 Core Skills**

#### **`reflect/` - Session Reflection & Learning**
**Purpose**: Capture session learnings to prevent repeating mistakes
**Usage**: End-of-session analysis and continuous improvement

**Structure**:
```
reflect/
├── SKILL.md           # Main documentation
└── scripts/           # Analysis scripts (optional)
```

**Key Features**:
- Analyzes conversation history
- Extracts user preferences and corrections
- Updates SKILL.md files with learnings
- Prevents repeated anti-patterns

**When to Use**:
- End of work session (mandated by RTB)
- After encountering significant problems
- When discovering new workflows
- After user corrections or preferences

---

#### **`return-to-base/` - RTB Procedures**
**Purpose**: Complete Return To Base workflow with validation
**Usage**: End-of-session validation and cleanup

**Structure**:
```
return-to-base/
├── SKILL.md           # RTB procedures
└── scripts/           # Validation scripts
```

**Key Features**:
- Validates git status and commits
- Runs quality gates (linters, tests)
- Checks markdown integrity
- Completes session workflow

**Critical Validation Points**:
- All changes committed and pushed
- Quality gates passed
- No broken symlinks
- Documentation updated

---

#### **`show-next-task/` - Task Discovery**
**Purpose**: Discover available tasks and current priorities
**Usage**: Task assignment and workflow navigation

**Structure**:
```
show-next-task/
├── SKILL.md           # Task discovery logic
└── scripts/           # Integration with beads
```

**Key Features**:
- Integrates with `bd ready` command
- Analyzes project roadmap
- Prioritizes tasks by dependencies
- Provides task context and requirements

---

### **⚙️ System Skills**

#### **`openviking/` - Enhanced Agent System**
**Purpose**: OpenViking enhanced agent capabilities
**Usage**: Advanced agent operations and optimization

**Structure**:
```
openviking/
├── SKILL.md           # OpenViking documentation
├── scripts/           # Agent management
└── config/            # Configuration files
```

**Key Features**:
- Token efficiency optimization
- Conversation memory management
- Integration with LightRAG on port :9622
- API endpoint management

---

#### **`process/` - Process Management**
**Purpose**: Workflow and process automation
**Usage**: Complex workflow coordination

**Structure**:
```
process/
├── SKILL.md           # Process documentation
└── scripts/           # Automation scripts
```

**Key Features**:
- Workflow orchestration
- Multi-step process automation
- Integration with external tools
- Error handling and recovery

---

### **🧪 Development Skills**

#### **`testing/` - Testing Protocols**
**Purpose**: Comprehensive testing strategies
**Usage**: Test planning, execution, and validation

**Structure**:
```
testing/
├── SKILL.md           # Testing methodology
├── scripts/           # Test utilities
└── templates/         # Test templates
```

**Key Features**:
- TDD gate enforcement
- Test coverage analysis
- Performance benchmarking
- Cross-platform testing

---

#### **`ui/` - UI Operations**
**Purpose**: User interface testing and validation
**Usage**: Frontend testing and browser automation

**Structure**:
```
ui/
├── SKILL.md           # UI testing documentation
└── scripts/           # Browser automation
```

**Key Features**:
- Playwright integration
- Cross-browser testing
- UI validation workflows
- Screenshot comparison

---

## 🔧 **Skill Usage Patterns**

### **Basic Skill Invocation**
```bash
# Pattern depends on tool/agent implementation
/skill <skill-name>

# Examples:
/skill reflect
/skill return-to-base
/skill show-next-task
```

### **Advanced Skill Usage**
```bash
# With parameters
/skill reflect --session-type "development"

# With context
/skill show-next-task --priority "high"

# Chain skills
/skill show-next-task && /skill reflect
```

### **Skill Development**
```bash
# Create new skill in global location
mkdir ~/.gemini/antigravity/skills/my-skill
echo "# My Skill\n..." > ~/.gemini/antigravity/skills/my-skill/SKILL.md
```

---

## 🔗 **Cross-Tool Integration**

### **OpenCode Integration**
```bash
# Skills accessible through OpenCode configuration
ls ~/.config/opencode/skills/  # → symlinked to global skills

# Usage in OpenCode context
opencode --skill reflect
```

### **Antigravity Integration**
```bash
# Skills accessible through Antigravity agent system
ls .agent/skills/  # → symlinked to global skills

# Usage in Antigravity context
/reflect  # directly available
```

### **Claude Integration (Legacy)**
```bash
# Skills accessible through Claude-compatible structure
ls ~/.claude/skills/  # → symlinked to global skills
```

---

## 🔧 **Skill Management**

### **Adding New Skills**
1. **Create Skill Directory**:
   ```bash
   mkdir ~/.gemini/antigravity/skills/new-skill
   ```

2. **Create SKILL.md**:
   ```markdown
   # New Skill

   **Purpose**: Brief description
   **Usage**: How to invoke
   **Structure**: Directory layout
   ```

3. **Add Scripts (Optional)**:
   ```bash
   mkdir ~/.gemini/antigravity/skills/new-skill/scripts
   # Add automation scripts
   ```

4. **Test Symlinks**:
   ```bash
   ls -la .agent/skills/new-skill/  # Should resolve
   ```

### **Updating Skills**
1. **Edit in Source of Truth**:
   ```bash
   vim ~/.gemini/antigravity/skills/existing-skill/SKILL.md
   ```

2. **Verify Access Points**:
   ```bash
   readlink .agent/skills/existing-skill/SKILL.md
   readlink ~/.config/opencode/skills/existing-skill/SKILL.md
   ```

3. **Test Functionality**:
   ```bash
   /skill existing-skill  # Test updated skill
   ```

---

## 🚨 **Troubleshooting**

### **Broken Symlinks**
```bash
# Check all skill access points
ls -la .agent/skills/
ls -la ~/.config/opencode/skills/
ls -la ~/.claude/skills/

# Fix broken project symlink
rm .agent/skills
ln -s ~/.gemini/antigravity/skills/ .agent/skills/

# Fix broken OpenCode symlink
rm ~/.config/opencode/skills
ln -s ~/.gemini/antigravity/skills/ ~/.config/opencode/skills/
```

### **Skill Not Found**
```bash
# Verify skill exists in global location
ls ~/.gemini/antigravity/skills/

# Check symlink resolution
readlink .agent/skills/skill-name

# Recreate missing symlinks
./scripts/setup-skill-symlinks.sh
```

### **Permission Issues**
```bash
# Check permissions on global skills
ls -la ~/.gemini/antigravity/skills/

# Fix permissions if needed
chmod -R 755 ~/.gemini/antigravity/skills/
```

### **Skill Functionality Issues**
```bash
# Test skill directly
python ~/.gemini/antigravity/skills/skill-name/scripts/test.py

# Check skill documentation
cat ~/.gemini/antigravity/skills/skill-name/SKILL.md

# Verify dependencies
pip install -r ~/.gemini/antigravity/skills/skill-name/requirements.txt
```

---

## 📊 **Skill Ecosystem Health**

### **Validation Commands**
```bash
# Validate all skill symlinks
python ~/.agent/scripts/validate_skill_symlinks.py

# Check skill documentation integrity
python ~/.agent/scripts/validate_skill_docs.py

# Test skill functionality
python ~/.agent/scripts/test_all_skills.py
```

### **Health Monitoring**
```bash
# Regular health check (included in RTB)
./scripts/validate-skills.sh

# Detailed ecosystem report
./scripts/skills-ecosystem-report.sh
```

---

## 📚 **Related Documentation**

### **Tier Navigation**
- **⬆️ Up**: [**Quick Reference**](../workspace/QUICK_REFERENCE.md) - Daily essential skills
- **⬆️ Up**: [**Complete Symlink Ecosystem**](./COMPLETE_SYMLINK_ECOSYSTEM.md) - Technical reference
- **↔️ Related**: [**Commands Ecosystem Guide**](./COMMANDS_ECOSYSTEM.md) - Slash commands and workflows

### **Project Integration**
- **[Project Roadmap](../../rules/ROADMAP.md)** - Current project objectives
- **[Implementation Plan](../../rules/ImplementationPlan.md)** - Technical execution plan
- **[SOP Validation](./SOP_CONSISTENCY_VALIDATION.md)** - Compliance validation

---

**Last Updated**: 2026-02-03
**Part of**: LightRAG Three-Tier Documentation System (Tier 2 - Skills Ecosystem)
**Scope**: Universal Skills Documentation (cross-project compatibility)
