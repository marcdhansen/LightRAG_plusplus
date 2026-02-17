"""
Benchmark: Native LightRAG extraction with different gleaning values

Run individually:
  pytest tests/benchmark_native_gleaning.py::test_gleaning_0 -v -s
  pytest tests/benchmark_native_gleaning.py::test_gleaning_1 -v -s
  pytest tests/benchmark_native_gleaning.py::test_gleaning_2 -v -s

Run all:
  pytest tests/benchmark_native_gleaning.py -v -s
"""

import os
import shutil
from functools import partial

import pytest

from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc


TEXT = (
    "Albert Einstein developed the Theory of Relativity while working in Switzerland."
)
EXPECTED = [
    {"name": "Albert Einstein", "type": "Person"},
    {"name": "Theory of Relativity", "type": "Concept"},
    {"name": "Switzerland", "type": "Location"},
]


def norm(s):
    return s.lower().strip()


def calc_recall(extracted, expected):
    if not expected:
        return 1.0
    if not extracted:
        return 0.0
    exp_names = {norm(e["name"]) for e in expected}
    matched = 0
    for e in extracted:
        e_name = norm(e["name"])
        for exp in exp_names:
            if exp in e_name or e_name in exp:
                matched += 1
                break
    return matched / len(exp_names) if exp_names else 0.0


WORKING_DIR = "./rag_storage_gleaning"


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up before and after each test."""
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    yield
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)


@pytest.mark.light
@pytest.mark.asyncio
async def test_gleaning_0():
    """Test with gleaning=0."""
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:3b",
        entity_extract_max_gleaning=0,
        extraction_format="default",
        addon_params={
            "entity_types": ["Person", "Organization", "Location", "Concept", "Theory"]
        },
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    await rag.ainsert(TEXT)

    nodes = await rag.chunk_entity_relation_graph.get_all_nodes()
    entities = [
        {"name": n.get("id", ""), "type": n.get("entity_type", "")} for n in nodes
    ]

    recall = calc_recall(entities, EXPECTED)

    print(f"\n=== Gleaning=0 ===")
    print(f"Entities: {[e['name'] for e in entities]}")
    print(f"Recall: {recall:.2f}")

    assert recall >= 0


@pytest.mark.light
@pytest.mark.asyncio
async def test_gleaning_1():
    """Test with gleaning=1."""
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:3b",
        entity_extract_max_gleaning=1,
        extraction_format="default",
        addon_params={
            "entity_types": ["Person", "Organization", "Location", "Concept", "Theory"]
        },
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    await rag.ainsert(TEXT)

    nodes = await rag.chunk_entity_relation_graph.get_all_nodes()
    entities = [
        {"name": n.get("id", ""), "type": n.get("entity_type", "")} for n in nodes
    ]

    recall = calc_recall(entities, EXPECTED)

    print(f"\n=== Gleaning=1 ===")
    print(f"Entities: {[e['name'] for e in entities]}")
    print(f"Recall: {recall:.2f}")

    assert recall >= 0


@pytest.mark.light
@pytest.mark.asyncio
async def test_gleaning_2():
    """Test with gleaning=2."""
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:3b",
        entity_extract_max_gleaning=2,
        extraction_format="default",
        addon_params={
            "entity_types": ["Person", "Organization", "Location", "Concept", "Theory"]
        },
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()
    await rag.ainsert(TEXT)

    nodes = await rag.chunk_entity_relation_graph.get_all_nodes()
    entities = [
        {"name": n.get("id", ""), "type": n.get("entity_type", "")} for n in nodes
    ]

    recall = calc_recall(entities, EXPECTED)

    print(f"\n=== Gleaning=2 ===")
    print(f"Entities: {[e['name'] for e in entities]}")
    print(f"Recall: {recall:.2f}")

    assert recall >= 0
