# 🗺️ Ultimate Navigation Guide

**Purpose**: How to find ANYTHING in this workspace quickly and efficiently.

## 🎯 Finding Information Fast

### **I need to...**
**...get started**: [Quick Start](../quick/QUICK_START.md)
**...fix a problem**: [Troubleshooting](../quick/TROUBLESHOOTING.md)
**...understand the project**: [Project Overview](../../README.md)
**...coordinate with agents**: [.agent Interface](../../.agent/README.md)

### **I'm looking for...**
**...documentation**: [📚 Documentation Layers](#documentation-layers)
**...skills**: [🛠️ Skills Directory](../navigation/SKILL_DIRECTORY.md)
**...tasks**: [📋 Current Tasks](../../.agent/workspace/docs/workspace/TODO.md)
**...archives**: [🗃️ Historical Content](#archives)

## 📚 Documentation Layers

### **Quick References** ([../quick/](../quick/))
*5 minutes or less*
- [Quick Start](../quick/QUICK_START.md) - Get running immediately
- [Skills Overview](../quick/SKILLS.md) - Available capabilities
- [Common Issues](../quick/TROUBLESHOOTING.md) - Fast fixes

### **Standard Documentation** ([../standard/](../standard/))
*15 minutes or less*
- [Complete Setup Guide](../standard/guides/) - Full configuration
- [Testing Strategy](../standard/TEST_INVENTORY.md) - How testing works
- [Security Guide](../standard/guides/SECURITY.md) - Security practices

### **Detailed Content** ([../detailed/](../detailed/))
*Reference as needed*
- [Technical Specifications](../detailed/specifications/) - Deep technical details
- [API Documentation](../detailed/api/) - Complete API reference
- [Architecture](../detailed/architecture/) - System design

## 🛠️ Skills by Use Case

**Development Tasks:**
- [UI Skill](../../.agent/skills/ui/SKILL.md) - Frontend issues
- [Graph Skill](../../.agent/skills/graph/SKILL.md) - Knowledge graphs
- [Testing Skill](../../.agent/skills/testing/SKILL.md) - Test failures

**Operations Tasks:**
- [Process Skill](../../.agent/skills/process/SKILL.md) - Workflows
- [Evaluation Skill](../../.agent/skills/evaluation/SKILL.md) - Benchmarks
- [Docs Skill](../../.agent/skills/docs/SKILL.md) - Documentation

**Coordination Tasks:**
- [FlightDirector](~/.gemini/antigravity/skills/FlightDirector/SKILL.md) - Project management
- [Librarian](~/.gemini/antigravity/skills/Librarian/SKILL.md) - Knowledge organization
- [QualityAnalyst](~/.gemini/antigravity/skills/QualityAnalyst/SKILL.md) - Code quality

## 🗃️ Archives

**Benchmarks & Results** ([../../archive/benchmarks/](../../archive/benchmarks/))
- Performance reports and comparison data
- Historical benchmark results

**Audits & Analysis** ([../../archive/audits/](../../archive/audits/))
- Code audits and quality reports
- Security audit results

**Legacy Documentation** ([../../archive/legacy/](../../archive/legacy/))
- Old documentation formats
- Historical project information

## 🔍 Search Strategy

### **By File Type**
```bash
# Documentation
find . -name "*.md" | grep -E "(docs|\.agent)"

# Configuration files
find . -name "*.json" -o -name "*.yaml" -o -name "*.toml"

# Code files
find . -name "*.py" -o -name "*.js" -o -name "*.ts"
```

### **By Content**
```bash
# Search within files
grep -r "keyword" . --include="*.md"

# Find references
rg "issue-id" --type md
```

### **By Directory**
```
.agent/          → Agent coordination and skills
docs/            → Documentation (layered)
archive/         → Historical content
lightrag/        → Core library code
lightrag_webui/  → Web interface
tests/           → Test suite
```

## ⚡ Progressive Disclosure Rules

**For Common Tasks:**
1. Start with [Quick Start](../quick/QUICK_START.md)
2. Add [Standard Docs](../standard/) as needed
3. Reference [Detailed Content](../detailed/) for specific questions

**For Debugging:**
1. Try [Common Issues](../quick/TROUBLESHOOTING.md) first
2. Check [Troubleshooting Map](../navigation/TROUBLESHOOTING_MAP.md)
3. Search [archive/audits/](../../archive/audits/) for similar issues

**For New Development:**
1. Read [Skills Overview](../quick/SKILLS.md) for available tools
2. Check [Current Tasks](../../.agent/workspace/docs/workspace/TODO.md) for what's needed
3. Use [Global Standards](../../.agent/GLOBAL/standards/) for best practices

## 🆘 Emergency Navigation

**Can't find something?**
1. Check [GLOBAL_INDEX.md](../../.agent/GLOBAL/index/GLOBAL_INDEX.md) - master index
2. Search with `rg keyword --type md`
3. Look in [archive/misc/](../../archive/misc/) for moved files
4. Ask the [Librarian skill](~/.gemini/antigravity/skills/Librarian/SKILL.md)

**File moved or missing?**
1. Check the [archive/](../../archive/) directories
2. Look for symlinks or redirects
3. Search the git history: `git log --follow --name-status -- <filename>`

---

**💡 Key Navigation Principle**: Start broad (quick), then dive deep (standard/detailed). Never load more documentation than you need for your current task.
