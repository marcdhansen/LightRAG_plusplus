"""
Regression Comparator for Extraction Validation

Provides comprehensive comparison functionality for regression testing
between different extraction runs and versions.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RegressionChange:
    """Represents a specific change in extraction results"""

    change_type: str  # "added", "removed", "modified"
    item_type: str  # "entity", "relationship", "property"
    item_id: str
    description: str
    impact_score: float  # 0.0-1.0, higher = more significant
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RegressionSummary:
    """Summary of regression comparison results"""

    baseline_version: str
    current_version: str
    timestamp: datetime
    overall_stability_score: float  # 0.0-1.0, higher = more stable

    # Counts
    entities_added: int = 0
    entities_removed: int = 0
    entities_modified: int = 0

    relationships_added: int = 0
    relationships_removed: int = 0
    relationships_modified: int = 0

    # Structural changes
    connectivity_changed: bool = False
    component_changes: int = 0
    density_change: float = 0.0

    # Performance changes
    execution_time_change: float = 0.0
    memory_usage_change: int = 0

    # Detailed changes
    significant_changes: list[RegressionChange] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Classification
    regression_detected: bool = False
    improvement_detected: bool = False
    neutral_change: bool = False


class RegressionComparator:
    """
    Comprehensive regression testing for extraction results

    Compares extraction results across different runs, versions, or
    configurations to detect regressions and improvements.
    """

    def __init__(self, tolerance: float = 0.1, min_impact_score: float = 0.1):
        """
        Initialize the regression comparator

        Args:
            tolerance: Relative change tolerance for significance
            min_impact_score: Minimum impact score to consider a change significant
        """
        self.tolerance = tolerance
        self.min_impact_score = min_impact_score

    def _calculate_entity_impact(self, entity: dict[str, Any]) -> float:
        """Calculate impact score for an entity change"""
        # Base impact on entity type and properties
        entity_type = entity.get("entity_type", "").lower()

        # Higher impact for important entity types
        type_scores = {
            "person": 0.8,
            "organization": 0.9,
            "location": 0.7,
            "concept": 0.6,
            "event": 0.7,
            "theory": 0.5,
        }

        base_score = type_scores.get(entity_type, 0.5)

        # Increase impact for entities with more properties
        property_count = len(entity.get("properties", {}))
        property_bonus = min(property_count * 0.1, 0.3)

        return min(base_score + property_bonus, 1.0)

    def _calculate_relationship_impact(self, relationship: dict[str, Any]) -> float:
        """Calculate impact score for a relationship change"""
        # Base impact on relationship keywords and properties
        keywords = relationship.get("keywords", "").lower()

        # Higher impact for important relationship types
        important_keywords = [
            "founded",
            "created",
            "developed",
            "discovered",
            "leads",
            "manages",
            "controls",
            "owns",
            "acquired",
            "merged",
            "partnered",
        ]

        base_score = 0.5
        if any(kw in keywords for kw in important_keywords):
            base_score = 0.8

        # Increase impact for relationships with more properties
        property_count = len(relationship.get("properties", {}))
        property_bonus = min(property_count * 0.1, 0.2)

        return min(base_score + property_bonus, 1.0)

    def _compare_entities(
        self,
        baseline_entities: list[dict[str, Any]],
        current_entities: list[dict[str, Any]],
    ) -> tuple[list[RegressionChange], int, int, int]:
        """
        Compare entities between baseline and current results

        Returns:
            Tuple of (changes, added_count, removed_count, modified_count)
        """
        changes = []

        # Create lookup dictionaries
        baseline_by_id = {
            entity.get("id", entity.get("entity_name", "")): entity
            for entity in baseline_entities
        }
        current_by_id = {
            entity.get("id", entity.get("entity_name", "")): entity
            for entity in current_entities
        }

        baseline_ids = set(baseline_by_id.keys())
        current_ids = set(current_by_id.keys())

        # Added entities
        added_ids = current_ids - baseline_ids
        for entity_id in added_ids:
            entity = current_by_id[entity_id]
            impact = self._calculate_entity_impact(entity)
            changes.append(
                RegressionChange(
                    change_type="added",
                    item_type="entity",
                    item_id=entity_id,
                    description=f"Added entity: {entity_id}",
                    impact_score=impact,
                    details={"entity": entity},
                )
            )

        # Removed entities
        removed_ids = baseline_ids - current_ids
        for entity_id in removed_ids:
            entity = baseline_by_id[entity_id]
            impact = self._calculate_entity_impact(entity)
            changes.append(
                RegressionChange(
                    change_type="removed",
                    item_type="entity",
                    item_id=entity_id,
                    description=f"Removed entity: {entity_id}",
                    impact_score=impact,
                    details={"entity": entity},
                )
            )

        # Modified entities
        common_ids = baseline_ids & current_ids
        for entity_id in common_ids:
            baseline_entity = baseline_by_id[entity_id]
            current_entity = current_by_id[entity_id]

            # Check for modifications
            modifications = []

            # Type changes
            if baseline_entity.get("entity_type") != current_entity.get("entity_type"):
                modifications.append(
                    f"Type: {baseline_entity.get('entity_type')} -> {current_entity.get('entity_type')}"
                )

            # Description changes
            baseline_desc = baseline_entity.get("description", "")
            current_desc = current_entity.get("description", "")
            if baseline_desc != current_desc:
                modifications.append("Description changed")

            # Property changes
            baseline_props = baseline_entity.get("properties", {})
            current_props = current_entity.get("properties", {})
            if baseline_props != current_props:
                modifications.append("Properties changed")

            if modifications:
                impact = self._calculate_entity_impact(current_entity)
                changes.append(
                    RegressionChange(
                        change_type="modified",
                        item_type="entity",
                        item_id=entity_id,
                        description=f"Modified entity: {entity_id}",
                        impact_score=impact,
                        details={
                            "modifications": modifications,
                            "baseline": baseline_entity,
                            "current": current_entity,
                        },
                    )
                )

        return (
            changes,
            len(added_ids),
            len(removed_ids),
            len([c for c in changes if c.change_type == "modified"]),
        )

    def _compare_relationships(
        self,
        baseline_relationships: list[dict[str, Any]],
        current_relationships: list[dict[str, Any]],
    ) -> tuple[list[RegressionChange], int, int, int]:
        """
        Compare relationships between baseline and current results

        Returns:
            Tuple of (changes, added_count, removed_count, modified_count)
        """
        changes = []

        # Create relationship identifiers
        def create_rel_id(rel):
            src = rel.get("src_id", "")
            tgt = rel.get("tgt_id", "")
            keywords = rel.get("keywords", "")
            return f"{src}->{tgt}:{keywords}"

        baseline_by_id = {create_rel_id(rel): rel for rel in baseline_relationships}
        current_by_id = {create_rel_id(rel): rel for rel in current_relationships}

        baseline_ids = set(baseline_by_id.keys())
        current_ids = set(current_by_id.keys())

        # Added relationships
        added_ids = current_ids - baseline_ids
        for rel_id in added_ids:
            relationship = current_by_id[rel_id]
            impact = self._calculate_relationship_impact(relationship)
            changes.append(
                RegressionChange(
                    change_type="added",
                    item_type="relationship",
                    item_id=rel_id,
                    description=f"Added relationship: {rel_id}",
                    impact_score=impact,
                    details={"relationship": relationship},
                )
            )

        # Removed relationships
        removed_ids = baseline_ids - current_ids
        for rel_id in removed_ids:
            relationship = baseline_by_id[rel_id]
            impact = self._calculate_relationship_impact(relationship)
            changes.append(
                RegressionChange(
                    change_type="removed",
                    item_type="relationship",
                    item_id=rel_id,
                    description=f"Removed relationship: {rel_id}",
                    impact_score=impact,
                    details={"relationship": relationship},
                )
            )

        # Modified relationships
        common_ids = baseline_ids & current_ids
        for rel_id in common_ids:
            baseline_rel = baseline_by_id[rel_id]
            current_rel = current_by_id[rel_id]

            # Check for modifications
            if baseline_rel != current_rel:
                impact = self._calculate_relationship_impact(current_rel)
                changes.append(
                    RegressionChange(
                        change_type="modified",
                        item_type="relationship",
                        item_id=rel_id,
                        description=f"Modified relationship: {rel_id}",
                        impact_score=impact,
                        details={"baseline": baseline_rel, "current": current_rel},
                    )
                )

        return (
            changes,
            len(added_ids),
            len(removed_ids),
            len([c for c in changes if c.change_type == "modified"]),
        )

    def _compare_structure(
        self,
        baseline_entities: list[dict[str, Any]],
        baseline_relationships: list[dict[str, Any]],
        current_entities: list[dict[str, Any]],
        current_relationships: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare structural properties of graphs"""
        # Create basic structural metrics
        baseline_structure = {
            "entity_count": len(baseline_entities),
            "relationship_count": len(baseline_relationships),
            "density": len(baseline_relationships)
            / max(len(baseline_entities) * (len(baseline_entities) - 1), 1),
        }

        current_structure = {
            "entity_count": len(current_entities),
            "relationship_count": len(current_relationships),
            "density": len(current_relationships)
            / max(len(current_entities) * (len(current_entities) - 1), 1),
        }

        return {
            "entity_count_change": current_structure["entity_count"]
            - baseline_structure["entity_count"],
            "relationship_count_change": current_structure["relationship_count"]
            - baseline_structure["relationship_count"],
            "density_change": current_structure["density"]
            - baseline_structure["density"],
            "baseline": baseline_structure,
            "current": current_structure,
        }

    def _calculate_stability_score(self, changes: list[RegressionChange]) -> float:
        """Calculate overall stability score from changes"""
        if not changes:
            return 1.0

        # Weight changes by impact and type
        total_impact = 0.0
        removal_penalty = 0.0
        addition_penalty = 0.0

        for change in changes:
            impact = change.impact_score

            if change.change_type == "removed":
                removal_penalty += impact * 1.5  # Higher penalty for removals
            elif change.change_type == "added":
                addition_penalty += impact * 1.0  # Moderate penalty for additions
            elif change.change_type == "modified":
                total_impact += impact * 0.8  # Lower penalty for modifications

        total_penalty = total_impact + removal_penalty + addition_penalty

        # Normalize to 0.0-1.0 range
        # Assuming maximum reasonable penalty of 10.0 for normalization
        stability_score = max(0.0, 1.0 - (total_penalty / 10.0))

        return stability_score

    def _generate_recommendations(
        self,
        changes: list[RegressionChange],
        structure_changes: dict[str, Any],
        stability_score: float,
    ) -> list[str]:
        """Generate recommendations based on changes"""
        recommendations = []

        # High-level recommendations
        if stability_score < 0.7:
            recommendations.append(
                "Low stability score detected - review extraction changes"
            )

        # Entity-specific recommendations
        entity_changes = [c for c in changes if c.item_type == "entity"]
        if len(entity_changes) > 5:
            recommendations.append(
                f"High number of entity changes ({len(entity_changes)}) - consider reviewing extraction parameters"
            )

        removed_entities = [c for c in entity_changes if c.change_type == "removed"]
        if len(removed_entities) > 3:
            recommendations.append(
                "Multiple entities removed - potential regression detected"
            )

        # Relationship-specific recommendations
        rel_changes = [c for c in changes if c.item_type == "relationship"]
        if len(rel_changes) > 5:
            recommendations.append(
                f"High number of relationship changes ({len(rel_changes)}) - check relationship extraction logic"
            )

        # Structure-specific recommendations
        if abs(structure_changes["density_change"]) > 0.1:
            if structure_changes["density_change"] > 0:
                recommendations.append(
                    "Graph density increased significantly - may affect query performance"
                )
            else:
                recommendations.append(
                    "Graph density decreased significantly - potential loss of information"
                )

        if structure_changes["entity_count_change"] < -5:
            recommendations.append(
                "Significant entity count reduction - review extraction filtering"
            )

        # Performance recommendations (if available)
        high_impact_changes = [c for c in changes if c.impact_score > 0.8]
        if high_impact_changes:
            recommendations.append(
                f"High-impact changes detected ({len(high_impact_changes)}) - prioritize manual review"
            )

        if not recommendations:
            recommendations.append(
                "No significant issues detected - extraction appears stable"
            )

        return recommendations

    def compare_extraction_results(
        self,
        baseline_result: dict[str, Any],
        current_result: dict[str, Any],
        baseline_version: str = "baseline",
        current_version: str = "current",
        execution_time_baseline: float | None = None,
        execution_time_current: float | None = None,
        memory_usage_baseline: int | None = None,
        memory_usage_current: int | None = None,
    ) -> RegressionSummary:
        """
        Compare two extraction results comprehensively

        Args:
            baseline_result: Baseline extraction result
            current_result: Current extraction result
            baseline_version: Version identifier for baseline
            current_version: Version identifier for current
            execution_time_baseline: Execution time for baseline (optional)
            execution_time_current: Execution time for current (optional)
            memory_usage_baseline: Memory usage for baseline (optional)
            memory_usage_current: Memory usage for current (optional)

        Returns:
            Comprehensive regression summary
        """
        # Extract data
        baseline_entities = baseline_result.get("entities", [])
        baseline_relationships = baseline_result.get("relationships", [])
        current_entities = current_result.get("entities", [])
        current_relationships = current_result.get("relationships", [])

        # Compare entities
        entity_changes, entities_added, entities_removed, entities_modified = (
            self._compare_entities(baseline_entities, current_entities)
        )

        # Compare relationships
        rel_changes, rels_added, rels_removed, rels_modified = (
            self._compare_relationships(baseline_relationships, current_relationships)
        )

        # Compare structure
        structure_changes = self._compare_structure(
            baseline_entities,
            baseline_relationships,
            current_entities,
            current_relationships,
        )

        # Combine all changes
        all_changes = entity_changes + rel_changes

        # Filter significant changes
        significant_changes = [
            change
            for change in all_changes
            if change.impact_score >= self.min_impact_score
        ]

        # Calculate stability score
        stability_score = self._calculate_stability_score(all_changes)

        # Calculate performance changes
        execution_time_change = 0.0
        if execution_time_baseline is not None and execution_time_current is not None:
            execution_time_change = execution_time_current - execution_time_baseline

        memory_usage_change = 0
        if memory_usage_baseline is not None and memory_usage_current is not None:
            memory_usage_change = memory_usage_current - memory_usage_baseline

        # Generate recommendations
        recommendations = self._generate_recommendations(
            significant_changes, structure_changes, stability_score
        )

        # Classify change type
        regression_detected = stability_score < (1.0 - self.tolerance)
        improvement_detected = (
            structure_changes["entity_count_change"] > 0
            and structure_changes["relationship_count_change"] > 0
            and stability_score > 0.8
        )
        neutral_change = not regression_detected and not improvement_detected

        return RegressionSummary(
            baseline_version=baseline_version,
            current_version=current_version,
            timestamp=datetime.now(),
            overall_stability_score=stability_score,
            entities_added=entities_added,
            entities_removed=entities_removed,
            entities_modified=entities_modified,
            relationships_added=rels_added,
            relationships_removed=rels_removed,
            relationships_modified=rels_modified,
            connectivity_changed=False,  # Could be enhanced with actual connectivity analysis
            component_changes=0,  # Could be enhanced with actual component analysis
            density_change=structure_changes["density_change"],
            execution_time_change=execution_time_change,
            memory_usage_change=memory_usage_change,
            significant_changes=significant_changes,
            recommendations=recommendations,
            regression_detected=regression_detected,
            improvement_detected=improvement_detected,
            neutral_change=neutral_change,
        )

    def load_extraction_result(self, file_path: str | Path) -> dict[str, Any]:
        """Load extraction result from file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Extraction result file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    return json.load(f)
                else:
                    # Assume it's a text file with basic format
                    content = f.read()
                    return {"entities": [], "relationships": [], "raw_text": content}
        except Exception as e:
            raise Exception(
                f"Error loading extraction result from {file_path}: {e}"
            ) from e

    def compare_files(
        self,
        baseline_file: str | Path,
        current_file: str | Path,
        baseline_version: str = None,
        current_version: str = None,
    ) -> RegressionSummary:
        """
        Compare extraction results from files

        Args:
            baseline_file: Path to baseline extraction result file
            current_file: Path to current extraction result file
            baseline_version: Version identifier for baseline (optional)
            current_version: Version identifier for current (optional)

        Returns:
            Comprehensive regression summary
        """
        # Load results from files
        baseline_result = self.load_extraction_result(baseline_file)
        current_result = self.load_extraction_result(current_file)

        # Extract version information from filenames if not provided
        if baseline_version is None:
            baseline_version = Path(baseline_file).stem
        if current_version is None:
            current_version = Path(current_file).stem

        return self.compare_extraction_results(
            baseline_result, current_result, baseline_version, current_version
        )

    def save_regression_report(
        self,
        summary: RegressionSummary,
        output_path: str | Path,
        format: str = "json",
    ) -> None:
        """
        Save regression comparison report

        Args:
            summary: Regression summary to save
            output_path: Output file path
            format: Output format ("json" or "markdown")
        """
        output_path = Path(output_path)

        if format.lower() == "json":
            # Convert to JSON-serializable format
            report_data = {
                "baseline_version": summary.baseline_version,
                "current_version": summary.current_version,
                "timestamp": summary.timestamp.isoformat(),
                "overall_stability_score": summary.overall_stability_score,
                "entities": {
                    "added": summary.entities_added,
                    "removed": summary.entities_removed,
                    "modified": summary.entities_modified,
                },
                "relationships": {
                    "added": summary.relationships_added,
                    "removed": summary.relationships_removed,
                    "modified": summary.relationships_modified,
                },
                "structural": {
                    "connectivity_changed": summary.connectivity_changed,
                    "component_changes": summary.component_changes,
                    "density_change": summary.density_change,
                },
                "performance": {
                    "execution_time_change": summary.execution_time_change,
                    "memory_usage_change": summary.memory_usage_change,
                },
                "significant_changes": [
                    {
                        "change_type": change.change_type,
                        "item_type": change.item_type,
                        "item_id": change.item_id,
                        "description": change.description,
                        "impact_score": change.impact_score,
                        "details": change.details,
                    }
                    for change in summary.significant_changes
                ],
                "recommendations": summary.recommendations,
                "classification": {
                    "regression_detected": summary.regression_detected,
                    "improvement_detected": summary.improvement_detected,
                    "neutral_change": summary.neutral_change,
                },
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, default=str)

        elif format.lower() == "markdown":
            # Generate markdown report
            report_lines = [
                "# Extraction Regression Report",
                "",
                "## Summary",
                f"- **Baseline Version**: {summary.baseline_version}",
                f"- **Current Version**: {summary.current_version}",
                f"- **Generated**: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **Overall Stability Score**: {summary.overall_stability_score:.3f}",
                "",
                "## Classification",
                f"- {'🔴' if summary.regression_detected else '🟢'} **Regression Detected**: {summary.regression_detected}",
                f"- {'🟢' if summary.improvement_detected else '⚪'} **Improvement Detected**: {summary.improvement_detected}",
                f"- {'⚪' if summary.neutral_change else '🔵'} **Neutral Change**: {summary.neutral_change}",
                "",
                "## Entity Changes",
                f"- Added: {summary.entities_added}",
                f"- Removed: {summary.entities_removed}",
                f"- Modified: {summary.entities_modified}",
                "",
                "## Relationship Changes",
                f"- Added: {summary.relationships_added}",
                f"- Removed: {summary.relationships_removed}",
                f"- Modified: {summary.relationships_modified}",
                "",
                "## Structural Changes",
                f"- Density Change: {summary.density_change:+.4f}",
                f"- Connectivity Changed: {summary.connectivity_changed}",
                f"- Component Changes: {summary.component_changes}",
                "",
                "## Performance Changes",
                f"- Execution Time Change: {summary.execution_time_change:+.2f}s",
                f"- Memory Usage Change: {summary.memory_usage_change:+d}",
                "",
                "## Significant Changes",
            ]

            if summary.significant_changes:
                for change in summary.significant_changes:
                    report_lines.extend(
                        [
                            "",
                            f"### {change.item_type.title()} {change.change_type.title()}: {change.item_id}",
                            f"- **Description**: {change.description}",
                            f"- **Impact Score**: {change.impact_score:.3f}",
                            f"- **Details**: {json.dumps(change.details, indent=2)}",
                        ]
                    )
            else:
                report_lines.extend(["", "No significant changes detected."])

            report_lines.extend(["", "## Recommendations"])

            for rec in summary.recommendations:
                report_lines.append(f"- {rec}")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))

        else:
            raise ValueError(f"Unsupported output format: {format}")
