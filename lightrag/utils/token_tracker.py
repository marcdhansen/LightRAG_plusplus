"""Token usage tracking for LightRAG.

This module provides utilities for tracking and reporting token consumption
across extraction, querying, and other LLM operations.
"""

import asyncio
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from lightrag.utils import get_env_value, logger


@dataclass
class TokenMetrics:
    """Token usage metrics for a single operation."""

    operation: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    @property
    def cost_estimate(self) -> float:
        """Estimate cost based on token usage (placeholder for actual pricing)."""
        return self.prompt_tokens * 0.00001 + self.completion_tokens * 0.00003


class TokenTracker:
    """Track token usage across LightRAG operations."""

    _instance: "TokenTracker | None" = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> "TokenTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._metrics: list[TokenMetrics] = []
        self._enabled = bool(
            get_env_value("LANGFUSE_ENABLE_TRACE", "false").lower() == "true"
        )
        self._operation_counts: dict[str, int] = {}
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_operations = 0

    @property
    def is_enabled(self) -> bool:
        """Check if token tracking is enabled."""
        return self._enabled

    def record_operation(
        self,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float = 0.0,
        metadata: dict | None = None,
    ) -> TokenMetrics:
        """Record token usage for an operation."""
        metrics = TokenMetrics(
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self._metrics.append(metrics)
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._total_operations += 1
        self._operation_counts[operation] = self._operation_counts.get(operation, 0) + 1
        return metrics

    def get_summary(self) -> dict[str, Any]:
        """Get summary of token usage."""
        return {
            "total_operations": self._total_operations,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "operation_counts": dict(self._operation_counts),
            "estimated_cost_dollars": (
                self._total_prompt_tokens * 0.00001
                + self._total_completion_tokens * 0.00003
            ),
        }

    def get_operation_stats(self, operation: str) -> dict[str, Any]:
        """Get statistics for a specific operation."""
        op_metrics = [m for m in self._metrics if m.operation == operation]
        if not op_metrics:
            return {"count": 0, "avg_tokens": 0, "avg_duration_ms": 0}

        prompt_tokens = sum(m.prompt_tokens for m in op_metrics)
        completion_tokens = sum(m.completion_tokens for m in op_metrics)
        duration = sum(m.duration_ms for m in op_metrics)
        count = len(op_metrics)

        return {
            "count": count,
            "total_prompt_tokens": prompt_tokens,
            "total_completion_tokens": completion_tokens,
            "avg_prompt_tokens": prompt_tokens / count,
            "avg_completion_tokens": completion_tokens / count,
            "avg_total_tokens": (prompt_tokens + completion_tokens) / count,
            "avg_duration_ms": duration / count,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._operation_counts.clear()
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_operations = 0


def get_token_tracker() -> TokenTracker:
    """Get the global TokenTracker instance."""
    return TokenTracker()


@contextmanager
def track_operation(
    operation: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    metadata: dict | None = None,
):
    """Context manager for tracking an operation's token usage."""
    tracker = get_token_tracker()
    start_time = time.time()
    try:
        yield tracker
    finally:
        duration_ms = (time.time() - start_time) * 1000
        tracker.record_operation(
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms,
            metadata=metadata,
        )


def estimate_prompt_tokens(text: str) -> int:
    """Estimate token count for a text string.

    This is a simple estimation. For accurate counts, use tiktoken.
    """
    if not text:
        return 0
    return len(text) // 4


def log_token_summary() -> None:
    """Log a summary of token usage."""
    tracker = get_token_tracker()
    summary = tracker.get_summary()
    logger.info(
        f"Token Usage Summary: {summary['total_operations']} operations, "
        f"{summary['total_tokens']} total tokens, "
        f"${summary['estimated_cost_dollars']:.4f} estimated cost"
    )
