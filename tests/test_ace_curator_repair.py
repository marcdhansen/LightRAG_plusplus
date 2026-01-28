import asyncio
import pytest
from unittest.mock import AsyncMock
from lightrag import LightRAG


@pytest.mark.asyncio
async def test_ace_curator_merge_logic():
    # Mock dependencies
    async def dummy_embed(texts):
        import numpy as np

        return np.zeros((len(texts), 1536))

    from lightrag.utils import EmbeddingFunc

    mock_embed = EmbeddingFunc(
        embedding_dim=1536, func=dummy_embed, max_token_size=8192
    )

    async def dummy_llm(prompt, **kwargs):
        return "[]"

    # Mock RAG instance
    rag = LightRAG(
        working_dir="./test_ace_curator",
        llm_model_func=dummy_llm,
        llm_model_name="test-model",
        embedding_func=mock_embed,
        enable_ace=True,
    )

    # Mock the LLM functions
    # 1. Generator returns a response
    # 2. Reflector (General) returns insights
    # 3. Reflector (Graph) returns a merge recommendation

    mock_gen_response = {
        "response": "AI is a field of computer science. Artificial Intelligence is great.",
        "context_data": {
            "entities": [
                {
                    "entity_name": "AI",
                    "entity_type": "ORGANIZATION",
                    "description": "Short for Artificial Intelligence",
                },
                {
                    "entity_name": "Artificial Intelligence",
                    "entity_type": "TECHNOLOGY",
                    "description": "Human-like intelligence in machines",
                },
            ],
            "relationships": [],
            "chunks": [
                {"content": "AI and Artificial Intelligence are the same thing."}
            ],
        },
    }

    # Mock Generator.generate
    rag.ace_generator.generate = AsyncMock(return_value=mock_gen_response)

    # Mock Reflector.reflect
    rag.ace_reflector.reflect = AsyncMock(
        return_value=["Insight: Deduplicate AI terms"]
    )

    # Mock Reflector.reflect_graph_issues to return a merge action
    repair_action = {
        "action": "merge_entities",
        "sources": ["AI"],
        "target": "Artificial Intelligence",
        "reason": "They refer to the same concept.",
    }
    rag.ace_reflector.reflect_graph_issues = AsyncMock(return_value=[repair_action])

    # Mock Curators
    rag.ace_curator.curate = AsyncMock()
    rag.ace_curator.apply_repairs = AsyncMock()

    # Trigger ace_query
    result = await rag.ace_query("Tell me about AI", auto_reflect=True)

    # Verify repairs were applied
    rag.ace_curator.apply_repairs.assert_called_once_with([repair_action])
    assert result["repairs_applied"] == [repair_action]


@pytest.mark.asyncio
async def test_curator_apply_repairs_execution():
    # This test verifies that ace_curator.apply_repairs actually calls rag.amerge_entities
    async def dummy_embed(texts):
        import numpy as np

        return np.zeros((len(texts), 1536))

    from lightrag.utils import EmbeddingFunc

    mock_embed = EmbeddingFunc(
        embedding_dim=1536, func=dummy_embed, max_token_size=8192
    )

    async def dummy_llm(prompt, **kwargs):
        return "[]"

    rag = LightRAG(
        working_dir="./test_ace_curator_exec",
        llm_model_func=dummy_llm,
        llm_model_name="test-model",
        embedding_func=mock_embed,
        enable_ace=True,
    )

    # Mock the core RAG methods
    rag.adelete_relation = AsyncMock()
    rag.adelete_entity = AsyncMock()
    rag.amerge_entities = AsyncMock()

    repairs = [
        {
            "action": "delete_relation",
            "source": "A",
            "target": "B",
            "reason": "Hallucination",
        },
        {"action": "delete_entity", "name": "C", "reason": "Not in text"},
        {
            "action": "merge_entities",
            "sources": ["D"],
            "target": "E",
            "reason": "Duplicate",
        },
    ]

    await rag.ace_curator.apply_repairs(repairs)

    rag.adelete_relation.assert_called_once_with("A", "B")
    rag.adelete_entity.assert_called_once_with("C")
    rag.amerge_entities.assert_called_once()

    # Check amerge_entities arguments
    args, kwargs = rag.amerge_entities.call_args
    assert kwargs["source_entities"] == ["D"]
    assert kwargs["target_entity"] == "E"


if __name__ == "__main__":
    asyncio.run(test_ace_curator_merge_logic())
    asyncio.run(test_curator_apply_repairs_execution())
    print("ACE Curator tests passed!")
