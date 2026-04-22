# Feature Research

**Domain:** Git-driven Docker Compose reconciler/actuator CLI for a single Unraid host
**Researched:** 2026-04-22
**Confidence:** HIGH for table stakes, MEDIUM for differentiators

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Managed source checkout + persisted init config | Operators need a repeatable source of truth and a known working path | LOW | Covers repo URL, deploy branch, hostname, and clone location persistence. |
| Strict config discovery and validation | No one will trust automated reconcile without strong validation | HIGH | Must validate declared apps/environments strictly and treat undeclared invalid configs as warnings only. |
| Build of a normalized runtime tree | Safe deploys require a consistent artifact shape regardless of source form | HIGH | Every environment should become `docker-compose.yml` plus merged `.env` in a marked actuator build tree. |
| Compose validation against rendered output | Prevents bad deploys from malformed Compose or `build.py` output | MEDIUM | `docker compose config -q` should run against the final resolved output, including stdin validation for generated YAML. |
| Deterministic project identity | Compose stacks must be stable across temp dirs and repeated runs | MEDIUM | Use host/app/environment-derived names, not directory names. |
| Reconcile loop with changed-vs-removed handling | This is the core product behavior | HIGH | Must fetch, diff commits, validate candidate state, tear down removals, and deploy changes safely. |
| Dry-run/testable execution model | Required by the project brief and crucial for operator confidence | HIGH | Every mutating workflow should be representable as an execution plan before it runs. |
| Logging and operator-visible failure reporting | Cron jobs need post-hoc observability | MEDIUM | Syslog plus log files are baseline; Unraid notifications are part of the requested operator experience. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Policy checks for risky Compose settings | Helps prevent self-inflicted dangerous deploys on a homelab host | MEDIUM | Examples: privileged containers, Docker socket mounts, or risky host path exposure. |
| Last-successful-commit tracking | Makes state transitions auditable and safer than “just pull and hope” | MEDIUM | Strong differentiator for safe Git-driven automation. |
| Health-gated reconcile success | Avoids marking deploy success on CLI exit code alone | HIGH | Requires waiting for running/healthy services before recording success. |
| Per-app/environment scoped deploy and teardown | Useful for controlled operations outside the full reconcile loop | LOW | Already in the product brief; adds operational flexibility without changing the trust model. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-host orchestration from one instance | Sounds efficient for homelab operators with several servers | Expands the blast radius, state model, and failure modes dramatically | Keep one actuator per host and reuse the same package/config model |
| Automatic rollback in the first release | Feels safer on paper | Easy to implement badly; rollback semantics for data/stateful apps are not trivial | Track last successful commit first, then add explicit rollback later |
| Direct deploy from the mutable repo checkout | Simpler implementation | Couples source state, candidate state, and runtime state; increases secret leakage risk | Always build and deploy from a normalized candidate tree |
| Ambient host env interpolation as part of desired state | Convenient during development | Makes cron and interactive runs behave differently | Build a materialized `.env` explicitly and scrub subprocess env |

## Feature Dependencies

```text
init/config
    └── requires ──> repository discovery
                         └── requires ──> strict YAML schemas

validation
    └── requires ──> rendered compose generation
                         └── requires ──> secrets/env merge

reconcile
    ├── requires ──> validation
    ├── requires ──> build/runtime tree
    └── requires ──> planner + execution runner

dry-run
    └── enhances ──> build / deploy / reconcile / teardown
```

### Dependency Notes

- **Reconcile requires validation:** mutating host state before candidate validation defeats the core safety promise.
- **Validation requires rendered compose:** `build.py` output must be normalized first or validation is incomplete.
- **Dry-run enhances all mutating flows:** it is not a separate product surface; it should fall out of the execution architecture.
- **Deterministic project naming underpins deploy, teardown, and reconcile:** without stable identity, action planning is unsafe.

## MVP Definition

### Launch With (v1)

- [ ] Managed source checkout + persisted settings — necessary to establish the source-of-truth workflow
- [ ] Strict discovery and validation rules — required for operator trust
- [ ] Normalized build output with secrets/env merge — required for safe deploy inputs
- [ ] Deploy and teardown from a marked build tree — core operational control
- [ ] Reconcile loop with commit detection and safe fast-forward behavior — the product’s main differentiator
- [ ] Dry-run-capable execution architecture and strong unit tests — required by the project brief

### Add After Validation (v1.x)

- [ ] Policy pack for dangerous Compose settings — add once the core lifecycle is stable
- [ ] Health-gated success checks — add after basic deploy/reconcile plumbing works
- [ ] More structured logs or machine-readable reports — add when operators want richer automation hooks

### Future Consideration (v2+)

- [ ] Explicit rollback workflow — only after last-successful state and health checks are reliable
- [ ] Alternate secret providers — defer until EJSON + `.env` is proven insufficient
- [ ] Multi-host coordination — explicitly deferred by project scope

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Init/config persistence | HIGH | LOW | P1 |
| Validation engine | HIGH | HIGH | P1 |
| Build/runtime tree | HIGH | HIGH | P1 |
| Deploy/teardown | HIGH | MEDIUM | P1 |
| Reconcile engine | HIGH | HIGH | P1 |
| Dry-run/testability | HIGH | HIGH | P1 |
| Policy checks | MEDIUM | MEDIUM | P2 |
| Health-gated success | MEDIUM-HIGH | HIGH | P2 |
| Rollback workflow | MEDIUM | HIGH | P3 |
| Multi-host orchestration | LOW for current scope | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Watchtower-style tools | GitOps/CI deploy workflows | Our Approach |
|---------|------------------------|----------------------------|--------------|
| Source of truth | Image/tag driven, not repo-layout driven | Git-driven but often CI-centric | Host-local Git source + local reconcile |
| Validation | Usually limited | Often externalized to CI | Built into the actuator for every run |
| Secrets | Varies widely | Often external secret managers | EJSON + `.env` merge, scoped to host/app/env |
| Dry-run | Often limited | Usually possible in CI | First-class because this runs on cron on the host |

## Sources

- Project brief in `.planning/PROJECT.md`
- Docker Compose CLI docs and environment/project-name docs
- EJSON documentation
- Common patterns from Git-driven operations tooling and single-host deployment workflows

---
*Feature research for: Git-driven Docker Compose reconciler/actuator CLI for a single Unraid host*
*Researched: 2026-04-22*
