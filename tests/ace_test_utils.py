from typing import Any

from lightrag import LightRAG


class ACETestKit:
    """
    Standardized utility for testing Injection-Reflection-Repair cycles in ACE.
    """

    def __init__(self, rag: LightRAG):
        self.rag = rag

    async def inject_hallucination(
        self,
        src_id: str,
        tgt_id: str,
        relation_data: dict[str, Any],
        tgt_node_data: dict[str, Any] | None = None,
    ):
        """
        Manually injects a node and/or edge into the graph to simulate a hallucination
        or incorrect knowledge that needs repair.
        """
        if tgt_node_data:
            await self.rag.chunk_entity_relation_graph.upsert_node(
                tgt_id, tgt_node_data
            )

        # Ensure relation_data has required keys if missing
        if "src_id" not in relation_data:
            relation_data["src_id"] = src_id
        if "tgt_id" not in relation_data:
            relation_data["tgt_id"] = tgt_id

        await self.rag.chunk_entity_relation_graph.upsert_edge(
            src_id, tgt_id, relation_data
        )

    async def verify_relation_existence(
        self, src_id: str, tgt_id: str, should_exist: bool = False
    ):
        """
        Verifies whether a relation exists between two nodes.
        """
        exists = await self.rag.chunk_entity_relation_graph.has_edge(src_id, tgt_id)
        if should_exist:
            assert exists, f"Relation should exist between '{src_id}' and '{tgt_id}'"
        else:
            assert not exists, (
                f"Relation between '{src_id}' and '{tgt_id}' should have been removed"
            )

    async def verify_entity_existence(self, entity_id: str, should_exist: bool = False):
        """
        Verifies whether an entity node exists in the graph.
        """
        exists = await self.rag.chunk_entity_relation_graph.has_node(entity_id)
        if should_exist:
            assert exists, f"Entity '{entity_id}' should exist"
        else:
            assert not exists, f"Entity '{entity_id}' should have been removed"

    def find_repair_step(
        self, trajectory: list, step_name: str = "graph_repair"
    ) -> dict[str, Any] | None:
        """
        Helper to find a specific step in the ACE trajectory.
        """
        return next((s for s in trajectory if s["step"] == step_name), None)
