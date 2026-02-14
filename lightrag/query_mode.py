"""Query mode detection for LightRAG.

This module provides utilities for automatically detecting the optimal query mode
based on query characteristics.
"""

import re


def detect_query_mode(query: str) -> str:
    """
    Automatically detect the optimal query mode based on query characteristics.

    Uses simple heuristics to analyze the query and select the best retrieval mode:
    - "naive": Short, vague queries
    - "local": Queries with specific entities, names, numbers
    - "global": Conceptual queries about relationships, causes, comparisons
    - "hybrid": Complex queries that need both local and global
    - "mix": Technical queries that benefit from KG + vector combination

    Args:
        query: The user's query text

    Returns:
        The detected optimal mode: "naive", "local", "global", "hybrid", or "mix"
    """
    query_lower = query.lower().strip()
    query_len = len(query)

    if query_len == 0 or not query.strip():
        return "hybrid"

    CONCEPTUAL_PATTERNS = [
        "how to",
        "how does",
        "how did",
        "why does",
        "why is",
        "what is",
        "what are",
        "what does",
        "what was",
        "what will",
        "define",
        "meaning of",
        "description of",
        "explain",
        "describe",
        "tell me about",
        "give me information about",
        "explain the concept",
        "compare",
        "difference between",
        "what are the benefits",
        "what are the advantages",
        "what causes",
        "relationship between",
        "connection between",
    ]

    TECHNICAL_PATTERNS = [
        "function",
        "method",
        "class",
        "api",
        "code",
        "programming",
        "implement",
        "algorithm",
        "error",
        "bug",
        "debug",
        "syntax",
        "parameter",
        "return",
        "import",
        "module",
        "library",
        "package",
    ]

    has_concepts = any(p in query_lower for p in CONCEPTUAL_PATTERNS)
    has_technical = any(p in query_lower for p in TECHNICAL_PATTERNS)

    has_numbers = bool(re.search(r"\b\d+\b", query))
    has_email = bool(re.search(r"\b\w+@\w+\.\w+\b", query))
    has_date = bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", query))

    name_pattern = r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"
    has_name = bool(re.search(name_pattern, query))

    if query_len < 20:
        if has_concepts:
            return "global"
        if has_technical:
            return "mix"
        return "naive"

    if has_technical:
        return "mix"

    if has_concepts and not has_numbers and not has_name:
        return "global"

    if has_name or has_numbers or has_email or has_date:
        return "local"

    if has_concepts:
        return "hybrid"

    if query_len > 100:
        return "hybrid"

    return "hybrid"
