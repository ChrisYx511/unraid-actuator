---
phase: 04-safe-deploy-teardown
plan: 01
subsystem: runtime
tags: [deploy, compose, runtime-tree]
requires:
  - phase: 03-runtime-build-secret-materialization
    provides: marked runtime tree, normalized compose output, shared host declaration loaders
provides:
  - Runtime target DTOs
  - Marked-tree resolution helpers
  - Explicit compose up/down command factories
affects: [deploy service, teardown service, deploy CLI]
tech-stack:
  added: []
  patterns: [full-tree trust vs scoped revalidation, explicit compose identity]
key-files:
  created: [src/unraid_actuator/deploy_models.py, src/unraid_actuator/deploy_tree.py, src/unraid_actuator/compose_runtime.py, tests/unit/test_deploy_tree.py, tests/unit/test_compose_runtime.py]
  modified: []
key-decisions:
  - "Full-tree actions trust a marked runtime tree, while scoped actions still require current host declaration membership."
  - "Compose commands always pass explicit project identity and pin COMPOSE_REMOVE_ORPHANS=0 without using --remove-orphans."
patterns-established:
  - "Runtime-target resolution lives in one helper module instead of being reimplemented by services or CLI code."
requirements-completed: [DEP-01, DEP-02, DEP-03]
duration: unknown
completed: 2026-04-22
---

# Phase 4: Plan 01 Summary

**Phase 4 now has a typed runtime-tree contract and deterministic Compose command builders, so deploy/teardown orchestration can stay thin and safety-focused.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22T19:20:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added runtime-target dataclasses for deploy/teardown execution results.
- Implemented marked-tree validation plus full-tree and scoped target resolution helpers.
- Added exact `docker compose up -d` and `docker compose down` command-spec factories with explicit project identity.

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/deploy_models.py` - Runtime target and action result DTOs.
- `src/unraid_actuator/deploy_tree.py` - Marked-tree trust, declaration-order full-tree selection, and scoped revalidation helpers.
- `src/unraid_actuator/compose_runtime.py` - Explicit Compose command builders for `up -d` and `down`.
- `tests/unit/test_deploy_tree.py` - Coverage for marker trust, stale full-tree tolerance, and scoped declaration checks.
- `tests/unit/test_compose_runtime.py` - Coverage for exact Compose argv/env construction.

## Decisions Made

- Allowed stale build-only targets during full-tree resolution, but appended them only after current declared targets in deterministic order.
- Reused the existing marker and project-name helpers instead of introducing parallel contracts.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Wave 2 can now implement ordered deploy/teardown orchestration entirely in terms of shared runtime-target selection and fixed Compose command specs.

---
*Phase: 04-safe-deploy-teardown*
*Completed: 2026-04-22*
