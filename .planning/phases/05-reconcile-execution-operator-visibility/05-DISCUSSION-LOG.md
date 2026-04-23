# Phase 5: Reconcile Execution & Operator Visibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 05-reconcile-execution-operator-visibility
**Areas discussed:** Local git divergence handling, reconcile ordering, notification/log behavior, removed-target teardown failure policy, missing current runtime tree handling, dry-run behavior, reconcile locking

## Local git divergence handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fail immediately and require operator cleanup | Refuse reconcile if managed checkout is dirty or locally diverged | ✓ |
| Reset the managed checkout automatically | Force local state back to remote before reconcile | |
| Continue from local checkout if validation passes | Trust local drift if it still parses/builds | |

**User's choice:** Reconcile should fail immediately when the managed checkout has uncommitted changes or local commits that are not a clean fast-forward from the configured deploy branch.

## Reconcile ordering after candidate build

| Option | Description | Selected |
|--------|-------------|----------|
| Teardown removed targets first, then apply desired state | Remove deleted targets before `docker compose up` on the candidate runtime tree | ✓ |
| Apply desired state first, then teardown removed targets | Prioritize new runtime before removals | |
| Interleave teardown/apply target-by-target | Mix removal and apply steps | |

**User's choice:** After the incoming candidate is fetched, validated, and built successfully, reconcile should tear down removed targets first and only then apply the desired runtime tree.

## Notification availability

| Option | Description | Selected |
|--------|-------------|----------|
| Continue with warning | Missing Unraid notification command warns but does not block reconcile | ✓ |
| Fail reconcile | Notifications are required for a successful reconcile | |
| Skip silently | Missing notifications have no visible warning | |

**User's choice:** If the expected Unraid notification command is unavailable, reconcile should continue, warn, and still use syslog/file logs.

## No-op notification behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Syslog/log file only for no-op | Keep no-op reconciles out of the Unraid notification channel | ✓ |
| Send Unraid notification for no-op success | Treat no-op as user-visible success | |

**User's choice:** No-op reconciles should write to syslog and log files only; Unraid notifications are reserved for applied success and failures.

## Reconcile log file strategy

| Option | Description | Selected |
|--------|-------------|----------|
| One timestamped log file per run | Strong audit trail and easier failure triage | ✓ |
| Append to one rolling log file | Simpler filesystem footprint | |

**User's choice:** Reconcile should create one timestamped log file per run under `/var/log/unraid-actuator/`.

## Removed-target teardown failure policy

| Option | Description | Selected |
|--------|-------------|----------|
| Stop reconcile immediately | Do not apply incoming desired state after a removal failure | ✓ |
| Continue applying desired state | Report the removal failure after finishing the apply work | |

**User's choice:** If teardown of a removed app/environment fails during reconcile, stop the entire reconcile and do not apply the incoming desired state.

## Missing current runtime tree during removals

| Option | Description | Selected |
|--------|-------------|----------|
| Rebuild from current known good clone, then continue | Regenerate the current runtime tree from the managed checkout before teardown | ✓ |
| Fail reconcile safely | Require operator intervention when removals need a missing/malformed current marked runtime tree | |
| Skip removals and continue apply | Leave removed targets running if teardown inputs are unavailable | |
| Reconstruct from source repo and continue | Guess teardown inputs from non-runtime artifacts | |

**User's choice:** If removals are required but the current marked runtime tree is missing or malformed, reconcile should rebuild that current runtime tree from the current known-good managed checkout and use it for teardown. If that rebuild cannot be produced safely, then reconcile should fail.

## Public reconcile dry-run

| Option | Description | Selected |
|--------|-------------|----------|
| Support explicit `reconcile --dry-run` behavior | Public reconcile dry-run is part of Phase 5 | ✓ |
| Defer public dry-run | Keep internals testable but no public reconcile dry-run yet | |

**User's choice:** Phase 5 should include a public `reconcile --dry-run` mode with explicit non-mutating behavior.

## Reconcile locking

| Option | Description | Selected |
|--------|-------------|----------|
| Add single-run reconcile lock | Prevent overlapping cron/manual runs in Phase 5 | ✓ |
| Defer concurrency control | Allow overlapping runs for now | |

**User's choice:** Phase 5 should include a single-run reconcile lock and fail if another run is already active.

## the agent's Discretion

- Internal helper/module boundaries for Git candidate evaluation, reconcile logging, dry-run simulation, locking, and notification adapters
- Exact log filename format and reconcile success/warning wording
- Exact adapter strategy for syslog and Unraid notifications
- Exact lock-file strategy and lifetime handling

## Deferred Ideas

- Health-based reconcile success criteria
- Log retention/rotation policy beyond one file per run
- Broader notification behavior for manual deploy/teardown commands
- Alternative dry-run/reporting UX beyond the initial explicit reconcile dry-run
