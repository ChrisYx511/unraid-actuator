---
phase: 01-runtime-foundations-initialization
plan: 02
subsystem: infra
tags: [python, strictyaml, git, init, config]
requires:
  - phase: 01-runtime-foundations-initialization
    provides: package scaffold, CLI shell, and command runner abstraction
provides:
  - Single active config contract persisted at /tmp/actuator-cfg.yml
  - Clone-or-reuse init workflow
  - CLI-wired init command with dry-run-safe behavior
affects: [desired-state discovery, reconcile]
tech-stack:
  added: []
  patterns: [schema-backed config persistence, injected CLI runners for tests]
key-files:
  created: [src/unraid_actuator/config.py, src/unraid_actuator/init.py, tests/unit/test_config_store.py, tests/unit/test_init_command.py]
  modified: [src/unraid_actuator/cli.py]
key-decisions:
  - "Persisted exactly one active config with no profile/history expansion."
  - "Injected runners and config paths through CLI main() so init remains unit-testable without live git."
patterns-established:
  - "Operator workflows return structured service results and format user output at the CLI boundary."
  - "strictyaml schemas define persisted contract boundaries explicitly."
requirements-completed: [INIT-01, INIT-02, INIT-03, INIT-04]
duration: unknown
completed: 2026-04-22
---

# Phase 1: Plan 02 Summary

**`unraid-actuator init` now persists the active host checkout contract and safely clones or reuses the managed source tree.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22T05:05:59Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added a strict `ActiveConfig` schema and UTF-8 load/save helpers for `/tmp/actuator-cfg.yml`.
- Implemented `init` orchestration that creates missing directories, clones into missing/empty targets, and skips recloning for non-empty trees.
- Wired `init` through the packaged CLI with dry-run-safe behavior and unit coverage for clone, reuse, and config persistence.

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `src/unraid_actuator/config.py` - Typed single-config contract with strict YAML schema enforcement.
- `src/unraid_actuator/init.py` - Clone-or-reuse initialization workflow using the shared runner abstraction.
- `src/unraid_actuator/cli.py` - `init` command routing, runner selection, and user-facing result formatting.
- `tests/unit/test_config_store.py` - Round-trip and schema-drift rejection tests for config persistence.
- `tests/unit/test_init_command.py` - CLI-level tests for clone, reuse, and dry-run behavior.

## Decisions Made

- Rejected extra or missing config keys instead of allowing the persisted contract to drift.
- Treated a non-directory source path as an explicit error because the managed checkout path must be a directory.

## Deviations from Plan

### Auto-fixed Issues

**1. Parsing edge in shared `--dry-run` flag handling**
- **Found during:** Task 2 (`init` CLI wiring)
- **Issue:** Declaring `--dry-run` on both the root parser and the init subparser caused the subparser default to overwrite the root value.
- **Fix:** Kept `--dry-run` as the root-level public flag and removed the duplicate subparser declaration.
- **Files modified:** `src/unraid_actuator/cli.py`
- **Verification:** Dry-run init test passes without directory or config mutation.
- **Committed in:** none

---

**Total deviations:** 1 auto-fixed
**Impact on plan:** No scope creep; the fix was required to preserve the intended dry-run contract.

## Issues Encountered

None beyond the parser edge fixed above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 2 can build strict repository discovery and validation on top of the persisted active config and shared runner surface.

---
*Phase: 01-runtime-foundations-initialization*
*Completed: 2026-04-22*
