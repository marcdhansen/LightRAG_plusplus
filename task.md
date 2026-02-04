# Task: lightrag-uc1 - Implement comprehensive A/B testing framework

## Objective

Build a production-grade A/B testing system to compare the legacy Standard Mission Protocol (SMP) against the new OpenViking production environment. The framework must provide statistically significant insights into latency, cost, and extraction quality.

## Success Criteria

- [ ] Automated A/B test harness that can run parallel queries across SMP and OpenViking endpoints.
- [ ] Metric collection for:
  - Mean/P95 Latency.
  - Token Usage (Input/Output).
  - Extraction Quality (Entity/Relation F1 via `eval_metrics.py`).
- [ ] Statistical analysis module (calculating Lift, Confidence Intervals).
- [ ] Automated markdown report generator for experiment results.
- [ ] Integration with existing monitoring (Langfuse/Prometheus if available).

## Proposed Strategy

1. **Runner Design**: Create a unified runner script `scripts/ab_test_runner.py` that takes a set of test documents/queries and dispatches them to both "Baseline" (SMP) and "Candidate" (OpenViking).
2. **Telemetry Management**: Reuse `eval_metrics.py` for quality and add a context manager for timing and token counting.
3. **Analysis Library**: Use `scipy` or basic math to implement t-tests for latency and recall improvements.
4. **Reporting**: Generate a dashboard-like markdown file in `audit_results/ab_reports/`.

## Approval

Plan Completed: 2026-02-03 18:29
A/B testing framework integration and OpenViking slash commands fixed.
