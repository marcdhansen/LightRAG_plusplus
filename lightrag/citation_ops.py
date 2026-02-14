"""Citation generation operations extracted from operate.py."""

from lightrag.base import QueryParam
from lightrag.highlight import generate_citations_from_highlights
from lightrag.utils import generate_reference_list_from_chunks, logger


async def _generate_citations_with_auto_highlight(
    truncated_chunks: list[dict],
    query: str,
    query_param: QueryParam,
) -> tuple[list[dict], list[dict]]:
    """
    Generate citations using automatic highlighting when auto_citations is enabled.

    This function conditionally uses Zilliz semantic highlighting for automatic
    citation generation, or falls back to frequency-based citation generation.

    Args:
        truncated_chunks: List of chunk dictionaries with content and file_path
        query: User query
        query_param: Query parameters including auto_citations flag

    Returns:
        Tuple of (reference_list, truncated_chunks_with_refs)
    """
    if query_param.auto_citations:
        try:
            logger.info(
                f"Generating automatic citations with threshold {query_param.citation_threshold}"
            )
            reference_list, highlighted_citations = generate_citations_from_highlights(
                chunks=truncated_chunks,
                query=query,
                threshold=query_param.citation_threshold,
                max_citations=5,
            )

            file_path_to_ref_id = {
                ref["file_path"]: ref["reference_id"] for ref in reference_list
            }

            for chunk in truncated_chunks:
                file_path = chunk.get("file_path", "unknown_source")
                if file_path in file_path_to_ref_id:
                    chunk["reference_id"] = file_path_to_ref_id[file_path]
                else:
                    chunk["reference_id"] = ""

            logger.info(
                f"Auto-citations generated: {len(reference_list)} references from {len(highlighted_citations)} chunks"
            )
            return reference_list, truncated_chunks

        except Exception as e:
            logger.warning(
                f"Automatic citation generation failed, falling back to frequency-based: {e}"
            )

    return generate_reference_list_from_chunks(truncated_chunks)
