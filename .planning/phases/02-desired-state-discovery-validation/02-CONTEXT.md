# Phase 2: Desired-State Discovery & Validation - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove that the configured host's desired state can be discovered and validated safely before any build, deploy, or reconcile work happens. This phase covers host-tree discovery, `apps.yaml` and actuator-config parsing, declaration checks, `docker-compose.y[a]ml` XOR `build.py` enforcement, Compose validation behavior, and validation reporting for the currently configured host. It does not build runtime trees, decrypt secrets for use, deploy Compose projects, or reconcile Git changes.

</domain>

<decisions>
## Implementation Decisions

### Secret handling during validation
- **D-01:** Phase 2 validation should **not decrypt secrets at all**.
- **D-02:** Validation should **check `secret-env.ejson` structurally/formally only**, and leave actual secret decryption/use to the build phase.

### Compose project naming
- **D-03:** Compose project names should be derived from **normalized `{app}-{environment}`** rather than including hostname.
- **D-04:** Validation should **fail on unsafe or ambiguous naming inputs** instead of silently normalizing or rewriting them.

### Validation outcomes
- **D-05:** If validation finds **only undeclared invalid app/environments**, the command should **exit 0 and report warnings**.
- **D-06:** If declared app/environments are invalid, validation should **collect all hard errors for the current run and then fail**, rather than stopping at the first error.

### Validation report style
- **D-07:** Validation output should be a **grouped human-readable report** with separate errors/warnings plus final counts.

### the agent's Discretion
- Exact internal module split for repository discovery, schema parsing, Compose checks, and report rendering.
- Exact `strictyaml` schemas for `apps.yaml`, actuator config, and the structural validation shape for `secret-env.ejson`, as long as they enforce the locked rules above.
- Exact helper/DTO names for validation findings, summaries, and CLI formatting.
- Exact mechanics for running `docker compose config` for static Compose files versus `build.py` output, as long as Phase 2 remains secret-free.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` § Phase 2: Desired-State Discovery & Validation — phase goal, success criteria, and requirement mapping
- `.planning/REQUIREMENTS.md` § Discovery & Validation — `VAL-01` through `VAL-08`
- `.planning/PROJECT.md` § Core Value — safety-first validation posture
- `.planning/PROJECT.md` § Constraints — Unraid runtime limits, strict YAML parsing, and CLI/testability expectations

### Prior phase decisions
- `.planning/phases/01-runtime-foundations-initialization/01-CONTEXT.md` — locked Phase 1 decisions around single active config, thin argparse CLI, and dry-run-friendly runner abstractions
- `.planning/phases/01-runtime-foundations-initialization/01-VERIFICATION.md` — verified package/runtime foundation and existing reusable surfaces

### Research guidance
- `.planning/research/SUMMARY.md` — validates the roadmap order and safety-first sequencing
- `.planning/research/ARCHITECTURE.md` — recommends thin CLI + services + adapters separation
- `.planning/research/PITFALLS.md` — cautions around Compose validation, naming, and safe pre-apply checks

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/unraid_actuator/config.py` — already loads the active single-host config and should anchor Phase 2 host selection
- `src/unraid_actuator/runner.py` — shared command abstraction for `docker compose config` and other external validation checks
- `src/unraid_actuator/cli.py` — thin argparse shell ready to grow a `validate` subcommand without mixing in business logic

### Established Patterns
- Runtime commands are routed through thin CLI parsing into service-style functions (`run_init(...)`)
- Persisted config is schema-backed with `strictyaml`, and Phase 2 should follow the same explicit-contract style
- Dry-run/testability is already established as a cross-command pattern and should continue in validation work

### Integration Points
- Add a new validation orchestration module under `src/unraid_actuator/`
- Extend `cli.py` with a `validate` subcommand that reads the existing active config
- Reuse `CommandRunner` for Compose validation invocations and make validation findings unit-testable without live infrastructure where possible

</code_context>

<specifics>
## Specific Ideas

- Validation is a **hard gate for declared configurations**, but it should remain **secret-free** in this phase.
- `secret-env.ejson` belongs in validation only as a **format/structure check**, not as decrypted runtime input.
- The operator experience should favor **one grouped report** over a fail-fast stream so a single run exposes the whole broken desired state.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-desired-state-discovery-validation*
*Context gathered: 2026-04-22*
