---
phase: 05-reconcile-execution-operator-visibility
plan: 01
subsystem: reconcile
tags: [git, candidate-checkout, removal-planning]
requires:
  - phase: 04-safe-deploy-teardown
    provides: runtime target DTOs, trusted runtime-tree helpers
provides:
  - Reconcile DTOs
  - Managed checkout safety checks
  - Isolated candidate checkout helpers
  - Declaration-driven removal planning
affects: [reconcile service]
tech-stack:
  added: []
  patterns: [candidate isolation, exact-SHA reconcile inputs, rebuild-required removal planning]
key-files:
  created: [src/unraid_actuator/reconcile_models.py, src/unraid_actuator/reconcile_git.py, src/unraid_actuator/reconcile_plan.py, tests/unit/test_reconcile_git.py, tests/unit/test_reconcile_plan.py]
  modified: []
key-decisions:
  - "Dirty or locally diverged managed checkouts fail before any reconcile mutation."
  - "Removal planning is declaration-driven and can signal a required current-runtime rebuild instead of guessing teardown inputs."
patterns-established:
  - "Reconcile orchestration consumes typed Git/workspace/removal DTOs instead of ad hoc tuples and dicts."
requirements-completed: [REC-01, REC-02, REC-04, REC-06]
duration: unknown
completed: 2026-04-22
---

# Phase 5: Plan 01 Summary

**Phase 5 now has explicit Git-safety and removal-planning contracts, so reconcile can reason about candidate state and removals without mutating or guessing.**

## Accomplishments

- Added typed reconcile DTOs for managed checkout state, candidate workspaces, removal plans, and reconcile results.
- Implemented managed-checkout inspection with dirty/diverged failure rules and exact candidate SHA capture.
- Added isolated candidate checkout preparation and exact-SHA fast-forward helpers.
- Implemented declaration-driven removed-target planning with explicit rebuild-required signaling for malformed or missing current runtime trees.

## Files Created/Modified

- `src/unraid_actuator/reconcile_models.py` - Shared reconcile DTOs and status enum.
- `src/unraid_actuator/reconcile_git.py` - Managed checkout inspection, isolated candidate checkout setup, and fast-forward helper.
- `src/unraid_actuator/reconcile_plan.py` - Current-vs-incoming removal planning and runtime target resolution.
- `tests/unit/test_reconcile_git.py` - Coverage for dirty/diverged rejection, SHA capture, candidate checkout, and fast-forward.
- `tests/unit/test_reconcile_plan.py` - Coverage for declaration-order removals, rebuild-required signaling, and invalid incoming state propagation.

## Verification

- `uv run pytest tests/unit/test_reconcile_git.py tests/unit/test_reconcile_plan.py -q`

## Deviations from Plan

None.

---
*Phase: 05-reconcile-execution-operator-visibility*
*Completed: 2026-04-22*
