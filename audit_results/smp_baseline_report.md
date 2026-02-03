# LightRAG Benchmark Comparison Report

**Original Repo**: /Users/marchansen/GitHub/HKUDS/LightRAG
**Current Repo**: /Users/marchansen/antigravity_lightrag/LightRAG
**Date**: 2026-02-03 17:28:08

## Summary

| Benchmark | Metric | Original | Current | Diff |
|-----------|--------|----------|---------|------|
| fewnerd | entity_f1 | 0.517 | 0.592 | +0.075 |
| fewnerd | entity_recall | 0.440 | 0.560 | +0.120 |
| fewnerd | entity_precision | 0.717 | 0.633 | -0.083 |
| fewnerd | overall_f1 | 0.517 | 0.592 | +0.075 |
| text2kgbench | entity_f1 | 0.417 | 0.638 | +0.220 |
| text2kgbench | entity_recall | 0.380 | 0.553 | +0.173 |
| text2kgbench | entity_precision | 0.533 | 0.767 | +0.233 |
| text2kgbench | overall_f1 | 0.417 | 0.638 | +0.220 |

## Details

### Fewnerd
#### Original Repository
- Cases: 5
  - entity_f1: 0.517
  - entity_recall: 0.440
  - entity_precision: 0.717
  - overall_f1: 0.517

#### Current Repository
- Cases: 5
  - entity_f1: 0.592
  - entity_recall: 0.560
  - entity_precision: 0.633
  - overall_f1: 0.592

### Text2kgbench
#### Original Repository
- Cases: 5
  - entity_f1: 0.417
  - entity_recall: 0.380
  - entity_precision: 0.533
  - overall_f1: 0.417

#### Current Repository
- Cases: 5
  - entity_f1: 0.638
  - entity_recall: 0.553
  - entity_precision: 0.767
  - overall_f1: 0.638
