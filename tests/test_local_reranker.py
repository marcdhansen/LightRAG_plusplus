import pytest

import asyncio
import os
import sys

pytestmark = pytest.mark.light

# Add the root directory to sys.path to import lightrag
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lightrag.rerank import local_rerank  # noqa: E402


async def test_reranker():
    docs = [
        "The capital of France is Paris.",
        "Tokyo is the capital of Japan.",
        "London is the capital of England.",
        "A building must have at least two streets for certain fire safety classifications in the BC Building Code.",
        "A sprinkler system is effective at reducing fire spread.",
    ]

    query = "What is required for fire safety in the BC Building Code?"

    print(f"\nQuery: {query}")
    print("Testing local_rerank with BAAI/bge-reranker-v2-m3...")

    try:
        results = await local_rerank(query=query, documents=docs, top_n=3)

        print("\nResults:")
        for item in results:
            print(
                f"Score: {item['relevance_score']:.4f} | Document: {docs[item['index']]}"
            )

    except Exception as e:
        print(f"Error during reranking: {e}")


if __name__ == "__main__":
    asyncio.run(test_reranker())
