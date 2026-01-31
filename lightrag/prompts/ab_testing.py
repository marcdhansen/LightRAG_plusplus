"""LightRAG Prompt AB Testing (Skeleton).

This module provides a minimal hook to support simple AB testing of prompt variants
without requiring a full integration into the runtime prompt pipeline yet.

Usage (reserved for future integration):
- Expose a single function to choose a variant key (e.g., 'A' or 'B') based on
  model name or a random seed. The main extractor can then select a different
  system prompt key depending on the variant.
"""

from __future__ import annotations

try:
    from .ab_test_config import DEFAULT_AB_VARIANT  # type: ignore
except Exception:
    DEFAULT_AB_VARIANT = None  # type: ignore


def choose_variant(llm_model_name: str) -> str:
    """Return a prompt variant key ('A' or 'B') for a given model name.

    This is a lightweight heuristic: larger models lean toward variant B, smaller
    models toward variant A. If no model name is provided, fall back to 'A'.
    """
    # First, check for per-model default variant from AB defaults
    try:
        from lightrag.ab_defaults import get_default_variant

        default_variant = get_default_variant(llm_model_name)
        if default_variant:
            return default_variant
    except Exception:
        pass

    name = (llm_model_name or "").lower()
    if "7b" in name or name.endswith("b") and len(name) > 0:
        return "B"  # Larger (7B) tends to benefit from a different prompt
    if "3b" in name:
        return "B"
    # Optional: use a size heuristic if available
    try:
        from lightrag.utils import parse_model_size

        size = parse_model_size(llm_model_name)  # type: ignore
        if size is not None and size >= 3.0:
            return "B"
    except Exception:
        pass
    return DEFAULT_AB_VARIANT or "A"
