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
            "Format your output as a simple JSON list of strings, e.g. [\"Insight 1\", \"Insight 2\"].\n\n"
            f"Query: {query}\n"
            f"Response: {response}\n"
        )

        try:
            # We use the same LLM for reflection for now
            llm_output = await self.rag.llm_model_func(prompt)
            
            # Simple parsing of the list (robustness improvements needed for prod)
            # Assuming the LLM returns a valid JSON string or close to it
            cleaned_output = llm_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output.replace("```json", "").replace("```", "")
            
            insights = json.loads(cleaned_output)
            if isinstance(insights, list):
                return [str(i) for i in insights]
            else:
                return [str(cleaned_output)]

        except Exception as e:
            logger.error(f"ACE Reflector: Failed to reflect: {e}")
            return [f"Reflection failed: {e}"]
