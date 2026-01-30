# 🔭 Observability with Langfuse

LightRAG integrates with [Langfuse](https://langfuse.com/) to provide state-of-the-art observability, tracing, and analytics for RAG pipelines.

## 🚀 Why Langfuse?

Integrating Langfuse provides several key advantages for maturing the LightRAG system:

1. **Full-Chain Tracing**: Visualize the entire execution flow—from graph traversal and chunk retrieval to the final LLM generation.
2. **Performance Analytics**: Automatically track **latency** and **token usage (cost)** for every request.
3. **Debugging & Optimization**: Identify bottlenecks in retrieval or specific LLM calls that lead to poor results.
4. **Metric Mapping**: Link evaluation scores (like RAGAS) directly to the execution trace that produced them.

## 🛠️ Setup Instructions

### 1. Start Langfuse via Docker

We provide a pre-configured Docker stack for local development.

```bash
cd langfuse_docker
docker-compose up -d
```

- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **Default Keys** (initialized automatically):
  - **Public Key**: `pk-lf-lightrag`
  - **Secret Key**: `sk-lf-lightrag`

### 2. Enable Tracing in LightRAG

Tracing is controlled via environment variables in your `.env` file:

```bash
LANGFUSE_ENABLE_TRACE=true
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-lightrag
LANGFUSE_SECRET_KEY=sk-lf-lightrag
```

## 📊 Viewing Traces

Once enabled, every query processed by LightRAG (through the API or the evaluation script) will stream traces to the Langfuse dashboard.

- **Dashboard**: Overview of total requests, latency, and costs.
- **Traces List**: Drill down into individual executions to see the detailed DAG of component calls.
- **Metrics**: If running `eval_rag_quality.py`, scores will appear in the "Scores" tab of the associated traces.

---

## 📚 Resources

- [Langfuse Documentation](https://docs.langfuse.com/)
- [LightRAG Evaluation Guide](EVALUATION.md)
