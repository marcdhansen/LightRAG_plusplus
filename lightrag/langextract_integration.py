"""LangExtract integration for entity extraction with character-level source spans."""

import json
import os
from typing import Any

import langextract as lx
from langextract.data import ExampleData, Extraction

from lightrag.utils import logger

DEFAULT_EXAMPLES = [
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
            Extraction(
                extraction_class="relationship",
                extraction_text="Steve Jobs founded Apple",
                attributes={
                    "source": "Steve Jobs",
                    "target": "Apple",
                    "keywords": "founded",
                },
            ),
        ],
    ),
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

PROMPT_DESCRIPTION = """Extract entities and relationships.

ENTITY TYPES: Person, Location, Organization, Concept, Theory

CRITICAL RULES:
1. Extract each location SEPARATELY - "Ulm, Germany" means Ulm AND Germany (NOT combined)
2. Extract CONCEPTS and THEORIES exactly as named - e.g., "Theory of Relativity" is a Theory
3. Create ALL relationships between entities"""


def load_examples(examples_path: str) -> list[ExampleData]:
    """Load examples from a JSON file."""
    if not examples_path or not os.path.exists(examples_path):
        logger.warning(
            f"LangExtract examples file not found: {examples_path}, using defaults"
        )
        return DEFAULT_EXAMPLES

    with open(examples_path) as f:
        examples_data = json.load(f)

    examples = []
    for example_data in examples_data:
        extractions = []
        for ext in example_data.get("extractions", []):
            extractions.append(
                Extraction(
                    extraction_class=ext.get("extraction_class", "entity"),
                    extraction_text=ext.get("extraction_text", ""),
                    attributes=ext.get("attributes", {}),
                )
            )
        examples.append(
            ExampleData(
                text=example_data.get("text", ""),
                extractions=extractions,
            )
        )

    return examples


def extract_with_langextract(
    text: str,
    model_id: str = "qwen2.5-coder:3b",
    model_url: str = "http://localhost:11434",
    examples_path: str = "",
) -> dict[str, Any]:
    """Extract entities and relationships using LangExtract.

    Returns:
        Dictionary with 'entities' and 'relationships' keys, compatible with LightRAG's
        internal format, plus 'sources' for character-level spans.
    """
    examples = load_examples(examples_path)

    result = lx.extract(
        text_or_documents=text,
        prompt_description=PROMPT_DESCRIPTION,
        examples=examples,
        model_id=model_id,
        model_url=model_url,
        fence_output=False,
        use_schema_constraints=False,
        max_char_buffer=500,
    )

    entities = {}
    relationships = {}
    sources = {}

    for ext in result.extractions:
        if ext.extraction_class == "entity":
            entity_name = ext.extraction_text.strip()
            entity_type = ext.attributes.get("type", "Concept")

            entities[entity_name] = [
                {
                    "entity_name": entity_name,
                    "entity_type": entity_type.lower(),
                    "description": f"{entity_name} is a {entity_type}.",
                    "source_id": "",
                    "file_path": "",
                }
            ]

            if hasattr(ext, "span") and ext.span:
                sources[entity_name] = {
                    "start": ext.span.start,
                    "end": ext.span.end,
                    "text": ext.span.text,
                }

        elif ext.extraction_class == "relationship":
            if not ext.attributes:
                continue
            source = ext.attributes.get("source", "") or ""
            target = ext.attributes.get("target", "") or ""
            keywords = ext.attributes.get("keywords", "") or ""

            if not source or not target:
                continue

            edge_key = (source.strip(), target.strip())
            relationships[edge_key] = [
                {
                    "source": source.strip(),
                    "target": target.strip(),
                    "keywords": keywords
                    if isinstance(keywords, str)
                    else ", ".join(keywords),
                    "description": ext.extraction_text
                    or f"{source} {keywords} {target}",
                }
            ]

            if hasattr(ext, "span") and ext.span:
                sources[f"{source}->{target}"] = {
                    "start": ext.span.start,
                    "end": ext.span.end,
                    "text": ext.span.text,
                }

    return {
        "entities": entities,
        "relationships": relationships,
        "sources": sources,
    }


async def async_extract_with_langextract(
    text: str,
    model_id: str = "qwen2.5-coder:3b",
    model_url: str = "http://localhost:11434",
    examples_path: str = "",
) -> dict[str, Any]:
    """Async wrapper for LangExtract extraction."""
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, extract_with_langextract, text, model_id, model_url, examples_path
    )
