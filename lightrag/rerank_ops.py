"""Reranking operations extracted from operate.py."""

from lightrag.base import QueryParam
from lightrag.utils import apply_rerank_if_enabled


async def rerank_graph_elements(
    query: str,
    elements: list[dict],
    global_config: dict,
    element_type: str,
    query_param: QueryParam,
) -> list[dict]:
    """Rerank graph elements (entities or relations) based on relevance to the query."""
    if not elements:
        return elements

    formatted_elements = []
    for el in elements:
        if element_type == "entity":
            content = f"Entity: {el.get('entity_name', '')} | Type: {el.get('entity_type', '')} | Description: {el.get('description', '')}"
        else:  # relation
            src = el.get("src_id") or (el.get("src_tgt")[0] if "src_tgt" in el else "")
            tgt = el.get("tgt_id") or (el.get("src_tgt")[1] if "src_tgt" in el else "")
            content = (
                f"Relation: {src} -> {tgt} | Description: {el.get('description', '')}"
            )

        formatted_elements.append({"content": content, "_original": el})

    top_n = query_param.top_k
    reranked_proxies = await apply_rerank_if_enabled(
        query=query,
        retrieved_docs=formatted_elements,
        global_config=global_config,
        enable_rerank=True,
        top_n=top_n,
    )

    results = []
    for proxy in reranked_proxies:
        original = proxy["_original"]
        if "relevance_score" in proxy:
            original["rerank_score"] = proxy["relevance_score"]
        results.append(original)

    return results
