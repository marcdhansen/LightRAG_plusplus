# Task: Reasoning Threshold Policy (lightrag-oi6)

## Status: COMPLETED

### Objective

Formalize the requirement that ACE "Reflector" models (used for graph repair) should be 7B+ parameters to ensure high-quality reasoning, preventing small models from damaging the graph with poor edits.

### Tasks

- [x] Verify `parse_model_size` utility in `lightrag/utils.py`.
- [x] Determine if the current warning in `lightrag/core.py` is sufficient or if it should be an exception/strict check.
- [x] Implement an override mechanism (e.g., `allow_small_reflector` config).
- [x] Document the policy in `docs/ACE_FRAMEWORK.md` or similar.
- [x] Verify via test (mocking a small model name).

### Steps

1. [x] Check `lightrag/utils.py`.
2. [x] Update `lightrag/core.py` and `lightrag/ace/config.py` (if needed) to support the policy and override.
3. [x] Create/Update documentation.
4. [x] Create a test case.
