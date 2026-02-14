# Technical Analysis: Automatic Query Mode Selection

## Feature Overview

**Feature**: Automatic query mode selection with simple heuristics  
**Module**: `lightrag.operate`  
**Function**: `detect_query_mode`

## Problem Statement

Users must manually specify query modes (naive, local, global, hybrid, mix) when querying the RAG system. This adds friction and requires users to understand the differences between modes.

## Solution

Implement automatic query mode detection based on query characteristics:

| Query Pattern | Detected Mode |
|--------------|---------------|
| Short/vague (< 5 chars) | naive |
| Contains email/phone | local |
| Contains dates | local |
| Conceptual (how/why) | global |
| Technical (fix/debug/error) | mix |
| Long/complex | hybrid |

## Implementation Details

### Algorithm
1. Check query length - short queries → naive
2. Check for specific patterns (emails, dates) → local
3. Check for conceptual keywords → global
4. Check for technical keywords → mix
5. Default → hybrid

### Performance Considerations
- Simple regex-based detection: O(n) where n = query length
- No external API calls required
- Stateless - no caching needed

## Tradeoffs

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Accuracy | Heuristic-based | Fast, no LLM needed |
| Coverage | 5 modes | Balances complexity/utility |
| Latency | < 1ms | Inline detection |

## Testing Strategy

- Unit tests: All detection rules
- Functional tests: End-to-end scenarios
- Edge cases: Empty, whitespace, very long queries
