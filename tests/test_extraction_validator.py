"""
Comprehensive tests for the CLI Extraction Validator

Tests all components of the extraction validation system including
validation logic, structural analysis, gold standard management,
and regression comparison.
"""

import json
import tempfile
from pathlib import Path

import pytest

from validation.extraction_validator import (
    EntityValidationResult,
    ExtractionValidationResult,
    ExtractionValidator,
    RelationshipValidationResult,
    StructuralValidationResult,
)
from validation.gold_standard_manager import (
    GoldStandardCase,
    GoldStandardManager,
    ValidationResult,
)
from validation.regression_comparator import (
    RegressionComparator,
    RegressionSummary,
)
from validation.structural_analysis import StructuralAnalyzer, StructuralMetrics


class TestExtractionValidator:
    """Test cases for ExtractionValidator"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return ExtractionValidator(tolerance=0.8)

    @pytest.fixture
    def sample_entities(self):
        """Sample entities for testing"""
        return [
            {
                "id": "Apple Inc.",
                "entity_type": "Organization",
                "description": "Tech company",
            },
            {"id": "Steve Jobs", "entity_type": "Person", "description": "Co-founder"},
            {"id": "Cupertino", "entity_type": "Location", "description": "City"},
            {"id": "California", "entity_type": "Location", "description": "State"},
        ]

    @pytest.fixture
    def sample_relationships(self):
        """Sample relationships for testing"""
        return [
            {"src_id": "Steve Jobs", "tgt_id": "Apple Inc.", "keywords": "founded"},
            {
                "src_id": "Apple Inc.",
                "tgt_id": "Cupertino",
                "keywords": "headquartered",
            },
            {"src_id": "Cupertino", "tgt_id": "California", "keywords": "located in"},
        ]

    @pytest.fixture
    def gold_case(self):
        """Sample gold standard case"""
        return {
            "id": "test_case_1",
            "name": "Test Case",
            "description": "Test description",
            "text": "Apple Inc. is a company founded by Steve Jobs in Cupertino.",
            "expected_entities": [
                {"name": "Apple Inc.", "type": "Organization"},
                {"name": "Steve Jobs", "type": "Person"},
                {"name": "Cupertino", "type": "Location"},
            ],
            "expected_relationships": [
                {
                    "source": "Steve Jobs",
                    "target": "Apple Inc.",
                    "keywords": ["founded"],
                },
                {
                    "source": "Apple Inc.",
                    "target": "Cupertino",
                    "keywords": ["located"],
                },
            ],
            "structural_checks": {
                "min_entities": 3,
                "min_relationships": 2,
                "graph_connectivity": True,
            },
        }

    def test_normalize_name(self, validator):
        """Test name normalization"""
        assert validator.normalize_name("the Apple Inc.") == "apple inc."
        assert validator.normalize_name("  Steve Jobs  ") == "steve jobs"
        assert validator.normalize_name("a Company") == "company"

    def test_find_entity_match(self, validator, sample_entities):
        """Test entity matching"""
        # Exact match
        match = validator.find_entity_match("Steve Jobs", sample_entities)
        assert match is not None
        assert match["id"] == "Steve Jobs"

        # Partial match
        match = validator.find_entity_match("Apple", sample_entities)
        assert match is not None
        assert "Apple" in match["id"]

        # No match
        match = validator.find_entity_match("Nonexistent", sample_entities)
        assert match is None

    def test_find_relationship_match(
        self, validator, sample_relationships, sample_entities
    ):
        """Test relationship matching"""
        expected_rel = {
            "source": "Steve Jobs",
            "target": "Apple Inc.",
            "keywords": ["founded"],
        }

        match = validator.find_relationship_match(
            expected_rel, sample_relationships, sample_entities
        )
        assert match is not None
        assert match["src_id"] == "Steve Jobs"
        assert match["tgt_id"] == "Apple Inc."

    @pytest.mark.asyncio
    async def test_validate_entities(self, validator, sample_entities):
        """Test entity validation"""
        expected_entities = [
            {"name": "Apple Inc.", "type": "Organization"},
            {"name": "Steve Jobs", "type": "Person"},
            {"name": "Cupertino", "type": "Location"},
        ]

        result = await validator.validate_entities(sample_entities, expected_entities)

        assert isinstance(result, EntityValidationResult)
        assert result.expected_count == 3
        assert result.actual_count == len(sample_entities)
        assert result.fuzzy_match_score >= 0.8
        assert len(result.missing_entities) == 0

    @pytest.mark.asyncio
    async def test_validate_relationships(
        self, validator, sample_relationships, sample_entities
    ):
        """Test relationship validation"""
        expected_relationships = [
            {"source": "Steve Jobs", "target": "Apple Inc.", "keywords": ["founded"]},
            {"source": "Apple Inc.", "target": "Cupertino", "keywords": ["located"]},
        ]

        result = await validator.validate_relationships(
            sample_relationships, expected_relationships, sample_entities
        )

        assert isinstance(result, RelationshipValidationResult)
        assert result.expected_count == 2
        assert result.actual_count == len(sample_relationships)
        assert result.keyword_match_score >= 0.5

    def test_analyze_graph_structure(
        self, validator, sample_entities, sample_relationships
    ):
        """Test graph structure analysis"""
        result = validator.analyze_graph_structure(
            sample_entities, sample_relationships
        )

        assert isinstance(result, StructuralValidationResult)
        assert result.graph_connectivity is True
        assert result.connected_components == 1
        assert len(result.isolation_issues) == 0

    @pytest.mark.asyncio
    async def test_validate_against_gold_standard(self, validator, gold_case):
        """Test gold standard validation"""
        extraction_result = {
            "entities": [
                {"id": "Apple Inc.", "entity_type": "Organization"},
                {"id": "Steve Jobs", "entity_type": "Person"},
                {"id": "Cupertino", "entity_type": "Location"},
            ],
            "relationships": [
                {"src_id": "Steve Jobs", "tgt_id": "Apple Inc.", "keywords": "founded"},
                {"src_id": "Apple Inc.", "tgt_id": "Cupertino", "keywords": "located"},
            ],
        }

        result = await validator.validate_against_gold_standard(
            extraction_result, gold_case
        )

        assert isinstance(result, ExtractionValidationResult)
        assert result.gold_case_id == "test_case_1"
        assert result.overall_score >= 0.7
        assert isinstance(result.passed, bool)


class TestStructuralAnalyzer:
    """Test cases for StructuralAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return StructuralAnalyzer()

    @pytest.fixture
    def sample_graph_data(self):
        """Sample graph data"""
        entities = [
            {"id": "A", "type": "Entity"},
            {"id": "B", "type": "Entity"},
            {"id": "C", "type": "Entity"},
        ]
        relationships = [
            {"src_id": "A", "tgt_id": "B", "keywords": "relates"},
            {"src_id": "B", "tgt_id": "C", "keywords": "connects"},
        ]
        return entities, relationships

    def test_create_graph(self, analyzer, sample_graph_data):
        """Test graph creation"""
        entities, relationships = sample_graph_data
        G = analyzer.create_graph(entities, relationships)

        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
        assert "A" in G.nodes
        assert "B" in G.nodes
        assert "C" in G.nodes

    def test_calculate_basic_metrics(self, analyzer, sample_graph_data):
        """Test basic metrics calculation"""
        entities, relationships = sample_graph_data
        G = analyzer.create_graph(entities, relationships)

        metrics = analyzer.calculate_basic_metrics(G)

        assert metrics["node_count"] == 3
        assert metrics["edge_count"] == 2
        assert metrics["density"] == 2 / 3  # 2 edges / (3*2) possible edges

    def test_calculate_connectivity_metrics(self, analyzer, sample_graph_data):
        """Test connectivity metrics calculation"""
        entities, relationships = sample_graph_data
        G = analyzer.create_graph(entities, relationships)

        metrics = analyzer.calculate_connectivity_metrics(G)

        assert metrics["is_connected"] is True
        assert metrics["connected_components"] == 1

    def test_analyze_comprehensive(self, analyzer, sample_graph_data):
        """Test comprehensive analysis"""
        entities, relationships = sample_graph_data
        metrics = analyzer.analyze_comprehensive(entities, relationships)

        assert isinstance(metrics, StructuralMetrics)
        assert metrics.node_count == 3
        assert metrics.edge_count == 2
        assert metrics.is_connected is True

    def test_validate_structure_requirements(self, analyzer):
        """Test structure requirements validation"""
        metrics = StructuralMetrics(
            node_count=3,
            edge_count=2,
            density=0.3,
            is_connected=True,
            connected_components=1,
            largest_component_size=3,
            diameter=None,
            average_path_length=None,
            max_path_length=None,
            average_degree=1.3,
            max_degree=2,
            min_degree=1,
            clustering_coefficient=0.0,
            transitivity=0.0,
            isolated_nodes=[],
            weakly_connected_components=1,
            bridges=[],
            articulation_points=[],
        )

        requirements = {
            "min_entities": 2,
            "min_relationships": 1,
            "graph_connectivity": True,
        }

        passed, issues = analyzer.validate_structure_requirements(metrics, requirements)

        assert passed is True
        assert len(issues) == 0


class TestGoldStandardManager:
    """Test cases for GoldStandardManager"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create manager instance for testing"""
        return GoldStandardManager(data_dir=temp_dir)

    def test_create_case(self, manager):
        """Test case creation"""
        case = manager.create_case(
            name="Test Case",
            description="Test description",
            text="Test text",
            expected_entities=[{"name": "Test", "type": "Entity"}],
            expected_relationships=[
                {"source": "A", "target": "B", "keywords": ["relates"]}
            ],
        )

        assert isinstance(case, GoldStandardCase)
        assert case.name == "Test Case"
        assert case.description == "Test description"
        assert len(case.expected_entities) == 1
        assert len(case.expected_relationships) == 1
        assert case.id in manager.cases

    def test_get_case(self, manager):
        """Test case retrieval"""
        # Create a case first
        case = manager.create_case(
            name="Test Case",
            description="Test description",
            text="Test text",
            expected_entities=[],
            expected_relationships=[],
        )

        # Retrieve it
        retrieved_case = manager.get_case(case.id)

        assert retrieved_case is not None
        assert retrieved_case.id == case.id
        assert retrieved_case.name == case.name

    def test_list_cases(self, manager):
        """Test case listing"""
        # Create multiple cases
        manager.create_case("Case 1", "Desc 1", "Text 1", [], [], tags=["tag1"])
        manager.create_case("Case 2", "Desc 2", "Text 2", [], [], tags=["tag2"])
        manager.create_case("Case 3", "Desc 3", "Text 3", [], [], difficulty="hard")

        # List all cases
        all_cases = manager.list_cases()
        assert len(all_cases) == 3

        # Filter by tag
        tag_cases = manager.list_cases(tags=["tag1"])
        assert len(tag_cases) == 1

        # Filter by difficulty
        hard_cases = manager.list_cases(difficulty="hard")
        assert len(hard_cases) == 1

    def test_update_case(self, manager):
        """Test case updating"""
        # Create a case
        case = manager.create_case(
            name="Original Name",
            description="Original description",
            text="Original text",
            expected_entities=[],
            expected_relationships=[],
        )

        # Update it
        updated_case = manager.update_case(
            case.id, name="Updated Name", description="Updated description"
        )

        assert updated_case is not None
        assert updated_case.name == "Updated Name"
        assert updated_case.description == "Updated description"
        assert updated_case.text == "Original text"  # Unchanged

    def test_delete_case(self, manager):
        """Test case deletion"""
        # Create a case
        case = manager.create_case(
            name="To Delete",
            description="Will be deleted",
            text="Text",
            expected_entities=[],
            expected_relationships=[],
        )

        # Verify it exists
        assert manager.get_case(case.id) is not None

        # Delete it
        deleted = manager.delete_case(case.id)

        assert deleted is True
        assert manager.get_case(case.id) is None

    def test_get_statistics(self, manager):
        """Test statistics generation"""
        # Create test cases with different properties
        manager.create_case("Easy Case", "Desc", "Text", [], [], difficulty="easy")
        manager.create_case("Hard Case", "Desc", "Text", [], [], difficulty="hard")
        manager.create_case("Tagged Case", "Desc", "Text", [], [], tags=["special"])

        stats = manager.get_statistics()

        assert stats["total_cases"] == 3
        assert stats["by_difficulty"]["easy"] == 1
        assert stats["by_difficulty"]["hard"] == 1
        assert stats["by_tags"]["special"] == 1


class TestRegressionComparator:
    """Test cases for RegressionComparator"""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance for testing"""
        return RegressionComparator(tolerance=0.1, min_impact_score=0.1)

    @pytest.fixture
    def baseline_result(self):
        """Baseline extraction result"""
        return {
            "entities": [
                {
                    "id": "Entity1",
                    "entity_type": "Person",
                    "description": "First entity",
                },
                {
                    "id": "Entity2",
                    "entity_type": "Organization",
                    "description": "Second entity",
                },
            ],
            "relationships": [
                {"src_id": "Entity1", "tgt_id": "Entity2", "keywords": "works_at"}
            ],
        }

    @pytest.fixture
    def current_result(self):
        """Current extraction result with some changes"""
        return {
            "entities": [
                {
                    "id": "Entity1",
                    "entity_type": "Person",
                    "description": "First entity",
                },
                {
                    "id": "Entity2",
                    "entity_type": "Company",
                    "description": "Modified entity",
                },  # Changed
                {
                    "id": "Entity3",
                    "entity_type": "Location",
                    "description": "New entity",
                },  # Added
            ],
            "relationships": [
                {
                    "src_id": "Entity1",
                    "tgt_id": "Entity2",
                    "keywords": "employed_by",
                },  # Modified
                {
                    "src_id": "Entity2",
                    "tgt_id": "Entity3",
                    "keywords": "located_in",
                },  # Added
            ],
        }

    def test_compare_extraction_results(
        self, comparator, baseline_result, current_result
    ):
        """Test extraction result comparison"""
        summary = comparator.compare_extraction_results(
            baseline_result, current_result, "v1.0", "v2.0"
        )

        assert isinstance(summary, RegressionSummary)
        assert summary.baseline_version == "v1.0"
        assert summary.current_version == "v2.0"
        assert summary.entities_added == 1
        assert summary.entities_modified == 1
        assert summary.relationships_added == 1
        assert summary.relationships_modified == 1
        assert 0.0 <= summary.overall_stability_score <= 1.0

    def test_calculate_entity_impact(self, comparator):
        """Test entity impact calculation"""
        person = {"entity_type": "Person", "properties": {"age": 30}}
        org = {"entity_type": "Organization", "properties": {"employees": 100}}
        concept = {"entity_type": "Concept", "properties": {}}

        person_impact = comparator._calculate_entity_impact(person)
        org_impact = comparator._calculate_entity_impact(org)
        concept_impact = comparator._calculate_entity_impact(concept)

        assert 0.0 <= person_impact <= 1.0
        assert 0.0 <= org_impact <= 1.0
        assert 0.0 <= concept_impact <= 1.0
        assert org_impact > concept_impact  # Organization should have higher impact

    def test_calculate_relationship_impact(self, comparator):
        """Test relationship impact calculation"""
        important_rel = {"keywords": "founded", "properties": {"date": "1976"}}
        normal_rel = {"keywords": "relates_to", "properties": {}}

        important_impact = comparator._calculate_relationship_impact(important_rel)
        normal_impact = comparator._calculate_relationship_impact(normal_rel)

        assert 0.0 <= important_impact <= 1.0
        assert 0.0 <= normal_impact <= 1.0
        assert (
            important_impact > normal_impact
        )  # Important relationship should have higher impact

    def test_load_and_save_result(self, comparator, baseline_result):
        """Test loading and saving extraction results"""
        # Test saving
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(baseline_result, f)
            temp_path = f.name

        try:
            # Test loading
            loaded_result = comparator.load_extraction_result(temp_path)
            assert loaded_result == baseline_result
        finally:
            Path(temp_path).unlink()

    def test_save_regression_report(self, comparator, baseline_result, current_result):
        """Test saving regression report"""
        summary = comparator.compare_extraction_results(
            baseline_result, current_result, "v1.0", "v2.0"
        )

        # Test JSON format
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = f.name

        try:
            comparator.save_regression_report(summary, json_path, "json")

            # Verify file was created and contains valid JSON
            assert Path(json_path).exists()
            with open(json_path) as f:
                data = json.load(f)
                assert "baseline_version" in data
                assert "current_version" in data
                assert "overall_stability_score" in data
        finally:
            Path(json_path).unlink()

        # Test Markdown format
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            md_path = f.name

        try:
            comparator.save_regression_report(summary, md_path, "markdown")

            # Verify file was created and contains markdown
            assert Path(md_path).exists()
            with open(md_path) as f:
                content = f.read()
                assert "# Extraction Regression Report" in content
                assert "## Summary" in content
        finally:
            Path(md_path).unlink()


class TestIntegration:
    """Integration tests for the complete extraction validation system"""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self):
        """Test complete validation workflow"""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize components
            manager = GoldStandardManager(data_dir=temp_path)
            validator = ExtractionValidator(tolerance=0.8)

            # Create gold standard case
            case = manager.create_case(
                name="Integration Test Case",
                description="Test case for integration testing",
                text="Apple Inc. was founded by Steve Jobs in Cupertino, California.",
                expected_entities=[
                    {"name": "Apple Inc.", "type": "Organization"},
                    {"name": "Steve Jobs", "type": "Person"},
                    {"name": "Cupertino", "type": "Location"},
                    {"name": "California", "type": "Location"},
                ],
                expected_relationships=[
                    {
                        "source": "Steve Jobs",
                        "target": "Apple Inc.",
                        "keywords": ["founded"],
                    },
                    {
                        "source": "Apple Inc.",
                        "target": "Cupertino",
                        "keywords": ["located"],
                    },
                    {"source": "Cupertino", "target": "California", "keywords": ["in"]},
                ],
                structural_checks={
                    "min_entities": 4,
                    "min_relationships": 3,
                    "graph_connectivity": True,
                },
            )

            # Create extraction result (perfect match)
            extraction_result = {
                "entities": [
                    {"id": "Apple Inc.", "entity_type": "Organization"},
                    {"id": "Steve Jobs", "entity_type": "Person"},
                    {"id": "Cupertino", "entity_type": "Location"},
                    {"id": "California", "entity_type": "Location"},
                ],
                "relationships": [
                    {
                        "src_id": "Steve Jobs",
                        "tgt_id": "Apple Inc.",
                        "keywords": "founded",
                    },
                    {
                        "src_id": "Apple Inc.",
                        "tgt_id": "Cupertino",
                        "keywords": "located",
                    },
                    {"src_id": "Cupertino", "tgt_id": "California", "keywords": "in"},
                ],
            }

            # Run validation
            result = await validator.validate_against_gold_standard(
                extraction_result, case.__dict__
            )

            # Verify results
            assert isinstance(result, ExtractionValidationResult)
            assert result.gold_case_id == case.id
            assert result.passed is True
            assert result.overall_score >= 0.9

            # Save validation result
            validation_result = ValidationResult(
                case_id=result.gold_case_id,
                passed=result.passed,
                score=result.overall_score,
                entity_validation=result.entity_validation.__dict__,
                relationship_validation=result.relationship_validation.__dict__,
                structural_validation=result.structural_validation.__dict__,
                execution_time=result.validation_duration_seconds,
                timestamp=result.timestamp,
                recommendations=result.recommendations,
            )
            manager.save_validation_result(validation_result)

            # Verify result was saved
            history = manager.get_validation_history(case.id)
            assert len(history) == 1
            assert history[0]["case_id"] == case.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
