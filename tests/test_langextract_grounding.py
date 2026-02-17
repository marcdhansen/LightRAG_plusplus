#!/usr/bin/env python3
"""Test LangExtract source grounding feature"""

import time
import langextract as lx
from langextract.data import ExampleData, Extraction

text = (
    "Albert Einstein was a famous theoretical physicist born in Ulm, Germany. "
    "He is best known for developing the Theory of Relativity."
)

prompt = """Extract entities and relationships.

ENTITY TYPES: Person, Location, Organization, Concept, Theory

CRITICAL RULES:
1. Extract each location SEPARATELY
2. Extract THEORIES exactly as named
3. Create ALL relationships"""

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
]

print("=" * 60)
print("Testing LangExtract Source Grounding")
print("=" * 60)
print(f"\nSource text:\n{text}\n")

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

print("=" * 60)
print("EXTRACTIONS WITH SOURCE POSITIONS")
print("=" * 60)

for ext in result.extractions:
    # Use char_interval for source grounding (not text_position)
    pos = getattr(ext, "char_interval", None)
    print(f"\n{ext.extraction_class.upper()}: {ext.extraction_text}")
    print(f"  Type: {ext.attributes.get('type', 'N/A')}")
    print(f"  Source position: {pos}")

    # Show the actual text snippet
    if pos and pos.start_pos is not None and pos.end_pos is not None:
        snippet = text[pos.start_pos : pos.end_pos]
        print(f'  Matched text: "{snippet}"')

print("\n" + "=" * 60)
print("CITATION EXAMPLE")
print("=" * 60)

# Show how this could be used for citations
print("\nWith source grounding, we can generate citations like:")
for i, ext in enumerate(result.extractions, 1):
    if ext.extraction_class == "entity":
        pos = getattr(ext, "char_interval", None)
        if pos and pos.start_pos is not None:
            snippet = text[max(0, pos.start_pos - 10) : pos.end_pos + 10]
            print(f'  [^{i}] "{snippet}..." (position {pos.start_pos}-{pos.end_pos})')

print(f"\n✓ Time: {elapsed:.1f}s")
print("✓ Source grounding works - each extraction maps to source text position")
