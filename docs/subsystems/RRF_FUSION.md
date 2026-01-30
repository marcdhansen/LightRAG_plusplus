# Reciprocal Rank Fusion (RRF) Subsystem

## Overview

**Reciprocal Rank Fusion (RRF)** is an information retrieval technique that combines multiple result lists by scoring documents based on their rank positions across different retrieval methods.

**Purpose in LightRAG**: Address the 0% context precision issue in mix mode by implementing consensus-based document ranking.

## Problem Statement

### Current Mix Mode Issues
- **Context Precision**: 0.0000 (baseline evaluation)
- **Problem**: Simple union of vector + graph + keyword results creates noisy context
- **Result**: Retrieved contexts contain excessive irrelevant information

### Root Cause Analysis
1. **Union Approach**: Mix mode concatenates all results without ranking validation
2. **Document Overlap**: Same documents appear in multiple retrieval methods
3. **Noise Amplification**: Low-ranking results from individual methods pollute final context
4. **No Consensus**: Documents ranking well across multiple methods aren't prioritized

## RRF Solution

### Algorithm Overview
```
RRF_Score(doc) = Σ (weight_i / (k + rank_i(doc)))
```

**Where:**
- `weight_i`: Weight for retrieval method i (vector, graph, keyword)
- `k`: Damping constant (typically 60)
- `rank_i(doc)`: 1-based rank of document in method i results

### Intuitive Explanation
- **High-Ranked Documents**: Receive larger scores across methods → Consensus signal
- **Consistently Ranked**: Appear in top positions → Higher reliability score
- **Method-Specific Weighting**: Vector/graph/keyword methods can be prioritized differently

## Implementation Details

### RRF Integration Points

#### 1. QueryParam Enhancement
```python
@dataclass
class QueryParam:
    mode: Literal["local", "global", "hybrid", "naive", "mix", "rrf", "bypass"] = "mix"
    rrf_k: int = 60
    rrf_weights: dict[str, float] = field(default_factory=lambda: {
        "vector": 1.0, "graph": 1.0, "keyword": 1.0
    })
```

#### 2. Retrieval Method Calls
```python
# Parallel execution of all three methods
vector_results = await self.vector_context_for_query(query, param=query_param)
graph_results = await self.graph_context_for_query(query, param=query_param)
keyword_results = await self.local_context_for_query(query, param=query_param)
```

#### 3. Score Calculation & Ranking
```python
# RRF scoring with configurable weights
for method_name, results in enumerate(result_lists):
    method_key = ["vector", "graph", "keyword"][method_name]
    weight = weights.get(method_key, 1.0)

    for rank, result in enumerate(results, 1):  # 1-based ranking
        doc_id = result.get("id", f"doc_{method_key}_{rank}")
        rrf_scores[doc_id] += weight / (k + rank)
```

#### 4. Result Fusion
```python
# Sort by RRF score, apply top_k limit
sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
top_k = min(query_param.top_k or 3, len(sorted_results))
fused_results = [doc_id for doc_id, score in sorted_results[:top_k]]
```

## Performance Matrix Configuration

### User-Configurable Trade-offs

#### Environment Variables
```env
EVAL_PERFORMANCE_MODE=quality  # Options: speed, balanced, quality (default)

# Automatic configuration based on mode
EVAL_RRF_K=60               # Damping constant
EVAL_QUERY_TOP_K=3            # Results count
EVAL_RRF_VECTOR_WEIGHT=1.0   # Method priorities
EVAL_RRF_GRAPH_WEIGHT=1.0
EVAL_RRF_KEYWORD_WEIGHT=1.0
```

#### Expected Performance Matrix

| Configuration | Time (s) | Precision | Use Case |
|--------------|-------------|-----------|----------|
| Baseline Mix | 240 | 0% | Legacy compatibility |
| Conservative RRF | 180 | 75% | Default balanced |
| Aggressive RRF | 120 | 85% | Speed optimization |
| Weighted RRF | 150 | 90% | Quality focus |

### Mode Selection Logic
```python
def get_adaptive_rrf_config(document_char_count: int, user_mode: str = "quality"):
    if user_mode == "speed":
        return {"top_k": 2, "rrf_k": 40}
    elif user_mode == "balanced":
        return {"top_k": 3, "rrf_k": 60}
    elif user_mode == "quality":
        return {"top_k": 3, "rrf_k": 80}
    elif document_char_count < 500:
        return {"top_k": 2, "rrf_k": 80}  # Maximum precision for tiny docs
    else:
        return {"top_k": 3, "rrf_k": 60}  # Default balanced
```

## Integration Architecture

### Query Flow Enhancement
```
┌─────────────────┐
│ User Query     │
└─────────────────┘
        │
        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Vector Search │    │ Graph Search   │    │ Keyword Search  │
│ (similarity)   │    │ (entities)    │    │ (text match)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        │                      ▼                      │
        │            ┌─────────────────────────────┐
        │            │     RRF Fusion Algorithm   │
        │            │  (consensus scoring)      │
        │            └─────────────────────────────┘
        │                      │
        ▼                      │
    ┌─────────────────────┐
    │  Ranked Results   │
    │  (precision-focused)│
    └─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Context to LLM   │
│  (high precision) │
└─────────────────────┘
```

## Validation & Testing

### RRF Unit Tests
- **Algorithm Correctness**: Verify RRF formula implementation
- **Consensus Behavior**: Documents ranked high across methods score higher
- **Weighted Scoring**: Method weights properly applied
- **Parameter Validation**: All RRF configuration options work correctly

### Performance Matrix Tests
- **Timing Validation**: Measure query time vs expected benchmarks
- **Precision Measurement**: Calculate context precision improvements
- **Trade-off Analysis**: Quantify speed vs quality decisions
- **Configuration Recommendations**: Data-driven optimal settings

### RAGAS Integration
- **Baseline Comparison**: Mix mode vs RRF mode on same queries
- **Metric Tracking**: Faithfulness, Answer Relevance, Context Precision, Context Recall
- **Improvement Quantification**: Expected 75-90% precision improvement

## Architectural Decision Rationale

### Why RRF for LightRAG

1. **Precision Focus**: Addresses the core 0% context precision problem
2. **Consensus-Based**: Leverages multiple retrieval intelligently
3. **Configurable**: Adaptable to different use cases and document types
4. **Low-Risk**: Well-established information retrieval technique
5. **Measurable**: Clear performance targets and validation framework

### Alternatives Considered
- **Weighted Hybrid**: Complex, requires extensive training data
- **Learning-to-Rank**: Computationally expensive, needs large training set
- **Cross-Encoder**: Adds complexity without proven precision benefits

### Chosen Solution: RRF
- **Proven**: Standard technique in information retrieval research
- **Efficient**: Minimal computational overhead
- **Adaptable**: User-configurable weights and parameters
- **Measurable**: Clear performance matrix and validation framework

## Deployment Strategy

### Phase 1: Foundation ✅
- [x] QueryParam extension with RRF configuration
- [x] Architecture documentation linkage
- [x] Configuration documentation creation
- [x] Unit test suite implementation

### Phase 2: Implementation 🚧
- [ ] Core RRF algorithm completion
- [ ] Performance matrix execution
- [ ] RAGAS evaluation integration
- [ ] Production configuration validation

### Phase 3: Validation 📊
- [ ] Timing vs score trade-off analysis
- [ ] User configuration recommendations
- [ ] Architectural decision documentation
- [ ] Performance baseline establishment

## Success Metrics

### Technical Validation
- [ ] All RRF configuration options tested
- [ ] RRF scoring formula verified mathematically
- [ ] Performance matrix executed successfully
- [ ] Context precision improvement measured

### Performance Targets
- [ ] Context Precision: 0% → 75%+ (75%+ improvement)
- [ ] Query Time: 240s → 150s- (37%+ speed improvement)
- [ ] Overall RAGAS Score: 0.69 → 0.80+ (16%+ overall improvement)

### User Experience
- [ ] Clear performance mode configuration
- [ ] Automatic adaptation based on document size
- [ ] Transparent speed vs quality trade-offs
- [ ] Data-driven configuration recommendations

---

**RRF Fusion Subsystem**: Implementing consensus-based document ranking to solve precision challenges in LightRAG's multi-modal retrieval approach.
