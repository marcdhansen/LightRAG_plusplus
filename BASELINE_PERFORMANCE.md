# Baseline Performance Metrics

## Overview
This document captures baseline performance metrics for entity/relation extraction before optimization work.

**Issue**: lightrag-4om (P0: Test Review & Academic Benchmarks)

---

## Test Suite Status

### Light Tests (Quick Validation)
```
TOTAL: 21 tests
PASSED: 21 ✅
FAILED: 0 ❌
SKIPPED: 0 ⏭️
```

### Test Categories

| Category | Tests | Status |
|----------|-------|--------|
| Few-NERD Extraction | 8 | ✅ PASSED |
| Text2KGBench Extraction | 4 | ✅ PASSED |
| Evaluation Metrics | 5 | ✅ PASSED |
| Entity Type Mapping | 1 | ✅ PASSED |
| Benchmark Integration | 3 | ✅ PASSED |

---

## Evaluation Metrics Baseline

### Entity Metrics (Mock Extraction)

| Metric | Value | Notes |
|--------|-------|-------|
| Entity Recall | 0.75 | 3/4 entities found |
| Entity Precision | 1.00 | No extra entities |
| Entity F1 | 0.86 | Harmonic mean |

### Relation Metrics (Mock Extraction)

| Metric | Value | Notes |
|--------|-------|-------|
| Relation Recall | 0.50 | 1/2 relations found |
| Relation Precision | 1.00 | No extra relations |
| Relation F1 | 0.67 | Harmonic mean |

### Overall Quality Score

| Metric | Value | Weight |
|--------|-------|-------|
| Overall F1 | 0.79 | Entity (0.6) + Relation (0.4) |

---

## Token Metrics

### Extraction Prompt Tokens

| Prompt | Current Tokens | Target | Savings |
|--------|---------------|--------|---------|
| entity_extraction_system_prompt | ~1,084 | ~750 | -30% |
| entity_extraction_user_prompt | ~204 | ~180 | -12% |
| entity_continue_extraction_user_prompt | ~391 | ~320 | -18% |
| entity_extraction_key_value_system_prompt | ~285 | ~250 | -12% |
| entity_extraction_key_value_user_prompt | ~178 | ~160 | -10% |
| **Total** | **~2,142** | **~1,660** | **-22%** |

### Query Context Tokens

| Context Type | Current | Target | Savings |
|--------------|---------|--------|---------|
| Knowledge Graph Context | ~15-20K | ~12-15K | -20-25% |
| Naive Query Context | ~10-15K | ~8-12K | -20% |

---

## Test Data Summary

### Few-NERD Subset

| Metric | Value |
|--------|-------|
| Test Cases | 5 |
| Total Entities | 18 |
| Total Relations | 12 |
| Entity Types Covered | Person, Organization, Location, Artifact, Concept |

### Text2KGBench Subset

| Metric | Value |
|--------|-------|
| Test Cases | 3 |
| Total Entities | 6 |
| Total Relations | 3 |
| Entity Types Covered | Person, Organization, Concept |

---

## Coverage Analysis

### Entity Type Coverage

| Type | LightRAG Types | Few-NERD Types | Coverage |
|------|---------------|----------------|----------|
| Person | ✅ | ✅ | 100% |
| Organization | ✅ | ✅ | 100% |
| Location | ✅ | ✅ | 100% |
| Artifact | ✅ | ⚠️ Partial | 50% |
| Concept | ✅ | ⚠️ Partial | 50% |
| Event | ✅ | ❌ | 0% |
| Method | ✅ | ❌ | 0% |
| Content | ✅ | ❌ | 0% |
| Data | ✅ | ❌ | 0% |
| NaturalObject | ✅ | ❌ | 0% |
| Creature | ✅ | ❌ | 0% |

**Overall Coverage**: 4/11 (36%)

---

## Performance Targets

### Quality Targets (Post-Optimization)

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Entity Recall | 0.75 | ≥0.80 | +7% |
| Entity Precision | 1.00 | ≥0.95 | -5% |
| Entity F1 | 0.86 | ≥0.88 | +2% |
| Overall F1 | 0.79 | ≥0.85 | +8% |

### Token Savings Targets

| Metric | Current | Target | Savings |
|--------|---------|--------|---------|
| Extraction Tokens | ~2,142 | ~1,500 | -30% |
| Query Tokens | ~17,500 | ~14,000 | -20% |

---

## Benchmark Integration Status

| Benchmark | Status | Test Cases | Coverage |
|-----------|--------|------------|----------|
| Few-NERD (subset) | ✅ Integrated | 5 | 10% |
| Text2KGBench (subset) | ✅ Integrated | 3 | 17% |
| Few-NERD (full) | ⏳ Pending | ~200 | 100% |
| Text2KGBench (full) | ⏳ Pending | ~150 | 100% |

---

## Next Steps

1. **Complete Phase 2**: Download full Few-NERD and Text2KGBench datasets
2. **Run Full Benchmarks**: Execute heavy tests on full datasets
3. **Measure Model Performance**: Test 1.5B and 7B models
4. **Establish True Baseline**: Run actual extraction with LLM

---

*Generated: 2026-01-30*
*Part of: lightrag-4om (P0: Test Review & Academic Benchmarks)*
