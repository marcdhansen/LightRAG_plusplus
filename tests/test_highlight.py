import pytest

from lightrag.highlight import get_highlights


@pytest.mark.offline
def test_get_highlights_basic():
    """Test basic highlighting with a simple query and context."""
    pytest.importorskip(
        "transformers", reason="Requires transformers for semantic highlighting"
    )
    pytest.importorskip("torch", reason="Requires torch for semantic highlighting")

    query = "What is the capital of France?"
    context = "Paris is the capital of France. Berlin is the capital of Germany."
    result = get_highlights(
        query, context, threshold=0.1
    )  # Use low threshold to ensure match

    assert "highlighted_sentences" in result
    assert "sentence_probabilities" in result
    assert len(result["highlighted_sentences"]) > 0
    assert any("Paris" in s for s in result["highlighted_sentences"])
    assert len(result["highlighted_sentences"]) == len(result["sentence_probabilities"])


@pytest.mark.offline
def test_get_highlights_threshold():
    """Test that the threshold correctly filters out irrelevant content."""
    pytest.importorskip(
        "transformers", reason="Requires transformers for semantic highlighting"
    )
    pytest.importorskip("torch", reason="Requires torch for semantic highlighting")

    query = "What is the capital of France?"
    context = "Berlin is the capital of Germany. London is the capital of the UK."
    # With a high threshold, these should not match
    result = get_highlights(query, context, threshold=0.9)

    assert len(result["highlighted_sentences"]) == 0
    assert len(result["sentence_probabilities"]) == 0


@pytest.mark.offline
def test_get_highlights_empty():
    """Test highlighting with empty input."""
    result = get_highlights("", "", threshold=0.5)
    assert len(result["highlighted_sentences"]) == 0
    assert len(result["sentence_probabilities"]) == 0


def test_get_highlights_empty():
    """Test highlighting with empty input."""
    result = get_highlights("", "", threshold=0.5)
    assert len(result["highlighted_sentences"]) == 0
    assert len(result["sentence_probabilities"]) == 0
