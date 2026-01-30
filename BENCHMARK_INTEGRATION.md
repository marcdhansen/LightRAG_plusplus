# Academic Benchmark Integration Guide

## Overview
This document describes how to integrate and use academic benchmarks for testing LightRAG entity extraction.

**Issue**: lightrag-4om (P0: Test Review & Academic Benchmarks)

---

## Supported Benchmarks

### Tier 1: Currently Integrated

| Benchmark | Type | Entity Types | Status |
|-----------|------|--------------|--------|
| **Few-NERD** | Few-shot NER | 66 fine-grained | ✅ Integrated (subset) |
| **Text2KGBench** | Text-to-KG | Ontology-based | ✅ Integrated (subset) |

### Tier 2: Future Integration

| Benchmark | Type | Notes |
|-----------|------|-------|
| CoNLL 2003 | Standard NER | Industry standard |
| TAC KBP | Entity Discovery | Enterprise-grade |
| SciER | Scientific NER | Domain-specific |
| KnowledgeNet | KG Population | End-to-end |
| EMERGE | KG Updating | Temporal |

---

## Quick Start

### Running Light Tests (Quick Validation)

```bash
# Run all light academic benchmark tests
pytest -m light -k "fewnerd or text2kgbench" -v

# Run specific test class
pytest -m light -k "TestFewNERDExtraction" -v

# Run single test
pytest -m light -k "test_entity_recall_quick[fewnerd_1]" -v
```

### Running Heavy Tests (Full Benchmarks)

```bash
# Full benchmark tests (manual, on-demand)
pytest -m heavy -k "academic_full" -v

# Model comparison tests
pytest -m heavy -k "model_comparison" -v
```

---

## Test Structure

### Light Tests (Subset Data)

| Test File | Tests | Duration | Data |
|-----------|-------|----------|------|
| `test_academic_benchmarks.py` | 21 | <1 min | 5 Few-NERD + 3 Text2KGBench |

### Heavy Tests (Full Data)

| Test File | Tests | Duration | Data |
|-----------|-------|----------|------|
| `test_academic_benchmarks.py` | 3+ | ~30-60 min | Full datasets |

---

## Evaluation Metrics

### Entity Metrics

```python
from tests.benchmarks.eval_metrics import (
    calculate_entity_recall,
    calculate_entity_precision,
    calculate_entity_f1,
)

# Calculate metrics
recall = calculate_entity_recall(predicted_entities, gold_entities)
precision = calculate_entity_precision(predicted_entities, gold_entities)
f1 = calculate_entity_f1(recall["recall"], precision["precision"])
```

### Type-Specific Metrics

```python
from tests.benchmarks.eval_metrics import calculate_type_specific_metrics

type_metrics = calculate_type_specific_metrics(
    predicted_entities,
    gold_entities,
    entity_types=["Person", "Organization"]
)
```

### Overall Quality Score

```python
from tests.benchmarks.eval_metrics import calculate_extraction_quality_score

score = calculate_extraction_quality_score(
    predicted_entities=predicted,
    gold_entities=gold,
    predicted_relations=pred_rels,
    gold_relations=gold_rels,
    entity_weight=0.6,
    relation_weight=0.4,
)
```

---

## Adding New Benchmarks

### Step 1: Download Dataset

```python
# Example: Downloading Few-NERD
import subprocess
subprocess.run([
    "git", "clone", "https://github.com/thunlp/Few-NERD.git",
    "tests/benchmarks/fewnerd/raw"
])
```

### Step 2: Convert Format

```python
def convert_to_lightrag_format(benchmark_data: dict) -> dict:
    """Convert benchmark format to LightRAG format."""
    return {
        "id": benchmark_data["id"],
        "text": benchmark_data["text"],
        "entities": [
            {"name": e["name"], "type": map_type(e["type"]), "description": ""}
            for e in benchmark_data["entities"]
        ],
        "relations": [
            {"source": r["source"], "target": r["target"], "keywords": r.get("keywords", [])}
            for r in benchmark_data["relations"]
        ],
    }
```

### Step 3: Add Test Data

```python
# In test_academic_benchmarks.py

NEW_BENCHMARK_SUBSET = [
    {"id": "nb_1", "text": "...", "entities": [...], "relations": [...]},
    # Add more test cases
]
```

### Step 4: Add Tests

```python
class TestNewBenchmarkExtraction:
    @pytest.mark.light
    def test_entity_extraction(self):
        # Test implementation
        pass
```

---

## Benchmark Data Format

### Gold Standard Format

```python
{
    "id": "unique_id",
    "text": "The input text for extraction.",
    "entities": [
        {"name": "Entity Name", "type": "Person", "description": ""}
    ],
    "relations": [
        {
            "source": "Source Entity",
            "target": "Target Entity",
            "keywords": ["relation", "keywords"],
            "description": ""
        }
    ]
}
```

### Predicted Format

```python
{
    "entities": [
        {"name": "Entity Name", "type": "Person"}
    ],
    "relations": [
        {"source": "Source", "target": "Target", "keywords": ["keyword"]}
    ]
}
```

---

## CI/CD Integration

### Light Tests (Every Commit)

```yaml
# .github/workflows/tests.yml
- name: Run Light Academic Tests
  run: |
    pytest -m light -k "fewnerd or text2kgbench" --tb=short
```

### Heavy Tests (Manual)

```bash
# Run full benchmarks manually
pytest -m heavy -k "academic_full" -v --timeout=3600
```

---

## Performance Targets

### Quality Thresholds

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| Entity Recall | 0.80 | 0.90 | 0.95 |
| Entity Precision | 0.90 | 0.95 | 0.98 |
| Entity F1 | 0.85 | 0.92 | 0.96 |
| Relation F1 | 0.80 | 0.88 | 0.92 |

### Token Savings Targets

| Component | Current | Target | Savings |
|-----------|---------|--------|---------|
| Extraction Prompts | ~2,142 | ~1,500 | -30% |
| Query Context | ~17,500 | ~14,000 | -20% |

---

## Troubleshooting

### Tests Skipped

**Problem**: Tests are being skipped
**Solution**: Remove module-level `pytestmark` that marks tests as heavy

### Import Errors

**Problem**: `ModuleNotFoundError: tests.benchmarks.eval_metrics`
**Solution**: Ensure `tests/benchmarks/` directory exists

### Low Recall

**Problem**: Entity recall < 0.80
**Solution**:
1. Check entity type mapping
2. Verify normalization logic
3. Review extraction prompts

---

## References

### Academic Papers

- [Few-NERD: A Few-Shot Named Entity Recognition Dataset](https://arxiv.org/abs/2105.07464)
- [Text2KGBench: A Benchmark for Ontology-Driven KG Generation](https://arxiv.org/abs/2308.02357)
- [CoNLL 2003 NER Task](https://www.clips.uantwerpen.be/conll2003/ner/)

### Repositories

- [Few-NERD GitHub](https://github.com/thunlp/Few-NERD)
- [Text2KGBench](https://github.com/IBM/text2kgbench)

---

*Generated: 2026-01-30*
*Part of: lightrag-4om (P0: Test Review & Academic Benchmarks)*
