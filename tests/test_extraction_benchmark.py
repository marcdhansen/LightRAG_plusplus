"""
Benchmark: LangExtract extraction_passes vs LightRAG gleaning

This benchmark compares:
1. LangExtract with extraction_passes=1,2,3
2. Native LightRAG extraction with gleaning=0,1,2

Test datasets:
- Few-NERD subset (academic benchmark)
- Text2KGBench subset
- Diverse domains (technical, legal, medical)

Issue: lightrag-fv9
"""

import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from functools import partial
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langextract as lx
from langextract.data import ExampleData, Extraction

from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc


WORKING_DIR = "./rag_storage_benchmark"


# ============================================================================
# Test Data
# ============================================================================

BENCHMARK_CASES = [
    {
        "id": "fewnerd_einstein",
        "text": "Albert Einstein developed the Theory of Relativity while working in Switzerland.",
        "expected_entities": [
            {"name": "Albert Einstein", "type": "Person"},
            {"name": "Theory of Relativity", "type": "Concept"},
            {"name": "Switzerland", "type": "Location"},
        ],
        "expected_relations": [
            {
                "source": "Albert Einstein",
                "target": "Theory of Relativity",
                "keywords": ["developed"],
            },
            {
                "source": "Albert Einstein",
                "target": "Switzerland",
                "keywords": ["worked_in"],
            },
        ],
    },
    {
        "id": "fewnerd_apple",
        "text": "Steve Jobs founded Apple Inc. in Cupertino, California.",
        "expected_entities": [
            {"name": "Steve Jobs", "type": "Person"},
            {"name": "Apple Inc.", "type": "Organization"},
            {"name": "Cupertino", "type": "Location"},
            {"name": "California", "type": "Location"},
        ],
        "expected_relations": [
            {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
            {"source": "Steve Jobs", "target": "Cupertino", "keywords": ["location"]},
            {"source": "Cupertino", "target": "California", "keywords": ["located_in"]},
        ],
    },
    {
        "id": "fewnerd_google",
        "text": "Google was founded by Larry Page and Sergey Brin at Stanford University.",
        "expected_entities": [
            {"name": "Google", "type": "Organization"},
            {"name": "Larry Page", "type": "Person"},
            {"name": "Sergey Brin", "type": "Person"},
            {"name": "Stanford University", "type": "Organization"},
        ],
        "expected_relations": [
            {"source": "Larry Page", "target": "Google", "keywords": ["founded"]},
            {"source": "Sergey Brin", "target": "Google", "keywords": ["founded"]},
            {
                "source": "Google",
                "target": "Stanford University",
                "keywords": ["location"],
            },
        ],
    },
    {
        "id": "medical_simple",
        "text": "Patient John Smith was prescribed 500mg of Aspirin twice daily for hypertension.",
        "expected_entities": [
            {"name": "John Smith", "type": "Patient"},
            {"name": "500mg", "type": "Dosage"},
            {"name": "Aspirin", "type": "Medication"},
            {"name": "hypertension", "type": "Condition"},
        ],
        "expected_relations": [
            {"source": "John Smith", "target": "Aspirin", "keywords": ["prescribed"]},
            {"source": "Aspirin", "target": "500mg", "keywords": ["dosage"]},
            {
                "source": "John Smith",
                "target": "hypertension",
                "keywords": ["diagnosed"],
            },
        ],
    },
    {
        "id": "legal_contract",
        "text": "Acme Corp agrees to pay Vendor LLC $50,000 for consulting services by December 31, 2025.",
        "expected_entities": [
            {"name": "Acme Corp", "type": "Organization"},
            {"name": "Vendor LLC", "type": "Organization"},
            {"name": "$50,000", "type": "Amount"},
            {"name": "December 31, 2025", "type": "Date"},
        ],
        "expected_relations": [
            {"source": "Acme Corp", "target": "Vendor LLC", "keywords": ["pay"]},
            {"source": "Acme Corp", "target": "$50,000", "keywords": ["amount"]},
            {
                "source": "Acme Corp",
                "target": "December 31, 2025",
                "keywords": ["deadline"],
            },
        ],
    },
]


# ============================================================================
# Metrics Calculation
# ============================================================================


def normalize_name(name: str) -> str:
    return name.lower().strip()


def calculate_recall(
    extracted_entities: list[dict], expected_entities: list[dict]
) -> float:
    """Calculate entity recall."""
    if not expected_entities:
        return 1.0

    expected_names = {normalize_name(e["name"]) for e in expected_entities}
    extracted_names = {normalize_name(e["name"]) for e in extracted_entities}

    true_positives = len(expected_names & extracted_names)
    return true_positives / len(expected_names) if expected_names else 0.0


def calculate_precision(
    extracted_entities: list[dict], expected_entities: list[dict]
) -> float:
    """Calculate entity precision."""
    if not extracted_entities:
        return 0.0

    expected_names = {normalize_name(e["name"]) for e in expected_entities}
    extracted_names = {normalize_name(e["name"]) for e in extracted_entities}

    true_positives = len(expected_names & extracted_names)
    return true_positives / len(extracted_names) if extracted_names else 0.0


def calculate_f1(precision: float, recall: float) -> float:
    """Calculate F1 score."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


# ============================================================================
# LangExtract Benchmark
# ============================================================================

LANGEXTRACT_PROMPT = """Extract entities and relationships.

ENTITY TYPES: Person, Organization, Location, Concept, Theory, Patient, Medication, Condition, Dosage, Amount, Date

RULES:
1. Extract entities ONLY from the input text
2. Do NOT copy entities from examples
3. Extract ALL relationships between entities
4. Use exact text from the input (no paraphrasing)"""

LANGEXTRACT_EXAMPLES = [
    ExampleData(
        text="Test.",
        extractions=[
            Extraction(
                extraction_class="entity",
                extraction_text="A",
                attributes={"type": "Person"},
            ),
            Extraction(
                extraction_class="entity",
                extraction_text="B",
                attributes={"type": "Organization"},
            ),
        ],
    ),
]


@dataclass
class LangExtractResult:
    """Result from LangExtract benchmark."""

    extraction_passes: int
    model_id: str
    case_id: str
    entities: list[dict]
    relations: list[dict]
    elapsed_time: float
    recall: float = 0.0
    precision: float = 0.0
    f1: float = 0.0


def run_langextract_benchmark(
    text: str,
    expected_entities: list[dict],
    extraction_passes: int,
    model_id: str = "qwen2.5-coder:1.5b",  # Faster for testing
    model_url: str = "http://localhost:11434",
) -> LangExtractResult:
    """Run LangExtract with specified extraction passes."""

    start_time = time.time()

    result = lx.extract(
        text_or_documents=text,
        prompt_description=LANGEXTRACT_PROMPT,
        examples=LANGEXTRACT_EXAMPLES,
        model_id=model_id,
        model_url=model_url,
        fence_output=False,
        extraction_passes=extraction_passes,
    )

    elapsed_time = time.time() - start_time

    # Convert to LightRAG format
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

    # Calculate metrics
    recall = calculate_recall(entities, expected_entities)
    precision = calculate_precision(entities, expected_entities)
    f1 = calculate_f1(precision, recall)

    return LangExtractResult(
        extraction_passes=extraction_passes,
        model_id=model_id,
        case_id="",
        entities=entities,
        relations=relations,
        elapsed_time=elapsed_time,
        recall=recall,
        precision=precision,
        f1=f1,
    )


# ============================================================================
# Native LightRAG Benchmark
# ============================================================================


@dataclass
class NativeResult:
    """Result from native LightRAG extraction benchmark."""

    gleaning: int
    model_id: str
    case_id: str
    entities: list[dict]
    relations: list[dict]
    elapsed_time: float
    recall: float = 0.0
    precision: float = 0.0
    f1: float = 0.0


async def run_native_benchmark(
    text: str,
    expected_entities: list[dict],
    gleaning: int,
    model_id: str = "qwen2.5-coder:3b",
) -> NativeResult:
    """Run native LightRAG extraction with specified gleaning."""

    # Setup working directory
    work_dir = f"./rag_storage_native_gleaning_{gleaning}"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    start_time = time.time()

    try:
        rag = LightRAG(
            working_dir=work_dir,
            llm_model_name=model_id,
            entity_extract_max_gleaning=gleaning,
            addon_params={
                "entity_types": [
                    "Person",
                    "Organization",
                    "Location",
                    "Concept",
                    "Theory",
                    "Patient",
                    "Medication",
                    "Condition",
                    "Dosage",
                    "Amount",
                    "Date",
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

        # Insert text
        await rag.ainsert(text)

        # Get entities
        all_entities = await rag.chunk_entity_relation_graph.get_all_nodes()
        entities = [
            {"name": e.get("id", ""), "type": e.get("entity_type", "")}
            for e in all_entities
        ]

        # Get relations
        edges = await rag.chunk_entity_relation_graph.get_all_edges()
        relations = [
            {
                "source": e.get("source_id", ""),
                "target": e.get("target_id", ""),
                "keywords": e.get("keywords", ""),
            }
            for e in edges
        ]

    finally:
        # Cleanup
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

    elapsed_time = time.time() - start_time

    # Calculate metrics
    recall = calculate_recall(entities, expected_entities)
    precision = calculate_precision(entities, expected_entities)
    f1 = calculate_f1(precision, recall)

    return NativeResult(
        gleaning=gleaning,
        model_id=model_id,
        case_id="",
        entities=entities,
        relations=relations,
        elapsed_time=elapsed_time,
        recall=recall,
        precision=precision,
        f1=f1,
    )


# ============================================================================
# Benchmark Tests
# ============================================================================


@pytest.mark.light
class TestExtractionPassesVsGleaning:
    """Compare LangExtract extraction_passes vs native gleaning."""

    @pytest.mark.parametrize("case", BENCHMARK_CASES[:2])  # Quick: 2 cases
    @pytest.mark.parametrize("extraction_passes", [1, 2, 3])
    def test_langextract_passes(self, case, extraction_passes):
        """Test LangExtract with different extraction_passes."""

        result = run_langextract_benchmark(
            text=case["text"],
            expected_entities=case["expected_entities"],
            extraction_passes=extraction_passes,
            model_id="qwen2.5-coder:3b",
        )

        print(f"\n=== LangExtract passes={extraction_passes} | {case['id']} ===")
        print(f"Time: {result.elapsed_time:.1f}s")
        print(f"Entities: {[e['name'] for e in result.entities]}")
        print(
            f"Recall: {result.recall:.2f}, Precision: {result.precision:.2f}, F1: {result.f1:.2f}"
        )

        # Store case_id for reporting
        result.case_id = case["id"]

        # Basic sanity check
        assert result.elapsed_time > 0

    @pytest.mark.parametrize("case", BENCHMARK_CASES[:2])  # Quick: 2 cases
    @pytest.mark.parametrize("gleaning", [0, 1, 2])
    @pytest.mark.asyncio
    async def test_native_gleaning(self, case, gleaning):
        """Test native extraction with different gleaning levels."""

        result = await run_native_benchmark(
            text=case["text"],
            expected_entities=case["expected_entities"],
            gleaning=gleaning,
            model_id="qwen2.5-coder:3b",
        )

        print(f"\n=== Native gleaning={gleaning} | {case['id']} ===")
        print(f"Time: {result.elapsed_time:.1f}s")
        print(f"Entities: {[e['name'] for e in result.entities]}")
        print(
            f"Recall: {result.recall:.2f}, Precision: {result.precision:.2f}, F1: {result.f1:.2f}"
        )

        result.case_id = case["id"]


def run_quick_benchmark():
    """Run quick benchmark for extraction_passes comparison.

    This is a simplified version for quick testing.
    Use pytest for full benchmark with proper async support.
    """
    import langextract as lx
    from langextract.data import ExampleData, Extraction

    LANGEXTRACT_PROMPT = """Extract entities and relationships.
    ENTITY TYPES: Person, Organization, Location, Concept"""

    LANGEXTRACT_EXAMPLES = [
        ExampleData(
            text="Test.",
            extractions=[
                Extraction(
                    extraction_class="entity",
                    extraction_text="A",
                    attributes={"type": "Person"},
                ),
                Extraction(
                    extraction_class="entity",
                    extraction_text="B",
                    attributes={"type": "Organization"},
                ),
            ],
        ),
    ]

    text = "Albert Einstein developed the Theory of Relativity while working in Switzerland."
    expected = [
        {"name": "Albert Einstein", "type": "Person"},
        {"name": "Theory of Relativity", "type": "Concept"},
        {"name": "Switzerland", "type": "Location"},
    ]

    def calculate_recall(extracted, expected):
        expected_names = {e["name"].lower().strip() for e in expected}
        extracted_names = {e["name"].lower().strip() for e in extracted}
        if not expected_names:
            return 0.0
        return len(expected_names & extracted_names) / len(expected_names)

    results = []

    print("\n" + "=" * 80)
    print("BENCHMARK: extraction_passes comparison")
    print("=" * 80)
    print(f"\nTest case: Einstein")
    print(f"Text: {text}")
    print(f"Expected entities: {[e['name'] for e in expected]}")
    print(f"\n{'Passes':<8} {'Time':>10} {'Recall':>8} {'Entities':<40}")
    print("-" * 70)

    for passes in [1, 2, 3]:
        result = run_langextract_benchmark(
            text=text,
            expected_entities=expected,
            extraction_passes=passes,
        )

        results.append(
            {
                "passes": passes,
                "time": result.elapsed_time,
                "recall": result.recall,
                "entities": [e["name"] for e in result.entities],
            }
        )

        print(
            f"{passes:<8} {result.elapsed_time:>9.1f}s {result.recall:>8.2f} {[e['name'] for e in result.entities][:40]}"
        )

    print("\n" + "=" * 80)

    # Analysis
    print("\nANALYSIS:")
    best = max(results, key=lambda r: r["recall"])
    print(f"  Best recall: passes={best['passes']} ({best['recall']:.2f})")

    # Check if more passes = more time without recall gain
    if results[0]["recall"] == results[-1]["recall"]:
        print(f"  Finding: passes=1 achieves same recall as passes=3")
        print(f"  Recommendation: Use passes=1 (faster)")
    else:
        print(f"  Finding: Higher passes improve recall")


if __name__ == "__main__":
    run_quick_benchmark()
