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

## Phase: Infrastructure & Process Improvements (Current)

Strengthen the development lifecycle by enhancing automated checks and standardizing environment-specific configurations.

* [x] **Flight Director Enhancement**: Automate RTB cleanup and document verification (Beads: lightrag-ijs).
* [x] **Extraction Standardization**: Hard-code YAML for offline LLMs (Beads: lightrag-6h1).
* [ ] **Reasoning Threshold Policy**: Formalize model requirements for reflection (Beads: lightrag-oi6).

## Phase 6: ACE Optimizer (Upcoming)
