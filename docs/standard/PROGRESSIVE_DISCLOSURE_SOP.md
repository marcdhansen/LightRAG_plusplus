# 📖 Progressive Disclosure SOP

**Purpose**: Standard Operating Procedure for implementing progressive disclosure in documentation to optimize agent context windows and reduce cognitive load.

## 🎯 Progressive Disclosure Principles

### **Core Heuristic**
"Progressive disclosure is an important heuristic that should guide all documentation creation to prevent context overwhelm."

### **Three-Layer System**

**Layer 1: Quick Reference** (`docs/quick/`)
- **Purpose**: Immediate task completion (5 minutes or less)
- **Size Limit**: < 50 lines per document
- **Read Time**: 1-2 minutes maximum
- **Content**: Essential commands, quick fixes, one-page summaries

**Layer 2: Standard Documentation** (`docs/standard/`)
- **Purpose**: Complete information for common tasks (15 minutes or less)
- **Size Limit**: < 500 lines per document
- **Read Time**: 5-10 minutes maximum
- **Content**: Full guides, procedures, API documentation

**Layer 3: Detailed Content** (`docs/detailed/`)
- **Purpose**: In-depth reference (no time limits)
- **Size Limit**: None (reference as needed)
- **Read Time**: As needed for reference
- **Content**: Technical specifications, research findings, detailed analysis

## 📋 Implementation Guidelines

### **Content Creation Workflow**

**1. Always Create in Layers**
```bash
# Start with quick reference
docs/quick/TOPIC.md

# Expand to standard guide
docs/standard/topic/

# Add detailed specifications
docs/detailed/topic/
```

**2. Cross-Reference Between Layers**
```markdown
<!-- In Quick Reference -->
**Need more detail?** → [Complete Guide](../standard/topic/)

<!-- In Standard Guide -->
**In-depth technical details** → [Technical Specifications](../detailed/topic/)
**Quick overview** → [Quick Reference](../quick/TOPIC.md)
```

**3. Single Source of Truth**
- No duplication between layers
- Each layer links to the next level
- Maintain one canonical version per piece of information

### **File Naming Conventions**

**Quick References**:
```
docs/quick/QUICK_START.md      # All caps, underscores
docs/quick/SKILLS.md           # Short, clear names
docs/quick/TROUBLESHOOTING.md  # Purpose-driven names
```

**Standard Documentation**:
```
docs/standard/guides/          # Category directories
docs/standard/project/         # Topic directories
docs/standard/topic/README.md   # Index files
```

**Detailed Content**:
```
docs/detailed/specifications/  # Technical specs
docs/detailed/api/             # API documentation
docs/detailed/architecture/     # System design
```

## 🧩 Context Optimization Rules

### **For Agent Tasks**

**Quick Tasks** (< 30 minutes):
- Load only `docs/quick/` + relevant skill overview
- Target context: < 2000 tokens
- Examples: Bug fixes, simple features, configuration

**Standard Tasks** (30 minutes - 2 hours):
- Load `docs/standard/` sections as needed
- Target context: < 5000 tokens
- Examples: Feature development, debugging, testing

**Research Tasks** (> 2 hours):
- Access `docs/detailed/` for specific questions
- Target context: as needed for reference
- Examples: Architecture design, optimization research

### **Context Loading Patterns**

**Pattern 1: Progressive Loading**
```
1. Start with quick reference
2. Add standard sections if needed
3. Access detailed content for specific questions
```

**Pattern 2: Task-Based Loading**
```
1. Identify task type and complexity
2. Load appropriate layer(s)
3. Add context incrementally as needed
```

## 🔄 Quality Assurance

### **Review Checklist**

**Quick Reference Documents**:
- [ ] < 50 lines total
- [ ] < 2 minutes read time
- [ ] Essential information only
- [ ] Links to deeper content
- [ ] Clear action-oriented structure

**Standard Documentation**:
- [ ] < 500 lines total
- [ ] < 10 minutes read time
- [ ] Complete but not overwhelming
- [ ] Links to quick and detailed layers
- [ ] Logical organization

**Detailed Content**:
- [ ] Comprehensive coverage
- [ ] Clear navigation structure
- [ ] Links back to summary layers
- [ ] Reference-friendly format

### **Automated Validation**

**File Size Checks**:
```bash
# Quick docs should be < 50 lines
find docs/quick/ -name "*.md" -exec wc -l {} \; | awk '$1 > 50'

# Standard docs should be < 500 lines
find docs/standard/ -name "*.md" -exec wc -l {} \; | awk '$1 > 500'
```

**Link Validation**:
```bash
# Check for broken cross-references
grep -r "](\.\./" docs/ --include="*.md" | while read line; do
  # Validate each cross-reference exists
done
```

## 📊 Success Metrics

### **Quantitative**
- Quick docs: 100% under 50 lines
- Standard docs: 95% under 500 lines
- Average context load: 60% reduction
- Time to find information: 50% improvement

### **Qualitative**
- Agents can find needed information within 2 clicks
- Clear separation between archival and active content
- Progressive disclosure prevents context overwhelm
- Single source of truth eliminates confusion

## 🛠️ Implementation Tools

### **Templates**
Create templates for each layer to ensure consistency:
```bash
# Quick reference template
docs/quick/_template.md

# Standard documentation template
docs/standard/_template.md

# Detailed content template
docs/detailed/_template.md
```

### **Automation Scripts**
```bash
#!/bin/bash
# validate_progressive_disclosure.sh
# Checks compliance with progressive disclosure standards

echo "🔍 Checking progressive disclosure compliance..."

# Check file sizes
echo "📊 File size compliance:"
find docs/quick/ -name "*.md" -exec wc -l {} \; | awk '$1 > 50 {print "❌", $2, ":", $1, "lines"}'
find docs/standard/ -name "*.md" -exec wc -l {} \; | awk '$1 > 500 {print "❌", $2, ":", $1, "lines"}'

echo "✅ Progressive disclosure validation complete"
```

## 🔄 Maintenance Procedures

### **Weekly Maintenance**
- Review new documentation for compliance
- Archive outdated quick references
- Update cross-references between layers

### **Monthly Review**
- Audit all documentation for progressive disclosure compliance
- Update templates and standards as needed
- Collect feedback from agents on context optimization

### **Quarterly Updates**
- Review and refine progressive disclosure principles
- Update automation tools and validation scripts
- Analyze context loading metrics and optimization opportunities

---

**🎯 Key Principle**: Every piece of information should have a clear place in the progressive disclosure hierarchy, making it easy for agents to find what they need without being overwhelmed by unnecessary context.
