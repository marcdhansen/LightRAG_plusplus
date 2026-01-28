import asyncio
import logging
import os
from functools import partial

from dotenv import load_dotenv

from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

# Set up logging
logging.basicConfig(level=logging.INFO)
load_dotenv()


async def test_beekeeping():
    # Initialize LightRAG
    working_dir = "./rag_storage_beekeeping"
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=ollama_model_complete,
        llm_model_name=os.getenv("LLM_MODEL", "qwen2.5-coder:1.5b"),
        llm_model_kwargs={
            "host": os.getenv("LLM_BINDING_HOST", "http://127.0.0.1:11434"),
            "options": {"num_ctx": 8192},
            "timeout": int(os.getenv("LLM_TIMEOUT", "300")),
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "768")),
            max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
            func=partial(
                ollama_embed.func,
                embed_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text:v1.5"),
                host=os.getenv("EMBEDDING_BINDING_HOST", "http://127.0.0.1:11434"),
            ),
        ),
    )

    print("Initializing storages...")
    await rag.initialize_storages()
    print("Storage initialization complete.")

    # Ingest beekeeping text
    beekeeping_text_path = "./docs/beekeeping_test_data.txt"
    if not os.path.exists(beekeeping_text_path):
        print(f"Error: {beekeeping_text_path} not found.")
        return

    with open(beekeeping_text_path) as f:
        content = f.read()

    print("Ingesting beekeeping data...")
    await rag.ainsert(content)
    print("Ingestion complete.")

    # Test Retrieval
    queries = [
        "What is a beekeeper according to the text?",
        "How do beekeepers manage bees?",
        "What role does beekeeping play in agriculture?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        # Test Hybrid Retrieval
        print("--- Hybrid Retrieval ---")
        response = await rag.aquery(query, param=QueryParam(mode="hybrid"))
        print(f"Response: {response}")

        # Test Low-level Retrieval
        print("--- local Retrieval ---")
        response = await rag.aquery(query, param=QueryParam(mode="local"))
        print(f"Response: {response}")

        # Test High-level Retrieval
        print("--- global Retrieval ---")
        response = await rag.aquery(query, param=QueryParam(mode="global"))
        print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(test_beekeeping())
