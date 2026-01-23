from __future__ import annotations
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lightrag.core import LightRAG, QueryParam

from lightrag.ace.playbook import ContextPlaybook

logger = logging.getLogger(__name__)

class ACEGenerator:
    """
    ACE Generator Component.
    Executes queries using the Context Playbook and retrieved context.
    """

    def __init__(self, lightrag_instance: LightRAG, playbook: ContextPlaybook):
        self.rag = lightrag_instance
        self.playbook = playbook

    async def generate(self, query: str, param: Optional[QueryParam] = None) -> Dict[str, Any]:
        """
        Generates a response to the query using ACE context.
        """
        if param is None:
            from lightrag.base import QueryParam
            param = QueryParam()

        logger.info(f"ACE Generator: Executing query '{query}'")

        # 1. Retrieve Data (Context) from LightRAG without generation
        # This gets us the entities, relations, and chunks
        context_result = await self.rag.aquery_data(query, param)
        
        if context_result.get("status") != "success":
            logger.error(f"ACE Generator: Failed to retrieve context: {context_result.get('message')}")
            return {"error": "Failed to retrieve context", "details": context_result}

        context_data = context_result.get("data", {})

        # 2. Render the Playbook
        playbook_str = self.playbook.render()

        # 3. Format Retrieved Context
        # We need to turn the structured data into a text block for the LLM
        formatted_context = self._format_context_data(context_data)

        # 4. Construct the Prompt
        # This is a simplified prompt construction. 
        # In a full implementation, we might want to use specific templates.
        system_msg = (
            "You are an intelligent assistant powered by the ACE (Agentic Context Evolution) Framework.\n"
            "Your goal is to answer the user's query based strictly on the provided context and your operational playbook.\n\n"
            "### ACE Context Playbook\n"
            "This playbook defines your strategies and lessons learned. Follow these directives closely:\n"
            f"{playbook_str}\n\n"
            "### Retrieved Knowledge\n"
            f"{formatted_context}\n"
        )
        
        user_msg = f"User Query: {query}"
        
        full_prompt = f"{system_msg}\n\n{user_msg}"

        # 5. Execute LLM
        # We use the LightRAG instance's configured LLM function
        # Note: llm_model_func might be wrapped or expect specific kwargs
        try:
            response = await self.rag.llm_model_func(full_prompt)
        except Exception as e:
            logger.error(f"ACE Generator: LLM execution failed: {e}")
            return {"error": "LLM execution failed", "details": str(e)}

        return {
            "response": response,
            "context_data": context_data,
            "playbook_used": self.playbook.content.to_dict(),
            "trajectory": [{"step": "generation", "status": "Execution successful"}] 
        }

    def _format_context_data(self, data: Dict[str, Any]) -> str:
        """Formats structured context data into a readable string."""
        sections = []

        # Entities
        entities = data.get("entities", [])
        if entities:
            sections.append("#### Entities")
            for e in entities[:20]: # Limit for brevity in prototype
                sections.append(f"- {e.get('entity_name')} ({e.get('entity_type')}): {e.get('description')}")
        
        # Relationships
        relations = data.get("relationships", [])
        if relations:
            sections.append("\n#### Relationships")
            for r in relations[:20]:
                sections.append(f"- {r.get('src_id')} -> {r.get('tgt_id')}: {r.get('description')}")

        # Chunks
        chunks = data.get("chunks", [])
        if chunks:
            sections.append("\n#### Text Segments")
            for c in chunks[:5]: # Limit chunks
                sections.append(f"- ...{c.get('content')}...")

        return "\n".join(sections)
