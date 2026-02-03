# ⚡ Commands & Workflows Ecosystem Guide

**Purpose**: Complete documentation of LightRAG slash commands and workflow system.  
**Target**: Advanced users needing comprehensive command understanding.  
**Ecosystem Tier**: Tier 2 - Detailed Guide (separate ecosystem document)

---

## 🌐 **Commands Symlink Ecosystem**

### **Source of Truth**
```
~/.gemini/antigravity/global_workflows/  ← Universal Global Workflows Repository
```

### **Access Points (Symlinks)**
```
Global Agent Access:  ~/.agent/commands/ → ~/.gemini/antigravity/global_workflows/
OpenCode Global:     ~/.config/opencode/commands/ → ~/.gemini/antigravity/global_workflows/
Workspace-Specific:  .agent/workflows/ → Project-local workflows (managed locally)
Legacy OpenCode:     ~/.opencode/commands/ → Legacy access (if exists)
Project OpenCode:    .opencode/commands/ → Project-specific commands (if exists)
```

### **Why This Structure?**
- **Prevents Breakage**: Antigravity breaks if `~/.gemini` contains symlinks
- **Single Source**: Global workflows maintained in one location  
- **Multi-Tool Access**: Different IDEs/tools access same commands via symlinks
- **Workspace Flexibility**: Projects can have local workflow customizations

---

## 📁 **Command System Architecture**

### **Global Workflows (Universal)**
```bash
~/.gemini/antigravity/global_workflows/
├── rtb.md              # Return To Base workflow
├── next.md             # Task discovery workflow  
├── reflect.md          # Session reflection workflow
└── [other-workflows].md # Additional global workflows
```

### **Workspace Workflows (Project-Specific)**
```bash
.agent/workflows/
├── rtb.md              # Project-local RTB customizations (→ global)
├── next.md             # Project-local task discovery (→ global)
└── [project-specific].md # Project-only workflows
```

### **Tool-Specific Access**
```bash
# OpenCode Global Access
~/.config/opencode/commands/
├── rtb.md → ~/.gemini/antigravity/global_workflows/rtb.md
├── next.md → ~/.gemini/antigravity/global_workflows/next.md
└── reflect.md → ~/.gemini/antigravity/global_workflows/reflect.md

# Agent Global Access  
~/.agent/commands/
├── rtb.md → ~/.gemini/antigravity/global_workflows/rtb.md
├── next.md → ~/.gemini/antigravity/global_workflows/next.md
└── reflect.md → ~/.gemini/antigravity/global_workflows/reflect.md
```

---

## ⚡ **Available Commands (Complete Catalog)**

### **🛬 Core System Commands**

#### **`/rtb` - Return To Base**
**Purpose**: Complete Return To Base workflow with validation  
**Usage**: End-of-session validation and cleanup (MANDATORY)

**Access Points**:
```bash
/rtb                    # Direct invocation
# Available through all access points
```

**Workflow Structure**:
```markdown
---
description: Complete Return To Base workflow
agent: any
model: any
---

1. Validate git status and commits
2. Run quality gates (linters, tests)  
3. Check markdown integrity
4. Complete session workflow
5. Push changes and cleanup
```

**Key Features**:
- Validates git repository status
- Runs project-specific quality gates
- Checks for broken symlinks
- Ensures proper session completion
- Blocks completion if validation fails

**Critical Validation**:
- All changes committed and pushed
- Quality gates passed
- No broken symlinks detected
- Documentation integrity maintained

---

#### **`/next` - Task Discovery**
**Purpose**: Discover available tasks and current priorities  
**Usage**: Task assignment and workflow navigation

**Access Points**:
```bash
/next                   # Direct invocation
# Available through all access points
```

**Workflow Structure**:
```markdown
---
description: Task discovery and assignment
agent: any  
model: any
---

1. Query beads task system
2. Analyze project roadmap
3. Prioritize by dependencies
4. Present task options
5. Provide context and requirements
```

**Key Features**:
- Integrates with `bd ready` command
- Analyzes project roadmap and implementation plan
- Prioritizes tasks based on dependencies
- Provides detailed task context
- Suggests optimal next steps

---

#### **`/reflect` - Session Reflection**
**Purpose**: Capture session learnings and continuous improvement  
**Usage**: End-of-session analysis and learning capture

**Access Points**:
```bash
/reflect                # Direct invocation  
# Available through all access points
```

**Workflow Structure**:
```markdown
---
description: Session reflection and learning capture
agent: any
model: any
---

1. Analyze conversation history
2. Extract user preferences and corrections
3. Identify successful patterns
4. Update relevant SKILL.md files
5. Prevent repeated anti-patterns
```

**Key Features**:
- Analyzes conversation for learning opportunities
- Captures user preferences and corrections
- Updates skill documentation automatically
- Identifies process improvements
- Prevents repeating mistakes

---

### **🔧 Development Commands**

#### **`/test` - Test Execution**
**Purpose**: Comprehensive test execution and reporting  
**Usage**: Run tests with coverage and validation

**Access Points**:
```bash
/test                   # Run full test suite
/test unit             # Run unit tests only
/test integration      # Run integration tests
/test coverage         # Run with coverage report
```

**Workflow Structure**:
```markdown
---
description: Comprehensive test execution
agent: build
model: any
---

1. Run unit tests with coverage
2. Execute integration tests
3. Validate performance benchmarks
4. Generate test report
5. Check quality metrics
```

---

#### **`/build` - Build System**
**Purpose**: Build and package the project  
**Usage**: Compile, bundle, and validate build

**Access Points**:
```bash
build                   # Standard build
build release          # Release build
build debug            # Debug build
build clean            # Clean build artifacts
```

**Workflow Structure**:
```markdown
---
description: Project build and packaging
agent: build  
model: any
---

1. Clean previous build artifacts
2. Compile source code
3. Run build-time tests
4. Package artifacts
5. Validate build integrity
```

---

#### **`/lint` - Code Quality**
**Purpose**: Run linting and code quality checks  
**Usage**: Validate code style and quality standards

**Access Points**:
```bash
/lint                   # Run all linters
/lint fix              # Auto-fix issues where possible
/lint check            # Check without fixing
```

**Workflow Structure**:
```markdown
---
description: Code quality and style validation
agent: build
model: any
---

1. Run style linters (ruff, eslint, etc.)
2. Check type annotations
3. Validate security patterns
4. Auto-fix where possible
5. Report remaining issues
```

---

### **📊 Project Management Commands**

#### **`/status` - Project Status**
**Purpose**: Show current project status and health  
**Usage**: Quick project overview and health check

**Access Points**:
```bash
/status                 # Full project status
/status quick          # Quick overview
/status health         # Health check only
```

**Workflow Structure**:
```markdown
---
description: Project status and health overview
agent: any
model: any
---

1. Check git repository status
2. Query task system (bd ready)
3. Validate symlink ecosystem
4. Check build and test status
5. Generate status report
```

---

#### **`/plan` - Planning Mode**
**Purpose**: Enter planning mode for new features  
**Usage**: Structured planning and specification

**Access Points**:
```bash
/plan feature-name     # Plan new feature
/plan task-id         # Plan specific task
/plan review          # Review current plan
```

**Workflow Structure**:
```markdown
---
description: Structured planning and specification
agent: planning
model: any
---

1. Load project context and constraints
2. Analyze requirements and dependencies
3. Create detailed specification
4. Design implementation approach
5. Generate task breakdown
```

---

## 🔧 **Command Usage Patterns**

### **Basic Command Invocation**
```bash
# Direct slash command
/rtb
/next
/reflect

# With parameters  
/test coverage
/build release
/lint fix
```

### **Advanced Command Usage**
```bash
# Chain commands
/status && /next

# With specific targets
/lint --file src/main.py
/test --module authentication

# Conditional execution
/build && /test && /lint
```

### **Interactive Commands**
```bash
# Interactive task selection
/next --interactive

# Interactive problem resolution
/status --troubleshoot
```

---

## 🔗 **Tool-Specific Integration**

### **OpenCode Integration**
```bash
# Commands through OpenCode configuration
ls ~/.config/opencode/commands/  # → symlinked to global workflows

# Usage in OpenCode CLI
opencode command /rtb
opencode command /next
opencode command /reflect
```

**File Structure**:
```yaml
# ~/.config/opencode/commands/rtb.md
---
description: Complete Return To Base workflow
agent: any
model: any
---
# Workflow content...
```

### **Antigravity Integration**
```bash
# Commands through Antigravity agent system
ls .agent/workflows/  # → workspace-specific workflows

# Usage in Antigravity context
/rtb    # Direct availability
/next   # Direct availability  
/reflect # Direct availability
```

**File Structure**:
```yaml
# .agent/workflows/rtb.md (→ global)
---
description: Complete Return To Base workflow  
agent: any
model: any
---
# Workflow content...
```

### **Universal Agent Integration**
```bash
# Commands through universal agent system
ls ~/.agent/commands/  # → global workflows

# Usage in universal agent context
/rtb    # Available to all agents
/next   # Available to all agents
/reflect # Available to all agents
```

---

## 🔧 **Command Management**

### **Creating New Commands**

#### **Global Commands**
1. **Create Command File**:
   ```bash
   touch ~/.gemini/antigravity/global_workflows/my-command.md
   ```

2. **Add Command Structure**:
   ```yaml
   ---
   description: Brief command description
   agent: appropriate-agent-type
   model: any/specific-model
   ---
   
   # Command workflow steps
   1. Step one
   2. Step two
   3. Step three
   ```

3. **Test All Access Points**:
   ```bash
   ls -la ~/.agent/commands/my-command.md
   ls -la ~/.config/opencode/commands/my-command.md
   ```

#### **Workspace-Specific Commands**
1. **Create Local Command**:
   ```bash
   touch .agent/workflows/project-command.md
   ```

2. **Add Project-Specific Logic**:
   ```yaml
   ---
   description: Project-specific command
   agent: any
   model: any
   ---
   
   # Project-specific workflow
   1. Project step one
   2. Project step two
   ```

### **Updating Commands**
1. **Edit in Source Location**:
   ```bash
   # Global commands
   vim ~/.gemini/antigravity/global_workflows/existing-command.md
   
   # Workspace commands  
   vim .agent/workflows/project-command.md
   ```

2. **Verify Access Points**:
   ```bash
   # Test symlinks resolve correctly
   readlink ~/.agent/commands/existing-command.md
   readlink ~/.config/opencode/commands/existing-command.md
   ```

3. **Test Functionality**:
   ```bash
   /existing-command  # Test updated command
   ```

---

## 🚨 **Troubleshooting**

### **Broken Command Symlinks**
```bash
# Check all command access points
ls -la ~/.agent/commands/
ls -la ~/.config/opencode/commands/  
ls -la .agent/workflows/

# Fix broken agent global symlink
rm ~/.agent/commands
ln -s ~/.gemini/antigravity/global_workflows/ ~/.agent/commands/

# Fix broken OpenCode global symlink
rm ~/.config/opencode/commands
ln -s ~/.gemini/antigravity/global_workflows/ ~/.config/opencode/commands/
```

### **Command Not Found**
```bash
# Verify command exists in global location
ls ~/.gemini/antigravity/global_workflows/

# Check symlink resolution
readlink ~/.agent/commands/command-name
readlink ~/.config/opencode/commands/command-name

# Check workspace-specific commands
ls .agent/workflows/
```

### **Command Execution Issues**
```bash
# Test command directly
cat ~/.gemini/antigravity/global_workflows/command-name.md

# Check YAML frontmatter validity
python -c "import yaml; yaml.safe_load(open('~/.gemini/antigravity/global_workflows/command-name.md'))"

# Test in isolation
/rtb --dry-run  # If command supports dry-run mode
```

### **Workspace vs Global Conflicts**
```bash
# Check for shadowing commands
ls -la .agent/workflows/command-name
ls -la ~/.agent/commands/command-name

# Prioritization: workspace > global
# To use global version explicitly:
/global/command-name
```

---

## 📊 **Command Ecosystem Health**

### **Validation Commands**
```bash
# Validate all command symlinks
python ~/.agent/scripts/validate_command_symlinks.py

# Check command documentation integrity
python ~/.agent/scripts/validate_command_docs.py

# Test command functionality
python ~/.agent/scripts/test_all_commands.py
```

### **Health Monitoring**
```bash
# Regular health check (included in RTB)
./scripts/validate-commands.sh

# Detailed ecosystem report
./scripts/commands-ecosystem-report.sh

# Performance benchmarking
./scripts/benchmark-commands.sh
```

---

## 🔗 **Cross-Reference Integration**

### **Skills ↔ Commands Integration**
```bash
# Skills that invoke commands
/skill show-next-task  # May use /next internally

# Commands that use skills
/rtb                   # May invoke /skill reflect
/reflect               # Skill system integration
```

### **Task System Integration**
```bash
# Commands that interact with beads
/next                  # Queries bd ready
/status                # Checks bd status
/plan                  # Creates bd tasks
```

---

## 📚 **Related Documentation**

### **Tier Navigation**
- **⬆️ Up**: [**Quick Reference**](../workspace/QUICK_REFERENCE.md) - Daily essential commands
- **⬆️ Up**: [**Complete Symlink Ecosystem**](./COMPLETE_SYMLINK_ECOSYSTEM.md) - Technical reference
- **↔️ Related**: [**Skills Ecosystem Guide**](./SKILLS_ECOSYSTEM.md) - Skills and capabilities

### **Project Integration**  
- **[Project Roadmap](../../rules/ROADMAP.md)** - Current project objectives
- **[Implementation Plan](../../rules/ImplementationPlan.md)** - Technical execution plan
- **[SOP Validation](./SOP_CONSISTENCY_VALIDATION.md)** - Compliance validation

---

**Last Updated**: 2026-02-03  
**Part of**: LightRAG Three-Tier Documentation System (Tier 2 - Commands Ecosystem)  
**Scope**: Universal Commands Documentation (cross-project compatibility)