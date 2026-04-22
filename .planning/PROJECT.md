# unraid-actuator

## What This Is

`unraid-actuator` is a `uv`-buildable Python package and CLI for Unraid that reconciles a host's running Docker Compose configuration against a Git-managed infrastructure repository. It is built for homelab operators managing several servers separately, with each actuator instance owning one host's view of apps, environments, secrets, validation, build artifacts, and deployment actions.

The tool turns a repository organized as `[host]/[app]/[environment]/...` into a safe operational workflow: initialize a managed source checkout, validate declared configurations, build a normalized runtime tree with decrypted secrets, and reconcile or deploy that tree using `docker compose`.

## Core Value

The running Docker Compose state for one Unraid host can be reconciled to Git safely, predictably, and without applying invalid or ambiguous configuration.

## Requirements

### Validated

- ✓ Minimal Python package scaffold exists in `pyproject.toml` — existing
- ✓ A CLI entrypoint placeholder exists in `main.py` — existing
- ✓ The repository is already tracked in git and ready for planning artifacts — existing

### Active

- [ ] `unraid-actuator init` clones or reuses an infrastructure repository, creates missing folders, and persists deploy branch, hostname, and managed source path in `/tmp/actuator-cfg.yml`
- [ ] `unraid-actuator validate` validates all or selected app/environment configurations, enforces `docker-compose.y[a]ml` XOR `build.py`, checks `apps.yaml` declarations strictly, and only warns for undeclared invalid environments
- [ ] `unraid-actuator build` generates a normalized runtime tree in ram-backed temporary storage by decrypting `secret-env.ejson`, resolving either Compose files or `build.py`, merging secret and non-secret env vars, and marking the output as actuator-managed
- [ ] `unraid-actuator reconcile` detects new commits on the configured deploy branch, validates incoming state before applying it, tears down removed apps, deploys changed ones, logs to syslog and Unraid notifications, and only fast-forwards the managed source tree after a successful build/apply sequence
- [ ] `unraid-actuator deploy` and `teardown` operate on a validated actuator-built tree and support whole-tree or single app/environment actions with safe argument handling
- [ ] The project is importable by other `uv` projects via `uv_build`, uses `strictyaml` for YAML parsing, has strong unit coverage, and keeps command execution easy to dry-run and verify

### Out of Scope

- Multi-host orchestration from one actuator instance — each installation manages a single host, even if the operator runs multiple hosts separately
- Non-Docker-Compose deployment targets — v1 is specifically for Compose-managed applications on Unraid
- Alternate secret backends beyond root-level `secret-env.ejson` plus `.env` merging — keep the initial secret model narrow and operationally predictable

## Context

The intended source repository layout is host-centric: each host directory contains `apps.yaml`, `secret-env.ejson`, and one or more app/environment directories containing either `docker-compose.yml`/`docker-compose.yaml` or a `build.py` with a zero-argument `build()` function returning Compose YAML as a string.

This program is expected to run as a cron-driven utility on Unraid, where root storage is often ram-backed, persistent flash storage should avoid decrypted secret material, and operational tooling must work with standard platform constraints. The default build output under `/tmp/unraid-actuator/build` is aligned with that environment, and documentation should strongly recommend ramfs-backed custom build paths when overridden.

The current codebase is an early brownfield scaffold rather than an implemented actuator. `main.py` is a placeholder entrypoint, `pyproject.toml` defines bare project metadata, and there are no dependencies, tests, or runtime integrations yet. The codebase map in `.planning/codebase/` captures this baseline and should inform the first milestone.

## Constraints

- **Platform**: Must run within normal Unraid server constraints — cron execution, ramfs-heavy temporary storage, and persistent USB-backed boot media shape file placement and secret-handling decisions
- **Packaging**: Must be a Python project consumable by other `uv` projects via `uv_build` — the package layout and build backend need to support both CLI use and library imports
- **Parsing**: YAML must be parsed with `strictyaml` — configuration handling should avoid ad hoc parsing and keep validation deterministic
- **Secrets**: Decrypted secret material must only exist in intentionally generated runtime trees — defaults and docs should discourage persisting plaintext secrets on non-ephemeral storage
- **Operations**: `git` and `docker compose` CLI behavior are part of the runtime contract — command execution needs clear error surfaces, dry-run support, and testable wrappers

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Repository layout is `[host]/[app]/[environment]/...` with host-root `apps.yaml` and `secret-env.ejson` | The source of truth is organized around what each host should run, and reconciliation needs a predictable structure for discovery and validation | — Pending |
| Each environment may define either `docker-compose.y[a]ml` or `build.py`, but never both | Prevents ambiguous build sources and makes validation behavior explicit | — Pending |
| Build output normalizes every environment to `docker-compose.yml` plus merged `.env` files in a generated runtime tree | Deployment should consume one consistent shape regardless of whether the source was static Compose or dynamically generated | — Pending |
| Safety beats convenience for v1 | The primary value is safe reconciliation, so invalid declared configs fail early and reconcile stops on deployment errors instead of trying to self-heal aggressively | — Pending |
| The tool is single-host per installation | The operator may manage several servers, but each actuator instance should stay narrow and predictable | — Pending |

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
*Last updated: 2026-04-22 after initialization*
