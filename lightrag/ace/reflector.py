from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lightrag.core import LightRAG

logger = logging.getLogger(__name__)


class ACEReflector:
    """
    ACE Reflector Component.
    Critiques the Generator's performance and extracts lessons.
    """

    def __init__(self, lightrag_instance: LightRAG):
        self.rag = lightrag_instance

    def _parse_json_list(self, llm_output: str) -> list[Any]:
        """
        Robustly extracts and parses a JSON list from LLM output.
        """
        cleaned = llm_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "").strip()

        # Find the first [ and last ]
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]

        try:
            data = json.loads(cleaned)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(
                f"ACE Reflector: Failed to parse JSON list: {e}. Output: {llm_output[:100]}..."
            )
            return []

    async def reflect(self, query: str, generation_result: dict[str, Any]) -> list[str]:
        """
        Analyzes the interaction and returns a list of insights/lessons.
        """
        response = generation_result.get("response")
        if not response:
            return ["Error: No response generated to reflect upon."]

        # Construct Reflection Prompt
        prompt = (
            "You are the Reflector component of the ACE Framework.\n"
            "Analyze the following interaction for quality, accuracy, and adherence to instructions.\n"
            "Identify 1-3 key lessons or insights that could improve future performance.\n"
            'Format your output as a simple JSON list of strings, e.g. ["Insight 1", "Insight 2"].\n\n'
            f"Query: {query}\n"
            f"Response: {response}\n"
        )

        try:
            # Use the dedicated reflection LLM if available, falling back to default if not configured
            llm_func = self.rag.reflection_llm_model_func or self.rag.llm_model_func
            model_name = self.rag.reflection_llm_model_name or self.rag.llm_model_name

            if not llm_func:
                return ["Error: No LLM function configured for reflection."]

            llm_output = await llm_func(prompt, model=model_name)
            insights = self._parse_json_list(llm_output)
            return (
                [str(i) for i in insights]
                if insights
                else [f"Reflection failed to parse insights from: {llm_output[:50]}"]
            )

        except Exception as e:
            logger.error(f"ACE Reflector: Failed to reflect: {e}")
            return [f"Reflection failed: {e}"]

    async def reflect_graph_issues(
        self, query: str, generation_result: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Analyzes retrieved context for hallucinations, illogical relationships, or duplicate entities.
        Returns a list of repair actions.
        """
        context_data = generation_result.get("context_data", {})

        relations = context_data.get("relationships", [])
        entities = context_data.get("entities", [])
        chunks = context_data.get("chunks", [])

        if not chunks:
            return []

        # Construct Repair Reflection Prompt
        prompt = (
            "You are the Reflector component of the ACE Framework, specializing in Graph Integrity.\n"
            "CRITICAL TASK: Verify the retrieved graph data against the source text chunks provided below.\n\n"
            "### Source Text Chunks\n"
        )

        for i, c in enumerate(chunks[:5]):
            prompt += f"Chunk {i}: {c.get('content')}\n"

        prompt += "\n### Entities to Verify\n"
        for i, e in enumerate(entities[:50]):
            prompt += f"{i}. {e.get('entity_name')} ({e.get('entity_type')}): {e.get('description')}\n"

        prompt += "\n### Relationships to Verify\n"
        for i, r in enumerate(relations[:50]):
            prompt += (
                f"{i}. {r.get('src_id')} -> {r.get('tgt_id')}: {r.get('description')}\n"
            )

        prompt += (
            "\n### Verification Logic\n"
            "1. **Relation Verification:** Compare each relationship against the source chunks. If the relationship is not supported by "
            "the text (explicitly or logically inferred), you MUST delete it.\n"
            "2. **Entity Verification:** Look at the entities. If an entity is a hallucination (not mentioned in the source text), you MUST delete it.\n"
            "3. **De-duplication:** If you see multiple entities that refer to the SAME real-world object (e.g., 'AI' and 'Artificial Intelligence'), "
            "recommend a MERGE. Use the full name as the target.\n\n"
            "### Instructions\n"
            "- For `delete_relation`, use the EXACT 'src_id' and 'tgt_id' from the list above.\n"
            "- For `delete_entity`, use the EXACT 'entity_name' from the list above.\n"
            "- If an entity is deleted, and it was a hallucination, also delete any relations it was involved in.\n\n"
            "### Repair Actions JSON Format\n"
            "Actions: \n"
            '  - `{"action": "delete_relation", "source": "Node A", "target": "Node B", "reason": "..."}`\n'
            '  - `{"action": "delete_entity", "name": "Node X", "reason": "..."}`\n'
            '  - `{"action": "merge_entities", "sources": ["AI", "A.I."], "target": "Artificial Intelligence", "reason": "..."}`\n\n'
            "### Example\n"
            'Result: [{"action": "delete_relation", "source": "Einstein", "target": "Mars", "reason": "Text says he died on Earth."}, {"action": "delete_entity", "name": "Mars", "reason": "Mars is not mentioned in source text."}]\n\n'
            "Return ONLY the JSON list. If everything is correct, return []."
        )

        try:
            llm_func = self.rag.reflection_llm_model_func or self.rag.llm_model_func
            model_name = self.rag.reflection_llm_model_name or self.rag.llm_model_name

            if not llm_func:
                logger.error(
                    "ACE Reflector: No LLM function configured for graph repair reflection."
                )
                return []

            llm_output = await llm_func(prompt, model=model_name)
            repairs = self._parse_json_list(llm_output)
            if repairs:
                # Filter to only supported actions for safety
                valid_actions = ["delete_relation", "delete_entity", "merge_entities"]
                valid_repairs = [r for r in repairs if r.get("action") in valid_actions]
                if valid_repairs:
                    logger.info(
                        f"ACE Reflector: Identified {len(valid_repairs)} graph repairs."
                    )
                return valid_repairs
            return []

        except Exception as e:
            logger.error(f"ACE Reflector: Failed to reflect graph issues: {e}")
            return []
