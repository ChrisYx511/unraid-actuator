# Architecture Research

**Domain:** Git-driven Docker Compose reconciler/actuator CLI for one Unraid host
**Researched:** 2026-04-22
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         CLI / Entry Layer                           │
├──────────────────────────────────────────────────────────────────────┤
│  init   validate   build   reconcile   deploy   teardown            │
│    │         │        │         │         │         │               │
├────┴─────────┴────────┴─────────┴─────────┴─────────┴────────────────┤
│                    Application / Use-Case Layer                     │
├──────────────────────────────────────────────────────────────────────┤
│  InitService   ValidateService   BuildService   ReconcileService    │
│                               │                     │               │
│                         Planner / Diff Engine  Apply Orchestrator   │
├──────────────────────────────────────────────────────────────────────┤
│                        Domain / Policy Layer                        │
├──────────────────────────────────────────────────────────────────────┤
│  Repository layout rules   App/env identity   Validation rules      │
│  Desired manifest model    Operation plan     Safety invariants     │
├──────────────────────────────────────────────────────────────────────┤
│                     Ports / Adapter Boundary                        │
├──────────────────────────────────────────────────────────────────────┤
│  GitPort  ComposePort  SecretPort  BuildScriptPort  RunnerPort      │
│  StateStorePort  FsPort  NotifierPort  ClockPort                    │
├──────────────────────────────────────────────────────────────────────┤
│                         Adapter / IO Layer                          │
├──────────────────────────────────────────────────────────────────────┤
│  git CLI   docker compose CLI   ejson CLI   subprocess runner       │
│  workspace FS   strictyaml loader   syslog/unraid notifications     │
├──────────────────────────────────────────────────────────────────────┤
│                       External Systems / Storage                    │
│  Git repo   source checkout   ephemeral build tree   Docker Engine  │
│  syslog     Unraid notify     persisted apply state                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Recommended shape:** a small Python monolith with strict internal boundaries. Keep the CLI thin, orchestration in application services, domain logic pure, and all shell/file effects behind ports. This is the safest way to support dry runs, fake runners, and deterministic tests without over-engineering the project into a distributed system.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI layer | Parse args, select command, render output, map errors to exit codes | `argparse` or another very thin CLI wrapper |
| Use-case services | Orchestrate one command end-to-end | service modules per command |
| Domain models | Represent host/app/env, manifests, actions, and invariants | frozen dataclasses + enums |
| Discovery layer | Walk `[host]/[app]/[environment]` and classify files | filesystem traversal + typed records |
| Validation engine | Enforce repo and schema invariants | pure functions over parsed models |
| Build pipeline | Render normalized runtime tree | deterministic builder service |
| Planner / diff engine | Compare desired and applied/live state and emit ordered actions | pure planning code |
| Execution layer | Run or simulate `git`, `docker compose`, `ejson`, and `build.py` | command specs + runners |
| State store | Persist last successful commit and managed inventory | JSON/YAML file in persistent state dir |
| Observability | Write logs, syslog entries, and notifications | logging + notifier adapters |

## Recommended Project Structure

```text
src/
└── unraid_actuator/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── commands/
    │   ├── init.py
    │   ├── validate.py
    │   ├── build.py
    │   ├── reconcile.py
    │   ├── deploy.py
    │   └── teardown.py
    ├── application/
    │   ├── dto.py
    │   ├── planner.py
    │   └── services/
    ├── domain/
    │   ├── models.py
    │   ├── rules.py
    │   ├── identities.py
    │   ├── build_rules.py
    │   └── errors.py
    ├── ports/
    │   ├── runner.py
    │   ├── git.py
    │   ├── compose.py
    │   ├── secrets.py
    │   ├── build_scripts.py
    │   ├── state_store.py
    │   ├── filesystem.py
    │   └── notifications.py
    ├── adapters/
    │   ├── cli/
    │   ├── parsing/
    │   ├── fs/
    │   └── observability/
    └── config/
        ├── settings.py
        └── schema.py

tests/
├── unit/
├── integration/
└── fixtures/
```

### Structure Rationale

- **`src/` layout:** best fit for a package that must be both importable and executable.
- **`domain/`:** highest-value area for unit tests because most safety rules belong here.
- **`ports/` + `adapters/`:** essential for dry-run support and fake subprocess runners.
- **`tests/fixtures/`:** needed for representative repository trees, secrets fixtures, and reconcile scenarios.

## Architectural Patterns

### Pattern 1: Functional Core, Imperative Shell

**What:** keep policy and planning pure; isolate shell-outs and file mutation in adapters.
**When to use:** always.
**Trade-offs:** slightly more structure up front, much easier verification and dry-run support later.

### Pattern 2: Explicit Plan Before Apply

**What:** every mutating command first builds an `OperationPlan`, then either prints it (`--dry-run`) or executes it.
**When to use:** `reconcile`, `deploy`, and `teardown`.
**Trade-offs:** requires a planner abstraction, but makes behavior inspectable and testable.

### Pattern 3: Command Runner Abstraction

**What:** represent shell commands as data, then pass them to a runner implementation.
**When to use:** every `git`, `docker compose`, `ejson`, and build-script execution.
**Trade-offs:** one more interface, but it is the key to deterministic testing.

### Pattern 4: Ephemeral Candidate Build Workspace

**What:** never reconcile directly from the mutable checkout. Build and validate a candidate runtime tree in ephemeral storage, then apply from that tree.
**When to use:** always for `build` and `reconcile`.
**Trade-offs:** more filesystem work, much better safety around secrets and partial updates.

## Data Flow

### Reconcile Flow

```text
cron / CLI reconcile
    ↓
load settings + current managed state
    ↓
git fetch target branch
    ↓
no new commit?
    ├── yes → exit cleanly
    └── no
         ↓
create candidate workspace for target commit
         ↓
discover host tree + parse YAML + validate declarations
         ↓
build normalized runtime tree in ephemeral path
         ↓
validate each rendered compose via `docker compose config -q`
         ↓
generate desired manifest
         ↓
load last applied manifest / managed inventory
         ↓
planner computes ordered actions
         ↓
dry-run? print plan : executor applies actions
         ↓
on full success only → persist applied state + advance managed ref + notify
```

### Key Data Flows

1. **Source-of-truth flow:** Git commit → parsed declarations → desired manifest → operation plan.
2. **Safety flow:** candidate commit → validation → normalized runtime tree → compose validation → apply eligibility.
3. **Audit flow:** command results → structured report → log files/syslog/notifications → persisted last-successful state.

### State Management

1. **Managed source state:** persistent checkout and branch/ref metadata; no decrypted secrets.
2. **Ephemeral build state:** rendered compose files, merged `.env`, decrypted secret material; tmpfs-friendly and disposable.
3. **Applied state record:** last successful commit, managed inventory, and non-secret fingerprints; small and persistent.

## Anti-Patterns

### Anti-Pattern 1: Reconciling directly from the live checkout

**Why it is wrong:** mixes candidate state with current state and makes failures harder to contain.
**Do this instead:** build from an immutable candidate snapshot and advance the managed ref only after success.

### Anti-Pattern 2: Putting subprocess logic inside CLI handlers

**Why it is wrong:** destroys testability and makes dry-run support bolted-on rather than architectural.
**Do this instead:** keep CLI handlers thin and route all work through services + adapters.

### Anti-Pattern 3: Treating temp paths as runtime identity

**Why it is wrong:** Compose names resources based on project identity and path-derived names drift.
**Do this instead:** derive stable project names from host/app/environment and pass them explicitly.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Git | subprocess to `git fetch`, `git rev-parse`, `git worktree/checkout` operations | Must preserve fast-forward-only semantics for managed source updates |
| Docker Compose | subprocess to `docker compose config/up/down` | Centralize flags, project naming, and environment scrubbing |
| EJSON | subprocess to `ejson decrypt` | Use only during build, not as a persistent runtime dependency |
| Syslog / Unraid notifications | adapter per sink | Must never leak secret values |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ application services | request/response DTOs | avoid passing raw argparse objects deeply |
| application ↔ domain | typed domain models | domain should remain side-effect free |
| application ↔ adapters | ports/interfaces | enables fake implementations in tests |

## Sources

- `.planning/PROJECT.md`
- https://docs.docker.com/reference/cli/docker/compose/config/
- https://docs.docker.com/reference/cli/docker/compose/up/
- https://docs.docker.com/reference/cli/docker/compose/down/
- https://docs.docker.com/compose/how-tos/project-name/

---
*Architecture research for: Git-driven Docker Compose reconciler/actuator CLI for one Unraid host*
*Researched: 2026-04-22*
