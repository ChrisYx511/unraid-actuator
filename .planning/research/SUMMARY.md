# Project Research Summary

**Project:** unraid-actuator
**Domain:** Git-driven Docker Compose reconciler/actuator CLI for a single Unraid host
**Researched:** 2026-04-22
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project fits best as a small Python monolith with a thin CLI, strong schema validation, a deterministic build pipeline, and adapter-based command execution for `git`, `docker compose`, and `ejson`. The product’s core value is not “deployment automation” in the abstract; it is safe state reconciliation on a host that runs under cron, manages secrets, and must remain debuggable when something goes wrong.

Research points toward a normalized runtime-tree model: fetch a target commit, parse and validate host/app/environment definitions strictly, render every environment into a consistent `docker-compose.yml` plus merged `.env`, and only then generate and apply a plan. The major risks are premature source-state advancement, Compose identity drift, ambient-environment interpolation surprises, and secret leakage to persistent media or logs.

## Key Findings

### Recommended Stack

Use Python with a real `uv_build` backend, `strictyaml` for schema-driven YAML parsing, and explicit CLI adapters around `git`, `docker compose`, and `ejson`. Prefer stdlib-heavy implementation choices and deterministic subprocess wrappers over richer abstractions that hide runtime behavior from operators.

**Core technologies:**
- **Python 3.12+**: implementation language and runtime — strong fit for systems scripting plus package reuse
- **`uv_build`**: packaging/build backend — required for clean `uv build` integration
- **`strictyaml`**: strict config parsing — prevents ambiguous YAML behavior
- **Docker Compose CLI**: deploy/validate surface — authoritative contract for runtime behavior
- **Git CLI**: source control integration — explicit commit/ref handling matters more than object-model richness

### Expected Features

Operators will expect strict validation, a safe build artifact, deterministic project naming, scoped deploy/teardown, and a reconcile loop that refuses to advance local source state until the candidate state is proven deployable. Dry-run capability is not optional for this product because it runs unattended on a host via cron.

**Must have (table stakes):**
- managed checkout + persisted init config
- schema-driven validation of declared apps/environments
- normalized build tree with rendered Compose and merged `.env`
- safe deploy, teardown, and reconcile flows
- dry-run/testable execution model

**Should have (competitive):**
- last-successful-commit tracking
- policy checks for dangerous Compose patterns
- health-gated success criteria

**Defer (v2+):**
- rollback workflows
- alternate secret backends
- multi-host orchestration

### Architecture Approach

The recommended architecture separates pure planning/rules from side effects. CLI handlers call application services, services use domain rules and planners, and adapters own all subprocess/filesystem interactions. Candidate builds happen in ephemeral storage, while a small persistent state file records last successful deployment metadata.

**Major components:**
1. **Discovery + validation** — parse repo layout, `apps.yaml`, and environment invariants
2. **Build pipeline** — render/normalize Compose and `.env` artifacts
3. **Planner + executor** — compute and optionally apply ordered actions
4. **State store** — track last successful commit and managed inventory
5. **Observability layer** — logs, syslog, notifications, and dry-run reporting

### Critical Pitfalls

1. **Advancing the checkout before success** — deploy from a candidate commit and only advance persistent state after full success
2. **Treating invalid as deleted** — invalid desired state must block reconcile, not trigger teardown
3. **Unstable Compose project names** — use deterministic host/app/env-derived identity
4. **Secret leakage** — keep plaintext only in ephemeral build paths and redact logs
5. **Ambient environment drift** — materialize env explicitly and scrub subprocess environments

## Implications for Roadmap

Based on research, the project should be phased around trust and determinism before operational automation:

### Phase 1: Package and runtime foundations
**Rationale:** package shape, settings, command runner abstractions, and persistent non-secret state are prerequisites for every other phase.
**Delivers:** importable package, CLI shell, config model, command runner interfaces, dry-run foundation.
**Addresses:** safe execution architecture and trust boundaries.
**Avoids:** subprocess logic leaking everywhere.

### Phase 2: Repository discovery and validation
**Rationale:** reconcile safety depends on getting desired-state modeling right before any apply logic exists.
**Delivers:** strict schemas, host/app/env discovery, XOR build rules, project naming, validation semantics.
**Addresses:** invalid-vs-removed distinctions and unsafe config ambiguity.
**Avoids:** accidental teardowns from bad commits.

### Phase 3: Build and secrets pipeline
**Rationale:** all deploy paths depend on a normalized runtime artifact.
**Delivers:** EJSON decryption, `.env` merge, `build.py` execution model, generated Compose output, build markers.
**Uses:** tmpfs-friendly ephemeral output patterns.
**Implements:** deterministic runtime-tree generation.

### Phase 4: Deploy, teardown, and reconcile execution
**Rationale:** only safe once validation and build artifacts are reliable.
**Delivers:** targeted deploy/teardown, candidate-commit reconcile, fast-forward-on-success behavior, action planning.
**Addresses:** source-state advancement, deletion semantics, and Compose identity stability.

### Phase 5: Observability and hardening
**Rationale:** operators need confidence once the core engine works.
**Delivers:** syslog/unraid notification integration, richer logs, policy warnings, health-gated success, stronger test coverage.
**Avoids:** “it returned 0 so we called it done” behavior.

### Phase Ordering Rationale

- validation must precede build because bad source trees need to fail before secrets are decrypted or actions are planned
- build must precede reconcile because deploy input needs a deterministic runtime shape
- plan/executor architecture should be in place before any host mutation logic ships
- hardening belongs after the basic lifecycle exists, but key security constraints must inform earlier phases

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** `build.py` trust model and subprocess isolation details
- **Phase 5:** exact Unraid notification integration surface and health-check strategy

Phases with standard patterns:
- **Phase 1:** package layout, runners, settings, and test scaffolding
- **Phase 2:** schema-driven parsing and deterministic validation rules

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Mostly grounded in official docs and explicit project constraints |
| Features | HIGH | Directly reinforced by the product brief and normal operator expectations |
| Architecture | MEDIUM | Structure is strong, but some adapter details will still be refined during planning |
| Pitfalls | HIGH | The highest-risk failure modes are well understood for Git/Compose/secret workflows |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- Exact Python baseline for Unraid compatibility vs current scaffold (`>=3.13`)
- Exact persisted-state location and format for last successful deployment metadata
- Exact notification adapter behavior on standard Unraid systems

## Sources

### Primary (HIGH confidence)
- https://docs.astral.sh/uv/concepts/projects/build/ — packaging/build behavior
- https://hitchdev.com/strictyaml/ — strict YAML parsing behavior
- https://docs.docker.com/reference/cli/docker/compose/config/ — Compose validation behavior
- https://docs.docker.com/compose/how-tos/project-name/ — stable project naming rules
- https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/ — env precedence behavior

### Secondary (MEDIUM confidence)
- https://github.com/Shopify/ejson — EJSON operational model
- https://docs.docker.com/reference/cli/docker/compose/up/
- https://docs.docker.com/reference/cli/docker/compose/down/

---
*Research completed: 2026-04-22*
*Ready for roadmap: yes*
