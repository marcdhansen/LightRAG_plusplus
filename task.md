# Task: Standardize Injection-Reflection-Repair Unit Test Pattern (lightrag-dog)

## Status: IN_PROGRESS

### Objective

Establish a standardized, reusable testing pattern for the ACE (Agentic Context Evolution) framework to verify the full Injection-Reflection-Repair cycle. This will replace ad-hoc testing scripts with a robust Pytest fixture or class-based approach, ensuring consistent validation of graph evolution.

### Tasks

- [ ] **Analysis**: Review existing ACE tests (e.g., `tests/test_ace_process.py`) to identify common patterns and pain points.
- [ ] **Design**: Define a standard `AceIntegrationTest` class or `ace_lifecycle` fixture in `tests/conftest.py` or a shared utility.
  - [ ] Support for clean injection of entities/relations.
  - [ ] Triggering of specific Reflection/Curator logic.
  - [ ] Assertions for "Before" and "After" graph states.
- [ ] **Implementation**: Create the standardized test harness.
- [ ] **Migration**: Refactor at least one major ACE test to use the new pattern.
- [ ] **Verification**: Ensure tests pass reliably and produce clear failure messages.

### Steps

1. [ ] Analyze `tests/test_ace_process.py` and `tests/test_gold_standard_extraction.py`.
2. [ ] Prototype the `AceTestHarness` class/fixture.
3. [ ] Implement a test case using the harness:
   - Inject a contradiction (e.g., "Apple is a fruit" vs "Apple is a car").
   - Trigger Reflection.
   - Verify Curator successfully resolves it or flags it.
4. [ ] Run tests and verify output.
