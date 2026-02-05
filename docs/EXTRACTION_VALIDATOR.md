# CLI Extraction Validator for Structural Link Regression Testing

## Overview

The CLI Extraction Validator provides comprehensive validation of LightRAG extraction results, including entity consistency, relationship integrity, and structural graph analysis. It integrates seamlessly with the existing LightRAG validation infrastructure and uses a gold standard test framework approach.

## Features

- **Comprehensive Validation**: Entity consistency, relationship integrity, and structural links
- **Gold Standard Testing**: Extensive test case management and comparison
- **Regression Testing**: Compare extraction results across different runs/versions
- **Structural Analysis**: Graph connectivity, path analysis, and isolation detection
- **CLI Integration**: Seamless integration with existing validation commands
- **Flexible Reporting**: Text and JSON output formats
- **Configurable Tolerances**: Adjustable validation strictness

## Installation & Setup

The CLI Extraction Validator is integrated into the LightRAG validation system. No additional installation required.

## Quick Start

### 1. List Available Gold Standard Cases

```bash
python -m validation.cli extract gold list-cases
```

### 2. View Gold Standard Statistics

```bash
python -m validation.cli extract gold stats
```

### 3. Validate Extraction Against Gold Standard

```bash
python -m validation.cli extract validate-extraction \
  "Apple Inc. was founded by Steve Jobs in Cupertino, California." \
  --gold-standard "structural_basic_1"
```

### 4. Compare Two Extraction Results for Regression

```bash
python -m validation.cli extract compare \
  baseline_extraction.json \
  current_extraction.json
```

## Command Reference

### Main Commands

```bash
python -m validation.cli extract [OPTIONS] COMMAND
```

#### Options
- `--tolerance FLOAT`: Fuzzy matching tolerance for validation (0.0-1.0, default: 0.8)

#### Subcommands

##### `validate-extraction` - Validate extraction against gold standard

```bash
python -m validation.cli extract validate-extraction INPUT_TEXT --gold-standard CASE_ID [OPTIONS]
```

**Arguments:**
- `INPUT_TEXT`: Text to validate extraction against

**Required Options:**
- `--gold-standard CASE_ID`: Gold standard case ID to validate against

**Optional Options:**
- `--tolerance FLOAT`: Override default tolerance for this validation
- `--output [text|json]`: Output format (default: text)

**Example:**
```bash
python -m validation.cli extract validate-extraction \
  "Apple Inc. is a technology company founded by Steve Jobs." \
  --gold-standard "structural_basic_1" \
  --output json
```

##### `compare` - Compare two extraction results for regression

```bash
python -m validation.cli extract compare RUN1 RUN2 [OPTIONS]
```

**Arguments:**
- `RUN1`: Baseline extraction result file or identifier
- `RUN2`: Current extraction result file or identifier

**Optional Options:**
- `--tolerance FLOAT`: Override default tolerance for comparison
- `--output [text|json]`: Output format (default: text)

**Example:**
```bash
python -m validation.cli extract compare \
  baseline_results.json \
  current_results.json \
  --output markdown > regression_report.md
```

##### `gold` - Gold standard test case management

```bash
python -m validation.cli extract gold SUBCOMMAND
```

**Subcommands:**

###### `list-cases` - List available gold standard cases

```bash
python -m validation.cli extract gold list-cases [OPTIONS]
```

**Options:**
- `--tags TEXT...`: Filter by tags (can specify multiple)
- `--difficulty [easy|medium|hard]`: Filter by difficulty level
- `--domain TEXT`: Filter by domain
- `--limit INTEGER`: Maximum number of cases to show (default: 20)
- `--output [text|json]`: Output format (default: text)

**Example:**
```bash
python -m validation.cli extract gold list-cases \
  --tags structural basic \
  --difficulty easy \
  --limit 5
```

###### `add-case` - Add a new gold standard test case

```bash
python -m validation.cli extract gold add-case [OPTIONS]
```

**Required Options:**
- `--name TEXT`: Test case name
- `--description TEXT`: Test case description
- `--text TEXT`: Input text for extraction

**Optional Options:**
- `--entities TEXT`: Expected entities (format: name:type,name:type)
- `--relationships TEXT`: Expected relationships (format: source->target:keywords)
- `--tags TEXT...`: Tags for test case (can specify multiple)
- `--difficulty [easy|medium|hard]`: Difficulty level (default: medium)
- `--domain TEXT`: Domain category (default: general)

**Example:**
```bash
python -m validation.cli extract gold add-case \
  --name "Tech Company Test" \
  --description "Basic technology company extraction test" \
  --text "Apple Inc. was founded by Steve Jobs and is headquartered in Cupertino." \
  --entities "Apple Inc.:Organization,Steve Jobs:Person,Cupertino:Location" \
  --relationships "founded:Steve Jobs->Apple Inc.",headquartered:Apple Inc.->Cupertino" \
  --tags technology structural \
  --difficulty easy
```

###### `delete-case` - Delete a gold standard test case

```bash
python -m validation.cli extract gold delete-case CASE_ID
```

**Example:**
```bash
python -m validation.cli extract gold delete-case "old_test_case_123"
```

###### `stats` - Show gold standard statistics

```bash
python -m validation.cli extract gold stats
```

## Gold Standard Test Cases

### Included Test Cases

The CLI Extraction Validator comes with several pre-configured gold standard test cases:

#### 1. Structural Basic Test (`structural_basic_1`)
- **Description**: Simple test case with connected entities and relationships
- **Difficulty**: Easy
- **Domain**: Technology
- **Text**: "Apple Inc. is a technology company founded by Steve Jobs. It is headquartered in Cupertino, California."
- **Expected Entities**: 4 (Apple Inc., Steve Jobs, Cupertino, California)
- **Expected Relationships**: 3
- **Structural Requirements**: Graph connectivity, max path length 3

#### 2. Structural Complex Test (`structural_complex_1`)
- **Description**: Complex test case with multiple interconnected entities
- **Difficulty**: Medium
- **Domain**: Technology
- **Text**: "Microsoft was founded by Bill Gates and Paul Allen in 1975..."
- **Expected Entities**: 8
- **Expected Relationships**: 7
- **Structural Requirements**: Graph connectivity, minimum density

#### 3. Scientific Concept Test (`structural_scientific_1`)
- **Description**: Test case involving scientific concepts and relationships
- **Difficulty**: Hard
- **Domain**: Science
- **Text**: "Albert Einstein developed theory of relativity while working at Swiss Patent Office..."
- **Expected Entities**: 9
- **Expected Relationships**: 8
- **Structural Requirements**: Graph connectivity, clustering requirements

#### 4. Isolation Detection Test (`structural_isolation_test`)
- **Description**: Test case with intentionally isolated entities
- **Difficulty**: Medium
- **Domain**: Testing
- **Purpose**: Tests isolation detection capabilities

## Validation Metrics

### Entity Validation Metrics

- **Fuzzy Match Score**: 0.0-1.0, measures entity name matching accuracy
- **Type Consistency Score**: 0.0-1.0, measures entity type accuracy
- **Missing Entities**: List of expected entities not found
- **Extra Entities**: List of unexpected entities extracted

### Relationship Validation Metrics

- **Keyword Match Score**: 0.0-1.0, measures relationship keyword accuracy
- **Missing Relationships**: List of expected relationships not found
- **Extra Relationships**: List of unexpected relationships extracted

### Structural Validation Metrics

- **Graph Connectivity**: Boolean indicating if graph is connected
- **Connected Components**: Number of disconnected components
- **Clustering Coefficient**: Graph clustering metric (0.0-1.0)
- **Isolation Issues**: List of isolated nodes

### Overall Validation Score

- **Composite Score**: 0.0-1.0, weighted average of all validation metrics
- **Pass/Fail Status**: Based on tolerance thresholds and structural requirements

## Configuration

### Tolerance Settings

Validation tolerances can be configured at multiple levels:

1. **Global Default** (0.8): Set via `--tolerance` on main extract command
2. **Per-Validation Override**: Set via `--tolerance` on specific commands
3. **Gold Standard Specific**: Set in individual gold standard case definitions

### Structural Requirements

Gold standard cases can define structural validation requirements:

```json
{
  "structural_checks": {
    "min_entities": 3,
    "min_relationships": 2,
    "graph_connectivity": true,
    "max_path_length": 4,
    "min_density": 0.1,
    "allow_isolated_nodes": false,
    "expected_isolated_nodes": 0
  }
}
```

## Output Formats

### Text Output

Human-readable format with colored indicators:
- ✅ PASSED / ❌ FAILED status
- 📊 Validation scores
- 🔹 Entity details
- 🔗 Relationship details
- 🏗️ Structural analysis
- 💡 Recommendations

### JSON Output

Machine-readable format with complete validation data:

```json
{
  "case_id": "structural_basic_1",
  "passed": true,
  "overall_score": 0.95,
  "entity_validation": {
    "expected_count": 4,
    "actual_count": 4,
    "fuzzy_match_score": 0.9,
    "type_consistency_score": 1.0,
    "missing_entities": [],
    "extra_entities": []
  },
  "relationship_validation": {
    "expected_count": 3,
    "actual_count": 3,
    "keyword_match_score": 0.85,
    "missing_relationships": [],
    "extra_relationships": []
  },
  "structural_validation": {
    "graph_connectivity": true,
    "connected_components": 1,
    "clustering_coefficient": 0.333,
    "isolation_issues": []
  },
  "recommendations": [],
  "validation_duration_seconds": 0.12
}
```

## Integration Examples

### 1. CI/CD Pipeline Integration

```bash
#!/bin/bash
# Extract validation results
python -m validation.cli extract validate-extraction \
  "$TEST_TEXT" \
  --gold-standard "structural_basic_1" \
  --output json > validation_results.json

# Check if validation passed
SCORE=$(jq -r '.overall_score' validation_results.json)
PASSED=$(jq -r '.passed' validation_results.json)

if [[ "$PASSED" != "true" || $(echo "$SCORE < 0.8" | bc -l) -eq 1 ]]; then
  echo "❌ Validation failed with score $SCORE"
  exit 1
fi

echo "✅ Validation passed with score $SCORE"
```

### 2. Regression Testing Workflow

```bash
# Run baseline extraction
run_extraction baseline_data.txt baseline_results.json

# Run current extraction
run_extraction current_data.txt current_results.json

# Compare for regressions
python -m validation.cli extract compare \
  baseline_results.json \
  current_results.json \
  --output json > regression_report.json

# Check for regressions
REGRESSION=$(jq -r '.regression_detected' regression_report.json)
if [[ "$REGRESSION" == "true" ]]; then
  echo "🚨 Regression detected!"
  cat regression_report.json | jq '.recommendations[]'
  exit 1
fi

echo "✅ No regressions detected"
```

### 3. Batch Gold Standard Testing

```bash
#!/bin/bash
# Test against all gold standard cases
python -m validation.cli extract gold list-cases --output json | \
  jq -r '.[].id' | while read case_id; do
    echo "Testing case: $case_id"

    python -m validation.cli extract validate-extraction \
      "$(get_test_text_for_case $case_id)" \
      --gold-standard "$case_id" \
      --output json > "results/${case_id}.json"

    # Process results as needed
done
```

## Troubleshooting

### Common Issues

#### 1. Validation Always Fails
- Check tolerance settings
- Verify gold standard case expectations
- Ensure input text matches expectations

#### 2. JSON Parse Errors
- Validate JSON syntax in gold standard files
- Check for trailing commas or missing quotes
- Use JSON linter to verify syntax

#### 3. Missing Gold Standard Cases
- Verify data directory structure
- Check file permissions
- Ensure JSON files are valid

#### 4. Performance Issues
- Reduce test case complexity
- Increase tolerance for faster matching
- Use text output instead of JSON for large results

### Debug Mode

Enable verbose output for debugging:

```bash
python -m validation.cli extract validate-extraction \
  "test text" \
  --gold-standard "test_case" \
  --output json \
  --tolerance 0.5 \
  2>&1 | tee debug_output.log
```

## API Reference

### ExtractionValidator Class

```python
class ExtractionValidator:
    def __init__(self, tolerance: float = 0.8):
        """Initialize validator with fuzzy matching tolerance"""

    async def validate_against_gold_standard(
        self,
        extraction_result: Dict[str, Any],
        gold_case: Dict[str, Any]
    ) -> ExtractionValidationResult:
        """Validate extraction against gold standard case"""

    async def compare_extractions(
        self,
        baseline_result: Dict[str, Any],
        current_result: Dict[str, Any]
    ) -> ExtractionValidationResult:
        """Compare two extraction results"""
```

### GoldStandardManager Class

```python
class GoldStandardManager:
    def __init__(self, data_dir: Union[str, Path] = None):
        """Initialize with custom data directory"""

    def create_case(self, name: str, description: str, ... ) -> GoldStandardCase:
        """Create new gold standard test case"""

    def list_cases(self, tags: List[str] = None, ...) -> List[GoldStandardCase]:
        """List cases with optional filtering"""

    def get_case(self, case_id: str) -> Optional[GoldStandardCase]:
        """Get specific gold standard case"""

    def update_case(self, case_id: str, ...) -> Optional[GoldStandardCase]:
        """Update existing case"""
```

### StructuralAnalyzer Class

```python
class StructuralAnalyzer:
    def analyze_comprehensive(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> StructuralMetrics:
        """Perform comprehensive structural analysis"""

    def validate_structure_requirements(
        self,
        metrics: StructuralMetrics,
        requirements: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate against structural requirements"""
```

## Contributing

### Adding New Gold Standard Cases

1. Use the CLI to create new cases:
   ```bash
   python -m validation.cli extract gold add-case --name "New Case" ...
   ```

2. Or manually create JSON files in `tests/gold_standards/`

3. Follow the naming convention: `{category}_{description}_{id}.json`

### Extending Validation Logic

1. Modify `ExtractionValidator` class in `validation/extraction_validator.py`
2. Add new validation methods as needed
3. Update result data structures
4. Add corresponding tests

### Adding Structural Metrics

1. Extend `StructuralAnalyzer` class
2. Add new analysis methods
3. Update `StructuralMetrics` dataclass
4. Include in validation workflow

## License

This CLI Extraction Validator is part of the LightRAG project and follows the same licensing terms.
