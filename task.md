# Task: lightrag-0o1 - Stabilize SMP baseline for fair comparison

## Objective

Establish a rock-solid, reproducible baseline for the existing Standard Mission Protocol (SMP) to enable fair A/B testing against the new OpenViking system. This involves fixing environmental inconsistencies, documenting current performance metrics, and ensuring the baseline code is immutable during the experiment.

## Success Criteria

- [x] Baseline repository hangs are resolved or bypassed for benchmarking.
- [x] Automated baseline benchmark script produces consistent results across 3 runs.
- [x] Metrics (latency, token efficiency, extraction quality) are recorded in `audit_results/smp_baseline_report.md`.
- [x] Environment variables for SMP are isolated from OpenViking.

## Proposed Strategy

1. **Environment Isolation**: Create a dedicated `.env.smp` for the baseline.
2. **Benchmark Execution**: Run the existing `compare_benchmarks.py` or similar to capture current state.
3. **Hang Mitigation**: If the original repo still hangs (as seen in `lightrag-o9j`), identify the minimum guardrails needed to complete the benchmark without data loss.
4. **Documentation**: formalize the "State of the SMP" report.

## Approval

Plan Approved: 2026-02-03 16:51
Approved to stabilize baseline.
