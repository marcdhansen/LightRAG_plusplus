from __future__ import annotations
import logging
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lightrag.core import LightRAG

from lightrag.ace.playbook import ContextPlaybook

logger = logging.getLogger(__name__)


class ACECurator:
    """
    ACE Curator Component.
    Updates the Playbook based on insights from the Reflector and applies graph repairs.
    """

    def __init__(self, lightrag_instance: LightRAG, playbook: ContextPlaybook):
        self.rag = lightrag_instance
        self.playbook = playbook

    async def curate(self, insights: List[str]):
        """
        Incorporates insights into the playbook.
        """
        if not insights:
            return

        logger.info(f"ACE Curator: Processing {len(insights)} insights.")

        for insight in insights:
            # Prototype logic: directly add as a lesson
            # Future: Contextual deduplication, strategy refinement, etc.
            self.playbook.add_lesson(insight)
            logger.info(f"ACE Curator: Added lesson: {insight}")

    async def apply_repairs(self, repairs: List[Dict[str, Any]]):
        """
        Applies graph repairs (deletions, updates) to the LightRAG instance.
        """
        if not repairs:
            return

        logger.info(f"ACE Curator: Applying {len(repairs)} graph repairs.")

        for repair in repairs:
            action = repair.get("action")
            try:
                if action == "delete_relation":
                    source = repair.get("source")
                    target = repair.get("target")
                    if source and target:
                        logger.info(
                            f"ACE Curator: Deleting relation {source} -> {target}"
                        )
                        await self.rag.adelete_relation(source, target)
                elif action == "delete_entity":
                    name = repair.get("name")
                    if name:
                        logger.info(f"ACE Curator: Deleting entity {name}")
                        await self.rag.adelete_entity(name)
                else:
                    logger.warning(f"ACE Curator: Unknown repair action '{action}'")
            except Exception as e:
                logger.error(f"ACE Curator: Failed to apply repair {repair}: {e}")
