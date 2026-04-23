---
phase: 03-runtime-build-secret-materialization
plan: 04
subsystem: build-service
tags: [build, runtime-tree, staging]
requires:
  - plan: 03-01
  - plan: 03-02
  - plan: 03-03
provides:
  - Build DTOs
  - Staged runtime-tree generation
  - Marker-based successful build contract
affects: [build service, downstream deploy/reconcile runtime-tree trust]
tech-stack:
  added: []
  patterns: [declared-only builds, stage-then-promote, marker-on-success]
key-files:
  created: [src/unraid_actuator/build_models.py]
  modified: [src/unraid_actuator/build.py, tests/unit/test_build_service.py]
key-decisions:
  - "Build materializes only declared app/environment pairs for the active host."
  - "Successful trees are marked and promoted only after all declared environments succeed."
patterns-established:
  - "Build orchestration stays thin by delegating normalization, secrets, and env serialization to dedicated helpers."
requirements-completed: [BLD-01, BLD-02, BLD-03, BLD-05, BLD-06, BLD-07]
duration: unknown
completed: 2026-04-22
---

# Phase 3: Plan 04 Summary

**The build command now produces one staged, actuator-managed runtime tree that downstream deploy and reconcile flows can trust.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments

- Added `BuildTarget` and `BuildResult` contracts for the service and CLI.
- Implemented full-host build orchestration over declared targets only.
- Staged the runtime tree under a sibling temp directory and promoted it only after every environment succeeded.
- Wrote the `.UNRAID_RUNNING_CONFIGURATION` marker only for successful staged trees.

## Verification

- `uv run pytest tests/unit/test_build_service.py tests/unit/test_build_paths.py -q`

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/build_models.py` - Typed build target/result DTOs.
- `src/unraid_actuator/build.py` - End-to-end build orchestration from active config to staged runtime tree.
- `tests/unit/test_build_service.py` - Covered declared-only selection, safe failure, marker writes, and stage promotion.

## Decisions Made

- Failed missing or ambiguous declared environments before decrypting secrets or creating the stage root.
- Preserved the default `/tmp/unraid-actuator/build` path while keeping custom-root emptiness checks centralized in shared helpers.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Wave 4 can align validation with the shipped template/value source model and expose the build service through the public CLI.

---
*Phase: 03-runtime-build-secret-materialization*
*Completed: 2026-04-22*
