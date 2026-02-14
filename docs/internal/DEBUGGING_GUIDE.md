# LightRAG Context Passing Bug Debugging Kit

**For GitHub Issue #2643: /query endpoint doesn't pass retrieved context to LLM (OpenAI binding)**

This debugging kit provides comprehensive tools to identify and fix the root cause of context passing failures between `/query` and `/query/data` endpoints.

## 🛠️ Debugging Tools

### 1. Enhanced Logging (Phase 1 Complete)

**Modified Files:**
- `lightrag/operate.py` - Added verbose debugging at critical failure points
- `lightrag/kg/nano_vector_db_impl.py` - Added vector search result logging

**New Debug Tags:**
- `[KEYWORDS]` - Keyword extraction success/failure
- `[CONTEXT]` - Empty context detection and keyword fallback  
- `[TOKENS]` - Token budget allocation issues
- `[VECTOR]` - Vector search results and threshold effects
- `[PROMPT]` - System prompt construction and context data
- `[LLM_CALL]` - Final LLM invocation details

**Usage:**
```bash
# Enable verbose debugging
export VERBOSE=true

# Or set programmatically
from lightrag.utils import set_verbose_debug
set_verbose_debug(True)
```

### 2. Query Comparison Tool

**File:** `debug_query_comparison.py`

Compares `/query` vs `/query/data` endpoint behavior for identical queries.

**Features:**
- Side-by-side endpoint testing
- Context availability analysis  
- Generic response detection
- Rich comparison reporting

**Usage:**
```bash
python debug_query_comparison.py "Who is researcher?" --verbose
```

### 3. Configuration Health Checker

**File:** `config_health_check.py`

Validates common configuration problems that cause context failures.

**Health Checks:**
- Server connectivity
- Model information
- Embedding quality (case sensitivity testing)
- Cosine threshold effectiveness
- Token allocation for 8K context models
- Configuration validation

**Usage:**
```bash
python config_health_check.py --url http://localhost:9621
```

### 4. Reproduction Case Manager

**File:** `create_reproduction_case.py`

Creates the exact scenario from GitHub issue for systematic debugging.

**Features:**
- Document ingestion with test data
- Controlled query testing
- Direct LLM verification
- Automated bug confirmation

**Usage:**
```bash
# Full reproduction case
python create_reproduction_case.py --ingest --test

# Test with existing data
python create_reproduction_case.py --skip-ingest --test
```

## 🔍 Root Cause Analysis

Based on investigation, the most likely failure points are:

### **Priority 1: Token Budget Issues**
- **8K context models** (qwen2.5:7b) have limited token space
- **Negative chunk budgets** when `max_total_tokens` not properly set
- **Symptom:** Context retrieved but chunks truncated to empty

### **Priority 2: Embedding Quality**  
- **Case sensitivity** between "researcher" and "Researcher"
- **qwen3-embedding:4b** quality with proper nouns
- **Cosine threshold 0.1** allows poor matches
- **Symptom:** Vector search returns no results

### **Priority 3: Keyword Extraction Failures**
- **JSON parsing errors** in LLM keyword extraction
- **Short queries** falling back to query-as-keyword
- **Symptom:** Empty high/low level keywords

### **Priority 4: OpenAI Binding Issues**
- **Message construction** problems in OpenAI client
- **System prompt passing** failures
- **Symptom:** LLM receives no context despite successful retrieval

## 🎯 Debugging Strategy

### **Step 1: Enable Verbose Logging**
```bash
export VERBOSE=true
python -m lightrag.api.server
```

Run query and look for these patterns in logs:
- `[TOKENS] NEGATIVE CHUNK BUDGET` - Token allocation problem
- `[VECTOR] Query returned 0 matches` - Vector search problem  
- `[KEYWORDS] JSON decode error` - Keyword extraction failure
- `[PROMPT] WARNING: Very short context` - Context truncation

### **Step 2: Run Configuration Health Check**
```bash
python config_health_check.py
```

Focus on ERROR level issues first:
- **Embedding case sensitivity** - Test with "researcher" vs "Researcher"
- **Cosine threshold 0.1** - Try 0.3, 0.4 for better results
- **Token allocation** - Verify 8K model has reasonable budget

### **Step 3: Compare Endpoints**
```bash
python debug_query_comparison.py "Who is researcher?" --verbose
```

Look for:
- **Different context counts** between endpoints
- **Generic LLM responses** despite available context
- **Status discrepancies** indicating silent failures

### **Step 4: Reproduce Exact Case**
```bash
python create_reproduction_case.py --ingest --test
```

This will:
1. Ingest the exact document from GitHub issue
2. Test both query endpoints  
3. Test direct LLM with context
4. Provide definitive bug confirmation

## 🛠️ Common Fixes

### **Token Budget Fix**
```python
# In lightrag/core/__init__.py or config
if "qwen2.5" in model_name.lower():
    max_total_tokens = 6000  # Conservative for 8K models
else:
    max_total_tokens = 30000  # Default for larger models
```

### **Cosine Threshold Fix**
```bash
# Test different thresholds
export COSINE_THRESHOLD=0.3
export COSINE_THRESHOLD=0.4
export COSINE_THRESHOLD=0.5
```

### **Case Normalization Fix**
Add to preprocessing pipeline:
```python
# Normalize case for entity extraction
normalized_text = text.lower()
# Or implement case-insensitive vector search
```

### **Embedding Quality Test**
```bash
# Test with different embedding models
export EMBEDDING_MODEL=bge-m3
export EMBEDDING_MODEL=text-embedding-3-small
```

## 📊 Success Criteria

**Bug Confirmed:**
- `/query/data` retrieves context successfully
- `/query` returns "I don't have information..." response  
- Direct LLM test shows context can be used
- Verbose logs show where context is lost

**Bug Fixed:**
- Both endpoints return consistent results
- `/query` response includes information from retrieved context
- No generic responses when context is available
- Token budgets properly allocated

**Regression Prevention:**
- Automated tests for context passing
- Configuration validation on startup  
- Token budget monitoring and alerts
- Embedding quality benchmarks

## 🚀 Usage Workflow

1. **Initial Diagnosis:**
   ```bash
   python config_health_check.py
   python debug_query_comparison.py "test query"
   ```

2. **Bug Reproduction:**
   ```bash
   python create_reproduction_case.py --skip-ingest --test
   ```

3. **Targeted Fix:**
   - Apply specific fix based on root cause identified
   - Test with reproduction case
   - Verify with multiple queries

4. **Validation:**
   - Run full test suite
   - Check performance regression
   - Update configuration documentation

---

**Phase 1 Complete: Enhanced logging infrastructure deployed and ready for root cause analysis.**

Next: Phase 2 - Root Cause Identification with specific debugging scenarios.