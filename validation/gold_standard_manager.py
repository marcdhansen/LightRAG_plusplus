"""
Gold Standard Manager for Extraction Validation

Manages gold standard test cases for extraction validation,
including creation, loading, and maintenance of test cases.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class GoldStandardCase:
    """Gold standard test case for extraction validation"""

    id: str
    name: str
    description: str
    text: str

    # Expected extraction results
    expected_entities: list[dict[str, Any]]
    expected_relationships: list[dict[str, Any]]

    # Structural requirements
    structural_checks: dict[str, Any] = field(default_factory=dict)

    # Validation tolerances
    tolerances: dict[str, float] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    domain: str = "general"

    # Performance expectations
    expected_extraction_time: float | None = None
    max_memory_usage: int | None = None


@dataclass
class ValidationResult:
    """Result of gold standard validation"""

    case_id: str
    passed: bool
    score: float
    entity_validation: dict[str, Any]
    relationship_validation: dict[str, Any]
    structural_validation: dict[str, Any]
    execution_time: float
    timestamp: datetime
    recommendations: list[str] = field(default_factory=list)


class GoldStandardManager:
    """
    Manages gold standard test cases for extraction validation

    Provides functionality to create, load, update, and validate
    against gold standard test cases.
    """

    def __init__(self, data_dir: str | Path = None):
        """
        Initialize the gold standard manager

        Args:
            data_dir: Directory containing gold standard cases
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "tests" / "gold_standards"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Case files
        self.cases_file = self.data_dir / "extraction_cases.json"
        self.structural_cases_file = self.data_dir / "structural_cases.json"
        self.entity_cases_file = self.data_dir / "entity_consistency.json"
        self.relationship_cases_file = self.data_dir / "relationship_integrity.json"

        # Results directory
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Load existing cases
        self.cases = self._load_cases()

    def _load_cases(self) -> dict[str, GoldStandardCase]:
        """Load gold standard cases from files"""
        cases = {}

        # Load main extraction cases
        if self.cases_file.exists():
            try:
                with open(self.cases_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for case_data in data:
                        case = GoldStandardCase(**case_data)
                        cases[case.id] = case
            except Exception as e:
                print(f"Error loading main cases: {e}")

        # Load structural cases
        if self.structural_cases_file.exists():
            try:
                with open(self.structural_cases_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for case_data in data:
                        case = GoldStandardCase(**case_data)
                        cases[case.id] = case
            except Exception as e:
                print(f"Error loading structural cases: {e}")

        # Load other case files
        for case_file in [self.entity_cases_file, self.relationship_cases_file]:
            if case_file.exists():
                try:
                    with open(case_file, encoding="utf-8") as f:
                        data = json.load(f)
                    for case_data in data:
                        # Convert string dates to datetime objects
                        if "created_at" in case_data and isinstance(
                            case_data["created_at"], str
                        ):
                            case_data["created_at"] = datetime.fromisoformat(
                                case_data["created_at"]
                            )
                        if "updated_at" in case_data and isinstance(
                            case_data["updated_at"], str
                        ):
                            case_data["updated_at"] = datetime.fromisoformat(
                                case_data["updated_at"]
                            )

                        case = GoldStandardCase(**case_data)
                        cases[case.id] = case
                except Exception as e:
                    print(f"Error loading cases from {case_file}: {e}")

        return cases

    def _save_cases(self, cases: dict[str, GoldStandardCase] = None) -> None:
        """Save gold standard cases to files"""
        if cases is None:
            cases = self.cases

        # Categorize cases by type
        structural_cases = []
        entity_cases = []
        relationship_cases = []
        main_cases = []

        for case in cases.values():
            case_dict = self._case_to_dict(case)

            if "structural" in case.tags:
                structural_cases.append(case_dict)
            elif "entity_consistency" in case.tags:
                entity_cases.append(case_dict)
            elif "relationship_integrity" in case.tags:
                relationship_cases.append(case_dict)
            else:
                main_cases.append(case_dict)

        # Save to appropriate files
        try:
            # Main cases
            with open(self.cases_file, "w", encoding="utf-8") as f:
                json.dump(main_cases, f, indent=2, default=str)

            # Structural cases
            with open(self.structural_cases_file, "w", encoding="utf-8") as f:
                json.dump(structural_cases, f, indent=2, default=str)

            # Entity consistency cases
            with open(self.entity_cases_file, "w", encoding="utf-8") as f:
                json.dump(entity_cases, f, indent=2, default=str)

            # Relationship integrity cases
            with open(self.relationship_cases_file, "w", encoding="utf-8") as f:
                json.dump(relationship_cases, f, indent=2, default=str)

        except Exception as e:
            raise Exception(f"Error saving cases: {e}") from e

    def _case_to_dict(self, case: GoldStandardCase) -> dict[str, Any]:
        """Convert GoldStandardCase to dictionary"""
        created_at = case.created_at
        updated_at = case.updated_at

        return {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "text": case.text,
            "expected_entities": case.expected_entities,
            "expected_relationships": case.expected_relationships,
            "structural_checks": case.structural_checks,
            "tolerances": case.tolerances,
            "created_at": created_at.isoformat()
            if hasattr(created_at, "isoformat")
            else str(created_at),
            "updated_at": updated_at.isoformat()
            if hasattr(updated_at, "isoformat")
            else str(updated_at),
            "tags": case.tags,
            "difficulty": case.difficulty,
            "domain": case.domain,
            "expected_extraction_time": case.expected_extraction_time,
            "max_memory_usage": case.max_memory_usage,
        }

    def _generate_case_id(self, name: str) -> str:
        """Generate unique case ID from name"""
        # Clean up name
        clean_name = "".join(c.lower() for c in name if c.isalnum() or c in ["-", "_"])
        clean_name = clean_name.replace(" ", "_")

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{clean_name}_{timestamp}"

    def create_case(
        self,
        name: str,
        description: str,
        text: str,
        expected_entities: list[dict[str, Any]],
        expected_relationships: list[dict[str, Any]],
        structural_checks: dict[str, Any] = None,
        tolerances: dict[str, float] = None,
        tags: list[str] = None,
        difficulty: str = "medium",
        domain: str = "general",
    ) -> GoldStandardCase:
        """
        Create a new gold standard case

        Args:
            name: Case name
            description: Case description
            text: Input text for extraction
            expected_entities: Expected entities
            expected_relationships: Expected relationships
            structural_checks: Structural validation requirements
            tolerances: Validation tolerances
            tags: Case tags
            difficulty: Difficulty level
            domain: Domain category

        Returns:
            Created gold standard case
        """
        case_id = self._generate_case_id(name)

        case = GoldStandardCase(
            id=case_id,
            name=name,
            description=description,
            text=text,
            expected_entities=expected_entities,
            expected_relationships=expected_relationships,
            structural_checks=structural_checks or {},
            tolerances=tolerances or {},
            tags=tags or [],
            difficulty=difficulty,
            domain=domain,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.cases[case_id] = case
        self._save_cases()

        return case

    def get_case(self, case_id: str) -> GoldStandardCase | None:
        """Get a gold standard case by ID"""
        return self.cases.get(case_id)

    def list_cases(
        self,
        tags: list[str] = None,
        difficulty: str = None,
        domain: str = None,
        limit: int = None,
    ) -> list[GoldStandardCase]:
        """
        List gold standard cases with optional filtering

        Args:
            tags: Filter by tags
            difficulty: Filter by difficulty
            domain: Filter by domain
            limit: Maximum number of cases to return

        Returns:
            List of matching cases
        """
        cases = list(self.cases.values())

        # Apply filters
        if tags:
            cases = [c for c in cases if any(tag in c.tags for tag in tags)]

        if difficulty:
            cases = [c for c in cases if c.difficulty == difficulty]

        if domain:
            cases = [c for c in cases if c.domain == domain]

        # Sort by creation date (newest first)
        cases.sort(key=lambda c: c.created_at, reverse=True)

        # Apply limit
        if limit:
            cases = cases[:limit]

        return cases

    def update_case(
        self,
        case_id: str,
        name: str = None,
        description: str = None,
        text: str = None,
        expected_entities: list[dict[str, Any]] = None,
        expected_relationships: list[dict[str, Any]] = None,
        structural_checks: dict[str, Any] = None,
        tolerances: dict[str, float] = None,
        tags: list[str] = None,
        difficulty: str = None,
        domain: str = None,
    ) -> GoldStandardCase | None:
        """
        Update an existing gold standard case

        Args:
            case_id: Case ID to update
            name: New name (optional)
            description: New description (optional)
            text: New text (optional)
            expected_entities: New expected entities (optional)
            expected_relationships: New expected relationships (optional)
            structural_checks: New structural checks (optional)
            tolerances: New tolerances (optional)
            tags: New tags (optional)
            difficulty: New difficulty (optional)
            domain: New domain (optional)

        Returns:
            Updated case or None if not found
        """
        case = self.cases.get(case_id)
        if not case:
            return None

        # Update fields
        if name is not None:
            case.name = name
        if description is not None:
            case.description = description
        if text is not None:
            case.text = text
        if expected_entities is not None:
            case.expected_entities = expected_entities
        if expected_relationships is not None:
            case.expected_relationships = expected_relationships
        if structural_checks is not None:
            case.structural_checks = structural_checks
        if tolerances is not None:
            case.tolerances = tolerances
        if tags is not None:
            case.tags = tags
        if difficulty is not None:
            case.difficulty = difficulty
        if domain is not None:
            case.domain = domain

        case.updated_at = datetime.now()

        self._save_cases()

        return case

    def delete_case(self, case_id: str) -> bool:
        """Delete a gold standard case"""
        if case_id in self.cases:
            del self.cases[case_id]
            self._save_cases()
            return True
        return False

    def save_validation_result(self, result: ValidationResult) -> None:
        """Save validation result"""
        result_file = (
            self.results_dir
            / f"{result.case_id}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )

        result_dict = {
            "case_id": result.case_id,
            "passed": result.passed,
            "score": result.score,
            "entity_validation": result.entity_validation,
            "relationship_validation": result.relationship_validation,
            "structural_validation": result.structural_validation,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat(),
            "recommendations": result.recommendations,
        }

        try:
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving validation result: {e}")

    def get_validation_history(
        self, case_id: str = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get validation history"""
        history = []

        for result_file in self.results_dir.glob("*.json"):
            if case_id and not result_file.name.startswith(case_id):
                continue

            try:
                with open(result_file, encoding="utf-8") as f:
                    result_data = json.load(f)
                    history.append(result_data)
            except Exception as e:
                print(f"Error loading result from {result_file}: {e}")

        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return history[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about gold standard cases"""
        cases = list(self.cases.values())

        stats = {
            "total_cases": len(cases),
            "by_difficulty": {},
            "by_domain": {},
            "by_tags": {},
            "average_entities": 0,
            "average_relationships": 0,
        }

        if cases:
            # Difficulty distribution
            for difficulty in ["easy", "medium", "hard"]:
                stats["by_difficulty"][difficulty] = len(
                    [c for c in cases if c.difficulty == difficulty]
                )

            # Domain distribution
            stats["by_domain"] = {
                domain: len([c for c in cases if c.domain == domain])
                for domain in {c.domain for c in cases}
            }

            # Tag distribution
            all_tags = []
            for case in cases:
                all_tags.extend(case.tags)

            for tag in set(all_tags):
                stats["by_tags"][tag] = all_tags.count(tag)

            # Averages
            stats["average_entities"] = sum(
                len(case.expected_entities) for case in cases
            ) / len(cases)

            stats["average_relationships"] = sum(
                len(case.expected_relationships) for case in cases
            ) / len(cases)

        return stats

    def export_cases(
        self,
        output_file: str | Path,
        case_ids: list[str] = None,
        format: str = "json",
    ) -> None:
        """Export gold standard cases to file"""
        if case_ids:
            cases_to_export = {k: v for k, v in self.cases.items() if k in case_ids}
        else:
            cases_to_export = self.cases

        output_path = Path(output_file)

        if format.lower() == "json":
            cases_data = [self._case_to_dict(case) for case in cases_to_export.values()]

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cases_data, f, indent=2, default=str)

        elif format.lower() == "csv":
            # Export to CSV format (simplified)
            import csv

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "ID",
                        "Name",
                        "Description",
                        "Text",
                        "Entity Count",
                        "Relationship Count",
                        "Difficulty",
                        "Domain",
                        "Tags",
                    ]
                )

                for case in cases_to_export.values():
                    writer.writerow(
                        [
                            case.id,
                            case.name,
                            case.description,
                            case.text[:100] + "..."
                            if len(case.text) > 100
                            else case.text,
                            len(case.expected_entities),
                            len(case.expected_relationships),
                            case.difficulty,
                            case.domain,
                            ", ".join(case.tags),
                        ]
                    )

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_cases(self, input_file: str | Path, format: str = "json") -> int:
        """Import gold standard cases from file"""
        input_path = Path(input_file)
        imported_count = 0

        if format.lower() == "json":
            with open(input_path, encoding="utf-8") as f:
                cases_data = json.load(f)

                for case_data in cases_data:
                    case = GoldStandardCase(**case_data)
                    self.cases[case.id] = case
                    imported_count += 1

        elif format.lower() == "csv":
            # Import from CSV (basic reconstruction)
            import csv

            with open(input_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Create a basic case from CSV data
                    case = GoldStandardCase(
                        id=row["ID"],
                        name=row["Name"],
                        description=row["Description"],
                        text=row["Text"],
                        expected_entities=[],
                        expected_relationships=[],
                        difficulty=row.get("Difficulty", "medium"),
                        domain=row.get("Domain", "general"),
                        tags=row.get("Tags", "").split(", ") if row.get("Tags") else [],
                    )

                    self.cases[case.id] = case
                    imported_count += 1

        else:
            raise ValueError(f"Unsupported import format: {format}")

        if imported_count > 0:
            self._save_cases()

        return imported_count
