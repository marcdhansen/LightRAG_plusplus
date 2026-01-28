import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.ace_test_utils import ACETestKit
from lightrag import LightRAG


@pytest.mark.asyncio
async def test_ace_test_kit_methods():
    # Mock LightRAG
    rag_mock = MagicMock(spec=LightRAG)
    rag_mock.chunk_entity_relation_graph = MagicMock()
    rag_mock.chunk_entity_relation_graph.upsert_node = AsyncMock()
    rag_mock.chunk_entity_relation_graph.upsert_edge = AsyncMock()
    rag_mock.chunk_entity_relation_graph.has_edge = AsyncMock(return_value=True)
    rag_mock.chunk_entity_relation_graph.has_node = AsyncMock(return_value=True)

    kit = ACETestKit(rag_mock)

    # Test Injection
    await kit.inject_hallucination("A", "B", {"desc": "relation"}, {"type": "node"})
    rag_mock.chunk_entity_relation_graph.upsert_node.assert_called_with(
        "B", {"type": "node"}
    )
    rag_mock.chunk_entity_relation_graph.upsert_edge.assert_called_with(
        "A", "B", {"desc": "relation", "src_id": "A", "tgt_id": "B"}
    )

    # Test Verification
    await kit.verify_relation_existence("A", "B", should_exist=True)
    rag_mock.chunk_entity_relation_graph.has_edge.assert_called_with("A", "B")

    # Test Repair Step Finding
    traj = [{"step": "irrelevant"}, {"step": "graph_repair", "status": "fixed"}]
    step = kit.find_repair_step(traj)
    assert step["status"] == "fixed"
