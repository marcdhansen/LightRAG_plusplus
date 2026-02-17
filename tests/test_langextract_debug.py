#!/usr/bin/env python3
"""Debug: Check what attributes LangExtract returns"""

import time
import langextract as lx
from langextract.data import ExampleData, Extraction

text = "Albert Einstein was born in Ulm, Germany."

prompt = """Extract entities and relationships."""
examples = [
    ExampleData(
        text="Steve Jobs founded Apple.",
        extractions=[
            Extraction(
                extraction_class="entity",
                extraction_text="Steve Jobs",
                attributes={"type": "Person"},
            ),
            Extraction(
                extraction_class="entity",
                extraction_text="Apple",
                attributes={"type": "Organization"},
            ),
        ],
    ),
]

result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="qwen2.5-coder:3b",
    model_url="http://localhost:11434",
    fence_output=False,
    use_schema_constraints=False,
)

print("Extraction object attributes:")
for ext in result.extractions:
    print(f"\n--- {ext.extraction_class}: {ext.extraction_text} ---")
    print(f"  All attributes: {vars(ext)}")
