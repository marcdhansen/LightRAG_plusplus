# LightRAG Standard Operating Procedures (SOP)

> **📍 Hierarchy**: **Global SOP** (base) → **Local Extensions** (project-specific)
>
> This directory extends the **[Global SOP](~/.agent/docs/sop/)** with LightRAG-specific requirements while maintaining full compliance with universal protocols.

## 🌐 **Global SOP Base Standards**

**Mandatory Foundation**: All agents must follow the [Global SOP](~/.agent/docs/sop/) as the authoritative source:

- **[📖 Global SOP README](~/.agent/docs/sop/README.md)** - Universal standards
- **[🚀 GEMINI.md](./global-configs/GEMINI.md)** - Global Agent Rules & SMP
- **[🤝 COLLABORATION.md](./global-configs/COLLABORATION.md)** - Multi-agent coordination
- **[🧪 tdd-workflow.md](./global-configs/tdd-workflow.md)** - Universal TDD workflow
- **[📋 AGENT_ONBOARDING.md](./global-configs/AGENT_ONBOARDING.md)** - Universal onboarding

### **Global Access Points**

```bash
.agent/docs/sop/global-configs/  # → symlinks to ~/.agent/docs/sop/
```

---

## 🔧 **LightRAG-Specific Extensions**

### **Enhanced TDD Requirements**

**🚫 MANDATORY**: [TDD Mandatory Gate](./TDD_MANDATORY_GATE.md) - **Cannot bypass**

Project-specific TDD enforcement that extends the global `tdd-workflow.md`:

- **Automated blocking** for non-compliant implementations
- **Performance benchmarking** with speed-accuracy tradeoff analysis
- **Quality gate enforcement** that prevents work continuation
- **Integration validation** with LightRAG-specific testing patterns

### **Multi-Phase Implementation**

**🚫 MANDATORY**: [Multi-Phase Hand-off Protocol](./MULTI_PHASE_HANDOFF_PROTOCOL.md)

Complex feature coordination beyond standard SMP:

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
# Validate TDD compliance (LightRAG extension)
./scripts/validate_tdd_compliance.sh <feature-name>

# Verify hand-off compliance (LightRAG extension)
./scripts/verify_handoff_compliance.sh --phase <phase> --feature <feature>

# Global SOP compliance (base requirements)
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

1. **Global TDD Workflow** - Follow `tdd-workflow.md` as base
2. **LightRAG TDD Gate** - Additional mandatory requirements
3. **Performance Benchmarks** - LightRAG-specific validation
4. **Quality Gates** - Both global and local validation

---

## 📚 **Complete Documentation Navigation**

### **Global Standards (Base)**

- **[🌐 Global SOP Hub](~/.agent/docs/sop/README.md)** - Universal protocols
- **[🚀 Global Agent Rules](./global-configs/GEMINI.md)** - SMP and procedures

### **LightRAG Extensions**

- **[🔧 TDD Mandatory Gate](./TDD_MANDATORY_GATE.md)** - Enhanced TDD requirements
- **[🔄 Multi-Phase Hand-off](./MULTI_PHASE_HANDOFF_PROTOCOL.md)** - Complex coordination

### **Skills & Commands (Universal)**

- **[🧠 Skills Ecosystem](./SKILLS_ECOSYSTEM.md)** - Agent capabilities
- **[⚡ Commands Ecosystem](./COMMANDS_ECOSYSTEM.md)** - Workflow commands

---

**Last Updated**: 2026-02-05
**Hierarchy**: Global SOP (base) + LightRAG Extensions (project-specific)
**Scope**: LightRAG Project - maintains full global SOP compliance
