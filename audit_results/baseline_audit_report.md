# Prompt Baseline Audit Report (Phase 6.1)

**Date**: 2026-01-30
**Environment**: Ollama (qwen2.5-coder series)
**Task**: ACE Optimizer - Baseline Audit (lightrag-992)

## 📊 Summary Metrics

| Model | Entity Recall | Relation Accuracy | Hallucination Rate | YAML Compliance | Avg Exec Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **qwen2.5-coder:1.5b** | 86.1% | 66.7% | 7.4% | 100% | 131.0s |
| **qwen2.5-coder:3b** | 100.0% | 66.7% | 0.0% | 100% | 146.4s |
| **qwen2.5-coder:7b** | 100.0% | 83.3% | 0.0% | 100% | 360.0s |

## 🔍 Key Findings

### 1. YAML Compliance: SUCCESS

All models achieved **100% YAML compliance**. This confirms that the recent switch to hard-coded YAML extraction for local/offline LLMs is robust and provides a stable parsing foundation.

### 2. Entity Extraction: STRONG (Scale-dependent)

- **3B & 7B** models achieved perfect entity recall across all test cases.
- **1.5B** model missed some concepts in the complex "Dickens" opening and failed on one entity in the "Einstein" case.
- **Hallucinations**: Only the 1.5B model showed significant hallucinations (22.2% in the Dickens case), likely due to its smaller parameter count struggling with abstract concept boundaries.

### 3. Relationship Accuracy: BOTTLENECK

- This is the primary area for improvement.
- **Einstein Case**: Both 1.5B and 3B models failed to extract any correct relationships (0%). They often merged relationships or failed to follow the expected source-target-keyword schema perfectly.
- **7B Model**: Achieved 50% accuracy on the Einstein case, showing better comprehension of structural links but still missing nuances like "Einstein born in Germany" (it often only linked him to "Ulm").

### 4. Performance Tradeoffs

- 1.5B and 3B have comparable speeds (~2 mins per case), making 3B the "sweet spot" for extraction on this hardware (better recall, same speed).
- 7B is ~2.5x slower than 3B. While it offers better relationship accuracy, the latency tax is high for real-time applications.

## 🛠️ Recommended Optimization Strategies

### A. Extraction Prompt Enhancement (P2)

- **Problem**: Relationship extraction is weak on smaller models.
- **Fix**: Introduce more explicit relationship examples in the prompt. Use a "Strict Schema" instruction for relationships.
- **Experiment**: Test if `gleaning=2` improves relationship recall for 1.5B/3B without excessive time penalty.

### B. Reflection Prompt Refinement (P2)

- **Problem**: 1.5B hallucinations and relationship gaps.
- **Fix**: The ACE Reflector needs to be specifically tuned to detect "Abstract Concepts" that 1.5B tends to hallucinate or miss.
- **Experiment**: Use the 7B model as the "Reflector" (Asymmetric Routing) to repair 1.5B/3B extraction errors.

### C. Concept Extraction Tuning

- Improve instructions for "Concept" type entities, as these were the most variable across models.

---
---
**Next Step**: Implement Extraction Prompt Enhancements based on these failure patterns.

**UPDATE (2026-02-04)**: Optimizations implemented. See [Post-Optimization Report](../docs/benchmarks/EXTRACTION_PROMPT_OPTIMIZATION.md).
