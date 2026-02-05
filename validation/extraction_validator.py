"""
Extraction Validator for Structural Link Regression Testing

Provides comprehensive validation of LightRAG extraction results including
entity consistency, relationship integrity, and structural graph analysis.
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import networkx as nx

from lightrag.utils import logger


@dataclass
class EntityValidationResult:
    """Results of entity validation"""

    expected_count: int
    actual_count: int
    matched_entities: list[dict[str, Any]]
    missing_entities: list[str]
    extra_entities: list[str]
    fuzzy_match_score: float
    type_consistency_score: float


@dataclass
class RelationshipValidationResult:
    """Results of relationship validation"""

    expected_count: int
    actual_count: int
    matched_relationships: list[dict[str, Any]]
    missing_relationships: list[str]
    extra_relationships: list[str]
    keyword_match_score: float
    direction_consistency_score: float


@dataclass
class StructuralValidationResult:
    """Results of graph structure validation"""

    graph_connectivity: bool
    connected_components: int
    max_path_length: int | None
    clustering_coefficient: float
    density: float
    isolation_issues: list[str]


@dataclass
class ExtractionValidationResult:
    """Comprehensive extraction validation result"""

    gold_case_id: str
    timestamp: datetime
    entity_validation: EntityValidationResult
    relationship_validation: RelationshipValidationResult
    structural_validation: StructuralValidationResult
    overall_score: float
    passed: bool
    recommendations: list[str] = field(default_factory=list)
    validation_duration_seconds: float = 0.0


class ExtractionValidator:
    """
    Main extraction validation engine for LightRAG

    Provides comprehensive validation of extraction results against gold standard
    cases with support for fuzzy matching, structural analysis, and regression testing.
    """

    def __init__(self, tolerance: float = 0.8):
        """
        Initialize the extraction validator

        Args:
            tolerance: Fuzzy matching threshold for entity/relationship comparison
        """
        self.tolerance = tolerance
        self.logger = logger

    def normalize_name(self, name: str) -> str:
        """Normalize string for fuzzy comparison"""
        return (
            name.lower()
            .strip()
            .replace("the ", "")
            .replace("a ", "")
            .replace("an ", "")
        )

    def find_entity_match(
        self,
        target_name: str,
        entities: list[dict[str, Any]],
        tolerance: float | None = None,
    ) -> dict[str, Any] | None:
        """Find matching entity using fuzzy name matching"""
        if tolerance is None:
            tolerance = self.tolerance

        target_normalized = self.normalize_name(target_name)

        for entity in entities:
            entity_name = entity.get("id", entity.get("entity_name", ""))
            entity_normalized = self.normalize_name(entity_name)

            # Simple containment check with tolerance
            if (
                target_normalized in entity_normalized
                or entity_normalized in target_normalized
            ):
                return entity

            # Check for substantial overlap
            words_target = set(target_normalized.split())
            words_entity = set(entity_normalized.split())

            if words_target and words_entity:
                overlap = len(words_target.intersection(words_entity))
                similarity = overlap / max(len(words_target), len(words_entity))

                if similarity >= tolerance:
                    return entity

        return None

    def find_relationship_match(
        self,
        expected_rel: dict[str, Any],
        actual_rels: list[dict[str, Any]],
        entities: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Find matching relationship considering source, target, and keywords"""
        source_name = expected_rel["source"]
        target_name = expected_rel["target"]
        keywords = expected_rel.get("keywords", [])

        # Find source and target entities
        src_entity = self.find_entity_match(source_name, entities)
        tgt_entity = self.find_entity_match(target_name, entities)

        if not src_entity or not tgt_entity:
            return None

        src_id = src_entity.get("id", src_entity.get("entity_name", ""))
        tgt_id = tgt_entity.get("id", tgt_entity.get("entity_name", ""))

        # Look for matching relationships
        for rel in actual_rels:
            rel_src_id = rel.get("src_id", "")
            rel_tgt_id = rel.get("tgt_id", "")
            rel_keywords = rel.get("keywords", "").lower()

            # Check source and target match (bidirectional)
            src_match = rel_src_id == src_id or rel_tgt_id == src_id
            tgt_match = rel_tgt_id == tgt_id or rel_src_id == tgt_id

            if src_match and tgt_match:
                # Check keyword match
                if keywords:
                    keyword_match = any(kw.lower() in rel_keywords for kw in keywords)
                    if keyword_match:
                        return rel
                else:
                    return rel

        return None

    async def validate_entities(
        self,
        extracted_entities: list[dict[str, Any]],
        expected_entities: list[dict[str, Any]],
    ) -> EntityValidationResult:
        """Validate extracted entities against expected entities"""
        matched_entities = []
        missing_entities = []
        extra_entities = []

        # Check expected entities
        for expected in expected_entities:
            match = self.find_entity_match(expected["name"], extracted_entities)
            if match:
                # Check type consistency
                expected_type = expected.get("type", "").lower()
                actual_type = match.get("entity_type", "").lower()

                if expected_type and actual_type and expected_type != actual_type:
                    self.logger.warning(
                        f"Type mismatch for {expected['name']}: "
                        f"expected {expected_type}, got {actual_type}"
                    )

                matched_entities.append(
                    {
                        "expected": expected,
                        "actual": match,
                        "type_match": expected_type == actual_type
                        if expected_type and actual_type
                        else True,
                    }
                )
            else:
                missing_entities.append(expected["name"])

        # Find extra entities
        extracted_names = {
            entity.get("id", entity.get("entity_name", ""))
            for entity in extracted_entities
        }
        matched_names = {
            match["actual"].get("id", match["actual"].get("entity_name", ""))
            for match in matched_entities
        }
        extra_names = extracted_names - matched_names

        # Map extra names back to entities
        name_to_entity = {
            entity.get("id", entity.get("entity_name", "")): entity
            for entity in extracted_entities
        }
        extra_entities = [name_to_entity[name] for name in extra_names if name]

        # Calculate scores
        fuzzy_match_score = len(matched_entities) / max(len(expected_entities), 1)
        type_consistency_score = sum(
            1 for match in matched_entities if match["type_match"]
        ) / max(len(matched_entities), 1)

        return EntityValidationResult(
            expected_count=len(expected_entities),
            actual_count=len(extracted_entities),
            matched_entities=matched_entities,
            missing_entities=missing_entities,
            extra_entities=[
                e.get("id", e.get("entity_name", "")) for e in extra_entities
            ],
            fuzzy_match_score=fuzzy_match_score,
            type_consistency_score=type_consistency_score,
        )

    async def validate_relationships(
        self,
        extracted_relationships: list[dict[str, Any]],
        expected_relationships: list[dict[str, Any]],
        entities: list[dict[str, Any]],
    ) -> RelationshipValidationResult:
        """Validate extracted relationships against expected relationships"""
        matched_relationships = []
        missing_relationships = []
        extra_relationships = []

        # Check expected relationships
        for expected in expected_relationships:
            match = self.find_relationship_match(
                expected, extracted_relationships, entities
            )
            if match:
                matched_relationships.append({"expected": expected, "actual": match})
            else:
                missing_relationships.append(
                    f"{expected['source']} -> {expected['target']} ({expected.get('keywords', [])})"
                )

        # Find extra relationships
        matched_actual_rels = {id(match["actual"]) for match in matched_relationships}
        extra_rels = [
            rel for rel in extracted_relationships if id(rel) not in matched_actual_rels
        ]
        extra_relationships = [
            f"{rel.get('src_id', '')} -> {rel.get('tgt_id', '')} ({rel.get('keywords', '')})"
            for rel in extra_rels
        ]

        # Calculate scores
        keyword_match_score = len(matched_relationships) / max(
            len(expected_relationships), 1
        )
        direction_consistency_score = keyword_match_score  # Simplified for now

        return RelationshipValidationResult(
            expected_count=len(expected_relationships),
            actual_count=len(extracted_relationships),
            matched_relationships=matched_relationships,
            missing_relationships=missing_relationships,
            extra_relationships=extra_relationships,
            keyword_match_score=keyword_match_score,
            direction_consistency_score=direction_consistency_score,
        )

    def analyze_graph_structure(
        self, entities: list[dict[str, Any]], relationships: list[dict[str, Any]]
    ) -> StructuralValidationResult:
        """Analyze graph structure and connectivity"""
        # Create NetworkX graph
        G = nx.DiGraph()

        # Add nodes
        for entity in entities:
            entity_id = entity.get("id", entity.get("entity_name", ""))
            if entity_id:
                G.add_node(entity_id, **entity)

        # Add edges
        for rel in relationships:
            src_id = rel.get("src_id", "")
            tgt_id = rel.get("tgt_id", "")
            if src_id and tgt_id and G.has_node(src_id) and G.has_node(tgt_id):
                G.add_edge(src_id, tgt_id, **rel)

        # Analyze structure
        if G.number_of_nodes() == 0:
            return StructuralValidationResult(
                graph_connectivity=False,
                connected_components=0,
                max_path_length=None,
                clustering_coefficient=0.0,
                density=0.0,
                isolation_issues=["Empty graph - no entities found"],
            )

        # Convert to undirected for connectivity analysis
        undirected_G = G.to_undirected()

        # Connectivity analysis
        is_connected = nx.is_connected(undirected_G)
        connected_components = nx.number_connected_components(undirected_G)

        # Path analysis
        try:
            if is_connected:
                max_path_length = nx.diameter(undirected_G)
            else:
                # Find largest component
                largest_cc = max(nx.connected_components(undirected_G), key=len)
                subgraph = undirected_G.subgraph(largest_cc)
                max_path_length = nx.diameter(subgraph) if len(largest_cc) > 1 else 0
        except Exception as e:
            logger.warning(f"Path calculation failed: {e}")
            max_path_length = None

        # Clustering coefficient and density
        clustering_coefficient = nx.average_clustering(undirected_G)
        density = nx.density(undirected_G)

        # Isolation issues
        isolation_issues = []
        isolated_nodes = list(nx.isolates(undirected_G))
        if isolated_nodes:
            isolation_issues.extend(
                [f"Isolated entity: {node}" for node in isolated_nodes]
            )

        return StructuralValidationResult(
            graph_connectivity=is_connected,
            connected_components=connected_components,
            max_path_length=max_path_length,
            clustering_coefficient=clustering_coefficient,
            density=density,
            isolation_issues=isolation_issues,
        )

    async def validate_against_gold_standard(
        self, extraction_result: dict[str, Any], gold_case: dict[str, Any]
    ) -> ExtractionValidationResult:
        """
        Validate extraction result against a gold standard case

        Args:
            extraction_result: Dictionary containing 'entities' and 'relationships'
            gold_case: Gold standard case with expected entities and relationships

        Returns:
            Comprehensive validation result
        """
        start_time = datetime.now()

        # Extract data
        entities = extraction_result.get("entities", [])
        relationships = extraction_result.get("relationships", [])

        expected_entities = gold_case.get("expected_entities", [])
        expected_relationships = gold_case.get("expected_relations", [])

        # Perform validations
        entity_validation = await self.validate_entities(entities, expected_entities)
        relationship_validation = await self.validate_relationships(
            relationships, expected_relationships, entities
        )
        structural_validation = self.analyze_graph_structure(entities, relationships)

        # Calculate overall score
        scores = [
            entity_validation.fuzzy_match_score,
            entity_validation.type_consistency_score,
            relationship_validation.keyword_match_score,
            1.0 if structural_validation.graph_connectivity else 0.5,
        ]
        overall_score = statistics.mean(scores)

        # Determine if passed
        structural_checks = gold_case.get("structural_checks", {})
        min_entities = structural_checks.get("min_entities", 0)
        min_relationships = structural_checks.get("min_relationships", 0)
        require_connectivity = structural_checks.get("graph_connectivity", False)

        passed = (
            overall_score >= self.tolerance
            and len(entities) >= min_entities
            and len(relationships) >= min_relationships
            and (not require_connectivity or structural_validation.graph_connectivity)
        )

        # Generate recommendations
        recommendations = []

        if entity_validation.missing_entities:
            recommendations.append(
                f"Missing entities detected: {', '.join(entity_validation.missing_entities[:3])}"
                f"{'...' if len(entity_validation.missing_entities) > 3 else ''}"
            )

        if relationship_validation.missing_relationships:
            recommendations.append(
                f"Missing relationships: {', '.join(relationship_validation.missing_relationships[:2])}"
                f"{'...' if len(relationship_validation.missing_relationships) > 2 else ''}"
            )

        if structural_validation.isolation_issues:
            recommendations.append(
                f"Graph structure issues: {', '.join(structural_validation.isolation_issues[:2])}"
            )

        if not passed:
            recommendations.append("Overall validation score below threshold")

        duration = (datetime.now() - start_time).total_seconds()

        return ExtractionValidationResult(
            gold_case_id=gold_case.get("id", "unknown"),
            timestamp=start_time,
            entity_validation=entity_validation,
            relationship_validation=relationship_validation,
            structural_validation=structural_validation,
            overall_score=overall_score,
            passed=passed,
            recommendations=recommendations,
            validation_duration_seconds=duration,
        )

    async def compare_extractions(
        self, baseline_result: dict[str, Any], current_result: dict[str, Any]
    ) -> ExtractionValidationResult:
        """
        Compare two extraction results for regression testing

        Args:
            baseline_result: Baseline extraction result
            current_result: Current extraction result

        Returns:
            Regression comparison result
        """
        start_time = datetime.now()

        # Extract data
        baseline_entities = baseline_result.get("entities", [])
        baseline_relationships = baseline_result.get("relationships", [])

        current_entities = current_result.get("entities", [])
        current_relationships = current_result.get("relationships", [])

        # Entity comparison
        entity_changes = {"added": [], "removed": [], "changed": []}

        baseline_entity_names = {
            self.normalize_name(e.get("id", e.get("entity_name", "")))
            for e in baseline_entities
        }
        current_entity_names = {
            self.normalize_name(e.get("id", e.get("entity_name", "")))
            for e in current_entities
        }

        # Added entities
        added_names = current_entity_names - baseline_entity_names
        for name in added_names:
            entity = next(
                (
                    e
                    for e in current_entities
                    if self.normalize_name(e.get("id", e.get("entity_name", "")))
                    == name
                ),
                None,
            )
            if entity:
                entity_changes["added"].append(entity)

        # Removed entities
        removed_names = baseline_entity_names - current_entity_names
        for name in removed_names:
            entity = next(
                (
                    e
                    for e in baseline_entities
                    if self.normalize_name(e.get("id", e.get("entity_name", "")))
                    == name
                ),
                None,
            )
            if entity:
                entity_changes["removed"].append(entity)

        # Simplified relationship comparison
        baseline_rel_count = len(baseline_relationships)
        current_rel_count = len(current_relationships)

        # Calculate regression score
        entity_stability = 1.0 - (
            len(entity_changes["added"]) + len(entity_changes["removed"])
        ) / max(len(baseline_entities), 1)
        relationship_stability = 1.0 - abs(
            baseline_rel_count - current_rel_count
        ) / max(baseline_rel_count, 1)

        regression_score = (entity_stability + relationship_stability) / 2

        # Create validation results (simplified for regression)
        entity_validation = EntityValidationResult(
            expected_count=len(baseline_entities),
            actual_count=len(current_entities),
            matched_entities=[],  # Not applicable for regression
            missing_entities=[
                e.get("id", e.get("entity_name", "")) for e in entity_changes["removed"]
            ],
            extra_entities=[
                e.get("id", e.get("entity_name", "")) for e in entity_changes["added"]
            ],
            fuzzy_match_score=entity_stability,
            type_consistency_score=1.0,  # Simplified
        )

        relationship_validation = RelationshipValidationResult(
            expected_count=len(baseline_relationships),
            actual_count=len(current_relationships),
            matched_relationships=[],
            missing_relationships=[f"Removed: {r}" for r in entity_changes["removed"]],
            extra_relationships=[f"Added: {r}" for r in entity_changes["added"]],
            keyword_match_score=relationship_stability,
            direction_consistency_score=1.0,  # Simplified
        )

        structural_validation = self.analyze_graph_structure(
            current_entities, current_relationships
        )

        # Generate recommendations
        recommendations = []
        if regression_score < 0.8:
            recommendations.append("Significant changes detected in extraction results")
        if entity_changes["added"]:
            recommendations.append(f"Added {len(entity_changes['added'])} entities")
        if entity_changes["removed"]:
            recommendations.append(f"Removed {len(entity_changes['removed'])} entities")

        duration = (datetime.now() - start_time).total_seconds()

        return ExtractionValidationResult(
            gold_case_id="regression_comparison",
            timestamp=start_time,
            entity_validation=entity_validation,
            relationship_validation=relationship_validation,
            structural_validation=structural_validation,
            overall_score=regression_score,
            passed=regression_score >= self.tolerance,
            recommendations=recommendations,
            validation_duration_seconds=duration,
        )
