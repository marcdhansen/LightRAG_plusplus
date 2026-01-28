import asyncio

import numpy as np
import pytest

from lightrag.kg.memgraph_impl import MemgraphStorage, MemgraphVectorStorage
from lightrag.kg.shared_storage import initialize_share_data

pytestmark = [pytest.mark.heavy, pytest.mark.integration]


async def mock_embedding_func(texts):
    return np.random.rand(len(texts), 768)


async def test_memgraph_unified_search():
    initialize_share_data()

    global_config = {"embedding_batch_num": 32, "working_dir": "./tests/test_data"}

    graph_storage = MemgraphStorage(
        namespace="test_graph",
        workspace="unified_ws",
        global_config=global_config,
        embedding_func=mock_embedding_func,
    )

    vector_storage = MemgraphVectorStorage(
        namespace="test_vector",
        workspace="unified_ws",
        global_config=global_config,
        embedding_func=mock_embedding_func,
    )

    await graph_storage.initialize()
    await vector_storage.initialize()

    # 1. Clear data
    await graph_storage.drop()
    await vector_storage.drop()

    # 2. Ingest data into Graph
    # Node: Project X
    # Node: Chunk 1 (content about AI)
    # Edge: Chunk 1 -> Project X (PART_OF)

    await graph_storage.upsert_node(
        "Project X",
        {
            "entity_id": "Project X",
            "entity_type": "Project",
            "description": "A secret project about AI.",
        },
    )
    await graph_storage.upsert_node(
        "Chunk 1",
        {
            "entity_id": "Chunk 1",
            "entity_type": "Chunk",
            "content": "This chunk discusses artificial neural networks.",
        },
    )
    await graph_storage.upsert_edge("Chunk 1", "Project X", {"relationship": "part of"})

    # 3. Ingest data into Vector Storage
    # We use the same ID "Chunk 1" to link them logically in our mental model,
    # though Vector storage usually uses UUIDs or hashes.
    # For unified test, let's use the same ID.

    await vector_storage.upsert(
        {"Chunk 1": {"content": "This chunk discusses artificial neural networks."}}
    )

    # Debug node counts
    async with graph_storage._driver.session(
        database=graph_storage._DATABASE
    ) as session:
        v_count = await session.run(
            f"MATCH (n:`{vector_storage.label}`) RETURN count(n) as c"
        )
        c_count = await session.run("MATCH (n:unified_ws) RETURN count(n) as c")
        print(f"Vector nodes: {(await v_count.single())['c']}")
        print(f"Graph nodes: {(await c_count.single())['c']}")

        rel_res = await session.run(
            "MATCH (n:unified_ws)-[r]->(m:unified_ws) RETURN n.entity_id as src, type(r) as type, m.entity_id as tgt"
        )
        async for r in rel_res:
            print(f"Rel: {r['src']} -[:{r['type']}]-> {r['tgt']}")

    # 4. Perform Unified Query (The "Killer Feature")
    # "Find chunks similar to 'neural networks' that are part of 'Project X'"

    # Let's try a hybrid Cypher query!
    async with graph_storage._driver.session(
        database=graph_storage._DATABASE
    ) as session:
        query = f"""
        MATCH (v:`{vector_storage.label}`)
        WHERE vector_search.cosine_similarity(v.vector, $embedding) > -1.0
        MATCH (c:unified_ws {{entity_id: v.id}})
        OPTIONAL MATCH (c)-[r]->(p:unified_ws)
        WHERE r.relationship = 'part of'
        RETURN v.id, v.content, p.entity_id, vector_search.cosine_similarity(v.vector, $embedding) AS score
        ORDER BY score DESC
        """
        # Get random embedding for search
        search_vec = (await mock_embedding_func(["test"]))[0].tolist()

        print("\nExecuting Unified Hybrid Query...")
        res = await session.run(query, embedding=search_vec)
        found = False
        async for r in res:
            if r["p.entity_id"]:
                print(
                    f"Found: {r['v.id']} attached to {r['p.entity_id']} with score {r['score']:.4f}"
                )
                found = True
            else:
                print(f"Found: {r['v.id']} but no parent relationship found.")

        if not found:
            print("No complete hybrid results found.")

    await graph_storage.finalize()
    await vector_storage.finalize()


if __name__ == "__main__":
    asyncio.run(test_memgraph_unified_search())
