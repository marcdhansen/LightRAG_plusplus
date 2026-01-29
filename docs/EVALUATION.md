# 📊 RAGAS Evaluation Framework

LightRAG uses **RAGAS** (Retrieval-Augmented Generation Assessment) to provide quantitative, reference-free evaluation of its RAG quality.

## 📈 Key Metrics

| Metric | What It Measures | Ideal Score |
| :--- | :--- | :--- |
| **Faithfulness** | Does the answer contain hallucinations? (Factually accurate based on context) | > 0.80 |
| **Answer Relevance** | Does the answer directly address the user's question? | > 0.80 |
| **Context Recall** | Did the system find all relevant documents needed to answer? | > 0.80 |
| **Context Precision** | Is the retrieved context focused, or does it contain "noise"? | > 0.80 |
| **RAGAS Score** | Harmonics mean of the above metrics. | > 0.80 |

## 🧪 Running Evaluations

### 1. Lightweight Verification (Quick Path)

Use this to verify your setup is working correctly. It runs a single test case.

```bash
pytest -m light tests/test_rag_quality.py
```

### 2. Full Benchmark (Heavy Path)

Use this for full system assessment. It runs the entire dataset.

```bash
pytest -m heavy tests/test_rag_quality.py
```

## ⚙️ Configuration

RAGAS requires a "Judge LLM" to score the responses. By default, it is configured to use local Ollama models for privacy and cost savings.

**Environment Variables (.env):**

- `EVAL_LLM_MODEL`: The judge model (e.g., `qwen2.5-coder:1.5b`).
- `EVAL_EMBEDDING_MODEL`: The embedding model (e.g., `nomic-embed-text:v1.5`).
- `EVAL_LLM_BINDING_HOST`: Endpoint for the judge (usually `http://127.0.0.1:11434/v1`).

## 🔭 Observability Integration

RAGAS evaluations are automatically traced in **Langfuse** if enabled. This allows you to inspect the reasoning of the Judge LLM itself.

## 📊 Benchmark Results

For detailed performance analysis of specific features, refer to:

- [Graph Reranking Benchmark (Jan 2026)](GRAPH_RERANKING.md#benchmarking-results) - Demonstrates +13.8% quality improvement using entity/relation prioritization.

---

## 📚 Resources

- [RAGAS Documentation](https://docs.ragas.io/)
- [Langfuse Observability Guide](OBSERVABILITY.md)
- [Academic Benchmarking Suite](ACADEMIC_BENCHMARKING.md)
