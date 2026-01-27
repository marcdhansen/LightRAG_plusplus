# Evaluation Framework Standardization (RAGAS + Langfuse)

## Goal

Establish a robust evaluation pipeline to measure RAG quality (Context Recall, Faithfulness, Answer Relevance) using RAGAS, and visualize traces/metrics in Langfuse.

## Graph Reranking & Evaluation Framework

## Status: COMPLETE (2026-01-27)

* [x] **Langfuse Integration**: Traces and RAGAS scores are automatically sent to local Langfuse.
* [x] **Tiered Testing**: Pytest-based `light` and `heavy` paths implemented.
* [x] **Graph Reranking**: Implemented `rerank_entities` and `rerank_relations` with perfect faithfulness.
* [x] **Documentation**:
  * `docs/OBSERVABILITY.md`, `docs/EVALUATION.md`, `docs/ACE_FRAMEWORK.md`, `docs/GRAPH_RERANKING.md`.

## Next Phase: ACE Optimization & Visualization (Current)

Establish the full ACE cycle in production and provide visual tooling for graph inspection.

* [ ] **Graph Visualization**: Implement/Verify a dedicated visualizer for the knowledge graph (Beads: lightrag-b8r).
* [ ] **ACE Phase 3**: Finalize minimal framework prototype and deployment endpoints (Beads: lightrag-q29).
* [ ] **UI Integration**: Add reranking toggles and ACE controls to the WebUI.
