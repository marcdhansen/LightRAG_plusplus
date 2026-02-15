# 🔄 SOP Integration Guide

**Purpose**: Guide for navigating between Global SOP standards and LightRAG-specific extensions.
**Target**: Agents working on LightRAG who need to understand protocol hierarchy and usage patterns.
**Scope**: LightRAG Project - maintains full global SOP compliance while adding project-specific requirements.

---

## 🎯 **Quick Decision Tree**

```mermaid
flowchart TD
    A[Start Task] --> B{Need Global Standards?}
    B -->|Yes| C[Read Global SOP First]
    B -->|No| D[Check Local Extensions]

    C --> E[Follow GEMINI.md Universal Agent Protocol]
    E --> F[Apply Local Extensions]

    D --> G{TDD Development?}
    G -->|Yes| H[Use TDD Mandatory Gate]
    G -->|No| I[Multi-Phase Implementation?]
    I -->|Yes| J[Use Hand-off Protocol]
    I -->|No| K[Standard Workflow]

    F --> L[Complete Task]
    H --> L
    J --> L
    K --> L
```

---

## 📋 **Protocol Usage Matrix**

| **Scenario** | **Global SOP** | **Local Extension** | **Priority** |
|-------------|----------------|-------------------|-------------|
| **Basic Development** | `tdd-workflow.md` (MANDATORY enforcement) | None | Global only |
| **New Feature** | `tdd-workflow.md` (MANDATORY enforcement) | `TDD_IMPLEMENTATION_GUIDE.md` | Global mandatory → Local context |
| **Multi-Phase Feature** | Standard Universal Agent Protocol + Global TDD | `MULTI_PHASE_HANDOFF_PROTOCOL.md` | Global mandatory → Local coordination |
| **Agent Coordination** | `COLLABORATION.md` | None | Global only |
| **Session Management** | `GEMINI.md` (includes validation) | None | Global only |
| **Performance Testing** | Global performance requirements (MANDATORY) | `KEYWORD_SEARCH_PERFORMANCE.md` | Global mandatory → Local baselines |

**🔒 CRITICAL**: Global TDD enforcement is MANDATORY for ALL scenarios and CANNOT be bypassed. Local extensions provide context only.

---

## 🌐 **Global SOP - Foundation Standards**

### **When to Use Global SOP Only**

**These scenarios require ONLY global standards:**

1. **Session Management**
   - Pre-Flight Checks (PFC)
   - Initialization procedures
   - Finalization
   - Collaboration protocols

2. **Basic Development**
   - Simple feature implementation
   - Standard bug fixes
   - Routine documentation updates

3. **Agent Coordination**
   - Multi-agent work allocation
   - Branch isolation rules
   - Session lock management

### **Global SOP Access**

```bash
# Primary location
~/.agent/docs/sop/README.md

# Key global documents
.agent/docs/sop/global-configs/GEMINI.md           # Universal Agent Protocol & procedures
.agent/docs/sop/global-configs/COLLABORATION.md    # Multi-agent rules
~/.agent/docs/sop/tdd-workflow.md                    # Mandatory TDD with enforcement
.agent/docs/sop/global-configs/AGENT_ONBOARDING.md # Onboarding
```

---

## 🔧 **LightRAG Extensions - Project-Specific**

### **When to Use Local Extensions**

**Enhanced requirements that extend global standards:**

1. **Enhanced TDD Development**
   - **Global Base**: Follow `tdd-workflow.md` (includes mandatory enforcement, performance requirements, quality gates)
   - **Local Extension**: `TDD_IMPLEMENTATION_GUIDE.md` (LightRAG-specific patterns and examples)
   - **Triggers**: All development (global mandatory) + LightRAG context when needed

2. **Multi-Phase Implementation**
   - **Global Base**: Standard Universal Agent Protocol procedures
   - **Local Extension**: `MULTI_PHASE_HANDOFF_PROTOCOL.md`
   - **Triggers**: Complex features, multi-agent hand-offs, architectural changes

3. **Performance-Specific Work**
   - **Global Base**: Universal testing standards
   - **Local Extension**: `KEYWORD_SEARCH_PERFORMANCE.md`
   - **Triggers**: Performance optimizations, benchmarking, scalability work

### **Local Extension Access**

```bash
# LightRAG-specific extensions
.agent/docs/sop/TDD_MANDATORY_GATE.md                   # LightRAG implementation guide (extends global)
.agent/docs/sop/MULTI_PHASE_HANDOFF_PROTOCOL.md        # Complex coordination
.agent/docs/sop/global-configs/KEYWORD_SEARCH_PERFORMANCE.md  # Performance baselines
```

---

## ⚖️ **Conflict Resolution Protocol**

### **Hierarchy Rules**

1. **🥇 Global SOP is Supreme** - Never overridden by local rules
2. **🥈 Local Extensions Complement** - Add requirements, don't replace
3. **🥉 Workspace Rules are Temporary** - Must respect both global and local

### **Conflict Examples & Solutions**

#### **TDD Workflow Differences**

```bash
# Global requirement (tdd-workflow.md) - MANDATORY ENFORCEMENT
1. 🚫 MANDATORY PRE-FLIGHT VALIDATION (Implementation Readiness)
2. 📋 Specification Phase (Requirements + Baseline + Success Criteria)
3. 🔴 Red Phase (Failing Tests + Performance Benchmarks)
4. 🟢 Green Phase (Implementation + Performance Validation)
5. ✅ Verification Phase (Tests Pass + Benchmarks Pass)
6. 🔄 Refactor Phase (Code Cleanup + Performance Verification)
7. 📊 Audit Phase (Performance Analysis + Tradeoff Documentation)
8. 🚪 Quality Gate Validation (MANDATORY - No Override Possible)

# Local extension (TDD_IMPLEMENTATION_GUIDE.md) - LIGHTRAG CONTEXT ONLY
9. Apply LightRAG testing patterns ← LightRAG-specific guidance
10. Use LightRAG performance baselines ← Project-specific data
11. Follow LightRAG integration guidelines ← Domain expertise

🔒 KEY: Steps 1-8 are GLOBAL MANDATORY (cannot bypass)
📋 KEY: Steps 9-11 are LOCAL CONTEXT (project-specific guidance)
```

#### **Multi-Phase Coordination**

```bash
# Global requirement (GEMINI.md Universal Agent Protocol)
- Complete task
- Update documentation
- Hand off to next phase

# Local extension (MULTI_PHASE_HANDOFF_PROTOCOL.md) - ADDS requirements
- Complete task
- Update documentation
- Create comprehensive hand-off document ← NEW
- Verify automated checklist compliance ← NEW
- Record quality assessment metrics ← NEW
- Hand off to next phase
```

---

## 🔄 **Workflow Integration Examples**

### **Example 1: Simple Bug Fix**

```bash
# 1. Check global protocols
read .agent/docs/sop/global-configs/GEMINI.md  # Universal Agent Protocol procedures
read ~/.agent/docs/sop/tdd-workflow.md  # Enhanced TDD workflow

# 2. Follow global TDD workflow
write_failing_test()     # Red phase
implement_minimal_fix()  # Green phase
verify_test_passes()     # Verification

# 3. Standard global completion
update_documentation()
commit_and_push()

# No local extensions needed
```

### **Example 2: New Performance Feature**

```bash
# 1. Check global protocols (base requirements)
read .agent/docs/sop/global-configs/GEMINI.md
read ~/.agent/docs/sop/tdd-workflow.md  # Enhanced TDD with enforcement

# 2. Apply local extensions (enhanced requirements)
read .agent/docs/sop/TDD_MANDATORY_GATE.md
read .agent/docs/sop/global-configs/KEYWORD_SEARCH_PERFORMANCE.md

# 3. Enhanced TDD workflow (global + local)
write_failing_test()           # Global TDD
implement_minimal_fix()        # Global TDD
verify_test_passes()           # Global TDD
run_performance_benchmarks()   # ← Local extension
document_tradeoffs()          # ← Local extension
pass_quality_gate()            # ← Local extension

# 4. Enhanced completion
update_documentation()
add_performance_notes()        # ← Local extension
commit_and_push()
```

### **Example 3: Multi-Phase Architecture**

```bash
# 1. Check global protocols (foundation)
read .agent/docs/sop/global-configs/GEMINI.md
read .agent/docs/sop/global-configs/COLLABORATION.md

# 2. Apply local extensions (complex coordination)
read .agent/docs/sop/MULTI_PHASE_HANDOFF_PROTOCOL.md

# 3. Phase 1 (global Universal Agent Protocol + local hand-off preparation)
complete_phase_1_work()
create_handoff_documentation()  # ← Local extension
prepare_automated_verification() # ← Local extension

# 4. Phase 2 (receiving hand-off)
verify_handoff_compliance()     # ← Local extension
continue_phase_2_work()
```

---

## ✅ **Compliance Validation**

### **Validation Command Sequence**

```bash
# Global SOP validation (ALWAYS REQUIRED - MANDATORY)
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --init
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --finalize

# Local extension validation (when applicable - context only)
./scripts/validate_tdd_compliance.sh <feature-name>           # LightRAG TDD validation
./scripts/verify_handoff_compliance.sh --phase <phase> --feature <feature>  # Multi-Phase coordination

# Integration verification
python ~/.agent/scripts/validate_sop_alignment.py             # Global/Local alignment
```

### **Validation Priority**

1. **🔒 Global compliance must pass first** - Cannot proceed if global validation fails (MANDATORY)
2. **Local extensions validated next** - Additional context for specific scenarios (optional guidance)
3. **Integration verification final** - Ensures global mandatory + local context work together

---

## 🚨 **Common Pitfalls & Solutions**

### **Pitfall 1: Skipping Global Standards**

**❌ Wrong**: "I'm doing a LightRAG feature, so I'll only read local docs"
**✅ Correct**: Always read global standards first, then apply local extensions

### **Pitfall 2: Treating Extensions as Replacements**

**❌ Wrong**: "The TDD Mandatory Gate replaces the global TDD workflow"
**✅ Correct**: Local extensions add requirements to global standards, they don't replace them

### **Pitfall 3: Conflicting Documentation**

**❌ Wrong**: "Global doc says X, local doc says Y - I'll pick one"
**✅ Correct**: Follow global standard as base, then comply with local additions

### **Pitfall 4: Missing Extension Triggers**

**❌ Wrong**: "All development uses the full TDD Mandatory Gate"
**✅ Correct**: Use extensions only when triggered (new features, performance work, etc.)

---

## 📚 **Reference Navigation**

### **By Scenario**

- **[🚀 Session Management](../global-configs/GEMINI.md)** - Global Universal Agent Protocol procedures
- **[🧪 Development Workflows](~/.agent/docs/sop/tdd-workflow.md)** - Global TDD workflow (mandatory enforcement)
- **[🔒 LightRAG TDD Guide](./TDD_MANDATORY_GATE.md)** - LightRAG implementation context
- **[🤝 Multi-Phase Coordination](./MULTI_PHASE_HANDOFF_PROTOCOL.md)** - Complex implementation

### **By Priority**

- **[🌐 Global SOP Hub](~/.agent/docs/sop/README.md)** - Universal standards (always first)
- **[🔧 LightRAG SOP](./README.md)** - Project-specific extensions (after global)
- **[📊 Performance Benchmarks](./global-configs/KEYWORD_SEARCH_PERFORMANCE.md)** - Performance guidelines

---

## 🔧 **Troubleshooting**

### **Validation Failures**

```bash
# Global validation fails → Fix global compliance first
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --init

# Local validation fails → Check extension applicability
./scripts/validate_tdd_compliance.sh --help

# Integration issues → Verify alignment
python ~/.agent/scripts/validate_sop_alignment.py
```

### **Documentation Conflicts**

```bash
# Check which protocols apply
./scripts/analyze_scenario.sh --task <description>

# Get recommended reading order
./scripts/sop_reading_order.sh --scenario <type>
```

---

**Last Updated**: 2026-02-06
**Scope**: LightRAG Project SOP Integration Guide
**Principle**: 🔒 Global mandatory compliance first, local extensions provide context only (never replace or override)
