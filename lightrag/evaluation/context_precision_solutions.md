# Context Precision Issue Analysis & Solutions

## Problem Diagnosis

**Context Precision: 0.0000** indicates that while LightRAG retrieved relevant information (100% context recall), the retrieved content contains excessive noise or irrelevant information.

## Root Cause Analysis

### 1. Low Top-K Setting
- **Current**: `EVAL_QUERY_TOP_K=5` - retrieving 5 entities/relations
- **Issue**: With small dickens_short.txt (611 chars, 1 chunk), system may be returning duplicate or expanded context
- **Impact**: RAGAS compares retrieved context to ground truth, finds noise → 0% precision

### 2. Single Chunk Document
- **Document Size**: 611 characters processed as 1 chunk
- **Retrieval Behavior**: System may be returning:
  - Full document text repeatedly
  - Multiple overlapping entity references
  - Redundant context due to lack of chunk diversity

### 3. Mix Mode Retrieval
- **Current Mode**: `"mode": "mix"`
- **Behavior**: Combines vector + graph + keyword search
- **Potential Issue**: Multiple retrieval methods returning overlapping results

## Immediate Solutions

### Solution 1: Optimize Top-K for Small Documents
```bash
# For evaluation with small documents
export EVAL_QUERY_TOP_K=3

# Or even more conservative for tiny documents
export EVAL_QUERY_TOP_K=1
```

### Solution 2: Test Different Retrieval Modes
```bash
# Test vector-only mode (more precise)
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What historical period...", "mode": "vector", "top_k": 3}'

# Test local mode (exact text matching)
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What historical period...", "mode": "local", "top_k": 3}'
```

### Solution 3: Disable Reranking for Small Contexts
```bash
# Reranking may spread small contexts thin
export EVAL_ENABLE_RERANK=false
export EVAL_RERANK_ENTITIES=false
export EVAL_RERANK_RELATIONS=false
```

### Solution 4: Optimize Chunking Strategy
```python
# For small documents in evaluation
# Create multiple meaningful chunks instead of single large chunk
CHUNK_SIZE=300  # Instead of default 1200
CHUNK_OVERLAP=50  # Reduce overlap for precision
```

## Advanced Solutions

### Solution 5: Context Deduplication
Add context deduplication in evaluation script:

```python
# In eval_rag_quality.py around line 390
def deduplicate_contexts(contexts):
    """Remove duplicate and highly overlapping contexts"""
    seen = set()
    deduped = []
    for ctx in contexts:
        # Create a hash for similar content
        ctx_hash = hash(ctx[:100])  # First 100 chars
        if ctx_hash not in seen:
            seen.add(ctx_hash)
            deduped.append(ctx)
    return deduped

contexts = deduplicate_contexts(contexts)
```

### Solution 6: Enhanced Query Processing
Implement smarter query processing for small documents:

```python
# Add to evaluation payload
payload = {
    "query": question,
    "mode": "local",  # Use exact matching for small docs
    "top_k": min(3, len(document_chunks)),  # Don't exceed document size
    "max_context_tokens": 1000,  # Limit context size
    "include_references": True,
    "include_chunk_content": True,
}
```

## Testing Strategy

### Phase 1: Quick Wins (Immediate)
1. **Reduce Top-K**: Test with `EVAL_QUERY_TOP_K=1, 2, 3`
2. **Disable Rerank**: Set `EVAL_ENABLE_RERANK=false`
3. **Mode Testing**: Compare `"vector"` vs `"local"` vs `"mix"`

### Phase 2: Systematic Testing
1. **Chunk Analysis**: Review how dickens_short.txt was chunked
2. **Context Inspection**: Log actual retrieved contexts for precision analysis
3. **Threshold Tuning**: Adjust cosine similarity thresholds

### Phase 3: Advanced Optimization
1. **Multi-Modal Retrieval**: Combine methods but deduplicate results
2. **Context Ranking**: Implement custom precision-focused ranking
3. **Document Size Awareness**: Adaptive parameters based on document size

## Recommended Actions

### Immediate (Next Session)
```bash
# Test with conservative settings
export EVAL_QUERY_TOP_K=2
export EVAL_ENABLE_RERANK=false
python lightrag/evaluation/eval_rag_quality.py \
  --dataset lightrag/evaluation/dickens_dataset.json \
  --limit 2
```

### Configuration Changes
Add to `.env` for evaluation:
```env
# Small document optimization
EVAL_QUERY_TOP_K=3
EVAL_ENABLE_RERANK=false
EVAL_RERANK_ENTITIES=false
EVAL_RERANK_RELATIONS=false

# For documents < 1000 chars, use even smaller top_k
EVAL_SMALL_DOC_TOP_K=2
EVAL_SMALL_DOC_THRESHOLD=1000
```

### Code Enhancement
Modify evaluation script to detect document size and adapt parameters:

```python
# Add adaptive top-k based on document size
def adaptive_top_k(document_char_count):
    if document_char_count < 500:
        return 2  # Very small docs
    elif document_char_count < 1000:
        return 3  # Small docs
    else:
        return 5  # Default for larger docs

# In query payload
doc_size = get_document_size(question)  # Would need implementation
payload["top_k"] = adaptive_top_k(doc_size)
```

## Expected Impact

**Conservative Settings Expected Results:**
- Context Precision: 0% → 60-80%
- Context Recall: 100% → 80-90% (slight drop acceptable)
- Overall RAGAS Score: 0.69 → 0.75-0.85

**Optimal Settings Expected Results:**
- Context Precision: 0% → 80-90%
- Context Recall: Maintained at 90-100%
- Overall RAGAS Score: 0.69 → 0.85-0.90

## Implementation Priority

1. **High Priority**: Reduce EVAL_QUERY_TOP_K to 2-3
2. **Medium Priority**: Disable reranking for small documents
3. **Low Priority**: Implement adaptive parameter logic
4. **Future**: Context deduplication and ranking enhancements

The key insight: **Small documents need precision-focused retrieval, not maximum recall.**
