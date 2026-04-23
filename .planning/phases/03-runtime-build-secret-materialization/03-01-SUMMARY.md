---
phase: 03-runtime-build-secret-materialization
plan: 01
subsystem: build-foundations
tags: [build, discovery, schema, output-root]
requires:
  - phase: 02-desired-state-discovery-validation
    provides: strict host parsing, source discovery baseline, validation DTOs
provides:
  - Template/value source contract
  - Shared `apps.y[a]ml` resolver
  - Build-path safety helpers
affects: [build service, validation service, shared schema/discovery logic]
tech-stack:
  added: [Jinja2, python-dotenv]
  patterns: [template-over-build-py, shared yaml resolution, safe custom output roots]
key-files:
  created: [src/unraid_actuator/build_paths.py]
  modified: [pyproject.toml, src/unraid_actuator/validation_models.py, src/unraid_actuator/schemas.py, src/unraid_actuator/discovery.py, tests/unit/test_discovery.py, tests/unit/test_schemas.py, tests/unit/test_build_paths.py]
key-decisions:
  - "Repository-side Compose generation is declarative `template.y[a]ml` plus `values.y[a]ml`, not repo-executed Python."
  - "All host YAML-backed inputs accept both `.yaml` and `.yml` through shared resolvers."
  - "Custom build roots must be empty before the build starts."
patterns-established:
  - "Discovery, validation, and build reuse the same source classification and host declaration loaders."
requirements-completed: [BLD-02, BLD-03, BLD-04]
duration: unknown
completed: 2026-04-22
---

# Phase 3: Plan 01 Summary

**Phase 3 foundations now reflect the shipped template/value workflow, and every later build or validation path reuses the same strict host/source contracts.**

## Performance

- **Duration:** unknown
- **Started:** unknown
- **Completed:** 2026-04-22
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Replaced the stale `build.py` source branch with `SourceKind.TEMPLATE` and explicit template/value file tracking.
- Added strict loaders for `apps.y[a]ml`, `template.y[a]ml`, and mapping-only `values.y[a]ml`.
- Added reusable build-path helpers for the default runtime root, marker naming, staging, and custom-root safety checks.
- Declared the Phase 3 runtime dependencies needed for templating and deterministic `.env` parsing.

## Verification

- `uv run pytest tests/unit/test_discovery.py tests/unit/test_schemas.py tests/unit/test_build_paths.py -q`

## Task Commits

No git commits were created during this inline Copilot execution.

## Files Created/Modified

- `pyproject.toml` - Added Jinja2 and python-dotenv for template rendering and `.env` handling.
- `src/unraid_actuator/validation_models.py` - Replaced repo-executed build source metadata with template/value metadata.
- `src/unraid_actuator/schemas.py` - Added shared `.yaml`/`.yml` resolvers and strict template/value loaders.
- `src/unraid_actuator/discovery.py` - Classified environments as compose, template, missing, or ambiguous.
- `src/unraid_actuator/build_paths.py` - Added default/custom output-root guards, marker constant, and staging helpers.
- `tests/unit/test_discovery.py` - Covered template detection and ambiguous source-shape handling.
- `tests/unit/test_schemas.py` - Covered strict host/template/value YAML parsing.
- `tests/unit/test_build_paths.py` - Covered default root, empty custom roots, and safe custom-root rejection.

## Decisions Made

- Standardized all host YAML resolution through one shared helper instead of per-feature filename assumptions.
- Treated partial template inputs and mixed compose/template inputs as ambiguous so later phases could fail deterministically.

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Wave 2 can now render template sources, normalize Compose deterministically, and keep the template contract aligned across build and validation.

---
*Phase: 03-runtime-build-secret-materialization*
*Completed: 2026-04-22*
