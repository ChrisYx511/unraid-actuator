# Phase 1: Runtime Foundations & Initialization - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the package installable, importable, configurable, and dry-run/test friendly for one Unraid host. This phase covers the package/runtime foundation, the `init` command, the persisted active config contract, and the shared command-runner abstraction. It does not include validation, build, deploy, or reconcile behavior beyond what is needed to establish the foundation.

</domain>

<decisions>
## Implementation Decisions

### Runtime compatibility
- **D-01:** Keep the project on **Python 3.13+** for v1. Do not broaden compatibility in Phase 1.

### CLI surface
- **D-02:** Build the CLI as a **thin stdlib `argparse` subcommand interface** rather than using Typer or Click in Phase 1.

### Init state contract
- **D-03:** `/tmp/actuator-cfg.yml` should store a **single active config** containing **repo URL, deploy branch, hostname, and managed source path**.

### Dry-run contract
- **D-04:** Expose a **public `--dry-run` path in Phase 1** and implement a **shared command runner abstraction** that later mutating commands can reuse.

### the agent's Discretion
- Exact `src/unraid_actuator/` module split, as long as the package stays importable and the CLI remains thin.
- Exact shape of internal request/response DTOs and runner interfaces, as long as they preserve dry-run testability.
- Exact layout of logging/error helpers for the Phase 1 foundation.

</decisions>

<specifics>
## Specific Ideas

- Favor a minimal-dependency foundation suitable for a cron-first Unraid admin tool.
- Treat Phase 1 as the place to lock the CLI and packaging contract, not to start implementing validation or reconcile logic.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` § Phase 1: Runtime Foundations & Initialization — phase goal, success criteria, and requirement mapping
- `.planning/REQUIREMENTS.md` § Initialization & Configuration — `INIT-01` through `INIT-04`
- `.planning/REQUIREMENTS.md` § Observability & Testability — `OPS-04`
- `.planning/REQUIREMENTS.md` § Packaging & Developer Experience — `PKG-01` through `PKG-03`
- `.planning/PROJECT.md` § Core Value — safety-first project priority
- `.planning/PROJECT.md` § Constraints — Unraid runtime limits, packaging rules, parsing requirements, and dry-run/testability expectations

### Research guidance
- `.planning/research/SUMMARY.md` — rationale for doing package/runtime foundations before validation or apply work
- `.planning/research/ARCHITECTURE.md` — recommended `src/` package layout, command-runner abstraction, and state separation
- `.planning/research/STACK.md` — packaging/build backend guidance and minimal-dependency stack recommendations

### Existing baseline
- `.planning/codebase/STRUCTURE.md` — current flat repository layout and likely insertion points
- `.planning/codebase/CONVENTIONS.md` — current coding-style baseline and gaps to close in Phase 1

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml` — existing project metadata and Python version pin can be expanded into the final package/build configuration
- `main.py` — current placeholder entrypoint can either be replaced or turned into a thin compatibility shim
- `.gitignore` — already ignores common Python build and virtualenv artifacts

### Established Patterns
- The codebase is currently a minimal flat scaffold with no package layout, no dependencies, and no tests
- The current runtime assumption is Python `>=3.13`, which now becomes an explicit locked decision for Phase 1
- Output is currently `print()` based and there is no command abstraction yet; Phase 1 will establish the real pattern

### Integration Points
- Introduce `src/unraid_actuator/` as the real package root
- Update `pyproject.toml` to support `uv_build`, console entry points, and test tooling
- Replace the placeholder root entrypoint with thin CLI wiring into package code
- Add `tests/` and fixture support for dry-run/testable command execution

</code_context>

<deferred>
## Deferred Ideas

- Richer config metadata beyond the active single-config contract — revisit only if later phases need it
- Heavier CLI frameworks (Typer/Click) — deferred unless later ergonomics outweigh the minimal-dependency preference
- Broader Python compatibility targets — explicitly deferred by the locked Phase 1 decision to stay on 3.13+

</deferred>

---

*Phase: 01-runtime-foundations-initialization*
*Context gathered: 2026-04-22*
