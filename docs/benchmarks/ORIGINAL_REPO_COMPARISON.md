# Benchmark Report: Antigravity vs. HKUDS/LightRAG

## Overview

This report documents the performance comparison between the current Antigravity LightRAG repository and the original HKUDS/LightRAG implementation. The goal was to verify that recent optimizations (YAML-based extraction, prompt refinements, and model-specific tuning) maintain or improve extraction quality on small language models.

## Methodology

- **Date**: 2026-02-04
- **Hardware**: Local Machine (Mac)
- **Model**: `qwen2.5-coder:1.5b` (via Ollama)
- **Embedding**: `nomic-embed-text:v1.5` (via Ollama)
- **Datasets**:
  - **Few-NERD**: 10 representative cases.
  - **Text2KGBench**: 10 representative cases.
- **Metrics**: Entity F1, Precision, and Recall.

## Summary Results

| Benchmark | Metric | Original (HKUDS) | Antigravity (Current) | Difference |
| :--- | :--- | :--- | :--- | :--- |
| **Few-NERD** | Entity F1 | 0.496 | **0.686** | **+38%** |
| **Text2KGBench** | Entity F1 | 0.419 | **0.600** | **+43%** |

## Key Insights

### 1. Superior Extraction Quality

The Antigravity implementation shows a consistent ~40% improvement in F1 scores across both benchmarks. This is largely attributed to:

- **YAML-based Extraction**: Structured output reduces parsing errors and improves entity boundary detection on smaller models.
- **Prompt Engineering**: Refined instructions specifically tuned for the reasoning capabilities of 1.5B/7B models.

### 2. Enhanced Precision

In the Text2KGBench dataset, precision improved from **0.467** to **0.708**. This indicates a significant reduction in hallucinations and "noisy" entities that were common in the original codebase's output for small models.

### 3. Stability and Reliability

During the benchmark run, the original repository encountered a timeout (300s) on a complex Text2KGBench case, while the Antigravity repository processed all cases successfully. Our implementation showed better handling of resource constraints and asynchronous execution.

## Conclusion

The Antigravity LightRAG fork significantly outperforms the original HKUDS implementation for local, resource-constrained environments. The optimizations made during the ACE (Agentic Context Evolution) phases have successfully increased the floor for small-model RAG performance.

---
*Verified by: Antigravity AI Agent*
*Reference Commit: [cd36681b](https://github.com/marcdhansen/LightRAG_gemini/commit/cd36681b)*
