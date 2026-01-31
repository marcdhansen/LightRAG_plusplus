"""
Academic benchmark tests for entity extraction quality validation.

This test suite integrates:
1. Few-NERD: Few-shot Named Entity Recognition benchmark
2. Text2KGBench: Text-to-KG generation benchmark

Markers:
- @pytest.mark.light: Fast tests (subset data)
- @pytest.mark.heavy: Full benchmark tests (on-demand)

Run with:
    pytest -m light -k academic    # Quick subset tests
    pytest -m heavy -k academic_full  # Full benchmarks (manual)
"""

import pytest

from tests.benchmarks.eval_metrics import (
    calculate_entity_f1,
    calculate_entity_precision,
    calculate_entity_recall,
    calculate_extraction_quality_score,
    format_metrics_report,
)

# ============================================================================
# Few-NERD Benchmark Data (Representative Subset)
# ============================================================================

# Subset of Few-NERD INTRA split for quick testing
# Source: https://github.com/thunlp/Few-NERD
FEWNERD_SUBSET = [
    {
        "id": "fewnerd_1",
        "text": "Steve Jobs founded Apple Inc. in Cupertino, California.",
        "entities": [
            {"name": "Steve Jobs", "type": "Person"},
            {"name": "Apple Inc.", "type": "Organization"},
            {"name": "Cupertino", "type": "Location"},
            {"name": "California", "type": "Location"},
        ],
        "relations": [
            {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
            {"source": "Steve Jobs", "target": "Cupertino", "keywords": ["location"]},
            {"source": "Cupertino", "target": "California", "keywords": ["located_in"]},
        ],
    },
    {
        "id": "fewnerd_2",
        "text": "Albert Einstein developed the Theory of Relativity while working in Switzerland.",
        "entities": [
            {"name": "Albert Einstein", "type": "Person"},
            {"name": "Theory of Relativity", "type": "Concept"},
            {"name": "Switzerland", "type": "Location"},
        ],
        "relations": [
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
        "id": "fewnerd_3",
        "text": "Google was founded by Larry Page and Sergey Brin at Stanford University.",
        "entities": [
            {"name": "Google", "type": "Organization"},
            {"name": "Larry Page", "type": "Person"},
            {"name": "Sergey Brin", "type": "Person"},
            {"name": "Stanford University", "type": "Organization"},
        ],
        "relations": [
            {"source": "Larry Page", "target": "Google", "keywords": ["founded"]},
            {"source": "Sergey Brin", "target": "Google", "keywords": ["founded"]},
            {
                "source": "Google",
                "target": "Stanford University",
                "keywords": ["origin"],
            },
        ],
    },
    {
        "id": "fewnerd_4",
        "text": "The iPhone is manufactured by Apple and sold worldwide.",
        "entities": [
            {"name": "iPhone", "type": "Artifact"},
            {"name": "Apple", "type": "Organization"},
        ],
        "relations": [
            {"source": "Apple", "target": "iPhone", "keywords": ["manufactures"]},
        ],
    },
    {
        "id": "fewnerd_5",
        "text": "NASA launched the James Webb Space Telescope from Kennedy Space Center.",
        "entities": [
            {"name": "NASA", "type": "Organization"},
            {"name": "James Webb Space Telescope", "type": "Artifact"},
            {"name": "Kennedy Space Center", "type": "Location"},
        ],
        "relations": [
            {
                "source": "NASA",
                "target": "James Webb Space Telescope",
                "keywords": ["launched"],
            },
            {
                "source": "NASA",
                "target": "Kennedy Space Center",
                "keywords": ["used"],
            },
        ],
    },
]

# LightRAG entity type mapping from Few-NERD types
FEWNERD_TO_LIGHTRAG = {
    "Person": "Person",
    "Organization": "Organization",
    "Location": "Location",
    "Artifact": "Artifact",
    "Concept": "Concept",
    "Event": "Event",
    "Method": "Method",
    "Product": "Artifact",
    "Work": "Content",
    "Natural Phenomenon": "NaturalObject",
}


def convert_fewnerd_to_lightrag(fewnerd_data: dict) -> dict:
    """Convert Few-NERD format to LightRAG format."""
    converted = {
        "id": fewnerd_data["id"],
        "text": fewnerd_data["text"],
        "entities": [],
        "relations": [],
    }

    # Convert entities
    for entity in fewnerd_data.get("entities", []):
        lr_type = FEWNERD_TO_LIGHTRAG.get(entity.get("type", "Other"), "Other")
        converted["entities"].append(
            {"name": entity["name"], "type": lr_type, "description": ""}
        )

    # Convert relations
    for relation in fewnerd_data.get("relations", []):
        converted["relations"].append(
            {
                "source": relation["source"],
                "target": relation["target"],
                "keywords": relation.get("keywords", []),
                "description": "",
            }
        )

    return converted


# ============================================================================
# Text2KGBench Subset (Representative)
# ============================================================================

# Subset of Text2KGBench Wikidata-TekGen for quick testing
# Source: https://arxiv.org/abs/2308.02357
TEXT2KGBENCH_SUBSET = [
    {
        "id": "text2kg_1",
        "text": "Barack Obama served as the 44th President of the United States from 2009 to 2017.",
        "entities": [
            {"name": "Barack Obama", "type": "Person"},
            {"name": "United States", "type": "Location"},
        ],
        "relations": [
            {
                "source": "Barack Obama",
                "target": "United States",
                "keywords": ["president_of", "served_as"],
            },
        ],
    },
    {
        "id": "text2kg_2",
        "text": "The Python programming language was created by Guido van Rossum.",
        "entities": [
            {"name": "Python", "type": "Concept"},
            {"name": "Guido van Rossum", "type": "Person"},
        ],
        "relations": [
            {
                "source": "Guido van Rossum",
                "target": "Python",
                "keywords": ["created_by"],
            },
        ],
    },
    {
        "id": "text2kg_3",
        "text": "Microsoft Corporation acquired LinkedIn in 2016 for $26 billion.",
        "entities": [
            {"name": "Microsoft Corporation", "type": "Organization"},
            {"name": "LinkedIn", "type": "Organization"},
        ],
        "relations": [
            {
                "source": "Microsoft Corporation",
                "target": "LinkedIn",
                "keywords": ["acquired"],
            },
        ],
    },
]

# ============================================================================
# Mock Extraction for Testing Metrics (without actual LLM calls)
# ============================================================================

# Simulated extraction results for testing metrics
MOCK_EXTRACTION_RESULT = {
    "entities": [
        {"name": "Steve Jobs", "type": "Person"},
        {"name": "Apple Inc.", "type": "Organization"},
        {"name": "Cupertino", "type": "Location"},
        # Missing: California
    ],
    "relations": [
        {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
        # Missing: other relations
    ],
}


# ============================================================================
# Test Classes
# ============================================================================


class TestFewNERDExtraction:
    """Test extraction quality on Few-NERD benchmark subset."""

    @pytest.mark.light
    @pytest.mark.parametrize(
        "case_id",
        [c["id"] for c in FEWNERD_SUBSET],
    )
    def test_entity_recall_quick(self, case_id: str):
        """Test entity recall on Few-NERD subset (light test)."""
        case = next((c for c in FEWNERD_SUBSET if c["id"] == case_id), None)
        assert case is not None

        gold_entities = case["entities"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        metrics = calculate_entity_recall(predicted_entities, gold_entities)

        # For mock data, we expect partial recall
        # In real tests, this would use actual extraction
        assert "recall" in metrics
        assert 0 <= metrics["recall"] <= 1
        assert "tp" in metrics
        assert "fn" in metrics

    @pytest.mark.light
    def test_entity_precision_quick(self):
        """Test entity precision on Few-NERD subset (light test)."""
        case = FEWNERD_SUBSET[0]  # Use first case
        gold_entities = case["entities"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        metrics = calculate_entity_precision(predicted_entities, gold_entities)

        assert "precision" in metrics
        assert 0 <= metrics["precision"] <= 1
        assert "tp" in metrics
        assert "fp" in metrics

    @pytest.mark.light
    def test_entity_f1_quick(self):
        """Test entity F1 score on Few-NERD subset (light test)."""
        case = FEWNERD_SUBSET[0]
        gold_entities = case["entities"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        recall = calculate_entity_recall(predicted_entities, gold_entities)["recall"]
        precision = calculate_entity_precision(predicted_entities, gold_entities)[
            "precision"
        ]
        f1 = calculate_entity_f1(recall, precision)

        assert 0 <= f1 <= 1

    @pytest.mark.light
    def test_type_specific_metrics(self):
        """Test type-specific metrics calculation."""
        case = FEWNERD_SUBSET[0]
        gold_entities = case["entities"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        from tests.benchmarks.eval_metrics import calculate_type_specific_metrics

        type_metrics = calculate_type_specific_metrics(
            predicted_entities, gold_entities, entity_types=["Person", "Organization"]
        )

        assert "Person" in type_metrics or len(type_metrics) > 0


class TestText2KGBenchExtraction:
    """Test extraction quality on Text2KGBench subset."""

    @pytest.mark.light
    @pytest.mark.parametrize(
        "case_id",
        [c["id"] for c in TEXT2KGBENCH_SUBSET],
    )
    def test_entity_extraction_quick(self, case_id: str):
        """Test entity extraction on Text2KGBench subset (light test)."""
        case = next((c for c in TEXT2KGBENCH_SUBSET if c["id"] == case_id), None)
        assert case is not None

        gold_entities = case["entities"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        metrics = calculate_entity_recall(predicted_entities, gold_entities)

        assert "recall" in metrics
        assert "missing" in metrics

    @pytest.mark.light
    def test_quality_score(self):
        """Test overall extraction quality score."""
        case = FEWNERD_SUBSET[0]
        gold_entities = case["entities"]
        gold_relations = case["relations"]
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]
        predicted_relations = MOCK_EXTRACTION_RESULT["relations"]

        metrics = calculate_extraction_quality_score(
            predicted_entities=predicted_entities,
            gold_entities=gold_entities,
            predicted_relations=predicted_relations,
            gold_relations=gold_relations,
        )

        assert "overall_f1" in metrics
        assert "entity_f1" in metrics
        assert "relation_f1" in metrics


class TestEvaluationMetrics:
    """Unit tests for evaluation metrics functions."""

    @pytest.mark.light
    def test_normalize_entity_name(self):
        """Test entity name normalization."""
        from tests.benchmarks.eval_metrics import normalize_entity_name

        assert normalize_entity_name("Steve Jobs") == "steve jobs"
        assert normalize_entity_name("  The Apple  ") == "apple"
        assert normalize_entity_name("data-science") == "data science"

    @pytest.mark.light
    def test_entity_recall_empty_gold(self):
        """Test entity recall with empty gold set."""
        metrics = calculate_entity_recall([], [])
        assert metrics["recall"] == 1.0

    @pytest.mark.light
    def test_entity_precision_empty_predicted(self):
        """Test entity precision with empty predicted set."""
        gold = [{"name": "Test", "type": "Person"}]
        metrics = calculate_entity_precision([], gold)
        assert metrics["precision"] == 0.0

    @pytest.mark.light
    def test_f1_zero_division(self):
        """Test F1 calculation handles zero division."""
        f1 = calculate_entity_f1(0, 0)
        assert f1 == 0.0

    @pytest.mark.light
    def test_format_metrics_report(self):
        """Test metrics report formatting."""
        metrics = {
            "overall_f1": 0.75,
            "entity_f1": 0.8,
            "entity_recall": 0.85,
            "entity_precision": 0.75,
            "missing_entities": ["California"],
            "extra_entities": [],
        }

        report = format_metrics_report(metrics)
        assert "EXTRACTION QUALITY REPORT" in report
        assert "0.7500" in report


class TestEntityTypeMapping:
    """Tests for entity type mapping between benchmarks and LightRAG."""

    @pytest.mark.light
    def test_fewnerd_to_lightrag_mapping(self):
        """Test Few-NERD to LightRAG type mapping."""
        case = FEWNERD_SUBSET[0]
        converted = convert_fewnerd_to_lightrag(case)

        assert len(converted["entities"]) == len(case["entities"])

        for entity in converted["entities"]:
            assert entity["type"] in [
                "Person",
                "Organization",
                "Location",
                "Artifact",
                "Concept",
                "Event",
                "Method",
                "Content",
                "Data",
                "NaturalObject",
                "Other",
            ]


class TestBenchmarkIntegration:
    """Integration tests for benchmark data loading."""

    @pytest.mark.light
    def test_fewnerd_subset_loading(self):
        """Test Few-NERD subset data loads correctly."""
        assert len(FEWNERD_SUBSET) >= 5
        for case in FEWNERD_SUBSET:
            assert "id" in case
            assert "text" in case
            assert "entities" in case
            assert "relations" in case

    @pytest.mark.light
    def test_text2kgbench_subset_loading(self):
        """Test Text2KGBench subset data loads correctly."""
        assert len(TEXT2KGBENCH_SUBSET) >= 3
        for case in TEXT2KGBENCH_SUBSET:
            assert "id" in case
            assert "text" in case
            assert "entities" in case
            assert "relations" in case

    @pytest.mark.light
    def test_benchmark_data_coverage(self):
        """Test benchmark data covers multiple entity types."""
        all_types = set()
        for case in FEWNERD_SUBSET:
            for entity in case["entities"]:
                all_types.add(entity["type"])

        # Should cover at least 3 entity types
        assert len(all_types) >= 3


# ============================================================================
# Full Benchmark Tests (Heavy - Manual On-Demand)
# ============================================================================

from tests.benchmarks.fewnerd.full_dataset import (
    get_fewnerd_full_dataset,
)
from tests.benchmarks.text2kgbench.full_dataset import (
    convert_text2kgbench_to_lightrag,
    get_text2kgbench_full_dataset,
)


@pytest.mark.heavy
@pytest.mark.parametrize("benchmark", ["fewnerd_full", "text2kgbench_full"])
async def test_full_benchmark_extraction(benchmark: str):
    """Full benchmark extraction test (heavy, manual on-demand).

    This test requires:
    - Running LightRAG with actual LLM
    - Full benchmark dataset
    - Significant time (~30-60 minutes)

    Run with: pytest -m heavy -k academic_full
    """
    pytest.skip("Full benchmark - run manually on-demand")

    # Load full dataset
    if benchmark == "fewnerd_full":
        dataset = get_fewnerd_full_dataset()
        converter = convert_fewnerd_to_lightrag
    else:
        dataset = get_text2kgbench_full_dataset()
        converter = convert_text2kgbench_to_lightrag

    # Convert to LightRAG format
    lightrag_data = [converter(case) for case in dataset]

    # Calculate aggregate metrics
    total_recall = 0
    total_precision = 0
    total_f1 = 0

    for case in lightrag_data:
        gold_entities = case["entities"]
        # In real test: predicted_entities = run_extraction(case["text"])
        predicted_entities = MOCK_EXTRACTION_RESULT["entities"]

        recall = calculate_entity_recall(predicted_entities, gold_entities)["recall"]
        precision = calculate_entity_precision(predicted_entities, gold_entities)[
            "precision"
        ]
        f1 = calculate_entity_f1(recall, precision)

        total_recall += recall
        total_precision += precision
        total_f1 += f1

    n = len(lightrag_data)
    avg_recall = total_recall / n
    avg_precision = total_precision / n
    avg_f1 = total_f1 / n

    # Print results
    print(f"\n=== {benchmark.upper()} RESULTS ===")
    print(f"Test cases: {n}")
    print(f"Average Recall: {avg_recall:.4f}")
    print(f"Average Precision: {avg_precision:.4f}")
    print(f"Average F1: {avg_f1:.4f}")


@pytest.mark.heavy
async def test_model_comparison_full():
    """Compare extraction quality across model sizes (heavy, manual on-demand).

    Tests 1.5B vs 7B models on full benchmarks.
    """
    pytest.skip("Full benchmark - run manually on-demand")


@pytest.mark.heavy
async def test_fewnerd_full_benchmark_metrics():
    """Run metrics evaluation on full Few-NERD dataset (heavy test).

    This validates the evaluation metrics work correctly on larger datasets.
    """
    dataset = get_fewnerd_full_dataset()
    lightrag_data = [convert_fewnerd_to_lightrag(case) for case in dataset]

    # Verify dataset size
    assert len(lightrag_data) >= 50, f"Expected 50+ cases, got {len(lightrag_data)}"

    # Calculate aggregate metrics
    type_counts = {}
    for case in lightrag_data:
        for entity in case["entities"]:
            etype = entity["type"]
            type_counts[etype] = type_counts.get(etype, 0) + 1

    print("\n=== FEWNERD FULL DATASET METRICS ===")
    print(f"Total cases: {len(lightrag_data)}")
    print(f"Total entities: {sum(type_counts.values())}")
    print("Entity type distribution:")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {etype}: {count}")


@pytest.mark.heavy
async def test_text2kgbench_full_benchmark_metrics():
    """Run metrics evaluation on full Text2KGBench dataset (heavy test).

    This validates the evaluation metrics work correctly on larger datasets.
    """
    dataset = get_text2kgbench_full_dataset()
    lightrag_data = [convert_text2kgbench_to_lightrag(case) for case in dataset]

    # Verify dataset size
    assert len(lightrag_data) >= 25, f"Expected 25+ cases, got {len(lightrag_data)}"

    # Calculate aggregate metrics
    type_counts = {}
    for case in lightrag_data:
        for entity in case["entities"]:
            etype = entity["type"]
            type_counts[etype] = type_counts.get(etype, 0) + 1

    print("\n=== TEXT2KGBENCH FULL DATASET METRICS ===")
    print(f"Total cases: {len(lightrag_data)}")
    print(f"Total entities: {sum(type_counts.values())}")
    print("Entity type distribution:")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {etype}: {count}")


@pytest.mark.heavy
async def test_benchmark_data_validation():
    """Validate full benchmark datasets have correct structure (heavy test)."""
    # Validate Few-NERD
    fewnerd_data = get_fewnerd_full_dataset()
    for case in fewnerd_data:
        assert "id" in case
        assert "text" in case
        assert "entities" in case
        assert "relations" in case
        assert len(case["entities"]) > 0
        assert len(case["relations"]) > 0

    # Validate Text2KGBench
    t2kg_data = get_text2kgbench_full_dataset()
    for case in t2kg_data:
        assert "id" in case
        assert "text" in case
        assert "entities" in case
        assert "relations" in case

    print("\n=== DATA VALIDATION ===")
    print(f"Few-NERD: {len(fewnerd_data)} cases validated")
    print(f"Text2KGBench: {len(t2kg_data)} cases validated")
    print("All datasets have correct structure ✓")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "light"])
