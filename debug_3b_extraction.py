import asyncio
import os
import shutil
from functools import partial
import pytest
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./rag_storage_debug_extraction"

async def test_extraction_3b():
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:3b",
        extraction_format="key_value",
        entity_extract_max_gleaning=0,
        addon_params={
            "entity_types": [
                "Person",
                "Location",
                "Organization",
                "Concept",
                "Theory",
                "Event",
            ]
        },
        llm_model_func=ollama_model_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )
    await rag.initialize_storages()

    text = (
        "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
        "He is best known for developing the Theory of Relativity."
    )
    
    await rag.ainsert(text)

    entities = await rag.chunk_entity_relation_graph.get_all_nodes()
    relations = await rag.chunk_entity_relation_graph.get_all_edges()
    
    print(f"\nExtracted Entities ({len(entities)}): {[e['id'] for e in entities]}")
    print(f"Extracted Relations ({len(relations)}): {relations}")

    expected_relations = [
        ("Albert Einstein", "Ulm"),
        ("Albert Einstein", "Germany"),
        ("Ulm", "Germany"),
        ("Albert Einstein", "Theory of Relativity")
    ]

    found_count = 0
    for src_exp, tgt_exp in expected_relations:
        found = False
        for rel in relations:
            src = rel["source"]
            tgt = rel["target"]
            if (src_exp.lower() in src.lower() and tgt_exp.lower() in tgt.lower()) or \
               (src_exp.lower() in tgt.lower() and tgt_exp.lower() in src.lower()):
                found = True
                break
        if found:
            found_count += 1
            print(f"✅ Found relation: {src_exp} <-> {tgt_exp}")
        else:
            print(f"❌ Missing relation: {src_exp} <-> {tgt_exp}")

    accuracy = (found_count / len(expected_relations)) * 100
    print(f"\nRelationship Accuracy: {accuracy}%")

if __name__ == "__main__":
    asyncio.run(test_extraction_3b())
