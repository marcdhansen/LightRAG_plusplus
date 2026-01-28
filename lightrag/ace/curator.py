from __future__ import annotations
import logging
import json
import os
import uuid
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
        # Store repairs in the same directory as the playbook
        self.repairs_file = os.path.join(
            self.playbook.config.base_dir, "ace_repairs.json"
        )
        self.pending_repairs: Dict[str, Dict[str, Any]] = {}
        self._load_repairs()

    def _load_repairs(self):
        if os.path.exists(self.repairs_file):
            try:
                with open(self.repairs_file, "r") as f:
                    self.pending_repairs = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load pending repairs: {e}")
                self.pending_repairs = {}
        else:
            self.pending_repairs = {}

    def _save_repairs(self):
        try:
            with open(self.repairs_file, "w") as f:
                json.dump(self.pending_repairs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pending repairs: {e}")

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

        # Check for HITL
        hitl_enabled = False
        if self.rag.ace_config and self.rag.ace_config.enable_human_in_the_loop:
            hitl_enabled = True

        if hitl_enabled:
            logger.info(
                f"ACE Curator: Staging {len(repairs)} graph repairs for Human Review."
            )
            for repair in repairs:
                # Generate ID if not present
                if "id" not in repair:
                    repair["id"] = str(uuid.uuid4())

                # Set status if not present
                if "status" not in repair:
                    repair["status"] = "pending"

                # Set timestamp if not present
                if "created_at" not in repair:
                    import time

                    repair["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                self.pending_repairs[repair["id"]] = repair
            self._save_repairs()
            return

        logger.info(f"ACE Curator: Applying {len(repairs)} graph repairs.")

        for repair in repairs:
            await self._execute_repair(repair)

    async def _execute_repair(self, repair: Dict[str, Any]):
        action = repair.get("action")
        try:
            if action == "delete_relation":
                source = repair.get("source")
                target = repair.get("target")
                if source and target:
                    logger.info(f"ACE Curator: Deleting relation {source} -> {target}")
                    await self.rag.adelete_relation(source, target)
            elif action == "delete_entity":
                name = repair.get("name")
                if name:
                    logger.info(f"ACE Curator: Deleting entity {name}")
                    await self.rag.adelete_entity(name)
            elif action == "merge_entities":
                sources = repair.get("sources")
                target = repair.get("target")
                if sources and target:
                    logger.info(f"ACE Curator: Merging {sources} into {target}")
                    await self.rag.amerge_entities(
                        source_entities=sources,
                        target_entity=target,
                        merge_strategy={
                            "description": "concatenate",
                            "entity_type": "keep_first",
                        },
                    )
            else:
                logger.warning(f"ACE Curator: Unknown repair action '{action}'")
        except Exception as e:
            logger.error(f"ACE Curator: Failed to apply repair {repair}: {e}")

    def get_pending_repairs(self) -> List[Dict[str, Any]]:
        return list(self.pending_repairs.values())

    async def approve_repair(self, repair_id: str):
        if repair_id in self.pending_repairs:
            repair = self.pending_repairs[repair_id]
            logger.info(f"ACE Curator: Approving repair {repair_id}")
            await self._execute_repair(repair)
            # Remove from pending list after successful execution
            del self.pending_repairs[repair_id]
            self._save_repairs()
            return True
        return False

    async def reject_repair(self, repair_id: str):
        if repair_id in self.pending_repairs:
            logger.info(f"ACE Curator: Rejecting repair {repair_id}")
            del self.pending_repairs[repair_id]
            self._save_repairs()
            return True
        return False
