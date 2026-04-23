---
phase: 03-runtime-build-secret-materialization
plan: 03
subsystem: secret-materialization
tags: [build, secrets, env]
requires:
  - plan: 03-01
    provides: strict secret-env validation and shared runtime dependencies
provides:
  - EJSON decrypt adapter
  - Per-environment secret extraction
  - Deterministic merged `.env` output
affects: [build service, runtime tree contents]
tech-stack:
  added: []
  patterns: [decrypt-once-per-host, missing-secret-blocks-are-empty, secret-overrides-env]
key-files:
  created: [src/unraid_actuator/secrets.py, src/unraid_actuator/env_materialize.py, tests/unit/test_secrets.py, tests/unit/test_env_materialize.py]
  modified: []
key-decisions:
  - "Missing app/environment secret blocks are treated as empty input, not build failures."
  - "Decrypted secret values override repo `.env` keys in the generated runtime tree."
patterns-established:
  - "Secrets are decrypted once and then scoped down per app/environment before `.env` serialization."
requirements-completed: [BLD-05, BLD-06]
duration: unknown
completed: 2026-04-22
---

# Phase 3: Plan 03 Summary

**Phase 3 now has a clear secret boundary: decrypt once through EJSON, keep secrets out of templates, and materialize one deterministic merged `.env` file per built environment.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added the EJSON decrypt adapter behind the shared runner abstraction.
- Added per-environment secret extraction that ignores metadata keys and tolerates missing environment blocks.
- Added deterministic `.env` parsing, merge precedence, validation of bare keys, and stable serialization.

## Verification

- `uv run pytest tests/unit/test_secrets.py tests/unit/test_env_materialize.py -q`

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/secrets.py` - EJSON decrypt command construction, JSON validation, and environment-scoped secret extraction.
- `src/unraid_actuator/env_materialize.py` - `.env` parsing, secret precedence, and deterministic serialization.
- `tests/unit/test_secrets.py` - Covered decrypt failure, malformed decrypted JSON, and empty secret-block behavior.
- `tests/unit/test_env_materialize.py` - Covered missing `.env`, explicit-value enforcement, secret overrides, and sorted output.

## Decisions Made

- Preserved secret-free template rendering by keeping decrypted values out of Jinja inputs entirely.
- Standardized serialized `.env` output so later deploy/reconcile phases can trust the generated runtime tree.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Wave 3 can now orchestrate the full staged runtime-tree build using validated source classification, normalization helpers, and deterministic secret materialization.

---
*Phase: 03-runtime-build-secret-materialization*
*Completed: 2026-04-22*
