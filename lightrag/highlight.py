import logging
from typing import Any

import nltk
import torch
from transformers import AutoModel

logger = logging.getLogger(__name__)

# Ensure NLTK punkt is available for sentence splitting
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer data...")
    nltk.download("punkt")
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    logger.info("Downloading NLTK punkt_tab tokenizer data...")
    nltk.download("punkt_tab")

_HIGHLIGHT_MODEL = None


def load_highlight_model():
    """Lazy load the Zilliz semantic highlight model."""
    global _HIGHLIGHT_MODEL
    if _HIGHLIGHT_MODEL is None:
        model_name = "zilliz/semantic-highlight-bilingual-v1"
        logger.info(f"Loading highlighting model: {model_name}")
        try:
            # We must set trust_remote_code=True because this model uses a custom .process method
            _HIGHLIGHT_MODEL = AutoModel.from_pretrained(
                model_name, trust_remote_code=True
            )
            # Move to GPU if available
            if torch.cuda.is_available():
                _HIGHLIGHT_MODEL = _HIGHLIGHT_MODEL.to("cuda")
                logger.info("Highlighting model moved to CUDA")
            elif torch.backends.mps.is_available():
                _HIGHLIGHT_MODEL = _HIGHLIGHT_MODEL.to("mps")
                logger.info("Highlighting model moved to MPS")
            else:
                logger.info("Highlighting model using CPU")

            logger.info("Highlighting model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load highlighting model {model_name}: {e}")
            raise
    return _HIGHLIGHT_MODEL


def get_highlights(query: str, context: str, threshold: float = 0.6) -> dict[str, Any]:
    """
    Get highlighted sentences from context based on query relevance.

    Args:
        query: User query
        context: Source text to highlight
        threshold: Relevance threshold (0.0 to 1.0)

    Returns:
        Dict containing:
            - highlighted_sentences: List of relevant sentences
            - sentence_probabilities: List of probabilities for each sentence
    """
    try:
        model = load_highlight_model()

        # The Zilliz model has a custom .process method
        # It returns Dict[str, Any] with 'highlighted_sentences' and 'sentence_probabilities'
        result = model.process(
            question=query,
            context=context,
            threshold=threshold,
            return_sentence_metrics=True,
        )

        highlighted = result.get("highlighted_sentences", [])
        # Get all sentences and their probabilities
        all_probs = result.get("sentence_probabilities", [])

        # In Zilliz model, sentence_probabilities corresponds to segments in context
        # We only want those that passed the threshold.
        # The model's process method already filtered highlighted_sentences.
        # To get matching probabilities, we filter all_probs by threshold too.
        filtered_probs = [p for p in all_probs if p >= threshold]

        return {
            "highlighted_sentences": highlighted,
            "sentence_probabilities": filtered_probs,
        }
    except Exception as e:
        logger.error(f"Error during highlighting process: {e}")
        return {"highlighted_sentences": [], "sentence_probabilities": []}
