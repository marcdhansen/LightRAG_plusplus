# Task: Fix CI/CD Pipeline Cache Key Issue

## Objective

Fix the `Milestone Validation Pipeline` in
`.github/workflows/milestone_validation.yml` which is failing because the
`setup-environment` job does not correctly export the `cache-key` output.

## Problem Analysis

- The `setup-environment` job defines an output `cache-key` as
  `${{ steps.cache.outputs.cache-key }}`.
- However, the `steps.cache` (actions/cache@v5) does not provide an output
  named `cache-key`.
- There is a step "Cache validation environment" that sets `cache-key` in
  `$GITHUB_OUTPUT`, but it lacks an `id` and is not referenced by the job
  output.

## Proposed Fix

1. Add an `id: set-cache-key` to the "Cache validation environment" step in
   the `setup-environment` job.
2. Update the `setup-environment` job's `cache-key` output to reference
   `${{ steps.set-cache-key.outputs.cache-key }}`.
3. Verify that other jobs (`unit-tests`, `tdd-gate-validation`, etc.) correctly
   use this `cache-key`.

## Plan

- [x] Update `.github/workflows/milestone_validation.yml` with the fix.
- [x] Create PR and verify fix in CI.
  - [x] Fix secondary issue: Ghost worktree causing submodule errors in CI.
- [ ] Merge PR and verify on `main`.
- [ ] Cleanup (revert `agent/**` trigger if necessary, or keep it).

## Approval

## Approval: [User Sign-off at 2026-02-04 14:15...]
