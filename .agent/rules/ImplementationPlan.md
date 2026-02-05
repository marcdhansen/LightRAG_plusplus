# Evaluation Framework Standardization (RAGAS + Langfuse)

## Goal

Establish a robust evaluation pipeline to measure RAG quality (Context Recall, Faithfulness, Answer Relevance) using RAGAS, and visualize traces/metrics in Langfuse.

## Graph Reranking & Evaluation Framework

## Status: COMPLETE (2026-01-27)

* [x] **Langfuse Integration**: Traces and RAGAS scores are automatically sent to local Langfuse.
* [x] **Tiered Testing**: Pytest-based `light` and `heavy` paths implemented.
* [x] **Graph Reranking**: Implemented `rerank_entities` and `rerank_relations` with perfect faithfulness.
* [x] **Prompt Optimization**:
  * Implemented YAML-based extraction for small models.
  * 7B reaches 100% entity recall on Einstein benchmark; 1.5B/3B require gleaning=2 for similar results but remain inconsistent on abstract concepts.
* [x] **Documentation**:
  * `docs/OBSERVABILITY.md`, `docs/EVALUATION.md`, `docs/ACE_FRAMEWORK.md`, `docs/GRAPH_RERANKING.md`.

## Next Phase: ACE Optimization & Visualization (Current)

Establish the full ACE cycle in production and provide visual tooling for graph inspection.

* [x] **Graph Visualization**: Implement/Verify a dedicated visualizer for the knowledge graph (Beads: lightrag-42q).
* [x] **ACE Phase 3**: Finalize minimal framework prototype and deployment endpoints (Beads: lightrag-q29).
* [x] **UI Integration**: Add reranking toggles and ACE controls to the WebUI.
* [x] **ACE Asymmetric Routing**: Implement routing logic for Extraction vs. Reflection models (lightrag-043).
* [x] **ACE Curator (Phase 5)**: Implement graph pruning and deduplication logic (lightrag-56n).
* [x] **ACE Human-in-the-Loop**: Enable manual review of graph repairs via WebUI (Beads: lightrag-euu).
* [x] **Review Tab Visualization**: Integrate Graph Visualizer to inspect repair impact (Beads: lightrag-4u6).

## Phase: Infrastructure & Process Improvements (Current)

Strengthen the development lifecycle by enhancing automated checks and standardizing environment-specific configurations.

* [x] **Flight Director Enhancement**: Automate RTB cleanup and document verification (Beads: lightrag-ijs).
* [x] **Extraction Standardization**: Hard-code YAML for offline LLMs (Beads: lightrag-6h1).
* [x] **Reasoning Threshold Policy**: Formalize model requirements for reflection (Beads: lightrag-oi6).
* [x] **Continuous UI Testing**: Implement Playwright for automated frontend validation (Beads: lightrag-fan).
* [x] **ACE Standardized Testing**: Implemented `ACETestKit` for Injection-Reflection-Repair verification (Beads: lightrag-dog).
* [x] **Type Safety & Reliability Refactoring**: Resolved critical Pyright errors in `core.py`, `base.py`, and `utils_graph.py`. Relaxed graph data types to `dict[str, Any]` and fixed suspected `None` attribute access (Beads: lightrag-3mc).
* [x] **Architectural Consolidation**: Centralized ACE control loop in `ACEGenerator` to prevent redundant reflection triggers in `LightRAG.ace_query`.
* [x] **Documentation Directory Hardening**: Modified `.gitignore` in `~/.gemini`, `~/.antigravity`, and project `.agent` directories to ignore all files except markdown (Beads: lightrag-986).
* [x] **Automatic Bloat Removal**: Implement cleanup steps in RTB to prune binary bloat and temporary files in global config directories (Beads: lightrag-987).
* [x] **Beads Sync Optimization**: Modified `.gitignore` to track `.beads/issues.jsonl`, resolving "operation not permitted" errors (Beads: lightrag-988).
* [x] **Reflect Skill Formalization**: Updated `reflect` skill with standard mission processes, structured debriefing, and PFC/RTB analysis (Beads: lightrag-982).
* [x] **Universal SOP Standardization**: Documented cross-IDE/agent compatibility design in `CROSS_COMPATIBILITY.md` and integrated into `GLOBAL_INDEX.md` (Beads: lightrag-989).
* [x] **Plan-Blocker Implementation** (Beads: lightrag-fd1):
  * Enhanced `Flight Director` script to enforce a "Plan Approval" check in PFC.
  * Required marker: `## Approval: [User Sign-off at YYYY-MM-DD HH:MM...]` in `task.md`.
  * Status: Complete - agent cannot enter IFO without explicit approval marker.
* [x] **Container Management SOP Rule**: Added rule to global SMP (GEMINI.md) to run Docker without Docker Desktop to minimize resource consumption (Beads: lightrag-2kp).

## Agent Mission Protocol (AMP)

To ensure coordination and safety in multi-agent environments, the following gates are enforced:

1. **Pre-Flight Check (PFC)**: Verifies tools, Beads, and planning documents.
2. **Isolation Gate**: Verifies the agent is on a dedicated task branch and using a unique filesystem path (Worktree isolation).
3. **Plan-Blocker Gate**: Prevents implementation from starting until the user has added a fresh `## Approval` marker to the `task.md`. Approvals are only valid for 4 hours from the timestamp.
4. **Execution Handshake**: For tasks involving "Heavy Execution" (benchmarks, indexing, multi-hour scripts), the agent MUST explicitly list the proposed command and wait for a "Go" signal (e.g., "Go", "Execute", "Proceed"), even if the plan is approved.
5. **Return To Base (RTB)**: Verifies cleanup, linting, git sync, and clears/neutralizes the approval marker.

## Phase 6: ACE Optimizer (Current)

**Target**: Refine the ACE framework for production-grade reliability and performance on small models (Ollama 1.5B/7B).

**Objective**: Achieve consistent, high-quality knowledge graph extraction and reasoning on resource-constrained models through systematic prompt engineering, curator optimization, and comprehensive benchmarking.

### 6.1 Prompt Optimization (1.5B/7B) - **Priority: P2**

**Goal**: Achieve 95%+ extraction accuracy and eliminate hallucinations on small models.

* [x] **Baseline Audit** (Beads: lightrag-992):
  * Run extraction benchmarks on Einstein/Dickens test sets with 1.5B, 3B, and 7B models
  * Measure: entity recall, relationship accuracy, YAML compliance rate, hallucination frequency
  * Document failure patterns: missing concepts, malformed YAML, entity duplication
  * **Success Criteria**: Baseline metrics documented in [baseline_audit_report.md](../../audit_results/baseline_audit_report.md)
  * **Update (2026-02-04)**: Verified **+38% (Few-NERD)** and **+43% (Text2KGBench)** F1 improvement over original HKUDS repo. See [ORIGINAL_REPO_COMPARISON.md](../benchmarks/ORIGINAL_REPO_COMPARISON.md).

* [x] **Extraction Prompt Enhancement** (Beads: lightrag-fv9):
  * Implement explicit "Concept Extraction" instructions with examples
  * Add YAML schema constraints to prevent malformed output
  * Test gleaning=2 vs. gleaning=1 for small models
  * **Success Criteria**: 95% YAML compliance, 90% entity recall on 7B models
  * **Status**: Complete (2026-02-04) - Achieved 100% rel accuracy on 3B and
    75% on 1.5B (Einstein case) via dense linking prompts and gleaning.

* [ ] **Reflection Prompt Refinement**:
  * Design Chain-of-Thought (CoT) prompts for ACE Reflector
  * Add structured reasoning templates: "Evidence → Analysis → Conclusion"
  * Implement hallucination detection heuristics in prompts
  * **Success Criteria**: 80% hallucination detection rate, 70% repair accuracy

* [ ] **Prompt Versioning & A/B Testing**:
  * Create `lightrag/prompts/versions/` directory for prompt history
  * Implement A/B testing framework for prompt variants
  * Track performance metrics per prompt version
  * **Success Criteria**: Automated prompt regression testing in CI/CD

### 6.2 Curator 2.0 (Adaptive Memory) - **Priority: P3**

**Goal**: Implement intelligent playbook management to prevent context bloat and improve relevance.

* [ ] **Similarity-Based Deduplication**:
  * Implement embedding-based similarity detection for Context Playbook entries
  * Merge duplicate insights with confidence scoring
  * **Success Criteria**: 50% reduction in redundant playbook entries

* [ ] **Importance Scoring**:
  * Design utility scoring algorithm: frequency × recency × impact
  * Implement automatic pruning of low-utility insights (score < threshold)
  * Add manual review interface for borderline cases
  * **Success Criteria**: Playbook size stable at <100 entries with high relevance

* [ ] **Temporal Decay**:
  * Implement time-based relevance decay for older insights
  * Add "refresh" mechanism for frequently-used insights
  * **Success Criteria**: Playbook automatically adapts to evolving knowledge base

### 6.3 Source Attribution & Citations - **Priority: P2**

**Goal**: Enable full traceability from LLM responses back to original source documents.

* [x] **Graph Storage Enhancement** (Beads: lightrag-8g4):
  * Implemented automatic citation generation using Zilliz semantic highlighting
  * Added `auto_citations` and `citation_threshold` parameters to QueryParam
  * **Status**: Complete - citations now include highlighted excerpts with relevance scores

* [ ] **ACE Reasoning Citations**:
  * Update `ACEGenerator` to include markdown citations `[^N]` in reasoning trajectories
  * Link each repair action to specific source chunks
  * **Success Criteria**: Every ACE repair traceable to source evidence

* [ ] **Citation Validation**:
  * Implement citation accuracy tests: verify cited chunks support claims
  * Add citation coverage metrics to benchmarks
  * **Success Criteria**: 90% citation accuracy, 80% coverage of key facts

### 6.4 Visual Repair Debugging - **Priority**: P3**

**Goal**: Provide intuitive UI for inspecting and validating ACE repairs.

* [x] **Graph Visualizer Integration** (Beads: lightrag-4u6):
  * Integrated Sigma.js graph visualization in Review tab
  * **Status**: Complete - users can inspect graph structure before/after repairs

* [ ] **Side-by-Side Diff View**:
  * Implement graph diff visualization showing added/removed/modified nodes
  * Add color coding: green (added), red (removed), yellow (modified)
  * **Success Criteria**: Users can visually validate repairs before approval

* [ ] **Repair Impact Analysis**:
  * Show downstream effects of repairs (e.g., "Merging entities affects 5 relationships")
  * Add "undo" functionality for approved repairs
  * **Success Criteria**: Zero unintended side-effects from repairs

### 6.5 Automated Benchmarking Suite - **Priority: P2**

**Goal**: Prevent quality regression through continuous integration testing.

* [x] **ACETestKit Implementation** (Beads: lightrag-dog):
  * Created standardized Injection-Reflection-Repair test pattern
  * **Status**: Complete - framework ready for CI/CD integration

* [ ] **CI/CD Integration**:
  * Add ACE benchmarks to GitHub Actions workflow
  * Set quality gates: fail build if accuracy drops >5%
  * Generate performance reports with trend analysis
  * **Success Criteria**: Automated quality monitoring on every PR

* [ ] **Multi-Model Benchmarking**:
  * Test ACE performance across 1.5B, 3B, 7B, and 14B models
  * Document speed-accuracy tradeoffs for each model size
  * **Success Criteria**: Clear model selection guidelines based on use case

### 6.6 Performance Optimization - **Priority: P3**

**Goal**: Reduce ACE overhead to <20% of baseline query time.

* [ ] **Reflection Caching**:
  * Cache reflection results for identical graph states
  * Implement cache invalidation on graph updates
  * **Success Criteria**: 50% reduction in redundant reflections

* [ ] **Parallel Reflection**:
  * Run reflection on multiple graph regions concurrently
  * Implement conflict resolution for overlapping repairs
  * **Success Criteria**: 2x speedup on large graphs (>1000 nodes)

* [ ] **Adaptive Reflection Frequency**:
  * Trigger reflection only when graph quality drops below threshold
  * Implement "quiet periods" to skip reflection on stable graphs
  * **Success Criteria**: 70% reduction in unnecessary reflections

### Phase 6 Success Metrics

* **Extraction Quality**: 95% entity recall, 90% relationship accuracy on 7B models
* **Hallucination Rate**: <5% false entities/relationships
* **YAML Compliance**: 100% valid YAML output from extraction
* **ACE Repair Accuracy**: 80% of repairs improve graph quality
* **Performance**: ACE overhead <20% of baseline query time
* **User Satisfaction**: 90% of repairs approved without modification

## Phase 7: MCP Expansion (Upcoming)

* [ ] **LightRAG as MCP Server**: Expose retrieval/indexing capabilities.
* [ ] **LightRAG as MCP Client**: Allow the extractor to browse the web or read local files via MCP.

## Phase 8: Safety Guardrails Enhancement (Planned)

**Target**: Implement comprehensive, production-ready safety guardrails to protect users and ensure compliance across all deployment scenarios.

**Objective**: Build multi-layered safety system combining GroundedAI local processing with complementary protection mechanisms for enterprise-grade security and user protection.

### 8.1 GroundedAI Real-time Integration (Priority: P1)

**Goal**: Convert existing GroundedAI evaluation capabilities into real-time safety enforcement.

* [ ] **Real-time Safety Middleware**:
  * Convert `GroundedAIRAGEvaluator` from evaluation to prevention mode
  * Implement pre/post-response filtering with configurable thresholds
  * Add safety middleware to FastAPI application pipeline
  * **Success Criteria**: <50ms safety response time, 95% harmful content blocked

* [ ] **API Integration & Caching**:
  * Integrate safety checks into existing API routes (`/query`, `/extract`)
  * Implement safety evaluation caching for repeated content
  * Add safety metrics collection and monitoring
  * **Success Criteria**: <20% system overhead, comprehensive safety logging

### 8.2 Complementary Safety Layer (Priority: P1)

**Goal**: Add protection capabilities beyond GroundedAI's scope (prompt injection, PII, content filtering).

* [ ] **Prompt Injection Protection**:
  * Implement Llama Prompt Guard 2 or equivalent
  * Add adversarial input detection and sanitization
  * Create prompt pattern validation pipeline
  * **Success Criteria**: 95% prompt injection detection rate, <2% false positives

* [ ] **PII Detection & Redaction**:
  * Integrate spaCy/presidio for comprehensive PII detection
  * Implement automatic redaction with configurable policies
  * Add support for custom PII entity types
  * **Success Criteria**: 99% PII detection accuracy, minimal false positives

* [ ] **Content Filtering Enhancement**:
  * Add hate speech, violence, explicit content detection
  * Implement content category-based filtering policies
  * Create multi-modal content safety (text, images, documents)
  * **Success Criteria**: Block >90% harmful content categories

* [ ] **Rate Limiting & Abuse Detection**:
  * Implement multi-dimensional rate limiting (user, IP, token)
  * Add abuse pattern detection and automated blocking
  * Create adaptive rate limiting based on behavior
  * **Success Criteria**: Prevent abuse while minimizing legitimate user impact

### 8.3 Advanced Safety Features (Priority: P2)

**Goal**: Implement enterprise-grade safety capabilities for regulated industries.

* [ ] **Context-Aware Safety Policies**:
  * Domain-specific safety rules (healthcare, finance, education)
  * Role-based safety policies and access controls
  * Contextual content filtering based on use case
  * **Success Criteria**: Flexible policy engine supporting multiple domains

* [ ] **Audit Trails & Compliance**:
  * Comprehensive security event logging with immutable records
  * Compliance reporting for HIPAA, GDPR, SOX, etc.
  * Automated compliance validation and reporting
  * **Success Criteria**: Full audit trail coverage, automated compliance checks

* [ ] **Multi-Vendor Safety Orchestration**:
  * Combine GroundedAI, AWS Bedrock, Azure AI Content Safety
  * Implement safety priority routing and fallback mechanisms
  * Create unified safety management interface
  * **Success Criteria**: Seamless integration across multiple safety providers

* [ ] **Safety Performance Analytics**:
  * Safety effectiveness monitoring and optimization
  * Performance impact analysis and tuning
  * Continuous improvement through machine learning
  * **Success Criteria**: Data-driven safety optimization, minimal performance impact

### Phase 8 Success Metrics

* **Safety Coverage**: >95% of harmful content blocked across all categories
* **Performance Impact**: <20% overhead on baseline query response times
* **False Positive Rate**: <5% for legitimate content
* **Compliance**: 100% audit trail coverage, automated compliance reporting
* **User Experience**: >90% user satisfaction with safety measures
* **Reliability**: >99.9% safety system uptime, graceful degradation on failures

### Dependencies & Integration

* **Prerequisites**: Phase 6 (ACE Optimizer) completion
* **Integration Points**: API middleware, query pipeline, configuration system
* **Cross-Functional Requirements**: Legal, compliance, security teams
* **Documentation**: User safety guidelines, admin configuration guides

**Documentation**: See [Safety Guardrails Analysis](../../docs/project/SAFETY_GUARDRAILS_ANALYSIS.md) for comprehensive technical details and implementation guidance.
