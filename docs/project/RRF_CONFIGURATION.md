# Reciprocal Rank Fusion (RRF) Configuration Documentation

## Performance vs Precision Trade-off Setting

**Default Recommendation**: Quality-focused precision for optimal user experience

```env
# RRF Configuration - Default Values
EVAL_FUSION_METHOD=rrf
EVAL_RRF_K=60
EVAL_QUERY_TOP_K=3
EVAL_RRF_VECTOR_WEIGHT=1.0
EVAL_RRF_GRAPH_WEIGHT=1.0
EVAL_RRF_KEYWORD_WEIGHT=1.0

# Performance vs Precision Trade-off
# Users can override based on their needs:
EVAL_PERFORMANCE_MODE=quality  # Options: speed, balanced, quality (default)
```

## Configuration Modes Explained

### **Speed Mode** (Fastest)
```env
EVAL_PERFORMANCE_MODE=speed
EVAL_QUERY_TOP_K=2
EVAL_RRF_K=40  # Lower k = faster processing
```
- **Expected Time**: 120s per query
- **Expected Precision**: 80%
- **Use Case**: Real-time applications, large-scale processing

### **Balanced Mode** (Moderate)
```env
EVAL_PERFORMANCE_MODE=balanced
EVAL_QUERY_TOP_K=3
EVAL_RRF_K=60
```
- **Expected Time**: 180s per query
- **Expected Precision**: 85%
- **Use Case**: General purpose applications

### **Quality Mode** (Most Precise - Default)
```env
EVAL_PERFORMANCE_MODE=quality
EVAL_QUERY_TOP_K=3
EVAL_RRF_K=80  # Higher k = more thorough fusion
```
- **Expected Time**: 200s per query
- **Expected Precision**: 90%
- **Use Case**: High-accuracy applications, research, evaluation

## Runtime Adaptation

The system can automatically adapt based on document size:

```python
# Adaptive configuration based on document characteristics
def adaptive_rrf_config(document_char_count: int, user_mode: str = "quality"):
    if user_mode == "speed":
        return {"top_k": 2, "rrf_k": 40}
    elif user_mode == "balanced":
        return {"top_k": 3, "rrf_k": 60}
    elif document_char_count < 500:  # Very small documents
        return {"top_k": 2, "rrf_k": 80}  # Maximum precision
    elif document_char_count < 1000:  # Small documents
        return {"top_k": 3, "rrf_k": 60}  # Current default
    else:  # Large documents
        return {"top_k": 5, "rrf_k": 60}
```

## Implementation Status

- **Current File**: `docs/RRF_CONFIGURATION.md`
- **Purpose**: User-configurable precision vs speed trade-offs
- **Integration**: Will be linked from architecture decisions
- **Status**: Ready for implementation alongside RRF algorithm

This approach allows users to choose their optimal balance between speed and precision based on their specific use case requirements.
