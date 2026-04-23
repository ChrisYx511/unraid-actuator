# Phase 4: Safe Deploy & Teardown - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 04-safe-deploy-teardown
**Areas discussed:** Failure policy, scoped target trust, execution ordering, Compose safety behavior, stale full-tree policy, Compose environment inheritance

## Failure policy

| Option | Description | Selected |
|--------|-------------|----------|
| Stop on first failure | Fail fast during full-tree deploy/teardown | ✓ |
| Continue and summarize all failures | Best-effort batch processing | |

**User's choice:** Stop immediately on the first failed target and report it.

## Scoped target trust

| Option | Description | Selected |
|--------|-------------|----------|
| Built tree + current host declaration | Scoped target must still be valid for the current host | ✓ |
| Built tree only | Trust any target present in the built tree | |

**User's choice:** Scoped deploy/teardown targets must exist in the built tree and still be valid for the current host declaration.

## Execution ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Alphabetical `(app, environment)` order | Deterministic but detached from host declaration order | |
| Follow `apps.y[a]ml` order | Preserve declaration order for full-tree actions | ✓ |

**User's choice:** Full-tree deploy/teardown should follow `apps.y[a]ml` declaration order.

## Compose safety behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Do not use `--remove-orphans` | Safer initial deploy behavior | ✓ |
| Use `--remove-orphans` during deploy | More aggressive cleanup behavior | |

**User's choice:** Do not use `--remove-orphans` in Phase 4.

## Stale full-tree policy

| Option | Description | Selected |
|--------|-------------|----------|
| Reject stale full-tree roots | Require current host declaration to match the marked build tree before full-tree deploy/teardown | |
| Allow stale marked roots | Trust any marked build tree for full-tree deploy/teardown | ✓ |

**User's choice:** Allow full-tree deploy/teardown to operate on a marked runtime tree even when its target set no longer matches the current host declaration.

## Compose environment inheritance

| Option | Description | Selected |
|--------|-------------|----------|
| Force only `COMPOSE_REMOVE_ORPHANS=0` and otherwise inherit environment | Minimal intervention while locking orphan behavior | ✓ |
| Scrub most Compose env vars and allowlist only Docker essentials | More deterministic but riskier to host compatibility | |

**User's choice:** Force `COMPOSE_REMOVE_ORPHANS=0` and otherwise inherit the current environment for actuator-run Compose commands.

## the agent's Discretion

- Internal module boundaries for deploy-tree validation, target selection, and Compose command helpers
- Exact CLI success/failure message wording
- Exact helper strategy for declaration-order preservation

## Deferred Ideas

- Reconcile-driven removal semantics
- Richer deploy/teardown observability
- Future consideration of orphan-removal behavior
