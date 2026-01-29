# Task: Implement automated cross-reference check for new benchmark/feature documentation (lightrag-6l3)

## Status: COMPLETE

### Objective

Implement a robust, automated validation script to ensure that all documentation files within the project are correctly cross-referenced, that no "orphaned" documentation exists, and that all internal links are portable relative paths (no absolute paths). This is part of the Librarian skill's responsibility to maintain a high-quality, navigable documentation set.

### Tasks

- [x] **Design**: Define the scope of the cross-reference check.
- [x] **Implementation**: Develop `scripts/check_docs_coverage.py`.
  - [x] Implement link extraction from markdown files.
  - [x] Implement detection of orphaned files in `docs/`.
  - [x] Implement broken link detection.
  - [x] Implement absolute/non-portable link detection.
  - [x] Support for excluding specific files (e.g., templates, example inputs).
- [x] **Integration**: standalone command `scripts/check_docs_coverage.py` provided.
- [x] **Remediation**: Fixed all orphaned files:
  - Linked `ACADEMIC_BENCHMARKING.md` in `EVALUATION.md`.
  - Linked `Algorithm.md` in `ARCHITECTURE.md`.
  - Linked `LightRAG_concurrent_explain.md`, `TESTING_SUMMARY.md` in `ARCHITECTURE.md`.
  - Linked `UV_LOCK_GUIDE.md` in `README.md` and `ARCHITECTURE.md`.
- [x] **Verification**: Script passes with zero orphans and zero broken links (excluding restricted `global_docs`).

### Steps

1. [x] Analyze current `docs/` structure and existing validation script (`scripts/validate_docs.py`).
2. [x] Create `scripts/check_docs_coverage.py`.
3. [x] Run the script and identify orphaned files.
4. [x] Implement fixes for orphaned documentation.
5. [x] Verified script passes.
