# Phase 4: Safe Deploy & Teardown - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply or remove actuator-built Docker Compose configurations with safe scope handling for one host. This phase covers full-tree deploy/teardown, scoped app/environment deploy/teardown, built-tree trust checks, and safe argument handling for the public CLI. It does not reconcile Git changes, detect removed apps from incoming commits, or add observability/notification behavior beyond what command execution already returns.

</domain>

<decisions>
## Implementation Decisions

### Failure policy
- **D-01:** Full-tree deploy and full-tree teardown should stop immediately on the first failed target and report that failure, rather than continuing through the rest of the build tree.

### Scoped target trust
- **D-02:** When `--app` and `--environment` are provided together, the selected target must exist in the built tree **and** still be valid for the current host declaration before deploy or teardown can proceed.

### Execution ordering
- **D-03:** Full-tree deploy and teardown should follow the declaration order in `apps.y[a]ml`, not alphabetical `(app, environment)` order.

### Compose safety behavior
- **D-04:** Phase 4 deploy should **not** use `docker compose up --remove-orphans`.

### Full-tree staleness policy
- **D-05:** Full-tree deploy and teardown may operate on a marked runtime tree even if its target set no longer matches the current host declaration; only scoped actions must be revalidated against current declaration membership.

### Compose environment inheritance
- **D-06:** Phase 4 should force `COMPOSE_REMOVE_ORPHANS=0` for actuator-run Compose commands but otherwise inherit the current process environment rather than aggressively scrubbing Compose-related variables.

### the agent's Discretion
- Exact internal module split for deploy-tree validation, target selection, Compose command construction, and CLI/service wiring.
- Exact wording/format of deploy and teardown success messages, as long as failures remain explicit and safe.
- Exact helper strategy for preserving declaration order from `apps.y[a]ml` while still reusing existing schema/discovery code.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` § Phase 4: Safe Deploy & Teardown — goal, success criteria, and requirement mapping
- `.planning/REQUIREMENTS.md` § Deploy & Teardown — `DEP-01` through `DEP-04`
- `.planning/PROJECT.md` § Core Value — safety-first reconciliation posture
- `.planning/PROJECT.md` § Constraints — Unraid runtime limits, CLI/runtime contract, and dry-run/testability expectations

### Prior phase decisions
- `.planning/phases/01-runtime-foundations-initialization/01-CONTEXT.md` — thin argparse CLI and public `--dry-run` contract
- `.planning/phases/02-desired-state-discovery-validation/02-CONTEXT.md` — declared-state validation posture, naming rules, and hard-error aggregation
- `.planning/phases/03-runtime-build-secret-materialization/03-CONTEXT.md` — runtime-tree marker contract, YAML extension rule, and normalized build-tree shape

### Current implementation surfaces
- `src/unraid_actuator/build.py` — current build-tree output contract and declared-target handling
- `src/unraid_actuator/build_paths.py` — build marker name and output-root helpers
- `src/unraid_actuator/build_models.py` — current `BuildResult` / `BuildTarget` contracts
- `src/unraid_actuator/cli.py` — existing command-surface and thin service wiring pattern
- `src/unraid_actuator/runner.py` — external command abstraction for Compose operations

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/unraid_actuator/build.py` — already produces a marker-backed runtime tree containing only declared targets, which is the natural input surface for deploy/teardown
- `src/unraid_actuator/build_paths.py` — defines `.UNRAID_RUNNING_CONFIGURATION`, which should anchor full-tree trust checks in Phase 4
- `src/unraid_actuator/schemas.py` — already resolves `apps.yaml` / `apps.yml`, which should be reused for scoped-target validity checks and declaration-order handling
- `src/unraid_actuator/runner.py` — already provides dry-run, subprocess, and recording runners for safe/testable Compose command execution
- `src/unraid_actuator/cli.py` — already follows the thin argparse-to-service pattern for `init`, `validate`, and `build`

### Established Patterns
- Runtime commands are routed through thin CLI parsing into service functions
- Host-scoped validity is driven by the persisted active config plus strict schema-backed host files
- Phase 3 made the build tree the normalized operational artifact, so Phase 4 should consume that tree rather than re-deriving Compose sources from the repo

### Integration Points
- Add deploy/teardown orchestration modules under `src/unraid_actuator/`
- Extend `cli.py` with `deploy` and `teardown` subcommands that preserve paired scope-flag handling
- Reuse the existing build marker and declaration loaders to validate whole-tree and scoped actions before invoking Compose
- Reuse `runner.py` for `docker compose up -d` and `docker compose down` execution, including dry-run behavior

</code_context>

<specifics>
## Specific Ideas

- Treat the actuator-built tree as the only deployable input surface in Phase 4.
- Keep safe scope handling strict: incomplete scope arguments should fail instead of guessing operator intent.
- Avoid destructive convenience flags in the first deploy/teardown phase.

</specifics>

<deferred>
## Deferred Ideas

- `--remove-orphans` deploy behavior — explicitly deferred by the locked Phase 4 safety decision
- Reconcile-driven removal/apply behavior — belongs to Phase 5, not direct Phase 4 deploy/teardown
- Richer operator observability or notification behavior for deploy/teardown — Phase 5 concern

</deferred>

---

*Phase: 04-safe-deploy-teardown*
*Context gathered: 2026-04-22*
