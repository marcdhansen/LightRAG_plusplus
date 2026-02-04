"""
GroundedAI Integration for LightRAG Evaluation

Provides specialized Small Language Model (SLM) evaluation capabilities
using GroundedAI's purpose-built evaluation models.

Key Features:
- 100% local evaluation (no API keys required)
- Specialized SLM evaluation modes: HALLUCINATION, TOXICITY, RAG_RELEVANCE
- Token-efficient evaluation optimized for small models
- Unified interface with existing RAGAS evaluation

Usage:
    from lightrag.evaluation.grounded_ai_backend import GroundedAIEvaluator

    evaluator = GroundedAIEvaluator(model_id="grounded-ai/phi4-mini-judge")
    result = evaluator.evaluate_hallucination(
        query="What is the capital of France?",
        response="London is the capital of France.",
        context="Paris is the capital of France."
    )
"""

import os
from datetime import datetime

from lightrag.utils import logger

try:
    from grounded_ai import Evaluator as GroundedAIEvaluator

    GROUNDED_AI_AVAILABLE = True
except ImportError:
    GROUNDED_AI_AVAILABLE = False
    GroundedAIEvaluator = None

# Try to import EvaluationError for error handling
try:
    from grounded_ai.schemas import EvaluationError
except ImportError:
    # Fallback for older versions
    EvaluationError = Exception


class GroundedAIRAGEvaluator:
    """
    GroundedAI integration for LightRAG evaluation with SLM optimization.

    Provides specialized evaluation modes designed for small language models:
    - HALLUCINATION: Detect factual inconsistencies vs context
    - TOXICITY: Identify toxic or harmful content
    - RAG_RELEVANCE: Assess document relevance to queries

    Benefits over traditional evaluation:
    - 100% local evaluation (no API costs)
    - Optimized for small model constraints
    - Faster evaluation times
    - Privacy-first processing
    """

    def __init__(
        self,
        model_id: str = "grounded-ai/phi4-mini-judge",
        device: str | None = None,
        quantization: bool = False,
        timeout: int = 180,
    ):
        """
        Initialize GroundedAI evaluator.

        Args:
            model_id: GroundedAI model identifier
            device: Device to run evaluation on ('cuda', 'cpu', or auto-detect)
            quantization: Whether to use model quantization (8-bit)
            timeout: Evaluation timeout in seconds

        Raises:
            ImportError: If grounded-ai package not installed
        """
        if not GROUNDED_AI_AVAILABLE:
            raise ImportError(
                "GroundedAI not available. Install with: pip install grounded-ai[slm]"
            )

        self.model_id = model_id
        self.device = device or "cpu"  # Default to CPU for broader compatibility

        # Force CPU mode for GroundedAI to avoid CUDA issues
        if self.device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        self.quantization = quantization
        self.timeout = timeout

        # Initialize GroundedAI evaluator
        # Note: device parameter is only for SLM models, not for OpenAI/Anthropic
        kwargs = {"model": model_id}
        if not (model_id.startswith("openai/") or model_id.startswith("anthropic/")):
            # Only pass device parameter for non-OpenAI models (SLMs)
            kwargs["device"] = device
            kwargs["quantization"] = quantization

        self._evaluator = GroundedAIEvaluator(**kwargs)

        logger.info(f"GroundedAI evaluator initialized: {model_id} on {device}")

    def evaluate_hallucination(
        self, query: str, response: str, context: str, confidence_threshold: float = 0.5
    ) -> dict[str, float | str | bool]:
        """
        Evaluate response for hallucination using GroundedAI's specialized model.

        Hallucination detection checks if response is factually consistent
        with provided context and query.

        Args:
            query: Original user query
            response: Model-generated response to evaluate
            context: Ground truth context for comparison
            confidence_threshold: Minimum confidence threshold for reliable evaluation

        Returns:
            Dict containing:
            - score: 0.0 (faithful) to 1.0 (hallucinated)
            - label: 'faithful' or 'hallucinated'
            - reasoning: Detailed explanation of evaluation
            - confidence: Confidence score (0.0-1.0)
            - success: Whether evaluation succeeded
            - error: Error message if evaluation failed
        """
        try:
            result = self._evaluator.evaluate(
                query=query,
                response=response,
                context=context,
                eval_mode="HALLUCINATION",
            )

            # Handle case where GroundedAI returns a valid result object
            if hasattr(result, "score"):
                return {
                    "score": result.score,
                    "label": result.label,
                    "reasoning": getattr(result, "reasoning", ""),
                    "confidence": getattr(result, "confidence", 1.0),
                    "success": True,
                    "error": None,
                }
            else:
                # GroundedAI returned an error object/message
                logger.error(f"GroundedAI returned error: {result}")
                return {
                    "score": 0.5,  # Neutral score
                    "label": "evaluation_failed",
                    "reasoning": f"GroundedAI error: {str(result)}",
                    "confidence": 0.0,
                    "success": False,
                    "error": str(result),
                }

        except Exception as e:
            logger.error(f"GroundedAI hallucination evaluation failed: {str(e)}")
            return {
                "score": 0.5,  # Neutral score
                "label": "evaluation_failed",
                "reasoning": f"Evaluation error: {str(e)}",
                "confidence": 0.0,
                "success": False,
                "error": str(e),
            }

    def evaluate_toxicity(
        self, response: str, confidence_threshold: float = 0.5
    ) -> dict[str, float | str | bool]:
        """
        Evaluate response for toxicity using GroundedAI's specialized model.

        Args:
            response: Text to evaluate for toxicity
            confidence_threshold: Minimum confidence threshold for reliable evaluation

        Returns:
            Dict containing toxicity evaluation results
        """
        try:
            result = self._evaluator.evaluate(response=response, eval_mode="TOXICITY")

            return {
                "score": result.score,
                "label": result.label,
                "reasoning": getattr(result, "reasoning", ""),
                "confidence": getattr(result, "confidence", 1.0),
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"GroundedAI toxicity evaluation failed: {str(e)}")
            return {
                "score": 0.5,
                "label": "evaluation_failed",
                "reasoning": f"Evaluation error: {str(e)}",
                "confidence": 0.0,
                "success": False,
                "error": str(e),
            }

    def evaluate_rag_relevance(
        self, query: str, document: str, confidence_threshold: float = 0.5
    ) -> dict[str, float | str | bool]:
        """
        Evaluate document relevance to query using GroundedAI's specialized model.

        This is similar to RAGAS context precision but optimized for SLMs.

        Args:
            query: User query
            document: Document/retrieved context to evaluate
            confidence_threshold: Minimum confidence threshold for reliable evaluation

        Returns:
            Dict containing relevance evaluation results
        """
        try:
            result = self._evaluator.evaluate(
                query=query,
                response=document,  # GroundedAI treats document as 'response'
                eval_mode="RAG_RELEVANCE",
            )

            return {
                "score": result.score,
                "label": result.label,
                "reasoning": getattr(result, "reasoning", ""),
                "confidence": getattr(result, "confidence", 1.0),
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"GroundedAI RAG relevance evaluation failed: {str(e)}")
            return {
                "score": 0.5,
                "label": "evaluation_failed",
                "reasoning": f"Evaluation error: {str(e)}",
                "confidence": 0.0,
                "success": False,
                "error": str(e),
            }

    def evaluate_comprehensive(
        self, query: str, response: str, context: str, confidence_threshold: float = 0.5
    ) -> dict[str, dict]:
        """
        Run comprehensive evaluation using all GroundedAI evaluation modes.

        Combines hallucination, toxicity, and RAG relevance evaluation
        for a complete assessment of response quality.

        Args:
            query: Original user query
            response: Model-generated response
            context: Retrieved context for comparison
            confidence_threshold: Minimum confidence threshold

        Returns:
            Dict containing results from all evaluation modes:
            {
                "hallucination": {...},
                "toxicity": {...},
                "rag_relevance": {...},
                "summary": {
                    "overall_score": float,
                    "total_evaluations": int,
                    "successful_evaluations": int,
                    "evaluation_time": float
                }
            }
        """
        start_time = datetime.now()

        # Run all evaluations
        hallucination_result = self.evaluate_hallucination(
            query, response, context, confidence_threshold
        )
        toxicity_result = self.evaluate_toxicity(response, confidence_threshold)
        rag_relevance_result = self.evaluate_rag_relevance(
            query, context, confidence_threshold
        )

        # Calculate summary
        successful_evaluations = sum(
            [
                hallucination_result["success"],
                toxicity_result["success"],
                rag_relevance_result["success"],
            ]
        )

        # Calculate overall score (average of successful evaluations)
        successful_scores = [
            result["score"]
            for result in [hallucination_result, toxicity_result, rag_relevance_result]
            if result["success"]
        ]
        overall_score = (
            sum(successful_scores) / len(successful_scores)
            if successful_scores
            else 0.0
        )

        evaluation_time = (datetime.now() - start_time).total_seconds()

        return {
            "hallucination": hallucination_result,
            "toxicity": toxicity_result,
            "rag_relevance": rag_relevance_result,
            "summary": {
                "overall_score": overall_score,
                "total_evaluations": 3,
                "successful_evaluations": successful_evaluations,
                "evaluation_time": evaluation_time,
                "model_id": self.model_id,
                "device": self.device,
            },
        }


def create_grounded_ai_evaluator(**kwargs) -> GroundedAIRAGEvaluator | None:
    """
    Factory function to create GroundedAI evaluator with error handling.

    Args:
        **kwargs: Arguments passed to GroundedAIRAGEvaluator constructor

    Returns:
        GroundedAIRAGEvaluator instance or None if unavailable
    """
    if not GROUNDED_AI_AVAILABLE:
        logger.warning(
            "GroundedAI not available. Install with: pip install 'lightrag-hku[evaluation]'"
        )
        return None

    try:
        return GroundedAIRAGEvaluator(**kwargs)
    except Exception as e:
        logger.error(f"Failed to create GroundedAI evaluator: {str(e)}")
        return None


# Export availability flag and main classes
__all__ = [
    "GroundedAIRAGEvaluator",
    "create_grounded_ai_evaluator",
    "GROUNDED_AI_AVAILABLE",
]
