#!/usr/bin/env python3
"""
RAGAS Evaluation Script for LightRAG System

Evaluates RAG response quality using RAGAS metrics:
- Faithfulness: Is the answer factually accurate based on context?
- Answer Relevance: Is the answer relevant to the question?
- Context Recall: Is all relevant information retrieved?
- Context Precision: Is retrieved context clean without noise?

Usage:
    # Use defaults (sample_dataset.json, http://localhost:9621)
    python lightrag/evaluation/eval_rag_quality.py

    # Specify custom dataset
    python lightrag/evaluation/eval_rag_quality.py --dataset my_test.json
    python lightrag/evaluation/eval_rag_quality.py -d my_test.json

    # Specify custom RAG endpoint
    python lightrag/evaluation/eval_rag_quality.py --ragendpoint http://my-server.com:9621
    python lightrag/evaluation/eval_rag_quality.py -r http://my-server.com:9621

    # Specify both
    python lightrag/evaluation/eval_rag_quality.py -d my_test.json -r http://localhost:9621

    # Get help
    python lightrag/evaluation/eval_rag_quality.py --help

Results are saved to: lightrag/evaluation/results/
    - results_YYYYMMDD_HHMMSS.csv   (CSV export for analysis)
    - results_YYYYMMDD_HHMMSS.json  (Full results with details)

Technical Notes:
    - Uses stable RAGAS API (LangchainLLMWrapper) for maximum compatibility
    - Supports custom OpenAI-compatible endpoints via EVAL_LLM_BINDING_HOST
    - Enables bypass_n mode for endpoints that don't support 'n' parameter
    - Deprecation warnings are suppressed for cleaner output
"""

import argparse
import asyncio
import csv
import json
import math
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from lightrag.utils import logger

# Suppress LangchainLLMWrapper deprecation warning
# We use LangchainLLMWrapper for stability and compatibility with all RAGAS versions
warnings.filterwarnings(
    "ignore",
    message=".*LangchainLLMWrapper is deprecated.*",
    category=DeprecationWarning,
)

# Suppress token usage warning for custom OpenAI-compatible endpoints
# Custom endpoints (vLLM, SGLang, etc.) often don't return usage information
# This is non-critical as token tracking is not required for RAGAS evaluation
warnings.filterwarnings(
    "ignore",
    message=".*Unexpected type for token usage.*",
    category=UserWarning,
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# use the .env that is inside the current folder
# allows to use different .env file for each lightrag instance
# the OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

# Conditional imports - will raise ImportError if dependencies not installed
try:
    from datasets import Dataset
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    from ragas import RunConfig, evaluate
    from ragas.llms import LangchainLLMWrapper

    # Updated to avoid deprecation warnings - importing from collections if available seems to be the suggestion,
    # but the warning said "ragas.metrics.collections". However, standard Ragas usage often simply uses ragas.metrics.
    # Let's try the specific import path mentioned in the warning or simply catch the warning.
    # Actually, Ragas 0.2+ changed structure. Let's try the direct import if that's what the warning suggested.
    # Warning: "Importing Faithfulness from 'ragas.metrics' is deprecated... use 'ragas.metrics.collections'".
    from ragas.metrics import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )
    from tqdm.auto import tqdm

    RAGAS_AVAILABLE = True

except ImportError:
    RAGAS_AVAILABLE = False
    Dataset = None
    evaluate = None
    LangchainLLMWrapper = None

# Import GroundedAI for SLM evaluation
try:
    from lightrag.evaluation.grounded_ai_backend import (
        GROUNDED_AI_AVAILABLE,
        GroundedAIRAGEvaluator,
    )
except ImportError:
    GROUNDED_AI_AVAILABLE = False
    GroundedAIRAGEvaluator = None


CONNECT_TIMEOUT_SECONDS = 1800.0
READ_TIMEOUT_SECONDS = 1800.0
TOTAL_TIMEOUT_SECONDS = 1800.0


def _is_nan(value: Any) -> bool:
    """Return True when value is a float NaN."""
    return isinstance(value, float) and math.isnan(value)


# Enhanced exception classes for better error classification and recovery
class RAGASTimeoutError(Exception):
    """RAGAS evaluation timed out but may succeed with longer timeout"""

    def __init__(self, message: str, timeout_value: float = None):
        super().__init__(message)
        self.timeout_value = timeout_value
        self.error_type = "TIMEOUT"


class RAGASBadRequestError(Exception):
    """API parameter incompatibility - typically fixable with parameter mapping"""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = "BAD_REQUEST"


class RAGASResourceError(Exception):
    """Local model or system overwhelmed - fixable with reduced concurrency or resource management"""

    def __init__(self, message: str, resource_type: str = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.error_type = "RESOURCE"


class RAGASCapacityError(Exception):
    """Model genuinely cannot perform evaluation task - expected for smaller models"""

    def __init__(self, message: str, metric_name: str = None):
        super().__init__(message)
        self.metric_name = metric_name
        self.error_type = "CAPACITY"


class RAGEvaluator:
    """Evaluate RAG system quality using RAGAS metrics and/or GroundedAI SLM evaluation"""

    def __init__(
        self,
        test_dataset_path: str = None,
        rag_api_url: str = None,
        use_grounded_ai: bool = False,
        grounded_ai_model: str = "grounded-ai/phi4-mini-judge",
        grounded_ai_device: str = None,
        grounded_ai_quantization: bool = False,
        hybrid_mode: bool = False,
    ):
        """
        Initialize evaluator with test dataset

        Args:
            test_dataset_path: Path to test dataset JSON file
            rag_api_url: Base URL of LightRAG API (e.g., http://localhost:9621)
                        If None, will try to read from environment or use default

        Environment Variables:
            EVAL_LLM_MODEL: LLM model for evaluation (default: gpt-4o-mini)
            EVAL_EMBEDDING_MODEL: Embedding model for evaluation (default: text-embedding-3-small)
            EVAL_LLM_BINDING_API_KEY: API key for LLM (fallback to OPENAI_API_KEY)
            EVAL_LLM_BINDING_HOST: Custom endpoint URL for LLM (optional)
            EVAL_EMBEDDING_BINDING_API_KEY: API key for embeddings (fallback: EVAL_LLM_BINDING_API_KEY -> OPENAI_API_KEY)
            EVAL_EMBEDDING_BINDING_HOST: Custom endpoint URL for embeddings (fallback: EVAL_LLM_BINDING_HOST)

        Raises:
            ImportError: If ragas or datasets packages are not installed
            EnvironmentError: If EVAL_LLM_BINDING_API_KEY and OPENAI_API_KEY are both not set
        """
        # Validate dependencies are installed
        if not use_grounded_ai and not hybrid_mode:
            # Pure RAGAS mode requires RAGAS dependencies
            if not RAGAS_AVAILABLE:
                raise ImportError(
                    "RAGAS dependencies not installed. "
                    "Install with: pip install ragas datasets"
                )
        elif hybrid_mode:
            # Hybrid mode requires both RAGAS and GroundedAI
            if not RAGAS_AVAILABLE:
                raise ImportError(
                    "Hybrid evaluation requires RAGAS dependencies. "
                    "Install with: pip install ragas datasets"
                )
            if not GROUNDED_AI_AVAILABLE:
                raise ImportError(
                    "Hybrid evaluation requires GroundedAI dependencies. "
                    "Install with: pip install grounded-ai[slm]"
                )

        # For pure GroundedAI mode, only check GroundedAI availability
        if use_grounded_ai and not hybrid_mode and not GROUNDED_AI_AVAILABLE:
            raise ImportError(
                "GroundedAI dependencies not installed. "
                "Install with: pip install grounded-ai[slm]"
            )

# Initialize configuration variables outside conditionals to ensure they're always available
        eval_model = os.getenv("EVAL_LLM_MODEL", "gpt-4o-mini")
        eval_llm_base_url = os.getenv("EVAL_LLM_BINDING_HOST")
        eval_embedding_model = os.getenv("EVAL_EMBEDDING_MODEL", "text-embedding-3-large")
        eval_embedding_base_url = os.getenv("EVAL_EMBEDDING_BINDING_HOST") or os.getenv("EVAL_LLM_BINDING_HOST")
        
        # Detect model characteristics for dynamic timeout scaling
        self.model_characteristics = self._detect_model_characteristics(eval_model)
        logger.debug(
            f"Detected model characteristics: {self.model_characteristics}"
        )

if not eval_llm_api_key:
                raise OSError(
                    "EVAL_LLM_BINDING_API_KEY or OPENAI_API_KEY is required for RAGAS evaluation. "
                    "Set EVAL_LLM_BINDING_API_KEY to use a custom API key, "
                    "or ensure OPENAI_API_KEY is set."
                )

            # Configure evaluation embeddings (for RAGAS scoring)
            # Fallback chain: EVAL_EMBEDDING_BINDING_API_KEY -> EVAL_LLM_BINDING_API_KEY -> OPENAI_API_KEY
            eval_embedding_api_key = (
                os.getenv("EVAL_EMBEDDING_BINDING_API_KEY")
                or os.getenv("EVAL_LLM_BINDING_API_KEY")
                or os.getenv("OPENAI_API_KEY")
            )

            # Apply dynamic timeout scaling based on model characteristics
            base_timeout = int(os.getenv("EVAL_LLM_TIMEOUT", "600"))
            model_base_timeout = self.model_characteristics["base_timeout"]

            # Use the larger of: user-specified timeout, model-appropriate timeout
            dynamic_timeout = max(base_timeout, model_base_timeout)

            logger.info(
                f"Dynamic timeout calculation: base={base_timeout}s, "
                f"model-appropriate={model_base_timeout}s, final={dynamic_timeout}s"
            )

            # Apply dynamic timeout scaling based on model characteristics
            base_timeout = int(os.getenv("EVAL_LLM_TIMEOUT", "600"))
            model_base_timeout = self.model_characteristics["base_timeout"]

            # Use the larger of: user-specified timeout, model-appropriate timeout
            dynamic_timeout = max(base_timeout, model_base_timeout)

            logger.info(
                f"Dynamic timeout calculation: base={base_timeout}s, "
                f"model-appropriate={model_base_timeout}s, final={dynamic_timeout}s"
            )

            # Create Ollama-compatible LLM configuration
            llm_kwargs = self._create_ollama_compatible_llm_config(
                eval_model, eval_llm_api_key, dynamic_timeout, eval_llm_base_url
            )
            embedding_kwargs = {
                "model": eval_embedding_model,
                "api_key": eval_embedding_api_key,
            }

            if eval_llm_base_url:
                llm_kwargs["base_url"] = eval_llm_base_url

            if eval_embedding_base_url:
                embedding_kwargs["base_url"] = eval_embedding_base_url

            # Create base LangChain LLM
            base_llm = ChatOpenAI(**llm_kwargs)

            # Configure evaluation embeddings (for RAGAS scoring)
            eval_embedding_binding = os.getenv("EVAL_EMBEDDING_BINDING")
            if eval_embedding_binding == "ollama":
                # Native Ollama embeddings
                self.eval_embeddings = OllamaEmbeddings(
                    model=eval_embedding_model,
                    base_url=eval_embedding_base_url,
                )
                logger.info("Using native OllamaEmbeddings for evaluation")
            else:
                # Default to OpenAIEmbeddings
                self.eval_embeddings = OpenAIEmbeddings(**embedding_kwargs)
                logger.info("Using OpenAIEmbeddings for evaluation")

            # Wrap LLM with LangchainLLMWrapper and enable bypass_n mode for custom endpoints
            # This ensures compatibility with endpoints that don't support 'n' parameter
            # by generating multiple outputs through repeated prompts instead of using 'n' parameter
            try:
                self.eval_llm = LangchainLLMWrapper(
                    langchain_llm=base_llm,
                    bypass_n=True,  # Enable bypass_n to avoid passing 'n' to OpenAI API
                )
                logger.debug("Successfully configured bypass_n mode for LLM wrapper")
            except Exception as e:
                logger.warning(
                    "Could not configure LangchainLLMWrapper with bypass_n: %s. "
                    "Using base LLM directly, which may cause warnings with custom endpoints.",
                    e,
                )
                self.eval_llm = base_llm
        else:
            # GroundedAI-only mode: set placeholders and ensure variables are still defined
            self.eval_llm = None
            self.eval_embeddings = None
            # Initialize embedding variables even in GroundedAI mode for consistency
            eval_embedding_model = os.getenv(
                "EVAL_EMBEDDING_MODEL", "text-embedding-3-large"
            )
            eval_embedding_base_url = os.getenv(
                "EVAL_EMBEDDING_BINDING_HOST"
            ) or os.getenv("EVAL_LLM_BINDING_HOST")

        if test_dataset_path is None:
            test_dataset_path = Path(__file__).parent / "sample_dataset.json"

        if rag_api_url is None:
            rag_api_url = os.getenv("LIGHTRAG_API_URL", "http://localhost:9621")

        self.test_dataset_path = Path(test_dataset_path)
        self.rag_api_url = rag_api_url.rstrip("/")
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Load test dataset
        self.test_cases = self._load_test_dataset()

        # Store configuration values for display
        self.eval_model = eval_model
        self.eval_embedding_model = eval_embedding_model
        self.eval_llm_base_url = eval_llm_base_url
        self.eval_embedding_base_url = eval_embedding_base_url

        # Get LLM configuration values with defaults for GroundedAI-only mode
        if "llm_kwargs" in locals():
            self.eval_max_retries = llm_kwargs.get("max_retries", 5)
            self.eval_timeout = llm_kwargs.get("request_timeout", 600)
        else:
            # Default values for GroundedAI-only mode
            self.eval_max_retries = 5
            self.eval_timeout = 600

        # GroundedAI configuration
        self.use_grounded_ai = use_grounded_ai
        self.grounded_ai_model = grounded_ai_model
        self.grounded_ai_device = grounded_ai_device
        self.grounded_ai_quantization = grounded_ai_quantization
        self.hybrid_mode = hybrid_mode

        # Initialize GroundedAI evaluator if requested
        self.grounded_ai_evaluator = None
        if use_grounded_ai or hybrid_mode:
            try:
                self.grounded_ai_evaluator = GroundedAIRAGEvaluator(
                    model_id=grounded_ai_model,
                    device=grounded_ai_device,
                    quantization=grounded_ai_quantization,
                    timeout=self.eval_timeout,
                )
                logger.info("GroundedAI evaluator initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize GroundedAI evaluator: %s", str(e))
                if use_grounded_ai and not hybrid_mode:
                    # If pure GroundedAI mode fails, we can't proceed
                    raise
                else:
                    # For hybrid mode, we can continue with just RAGAS
                    logger.warning("Continuing with RAGAS evaluation only")

        # Display configuration
        self._display_configuration()

    def _display_configuration(self):
        """Display all evaluation configuration settings"""
        logger.info("Evaluation Models:")
        logger.info("  • LLM Model:            %s", self.eval_model)
        logger.info("  • Embedding Model:      %s", self.eval_embedding_model)

        # Display LLM endpoint
        if self.eval_llm_base_url:
            logger.info("  • LLM Endpoint:         %s", self.eval_llm_base_url)
            logger.info(
                "  • Bypass N-Parameter:   Enabled (use LangchainLLMWrapper for compatibility)"
            )
        else:
            logger.info("  • LLM Endpoint:         OpenAI Official API")

        # Display Embedding endpoint (only if different from LLM)
        if self.eval_embedding_base_url:
            if self.eval_embedding_base_url != self.eval_llm_base_url:
                logger.info(
                    "  • Embedding Endpoint:   %s", self.eval_embedding_base_url
                )
            # If same as LLM endpoint, no need to display separately
        elif not self.eval_llm_base_url:
            # Both using OpenAI - already displayed above
            pass
        else:
            # LLM uses custom endpoint, but embeddings use OpenAI
            logger.info("  • Embedding Endpoint:   OpenAI Official API")

        logger.info("Concurrency & Rate Limiting:")
        query_top_k = int(os.getenv("EVAL_QUERY_TOP_K", "10"))
        logger.info("  • Query Top-K:          %s Entities/Relations", query_top_k)
        logger.info("  • LLM Max Retries:      %s", self.eval_max_retries)
        logger.info("  • LLM Timeout:          %s seconds", self.eval_timeout)

        logger.info("Test Configuration:")
        logger.info("  • Total Test Cases:     %s", len(self.test_cases))
        logger.info("  • Test Dataset:         %s", self.test_dataset_path.name)
        logger.info("  • LightRAG API:         %s", self.rag_api_url)
        logger.info("  • Results Directory:    %s", self.results_dir.name)

    def _load_test_dataset(self) -> list[dict[str, str]]:
        """Load test cases from JSON file"""
        if not self.test_dataset_path.exists():
            raise FileNotFoundError(f"Test dataset not found: {self.test_dataset_path}")

        with open(self.test_dataset_path) as f:
            data = json.load(f)

        return data.get("test_cases", [])

    def _detect_model_characteristics(self, model_name: str) -> dict:
        """
        Detect model size and characteristics from model name for dynamic configuration.

        Args:
            model_name: Model name from environment variable

        Returns:
            Dictionary with model characteristics for timeout and concurrency scaling
        """
        model_lower = model_name.lower()

        # Parse model size from common naming patterns
        if "0.5b" in model_lower or "500m" in model_lower or "0.5b" in model_lower:
            return {
                "size_category": "tiny",
                "base_timeout": 900,  # 15 minutes for very small models
                "max_concurrent": 1,  # Strictly serial
                "description": "Very small model (~0.5B parameters)",
            }
        elif "1b" in model_lower or "1.5b" in model_lower or "1.8b" in model_lower:
            return {
                "size_category": "small",
                "base_timeout": 1200,  # 20 minutes for small models
                "max_concurrent": 1,  # Serial evaluation
                "description": "Small model (1-2B parameters)",
            }
        elif "3b" in model_lower or "2.5b" in model_lower or "2b" in model_lower:
            return {
                "size_category": "medium",
                "base_timeout": 900,  # 15 minutes for medium models
                "max_concurrent": 1,  # Conservative serial
                "description": "Medium model (2-4B parameters)",
            }
        elif "7b" in model_lower or "8b" in model_lower or "6b" in model_lower:
            return {
                "size_category": "large",
                "base_timeout": 600,  # 10 minutes for large models
                "max_concurrent": 2,  # Limited parallelism
                "description": "Large model (6-8B parameters)",
            }
        elif "13b" in model_lower or "14b" in model_lower or "12b" in model_lower:
            return {
                "size_category": "xlarge",
                "base_timeout": 450,  # 7.5 minutes for very large models
                "max_concurrent": 2,  # Limited parallelism
                "description": "Very large model (12-14B parameters)",
            }
        elif "gpt-4" in model_lower or "claude-3" in model_lower:
            return {
                "size_category": "enterprise",
                "base_timeout": 300,  # 5 minutes for enterprise models
                "max_concurrent": 3,  # Higher parallelism for cloud APIs
                "description": "Enterprise cloud model",
            }
        elif "gpt-3.5" in model_lower or "mixtral" in model_lower:
            return {
                "size_category": "standard",
                "base_timeout": 450,  # 7.5 minutes for standard models
                "max_concurrent": 2,  # Moderate parallelism
                "description": "Standard cloud model",
            }
        else:
            # Default for unknown models
            return {
                "size_category": "unknown",
                "base_timeout": 900,  # Conservative 15 minutes
                "max_concurrent": 1,  # Conservative serial evaluation
                "description": f"Unknown model: {model_name}",
            }

    def _calculate_optimal_concurrency(self, user_requested: int) -> int:
        """
        Calculate safe concurrency based on model characteristics and user preferences.

        Args:
            user_requested: User-specified maximum concurrency from environment

        Returns:
            Optimal concurrency value considering resource constraints
        """
        model_limit = self.model_characteristics["max_concurrent"]
        model_category = self.model_characteristics["size_category"]

        # Start with model-specific limit
        optimal_concurrency = model_limit

        # Additional constraints based on evaluation type and resources
        if self.grounded_ai_evaluator and self.hybrid_mode:
            # Hybrid mode (RAGAS + GroundedAI) is more resource intensive
            optimal_concurrency = min(optimal_concurrency, 1)
            logger.debug(
                "Hybrid evaluation mode: forcing serial evaluation for resource management"
            )

        # Override with user request if it's lower (user wants to be more conservative)
        if user_requested < optimal_concurrency:
            optimal_concurrency = user_requested
            logger.debug(f"User requested lower concurrency: {user_requested}")

        # Final safety constraints
        if model_category in ["tiny", "small"]:
            # Very small models should always use serial evaluation
            optimal_concurrency = 1
        elif model_category == "medium":
            # Medium models should be conservative
            optimal_concurrency = min(optimal_concurrency, 1)

        logger.debug(
            f"Concurrency calculation: user={user_requested}, model_limit={model_limit}, "
            f"optimal={optimal_concurrency}"
        )

        return max(1, optimal_concurrency)  # Ensure at least 1

    def _create_ollama_compatible_llm_config(
        self, model_name: str, api_key: str, timeout: int, base_url: str | None = None
    ) -> dict:
        """
        Create LLM configuration with enhanced Ollama compatibility.

        Args:
            model_name: Model name for evaluation
            api_key: API key (for Ollama this is typically "ollama")
            timeout: Request timeout in seconds
            base_url: Custom endpoint URL

        Returns:
            Dictionary with LLM configuration parameters
        """
        # Base configuration
        llm_kwargs = {
            "model": model_name,
            "api_key": api_key,
            "max_retries": int(os.getenv("EVAL_LLM_MAX_RETRIES", "5")),
            "request_timeout": timeout,
        }

        if base_url:
            llm_kwargs["base_url"] = base_url

        # Ollama-specific parameter optimization
        if base_url and ("11434" in base_url or "ollama" in base_url.lower()):
            logger.debug("Applying Ollama-specific configuration optimizations")

            # Ollama has different parameter requirements than OpenAI API
            llm_kwargs.update(
                {
                    "temperature": 0.1,  # Lower temperature for more consistent evaluation
                    "top_p": 0.9,  # Reasonable default for Ollama
                    # Note: max_tokens is not supported by Ollama, will be filtered out by Ollama client
                    # Note: response_format is partially supported but disabled for compatibility
                }
            )

            # Adjust timeouts specifically for Ollama (often slower than cloud APIs)
            model_category = self.model_characteristics["size_category"]
            if model_category in ["tiny", "small", "medium"]:
                # Give small local models extra time for complex evaluation tasks
                llm_kwargs["request_timeout"] = timeout * 1.5
                logger.debug(
                    f"Extended timeout for small Ollama model: {llm_kwargs['request_timeout']}s"
                )

            # Reduce max_retries for local models to avoid long retry cycles
            if model_category in ["tiny", "small"]:
                llm_kwargs["max_retries"] = min(llm_kwargs["max_retries"], 3)
                logger.debug(
                    f"Reduced max_retries for small Ollama model: {llm_kwargs['max_retries']}"
                )

        return llm_kwargs

    async def _evaluate_with_retry(
        self, idx: int, eval_dataset, max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Run RAGAS evaluation with exponential backoff retry logic.

        Args:
            idx: Test case index for logging
            eval_dataset: Dataset to evaluate
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with metrics and ragas_score, or error information
        """
        for attempt in range(max_retries):
            try:
                return await self._run_single_ragas_evaluation(idx, eval_dataset)

            except (RAGASTimeoutError, httpx.ReadTimeout) as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 5s, 10s, 20s
                    backoff_delay = 5 * (2**attempt)
                    extended_timeout = self.eval_timeout * (2**attempt)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries}: RAGAS timeout for test {idx}, "
                        f"retrying in {backoff_delay}s with {extended_timeout}s timeout"
                    )
                    await asyncio.sleep(backoff_delay)

                    # Temporarily extend timeout for retry
                    original_timeout = self.eval_timeout
                    self.eval_timeout = int(extended_timeout)
                    try:
                        result = await self._run_single_ragas_evaluation(
                            idx, eval_dataset
                        )
                        # Restore original timeout
                        self.eval_timeout = original_timeout
                        return result
                    except Exception:
                        # Restore original timeout even if retry fails
                        self.eval_timeout = original_timeout
                        raise
                else:
                    logger.error(
                        f"RAGAS evaluation failed after {max_retries} timeout attempts for test {idx}: {str(e)}"
                    )
                    return {
                        "metrics": {},
                        "ragas_score": 0,
                        "error": "TIMEOUT",
                        "error_details": str(e),
                        "retry_attempts": max_retries,
                    }

            except RAGASBadRequestError as e:
                # Don't retry bad requests - they'll fail the same way
                logger.error(
                    f"RAGAS evaluation failed due to parameter issues for test {idx}: {str(e)}"
                )
                return {
                    "metrics": {},
                    "ragas_score": 0,
                    "error": "BAD_REQUEST",
                    "error_details": str(e),
                    "retry_attempts": attempt + 1,
                }

            except RAGASResourceError as e:
                if attempt < max_retries - 1:
                    # Progressive backoff for resource issues: 10s, 20s, 30s
                    backoff_delay = 10 * (attempt + 1)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries}: Resource overload for test {idx}, "
                        f"pausing {backoff_delay}s before retry"
                    )
                    await asyncio.sleep(backoff_delay)
                    continue
                else:
                    logger.error(
                        f"RAGAS evaluation failed due to resource constraints for test {idx}: {str(e)}"
                    )
                    return {
                        "metrics": {},
                        "ragas_score": 0,
                        "error": "RESOURCE",
                        "error_details": str(e),
                        "retry_attempts": max_retries,
                    }

            except Exception as e:
                # Classify generic exceptions based on error message patterns
                error_msg = str(e).lower()
                if "timeout" in error_msg or "timed out" in error_msg:
                    if attempt < max_retries - 1:
                        backoff_delay = 5 * (2**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries}: Timeout detected for test {idx}, "
                            f"retrying in {backoff_delay}s"
                        )
                        await asyncio.sleep(backoff_delay)
                        continue
                    else:
                        return {
                            "metrics": {},
                            "ragas_score": 0,
                            "error": "TIMEOUT",
                            "error_details": str(e),
                            "retry_attempts": max_retries,
                        }
                elif (
                    "invalid input type" in error_msg
                    or "parameter" in error_msg
                    or "400" in error_msg
                ):
                    logger.error(
                        f"RAGAS evaluation failed due to parameter issues for test {idx}: {str(e)}"
                    )
                    return {
                        "metrics": {},
                        "ragas_score": 0,
                        "error": "BAD_REQUEST",
                        "error_details": str(e),
                        "retry_attempts": attempt + 1,
                    }
                elif (
                    "capacity" in error_msg
                    or "overload" in error_msg
                    or "429" in error_msg
                ):
                    if attempt < max_retries - 1:
                        backoff_delay = 10 * (attempt + 1)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries}: Resource issue for test {idx}, "
                            f"retrying in {backoff_delay}s"
                        )
                        await asyncio.sleep(backoff_delay)
                        continue
                    else:
                        return {
                            "metrics": {},
                            "ragas_score": 0,
                            "error": "RESOURCE",
                            "error_details": str(e),
                            "retry_attempts": max_retries,
                        }
                else:
                    # Unknown error - don't classify, just log and fail
                    logger.error(
                        f"RAGAS evaluation failed with unknown error for test {idx}: {str(e)}"
                    )
                    return {
                        "metrics": {},
                        "ragas_score": 0,
                        "error": "UNKNOWN",
                        "error_details": str(e),
                        "retry_attempts": attempt + 1,
                    }

    async def _run_single_ragas_evaluation(
        self, idx: int, eval_dataset
    ) -> dict[str, Any]:
        """
        Run a single RAGAS evaluation without retry logic.

        Args:
            idx: Test case index for logging
            eval_dataset: Dataset to evaluate

        Returns:
            Dictionary with metrics and ragas_score

        Raises:
            Various exceptions based on error type
        """
        callbacks = []
        if os.getenv("LANGFUSE_ENABLE_TRACE", "false").lower() == "true":
            try:
                langfuse_handler = LangfuseCallbackHandler()
                callbacks.append(langfuse_handler)
            except Exception as e:
                logger.warning("Failed to initialize Langfuse callback: %s", e)

        # Classify potential errors before calling evaluate
        try:
            eval_results = evaluate(
                dataset=eval_dataset,
                metrics=[
                    Faithfulness(),
                    AnswerRelevancy(),
                    ContextRecall(),
                    ContextPrecision(),
                ],
                llm=self.eval_llm,
                embeddings=self.eval_embeddings,
                run_config=RunConfig(timeout=self.eval_timeout, max_workers=1),
                callbacks=callbacks,
            )
        except httpx.ReadTimeout as e:
            raise RAGASTimeoutError(
                f"RAGAS evaluation timed out after {self.eval_timeout}s: {str(e)}",
                timeout_value=self.eval_timeout,
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise RAGASBadRequestError(
                    f"RAGAS evaluation failed due to bad request: {e.response.text}",
                    status_code=e.response.status_code,
                ) from e
            elif e.response.status_code == 429:
                raise RAGASResourceError(
                    f"RAGAS evaluation failed due to rate limiting: {e.response.text}",
                    resource_type="rate_limit",
                ) from e
            else:
                raise  # Re-raise other HTTP errors as-is
        except Exception as e:
            # Classify based on error message patterns
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                raise RAGASTimeoutError(f"RAGAS timeout detected: {str(e)}") from e
            elif (
                "invalid input type" in error_msg
                or "parameter" in error_msg
                or "schema" in error_msg
            ):
                raise RAGASBadRequestError(
                    f"RAGAS parameter validation failed: {str(e)}"
                ) from e
            elif (
                "capacity" in error_msg
                or "overload" in error_msg
                or "memory" in error_msg
            ):
                raise RAGASResourceError(
                    f"RAGAS resource constraint: {str(e)}", resource_type="system"
                ) from e
            else:
                raise  # Re-raise unknown errors

        # Convert to DataFrame (RAGAS v0.3+ API)
        df = eval_results.to_pandas()

        # Extract scores from first row
        scores_row = df.iloc[0]

        # Extract RAGAS scores
        metrics = {
            "faithfulness": float(scores_row.get("faithfulness", 0)),
            "answer_relevance": float(scores_row.get("answer_relevancy", 0)),
            "context_recall": float(scores_row.get("context_recall", 0)),
            "context_precision": float(scores_row.get("context_precision", 0)),
        }

        # Calculate RAGAS score (average of all metrics, excluding NaN values)
        valid_metrics = [v for v in metrics.values() if not _is_nan(v)]
        ragas_score = sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0

        return {"metrics": metrics, "ragas_score": round(ragas_score, 4)}

    async def generate_rag_response(
        self,
        question: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        """
        Generate RAG response by calling LightRAG API.

        Args:
            question: The user query.
            client: Shared httpx AsyncClient for connection pooling.

        Returns:
            Dictionary with 'answer' and 'contexts' keys.
            'contexts' is a list of strings (one per retrieved document).

        Raises:
            Exception: If LightRAG API is unavailable.
        """
        try:
            payload = {
                "query": question,
                "mode": "mix",
                "include_references": True,
                "include_chunk_content": True,  # NEW: Request chunk content in references
                "response_type": "Multiple Paragraphs",
                "top_k": int(os.getenv("EVAL_QUERY_TOP_K", "10")),
                # Explicitly disable rerank by default to avoid server warnings
                # Can be enabled via env var if a reranker is actually configured
                "enable_rerank": os.environ.get("EVAL_ENABLE_RERANK", "true").lower()
                == "true",
                "rerank_entities": os.environ.get(
                    "EVAL_RERANK_ENTITIES", "true"
                ).lower()
                == "true",
                "rerank_relations": os.environ.get(
                    "EVAL_RERANK_RELATIONS", "true"
                ).lower()
                == "true",
            }

            # Get API key from environment for authentication
            api_key = os.getenv("LIGHTRAG_API_KEY")

            # Prepare headers with optional authentication
            headers = {}
            if api_key:
                headers["X-API-Key"] = api_key

            # Single optimized API call - gets both answer AND chunk content
            response = await client.post(
                f"{self.rag_api_url}/query",
                json=payload,
                headers=headers if headers else None,
            )
            response.raise_for_status()
            result = response.json()

            answer = result.get("response", "No response generated")
            references = result.get("references", [])

            # DEBUG: Inspect the API response
            logger.debug("🔍 References Count: %s", len(references))
            if references:
                first_ref = references[0]
                logger.debug("🔍 First Reference Keys: %s", list(first_ref.keys()))
                if "content" in first_ref:
                    content_preview = first_ref["content"]
                    if isinstance(content_preview, list) and content_preview:
                        logger.debug(
                            "🔍 Content Preview (first chunk): %s...",
                            content_preview[0][:100],
                        )
                    elif isinstance(content_preview, str):
                        logger.debug("🔍 Content Preview: %s...", content_preview[:100])

            # Extract chunk content from enriched references
            # Note: content is now a list of chunks per reference (one file may have multiple chunks)
            contexts = []
            for ref in references:
                content = ref.get("content", [])
                if isinstance(content, list):
                    # Flatten the list: each chunk becomes a separate context
                    contexts.extend(content)
                elif isinstance(content, str):
                    # Backward compatibility: if content is still a string (shouldn't happen)
                    contexts.append(content)

            return {
                "answer": answer,
                "contexts": contexts,  # List of strings from actual retrieved chunks
            }

        except httpx.ConnectError as e:
            raise Exception(
                f"❌ Cannot connect to LightRAG API at {self.rag_api_url}\n"
                f"   Make sure LightRAG server is running:\n"
                f"   python -m lightrag.api.lightrag_server\n"
                f"   Error: {str(e)}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"LightRAG API error {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.ReadTimeout as e:
            raise Exception(
                f"Request timeout after waiting for response\n"
                f"   Question: {question[:100]}...\n"
                f"   Error: {str(e)}"
            ) from e
        except Exception as e:
            raise Exception(
                f"Error calling LightRAG API: {type(e).__name__}: {str(e)}"
            ) from e

    async def evaluate_single_case(
        self,
        idx: int,
        test_case: dict[str, str],
        rag_semaphore: asyncio.Semaphore,
        eval_semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        progress_counter: dict[str, int],
        position_pool: asyncio.Queue,
        pbar_creation_lock: asyncio.Lock,
    ) -> dict[str, Any]:
        """
        Evaluate a single test case with two-stage pipeline concurrency control

        Args:
            idx: Test case index (1-based)
            test_case: Test case dictionary with question and ground_truth
            rag_semaphore: Semaphore to control overall concurrency (covers entire function)
            eval_semaphore: Semaphore to control RAGAS evaluation concurrency (Stage 2)
            client: Shared httpx AsyncClient for connection pooling
            progress_counter: Shared dictionary for progress tracking
            position_pool: Queue of available tqdm position indices
            pbar_creation_lock: Lock to serialize tqdm creation and prevent race conditions

        Returns:
            Evaluation result dictionary
        """
        # rag_semaphore controls the entire evaluation process to prevent
        # all RAG responses from being generated at once when eval is slow
        async with rag_semaphore:
            question = test_case["question"]
            ground_truth = test_case["ground_truth"]

            # Stage 1: Generate RAG response
            try:
                rag_response = await self.generate_rag_response(
                    question=question, client=client
                )
            except Exception as e:
                logger.error("Error generating response for test %s: %s", idx, str(e))
                progress_counter["completed"] += 1
                return {
                    "test_number": idx,
                    "question": question,
                    "error": str(e),
                    "metrics": {},
                    "ragas_score": 0,
                    "timestamp": datetime.now().isoformat(),
                }

            # *** CRITICAL FIX: Use actual retrieved contexts, NOT ground_truth ***
            retrieved_contexts = rag_response["contexts"]

            # Initialize result with basic information and enhanced metadata
            evaluation_start_time = time.time()
            result = {
                "test_number": idx,
                "question": question,
                "answer": rag_response["answer"][:200] + "..."
                if len(rag_response["answer"]) > 200
                else rag_response["answer"],
                "ground_truth": ground_truth[:200] + "..."
                if len(ground_truth) > 200
                else ground_truth,
                "project": test_case.get("project", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "evaluation_metadata": {
                    "model_characteristics": self.model_characteristics,
                    "timeout_used": self.eval_timeout,
                    "model_name": self.eval_model,
                    "embedding_model": self.eval_embedding_model,
                    "is_ollama": self.eval_llm_base_url
                    and (
                        "11434" in self.eval_llm_base_url
                        or "ollama" in self.eval_llm_base_url.lower()
                    ),
                    "evaluation_start_time": evaluation_start_time,
                    "optimization_applied": "dynamic_timeout_and_retry",
                    "completion_status": "in_progress",  # Will be updated later
                    "metrics_completed": [],  # Will be populated later
                    "metrics_failed": [],  # Will be populated later
                    "retry_attempts": 0,  # Will be updated by retry logic
                },
            }

            # Run RAGAS evaluation if available
            if self.eval_llm and self.eval_embeddings:
                # Prepare dataset for RAGAS evaluation with CORRECT contexts
                eval_dataset = Dataset.from_dict(
                    {
                        "question": [question],
                        "answer": [rag_response["answer"]],
                        "contexts": [retrieved_contexts],
                        "ground_truth": [ground_truth],
                    }
                )

                # Stage 2: Run RAGAS evaluation with retry logic (controlled by eval_semaphore)
                # IMPORTANT: Create fresh metric instances for each evaluation to avoid
                # concurrent state conflicts when multiple tasks run in parallel
                async with eval_semaphore:
                    pbar = None
                    position = None
                    try:
                        # Acquire a position from the pool for this tqdm progress bar
                        position = await position_pool.get()

                        # Serialize tqdm creation to prevent race conditions
                        # Multiple tasks creating tqdm simultaneously can cause display conflicts
                        async with pbar_creation_lock:
                            # Create tqdm progress bar with assigned position to avoid overlapping
                            # leave=False ensures the progress bar is cleared after completion,
                            # preventing accumulation of completed bars and allowing position reuse
                            pbar = tqdm(
                                total=4,
                                desc=f"Eval-{idx:02d}",
                                position=position,
                                leave=False,
                            )
                            # Give tqdm time to initialize and claim its screen position
                            await asyncio.sleep(0.05)

                        # Add progress bar to the evaluation method for compatibility
                        # This maintains the existing progress display behavior
                        original_evaluate = self._run_single_ragas_evaluation

                        async def evaluate_with_pbar(idx, eval_dataset):
                            result = await original_evaluate(idx, eval_dataset)
                            # Update progress bar after successful evaluation
                            if pbar:
                                pbar.update(4)  # All 4 metrics completed
                            return result

                        # Run evaluation with retry logic
                        eval_result = await self._evaluate_with_retry(idx, eval_dataset)

                        # Extract results from retry logic and update metadata
                        if "error" in eval_result:
                            # Evaluation failed - log and set defaults
                            error_type = eval_result.get("error", "UNKNOWN")
                            logger.error(
                                f"RAGAS evaluation failed for test {idx} with {error_type}: {eval_result.get('error_details', 'Unknown error')}"
                            )
                            result["metrics"] = {}
                            result["ragas_score"] = 0
                            result["evaluation_error"] = eval_result

                            # Update evaluation metadata
                            result["evaluation_metadata"]["completion_status"] = (
                                "failed"
                            )
                            result["evaluation_metadata"]["retry_attempts"] = (
                                eval_result.get("retry_attempts", 0)
                            )
                        else:
                            # Evaluation succeeded - extract metrics and update metadata
                            result["metrics"] = eval_result["metrics"]
                            result["ragas_score"] = eval_result["ragas_score"]

                            # Update evaluation metadata
                            result["evaluation_metadata"]["completion_status"] = (
                                "completed"
                            )
                            result["evaluation_metadata"]["metrics_completed"] = list(
                                eval_result["metrics"].keys()
                            )
                            result["evaluation_metadata"]["retry_attempts"] = (
                                eval_result.get("retry_attempts", 0)
                            )

                        # Update evaluation duration
                        result["evaluation_metadata"]["evaluation_duration"] = (
                            time.time()
                            - result["evaluation_metadata"]["evaluation_start_time"]
                        )

                    finally:
                        # Force close progress bar to ensure completion
                        if pbar is not None:
                            pbar.close()
                        # Release the position back to the pool for reuse
                        if position is not None:
                            await position_pool.put(position)

            # Run GroundedAI evaluation if available
            if self.grounded_ai_evaluator:
                try:
                    # Combine retrieved contexts for GroundedAI evaluation
                    combined_context = " ".join(retrieved_contexts)

                    grounded_ai_result = (
                        self.grounded_ai_evaluator.evaluate_comprehensive(
                            query=question,
                            response=rag_response["answer"],
                            context=combined_context,
                        )
                    )

                    result["grounded_ai"] = grounded_ai_result

                    # Add GroundedAI summary for comparison
                    if "summary" in grounded_ai_result:
                        ga_summary = grounded_ai_result["summary"]
                        result["grounded_ai_summary"] = {
                            "overall_score": ga_summary.get("overall_score", 0.0),
                            "evaluation_time": ga_summary.get("evaluation_time", 0.0),
                            "successful_evaluations": ga_summary.get(
                                "successful_evaluations", 0
                            ),
                            "model_id": ga_summary.get("model_id", "unknown"),
                        }

                        logger.info(
                            "GroundedAI scores - Hallucination: %.2f, Toxicity: %.2f, RAG Relevance: %.2f",
                            grounded_ai_result.get("hallucination", {}).get(
                                "score", 0.0
                            ),
                            grounded_ai_result.get("toxicity", {}).get("score", 0.0),
                            grounded_ai_result.get("rag_relevance", {}).get(
                                "score", 0.0
                            ),
                        )

                except Exception as e:
                    logger.error("GroundedAI evaluation failed: %s", str(e))
                    result["grounded_ai"] = {"error": str(e)}

            # Update progress counter
            progress_counter["completed"] += 1

            return result

    async def evaluate_responses(self) -> list[dict[str, Any]]:
        """
        Evaluate all test cases in parallel with two-stage pipeline and return metrics

        Returns:
            List of evaluation results with metrics
        """
        # Calculate optimal concurrency based on model characteristics
        user_max_async = int(os.getenv("EVAL_MAX_CONCURRENT", "2"))
        optimal_concurrency = self._calculate_optimal_concurrency(user_max_async)

        logger.info("%s", "=" * 70)
        logger.info("🚀 Starting RAGAS Evaluation of LightRAG System")
        logger.info(
            f"🔧 Model Characteristics: {self.model_characteristics['description']}"
        )
        logger.info(
            f"🔧 Resource-Aware Concurrency: {optimal_concurrency} (requested: {user_max_async})"
        )
        logger.info("%s", "=" * 70)

        # Create two-stage pipeline semaphores with resource-aware limits
        # Stage 1: RAG generation - allow x2 concurrency to keep evaluation fed
        rag_semaphore = asyncio.Semaphore(optimal_concurrency * 2)
        # Stage 2: RAGAS evaluation - primary bottleneck
        eval_semaphore = asyncio.Semaphore(optimal_concurrency)

        # Create progress counter (shared across all tasks)
        progress_counter = {"completed": 0}

        # Create position pool for tqdm progress bars
        # Positions range from 0 to max_async-1, ensuring no overlapping displays
        position_pool = asyncio.Queue()
        for i in range(max_async):
            await position_pool.put(i)

        # Create lock to serialize tqdm creation and prevent race conditions
        # This ensures progress bars are created one at a time, avoiding display conflicts
        pbar_creation_lock = asyncio.Lock()

        # Create shared HTTP client with connection pooling and proper timeouts
        # Timeout: 3 minutes for connect, 5 minutes for read (LLM can be slow)
        timeout = httpx.Timeout(
            TOTAL_TIMEOUT_SECONDS,
            connect=CONNECT_TIMEOUT_SECONDS,
            read=READ_TIMEOUT_SECONDS,
        )
        limits = httpx.Limits(
            max_connections=(max_async + 1) * 2,  # Allow buffer for RAG stage
            max_keepalive_connections=max_async + 1,
        )

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            # Create tasks for all test cases
            tasks = [
                self.evaluate_single_case(
                    idx,
                    test_case,
                    rag_semaphore,
                    eval_semaphore,
                    client,
                    progress_counter,
                    position_pool,
                    pbar_creation_lock,
                )
                for idx, test_case in enumerate(self.test_cases, 1)
            ]

            # Run all evaluations in parallel (limited by two-stage semaphores)
            results = await asyncio.gather(*tasks)

        return list(results)

    def _export_to_csv(self, results: list[dict[str, Any]]) -> Path:
        """
        Export evaluation results to CSV file

        Args:
            results: List of evaluation results

        Returns:
            Path to the CSV file

        CSV Format:
            - question: The test question
            - project: Project context
            - faithfulness: Faithfulness score (0-1)
            - answer_relevance: Answer relevance score (0-1)
            - context_recall: Context recall score (0-1)
            - context_precision: Context precision score (0-1)
            - ragas_score: Overall RAGAS score (0-1)
            - timestamp: When evaluation was run
        """
        csv_path = (
            self.results_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "test_number",
                "question",
                "project",
                "faithfulness",
                "answer_relevance",
                "context_recall",
                "context_precision",
                "ragas_score",
                "status",
                "timestamp",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for idx, result in enumerate(results, 1):
                metrics = result.get("metrics", {})
                writer.writerow(
                    {
                        "test_number": idx,
                        "question": result.get("question", ""),
                        "project": result.get("project", "unknown"),
                        "faithfulness": f"{metrics.get('faithfulness', 0):.4f}",
                        "answer_relevance": f"{metrics.get('answer_relevance', 0):.4f}",
                        "context_recall": f"{metrics.get('context_recall', 0):.4f}",
                        "context_precision": f"{metrics.get('context_precision', 0):.4f}",
                        "ragas_score": f"{result.get('ragas_score', 0):.4f}",
                        "status": "success" if metrics else "error",
                        "timestamp": result.get("timestamp", ""),
                    }
                )

        return csv_path

    def _format_metric(self, value: float, width: int = 6) -> str:
        """
        Format a metric value for display, handling NaN gracefully

        Args:
            value: The metric value to format
            width: The width of the formatted string

        Returns:
            Formatted string (e.g., "0.8523" or "  N/A ")
        """
        if _is_nan(value):
            return "N/A".center(width)
        return f"{value:.4f}".rjust(width)

    def _display_results_table(self, results: list[dict[str, Any]]):
        """
        Display evaluation results in a formatted table

        Args:
            results: List of evaluation results
        """
        logger.info("")
        logger.info("%s", "=" * 115)
        logger.info("📊 EVALUATION RESULTS SUMMARY")
        logger.info("%s", "=" * 115)

        # Table header
        logger.info(
            "%-4s | %-50s | %6s | %7s | %6s | %7s | %6s | %6s",
            "#",
            "Question",
            "Faith",
            "AnswRel",
            "CtxRec",
            "CtxPrec",
            "RAGAS",
            "Status",
        )
        logger.info("%s", "-" * 115)

        # Table rows
        for result in results:
            test_num = result.get("test_number", 0)
            question = result.get("question", "")
            # Truncate question to 50 chars
            question_display = (
                (question[:47] + "...") if len(question) > 50 else question
            )

            metrics = result.get("metrics", {})
            if metrics:
                # Success case - format each metric, handling NaN values
                faith = metrics.get("faithfulness", 0)
                ans_rel = metrics.get("answer_relevance", 0)
                ctx_rec = metrics.get("context_recall", 0)
                ctx_prec = metrics.get("context_precision", 0)
                ragas = result.get("ragas_score", 0)
                status = "✓"

                logger.info(
                    "%-4d | %-50s | %s | %s | %s | %s | %s | %6s",
                    test_num,
                    question_display,
                    self._format_metric(faith, 6),
                    self._format_metric(ans_rel, 7),
                    self._format_metric(ctx_rec, 6),
                    self._format_metric(ctx_prec, 7),
                    self._format_metric(ragas, 6),
                    status,
                )
            else:
                # Error case
                error = result.get("error", "Unknown error")
                error_display = (error[:20] + "...") if len(error) > 23 else error
                logger.info(
                    "%-4d | %-50s | %6s | %7s | %6s | %7s | %6s | ✗ %s",
                    test_num,
                    question_display,
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    error_display,
                )

        logger.info("%s", "=" * 115)

    def _calculate_benchmark_stats(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate benchmark statistics from evaluation results

        Args:
            results: List of evaluation results

        Returns:
            Dictionary with benchmark statistics
        """
        # Filter out results with errors
        valid_results = [r for r in results if r.get("metrics")]
        total_tests = len(results)
        successful_tests = len(valid_results)
        failed_tests = total_tests - successful_tests

        if not valid_results:
            return {
                "total_tests": total_tests,
                "successful_tests": 0,
                "failed_tests": failed_tests,
                "success_rate": 0.0,
            }

        # Calculate averages for each metric (handling NaN values correctly)
        # Track both sum and count for each metric to handle NaN values properly
        metrics_data = {
            "faithfulness": {"sum": 0.0, "count": 0},
            "answer_relevance": {"sum": 0.0, "count": 0},
            "context_recall": {"sum": 0.0, "count": 0},
            "context_precision": {"sum": 0.0, "count": 0},
            "ragas_score": {"sum": 0.0, "count": 0},
        }

        for result in valid_results:
            metrics = result.get("metrics", {})

            # For each metric, sum non-NaN values and count them
            faithfulness = metrics.get("faithfulness", 0)
            if not _is_nan(faithfulness):
                metrics_data["faithfulness"]["sum"] += faithfulness
                metrics_data["faithfulness"]["count"] += 1

            answer_relevance = metrics.get("answer_relevance", 0)
            if not _is_nan(answer_relevance):
                metrics_data["answer_relevance"]["sum"] += answer_relevance
                metrics_data["answer_relevance"]["count"] += 1

            context_recall = metrics.get("context_recall", 0)
            if not _is_nan(context_recall):
                metrics_data["context_recall"]["sum"] += context_recall
                metrics_data["context_recall"]["count"] += 1

            context_precision = metrics.get("context_precision", 0)
            if not _is_nan(context_precision):
                metrics_data["context_precision"]["sum"] += context_precision
                metrics_data["context_precision"]["count"] += 1

            ragas_score = result.get("ragas_score", 0)
            if not _is_nan(ragas_score):
                metrics_data["ragas_score"]["sum"] += ragas_score
                metrics_data["ragas_score"]["count"] += 1

        # Calculate averages using actual counts for each metric
        avg_metrics = {}
        for metric_name, data in metrics_data.items():
            if data["count"] > 0:
                avg_val = data["sum"] / data["count"]
                avg_metrics[metric_name] = (
                    round(avg_val, 4) if not _is_nan(avg_val) else 0.0
                )
            else:
                avg_metrics[metric_name] = 0.0

        # Find min and max RAGAS scores (filter out NaN)
        ragas_scores = []
        for r in valid_results:
            score = r.get("ragas_score", 0)
            if _is_nan(score):
                continue  # Skip NaN values
            ragas_scores.append(score)

        min_score = min(ragas_scores) if ragas_scores else 0
        max_score = max(ragas_scores) if ragas_scores else 0

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(successful_tests / total_tests * 100, 2),
            "average_metrics": avg_metrics,
            "min_ragas_score": round(min_score, 4),
            "max_ragas_score": round(max_score, 4),
        }

    async def run(self, limit: int = None) -> dict[str, Any]:
        """Run complete evaluation pipeline"""

        start_time = time.time()

        if limit:
            logger.info("Setting limit to %d test cases", limit)
            self.test_cases = self.test_cases[:limit]

        # Evaluate responses
        results = await self.evaluate_responses()

        elapsed_time = time.time() - start_time

        # Calculate benchmark statistics
        benchmark_stats = self._calculate_benchmark_stats(results)

        # Save results
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "elapsed_time_seconds": round(elapsed_time, 2),
            "benchmark_stats": benchmark_stats,
            "results": results,
        }

        # Display results table
        self._display_results_table(results)

        # Save JSON results
        json_path = (
            self.results_dir
            / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)

        # Export to CSV
        csv_path = self._export_to_csv(results)

        # Print summary
        logger.info("")
        logger.info("%s", "=" * 70)
        logger.info("📊 EVALUATION COMPLETE")
        logger.info("%s", "=" * 70)
        logger.info("Total Tests:    %s", len(results))
        logger.info("Successful:     %s", benchmark_stats["successful_tests"])
        logger.info("Failed:         %s", benchmark_stats["failed_tests"])
        logger.info("Success Rate:   %.2f%%", benchmark_stats["success_rate"])
        logger.info("Elapsed Time:   %.2f seconds", elapsed_time)
        logger.info("Avg Time/Test:  %.2f seconds", elapsed_time / len(results))

        # Print benchmark metrics
        logger.info("")
        logger.info("%s", "=" * 70)
        logger.info("📈 BENCHMARK RESULTS (Average)")
        logger.info("%s", "=" * 70)
        avg = benchmark_stats["average_metrics"]
        logger.info("Average Faithfulness:      %.4f", avg["faithfulness"])
        logger.info("Average Answer Relevance:  %.4f", avg["answer_relevance"])
        logger.info("Average Context Recall:    %.4f", avg["context_recall"])
        logger.info("Average Context Precision: %.4f", avg["context_precision"])
        logger.info("Average RAGAS Score:       %.4f", avg["ragas_score"])
        logger.info("%s", "-" * 70)
        logger.info(
            "Min RAGAS Score:           %.4f",
            benchmark_stats["min_ragas_score"],
        )
        logger.info(
            "Max RAGAS Score:           %.4f",
            benchmark_stats["max_ragas_score"],
        )

        logger.info("")
        logger.info("%s", "=" * 70)
        logger.info("📁 GENERATED FILES")
        logger.info("%s", "=" * 70)
        logger.info("Results Dir:    %s", self.results_dir.absolute())
        logger.info("   • CSV:  %s", csv_path.name)
        logger.info("   • JSON: %s", json_path.name)
        logger.info("%s", "=" * 70)

        return summary


async def main():
    """
    Main entry point for RAGAS evaluation

    Command-line arguments:
        --dataset, -d: Path to test dataset JSON file (default: sample_dataset.json)
        --ragendpoint, -r: LightRAG API endpoint URL (default: http://localhost:9621 or $LIGHTRAG_API_URL)

    Usage:
        python lightrag/evaluation/eval_rag_quality.py
        python lightrag/evaluation/eval_rag_quality.py --dataset my_test.json
        python lightrag/evaluation/eval_rag_quality.py -d my_test.json -r http://localhost:9621
    """
    try:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(
            description="RAGAS Evaluation Script for LightRAG System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Use defaults
  python lightrag/evaluation/eval_rag_quality.py

  # Specify custom dataset
  python lightrag/evaluation/eval_rag_quality.py --dataset my_test.json

  # Specify custom RAG endpoint
  python lightrag/evaluation/eval_rag_quality.py --ragendpoint http://my-server.com:9621

  # Specify both
  python lightrag/evaluation/eval_rag_quality.py -d my_test.json -r http://localhost:9621
            """,
        )

        parser.add_argument(
            "--dataset",
            "-d",
            type=str,
            default=None,
            help="Path to test dataset JSON file (default: sample_dataset.json in evaluation directory)",
        )

        parser.add_argument(
            "--ragendpoint",
            "-r",
            type=str,
            default=None,
            help="LightRAG API endpoint URL (default: http://localhost:9621 or $LIGHTRAG_API_URL environment variable)",
        )

        parser.add_argument(
            "--limit",
            "-l",
            type=int,
            default=None,
            help="Limit the number of test cases to evaluate",
        )

        # GroundedAI SLM evaluation options
        parser.add_argument(
            "--use-grounded-ai",
            action="store_true",
            help="Use GroundedAI SLM evaluation instead of RAGAS (100% local, no API costs)",
        )

        parser.add_argument(
            "--grounded-ai-model",
            type=str,
            default="grounded-ai/phi4-mini-judge",
            help="GroundedAI model identifier (default: grounded-ai/phi4-mini-judge)",
        )

        parser.add_argument(
            "--grounded-ai-device",
            type=str,
            default=None,
            help="Device for GroundedAI evaluation (cuda/cpu, auto-detect if not specified)",
        )

        parser.add_argument(
            "--grounded-ai-quantization",
            action="store_true",
            help="Enable 8-bit quantization for GroundedAI models (reduces memory usage)",
        )

        parser.add_argument(
            "--hybrid-evaluation",
            action="store_true",
            help="Run both RAGAS and GroundedAI evaluation for comparison",
        )

        args = parser.parse_args()

        # Determine evaluation mode
        use_grounded_ai = args.use_grounded_ai
        use_hybrid = args.hybrid_evaluation

        if use_grounded_ai and not GROUNDED_AI_AVAILABLE:
            logger.error(
                "❌ GroundedAI not available. Install with: pip install 'lightrag-hku[evaluation]'"
            )
            sys.exit(1)

        # Log evaluation mode
        if use_hybrid:
            logger.info("%s", "=" * 70)
            logger.info("🔍 Hybrid Evaluation - RAGAS + GroundedAI SLM")
            logger.info("%s", "=" * 70)
        elif use_grounded_ai:
            logger.info("%s", "=" * 70)
            logger.info("🔍 GroundedAI SLM Evaluation - 100% Local, No API Costs")
            logger.info("%s", "=" * 70)
        else:
            logger.info("%s", "=" * 70)
            logger.info("🔍 RAGAS Evaluation - Using Real LightRAG API")
            logger.info("%s", "=" * 70)

        # Create appropriate evaluator
        if use_grounded_ai or use_hybrid:
            evaluator = RAGEvaluator(
                test_dataset_path=args.dataset,
                rag_api_url=args.ragendpoint,
                use_grounded_ai=use_grounded_ai,
                grounded_ai_model=args.grounded_ai_model,
                grounded_ai_device=args.grounded_ai_device,
                grounded_ai_quantization=args.grounded_ai_quantization,
                hybrid_mode=use_hybrid,
            )
        else:
            evaluator = RAGEvaluator(
                test_dataset_path=args.dataset, rag_api_url=args.ragendpoint
            )

        await evaluator.run(limit=args.limit)
    except Exception as e:
        logger.exception("❌ Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
