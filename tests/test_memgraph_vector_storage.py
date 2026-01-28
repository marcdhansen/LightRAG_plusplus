import asyncio

import numpy as np
import pytest

from lightrag.kg.memgraph_impl import MemgraphVectorStorage

pytestmark = [pytest.mark.heavy, pytest.mark.integration]


def dataclass_mock(func):
    func.embedding_dim = 768
    func.model_name = "mock-model"
    return func


@dataclass_mock
async def mock_embedding_func(texts, _priority=0):
    # nomic-embed-text:v1.5 has 768 dimensions as per .env
    return np.random.rand(len(texts), 768).astype(np.float32)


@pytest.mark.asyncio
async def test_memgraph_vector_storage_basic():
    """
    Basic verification of MemgraphVectorStorage upsert, query, and delete.
    Requires a running Memgraph instance at bolt://localhost:7687.
    """
    from lightrag.kg.shared_storage import initialize_share_data

    initialize_share_data()

    # Skip if MEMGRAPH_URI is not reachable
    # (Actually we assume it's there per instructions)

    storage = MemgraphVectorStorage(
        namespace="test_vector",
        workspace="test_ws",
        global_config={"working_dir": "./tests/test_data", "embedding_batch_num": 32},
        embedding_func=mock_embedding_func,
    )
    storage.meta_fields.add("meta1")

    try:
        await storage.initialize()

        async with storage._driver.session(database=storage._DATABASE) as session:
            version_res = await session.run("SHOW VERSION")
            v_record = await version_res.single()
            print(f"\nMemgraph Version: {v_record['version']}")

            modules_res = await session.run(
                "CALL mg.procedures() YIELD name, signature, returns"
            )
            async for m in modules_res:
                if "vector_search.search" in m["name"]:
                    print(f"Procedure {m['name']}:")
                    print(f"  Signature: {m['signature']}")
                    print(f"  Returns: {m['returns']}")

        # Clear previous data
        await storage.drop()

        # Test upsert
        test_data = {
            "id_1": {
                "content": "The quick brown fox jumps over the lazy dog",
                "meta1": "v1",
            },
            "id_2": {
                "content": "Artificial intelligence is transforming the world",
                "meta1": "v2",
            },
        }
        await storage.upsert(test_data)

        # Test get_by_id
        node = await storage.get_by_id("id_1")
        assert node is not None
        assert node["id"] == "id_1"
        assert node["meta1"] == "v1"

        # Test get_by_ids
        nodes = await storage.get_by_ids(["id_1", "id_2", "non_existent"])
        assert len(nodes) == 2
        assert any(n["id"] == "id_1" for n in nodes)
        assert any(n["id"] == "id_2" for n in nodes)

        # Test query
        # We search with random vector, just check we get results
        query_results = await storage.query("intelligence", top_k=5)
        assert len(query_results) > 0

        # Test get_vectors_by_ids
        vectors = await storage.get_vectors_by_ids(["id_1"])
        assert "id_1" in vectors
        assert len(vectors["id_1"]) == 768

        # Test delete
        await storage.delete(["id_1"])
        node_after = await storage.get_by_id("id_1")
        assert node_after is None

        # Test drop
        await storage.drop()
        remaining = await storage.get_by_ids(["id_2"])
        assert len(remaining) == 0

    finally:
        await storage.finalize()


if __name__ == "__main__":
    # Allow manual execution
    asyncio.run(test_memgraph_vector_storage_basic())
