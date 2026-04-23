---
phase: 05-reconcile-execution-operator-visibility
plan: 03
subsystem: reconcile-service
tags: [build, validate, reconcile]
requires:
  - phase: 05-reconcile-execution-operator-visibility
    provides: reconcile DTOs, git helpers, visibility adapters, locking
provides:
  - Host-root-aware validate/build reuse
  - Shared runtime-root promotion
  - Core reconcile coordinator
affects: [build command, validate command, reconcile CLI]
tech-stack:
  added: []
  patterns: [orchestrator-over-services, dry-run non-mutation, teardown-before-apply]
key-files:
  created: [src/unraid_actuator/reconcile.py, tests/unit/test_reconcile_service.py]
  modified: [src/unraid_actuator/build_paths.py, src/unraid_actuator/build.py, src/unraid_actuator/validate.py, tests/unit/test_build_service.py, tests/unit/test_validate_service.py]
key-decisions:
  - "Reconcile reuses the real validate/build/deploy/teardown services instead of forking a second execution stack."
  - "Dry-run candidate evaluation is explicit and non-mutating for the managed source and current runtime tree."
patterns-established:
  - "Promotion of a candidate runtime root into the live default runtime root uses the same shared helper as direct build."
requirements-completed: [REC-01, REC-02, REC-03, REC-04, REC-05, REC-06, OPS-01, OPS-02, OPS-03]
duration: unknown
completed: 2026-04-22
---

# Phase 5: Plan 03 Summary

**Phase 5 now has the actual reconcile coordinator, wired as an orchestrator over existing build/validate/deploy services with explicit dry-run semantics.**

## Accomplishments

- Lowered build and validate into reusable host-root helpers while preserving the original config-backed wrappers.
- Extracted shared runtime-root promotion into `build_paths.py`.
- Implemented `run_reconcile(...)` with lock acquisition, per-run visibility, candidate validation/build, declaration-driven removal planning, D-06 current-runtime rebuild handling, teardown-before-apply ordering, runtime-root promotion, and exact-SHA source fast-forward.
- Added focused unit tests for no-op, invalid candidate, removal failure, applied success, dry-run behavior, and runtime command logging.

## Files Created/Modified

- `src/unraid_actuator/build_paths.py` - Added `promote_runtime_root(...)`.
- `src/unraid_actuator/build.py` - Added `run_build_for_host(...)`; wrapper now delegates.
- `src/unraid_actuator/validate.py` - Added `run_validate_for_host(...)`; wrapper now delegates.
- `src/unraid_actuator/reconcile.py` - Core reconcile coordinator.
- `tests/unit/test_build_service.py` - Added wrapper/helper parity and promotion coverage.
- `tests/unit/test_validate_service.py` - Added wrapper/helper parity coverage.
- `tests/unit/test_reconcile_service.py` - Added reconcile flow coverage.

## Verification

- `uv run pytest tests/unit/test_build_service.py tests/unit/test_validate_service.py tests/unit/test_reconcile_service.py -q`

## Deviations from Plan

None.

---
*Phase: 05-reconcile-execution-operator-visibility*
*Completed: 2026-04-22*
