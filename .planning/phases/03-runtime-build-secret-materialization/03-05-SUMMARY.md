---
phase: 03-runtime-build-secret-materialization
plan: 05
subsystem: build-validation-cli
tags: [build, validate, cli]
requires:
  - plan: 03-02
  - plan: 03-04
provides:
  - Template-aware validation preflight
  - Public `build` CLI command
  - Shared template/value contract across discovery, validation, and build
affects: [validation service, build CLI]
tech-stack:
  added: []
  patterns: [shared source contract, thin cli, safe stderr failures]
key-files:
  created: [tests/unit/test_build_cli.py]
  modified: [src/unraid_actuator/compose_validation.py, src/unraid_actuator/validate.py, src/unraid_actuator/cli.py, tests/unit/test_compose_validation.py, tests/unit/test_validate_service.py]
key-decisions:
  - "Validation preflight remains secret-free and template-aware."
  - "The public CLI stays thin and surfaces build failures as readable exit-code-1 errors."
patterns-established:
  - "Public commands dispatch into service helpers instead of carrying feature logic in argparse handlers."
requirements-completed: [BLD-01, BLD-04, BLD-05, BLD-07]
duration: unknown
completed: 2026-04-22
---

# Phase 3: Plan 05 Summary

**Phase 3 finished as an operator-facing feature: validation and build now share the same template/value source contract, and the CLI exposes `unraid-actuator build` cleanly.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Replaced stale repo-`build.py` validation assumptions with template/value preflight behavior.
- Kept validation secret-free while rendering templates through the same shared helper used by build.
- Added the thin `build` CLI command with default/custom output-root dispatch and readable failure handling.

## Verification

- `uv run pytest tests/unit/test_compose_validation.py tests/unit/test_validate_service.py tests/unit/test_build_cli.py -q`

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/compose_validation.py` - Added template-aware validation preflight helpers.
- `src/unraid_actuator/validate.py` - Reused the shared source contract and `apps.y[a]ml` resolution in validation.
- `src/unraid_actuator/cli.py` - Added the public `build` subcommand.
- `tests/unit/test_compose_validation.py` - Covered template-source preflight behavior.
- `tests/unit/test_validate_service.py` - Covered shared declaration/source handling in grouped validation.
- `tests/unit/test_build_cli.py` - Covered CLI output-root dispatch and readable failures.

## Decisions Made

- Preserved the thin-CLI architecture instead of adding build logic at the command-line boundary.
- Kept validation free of `.env` and decrypted secrets so build remained the only secret-materialization phase.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Phase 4 can now trust one marked runtime-tree shape and one public build entrypoint regardless of whether the source started as static Compose or template/value input.

---
*Phase: 03-runtime-build-secret-materialization*
*Completed: 2026-04-22*
