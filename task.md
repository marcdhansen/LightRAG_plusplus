# Task: Run Benchmark Comparison with Ollama Models (lightrag-1sk)

## Status: IN_PROGRESS

### Objective

Verify that optimizations and changes in the current repository do not degrade extraction quality compared to the original LightRAG implementation.

### Tasks

- [x] **PFC**: Run Pre-Flight Check and verify current objective.
- [x] **Environment Check**: Verify access to original repo and Ollama models.
- [x] **Commit Pending Optimizations**: Stabilize and commit current extraction prompt enhancements.
- [x] **Fix Benchmark Script**: Implement isolated subprocesses for extraction to ensure fair repository comparison.
- [x] **Execute Verification**: Run isolated extraction to verify baseline functionality.
- [ ] **Run Full Comparison**: Execute full benchmark run when resources permit.
- [ ] **Analyze Results**: Review `benchmark_comparison_report.md` for regressions.
- [ ] **Document Findings**: Update `lightrag-1sk` status with results.

### Steps

1. [x] Run PFC and identify current objective (`lightrag-1sk`).
2. [x] Review uncommitted changes and stabilize them.
3. [x] Commit current optimizations to ensure a consistent benchmark base.
4. [x] Fix `compare_benchmarks.py` isolation bug by creating `isolated_extract.py`.
5. [x] Verify extraction prompts for small models (1.5b) via baseline audit.
6. [ ] Execute full comparison across multiple cases.
7. [ ] Perform RTB and final debrief.
