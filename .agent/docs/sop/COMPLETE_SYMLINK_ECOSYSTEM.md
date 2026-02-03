# 🔗 Complete Symlink Ecosystem Reference

**Purpose**: Comprehensive technical reference for LightRAG symlink architecture.  
**Target**: System administrators, advanced troubleshooting, and ecosystem maintenance.  
**Ecosystem Tier**: Tier 3 - Complete Technical Reference

---

## 🏗️ **System Architecture Overview**

### **Core Principle: Symlink Exception**
**Standard Rule**: `.agent/` directory is single source of truth  
**Exception**: Skills and commands use `~/.gemini/antigravity/` as universal source

### **Why This Architecture?**
1. **Prevents Antigravity Breakage**: `~/.gemini` with symlinks causes system failures
2. **Universal Resource Sharing**: Multiple tools access same capabilities  
3. **Cross-Project Compatibility**: Consistent access across all workspaces
4. **Tool-Specific Integration**: Different IDEs have different access patterns

---

## 🌐 **Complete Symlink Map**

### **Skills Ecosystem**
```
~/.gemini/antigravity/skills/                    ← UNIVERSAL SOURCE OF TRUTH
├── reflect/                                     # Session reflection
├── return-to-base/                              # RTB procedures  
├── show-next-task/                              # Task discovery
├── openviking/                                  # Enhanced agent system
├── process/                                     # Process management
├── testing/                                     # Testing protocols
└── ui/                                          # UI operations

↓ SYMLINK ACCESS POINTS ↓

.agent/skills/ → ~/.gemini/antigravity/skills/   # Project-level access
~/.config/opencode/skills/ → ~/.gemini/antigravity/skills/  # OpenCode global
~/.claude/skills/ → ~/.gemini/antigravity/skills/           # Claude legacy
```

### **Commands & Workflows Ecosystem**
```
~/.gemini/antigravity/global_workflows/          ← UNIVERSAL SOURCE OF TRUTH
├── rtb.md                                       # Return To Base
├── next.md                                      # Task discovery
├── reflect.md                                   # Session reflection
└── [additional-commands].md                     # Other global commands

↓ SYMLINK ACCESS POINTS ↓

~/.agent/commands/ → ~/.gemini/antigravity/global_workflows/     # Agent global
~/.config/opencode/commands/ → ~/.gemini/antigravity/global_workflows/  # OpenCode global
.agent/workflows/next.md → ~/.gemini/antigravity/global_workflows/next.md    # Project next
.agent/workflows/rtb.md → ~/.gemini/antigravity/global_workflows/rtb.md        # Project RTB
```

### **Global Configuration Ecosystem**
```
~/.agent/                                        ← UNIVERSAL AGENT CONFIGURATION
├── AGENTS.md                                     # Universal entry point
├── docs/GLOBAL_INDEX.md                           # Master navigation
├── docs/sop/                                     # Universal SOPs
└── scripts/                                      # Universal automation

↓ SYMLINK ACCESS POINTS ↓

.agent/docs/sop/global-configs/ → ~/.agent/docs/   # Project access to globals
BOOTSTRAP.md → ~/.agent/docs/ONBOARDING.md        # Project bootstrap guide
```

---

## 🔧 **Directory Structure Analysis**

### **Source Directories (Write Access)**
```bash
~/.gemini/antigravity/skills/           # Skills source of truth
~/.gemini/antigravity/global_workflows/  # Global commands source of truth (Antigravity naming)  
~/.agent/                               # Global configuration source
```

**📝 Note on Terminology**: Antigravity calls these "global_workflows" while other systems use "commands". Both refer to the same global slash command repository.

### **Access Points (Read-Only Symlinks)**
```bash
# Skills Access Points
.agent/skills/                           # Project-level skills access
~/.config/opencode/skills/               # OpenCode skills access
~/.claude/skills/                       # Claude skills access (legacy)

# Commands Access Points
~/.agent/commands/                      # Agent commands access
~/.config/opencode/commands/             # OpenCode commands access
.agent/workflows/                        # Project-specific workflows

# Configuration Access Points
.agent/docs/sop/global-configs/          # Project config access
BOOTSTRAP.md                            # Project bootstrap access
```

---

## 🔍 **Symlink Validation Matrix**

### **Critical Symlinks (Blocking Validation)**
| Symlink | Source | Target | Validation Command |
|---------|--------|--------|------------------|
| `.agent/skills/` | `.agent/skills/` | `~/.gemini/antigravity/skills/` | `readlink .agent/skills/` |
| `~/.config/opencode/skills/` | `~/.config/opencode/skills/` | `~/.gemini/antigravity/skills/` | `readlink ~/.config/opencode/skills/` |
| `~/.agent/commands/` | `~/.agent/commands/` | `~/.gemini/antigravity/global_workflows/` | `readlink ~/.agent/commands/` |
| `~/.config/opencode/commands/` | `~/.config/opencode/commands/` | `~/.gemini/antigravity/global_workflows/` | `readlink ~/.config/opencode/commands/` |

### **Project-Specific Symlinks**
| Symlink | Source | Target | Validation Command |
|---------|--------|--------|------------------|
| `.agent/workflows/next.md` | `.agent/workflows/next.md` | `~/.gemini/antigravity/global_workflows/next.md` | `readlink .agent/workflows/next.md` |
| `.agent/workflows/rtb.md` | `.agent/workflows/rtb.md` | `~/.gemini/antigravity/global_workflows/rtb.md` | `readlink .agent/workflows/rtb.md` |

### **Configuration Symlinks**
| Symlink | Source | Target | Validation Command |
|---------|--------|--------|------------------|
| `global-configs/` | `.agent/docs/sop/global-configs/` | `~/.agent/docs/` | `readlink .agent/docs/sop/global-configs/` |
| `BOOTSTRAP.md` | `BOOTSTRAP.md` | `~/.agent/docs/ONBOARDING.md` | `readlink BOOTSTRAP.md` |

---

## 🛠️ **Symlink Management Procedures**

### **Initial Setup**
```bash
# 1. Create global source directories (if not exists)
mkdir -p ~/.gemini/antigravity/skills/
mkdir -p ~/.gemini/antigravity/global_workflows/
mkdir -p ~/.agent/docs/

# 2. Create skills symlinks
ln -sf ~/.gemini/antigravity/skills/ .agent/skills/
ln -sf ~/.gemini/antigravity/skills/ ~/.config/opencode/skills/

# 3. Create commands symlinks  
ln -sf ~/.gemini/antigravity/global_workflows/ ~/.agent/commands/
ln -sf ~/.gemini/antigravity/global_workflows/ ~/.config/opencode/commands/

# 4. Create project-specific workflow symlinks
mkdir -p .agent/workflows/
ln -sf ~/.gemini/antigravity/global_workflows/next.md .agent/workflows/next.md
ln -sf ~/.gemini/antigravity/global_workflows/rtb.md .agent/workflows/rtb.md

# 5. Create configuration symlinks
ln -sf ~/.agent/docs/ .agent/docs/sop/global-configs/
ln -sf ~/.agent/docs/ONBOARDING.md BOOTSTRAP.md
```

### **Validation Procedures**
```bash
# Validate all critical symlinks
function validate_symlinks() {
    local errors=0
    
    # Skills symlinks
    if [[ ! -L ".agent/skills" ]] || [[ "$(readlink .agent/skills)" != "$(echo ~/.gemini/antigravity/skills/)" ]]; then
        echo "❌ BROKEN: .agent/skills symlink"
        ((errors++))
    fi
    
    if [[ ! -L "~/.config/opencode/skills" ]] || [[ "$(readlink ~/.config/opencode/skills)" != "$(echo ~/.gemini/antigravity/skills/)" ]]; then
        echo "❌ BROKEN: ~/.config/opencode/skills symlink"
        ((errors++))
    fi
    
    # Commands symlinks
    if [[ ! -L "~/.agent/commands" ]] || [[ "$(readlink ~/.agent/commands)" != "$(echo ~/.gemini/antigravity/global_workflows/)" ]]; then
        echo "❌ BROKEN: ~/.agent/commands symlink"
        ((errors++))
    fi
    
    if [[ ! -L "~/.config/opencode/commands" ]] || [[ "$(readlink ~/.config/opencode/commands)" != "$(echo ~/.gemini/antigravity/global_workflows/)" ]]; then
        echo "❌ BROKEN: ~/.config/opencode/commands symlink"
        ((errors++))
    fi
    
    return $errors
}

# Run validation
if validate_symlinks; then
    echo "✅ All symlinks valid"
else
    echo "❌ Broken symlinks detected - fix before continuing"
    exit 1
fi
```

### **Repair Procedures**
```bash
# Broken skills symlink repair
function repair_skills_symlinks() {
    echo "🔧 Repairing skills symlinks..."
    
    # Remove broken symlinks
    [[ -L ".agent/skills" ]] && rm .agent/skills
    [[ -L "~/.config/opencode/skills" ]] && rm ~/.config/opencode/skills
    
    # Recreate correct symlinks
    ln -sf ~/.gemini/antigravity/skills/ .agent/skills/
    ln -sf ~/.gemini/antigravity/skills/ ~/.config/opencode/skills/
    
    echo "✅ Skills symlinks repaired"
}

# Broken commands symlink repair
function repair_commands_symlinks() {
    echo "🔧 Repairing commands symlinks..."
    
    # Remove broken symlinks
    [[ -L "~/.agent/commands" ]] && rm ~/.agent/commands
    [[ -L "~/.config/opencode/commands" ]] && rm ~/.config/opencode/commands
    
    # Recreate correct symlinks
    ln -sf ~/.gemini/antigravity/global_workflows/ ~/.agent/commands/
    ln -sf ~/.gemini/antigravity/global_workflows/ ~/.config/opencode/commands/
    
    echo "✅ Commands symlinks repaired"
}
```

---

## 🔍 **Troubleshooting Guide**

### **Common Symlink Issues**

#### **Circular Symlinks**
```bash
# Problem: Symlink points to itself or creates loop
readlink .agent/skills  # Returns .agent/skills or circular path

# Solution: Remove and recreate
rm .agent/skills
ln -sf ~/.gemini/antigravity/skills/ .agent/skills/
```

#### **Stale Symlinks**
```bash
# Problem: Target doesn't exist
ls -la .agent/skills/  # Shows "No such file or directory"

# Solution: Verify source exists
ls -la ~/.gemini/antigravity/skills/  # Should show directory contents
# If missing, recreate source directory
mkdir -p ~/.gemini/antigravity/skills/
```

#### **Permission Issues**
```bash
# Problem: Can't read symlink target
readlink .agent/skills/  # Works, but access denied

# Solution: Check permissions
ls -la ~/.gemini/antigravity/skills/
chmod -R 755 ~/.gemini/antigravity/skills/
```

#### **Relative vs Absolute Path Issues**
```bash
# Problem: Mixed relative/absolute paths
readlink .agent/skills/  # Shows ../relative/path

# Solution: Use absolute paths for consistency
rm .agent/skills
ln -sf /full/path/to/.gemini/antigravity/skills/ .agent/skills/
```

### **Advanced Diagnostics**
```bash
# Complete symlink ecosystem audit
function audit_symlink_ecosystem() {
    echo "🔍 SYMLINK ECOSYSTEM AUDIT"
    echo "=========================="
    
    # Check source directories
    echo "📁 Source Directories:"
    for dir in "skills" "global_workflows"; do
        local path="~/.gemini/antigravity/$dir"
        if [[ -d "$path" ]]; then
            echo "✅ $path exists"
            ls -1 "$path" | head -3 | sed 's/^/   ├─ /'
        else
            echo "❌ $path MISSING"
        fi
    done
    
    # Check symlinks
    echo -e "\n🔗 Symlink Access Points:"
    declare -A symlinks=(
        [".agent/skills"]="~/.gemini/antigravity/skills/"
        ["~/.config/opencode/skills"]="~/.gemini/antigravity/skills/"
        ["~/.agent/commands"]="~/.gemini/antigravity/global_workflows/"
        ["~/.config/opencode/commands"]="~/.gemini/antigravity/global_workflows/"
    )
    
    for link in "${!symlinks[@]}"; do
        if [[ -L "$link" ]]; then
            local target=$(readlink "$link")
            local expected="${symlinks[$link]}"
            if [[ "$target" == "$expected" ]]; then
                echo "✅ $link → $target"
            else
                echo "❌ $link → $target (expected: $expected)"
            fi
        else
            echo "❌ $link NOT A SYMLINK"
        fi
    done
}
```

---

## 📊 **Performance Considerations**

### **Symlink Resolution Cost**
- **Modern Filesystems**: Symlinks have minimal overhead (< 1ms resolution)
- **Cache Friendly**: Frequently accessed symlinks cached by OS
- **Network Storage**: May have higher latency, consider local caching

### **Optimization Strategies**
```bash
# Use absolute paths to avoid relative path resolution overhead
ln -sf /absolute/path/to/target /absolute/path/to/link

# Batch symlink operations
for link in skill1 skill2 skill3; do
    ln -sf ~/.gemini/antigravity/skills/$link .agent/skills/$link
done

# Validate symlinks in parallel (for large ecosystems)
for dir in .agent ~/.config/opencode; do
    find $dir -type l -exec test ! -e {} \; &
done
wait
```

---

## 🔧 **Integration with Other Systems**

### **Git Integration**
```bash
# .gitignore recommendations for symlink ecosystem
.gitignore:
# Ignore symlink targets (but preserve symlinks themselves)
/.agent/skills/
~/.config/opencode/skills/
~/.agent/commands/
~/.config/opencode/commands/

# Keep source directories in version control
!/.gemini/antigravity/skills/
!/.gemini/antigravity/global_workflows/
```

### **Docker Integration**
```dockerfile
# Dockerfile
FROM ubuntu:22.04

# Create symlink ecosystem
RUN mkdir -p /root/.gemini/antigravity/{skills,global_workflows}
RUN ln -sf /root/.gemini/antigravity/skills/ /app/.agent/skills/
RUN ln -sf /root/.gemini/antigravity/global_workflows/ /root/.agent/commands/
```

### **CI/CD Integration**
```yaml
# .github/workflows/validate-symlinks.yml
name: Validate Symlink Ecosystem
on: [push, pull_request]

jobs:
  validate-symlinks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate symlinks
        run: |
          python .agent/scripts/validate_complete_symlink_ecosystem.py
```

---

## 📚 **Related Documentation**

### **Tier Navigation**
- **⬇️ Down**: [**Quick Reference**](../workspace/QUICK_REFERENCE.md) - Daily usage
- **⬇️ Down**: [**Skills Ecosystem Guide**](./SKILLS_ECOSYSTEM.md) - Skills details  
- **⬇️ Down**: [**Commands Ecosystem Guide**](./COMMANDS_ECOSYSTEM.md) - Commands details

### **System Integration**
- **[SOP Validation](./SOP_CONSISTENCY_VALIDATION.md)** - Automated validation
- **[Project Roadmap](../../rules/ROADMAP.md)** - Project context
- **[Implementation Plan](../../rules/ImplementationPlan.md)** - Technical execution

---

**Last Updated**: 2026-02-03  
**Part of**: LightRAG Three-Tier Documentation System (Tier 3 - Complete Technical Reference)  
**Scope**: Universal Symlink Architecture (cross-project, cross-tool compatibility)