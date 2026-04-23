# Phase 3: Runtime Build & Secret Materialization - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate a deterministic, actuator-managed runtime tree for the configured host in ephemeral storage. This phase covers build output path rules, secret decryption and `.env` materialization, declarative template rendering for generated Compose files, normalized build artifacts, and the build marker contract. It does not deploy Compose projects, tear them down, or reconcile Git changes.

</domain>

<decisions>
## Implementation Decisions

### Dynamic Compose generation model
- **D-01:** Replace `build.py` support with a declarative `template.yaml` mechanism. Phase 3 should not execute repository-provided Python to generate Compose output.
- **D-02:** `template.yaml` should declare includes as:
  ```yaml
  template:
    include:
      - path/to/file
  ```
  where each include path is relative to the current app/environment directory.
- **D-03:** Included template files must stay inside the same app/environment directory tree. Do not allow includes to escape upward to the host root or repository root.
- **D-04:** Build should concatenate included template fragments in the declared order, then render the combined text through Jinja2.
- **D-05:** Jinja rendering input should come from `values.yaml` only. Do not expose decrypted secrets or ambient process environment to templates.
- **D-06:** Missing or undefined Jinja values are hard build errors. All referenced template fields must resolve successfully.

### Secret materialization
- **D-07:** Decrypted secret values belong only in the built `.env` output, not in template rendering inputs.
- **D-08:** When the same key exists in both decrypted secrets and a non-secret `.env` file, the decrypted secret value overrides the `.env` value in the built output.
- **D-09:** A declared app/environment may omit a matching secret block in `secret-env.ejson`; treat that case as an empty secret set rather than a build failure.

### Build tree behavior
- **D-10:** Keep the build output ephemeral and normalized under the actuator-managed runtime-tree contract already implied by the roadmap: each successful environment must emit a normalized `docker-compose.yaml`, a merged `.env`, and the build root marker file `.UNRAID_RUNNING_CONFIGURATION`.
- **D-11:** Wherever the actuator accepts YAML-backed configuration files under its contract, it should accept both `.yaml` and `.yml` extensions rather than treating one as canonical-only.

### the agent's Discretion
- Exact internal module split for template loading, Jinja rendering, secret decryption, `.env` parsing/merging, and build-tree writing.
- Exact `strictyaml` schemas and helper DTOs for `template.yaml` / `template.yml` and `values.yaml` / `values.yml`, as long as they enforce the locked rendering rules above.
- Exact error/report formatting for build failures, as long as undefined template values and secret decryption failures surface clearly.
- Exact file-permission and temp-directory helper details, as long as the runtime tree remains ephemeral and safe by default on Unraid.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` § Phase 3: Runtime Build & Secret Materialization — goal, success criteria, and requirement mapping
- `.planning/REQUIREMENTS.md` § Build & Secrets — `BLD-01` through `BLD-07`
- `.planning/PROJECT.md` § Core Value — safety-first reconciliation posture
- `.planning/PROJECT.md` § Constraints — Unraid runtime limits, dry-run/testability expectations, and strict config parsing posture

### Prior phase decisions
- `.planning/phases/01-runtime-foundations-initialization/01-CONTEXT.md` — locked CLI/runtime/dry-run foundation
- `.planning/phases/02-desired-state-discovery-validation/02-CONTEXT.md` — discovery contracts, naming rules, and secret-free validation boundary

### Research guidance
- `.planning/research/SUMMARY.md` — phase ordering rationale and Phase 3 research flag
- `.planning/research/ARCHITECTURE.md` — thin CLI/service/adapters separation and deterministic builder guidance
- `.planning/research/PITFALLS.md` — operational pitfalls around runtime-tree generation and secret handling

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/unraid_actuator/config.py` — already anchors the active host/source selection for build input resolution
- `src/unraid_actuator/discovery.py` — already discovers the host/app/environment tree and can likely be extended for Phase 3 source-shape detection
- `src/unraid_actuator/runner.py` — shared command abstraction remains the right place for invoking external tools such as secret decryption helpers or future Compose checks
- `src/unraid_actuator/cli.py` — thin argparse shell is ready to grow a `build` subcommand without mixing in orchestration logic
- `src/unraid_actuator/schemas.py` — existing strict parsing boundary should be extended for `template.yaml` / `values.yaml` contracts

### Established Patterns
- Runtime commands are routed through a thin CLI into service-style functions
- Strict parsing and explicit DTO-style validation are already established patterns
- Validation intentionally avoided secret use in Phase 2, which makes Phase 3 the first phase allowed to decrypt and materialize secret data

### Integration Points
- Add a new build orchestration module under `src/unraid_actuator/`
- Extend discovery/schema logic to recognize declarative template-based environments in place of `build.py`
- Add Jinja2-backed rendering helpers using `values.yaml` / `values.yml` only, with strict undefined-variable behavior
- Reuse the existing runner abstraction for external secret-decryption steps and keep the build path dry-run/test friendly
- Plan for a follow-on alignment between validation and build source-shape rules, since the earlier `build.py` assumption is now superseded by `template.yaml`

</code_context>

<specifics>
## Specific Ideas

- Treat template-driven Compose generation as data rendering, not code execution.
- Keep secrets out of rendered Compose structure where possible; the built `.env` file is the secret boundary.
- Favor deterministic filesystem outputs so later deploy/reconcile phases can treat the build tree as the single runtime artifact contract.

</specifics>

<deferred>
## Deferred Ideas

- Shared template libraries outside an individual app/environment tree — explicitly deferred by the locked include-path decision.
- Any future alternate secret backend beyond host-root `secret-env.ejson` — already covered by `EXT-02`, not part of Phase 3.

</deferred>

---

*Phase: 03-runtime-build-secret-materialization*
*Context gathered: 2026-04-22*
