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

## Phase 6: ACE Optimizer (Upcoming)
