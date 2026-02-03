# LightRAG Test Inventory

## Overview
This document lists all 54 test files in the LightRAG test suite with descriptions, categories, and data sources.

## Test Statistics

| Category | Count |
|----------|-------|
| Total Test Files | 54 |
| Extraction-Related | ~20 |
| Retrieval/Query | ~10 |
| Storage/Integration | ~15 |
| Unit Tests | ~10 |

## Test Markers (per README_TESTING.md)

| Marker | Purpose | Command |
|--------|---------|---------|
| `@pytest.mark.light` | Fast tests (seconds) | `pytest -m light` |
| `@pytest.mark.heavy` | Integration tests | `pytest -m heavy` |
| `@pytest.mark.offline` | No external deps | `pytest -m offline` |
| `@pytest.mark.integration` | External services | `pytest --run-integration` |
| `@pytest.mark.manual` | Human verification | `pytest --run-manual` |
| `@pytest.mark.benchmark` | Performance tests | `pytest -k benchmark` |

---

## Complete Test File Listing

### 1. ACE (Agentic Context Evolution) Tests (8 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_ace_api.py` | ACE API endpoint testing | Unknown | heavy |
| `test_ace_components.py` | ACE component validation | Unknown | heavy |
| `test_ace_core_integration.py` | ACE core integration | Unknown | heavy |
| `test_ace_curator_hitl.py` | Human-in-the-loop curator | Unknown | heavy |
| `test_ace_curator_repair.py` | Curator repair functionality | Unknown | heavy |
| `test_ace_graph_repair.py` | Graph repair validation | Unknown | heavy |
| `test_ace_integration.py` | Full ACE integration | Unknown | heavy |
| `test_ace_policy.py` | ACE policy testing | Unknown | heavy |
| `test_ace_reflector_repair.py` | Reflector repair | Unknown | heavy |
| `test_ace_regression.py` | Regression tests | Unknown | heavy |
| `test_ace_utils_unit.py` | ACE utility unit tests | Unknown | light |

### 2. API Tests (5 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_api_highlight.py` | API highlighting features | Unknown | unknown |
| `test_api_v2_manual.py` | V2 API manual testing | Unknown | manual |
| `test_aquery_data_endpoint.py` | Aquery data endpoint | Unknown | heavy, integration |
| `test_asymmetric_routing.py` | Asymmetric routing | Unknown | unknown |

### 3. Extraction Tests (3 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_extraction_yaml.py` | YAML parsing validation | Mock responses | heavy |
| `test_gold_standard_extraction.py` | Entity/relation extraction | 2 hardcoded cases | light |
| `test_performance_matrix.py` | Performance benchmarking | Unknown | unknown |

### 4. Storage Backend Tests (12 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_graph_storage.py` | Graph storage operations | Unknown | heavy |
| `test_neo4j_fulltext_index.py` | Neo4j full-text index | Unknown | heavy, integration |
| `test_memgraph_compliance.py` | Memgraph compliance | Unknown | heavy, integration |
| `test_memgraph_optimized_query.py` | Memgraph optimized queries | Unknown | heavy, integration |
| `test_memgraph_unified.py` | Memgraph unified operations | Unknown | heavy, integration |
| `test_memgraph_vector_storage.py` | Memgraph vector storage | Unknown | heavy, integration |
| `test_postgres_index_name.py` | Postgres index naming | Unknown | heavy, integration |
| `test_postgres_migration.py` | Postgres migration | Unknown | heavy, integration |
| `test_postgres_retry_integration.py` | Postgres retry logic | Unknown | heavy, integration |
| `test_qdrant_migration.py` | Qdrant migration | Unknown | heavy, integration |
| `test_unified_lock_safety.py` | Lock safety validation | Unknown | heavy |
| `test_workspace_isolation.py` | Workspace isolation | Unknown | heavy |
| `test_workspace_migration_isolation.py` | Workspace migration | Unknown | heavy |

### 5. Retrieval/Query Tests (5 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_beekeeping_retrieval.py` | Beekeeping retrieval | Unknown | heavy |
| `test_benchmarks.py` | Multi-hop reasoning | HotpotQA-style | heavy, benchmark |
| `test_dimension_mismatch.py` | Dimension mismatch handling | Unknown | unknown |
| `test_local_reranker.py` | Local reranker testing | Unknown | unknown |
| `test_overlap_validation.py` | Overlap validation | Unknown | unknown |
| `test_rag_quality.py` | RAG quality testing | Unknown | unknown |
| `test_retrieval_accuracy.py` | Retrieval accuracy | Unknown | unknown |
| `test_rerank_chunking.py` | Rerank chunking | Unknown | unknown |
| `test_rrf_fusion.py` | RRF fusion | Unknown | unknown |
| `test_rrf_validation.py` | RRF validation | Unknown | unknown |

### 6. Document/Content Tests (3 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_doc_content_and_references.py` | Document content & refs | Unknown | heavy |
| `test_fail_fast_integration.py` | Fail-fast behavior | Unknown | heavy |
| `test_highlight.py` | Highlighting features | Unknown | unknown |

### 7. Model/Extraction Tests (4 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_lightrag_ollama_chat.py` | Ollama chat integration | Unknown | heavy |
| `test_no_model_suffix_safety.py` | Model suffix safety | Unknown | unknown |
| `test_ollama_timeout.py` | Ollama timeout handling | Unknown | unknown |
| `test_chunking.py` | Chunking logic | Unknown | heavy |

### 8. Utility/Optimization Tests (5 files)

| File | Purpose | Data Source | Markers |
|------|---------|-------------|---------|
| `test_write_json_optimization.py` | JSON write optimization | Synthetic data | light, offline |
| `test_token_auto_renewal.py` | Token auto-renewal | Unknown | unknown |
| `test_auto_citations.py` | Auto-citations | Unknown | unknown |

---

## Extraction-Related Tests Deep Dive

### Gold Standard Tests (`test_gold_standard_extraction.py`)

**Purpose**: Validate entity/relation extraction quality against known expected outputs.

**Test Cases**:
1. `naive_case`: "Steve Jobs founded Apple."
   - Expected entities: Apple (Organization), Steve Jobs (Person)
   - Expected relations: Steve Jobs -> Apple (founded)

2. `einstein_basic`: "Albert Einstein was a famous theoretical physicist..."
   - Expected entities: Albert Einstein (Person), Ulm (Location), Germany (Location), Theory of Relativity (Concept)
   - Expected relations: Albert Einstein -> Ulm (born), etc.
   - **Note**: Marked as xfail for 1.5B model

**Limitations**:
- Only 2 test cases
- No systematic entity type coverage
- No recall/precision metrics
- No multi-domain testing

### Benchmark Tests (`test_benchmarks.py`)

**Purpose**: Multi-hop reasoning validation (HotpotQA-style).

**Test Cases**:
1. "Which film starring Keanu Reeves as Neo was released first?"
   - Complexity: Multi-hop (Actor -> Role -> Movie -> Date)

2. "Who was the director of the movie that features the character Sarah Connor?"
   - Complexity: Multi-hop (Character -> Movie -> Director)

**Limitations**:
- Only 2 test cases
- Marked as xfail for small models
- No standardized metrics

---

## Test Data Sources

| Source | Usage | Location |
|--------|-------|----------|
| Hardcoded strings | Unit tests | In test files |
| Dickens text | Integration tests | `tests/inputs/` or runtime |
| Einstein bio | Extraction tests | Hardcoded in test files |
| Mock responses | API tests | In test files |
| Ollama API | Integration tests | External service |

---

## Current Gaps Summary

| Gap | Severity | Affected Tests |
|-----|----------|----------------|
| No standardized benchmark data | Critical | All extraction tests |
| Limited entity type coverage | High | test_gold_standard_extraction.py |
| No recall/precision metrics | High | All extraction tests |
| No multi-domain testing | Medium | All tests |
| No few-shot learning tests | Medium | All tests |
| Limited relation testing | Medium | test_gold_standard_extraction.py |

---

## Recommendations

1. **Integrate Few-NERD** for comprehensive entity type coverage
2. **Integrate Text2KGBench** for KG generation validation
3. **Add evaluation metrics** (recall, precision, F1)
4. **Create light/hevy splits** for CI/CD
5. **Add domain-specific tests** (scientific, legal, medical)

---

*Generated: 2026-01-30*
*Part of: lightrag-4om (P0: Test Review & Academic Benchmarks)*
