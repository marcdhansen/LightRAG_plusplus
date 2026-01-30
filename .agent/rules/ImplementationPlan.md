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
* [/] **Reflect Skill Formalization**: Updated `reflect` skill with standard mission processes and structured debriefing (Beads: lightrag-982).
* [x] **Universal SOP Standardization**: Documented cross-IDE/agent compatibility design in `CROSS_COMPATIBILITY.md` and integrated into `GLOBAL_INDEX.md` (Beads: lightrag-989).

## Phase 6: ACE Optimizer (Current)

**Target**: Refine the ACE framework for production-grade reliability and performance on small models (Ollama 1.5B/7B).

**Objective**: Achieve consistent, high-quality knowledge graph extraction and reasoning on resource-constrained models through systematic prompt engineering, curator optimization, and comprehensive benchmarking.

### 6.1 Prompt Optimization (1.5B/7B) - **Priority: P2**

**Goal**: Achieve 95%+ extraction accuracy and eliminate hallucinations on small models.

* [ ] **Baseline Audit** (Beads: lightrag-992):
  * Run extraction benchmarks on Einstein/Dickens test sets with 1.5B, 3B, and 7B models
  * Measure: entity recall, relationship accuracy, YAML compliance rate, hallucination frequency
  * Document failure patterns: missing concepts, malformed YAML, entity duplication
  * **Success Criteria**: Baseline metrics documented for all model sizes

* [ ] **Extraction Prompt Enhancement**:
  * Implement explicit "Concept Extraction" instructions with examples
  * Add YAML schema constraints to prevent malformed output
  * Test gleaning=2 vs. gleaning=1 for small models
  * **Success Criteria**: 95% YAML compliance, 90% entity recall on 7B models

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
