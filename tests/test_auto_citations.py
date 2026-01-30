"""
Test automatic citation generation from Zilliz highlights.
"""

import pytest

from lightrag.highlight import (
    generate_citations_from_highlights,
    get_highlights_with_positions,
)


@pytest.mark.offline
@pytest.mark.light
def test_get_highlights_with_positions():
    """Test that get_highlights_with_positions returns positions and citation candidates."""
    query = "What is the capital of France?"
    context = "Paris is the capital of France. Berlin is the capital of Germany."

    result = get_highlights_with_positions(query, context, threshold=0.1)

    assert "highlighted_sentences" in result
    assert "sentence_probabilities" in result
    assert "sentence_positions" in result
    assert "citation_candidates" in result

    # Check that citation candidates have required fields
    for candidate in result["citation_candidates"]:
        assert "sentence" in candidate
        assert "start_pos" in candidate
        assert "end_pos" in candidate
        assert "probability" in candidate
        assert "citation_score" in candidate

        # Validate positions
        assert candidate["start_pos"] >= 0
        assert candidate["end_pos"] > candidate["start_pos"]


@pytest.mark.offline
@pytest.mark.light
def test_get_highlights_with_positions_no_matches():
    """Test that function handles no matches gracefully."""
    query = "What is the capital of France?"
    context = "Berlin is the capital of Germany. London is the capital of the UK."

    result = get_highlights_with_positions(query, context, threshold=0.9)

    assert len(result["highlighted_sentences"]) == 0
    assert len(result["sentence_positions"]) == 0
    assert len(result["citation_candidates"]) == 0


@pytest.mark.offline
@pytest.mark.light
def test_generate_citations_from_highlights():
    """Test automatic citation generation from chunks."""
    query = "What is the capital of France?"

    # Create test chunks
    chunks = [
        {
            "content": "Paris is the capital of France.",
            "file_path": "/docs/france.txt",
            "chunk_id": "chunk-1",
            "full_doc_id": "doc-1",
        },
        {
            "content": "Berlin is the capital of Germany.",
            "file_path": "/docs/germany.txt",
            "chunk_id": "chunk-2",
            "full_doc_id": "doc-2",
        },
    ]

    reference_list, highlighted_citations = generate_citations_from_highlights(
        chunks=chunks,
        query=query,
        threshold=0.1,  # Low threshold for testing
        max_citations=5,
    )

    # Check that reference list was generated
    assert isinstance(reference_list, list)
    assert isinstance(highlighted_citations, list)

    # If any citations were found, check their structure
    for ref in reference_list:
        assert "reference_id" in ref
        assert "file_path" in ref
        assert "doc_id" in ref
        assert "chunk_id" in ref


@pytest.mark.offline
@pytest.mark.light
def test_generate_citations_empty_chunks():
    """Test that empty chunks return empty results."""
    reference_list, highlighted_citations = generate_citations_from_highlights(
        chunks=[],
        query="test query",
        threshold=0.6,
    )

    assert reference_list == []
    assert highlighted_citations == []


@pytest.mark.offline
@pytest.mark.light
def test_generate_citations_with_unknown_source():
    """Test that chunks with unknown_source are excluded."""
    chunks = [
        {
            "content": "Some content",
            "file_path": "unknown_source",
            "chunk_id": "chunk-1",
            "full_doc_id": "doc-1",
        }
    ]

    reference_list, highlighted_citations = generate_citations_from_highlights(
        chunks=chunks,
        query="test",
        threshold=0.1,
    )

    # Should not generate citations for unknown_source
    assert len(reference_list) == 0
    assert len(highlighted_citations) == 0


@pytest.mark.offline
@pytest.mark.light
def test_generate_citations_max_citations_limit():
    """Test that max_citations parameter is respected."""
    query = "capital cities"

    # Create many chunks
    chunks = [
        {
            "content": f"Chunk {i} about capitals.",
            "file_path": f"/docs/file{i}.txt",
            "chunk_id": f"chunk-{i}",
            "full_doc_id": f"doc-{i}",
        }
        for i in range(10)
    ]

    reference_list, _ = generate_citations_from_highlights(
        chunks=chunks,
        query=query,
        threshold=0.1,
        max_citations=3,  # Limit to 3 citations
    )

    # Should respect the max_citations limit
    assert len(reference_list) <= 3
