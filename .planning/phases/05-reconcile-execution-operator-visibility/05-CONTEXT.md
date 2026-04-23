# Phase 5: Reconcile Execution & Operator Visibility - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconcile the configured deploy branch into the host's running Docker Compose state with safe Git handling, candidate validation before host mutation, runtime removal/apply orchestration, and operator-visible logs/notifications. This phase covers no-op detection, candidate checkout/evaluation, removed-target teardown, desired-state apply, source fast-forward rules, syslog/notification behavior, and reconcile log files. It does not add container health gating beyond `docker compose up` success, nor does it expand deploy/teardown into richer manual observability features outside reconcile.

</domain>

<decisions>
## Implementation Decisions

### Managed source safety
- **D-01:** If the managed source checkout has uncommitted changes or local commits that are not a clean fast-forward from the configured deploy branch, reconcile should fail immediately and require operator cleanup.
- **D-02:** Reconcile should continue to evaluate incoming candidate state from a separate incoming checkout/work area before mutating the managed source checkout or the current runtime tree.

### Runtime mutation ordering
- **D-03:** After the incoming candidate has been fetched, validated, and built successfully, reconcile should tear down removed app/environments first and only then apply the desired runtime tree.
- **D-04:** If teardown of a removed app/environment fails during reconcile, stop the entire reconcile immediately and do not apply the incoming desired state.
- **D-05:** v1 reconcile success is defined by successful `docker compose up` execution, not by post-apply container health checks.
- **D-06:** If removals are required but the current marked runtime tree is missing or malformed, reconcile should first rebuild that current runtime tree from the current known-good managed checkout and use it for teardown; only fail if that rebuild cannot be produced safely.

### Operator visibility
- **D-07:** If the expected Unraid notification command is unavailable, reconcile should continue, emit a warning, and still write syslog/file logs.
- **D-08:** When reconcile finds no new commits to apply, record the no-op success in syslog and reconcile log files only; reserve Unraid notifications for applied success and failures.
- **D-09:** Reconcile should create one timestamped log file per run under `/var/log/unraid-actuator/`, rather than appending to a single rolling log.

### Dry-run and execution safety
- **D-10:** Phase 5 should include a public `reconcile --dry-run` mode with explicit non-mutating behavior rather than relying on accidental composition of the existing service dry-run paths.
- **D-11:** Phase 5 should include a single-run reconcile lock and fail when another reconcile is already active.

### the agent's Discretion
- Exact internal module split for Git candidate inspection, reconcile logging, notification adapters, and source fast-forward helpers.
- Exact log filename format and timestamp representation, as long as each reconcile run gets its own file.
- Exact warning/success message wording for syslog, files, and notifications, as long as the visibility contract above remains explicit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` § Phase 5: Reconcile Execution & Operator Visibility — goal, success criteria, and requirement mapping
- `.planning/REQUIREMENTS.md` § Reconciliation — `REC-01` through `REC-06`
- `.planning/REQUIREMENTS.md` § Observability & Testability — `OPS-01` through `OPS-03`
- `.planning/PROJECT.md` § Core Value — safety-first reconciliation posture
- `.planning/PROJECT.md` § Constraints — Unraid runtime limits, CLI/runtime contract, and dry-run/testability expectations

### Prior phase decisions
- `.planning/phases/01-runtime-foundations-initialization/01-CONTEXT.md` — managed source checkout contract, thin CLI pattern, and dry-run runner expectations
- `.planning/phases/02-desired-state-discovery-validation/02-CONTEXT.md` — declared-state validation posture and failure aggregation rules
- `.planning/phases/03-runtime-build-secret-materialization/03-CONTEXT.md` — candidate build contract, build marker, and ephemeral runtime-tree rules
- `.planning/phases/04-safe-deploy-teardown/04-CONTEXT.md` — full-tree vs scoped runtime behavior, fail-fast apply/down rules, and Compose safety defaults

### Current implementation surfaces
- `src/unraid_actuator/init.py` — managed source checkout and current Git clone/reuse contract
- `src/unraid_actuator/build.py` — runtime-tree build orchestration and marker-backed output contract
- `src/unraid_actuator/deploy.py` — fail-fast deploy/teardown services over the marked runtime tree
- `src/unraid_actuator/runner.py` — command abstraction for Git, Compose, logging, and notification adapters
- `src/unraid_actuator/cli.py` — existing thin command-surface pattern that reconcile should extend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/unraid_actuator/init.py` — already handles managed source checkout creation/reuse and is the natural starting point for Git-source helpers
- `src/unraid_actuator/build.py` — already produces a validated, marker-backed runtime tree from a host checkout and should be reused for candidate evaluation
- `src/unraid_actuator/deploy.py` — already provides fail-fast deploy/teardown behavior that reconcile can orchestrate rather than reimplement
- `src/unraid_actuator/runner.py` — already provides dry-run, subprocess, and recording runners suitable for Git/Compose/syslog/notification command seams
- `src/unraid_actuator/config.py` — already anchors the active host/source selection for reconcile input resolution

### Established Patterns
- Runtime commands are routed through a thin CLI into service-style functions
- Candidate state is validated before it is trusted, and generated runtime trees are the operational artifact contract
- Fail-fast behavior is already established for direct deploy/teardown and should stay consistent during reconcile

### Integration Points
- Add reconcile orchestration modules under `src/unraid_actuator/`
- Extend Git handling beyond initial clone so reconcile can fetch, diff, and evaluate an incoming candidate checkout safely
- Reuse build and deploy/teardown services instead of re-deriving Compose behavior inside reconcile
- Add logging/notification adapters that remain compatible with dry-run and recording-runner tests

</code_context>

<specifics>
## Specific Ideas

- Preserve the original product brief's separate incoming checkout under `/tmp/unraid-actuator/incoming` (or an equivalent isolated candidate workspace) so reconcile never validates directly against the mutable managed source checkout.
- Keep no-op reconciles low-noise: visible in syslog and file logs, but not as Unraid notifications.
- Treat per-run log files as the primary audit artifact for compose/apply output.

</specifics>

<deferred>
## Deferred Ideas

- Container health-based reconcile success criteria — explicitly deferred; v1 success is `docker compose up` succeeding
- Richer log retention/rotation policy beyond timestamped per-run files
- Broader manual deploy/teardown notification behavior outside reconcile

</deferred>

---

*Phase: 05-reconcile-execution-operator-visibility*
*Context gathered: 2026-04-22*
