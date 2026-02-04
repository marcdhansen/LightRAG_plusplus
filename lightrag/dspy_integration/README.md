# DSPy Integration for LightRAG

This directory contains the phased DSPy integration approach for LightRAG.

## Phase 1: DSPy for Prompt Generation (Current Phase)

### Goals:
- Use DSPy optimizers to generate improved prompt variants
- Feed optimized prompts back into existing AB testing framework  
- Validate improvements with current metrics
- No disruption to existing infrastructure

### Structure:
```
dspy_integration/
├── __init__.py
├── config.py           # DSPy configuration
├── optimizers/         # DSPy optimization scripts
├── generators/         # Prompt generation modules
├── evaluators/         # Evaluation frameworks
└── prompts/           # Generated optimized prompts
```

## Usage:
```python
from lightrag.dspy_integration.generators.entity_extractor import EntityExtractorGenerator

# Generate optimized prompts
generator = EntityExtractorGenerator()
optimized_prompts = generator.optimize_prompts(training_data, num_candidates=5)
```

## Integration with AB Testing:
Generated prompts are automatically formatted for compatibility with the existing AB testing framework in `/lightrag/prompts/ab_testing.py`.