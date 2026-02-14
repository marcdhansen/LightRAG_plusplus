import logging
from typing import Any

import nltk

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
        # Lazy import - only needed for semantic highlighting feature
        import torch
        from transformers import AutoModel

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


def get_highlights_with_positions(
    query: str, context: str, threshold: float = 0.6
) -> dict[str, Any]:
    """
    Get highlighted sentences with character positions for citation generation.

    Args:
        query: User query
        context: Source text to highlight
        threshold: Relevance threshold (0.0 to 1.0)

    Returns:
        Dict containing:
            - highlighted_sentences: List of relevant sentences
            - sentence_probabilities: List of probabilities for each sentence
            - sentence_positions: List of (start, end) character positions for each sentence
            - citation_candidates: List of dicts with sentence, position, probability for citation
    """
    try:
        model = load_highlight_model()

        # Get highlights using the model
        result = model.process(
            question=query,
            context=context,
            threshold=threshold,
            return_sentence_metrics=True,
        )

        highlighted = result.get("highlighted_sentences", [])
        all_probs = result.get("sentence_probabilities", [])

        # Find positions of highlighted sentences in the context
        sentence_positions = []
        citation_candidates = []

        for i, sentence in enumerate(highlighted):
            # Find the sentence position in context
            start_pos = context.find(sentence)
            if start_pos >= 0:
                end_pos = start_pos + len(sentence)
                sentence_positions.append((start_pos, end_pos))

                # Get the probability (handle index mismatch if needed)
                prob = all_probs[i] if i < len(all_probs) else 0.0

                citation_candidates.append(
                    {
                        "sentence": sentence,
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                        "probability": prob,
                        "citation_score": prob,  # Use probability as citation confidence
                    }
                )
            else:
                # Log warning if sentence not found in context
                logger.warning(
                    f"Highlighted sentence not found in context: {sentence[:50]}..."
                )

        # Filter probabilities for highlighted sentences only
        filtered_probs = [c["probability"] for c in citation_candidates]

        return {
            "highlighted_sentences": highlighted,
            "sentence_probabilities": filtered_probs,
            "sentence_positions": sentence_positions,
            "citation_candidates": citation_candidates,
        }
    except Exception as e:
        logger.error(f"Error during highlighting with positions: {e}")
        return {
            "highlighted_sentences": [],
            "sentence_probabilities": [],
            "sentence_positions": [],
            "citation_candidates": [],
        }


def generate_citations_from_highlights(
    chunks: list[dict],
    query: str,
    threshold: float = 0.6,
    max_citations: int = 5,
) -> tuple[list[dict], list[dict]]:
    """
    Generate citations from highlighted content across multiple chunks.

    Args:
        chunks: List of chunk dictionaries with 'content', 'file_path', 'chunk_id', 'full_doc_id'
        query: User query
        threshold: Relevance threshold for highlighting (0.0 to 1.0)
        max_citations: Maximum number of citations to generate

    Returns:
        Tuple of (reference_list, highlighted_citations):
            - reference_list: List of dicts with reference_id, file_path, doc_id for API
            - highlighted_citations: List of citation dicts with chunk info and highlighted sentences
    """
    try:
        highlighted_citations = []
        file_path_to_citations = {}

        # Process each chunk
        for chunk in chunks:
            content = chunk.get("content", "")
            file_path = chunk.get("file_path", "unknown_source")
            chunk_id = chunk.get("chunk_id", "")
            full_doc_id = chunk.get("full_doc_id", "")

            if not content or file_path == "unknown_source":
                continue

            # Get highlights with positions for this chunk
            highlight_result = get_highlights_with_positions(
                query=query, context=content, threshold=threshold
            )

            citation_candidates = highlight_result.get("citation_candidates", [])

            if citation_candidates:
                # Store citations for this file_path
                if file_path not in file_path_to_citations:
                    file_path_to_citations[file_path] = {
                        "file_path": file_path,
                        "chunk_id": chunk_id,
                        "full_doc_id": full_doc_id,
                        "citations": [],
                        "max_probability": 0.0,
                    }

                # Add citation candidates
                for candidate in citation_candidates:
                    file_path_to_citations[file_path]["citations"].append(
                        {
                            "sentence": candidate["sentence"],
                            "position": (candidate["start_pos"], candidate["end_pos"]),
                            "probability": candidate["probability"],
                            "citation_score": candidate["citation_score"],
                        }
                    )
                    # Track max probability for this source
                    file_path_to_citations[file_path]["max_probability"] = max(
                        file_path_to_citations[file_path]["max_probability"],
                        candidate["probability"],
                    )

                # Add to highlighted citations list
                highlighted_citations.append(
                    {
                        "chunk_id": chunk_id,
                        "file_path": file_path,
                        "full_doc_id": full_doc_id,
                        "highlights": citation_candidates,
                    }
                )

        # Sort file_paths by max probability (descending) for reference ordering
        sorted_file_paths = sorted(
            file_path_to_citations.keys(),
            key=lambda fp: file_path_to_citations[fp]["max_probability"],
            reverse=True,
        )

        # Generate reference list
        reference_list = []
        for i, file_path in enumerate(sorted_file_paths[:max_citations], 1):
            citation_data = file_path_to_citations[file_path]
            reference_list.append(
                {
                    "reference_id": str(i),
                    "file_path": file_path,
                    "doc_id": citation_data["full_doc_id"],
                    "chunk_id": citation_data["chunk_id"],
                    "max_probability": citation_data["max_probability"],
                    "num_highlights": len(citation_data["citations"]),
                }
            )

        # Limit highlighted citations to top max_citations sources
        top_file_paths = set(sorted_file_paths[:max_citations])
        filtered_highlighted_citations = [
            hc for hc in highlighted_citations if hc["file_path"] in top_file_paths
        ]

        logger.info(
            f"Generated {len(reference_list)} citations from {len(chunks)} chunks "
            f"(threshold: {threshold})"
        )

        return reference_list, filtered_highlighted_citations

    except Exception as e:
        logger.error(f"Error generating citations from highlights: {e}")
        return [], []
