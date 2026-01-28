import asyncio
import os
import shutil
from functools import partial

import pytest

from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc
from tests.ace_test_utils import ACETestKit

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
    kit = ACETestKit(rag)

    # 1. Ingest valid data
    text = "Albert Einstein was a theoretical physicist born in Ulm, Germany."
    await rag.ainsert(text)

    # 2. Manually inject a hallucination into the graph
    custom_rel = {
        "weight": 1.0,
        "description": "Albert Einstein was the first person to walk on Mars.",
        "keywords": "space travel, first person",
        "source_id": "manual_injection",
    }

    await kit.inject_hallucination(
        src_id="Albert Einstein",
        tgt_id="Mars",
        relation_data=custom_rel,
        tgt_node_data={"entity_type": "Location", "description": "Planet"},
    )

    # 3. Run ACE Query
    # Force keywords to ensure retrieval of 'Mars' and 'Albert Einstein'
    param = QueryParam(mode="mix")
    query = "Tell me about Albert Einstein's connection to space travel and the planet Mars."

    result = await rag.ace_query(query, param=param)

    trajectory = result.get("trajectory", [])
    print(f"[V] ACE Trajectory: {trajectory}")

    # 4. Verify graph after ACE repair
    repair_step = kit.find_repair_step(trajectory)
    assert repair_step is not None, "ACE Reflector failed to identify graph repairs."
    print(
        f"✅ ACE Reflector identified and repaired the hallucination! Status: {repair_step['status']}"
    )

    await kit.verify_relation_existence("Albert Einstein", "Mars", should_exist=False)
    await kit.verify_entity_existence("Mars", should_exist=False)

    print("✅ ACE Reflector verification complete.")


if __name__ == "__main__":
    asyncio.run(test_ace_reflector_repair_hallucination(None))
