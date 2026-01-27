# 📊 Model Profiling & Benchmark Results

This document tracks speed vs. accuracy tradeoffs for various local models used within the LightRAG ecosystem, specifically for Knowledge Graph (KG) extraction and ACE (Agentic Context Evolution) components.

## 🚀 Speed vs. Accuracy Tradeoff (Extraction & Reflection)

Benchmarks performed on Apple M2 Max (64GB RAM) using Ollama.

| Model Size | Extraction Time | Reflection Quality | Recommended Role |
| :--- | :--- | :--- | :--- |
| **1.5B** (Qwen2.5-Coder) | ~10-15s | ❌ Fails (Hallucinates) | Naive Extraction, Simple Q&A |
| **3B** (Qwen2.5-Coder) | ~20-30s | ⚠️ Unreliable | Granular Extraction (Gleaning=2) |
| **7B** (Qwen2.5-Coder) | ~60-120s | ✅ Success (Logical Repair) | **ACE Reflector**, Complex Reasoning |

---

## 🔬 In-Depth Analysis

### 1.5B Models (The "Aggressive Extractor")

- **Pros**: Extremely fast; low resource footprint.
- **Cons**: High "Hallucination by Proximity". When tasked with reflection, it tends to "agree" with the current graph rather than critiquing it.
- **GLEANING**: Setting `entity_extract_max_gleaning=2` is mandatory to catch abstract concepts, though recall remains inconsistent.

### 3B Models (The "Middle Ground")

- **Pros**: Balanced speed.
- **Cons**: During the "Einstein on Mars" hallucination test, the 3B model hallucinated *along* with the graph data, creating illogical justifications (e.g., "Soviet Martian missions") instead of identifying the conflict with source text.

### 7B+ Models (The "Reliable Reflector")

- **Pros**: High logical consistency. Successfully identifies mismatches between source text and graph edges.
- **Cons**: Slower execution; requires more VRAM.
- **Verdict**: **Mandatory for ACE Phase 4+** (Automated Graph Repair).

## 🛠️ Configuration Recommendations

For optimal reliability in an evolving Knowledge Graph:

- **Reflector Model**: Use `qwen2.5-coder:7b` or larger.
- **Extraction Model**: `qwen2.5-coder:1.5b` is acceptable for high-volume ingestion **IF** followed by a 7B Reflector sweep.
- **Gleaning**: For models <7B, always set `entity_extract_max_gleaning` to at least 1 or 2.
