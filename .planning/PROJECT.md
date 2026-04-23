# unraid-actuator

## What This Is

`unraid-actuator` is a shipped `uv`-buildable Python package and CLI for Unraid that reconciles a host's running Docker Compose configuration against a Git-managed infrastructure repository. Each actuator instance owns one host's view of apps, environments, secrets, validation, build artifacts, and deployment actions.

The tool turns a repository organized as `[host]/[app]/[environment]/...` into a safe operational workflow: initialize a managed source checkout, validate declared configurations, build a normalized runtime tree with decrypted secrets, and reconcile or deploy that tree using `docker compose`.

## Core Value

The running Docker Compose state for one Unraid host can be reconciled to Git safely, predictably, and without applying invalid or ambiguous configuration.

## Requirements

### Validated

- ✓ v1.0 ships a real `uv_build` package, packaged CLI entrypoints, and a dry-run-friendly command runner.
- ✓ v1.0 ships `unraid-actuator init` with clone-or-reuse behavior and a persisted active-config contract in `/tmp/actuator-cfg.yml`.
- ✓ v1.0 ships strict `strictyaml`-backed host discovery and validation with declared-state enforcement, undeclared warnings, naming checks, and Compose/template/value preflight coverage.
- ✓ v1.0 ships deterministic runtime-tree builds with template/value rendering, secret merge, actuator-managed markers, and validate-before-build enforcement before decrypt/materialization.
- ✓ v1.0 ships safe deploy and teardown commands over actuator-built trees with explicit full-tree versus scoped target handling.
- ✓ v1.0 ships candidate-based reconcile with removal planning, operator-visible logs and notifications, and managed-checkout promotion only after successful apply.

### Active

- [ ] No committed next-milestone product requirements exist yet; the next step is milestone definition and roadmap creation.

### Out of Scope

- Multi-host orchestration from one actuator instance — each installation manages a single host, even if the operator runs multiple hosts separately
- Non-Docker-Compose deployment targets — v1 is specifically for Compose-managed applications on Unraid
- Alternate secret backends beyond root-level `secret-env.ejson` plus `.env` merging — keep the initial secret model narrow and operationally predictable
- Automatic health-gated deploy or reconcile success — deferred until a later milestone so v1 can keep an explicit `docker compose up` success contract

## Context

The intended source repository layout is host-centric: each host directory contains `apps.yaml` or `apps.yml`, `secret-env.ejson`, and one or more app/environment directories containing either `docker-compose.yaml`/`docker-compose.yml` or a declarative `template.yaml`/`template.yml` paired with `values.yaml`/`values.yml`.

This program is expected to run as a cron-driven utility on Unraid, where root storage is often ram-backed, persistent flash storage should avoid decrypted secret material, and operational tooling must work with standard platform constraints. The default build output under `/tmp/unraid-actuator/build` is aligned with that environment, and documentation strongly recommends ramfs-backed custom build paths when overridden.

v1.0 shipped in 7 phases across 21 plans and 34 summarized tasks. The codebase now contains roughly 5,686 lines of Python across `src/` and `tests/`, including the packaged CLI, strict host validation, template/value runtime build flow, EJSON-backed secret materialization, safe deploy/teardown services, reconcile/logging/notification orchestration, validate-before-build hardening, and explicit regression coverage for git-failure bubbling in `init` and `reconcile`.

The remaining follow-up work is intentionally non-blocking: real host verification for Docker/EJSON/Unraid behaviors, optional Nyquist validation backfill, and whatever v1.1 scope the next milestone defines.

## Constraints

- **Platform**: Must run within normal Unraid server constraints — cron execution, ramfs-heavy temporary storage, and persistent USB-backed boot media shape file placement and secret-handling decisions
- **Packaging**: Must be a Python project consumable by other `uv` projects via `uv_build` — the package layout and build backend need to support both CLI use and library imports
- **Parsing**: YAML must be parsed with `strictyaml` — configuration handling should avoid ad hoc parsing and keep validation deterministic
- **Secrets**: Decrypted secret material must only exist in intentionally generated runtime trees — defaults and docs should discourage persisting plaintext secrets on non-ephemeral storage
- **Operations**: `git` and `docker compose` CLI behavior are part of the runtime contract — command execution needs clear error surfaces, dry-run support, and testable wrappers

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Repository layout is `[host]/[app]/[environment]/...` with host-root `apps.y[a]ml` and `secret-env.ejson` | The source of truth is organized around what each host should run, and reconciliation needs a predictable structure for discovery, build, and validation | Validated in Phases 2-6 |
| Each environment may define either `docker-compose.y[a]ml` or declarative `template.y[a]ml` + `values.y[a]ml`, but never both | Prevents ambiguous build sources, removes repo-executed Python, and keeps template rendering deterministic | Validated in Phases 2-3 |
| Build output normalizes every environment to `docker-compose.yaml` plus merged `.env` files in a generated runtime tree | Deployment should consume one consistent shape regardless of whether the source was static Compose or template-rendered | Validated in Phases 3 and 6 |
| Deploy and teardown operate only on marked actuator-built trees, with full-tree trust distinct from scoped current-host revalidation | Keeps direct runtime actions safe without blocking legitimate full-tree use of older marked outputs | Validated in Phase 4 |
| Safety beats convenience for v1 | The primary value is safe reconciliation, so invalid declared configs fail early, build now validates before materializing secrets, and deploy/teardown stop on the first runtime error instead of trying to self-heal aggressively | Validated in Phases 2-6 |
| The tool is single-host per installation | The operator may manage several servers, but each actuator instance should stay narrow and predictable | Validated in Phase 1 |
| Git-related `RuntimeError` failures in `init` and `reconcile` should bubble unchanged at the CLI boundary | The operator asked for explicit bubbling rather than CLI-side normalization, and tests now lock that policy in place | Validated in Phase 7 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-23 after the v1.0 milestone*
