"""Per-model AB defaults and weights for prompt variant selection.

This module provides helpers to determine the default AB variant for a given
LLM model and to choose a variant based on per-size weights when a hard
default is not specified.
"""

from __future__ import annotations

AB_DEFAULTS = {
    # Explicit per-model defaults (override anything else unless forced)
    "qwen2.5-coder:1.5b": "B",
    "qwen2.5-coder:3b": "A",
    "qwen2.5-coder:7b": "B",
}

AB_WEIGHTS = {
    # Weights per model size group: higher means more preferred for that variant
    # Example: prefer A for smaller models (higher recall), B for largest models (speed)
    "1.5b": {"A": 0.85, "B": 1.0, "C": 0.95},
    "3b": {"A": 0.9, "B": 1.0, "C": 0.97},
    "7b": {"A": 0.85, "B": 1.0, "C": 0.95},
}


def _size_key_from_model(model_name: str) -> str:
    if not model_name:
        return ""
    m = model_name.lower()
    if "1.5b" in m:
        return "1.5b"
    if "3b" in m:
        return "3b"
    if "7b" in m:
        return "7b"
    return ""


def get_default_variant(model_name: str) -> str | None:
    if not model_name:
        return None
    # Exact per-model default
    if model_name in AB_DEFAULTS:
        return AB_DEFAULTS[model_name]
    # Fallback by size group using common patterns
    key = _size_key_from_model(model_name)
    if key and key in ("1.5b", "3b", "7b"):
        # Derive a plausible default key from size group if available
        # Try to map to a known model key if present
        mapping = {
            "1.5b": "qwen2.5-coder:1.5b",
            "3b": "qwen2.5-coder:3b",
            "7b": "qwen2.5-coder:7b",
        }
        candidate = mapping.get(key, "")
        return AB_DEFAULTS.get(candidate)
    return None


def select_variant_by_weights(model_name: str) -> str:
    key = _size_key_from_model(model_name)
    if key not in AB_WEIGHTS:
        # Fallback to A if we can't determine size
        return "A"
    weights = AB_WEIGHTS[key]
    if not weights:
        return "A"
    # Pick the variant with the highest weight (supports A/B/C)
    best = max(weights.items(), key=lambda kv: kv[1])[0]
    return best
