# Academic Benchmarking Suite Design

## 1. Objective
Establish a rigorous, reproducible evaluation framework to validate LightRAG's performance against state-of-the-art baselines. The goal is to produce metrics suitable for academic publication and "Model Card" reporting.

## 2. Test Datasets
We will utilize standard benchmarks to ensure comparability.

### 2.1 BEIR (Benchmarking IR)
Focus on the **Retrieval** aspect.
- **Datasets**:
    - `MSMARCO`: Standard dense retrieval benchmark.
    - `Natural Questions (NQ)`: Real-world user queries.
    - `HotpotQA`: Multi-hop reasoning (critical for Graph validation).
    - `FiQA`: Financial domain (validate domain generalization).

### 2.2 RAG Benchmarks (End-to-End)
Focus on **Generation** quality.
- **RGB (Retrieval-Augmented Generation Benchmark)**: Tests noise robustness and negative rejection.
- **CRUD-RAG**: Tests Create/Read/Update/Delete capabilities (Graph updates).

## 3. Metrics

### 3.1 Retrieval Quality
- **NDCG@10**: Normalized Discounted Cumulative Gain (Ranking quality).
- **Recall@K (k=1, 5, 10)**: Proportion of relevant documents retrieved.
- **MRR (Mean Reciprocal Rank)**: Position of the first relevant document.

### 3.2 Generation Quality
- **RAGAS Score**:
    - **Faithfulness**: Hallucination check.
    - **Answer Relevance**: Does it answer the query?
    - **Context Precision/Recall**: Is the retrieved context useful?
- **Response Correctness**: Exact Match (EM) or F1 for factoid QA.

## 4. Baselines

1.  **Naive RAG (Vector Only)**
    - Standard chunking + Embedding (e.g., OpenAI/Ollama) + Cosine Similarity.
2.  **Sparse Retrieval (BM25)**
    - Keyword-based baseline (ElasticSearch/RankBM25).
3.  **GraphRAG (Microsoft)**
    - Community-based graph summary approach.
4.  **Hybrid RAG**
    - Weighted ensemble of Vector + BM25.

## 5. Ablation Studies
To demonstrate the value of specific LightRAG components:

| Experiment | Configuration | Hypothesis |
| :--- | :--- | :--- |
| **No Graph** | Vector Store Only | Graph structure improves multi-hop reasoning. |
| **No Vector** | Graph Traversal Only | Vector search improves semantic recall for broad queries. |
| **Dual-Level** | Low-level vs High-level keywords | High-level keywords improve global summary questions. |
| **Refinement** | With/Without "Reflector" loop | Iterative refinement improves answer precision. |

## 6. Implementation Roadmap

### Phase 1: Data Adapters
- Create `benchmarks/loader.py` to load HF Datasets (BEIR).
- Implement `LightRAGAdapter` to map `dataset` format to `rag.insert()`.

### Phase 2: Execution Engine
- Script `run_benchmark.py --dataset nq --model lightrag --limit 100`.
- Support checkpointing (save results after every N queries).

### Phase 3: Evaluation & Reporting
- Script `eval_metrics.py` to compute NDCG/Ragas from saved logs.
- Generate comparative tables (Markdown/LaTeX).
