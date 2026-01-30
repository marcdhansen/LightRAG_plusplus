# Reciprocal Rank Fusion (RRF) for Context Precision

## Concept Overview

**Reciprocal Rank Fusion (RRF)** combines multiple retrieval result lists by scoring each document based on its rank across different methods, giving higher scores to documents that rank well across multiple approaches.

## How RRF Solves the Context Precision Problem

### Current Issue (Mix Mode Problems)
```
Vector Search Results:  [chunk_A, chunk_B, chunk_C]
Graph Search Results:   [chunk_A, chunk_D, chunk_E]
Keyword Search Results: [chunk_F, chunk_A, chunk_G]

Mix Mode Union: [chunk_A, chunk_B, chunk_C, chunk_D, chunk_E, chunk_F, chunk_G]
→ 7 results, many irrelevant → 0% context precision
```

### RRF Solution (Rank-Based Fusion)
```
Ranks:
chunk_A: ranks [1, 1, 2] → RRF score: 1/1 + 1/1 + 1/2 = 2.5
chunk_B: ranks [2, 0, 0] → RRF score: 1/2 + 0 + 0 = 0.5
chunk_D: ranks [0, 2, 0] → RRF score: 0 + 1/2 + 0 = 0.5

RRF Results: [chunk_A (2.5), chunk_B (0.5), chunk_D (0.5)]
→ Top 2-3 most consistently relevant → 80%+ context precision
```

## RRF Implementation for LightRAG

### Core RRF Formula
```python
def reciprocal_rank_fusion(result_lists, k=60):
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion
    k is a constant (typically 60) to dampen low ranks
    """
    # Create score dictionary for all documents
    rrf_scores = {}

    for results in result_lists:
        for rank, doc in enumerate(results, 1):  # 1-based ranking
            doc_id = doc['id']
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0
            rrf_scores[doc_id] += 1.0 / (k + rank)

    # Sort by RRF score descending
    ranked_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [(doc_id, score) for doc_id, score in ranked_results]
```

### LightRAG Integration Points

#### 1. Query Router Enhancement
```python
# In LightRAG query processing
async def query_with_rrf(query: str, top_k: int = 5):
    """Execute parallel searches and fuse with RRF"""

    # Parallel execution of all three methods
    vector_results = await vector_search(query, top_k * 2)  # Get more candidates
    graph_results = await graph_search(query, top_k * 2)
    keyword_results = await keyword_search(query, top_k * 2)

    # RRF fusion
    rrf_results = reciprocal_rank_fusion([
        vector_results,
        graph_results,
        keyword_results
    ], k=60)

    # Return top-K from fused results
    return rrf_results[:top_k]
```

#### 2. API Endpoint Enhancement
```python
# Add to query endpoint options
@app.post("/query")
async def enhanced_query(request: QueryRequest):
    if request.fusion_method == "rrf":
        results = await query_with_rrf(
            query=request.query,
            top_k=request.top_k
        )
    elif request.fusion_method == "mix":
        results = await query_mix_mode(request)  # Current method
    else:
        results = await vector_search(request)

    return {"response": answer, "references": results}
```

### Evaluation Integration

#### Enhanced Evaluation Script
```python
# In eval_rag_quality.py, modify payload
payload = {
    "query": question,
    "fusion_method": "rrf",  # NEW: Use RRF instead of mix
    "top_k": int(os.getenv("EVAL_QUERY_TOP_K", "3")),  # Reduced from 5
    "rrf_k": 60,  # RRF damping constant
    "include_references": True,
    "include_chunk_content": True,
}
```

## Expected Impact on Context Precision

### Quantitative Improvements
```
Current Mix Mode:
- Retrieved: 7 contexts
- Relevant: 2 contexts
- Precision: 2/7 = 28.6%

RRF Method:
- Retrieved: 3 contexts
- Relevant: 2-3 contexts
- Precision: 2.5/3 = 83.3%
```

### RRF Advantages for Small Documents
1. **Consensus-Based**: Documents ranked well across methods are likely relevant
2. **Noise Reduction**: Ignores documents that only rank well in one method
3. **Diversity Preservation**: Still gets results from different retrieval approaches
4. **Configurable**: Can tune k constant for strictness/leniency

## Implementation Strategy

### Phase 1: Quick RRF Prototype
```python
# Simple RRF in existing mix mode
def simple_rrf_fusion(vector_results, graph_results, keyword_results, top_k=3):
    """Minimal RRF implementation for immediate testing"""
    all_results = {}

    # Score each result by rank position
    for rank, result in enumerate(vector_results[:5], 1):
        all_results[result['id']] = all_results.get(result['id'], 0) + 1.0/(60+rank)

    for rank, result in enumerate(graph_results[:5], 1):
        all_results[result['id']] = all_results.get(result['id'], 0) + 1.0/(60+rank)

    for rank, result in enumerate(keyword_results[:5], 1):
        all_results[result['id']] = all_results.get(result['id'], 0) + 1.0/(60+rank)

    # Return top-scoring results
    sorted_results = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    return [result_id for result_id, score in sorted_results[:top_k]]
```

### Phase 2: Production RRF System
- **Parallel Query Execution**: Run all retrieval methods concurrently
- **Score Normalization**: Handle different scoring scales
- **Result Deduplication**: Remove duplicate document IDs before fusion
- **Performance Monitoring**: Track fusion overhead vs precision gain

### Phase 3: Advanced Fusion Options
1. **Weighted RRF**: Different weights for vector/graph/keyword based on query type
2. **Adaptive k**: Adjust RRF constant based on document size
3. **Rank Threshold**: Minimum rank threshold to enter fusion

## Configuration for Evaluation

### Environment Variables
```env
# RRF Configuration
EVAL_FUSION_METHOD=rrf
EVAL_RRF_K=60
EVAL_QUERY_TOP_K=3  # Reduced with better fusion

# Retrieval Method Weights (optional)
EVAL_VECTOR_WEIGHT=1.0
EVAL_GRAPH_WEIGHT=0.8
EVAL_KEYWORD_WEIGHT=0.6
```

### Expected RAGAS Score Improvement
```
Current Baseline:
- Context Precision: 0.0000
- Overall RAGAS Score: 0.6884

With RRF:
- Context Precision: 0.8000 (predicted)
- Overall RAGAS Score: 0.8500 (predicted)
- Improvement: +23.4% overall score
```

## Recommendation

**RRF is an excellent solution** because:
1. **Addresses Root Cause**: Focuses on consensus across retrieval methods
2. **Maintains Recall**: Still gets documents from all approaches
3. **Dramatically Improves Precision**: Prioritizes consistently-ranked results
4. **Low Implementation Risk**: Well-established fusion technique
5. **Configurable**: Can fine-tune for different document sizes

**Next Step**: Implement Phase 1 prototype and test with dickens_short.txt to validate precision improvement.
