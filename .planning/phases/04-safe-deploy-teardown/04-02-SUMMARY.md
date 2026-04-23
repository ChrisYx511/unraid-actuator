---
phase: 04-safe-deploy-teardown
plan: 02
subsystem: runtime
tags: [deploy, teardown, services]
requires:
  - phase: 04-safe-deploy-teardown
    provides: runtime target contracts, marked-tree selection, and compose command specs
provides:
  - Deploy orchestration service
  - Teardown orchestration service
  - Fail-fast ordered batch behavior
affects: [phase-4 CLI surface, phase-5 reconcile apply/down flow]
tech-stack:
  added: []
  patterns: [runner-based orchestration, target-specific failure reporting]
key-files:
  created: [src/unraid_actuator/deploy.py, tests/unit/test_deploy_service.py, tests/unit/test_teardown_service.py]
  modified: []
key-decisions:
  - "Full-tree deploy and teardown stop immediately on the first failed target."
  - "Service-level selector guards mirror the CLI so scope safety holds even outside argparse."
patterns-established:
  - "Runtime actions resolve targets first, then loop over explicit Compose specs through the runner abstraction."
requirements-completed: [DEP-01, DEP-02, DEP-03, DEP-04]
duration: unknown
completed: 2026-04-22
---

# Phase 4: Plan 02 Summary

**Deploy and teardown now run as fail-fast services over the marked runtime tree, with scoped requests limited to one still-declared target and no hidden widening of scope.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22T19:25:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `run_deploy(...)` for full-tree and scoped `up -d` execution.
- Added `run_teardown(...)` for full-tree and scoped `down` execution.
- Preserved dry-run and recording-runner testability while surfacing target-specific failure messages.

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/deploy.py` - Shared deploy/teardown orchestration with fail-fast behavior.
- `tests/unit/test_deploy_service.py` - Coverage for ordered deploy execution, scoped dispatch, and selector guards.
- `tests/unit/test_teardown_service.py` - Coverage for ordered teardown execution, scoped dispatch, and selector guards.

## Decisions Made

- Kept the service layer thin by delegating all tree trust and command construction to Wave 1 helpers.
- Used explicit target names in failure messages so operators can see which app/environment stopped the batch.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Wave 3 can now expose deploy and teardown publicly without embedding runtime-tree discovery or Compose logic in the CLI.

---
*Phase: 04-safe-deploy-teardown*
*Completed: 2026-04-22*
