"""Lazy import helpers for KeyBERT-based keyword extraction.

This module provides a tiny utility to attempt a lazy import of KeyBERT
and the necessary sentence transformer model. It returns a prepared KeyBERT
model if dependencies are installed, otherwise returns None.
"""

from typing import Any


def get_keybert_model() -> Any | None:
    """Attempt to import and instantiate a KeyBERT model lazily.

    Returns:
        The KeyBERT model instance if available, else None
    """
    try:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        model = KeyBERT(SentenceTransformer("all-mpnet-base-v2"))
        return model
    except Exception:
        return None
