import asyncio
import os
import pytest
import shutil
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from functools import partial

WORKING_DIR = "./rag_storage_ace_test"


@pytest.fixture(scope="function")
async def ace_rag():
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:7b",  # Use 7b for reliable reflection
        llm_model_func=ollama_model_complete,
        enable_ace=True,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    yield rag


@pytest.mark.asyncio
async def test_ace_reflector_repair_hallucination(ace_rag):
    rag = ace_rag

    # 1. Ingest valid data
    text = "Albert Einstein was a theoretical physicist born in Ulm, Germany."
    await rag.ainsert(text)

    # 2. Manually inject a hallucination into the graph
    await rag.chunk_entity_relation_graph.upsert_node(
        "Mars", {"entity_type": "Location", "description": "Planet"}
    )
    custom_rel = {
        "src_id": "Albert Einstein",
        "tgt_id": "Mars",
        "weight": 1.0,
        "description": "Albert Einstein was the first person to walk on Mars.",
        "keywords": "space travel, first person",
        "source_id": "manual_injection",
    }
    await rag.chunk_entity_relation_graph.upsert_edge(
        "Albert Einstein", "Mars", custom_rel
    )

    # 3. Run ACE Query
    # Force keywords to ensure retrieval of 'Mars' and 'Albert Einstein'
    param = QueryParam(mode="mix")
    query = "Tell me about Albert Einstein's connection to space travel and the planet Mars."

    result = await rag.ace_query(query, param=param)

    trajectory = result.get("trajectory", [])
    print(f"[V] ACE Trajectory: {trajectory}")

    # 4. Verify graph after ACE repair
    rel_exists = await rag.chunk_entity_relation_graph.has_edge(
        "Albert Einstein", "Mars"
    )
    entity_exists = await rag.chunk_entity_relation_graph.has_node("Mars")

    # Check if a repair was applied
    repair_step = next((s for s in trajectory if s["step"] == "graph_repair"), None)
    assert repair_step is not None, "ACE Reflector failed to identify graph repairs."
    assert not rel_exists, "Hallucination relation should have been deleted."

    print(
        f"✅ ACE Reflector identified and repaired the hallucination! Status: {repair_step['status']}"
    )
    if not entity_exists:
        print("✅ ACE Reflector also deleted the hallucinated entity 'Mars'.")


if __name__ == "__main__":
    asyncio.run(test_ace_reflector_repair_hallucination(None))
