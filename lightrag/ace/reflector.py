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
        Analyzes retrieved context for hallucinations or illogical relationships.
        Returns a list of repair actions.
        """
        context_data = generation_result.get("context_data", {})

        relations = context_data.get("relationships", [])
        chunks = context_data.get("chunks", [])

        if not relations:
            return []

        # Construct Repair Reflection Prompt
        prompt = (
            "You are the Reflector component of the ACE Framework, specializing in Graph Integrity.\n"
            "CRITICAL TASK: Verify the retrieved relationships and entities against the source text chunks provided below. "
            "Identify anything that is NOT supported by the source text or is logically impossible.\n\n"
            "### Source Text Chunks\n"
        )

        for i, c in enumerate(chunks[:5]):
            prompt += f"Chunk {i}: {c.get('content')}\n"

        prompt += "\n### Relationships to Verify\n"
        for i, r in enumerate(relations[:50]):
            prompt += (
                f"{i}. {r.get('src_id')} -> {r.get('tgt_id')}: {r.get('description')}\n"
            )

        prompt += (
            "\n### Verification Logic\n"
            "Compare each relationship against the source chunks. If the relationship is not supported by "
            "the text, or if it makes a medically or scientifically impossible claim, you MUST delete it.\n\n"
            "### Example\n"
            "Relation: 'Beekeeper -> Heart Disease' (Description: Beekeepers diagnose heart disease)\n"
            "Source Text: 'Beekeepers manage hives... Heart disease is a serious condition.'\n"
            'Result: [{"action": "delete_relation", "source": "Beekeeper", "target": "Heart Disease", "reason": "Not in source text and medically false."}]\n\n'
            "\n### Actual Tasks\n"
            "1. **Relation Verification:** Check each relationship against source chunks. Delete if unsupported or false.\n"
            "2. **Entity Verification:** Look at the entities mentioned. If an entity itself is a hallucination (not mentioned or implied by the text), suggest deleting it.\n"
            "For each issue, suggest a repair action in JSON format.\n"
            "Actions: \n"
            "  - `{\"action\": \"delete_relation\", \"source\": \"Node A\", \"target\": \"Node B\", \"reason\": \"...\"}`\n"
            "  - `{\"action\": \"delete_entity\", \"name\": \"Node X\", \"reason\": \"...\"}`\n"
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

            # Basic parsing
            repairs = json.loads(cleaned_output)
            if isinstance(repairs, list):
                # Filter to only supported actions for safety
                valid_repairs = [
                    r
                    for r in repairs
                    if r.get("action") in ["delete_relation", "delete_entity"]
                ]
                if valid_repairs:
                    logger.info(
                        f"ACE Reflector: Identified {len(valid_repairs)} graph repairs."
                    )
                return valid_repairs
            return []

        except Exception as e:
            logger.error(f"ACE Reflector: Failed to reflect graph issues: {e}")
            return []
