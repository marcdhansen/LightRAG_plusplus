# Task: Extraction Standardization (lightrag-6h1)

## Status: COMPLETED

### Objective

Standardize the entity extraction format to YAML for local/offline LLMs (e.g., Ollama). This improves reliability and parsing success rates compared to JSON for smaller models (7B and below).

### Tasks

- [x] Identify location of extraction prompts in `lightrag`.
- [x] Modify `lightrag/llm/ollama.py` or `lightrag/prompt.py` to use YAML format by default or when configured.
- [x] Update `lightrag/utils.py` to support robust YAML parsing for extraction.
- [x] Verify extraction with a local model (e.g., `qwen2.5-coder:7b` or `1.5b`).
- [x] Ensure existing JSON extraction still works for other models/modes if needed.

### Steps

1. [x] Locate usage of extraction prompts.
2. [x] Implement YAML extraction prompt template.
3. [x] Implement `parse_yaml` or equivalent helper if missing.
4. [x] Create a test script `tests/test_extraction_yaml.py`.
5. [x] Verify and Commit.
