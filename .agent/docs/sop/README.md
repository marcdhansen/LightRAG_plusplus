# LightRAG Standard Operating Procedures (SOP)

> **📍 Hierarchy**: **Global SOP** (base) → **Local Extensions** (project-specific)
>
> This directory extends the **[Global SOP](~/.agent/docs/sop/)** with LightRAG-specific requirements while maintaining full compliance with universal protocols.

## 🌐 **Global SOP Base Standards**

**Mandatory Foundation**: All agents must follow the [Global SOP](~/.agent/docs/sop/) as the authoritative source:

- **[📖 Global SOP README](~/.agent/docs/sop/README.md)** - Universal standards
- **[🚀 GEMINI.md](./global-configs/GEMINI.md)** - Global Agent Rules & Universal Agent Protocol
- **[🤝 COLLABORATION.md](./global-configs/COLLABORATION.md)** - Multi-agent coordination
- **[🧪 Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)** - Mandatory TDD with enforcement
- **[📋 AGENT_ONBOARDING.md](./global-configs/AGENT_ONBOARDING.md)** - Universal onboarding

### **Global Access Points**

```bash
.agent/docs/sop/global-configs/  # → symlinks to ~/.agent/docs/sop/
```

---

## 🔧 **LightRAG-Specific Extensions**

### **TDD Implementation Guidance**

**🚫 MANDATORY**: [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md) - **Cannot bypass**

**NEW**: Global TDD workflow now includes mandatory enforcement mechanisms:

- ✅ **Automated blocking** for non-compliant implementations (global)
- ✅ **Performance benchmarking** with speed-accuracy tradeoff analysis (global)
- ✅ **Quality gate enforcement** that prevents work continuation (global)
- 🔧 **LightRAG Implementation Guide** - Project-specific patterns and examples

### **LightRAG Implementation Guide**

**📋 Project-Specific Guidance**: [TDD Implementation Guide](./TDD_MANDATORY_GATE.md)

This guide provides LightRAG-specific context for the global mandatory TDD standards:

- **LightRAG testing structure** and file organization patterns
- **Domain-specific performance benchmarks** and baselines
- **Multi-phase integration** for complex LightRAG features
- **Implementation examples** and common pitfalls
- **Project-specific validation scripts** and templates

**Note**: This guide **extends** (does not replace) global mandatory standards.

### **Multi-Phase Implementation**

**🚫 MANDATORY**: [Multi-Phase Hand-off Protocol](./MULTI_PHASE_HANDOFF_PROTOCOL.md)

Complex feature coordination beyond standard Universal Agent Protocol:

- **Agent responsibility definitions** for multi-phase implementations
- **Comprehensive hand-off documentation** requirements
- **Automated verification** that blocks phase transitions
- **Quality assessment** integration with reflect and debriefing systems

### **Project-Specific Performance**

- **[KEYWORD_SEARCH_PERFORMANCE.md](./global-configs/KEYWORD_SEARCH_PERFORMANCE.md)** - Performance benchmarks
- **LightRAG integration patterns** and optimization guidelines

---

## 🌐 **Skills & Commands Ecosystem**

**Critical Note**: Skills and commands follow the global symlink architecture with `~/.gemini/antigravity/` as the universal source of truth.

### **Access Points**

```bash
Source of Truth:  ~/.gemini/antigravity/skills/
Project Access:    .agent/skills/ → ~/.gemini/antigravity/skills/
OpenCode Global:   ~/.config/opencode/skills/ → ~/.gemini/antigravity/skills/

Source of Truth:  ~/.gemini/antigravity/global_workflows/
Agent Global:      ~/.agent/commands/ → ~/.gemini/antigravity/global_workflows/
OpenCode Global:   ~/.config/opencode/commands/ → ~/.gemini/antigravity/global_workflows/
```

### **Ecosystem Documentation**

- **[Skills Ecosystem Guide](./SKILLS_ECOSYSTEM.md)** → Global documentation (symlink)
- **[Commands Ecosystem Guide](./COMMANDS_ECOSYSTEM.md)** → Global documentation (symlink)

---

## 📋 **Protocol Compliance Priority**

When conflicts arise, this hierarchy applies:

1. **🥇 Global SOP** - Universal standards (never overridden)
2. **🥈 Local Extensions** - Project-specific requirements (must respect global)
3. **🥉 Workspace Rules** - Temporary/local rules (must respect both above)

### **Validation Scripts**

```bash
# Validate TDD compliance (LightRAG validation)
./scripts/validate_tdd_compliance.sh <feature-name>

# Verify hand-off compliance (LightRAG coordination)
./scripts/verify_handoff_compliance.sh --phase <phase> --feature <feature>

# Global SOP compliance (MANDATORY requirements)
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --init
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --finalize
```

---

## 🚨 **Critical Requirements**

### **For All Work Sessions**

1. **Read Global SOP** first - `~/.agent/docs/sop/README.md`
2. **Follow global protocols** - GEMINI.md, COLLABORATION.md, tdd-workflow.md
3. **Apply local extensions** - TDD Gate, Multi-Phase Hand-off
4. **Maintain hierarchy** - Never override global standards

### **For New Features**

1. **Global TDD Workflow** - Follow [tdd-workflow.md](~/.agent/docs/sop/tdd-workflow.md) (includes mandatory enforcement)
2. **LightRAG Implementation** - Apply [LightRAG-specific patterns](./TDD_MANDATORY_GATE.md)
3. **Performance Benchmarks** - Use LightRAG baselines and validation
4. **Quality Gates** - Global mandatory validation + LightRAG context

---

## 📚 **Complete Documentation Navigation**

### **Global Standards (Base)**

- **[🌐 Global SOP Hub](~/.agent/docs/sop/README.md)** - Universal protocols
- **[🚀 Global Agent Rules](./global-configs/GEMINI.md)** - Universal Agent Protocol and procedures

### **LightRAG Extensions**

- **[🔧 LightRAG TDD Guide](./TDD_MANDATORY_GATE.md)** - LightRAG implementation patterns
- **[🔄 Multi-Phase Hand-off](./MULTI_PHASE_HANDOFF_PROTOCOL.md)** - Complex coordination

### **Skills & Commands (Universal)**

- **[🧠 Skills Ecosystem](./SKILLS_ECOSYSTEM.md)** - Agent capabilities
- **[⚡ Commands Ecosystem](./COMMANDS_ECOSYSTEM.md)** - Workflow commands

---

**Last Updated**: 2026-02-05
**Hierarchy**: Global SOP (base) + LightRAG Extensions (project-specific)
**Scope**: LightRAG Project - maintains full global SOP compliance
