import pytest

from lightrag.ace.config import ACEConfig
from lightrag.ace.curator import ACECurator
from lightrag.ace.generator import ACEGenerator
from lightrag.ace.playbook import ContextPlaybook
from lightrag.ace.reflector import ACEReflector
from lightrag.core import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

pytestmark = pytest.mark.heavy

# Define the models to be used (must be pulled in Ollama)
LLM_MODEL = "qwen2.5-coder:1.5b"
EMBEDDING_MODEL = "nomic-embed-text:v1.5"
EMBEDDING_DIM = 768


@pytest.mark.asyncio
async def test_ace_live_integration(tmp_path):
    """
    Integration test for ACE components using live Ollama models.
    """
    working_dir = tmp_path / "lightrag_ace_test"
    working_dir.mkdir()

    # 1. Setup LightRAG
    async def llm_func(prompt, **kwargs):
        return await ollama_model_complete(prompt, **kwargs)

    # Embedding function wrapper
    async def embedding_implementation(texts):
        return await ollama_embed.func(texts, embed_model=EMBEDDING_MODEL)

    embedding_func = EmbeddingFunc(
        embedding_dim=EMBEDDING_DIM, max_token_size=8192, func=embedding_implementation
    )

    rag = LightRAG(
        working_dir=str(working_dir),
        llm_model_func=llm_func,
        llm_model_name=LLM_MODEL,
        embedding_func=embedding_func,
    )

    print("\n--- Initializing Storages ---")
    await rag.initialize_storages()

    print("--- Inserting Document ---")
    await rag.ainsert(
        "LightRAG is a Retrieval-Augmented Generation system. It uses knowledge graphs to structure information."
    )

    # 2. Setup ACE Components
    ace_dir = tmp_path / "ace_data"
    ace_config = ACEConfig(base_dir=str(ace_dir))
    playbook = ContextPlaybook(ace_config)

    generator = ACEGenerator(rag, playbook)
    reflector = ACEReflector(rag)
    curator = ACECurator(rag, playbook)

    # 3. Execute ACE Loop
    query = "What is LightRAG and how does it work?"

    print("\n--- ACE Generator ---")
    gen_result = await generator.generate(query)
    response = gen_result.get("response")
    print(f"Response: {response}")
    assert response is not None
    assert "LightRAG" in response

    print("\n--- ACE Reflector ---")
    insights = await reflector.reflect(query, gen_result)
    print(f"Insights: {insights}")
    assert isinstance(insights, list)
    assert len(insights) > 0

    print("\n--- ACE Curator ---")
    initial_lesson_count = len(playbook.content.lessons_learned)
    await curator.curate(insights)

    # 4. Verify Playbook Update
    assert len(playbook.content.lessons_learned) > initial_lesson_count
    print(f"New lessons count: {len(playbook.content.lessons_learned)}")

    # Verify persistence
    new_playbook = ContextPlaybook(ace_config)
    assert len(new_playbook.content.lessons_learned) == len(
        playbook.content.lessons_learned
    )

    print("\n--- Integration Test Success ---")
