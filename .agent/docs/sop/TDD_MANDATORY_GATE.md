# LightRAG TDD Implementation Guide

**Purpose**: LightRAG-specific implementation guidance for **global mandatory TDD standards**
**Base Standard**: [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md) - **🔒 MANDATORY foundation (cannot bypass)**
**Project Extension**: LightRAG-specific patterns and examples (context only)

---

## 🌐 **🔒 GLOBAL MANDATORY STANDARDS ARE SUPREME**

**⚠️ CRITICAL**: All LightRAG development **must** follow the [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md):

1. **🔒 Global Standards Are MANDATORY** - Cannot be bypassed, overridden, or skipped
2. **🔒 Enforcement Is Global** - All quality gates, validation, and blocking are from global standards
3. **📋 This Guide Provides Context Only** - LightRAG-specific patterns to apply global requirements
4. **⚠️ No Local Override** - This guide does NOT add or replace any global mandatory requirements

**🚨 CLARIFICATION**:
- **Global TDD**: MANDATORY enforcement, no bypass possible (Red→Green→Refactor+Performance+Quality Gates)
- **This Guide**: OPTIONAL context for applying global standards in LightRAG context
- **Violations**: Any attempt to bypass global TDD is automatically blocked regardless of local guidance

---

## 🔧 **LightRAG-Specific Implementation Patterns**

**🔒 Global Base**: **MANDATORY** - Follow [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md) exactly
**📋 LightRAG Context**: Use these patterns to **apply** global standards in LightRAG:

```bash
# LightRAG standard test organization
tests/
├── unit/                    # Unit tests (global pattern)
├── integration/             # Integration tests (global pattern)
├── benchmarks/              # Performance tests (LightRAG extension)
│   ├── keyword_search_performance.py
│   ├── graph_construction_speed.py
│   └── embedding_memory_usage.py
└── lightrag_specific/       # LightRAG domain tests
    ├── test_graph_algorithms.py
    ├── test_text_pipelines.py
    └── test_embedding_integration.py
```

### **2. LightRAG Performance Benchmarks**

**Global Base**: Performance assertions required by global TDD workflow
**LightRAG Extension**: Use these LightRAG-specific performance categories:

```yaml
LightRAG_Performance_Categories:
  Graph_Construction:
    - node_insertion_rate: ">1000 nodes/sec"
    - edge_creation_speed: "<5ms per edge"
    - memory_overhead: "<15% increase"

  Keyword_Search:
    - search_latency: "<50ms for 10k documents"
    - index_build_time: "<30 seconds"
    - memory_usage: "<500MB for full index"

  Embedding_Operations:
    - batch_embedding_speed: ">100 docs/sec"
    - vector_similarity_search: "<10ms"
    - model_loading_time: "<5 seconds"

  Text_Processing:
    - tokenization_speed: ">10k tokens/sec"
    - pipeline_latency: "<100ms per document"
    - memory_efficiency: "<100MB working set"
```

### **3. LightRAG Domain-Specific Testing**

**Global Base**: Standard functional testing patterns
**LightRAG Extension**: Domain-specific test scenarios:

```python
# Example: LightRAG Graph Algorithm Tests
class TestGraphAlgorithmsTDD:
    def test_community_detection_performance(self):
        """RED Phase: This should FAIL initially"""
        # Define performance expectations
        graph = create_test_graph(10000)  # 10k nodes
        start_time = time.time()

        communities = detect_communities(graph)

        duration = time.time() - start_time
        assert duration < 5.0, f"Community detection too slow: {duration}s"
        assert len(communities) > 0, "No communities detected"

    def test_centrality_calculation_accuracy(self):
        """RED Phase: Accuracy and speed test"""
        graph = create_known_test_graph()

        centrality_scores = calculate_centrality(graph)

        # Accuracy assertion
        expected_scores = get_expected_centrality_scores()
        assert centrality_scores == expected_scores, "Centrality calculation incorrect"

        # Performance assertion
        assert time_taken < 1.0, "Centrality calculation too slow"
```

---

## 📊 **LightRAG Performance Baselines**

**🔒 Global Base**: **MANDATORY** - Baseline documentation required by [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)
**📋 LightRAG Context**: Use these **project-specific** baseline measurements to meet global requirements:

### **Current LightRAG Baselines** (Updated 2026-02-06)

```yaml
Baseline_Measurements:
  Keyword_Search_Index:
    Build_Time: "25 seconds for 10k documents"
    Memory_Usage: "450MB"
    Search_Latency: "35ms average"

  Graph_Construction:
    Node_Insertion: "1200 nodes/sec"
    Edge_Creation: "3ms per edge"
    Memory_Overhead: "12%"

  Embedding_Pipeline:
    Model_Load: "3.2 seconds"
    Batch_Processing: "150 docs/sec"
    Similarity_Search: "7ms"
```

### **When to Update Baselines**:

1. **Algorithm Changes**: Re-measure all affected baselines
2. **Infrastructure Updates**: Update memory and timing benchmarks
3. **New Features**: Add new baseline categories
4. **Performance Regressions**: Document and investigate

---

## 🔄 **LightRAG Multi-Phase Integration**

**🔒 Global Base**: **MANDATORY** - Standard TDD Red→Green→Refactor cycle from [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)
**📋 LightRAG Context**: Multi-phase coordination patterns for **applying** global requirements to complex features:

```yaml
LightRAG_Multi_Phase_Pattern:
  Phase_1_Foundation:
    - Create failing tests for core algorithm
    - Implement basic functionality
    - Validate performance baseline

  Phase_2_Optimization:
    - Add performance benchmarks
    - Implement optimizations
    - Validate no regression

  Phase_3_Integration:
    - Add integration tests
    - Validate end-to-end performance
    - Document tradeoff analysis
```

---

## 🎯 **LightRAG-Specific Success Criteria**

**Global Base**: Universal success criteria from global TDD workflow
**LightRAG Extension**: Domain-specific validation:

### **Algorithm Features**
- ✅ **Correctness**: Passes all functional tests
- ✅ **Performance**: Meets LightRAG speed benchmarks
- ✅ **Scalability**: Handles target data sizes efficiently
- ✅ **Memory**: Stays within LightRAG memory constraints

### **Integration Features**
- ✅ **Compatibility**: Works with existing LightRAG pipelines
- ✅ **Backwards Compatibility**: Doesn't break existing APIs
- ✅ **Configuration**: Proper settings and parameter handling
- ✅ **Error Handling**: Graceful failure modes

### **Infrastructure Features**
- ✅ **Deployment**: Can be deployed in LightRAG environments
- ✅ **Monitoring**: Provides performance metrics
- ✅ **Debugging**: Includes debugging capabilities
- ✅ **Documentation**: Complete usage guidelines

---

## 🚀 **LightRAG Implementation Examples**

### **Example 1: Keyword Search Optimization**

```bash
# Step 1: Read global TDD workflow
cat ~/.agent/docs/sop/tdd-workflow.md

# Step 2: Create failing tests (RED)
cat > tests/keyword_search_optimization_tdd.py << 'EOF'
def test_search_speed_improvement():
    """Should FAIL initially - optimization not implemented"""
    documents = load_test_documents(10000)
    searcher = KeywordSearcher()

    start_time = time.time()
    results = searcher.search("test query", documents)
    duration = time.time() - start_time

    assert duration < 0.05, f"Search too slow: {duration}s"  # 50ms target
    assert len(results) > 0, "No results found"
EOF

# Step 3: Verify tests fail
pytest tests/keyword_search_optimization_tdd.py -v  # Should FAIL

# Step 4: Implement optimization (GREEN)
# ... implementation code ...

# Step 5: Verify tests pass
pytest tests/keyword_search_optimization_tdd.py -v  # Should PASS

# Step 6: Add comprehensive benchmarks
cat > tests/keyword_search_benchmarks.py << 'EOF'
def test_search_performance_benchmarks():
    """Performance validation"""
    # Benchmark against LightRAG baselines
    assert search_latency < 50, "Exceeds LightRAG baseline of 35ms"
    assert memory_usage < 500, "Exceeds LightRAG baseline of 450MB"
EOF
```

---

## 🔧 **LightRAG Development Tools**

**🔒 Global Base**: **MANDATORY** - Standard development tooling from global standards
**📋 LightRAG Context**: Project-specific validation scripts that **invoke** global requirements:

```bash
# LightRAG-specific validation (calls global standards)
./scripts/validate_lightrag_tdd.sh <feature_name>
./scripts/benchmark_lightrag_performance.sh <component>
./scripts/verify_lightrag_baselines.sh <feature>

# These scripts invoke global validation while adding LightRAG context
```

---

## 📚 **LightRAG Documentation Templates**

**🔒 Global Base**: **MANDATORY** - Standard documentation requirements from [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)
**📋 LightRAG Context**: Use these templates to **meet** global requirements for LightRAG features:

### **Performance Analysis Template**

```markdown
# Feature Performance Analysis - <Feature Name>

## Global Compliance
✅ Follows [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)
✅ Meets global performance requirements
✅ Includes mandatory tradeoff analysis

## LightRAG-Specific Performance

### Baseline Comparison
| Metric | Baseline | Current | Improvement | Status |
|--------|----------|---------|-------------|--------|
| Search Latency | 35ms | 28ms | 20% faster | ✅ |
| Memory Usage | 450MB | 420MB | 7% reduction | ✅ |
| Index Build Time | 25s | 22s | 12% faster | ✅ |

### LightRAG Integration Impact
- **Pipeline Compatibility**: Works with existing text processing
- **API Consistency**: Maintains backwards compatibility
- **Configuration**: No breaking changes to settings

### Deployment Readiness
- **Production Guidelines**: [Link to deployment doc]
- **Monitoring Metrics**: [Link to monitoring setup]
- **Rollback Plan**: Documented rollback procedure
```

---

## 🚨 **LightRAG-Specific Pitfalls**

**🔒 Global Base**: **MANDATORY** - Universal TDD pitfalls from [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)
**📋 LightRAG Context**: Common mistakes when **applying** global standards in LightRAG context:

### **Pitfall 1: Ignoring Graph Performance**
**❌ Wrong**: "Graph algorithm works, performance doesn't matter"
**✅ Correct**: Graph operations must meet LightRAG speed benchmarks

### **Pitfall 2: Memory Overlook**
**❌ Wrong**: "Embedding works, memory usage is fine"
**✅ Correct**: Memory must stay within LightRAG baseline constraints

### **Pitfall 3: Integration Testing**
**❌ Wrong**: "Feature works in isolation"
**✅ Correct**: Must validate with LightRAG pipeline integration

---

## 📞 **LightRAG Support**

### **LightRAG-Specific Help**
- **Examples**: See `tests/examples/` for LightRAG TDD patterns
- **Templates**: Use `.templates/lightrag_tdd/` for starting points
- **Benchmarks**: Reference `tests/benchmarks/` for performance patterns

### **When TDD Issues Occur**
1. **Check Global Compliance First**: Verify global TDD workflow is followed
2. **Apply LightRAG Patterns**: Use LightRAG-specific implementation guides
3. **Validate Performance**: Ensure LightRAG benchmarks are met
4. **Document Tradeoffs**: Include LightRAG-specific performance analysis

---

**🔗 INTEGRATION STATEMENT**:
This guide **extends** the **🔒 [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)** with LightRAG-specific implementation patterns. **Global standards are mandatory and supreme** - this guide **only** provides LightRAG context for applying mandatory requirements.

**⚠️ LAST UPDATED**: 2026-02-06
**🔄 BASE STANDARD**: **🔒 [Global TDD Workflow](~/.agent/docs/sop/tdd-workflow.md)** (MANDATORY enforcement - cannot bypass)

---

## 🚀 **IMPLEMENTATION READINESS VALIDATION**

### **Automated Checks**

#### **1. Implementation Readiness Check**

```bash
# Must run before any implementation
python .agent/scripts/validate_implementation_ready.py
# Expected: All implementation checks PASS
```

### **Implementation Readiness Requirements**

#### **1. Beads Issue Exists (MANDATORY)**

- [ ] **Active beads issue** assigned to current work
- [ ] **Issue status** is "open" or "in-progress"
- [ ] **Issue metadata** properly configured with type and priority

#### **2. Feature Branch Active (MANDATORY)**

- [ ] **Not on protected branch** (main, master, develop, dev)
- [ ] **Feature branch created** with descriptive name
- [ ] **Code changes isolated** from main development line

### **Manual Validation Points**

#### **Implementation Readiness Evidence**

- [ ] **Beads Issue ID**: Valid issue exists in tracking system
- [ ] **Branch Name**: Feature branch follows naming conventions
- [ ] **Git Status**: Clean isolation from main branch
- [ ] **Work Context**: Current task properly scoped and assigned

---

## 🔍 **TDD COMPLIANCE VALIDATION**

### **Automated Checks**

#### **1. Test Structure Validation**

```bash
# Must run before any implementation
python -m pytest tests/feature_*_tdd.py --dry-run
# Expected: All tests should FAIL (red phase)
```

#### **2. Implementation Validation**

```bash
# Must run after implementation
python -m pytest tests/feature_*_tdd.py tests/feature_*_functional.py
# Expected: All tests should PASS (green phase)
```

#### **3. Performance Validation**

```bash
# Must run for performance features
python -m pytest tests/feature_*_benchmarks.py
# Expected: All performance assertions PASS
```

### **Manual Validation Points**

#### **1. Test-First Evidence**

- [ ] **Failing Tests Written** BEFORE any implementation code
- [ ] **Test Commit Exists** with failing test results
- [ ] **Test Names Follow Convention**: `test_*_tdd.py`
- [ ] **Tests Define Expectations**: Clear performance thresholds

#### **2. Performance-First Evidence**

- [ ] **Baseline Measurements**: Document current performance
- [ ] **Speed Assertions**: Minimum % improvement defined
- [ ] **Memory Assertions**: Maximum overhead thresholds defined
- [ ] **Scalability Assertions**: Degradation limits defined

#### **3. Tradeoff Analysis Evidence**

- [ ] **Speed vs Memory**: Quantified tradeoff analysis
- [ ] **Algorithm Comparison**: Multiple options benchmarked
- [ ] **Use Case Guidelines**: When to use/not use feature
- [ ] **Production Readiness**: Deployment guidelines documented

---

## 🚫 **IMPOSSIBLE TO BYPASS**

### **System-Level Enforcement**

#### **1. Pre-Flight Gate Blocking**

```python
def validate_tdd_compliance(feature_name):
    """Automatic TDD validation - CANNOT BYPASS"""
    tdd_requirements = {
        'failing_tests_exist': check_failing_tests(feature_name),
        'baseline_measured': check_baseline_documented(feature_name),
        'performance_assertions': check_performance_assertions(feature_name),
        'benchmarks_exist': check_benchmark_tests(feature_name),
        'tradeoffs_analyzed': check_tradeoff_documentation(feature_name)
    }

    if not all(tdd_requirements.values()):
        block_work_with_tdd_violation(tdd_requirements)

    return tdd_requirements
```

#### **2. Work Session Validation**

```python
def validate_session_tdd_compliance():
    """Session completion validation - CANNOT PROCEED WITHOUT"""

    # Check git history for TDD compliance
    commits = get_feature_commits()
    tdd_timeline = validate_tdd_timeline(commits)

    # Check required artifacts exist
    required_artifacts = [
        'tests/feature_*_tdd.py',           # Failing tests first
        'tests/feature_*_benchmarks.py',        # Performance benchmarks
        'docs/feature_*_tradeoffs.md',        # Tradeoff analysis
        'tests/feature_*_functional.py'       # Passing tests after
    ]

    missing_artifacts = [artifact for artifact in required_artifacts
                       if not file_exists(artifact)]

    if missing_artifacts:
        block_session_completion(missing_artifacts, tdd_timeline)

    return True
```

### **3. Quality Gate Enforcement**

```python
def enforce_tdd_quality_gates():
    """Quality gates - CANNOT SKIP"""

    quality_checks = {
        'test_coverage': check_test_coverage(),
        'performance_benchmarks': check_benchmark_results(),
        'documentation_quality': check_tradeoff_analysis(),
        'measurable_metrics': check_quantified_assertions()
    }

    failed_checks = [check for check, result in quality_checks.items()
                    if not result]

    if failed_checks:
        raise TDDEnforcementError(
            "TDD quality gates failed: " + str(failed_checks),
            blocking=True  # CANNOT BYPASS
        )

    return quality_checks
```

---

## 📋 **TDD COMPLIANCE CHECKLIST**

### **Phase 1: Test Design (RED)**

- [ ] **Write Failing Tests First**: Define expectations that initially fail
- [ ] **Document Baseline Performance**: Measure current system behavior
- [ ] **Define Success Metrics**: Quantifiable improvement targets
- [ ] **Create Benchmark Suite**: Performance comparison tests ready
- [ ] **Establish Tradeoff Framework**: Analysis structure prepared

### **Phase 2: Implementation (GREEN)**

- [ ] **Implement to Pass Tests**: Code makes failing tests pass
- [ ] **Maintain Test Integrity**: Don't modify test expectations
- [ ] **Run Benchmark Validation**: Measure against baseline
- [ ] **Document All Tradeoffs**: Speed, memory, complexity analysis
- [ ] **Verify Performance Claims**: All assertions should pass

### **Phase 3: Validation (REFACTOR)**

- [ ] **Complete Performance Analysis**: Full benchmarking report
- [ ] **Document Production Guidelines**: When/how to use feature
- [ ] **Create Monitoring Plan**: Ongoing performance tracking
- [ ] **Update Documentation**: Global index and navigation updated
- [ ] **Pass All Quality Gates**: System validation succeeds

---

## 🚨 **TDD VIOLATION CONSEQUENCES**

### **Automatic Blocks**

- **Work Cannot Start**: PFC gate blocks non-compliant features
- **Session Cannot Complete**: Finalization gate blocks incomplete TDD
- **Deployment Blocked**: Quality gates prevent non-validated features
- **Merge Rejected**: Quality checks fail without TDD evidence

### **Manual Override Process** (IMPOSSIBLE)

```python
# THERE IS NO MANUAL OVERRIDE FOR TDD GATES

def attempt_tdd_override(reason: str):
    """IMPOSSIBLE FUNCTION - Always blocks"""
    # This function exists to make it clear that overrides are impossible
    raise TDDEnforcementError(
        f"TDD override attempted: {reason}. " +
        "TDD compliance is MANDATORY and CANNOT be bypassed. " +
        "Follow the TDD process or work cannot proceed.",
        override_impossible=True
    )
```

### **Escalation Path** (IF VIOLATION)

1. **Immediate Block**: All work stops at point of violation
2. **Violation Logged**: Permanent record of TDD bypass attempt
3. **Review Required**: Team lead review before any further work
4. **Remediation Required**: Complete proper TDD process before continuation

---

## 🔧 **IMPLEMENTATION INTEGRATION**

### **1. Agent Integration**

```bash
# Built into all agent workflows
./agent/scripts/validate_tdd_compliance.sh --feature <feature_name>
./agent/scripts/check_tdd_artifacts.sh --session <session_id>
./agent/scripts/enforce_tdd_gates.sh --quality-check
```

### **2. Development Workflow Integration**

```bash
# Pre-commit hooks for TDD validation
.git/hooks/pre-commit:
  ├── validate_tdd_artifacts.sh
  ├── run_tdd_test_suite.sh
  └── check_benchmark_coverage.sh

# Pre-push hooks for quality gates
.git/hooks/pre-push:
  ├── run_full_test_suite.sh
  ├── validate_performance_benchmarks.sh
  └── check_documentation_completeness.sh
```

### **3. CI/CD Integration**

```yaml
# GitHub Actions or similar CI/CD
TDD_Validation_Pipeline:
  - Stage_1: Validate_TDD_Artifacts
  - Stage_2: Run_TDD_Test_Suite
  - Stage_3: Execute_Performance_Benchmarks
  - Stage_4: Validate_Documentation_Quality
  - Stage_5: Enforce_Quality_Gates

Blocking: true  # Pipeline fails if any stage fails
```

---

## 📚 **REFERENCES & EXAMPLES**

### **Valid TDD Implementation Example**

- **Reference**: Community Detection Feature (`lightrag-bkj.2`)
- **Timeline**:
  - ❌ Week 1: Failing tests written (RED)
  - 🟢 Week 1: Implementation passes tests (GREEN)
  - 🔄 Week 2: Performance benchmarks created
  - 📊 Week 2: Tradeoff analysis completed
- **Result**: ✅ All TDD requirements met, feature delivered

### **Invalid TDD Bypass Attempt**

- **What Happens**: Agent tries to implement without failing tests
- **System Response**: Work blocked at PFC gate
- **Required Action**: Complete TDD process before continuation
- **Learning Opportunity**: Document as TDD training case

---

## 🎯 **QUALITY METRICS FOR TDD**

Every feature MUST meet these minimum standards:

### **Test Coverage Requirements**

- **Functional Tests**: ≥90% code coverage
- **Benchmark Tests**: 100% of performance claims validated
- **Edge Case Tests**: All error conditions covered
- **Integration Tests**: Real-world usage scenarios validated

### **Performance Documentation Requirements**

- **Speed Claims**: Must have measured % improvement
- **Memory Claims**: Must have measured overhead analysis
- **Scalability Claims**: Must have growth rate analysis
- **Tradeoff Analysis**: Must document all resource costs

### **Documentation Completeness Requirements**

- **Usage Guidelines**: Clear when/how to use feature
- **Performance Tradeoffs**: Detailed speed vs resource analysis
- **Production Readiness**: Deployment and monitoring guidelines
- **Troubleshooting Guide**: Common issues and solutions

---

## 🔐 **SECURITY & COMPLIANCE**

### **TDD Gate Tampering Prevention**

```python
class TDDGateSecurity:
    """Prevents any attempt to bypass TDD requirements"""

    def __init__(self):
        self.gate_status = "ENFORCED"
        self.bypass_attempts = 0
        self.violation_log = []

    def validate_compliance(self, feature_context):
        """Cannot be bypassed - no override capability"""
        if self.check_bypass_attempt():
            self.log_security_violation(feature_context)
            self.permanent_block()

        return self.enforce_tdd_requirements(feature_context)

    def permanent_block(self):
        """Permanent block - requires admin intervention"""
        raise SystemExit("TDD security violation - contact administrator")
```

### **Audit Trail**

- **All TDD Decisions Logged**: Immutable audit trail
- **Bypass Attempts Recorded**: Security violations tracked
- **Compliance Reports**: Regular TDD adherence reporting
- **Training Records**: TDD process education tracked

---

## 📞 **SUPPORT & ESCALATION**

### **TDD Process Help**

- **Documentation**: This SOP provides complete TDD guidance
- **Examples**: Reference implementations available
- **Templates**: TDD test and benchmark templates
- **Training**: Regular TDD methodology training

### **When TDD Block Occurs**

1. **Don't Panic**: Block is expected behavior
2. **Review SOP**: Follow this TDD gate documentation
3. **Complete Missing Requirements**: Use checklist to identify gaps
4. **Request Help**: Escalate if genuinely unclear on requirements

### **TDD Success Criteria**

- **All Gates Pass**: PFC and Finalization validation successful
- **Quality Metrics Met**: Coverage and performance standards achieved
- **Documentation Complete**: All required artifacts created
- **Feature Ready**: Production deployment approved

---

**🔒 ENFORCEMENT STATEMENT**:
TDD compliance is **MANDATORY** for all LightRAG development. These gates **CANNOT** be bypassed, overridden, or skipped. Any attempt to bypass TDD requirements will be **automatically blocked** and logged as a security violation. **This is not a guideline - this is a requirement.**

**⚠️ LAST UPDATED**: 2026-02-04
**🔄 REVIEW CYCLE**: Quarterly or when violations occur
**👮 APPROVAL**: LightRAG Technical Lead + Architectural Review Board
