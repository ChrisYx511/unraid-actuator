# Milestones

## v1.0 Initial Release (Shipped: 2026-04-23)

**Phases completed:** 7 phases, 21 plans, 34 tasks

**Key accomplishments:**

- uv_build packaging, argparse entrypoints, and a reusable dry-run-aware runner now define the actuator foundation.
- `unraid-actuator init` now persists the active host checkout contract and safely clones or reuses the managed source tree.
- Shared validation models and strict host-root schema checks now define the secret-free boundary for desired-state validation.
- Host discovery and pure validation rules now distinguish missing declared state, undeclared warnings, source ambiguity, and project-name collisions before any Compose subprocess work runs.
- Compose preflight now supports static files and stdin-fed `build.py` output through the shared runner, and validation output renders as one grouped human-readable report.
- `unraid-actuator validate` now validates the configured host or one selected app/environment with grouped reporting, scoped flag safety, and full-host naming-collision context.
- Phase 3 foundations now reflect the shipped template/value workflow, and every later build or validation path reuses the same strict host/source contracts.
- Template-driven environments now render deterministically from ordered includes, and both template and static sources normalize through the same secret-free Compose pipeline.
- Phase 3 now has a clear secret boundary: decrypt once through EJSON, keep secrets out of templates, and materialize one deterministic merged `.env` file per built environment.
- The build command now produces one staged, actuator-managed runtime tree that downstream deploy and reconcile flows can trust.
- Phase 3 finished as an operator-facing feature: validation and build now share the same template/value source contract, and the CLI exposes `unraid-actuator build` cleanly.
- Phase 4 now has a typed runtime-tree contract and deterministic Compose command builders, so deploy/teardown orchestration can stay thin and safety-focused.
- Deploy and teardown now run as fail-fast services over the marked runtime tree, with scoped requests limited to one still-declared target and no hidden widening of scope.
- `unraid-actuator deploy` and `unraid-actuator teardown` are now public commands with safe paired-scope handling, default or custom build-root support, and thin dispatch into the runtime services.
- Phase 5 now has explicit Git-safety and removal-planning contracts, so reconcile can reason about candidate state and removals without mutating or guessing.
- Phase 5 now has centralized operator visibility and concurrency guards, so reconcile runs have one audit trail and cannot overlap accidentally.
- Phase 5 now has the actual reconcile coordinator, wired as an orchestrator over existing build/validate/deploy services with explicit dry-run semantics.
- Phase 5 is now publicly operable from the CLI through `unraid-actuator reconcile`, including explicit reconcile dry-run behavior.
- The build service now hard-enforces validate-before-build, so invalid host trees can no longer reach secret decryption or staged runtime-tree writes.
- Phase 3 is auditable again: all five summaries and the missing verification report now exist, and the main planning docs describe the shipped template/value build flow instead of stale `build.py` behavior.
- Phase 7 closed the last stale milestone blocker by documenting and testing the intended git-failure bubbling policy instead of adding new CLI error formatting.

---
