import asyncio
import os
import pytest
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from functools import partial

WORKING_DIR = "./rag_storage_gold_standard"


@pytest.fixture(scope="function")
async def gold_rag():
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:1.5b",
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    return rag


@pytest.mark.asyncio
async def test_gold_standard_extraction(gold_rag):
    """
    Gold Standard Extraction Test:
    Verify that the system correctly identifies specific entities and relationships
    from a controlled, unambiguous text.
    """
    rag = gold_rag

    text = (
        "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
        "He is best known for developing the Theory of Relativity, which revolutionized physics. "
        "Einstein won the Nobel Prize in Physics in 1921."
    )

    # 1. Ingest
    await rag.ainsert(text)

    # 2. Check Entities
    entities = await rag.chunk_entity_relation_graph.get_all_nodes()
    entity_names = [e["id"] for e in entities]

    print(f"\nExtracted Entities: {entity_names}")

    # Check for Albert Einstein
    assert any(
        "EINSTEIN" in name.upper() for name in entity_names
    ), "Missing Albert Einstein"
    # Check for Germany
    assert any("GERMANY" in name.upper() for name in entity_names), "Missing Germany"
    # Check for Relativity
    assert any(
        "RELATIVITY" in name.upper() for name in entity_names
    ), f"Missing Relativity in {entity_names}"

    # 3. Check Relationships
    ae_name = next(name for name in entity_names if "EINSTEIN" in name.upper())
    germany_name = next(name for name in entity_names if "GERMANY" in name.upper())
    relativity_name = next(
        name for name in entity_names if "RELATIVITY" in name.upper()
    )

    # Verify Relationship: Einstein -> Germany
    exists_germany = await rag.chunk_entity_relation_graph.has_edge(
        ae_name, germany_name
    )
    assert exists_germany, f"Missing relationship between {ae_name} and {germany_name}"

    # Verify Relationship: Einstein -> Relativity
    exists_relativity = await rag.chunk_entity_relation_graph.has_edge(
        ae_name, relativity_name
    )
    assert (
        exists_relativity
    ), f"Missing relationship between {ae_name} and {relativity_name}"


if __name__ == "__main__":
    asyncio.run(test_gold_standard_extraction(None))
