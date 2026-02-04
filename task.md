# Task: lightrag-fv9 - Extraction Prompt Enhancement (Relationship Schema Refinement)

## Objective

Enhance the relationship extraction prompts to improve accuracy on small models (1.5B/7B), specifically addressing the 0% accuracy observed in the "Einstein" case for smaller models during the baseline audit.

## Success Criteria

- [ ] Relationship accuracy for `qwen2.5-coder:3b` on the "Einstein" case improves from 0% to >50%.
- [ ] Maintain 100% YAML compliance across all tested models.
- [ ] No regression in entity recall (>90% on 3B/7B).

## Proposed Strategy

1. **Analyze Failure Patterns**: Review the `baseline_audit_report.md` and the actual outputs of the Einstein test case to understand why relationships are being missed or malformed.
2. **Enhance Prompt Instructions**:
    - Update `entity_extraction_key_value_system_prompt` in `lightrag/prompt.py`.
    - Add explicit instructions for identifying binary relationships between *all* extracted entities.
    - Clarify the "source", "target", "keywords", "description" schema.
3. **Diversify Examples**: Add one or two more complex relationship examples to the `{examples}` placeholder or directly in the prompt if appropriate.
4. **Verification**:
    - Run `tests/test_gold_standard_extraction.py` using `qwen2.5-coder:3b` and `qwen2.5-coder:7b`.
    - Compare results with the baseline audit.

## Approval

## Status: IN_PROGRESS

Approved: [User Sign-off at 2026-02-04 15:30]
