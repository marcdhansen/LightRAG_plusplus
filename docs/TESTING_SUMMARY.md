# 🧪 Testing Summary: LightRAG

This document provides a high-level overview of how the LightRAG subsystems are tested and evaluated.

## 🏗️ Testing Architecture

LightRAG uses a multi-tiered testing strategy to balance speed during development with thoroughness for benchmarking.

### 1. Tiered Testing (Pytest)

We use `pytest` with custom markers to separate fast unit/integration tests from long-running evaluation benchmarks.

- **Light Path** (`--run-light`): Runs basic verification on minimal datasets (e.g., 1 document). Fast and suitable for CI/CD.
- **Heavy Path** (`--run-heavy`): Runs full benchmarks on academic datasets (e.g., HotpotQA). Slow (minutes to hours).
- **Integration Path** (`--run-integration`): Automatically starts/stops the `lightrag-server` and wipes temporary storage to ensure clean test environments.

### 2. RAG Quality Evaluation (RAGAS)

We use the **RAGAS** framework to quantify the quality of retrieved context and generated answers.

- **Metrics tracked**: Context Recall, Faithfulness, Answer Relevance, Context Precision.
- **Local Judges**: Evaluations are performed using local Ollama models (e.g., `qwen2.5-coder` or `llama3.2`) to avoid dependency on external APIs and ensure privacy.

### 3. Observability & Tracing (Langfuse)

All retrieval and generation steps are traced using **Langfuse**.

- **Traces**: Every query's internal execution path (chunk retrieval, reranking, LLM call) is recorded.
- **Metrics Dashboard**: RAGAS scores are automatically pushed to Langfuse for visualization and trend analysis.

### 4. ACE Stability & Graph Repair

Specialized tests evaluate the system's ability to self-heal the Knowledge Graph.

- **Hallucination Repair Test**: (`tests/test_ace_reflector_repair.py`) Manually injects illogical edges into the graph and verifies that the **Reflector** correctly identifies and removes them.

For model performance tradeoffs discovered during these tests, see [MODEL_PROFILING_RESULTS](../MODEL_PROFILING_RESULTS.md).

## 🛠️ Key Scripts

- `tests/test_rag_quality.py`: The main entry point for running quality benchmarks via pytest.
- `lightrag/evaluation/eval_rag_quality.py`: Core logic for executing RAGAS evaluations.
- `lightrag/evaluation/benchmarks/`: Contains academic datasets (HotpotQA, etc.) and evaluation logic.

## 🚀 How to Run Tests

Refer to [EVALUATION.md](EVALUATION.md) for detailed commands and setup instructions.
