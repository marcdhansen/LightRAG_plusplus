#!/usr/bin/env python3
"""Full comparison: LangExtract vs LightRAG with refined examples"""

import asyncio
import os
import shutil
import sys
import time
from functools import partial

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langextract as lx
from langextract.data import ExampleData, Extraction

from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./rag_storage_test"

TEST_CASES = [
    {
        "id": "naive_case",
        "text": "Steve Jobs founded Apple.",
        "expected_entities": [
            {"name": "Apple", "type": "Organization"},
            {"name": "Steve Jobs", "type": "Person"},
        ],
        "expected_relations": [
            {"source": "Steve Jobs", "target": "Apple", "keywords": ["founded"]}
        ],
    },
    {
        "id": "einstein_basic",
        "text": (
            "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
            "He is best known for developing the Theory of Relativity."
        ),
        "expected_entities": [
            {"name": "Albert Einstein", "type": "Person"},
            {"name": "Ulm", "type": "Location"},
            {"name": "Germany", "type": "Location"},
            {"name": "Theory of Relativity", "type": "Theory"},
        ],
        "expected_relations": [
            {"source": "Albert Einstein", "target": "Ulm", "keywords": ["born"]},
            {"source": "Albert Einstein", "target": "Germany", "keywords": ["born"]},
            {"source": "Ulm", "target": "Germany", "keywords": ["located", "in"]},
            {
                "source": "Albert Einstein",
                "target": "Theory of Relativity",
                "keywords": ["developed", "developing"],
            },
        ],
    },
]


def normalize_name(name: str) -> str:
    return name.lower().strip()


def extract_entities_langextract(text: str, model_id: str = "qwen2.5-coder:3b") -> dict:
    """LangExtract with refined examples"""

    prompt = """Extract entities and relationships.

ENTITY TYPES: Person, Location, Organization, Concept, Theory

CRITICAL RULES:
1. Extract each location SEPARATELY - "Ulm, Germany" means Ulm AND Germany (NOT combined)
2. Extract CONCEPTS and THEORIES exactly as named - e.g., "Theory of Relativity" is a Theory
3. Create ALL relationships between entities"""

    examples = [
        ExampleData(
            text="Steve Jobs founded Apple.",
            extractions=[
                Extraction(
                    extraction_class="entity",
                    extraction_text="Steve Jobs",
                    attributes={"type": "Person"},
                ),
                Extraction(
                    extraction_class="entity",
                    extraction_text="Apple",
                    attributes={"type": "Organization"},
                ),
                Extraction(
                    extraction_class="relationship",
                    extraction_text="Steve Jobs founded Apple",
                    attributes={
                        "source": "Steve Jobs",
                        "target": "Apple",
                        "keywords": "founded",
                    },
                ),
            ],
        ),
        ExampleData(
            text="Albert Einstein was born in Ulm, Germany.",
            extractions=[
                Extraction(
                    extraction_class="entity",
                    extraction_text="Albert Einstein",
                    attributes={"type": "Person"},
                ),
                Extraction(
                    extraction_class="entity",
                    extraction_text="Ulm",
                    attributes={"type": "Location"},
                ),
                Extraction(
                    extraction_class="entity",
                    extraction_text="Germany",
                    attributes={"type": "Location"},
                ),
                Extraction(
                    extraction_class="relationship",
                    extraction_text="Einstein born in Ulm",
                    attributes={
                        "source": "Albert Einstein",
                        "target": "Ulm",
                        "keywords": "born in",
                    },
                ),
                Extraction(
                    extraction_class="relationship",
                    extraction_text="Einstein born in Germany",
                    attributes={
                        "source": "Albert Einstein",
                        "target": "Germany",
                        "keywords": "born in",
                    },
                ),
                Extraction(
                    extraction_class="relationship",
                    extraction_text="Ulm in Germany",
                    attributes={
                        "source": "Ulm",
                        "target": "Germany",
                        "keywords": "located in",
                    },
                ),
            ],
        ),
        ExampleData(
            text="Newton developed the Theory of Gravity.",
            extractions=[
                Extraction(
                    extraction_class="entity",
                    extraction_text="Newton",
                    attributes={"type": "Person"},
                ),
                Extraction(
                    extraction_class="entity",
                    extraction_text="Theory of Gravity",
                    attributes={"type": "Theory"},
                ),
                Extraction(
                    extraction_class="relationship",
                    extraction_text="Newton developed Theory of Gravity",
                    attributes={
                        "source": "Newton",
                        "target": "Theory of Gravity",
                        "keywords": "developed",
                    },
                ),
            ],
        ),
    ]

    start_time = time.time()
    result = lx.extract(
        text_or_documents=text,
        prompt_description=prompt,
        examples=examples,
        model_id=model_id,
        model_url="http://localhost:11434",
        fence_output=False,
        use_schema_constraints=False,
        max_char_buffer=500,
    )
    elapsed = time.time() - start_time

    entities = []
    relations = []
    for ext in result.extractions:
        if ext.extraction_class == "entity":
            entities.append(
                {
                    "name": ext.extraction_text,
                    "type": ext.attributes.get("type", "Unknown"),
                }
            )
        elif ext.extraction_class == "relationship":
            relations.append(
                {
                    "source": ext.attributes.get("source", ""),
                    "target": ext.attributes.get("target", ""),
                    "keywords": ext.attributes.get("keywords", ""),
                }
            )

    return {"entities": entities, "relations": relations, "elapsed_time": elapsed}


async def extract_entities_lightrag(
    text: str, model_name: str = "qwen2.5-coder:3b"
) -> dict:
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name=model_name,
        extraction_format="default",
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

    start_time = time.time()
    await rag.ainsert(text)
    elapsed = time.time() - start_time

    all_entities = await rag.chunk_entity_relation_graph.get_all_nodes()
    entities = [
        {"name": e.get("id", ""), "type": e.get("entity_type", "")}
        for e in all_entities
    ]

    edges = await rag.chunk_entity_relation_graph.get_all_edges()
    relations = [
        {
            "source": e.get("source_id", ""),
            "target": e.get("target_id", ""),
            "keywords": e.get("keywords", ""),
        }
        for e in edges
    ]

    return {"entities": entities, "relations": relations, "elapsed_time": elapsed}


def evaluate(extracted: dict, expected: dict) -> dict:
    extracted_names = {normalize_name(e["name"]) for e in extracted.get("entities", [])}
    expected_names = {
        normalize_name(e["name"]) for e in expected.get("expected_entities", [])
    }
    entity_recall = (
        len(extracted_names & expected_names) / len(expected_names)
        if expected_names
        else 0
    )

    extracted_relations = extracted.get("relations", [])
    expected_relations = expected.get("expected_relations", [])
    matched = 0
    for exp_rel in expected_relations:
        src, tgt = normalize_name(exp_rel["source"]), normalize_name(exp_rel["target"])
        for ext_rel in extracted_relations:
            ext_src, ext_tgt = (
                normalize_name(ext_rel.get("source", "")),
                normalize_name(ext_rel.get("target", "")),
            )
            if (src in ext_src or ext_src in src) and (
                tgt in ext_tgt or ext_tgt in tgt
            ):
                matched += 1
                break
    relation_accuracy = matched / len(expected_relations) if expected_relations else 0

    return {"entity_recall": entity_recall, "relation_accuracy": relation_accuracy}


async def run_comparison():
    print("=" * 70)
    print("LangExtract vs LightRAG - Full Comparison")
    print("Model: qwen2.5-coder:3b")
    print("=" * 70)

    results = []

    for case in TEST_CASES:
        case_id = case["id"]
        text = case["text"]

        print(f"\n{'=' * 70}")
        print(f"TEST CASE: {case_id}")
        print(f"{'=' * 70}")

        # LangExtract
        print("\n--- LangExtract ---")
        le_result = extract_entities_langextract(text)
        print(f"Entities: {[e['name'] for e in le_result['entities']]}")
        print(
            f"Relations: {[(r['source'], r['target']) for r in le_result['relations']]}"
        )
        le_eval = evaluate(le_result, case)
        print(f"Entity Recall: {le_eval['entity_recall'] * 100:.0f}%")
        print(f"Relation Accuracy: {le_eval['relation_accuracy'] * 100:.0f}%")
        print(f"Time: {le_result['elapsed_time']:.1f}s")

        # LightRAG
        print("\n--- LightRAG ---")
        try:
            lr_result = await extract_entities_lightrag(text)
            print(f"Entities: {[e['name'] for e in lr_result['entities']]}")
            print(
                f"Relations: {[(r['source'], r['target']) for r in lr_result['relations']]}"
            )
            lr_eval = evaluate(lr_result, case)
            print(f"Entity Recall: {lr_eval['entity_recall'] * 100:.0f}%")
            print(f"Relation Accuracy: {lr_eval['relation_accuracy'] * 100:.0f}%")
            print(f"Time: {lr_result['elapsed_time']:.1f}s")
        except Exception as e:
            print(f"ERROR: {e}")
            lr_eval = {"entity_recall": 0, "relation_accuracy": 0}

        results.append(
            {"case_id": case_id, "langextract": le_eval, "lightrag": lr_eval}
        )

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(
        f"{'Case':<20} {'LE Recall':>10} {'LR Recall':>10} {'LE RelAcc':>10} {'LR RelAcc':>10}"
    )
    print("-" * 70)
    for r in results:
        print(
            f"{r['case_id']:<20} {r['langextract']['entity_recall'] * 100:>9.0f}% {r['lightrag']['entity_recall'] * 100:>9.0f}% {r['langextract']['relation_accuracy'] * 100:>9.0f}% {r['lightrag']['relation_accuracy'] * 100:>9.0f}%"
        )

    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)

    return results


if __name__ == "__main__":
    asyncio.run(run_comparison())
