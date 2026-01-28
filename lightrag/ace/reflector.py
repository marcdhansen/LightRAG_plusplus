from __future__ import annotations
import logging
import json
from typing import Dict, Any, List, TYPE_CHECKING

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

    async def reflect(self, query: str, generation_result: Dict[str, Any]) -> List[str]:
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
            # Use the dedicated reflection LLM if available, passing the model name explicitly
            llm_output = await self.rag.reflection_llm_model_func(
                prompt, model=self.rag.reflection_llm_model_name
            )

            # Simple parsing of the list (robustness improvements needed for prod)
            # Assuming the LLM returns a valid JSON string or close to it
            cleaned_output = llm_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output.replace("```json", "").replace(
                    "```", ""
                )

            insights = json.loads(cleaned_output)
            if isinstance(insights, list):
                return [str(i) for i in insights]
            else:
                return [str(cleaned_output)]

        except Exception as e:
            logger.error(f"ACE Reflector: Failed to reflect: {e}")
            return [f"Reflection failed: {e}"]

    async def reflect_graph_issues(
        self, query: str, generation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
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
            "the text, or if it is logically impossible, you MUST delete it.\n"
            "2. **Entity Verification:** Look at the entities. If an entity is a hallucination (not in text), delete it.\n"
            "3. **De-duplication:** If you see multiple entities that refer to the SAME real-world object (e.g., 'AI' and 'Artificial Intelligence'), "
            "recommend a MERGE. Use the full name as the target.\n\n"
            "### Repair Actions JSON Format\n"
            "Actions: \n"
            '  - `{"action": "delete_relation", "source": "Node A", "target": "Node B", "reason": "..."}`\n'
            '  - `{"action": "delete_entity", "name": "Node X", "reason": "..."}`\n'
            '  - `{"action": "merge_entities", "sources": ["AI", "A.I."], "target": "Artificial Intelligence", "reason": "..."}`\n\n'
            "### Example\n"
            'Result: [{"action": "delete_relation", "source": "Einstein", "target": "Mars", "reason": "Text says he died on Earth."}]\n\n'
            "Return ONLY the JSON list. If everything is correct, return []."
        )

        try:
            llm_output = await self.rag.reflection_llm_model_func(
                prompt, model=self.rag.reflection_llm_model_name
            )
            cleaned_output = llm_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output.replace("```json", "").replace(
                    "```", ""
                )

            # Find the first [ and last ] to extract JSON if LLM added text
            start = cleaned_output.find("[")
            end = cleaned_output.rfind("]")
            if start != -1 and end != -1:
                cleaned_output = cleaned_output[start : end + 1]

            # Basic parsing
            repairs = json.loads(cleaned_output)
            if isinstance(repairs, list):
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
