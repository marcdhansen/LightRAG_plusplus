import asyncio
import os
from functools import partial

import pytest

from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./rag_storage_ace_regression"


@pytest.fixture(scope="function")
async def rag_instance():
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        enable_ace=True,
        llm_model_name="qwen2.5-coder:1.5b",
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    return rag


@pytest.mark.asyncio
async def test_beekeeping_hallucination_repair(rag_instance):
    """
    ACE Regression Test:
    Ensures that the 'Beekeeper -> Heart Disease' hallucination is identified and repaired.
    """
    rag = rag_instance

    # 1. Manually insert the hallucinated edge and a relevant chunk
    try:
        # Ingest a small valid text to create a real chunk
        await rag.ainsert(
            "Beekeepers manage honey bee colonies for pollination and honey production."
        )

        await rag.acreate_entity(
            "Beekeeper", {"entity_type": "Person", "description": "A beekeeper."}
        )
        await rag.acreate_entity(
            "Heart Disease",
            {"entity_type": "Disease", "description": "A medical condition."},
        )
        await rag.acreate_relation(
            "Beekeeper",
            "Heart Disease",
            {
                "description": "Beekeepers diagnose heart disease in their spare time.",
                "keywords": "hallucination,medical",
                "weight": 1.0,
            },
        )
    except Exception as e:
        print(f"Note: Potential conflict during setup: {e}")

    # Verify it exists before ACE
    exists = await rag.chunk_entity_relation_graph.has_edge(
        "Beekeeper", "Heart Disease"
    )
    assert exists, "Hallucinated edge should exist for the test."

    # 2. Run query with ACE enabled and high top_k to ensure retrieval
    query = "Do beekeepers have medical expertise regarding heart disease?"
    print(f"\nRunning ACE Query: {query}")

    # We use mode='local' and high top_k to ensure the relationship is found
    # NOTE: Calling ace_query directly to trigger the repair loop
    result = await rag.ace_query(query, param=QueryParam(mode="local", top_k=20))

    print(f"ACE Response: {result.get('response')}")

    # 3. Verify the edge is gone
    exists_after = await rag.chunk_entity_relation_graph.has_edge(
        "Beekeeper", "Heart Disease"
    )

    if exists_after:
        # Check if it was retrieved but ignored
        print("Edge still exists. Checking if it was even in context...")
        # (This is hard to check without internal instrumentation, but we can infer)

    assert not exists_after, (
        "ACE should have deleted the logically unsound relationship 'Beekeeper -> Heart Disease'."
    )


if __name__ == "__main__":
    asyncio.run(test_beekeeping_hallucination_repair(None))  # Manual run helper
