import asyncio
import os
import logging
from lightrag import LightRAG, QueryParam

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKING_DIR = "./rag_storage_beekeeping"


async def test_ace_graph_repair():
    if not os.path.exists(WORKING_DIR):
        print(f"Directory {WORKING_DIR} does not exist. Please run ingestion first.")
        return

    from lightrag.llm.ollama import ollama_model_complete, ollama_embed
    from lightrag.utils import EmbeddingFunc
    from functools import partial

    # Initialize LightRAG with ACE enabled
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

    # 1. Verify the edge exists before repair
    print("\n--- Verifying initial state ---")
    edge = await rag.chunk_entity_relation_graph.get_edge("Beekeeper", "Heart Disease")
    if edge:
        print("Found hallucinated edge: Beekeeper -> Heart Disease")
    else:
        print("Hallucinated edge not found. Maybe it was already repaired?")
        # Re-create it if missing for test consistency
        await rag.acreate_relation(
            "Beekeeper",
            "Heart Disease",
            {
                "description": "Beekeepers diagnose potential heart issues, contributing to their overall health.",
                "keywords": "diagnosis,heart issues",
            },
        )
        print("Created hallucinated edge for testing.")

    # 2. Run ACE Query
    print("\n--- Running ACE Query & Repair Loop ---")
    query = "Do beekeepers diagnose heart disease?"
    result = await rag.ace_generator.generate(query, QueryParam(mode="mix"))

    print(f"Response: {result.get('response')}")
    print(f"Trajectory: {result.get('trajectory')}")

    # 3. Verify the edge is gone
    print("\n--- Verifying post-repair state ---")
    edge_after = await rag.chunk_entity_relation_graph.get_edge(
        "Beekeeper", "Heart Disease"
    )
    if not edge_after:
        print(
            "Success: Hallucinated edge 'Beekeeper -> Heart Disease' has been removed by ACE!"
        )
    else:
        print("Failure: Hallucinated edge still exists.")
        print(f"Edge data: {edge_after}")


if __name__ == "__main__":
    asyncio.run(test_ace_graph_repair())
