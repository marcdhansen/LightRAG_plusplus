"""
Evaluation metrics for entity and relation extraction benchmarks.

This module provides functions to calculate:
- Entity recall, precision, and F1 score
- Relation recall, precision, and F1 score
- Type-specific metrics
- Overall extraction quality scores
"""

from typing import Any


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for fuzzy matching."""
    return name.lower().strip().replace("the ", "").replace("-", " ").replace("_", " ")


def find_entity_match(
    predicted_entities: list[dict], gold_entity: dict, threshold: float = 0.8
) -> dict | None:
    """Find a matching entity in predicted list for a gold entity."""
    gold_name = normalize_entity_name(gold_entity.get("name", ""))
    gold_type = gold_entity.get("type", "")

    for pred in predicted_entities:
        pred_name = normalize_entity_name(pred.get("name", ""))
        pred_type = pred.get("type", "")

        # Check name similarity (simple substring match)
        name_match = gold_name in pred_name or pred_name in gold_name

        # Check type match (case-insensitive)
        type_match = gold_type.lower() == pred_type.lower()

        if name_match and type_match:
            return pred

    return None


def calculate_entity_recall(
    predicted_entities: list[dict], gold_entities: list[dict]
) -> dict[str, Any]:
    """Calculate entity recall.

    Recall = TP / (TP + FN)
    Where TP = correctly predicted entities, FN = missed gold entities
    """
    if not gold_entities:
        return {"recall": 1.0, "tp": 0, "fn": 0, "missing": []}

    tp = 0
    missing = []

    for gold in gold_entities:
        match = find_entity_match(predicted_entities, gold)
        if match:
            tp += 1
        else:
            missing.append(gold.get("name", "unknown"))

    fn = len(gold_entities) - tp
    recall = tp / len(gold_entities) if gold_entities else 1.0

    return {
        "recall": recall,
        "tp": tp,
        "fn": fn,
        "missing": missing,
    }


def calculate_entity_precision(
    predicted_entities: list[dict], gold_entities: list[dict]
) -> dict[str, Any]:
    """Calculate entity precision.

    Precision = TP / (TP + FP)
    Where TP = correctly predicted entities, FP = incorrectly predicted entities
    """
    if not predicted_entities:
        return {"precision": 0.0, "tp": 0, "fp": 0, "extra": []}

    tp = 0
    extra = []
    matched_gold = set()

    for i, pred in enumerate(predicted_entities):
        match = find_entity_match(gold_entities, pred)
        if match:
            tp += 1
            # Track which gold entities have been matched
            for j, gold in enumerate(gold_entities):
                if j not in matched_gold and normalize_entity_name(
                    gold.get("name", "")
                ) in normalize_entity_name(pred.get("name", "")):
                    matched_gold.add(j)
                    break
        else:
            extra.append(pred.get("name", f"unknown_{i}"))

    fp = len(predicted_entities) - tp
    precision = tp / len(predicted_entities) if predicted_entities else 0.0

    return {
        "precision": precision,
        "tp": tp,
        "fp": fp,
        "extra": extra,
    }


def calculate_entity_f1(recall: float, precision: float) -> float:
    """Calculate F1 score from recall and precision."""
    if recall + precision == 0:
        return 0.0
    return 2 * (recall * precision) / (recall + precision)


def calculate_relation_match(
    predicted_relations: list[dict], gold_relation: dict
) -> dict | None:
    """Find a matching relation in predicted list for a gold relation."""
    gold_src = normalize_entity_name(gold_relation.get("source", ""))
    gold_tgt = normalize_entity_name(gold_relation.get("target", ""))

    for pred in predicted_relations:
        pred_src = normalize_entity_name(pred.get("source", ""))
        pred_tgt = normalize_entity_name(pred.get("target", ""))

        # Check if source and target match (order-independent for undirected)
        src_match = gold_src in pred_src or pred_src in gold_src
        tgt_match = gold_tgt in pred_tgt or pred_tgt in gold_tgt

        if src_match and tgt_match:
            return pred

    return None


def calculate_relation_recall(
    predicted_relations: list[dict], gold_relations: list[dict]
) -> dict[str, Any]:
    """Calculate relation recall."""
    if not gold_relations:
        return {"recall": 1.0, "tp": 0, "fn": 0, "missing": []}

    tp = 0
    missing = []

    for gold in gold_relations:
        match = calculate_relation_match(predicted_relations, gold)
        if match:
            tp += 1
        else:
            missing.append(f"{gold.get('source', '?')} -> {gold.get('target', '?')}")

    fn = len(gold_relations) - tp
    recall = tp / len(gold_relations) if gold_relations else 1.0

    return {
        "recall": recall,
        "tp": tp,
        "fn": fn,
        "missing": missing,
    }


def calculate_relation_precision(
    predicted_relations: list[dict], gold_relations: list[dict]
) -> dict[str, Any]:
    """Calculate relation precision."""
    if not predicted_relations:
        return {"precision": 0.0, "tp": 0, "fp": 0, "extra": []}

    tp = 0
    extra = []

    for pred in predicted_relations:
        match = calculate_relation_match(gold_relations, pred)
        if match:
            tp += 1
        else:
            extra.append(f"{pred.get('source', '?')} -> {pred.get('target', '?')}")

    fp = len(predicted_relations) - tp
    precision = tp / len(predicted_relations) if predicted_relations else 0.0

    return {
        "precision": precision,
        "tp": tp,
        "fp": fp,
        "extra": extra,
    }


def calculate_type_specific_metrics(
    predicted_entities: list[dict],
    gold_entities: list[dict],
    entity_types: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Calculate metrics per entity type.

    Args:
        predicted_entities: List of predicted entity dicts
        gold_entities: List of gold entity dicts
        entity_types: Optional list of entity types to report

    Returns:
        Dict mapping entity type to metrics (recall, precision, f1)
    """
    # Group gold entities by type
    gold_by_type: dict[str, list[dict]] = {}
    for gold in gold_entities:
        etype = gold.get("type", "Unknown")
        if etype not in gold_by_type:
            gold_by_type[etype] = []
        gold_by_type[etype].append(gold)

    # Group predicted entities by type
    pred_by_type: dict[str, list[dict]] = {}
    for pred in predicted_entities:
        etype = pred.get("type", "Unknown")
        if etype not in pred_by_type:
            pred_by_type[etype] = []
        pred_by_type[etype].append(pred)

    # Calculate metrics per type
    results: dict[str, dict[str, float]] = {}

    all_types = set(gold_by_type.keys()) | set(pred_by_type.keys())
    if entity_types:
        all_types = all_types | set(entity_types)

    for etype in all_types:
        gold_list = gold_by_type.get(etype, [])
        pred_list = pred_by_type.get(etype, [])

        recall = calculate_entity_recall(pred_list, gold_list)["recall"]
        precision = calculate_entity_precision(pred_list, gold_list)["precision"]
        f1 = calculate_entity_f1(recall, precision)

        results[etype] = {
            "recall": recall,
            "precision": precision,
            "f1": f1,
            "gold_count": len(gold_list),
            "pred_count": len(pred_list),
        }

    return results


def calculate_extraction_quality_score(
    predicted_entities: list[dict],
    gold_entities: list[dict],
    predicted_relations: list[dict] | None = None,
    gold_relations: list[dict] | None = None,
    entity_weight: float = 0.6,
    relation_weight: float = 0.4,
) -> dict[str, Any]:
    """Calculate overall extraction quality score.

    Args:
        predicted_entities: List of predicted entities
        gold_entities: List of gold entities
        predicted_relations: Optional list of predicted relations
        gold_relations: Optional list of gold relations
        entity_weight: Weight for entity F1 (default 0.6)
        relation_weight: Weight for relation F1 (default 0.4)

    Returns:
        Dict with overall score and component scores
    """
    # Entity metrics
    entity_recall = calculate_entity_recall(predicted_entities, gold_entities)
    entity_precision = calculate_entity_precision(predicted_entities, gold_entities)
    entity_f1 = calculate_entity_f1(
        entity_recall["recall"], entity_precision["precision"]
    )

    # Relation metrics (if provided)
    if predicted_relations is not None and gold_relations is not None:
        relation_recall = calculate_relation_recall(predicted_relations, gold_relations)
        relation_precision = calculate_relation_precision(
            predicted_relations, gold_relations
        )
        relation_f1 = calculate_entity_f1(
            relation_recall["recall"], relation_precision["precision"]
        )

        # Overall score
        overall_f1 = entity_weight * entity_f1 + relation_weight * relation_f1

        return {
            "overall_f1": overall_f1,
            "entity_f1": entity_f1,
            "relation_f1": relation_f1,
            "entity_recall": entity_recall["recall"],
            "entity_precision": entity_precision["precision"],
            "relation_recall": relation_recall["recall"],
            "relation_precision": relation_precision["precision"],
            "missing_entities": entity_recall["missing"],
            "extra_entities": entity_precision["extra"],
            "missing_relations": relation_recall["missing"],
            "extra_relations": relation_precision["extra"],
        }

    return {
        "overall_f1": entity_f1,
        "entity_f1": entity_f1,
        "entity_recall": entity_recall["recall"],
        "entity_precision": entity_precision["precision"],
        "missing_entities": entity_recall["missing"],
        "extra_entities": entity_precision["extra"],
    }


def format_metrics_report(metrics: dict[str, Any]) -> str:
    """Format metrics as a human-readable report."""
    lines = [
        "=" * 50,
        "EXTRACTION QUALITY REPORT",
        "=" * 50,
        "",
        f"Overall F1 Score: {metrics.get('overall_f1', 0.0):.4f}",
        "",
        "Entity Metrics:",
        f"  - Recall:    {metrics.get('entity_recall', 0.0):.4f}",
        f"  - Precision: {metrics.get('entity_precision', 0.0):.4f}",
        f"  - F1:        {metrics.get('entity_f1', 0.0):.4f}",
        "",
    ]

    if "relation_f1" in metrics:
        lines.extend(
            [
                "Relation Metrics:",
                f"  - Recall:    {metrics.get('relation_recall', 0.0):.4f}",
                f"  - Precision: {metrics.get('relation_precision', 0.0):.4f}",
                f"  - F1:        {metrics.get('relation_f1', 0.0):.4f}",
                "",
            ]
        )

    if metrics.get("missing_entities"):
        lines.extend(
            [
                f"Missing Entities ({len(metrics['missing_entities'])}):",
            ]
            + [f"  - {e}" for e in metrics["missing_entities"][:10]]
            + [""]
        )

    if metrics.get("extra_entities"):
        lines.extend(
            [
                f"Extra Entities ({len(metrics['extra_entities'])}):",
            ]
            + [f"  - {e}" for e in metrics["extra_entities"][:10]]
            + [""]
        )

    lines.append("=" * 50)

    return "\n".join(lines)
