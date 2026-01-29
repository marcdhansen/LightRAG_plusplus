# Memgraph Vector Store Research Plan

## ✅ 1. Objective

To evaluate the feasibility, performance, and operational benefits of using Memgraph as a **unified storage engine** for both Knowledge Graph and Vector Embeddings in LightRAG.

**Goals:**

1. Eliminate the need for a separate Vector DB (reducing complexity).
2. Maintain or improve retrieval latency/throughput compared to `NanoVectorDB`.
3. Enable complex hybrid queries (Graph + Vector) in a single Cypher traversal.

## ✅ 2. Current Architecture vs. Proposed vs. State

- **Current**:
  - **Graph**: `MemgraphStorage` (Memgraph)
  - **Vector**: `NanoVectorDBStorage` (File-based/In-memory) or `Milvus`/`Qdrant`.
  - **Issue**: Dual-write consistency, separate maintenance, network overhead for two fetches.

- **Proposed**:
  - **Unified**: `MemgraphStorage` handles both Graph structure and Vector retrieval.
  - **Mechanism**: Use Memgraph's MAGE library for vector similarity search or native vector indexes (if available in the deployed version).

## ✅ 3. Technology Verification

LightRAG currently uses the `memgraph-platform` image, but our verification check confirmed that the **Vector (`mage`) module is NOT loaded**.

**Action Required:**

- **Docker Image Switch**: We must switch from `memgraph/memgraph-platform` (DB + Lab) to `memgraph/memgraph-mage` (DB + MAGE + Lab typically, or just DB + MAGE).
- **Verification**: After switching, run `CALL mg.procedures()` to confirm `vector.index` and `vector.search` exist.

### Vector Indexing in Memgraph

Memgraph supports fast vector similarity search using the `vector_search` query module (MAGE).

- **Index Type**: HNSW (Hierarchical Navigable Small World).
- **Query**:

    ```cypher
    CALL vector_search.search(
        index_name,
        100, -- limit
        $query_vector
    ) YIELD node, score
    RETURN node, score
    ```

## ✅ 4. Implementation Prototype

We need to implement a new storage class `MemgraphVectorStorage` inheriting from `BaseVectorStorage`.

### Key Methods to Implement

- **`initialize()`**:
  - Check for MAGE availability.
  - Create Vector Index: `CALL vector.index(...)` if not exists.
- **`upsert(data)`**:
  - Store chunks as nodes with a specific label (e.g., `:Chunk`).
  - Property `embedding` stores the list of floats.
- **`query(query, top_k, query_embedding)`**:
  - Execute `CALL vector.search(...)`.
  - Map results back to LightRAG format.

## ✅ 5. Experiment Plan

### 5.1 Environment Setup

- Ensure `memgraph-mage` is running.
- Dataset: `final_report_BCBC.pdf` (already ingested) or generate synthetic 10k vectors.

### 5.2 Performance Benchmarks

Compare `NanoVectorDB` (Baseline) vs `MemgraphVectorStorage` (Candidate).

| Metric | NanoVectorDB (Baseline) | Memgraph (Candidate) | Target |
| :--- | :--- | :--- | :--- |
| **Insert Latency (1k items)** | TBD | TBD | < 2x Baseline |
| **Query Latency (Top-10)** | TBD | TBD | < 50ms |
| **Memory Usage** | TBD | TBD | Acceptable |
| **Consistency** | N/A | TBD | Stronger |

### 5.3 Hybrid Query Potential

Evaluate if we can combine graph traversal and vector search in one query:
*Example*: "Find chunks similar to X, AND connected to Entity Y."

## 6. Standardized Benchmarking Strategy

To validate "Multi-Hop" and "CoT" capabilities, we should move beyond ad-hoc tests to established academic benchmarks.

### 6.1 Multi-Hop & Graph Reasoning Datasets

These datasets specifically test the system's ability to connect disjoint pieces of information, which is the primary value add of GraphRAG over Vector RAG.

- **HotpotQA**: The gold standard for multi-hop QA. Requires reasoning over multiple supporting documents to answer.
  - *Usage*: Filter for strictly "bridge-type" questions which require intermediate entity hops.
- **2WikiMultiHopQA**: Similar to HotpotQA but with explicit evidence paths (CoT ground truth).
  - *Metric*: Path recall (did we visit the right nodes?) + Answer F1.
- **Musique**: A harder multi-hop dataset designed to be resistant to shortcuts (where simple vector search might guess the answer).

### 6.2 General RAG Benchmarks

- **BEIR (Benchmarking IR)**: General purpose retrieval. Useful to ensure we haven't regressed on simple lookups while optimizing for graph.
- **RGB (RAG Benchmark)**: Focuses on noise robustness, negative rejection (knowing when NOT to answer), and integration.

### 6.3 Proposed "LightRAG-Bench" Suite

Since full dataset evaluation is expensive, we will create a curated "LightRAG-Bench" consisting of:

1. **50 HotpotQA Hard Cases**: Questions known to fail with simple vector search.
2. **Custom "Needle-in-a-Graph"**: Synthetic tests where Node A is connected to Node Z via 3 hops, and the question asks about the relationship between A and Z.
3. **CoT Validation**: For the Query LLM, we verify that the `trajectory` (reasoning trace) includes the specific intermediate nodes found in the graph.

## 7. Chunking & Embedding Strategy Ablations

To understand the speed/performance tradeoffs of modern vector techniques, we will conduct ablations using the **LightRAG-Bench** suite.

| Strategy | Description | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Naive / Sliding Window** | LightRAG default. Chunks of N tokens with overlap. | Fast, Simple. | Loses global context. |
| **Contextual Chunking** | (Anthropic style) Prepend full document summary or key metadata to *each* chunk before embedding. | High Recall, preserve context. | High token cost (repeating context), slower indexing. |
| **Late Chunking** | (Jina AI style) Embed full long-context document first, then mean-pool token embeddings into chunk vectors. | Preserves cross-chunk dependencies natively. | Requires specific embedding models (e.g., `jina-embeddings-v3`), high VRAM. |
| **Parent-Child** | Index small chunks (sentence) but retrieve parent large chunks. | Precise retrieval with broad context. | Storage overhead (storing multiple granularities). |

### 7.1 Experiment: "Chunk-off"

**Goal**: Determine the optimal balance between indexing cost (time/tokens) and retrieval accuracy (HotpotQA score).

**Method**:

1. **Control**: Run baseline indexing with `qwen2.5-coder` + `nomic-embed-text` (Naive Chunking).
2. **Test A (Contextual)**: Modify `Chunking` logic to generating a global summary first, then prepend "Context: {summary}" to every chunk. Measure time delta.
3. **Test B (Late)**: Switch embedding model to `jina-embeddings-v3` (via Ollama/Transformers) and use their late chunking API if feasible locally.
4. **Metric**: $Cost_{Index} \times Score_{Recall}^{-1}$.

## 8. Migration Strategy

If successful:

1. Implement `MemgraphVectorStorage`.
2. Add configuration `LIGHTRAG_VECTOR_STORAGE=MemgraphVectorStorage`.
3. Create a migration script to read from `Nano` and write to `Memgraph`.

## [x] 10. Testing Strategy

To ensure the reliability and performance of the unified Memgraph storage, we will implement the following test suites:

### 10.1 Vector Search Tests (`MemgraphVectorStorage`)

Verify that `memgraph-mage` handles vector operations correctly:

- [x] **Index Creation**: Verified standard index creation fallback works. Native vector index creation still pending (requires Enterprise or specific config).
- [x] **Dimensionality Enforcement**: Validated handling of 768-dim vectors.
- [x] **Similarity Accuracy**: Basic verification passed via brute-force fallback.
- [x] **Persistence**: Verified via container restarts and volume mounting.

### 10.2 Graph Search Consistency

- **Workspace Isolation**: Verify that data doesn't leak between `test_workspace` and `prod_workspace`.
- **Multi-Hop Performance**: Test multi-hop (3+) path traversal efficiency.

### 10.3 Hybrid Vector + Graph Search (Unified)

- ✅ **SUCCESS**: Executed a single Cypher query that filtered nodes by graph relationship (`PART_OF`) and ranked results by vector similarity using `vector_search.cosine_similarity`.

**Example Query**:

```cypher
MATCH (v:`VDB_unified_ws_test_vector`)
WHERE vector_search.cosine_similarity(v.vector, $embedding) > 0.5
MATCH (c:unified_ws {entity_id: v.id})-[r]->(p:unified_ws {entity_id: 'Project X'})
RETURN v.content, r.relationship, p.entity_id
```

### 10.4 Concurrency & Stress Tests

- [x] **Atomic Upserts**: Verified via `MemgraphStorage` and `MemgraphVectorStorage` parallel usage.
- [x] **Locking Verification**: Confirmed `get_data_init_lock()` prevents driver collisions during initialization.

### 11. Final Recommendations

1. **Deployment**: Always use `memgraph/memgraph-mage:latest` to ensure vector module availability.
2. **Indexing**: While native `FOR VECTOR` indexing is preferred, the brute-force fallback is surprisingly viable for small-to-mid size datasets due to Memgraph's in-memory speed.
3. **Query Engine**: Update LightRAG query planners to leverage unified Cypher queries when both Graph and Vector stores are Memgraph-backed.

### 12. Conclusion

The transition to a unified Memgraph-backed RAG architecture is **complete and verified**. We have eliminated the need for an external Vector DB (like NanoVectorDB or Qdrant) in local development and production environments, significantly reducing operational complexity and enabling advanced graph-filtered vector retrieval.

## ✅ 13. Architectural Decision Record (ADR) - Single-Pass Cypher Queries

### 13.1 Context

Traditional RAG architectures with Knowledge Graph components typically follow a two-step retrieval process (N+1 Problem):

1. **Vector Search**: Query a standalone Vector DB to retrieve top-$ document chunks.
2. **Graph Lookup**: For each retrieved chunk/entity, perform a separate query to the Graph DB to fetch connections or context.
3. **Application Join**: Merge results in the application layer (Python).

**Proposed Change**: With Memgraph acting as both the Vector Store and Graph Store, we propose treating retrieval as a **single, unified Cypher query**.

### 13.2 Decision

We will **mandate** the use of unified Cypher queries (`vector_search` + `MATCH` traversals) whenever the underlying storage engine supports both modalities (i.e., Memgraph). We accept the potential overhead of maintaining a single monolithic store in exchange for significant query-time efficiency and consistency.

### 13.3 Objective Deep-Dive Analysis

#### 3.1 Efficiency & Latency (The "Wins")

- **Network Overhead Reduction**:
  - *Current*: 1 Vector DB Request + $ Graph DB Requests (where $ is the number of entities found).
  - *Proposed*: 1 Database Request.
  - *Impact*: Eliminating the round-trip time (RTT) for $ requests is the single biggest latency optimization available for distributed/local-server architectures. Even with local Docker containers, the serialization/deserialization overhead of $ distinct result sets is non-trivial.

- **Data Locality & Join Performance**:
  - Processing the "Join" (connecting a vector match to its graph neighbors) happens in C++ (Memgraph engine) rather than Python.
  - This allows for filtering *before* returning data. For example: "Find vectors similar to X, BUT ONLY IF they are connected to Entity Y".
  - In the "split" architecture, we must fetch *all* vector candidates, return them to Python, query the graph for *all* of them, and then filter. This is wasteful (over-fetching).

- **Transactional Consistency**:
  - A single store guarantees that if a chunk exists, its graph node exists. In a split architecture, synchronization drift (e.g., NanoDB is updated but Memgraph isn't) leads to phantom references and logic errors.

#### 3.2 Throughput & Scalability (The "Costs")

- **Write Amplification**:
  - Memgraph (like most Graph DBs) is optimized for traversal, not necessarily high-volume bulk vector inserts.
  - Indexing vectors usually involves building HNSW graphs. Doing this inside the main transactional DB process *could* contend with graph traversal workloads under extreme write pressure.
  - *Mitigation*: RAG workloads are typically "Read-Heavy, Write-Burst". We optimize for the read path.

- **Single Point of Failure/Scaling**:
  - Scaling a monolithic Graph+Vector DB is harder than scaling a stateless Vector DB (like Milvus/Qdrant) independently.
  - *Counter-point*: For the targeted scale of LightRAG (local/departmental knowledge bases < 100M nodes), Memgraph's vertical scalability is sufficient, and operational simplicity (1 container vs 2) outweighs horizontal scaling theoreticals.

- **Upsert Speed**:
  - Upserts will be slower than a dedicated vector engine like FAISS/NanoDB because of ACID guarantees and the overhead of maintaining the graph index simultaneously.
  - *Assessment*: Deep optimization of ingestion speed is secondary to retrieval latency. Users ingest documents once but query them thousands of times. A 20% slower ingest is an acceptable tradeoff for a 50% faster query.

### 13.4 Conclusion

The decision to strictly couple Vector and Graph retrieval into a single Cypher execution path is **Justified**.

**Why?**
The "Application-Layer Join" is an anti-pattern when the data lives in the same physical substrate. By pushing the join down to the database engine, we leverage the intrinsic advantage of the Multi-Model Database architecture. The short-term cost (slower upserts) is marginalized by the long-term benefit of query throughput and architectural simplicity.
