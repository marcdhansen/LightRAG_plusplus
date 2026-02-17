#!/usr/bin/env python3
"""Quick test for Einstein case - fix Theory of Relativity extraction"""

import time
import langextract as lx
from langextract.data import ExampleData, Extraction

text = (
    "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
    "He is best known for developing the Theory of Relativity."
)

# Refined prompt with explicit Theory extraction
prompt = """Extract entities and relationships.

ENTITY TYPES: Person, Location, Organization, Concept, Theory

CRITICAL RULES:
1. Extract each location SEPARATELY - "Ulm, Germany" means Ulm AND Germany (NOT combined)
2. Extract CONCEPTS and THEORIES exactly as named - e.g., "Theory of Relativity" is a Theory, NOT "theoretical physicist"
3. Create ALL relationships between entities

EXAMPLES OF CORRECT EXTRACTION:
- "born in Ulm, Germany" → Person->Location (Ulm), Person->Location (Germany), Location->Location (Ulm->Germany)
- "developed Theory of Relativity" → Person->Theory (Theory of Relativity)"""

examples = [
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

print("Testing Einstein case - fixing Theory of Relativity extraction...")
start = time.time()
result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="qwen2.5-coder:3b",
    model_url="http://localhost:11434",
    fence_output=False,
    use_schema_constraints=False,
    max_char_buffer=500,
)
elapsed = time.time() - start

print(f"\nEntities found:")
for ext in result.extractions:
    if ext.extraction_class == "entity":
        print(f"  - {ext.extraction_text} ({ext.attributes.get('type')})")

print(f"\nRelations found:")
for ext in result.extractions:
    if ext.extraction_class == "relationship":
        print(
            f"  - {ext.attributes.get('source')} -> {ext.attributes.get('target')} ({ext.attributes.get('keywords')})"
        )

entities = [
    e.extraction_text for e in result.extractions if e.extraction_class == "entity"
]
print(f"\n--- Results ---")
print(f"✓ Separate Ulm and Germany: {'Ulm' in entities and 'Germany' in entities}")
print(f"✓ Has 'Theory of Relativity': {'Theory of Relativity' in entities}")
print(f"✓ Has 'Albert Einstein': {'Albert Einstein' in entities}")
print(f"Time: {elapsed:.1f}s")
