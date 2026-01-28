import pytest
import os
import shutil
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc

pytestmark = pytest.mark.heavy

# Use short-lived test directory
TEST_DIR = "test_ace_core_storage"


@pytest.fixture(autouse=True)
def setup_test_env():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


async def mock_llm_complete(prompt, system_prompt=None, **kwargs):
    # Handle keyword extraction during aquery_data
    if "high_level_keywords" in str(prompt):
        return '{"high_level_keywords": ["test"], "low_level_keywords": ["test"]}'

    # Determine if it's a generator or reflector call
    if "Context Playbook" in str(prompt) or (
        system_prompt and "Context Playbook" in str(system_prompt)
    ):
        return "This is an ACE generated response."
    elif "ACE Framework" in str(prompt) and "JSON" in str(prompt):
        return '["Insight 1", "Insight 2"]'
    return "Mocked response"


@pytest.mark.asyncio
async def test_ace_core_query_flow():
    import numpy as np

    async def mock_embed(texts):
        return np.array([[0.1] * 768 for _ in texts])

    # Initialize LightRAG with ACE enabled
    rag = LightRAG(
        working_dir=TEST_DIR,
        enable_ace=True,
        llm_model_func=mock_llm_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768, max_token_size=8192, func=mock_embed
        ),
    )

    # Wait for storage initialization if necessary
    await rag.initialize_storages()

    # Insert a dummy document to ensure retrieval works
    await rag.ainsert("LightRAG is a fast RAG system.")

    # Execute ACE query
    query = "What is LightRAG?"
    result = await rag.ace_query(query, auto_reflect=True)

    # Verify result structure
    assert "response" in result
    assert result["response"] == "This is an ACE generated response."
    assert "insights" in result
    assert len(result["insights"]) == 2
    assert "playbook_used" in result

    # Verify persistence
    playbook_file = os.path.join(TEST_DIR, "ace_data", "context_playbook.json")
    assert os.path.exists(playbook_file)

    await rag.finalize_storages()
