---
phase: 04-safe-deploy-teardown
verified: 2026-04-22T19:07:02Z
status: passed
score: 5/5 must-haves verified
---

# Phase 4: Safe Deploy & Teardown Verification Report

**Phase Goal:** Operators can apply or remove validated actuator-built configurations with safe scope handling.
**Verified:** 2026-04-22T19:07:02Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Full-tree deploy/teardown only operate on a marked actuator runtime tree. | ✓ VERIFIED | `src/unraid_actuator/deploy_tree.py` enforces `.UNRAID_RUNNING_CONFIGURATION` in `require_marked_runtime_tree()`, and both full-tree/scoped resolution paths call it before command construction. Covered by `tests/unit/test_deploy_tree.py::test_runtime_tree_must_be_marked_and_well_formed`. |
| 2 | Scoped deploy/teardown only succeed when both selectors are provided and the target both exists in the build tree and is still declared for the current host. | ✓ VERIFIED | CLI rejects partial scope in `src/unraid_actuator/cli.py`; services re-guard partial scope in `src/unraid_actuator/deploy.py`; `resolve_scoped_target()` in `src/unraid_actuator/deploy_tree.py` requires current declaration membership plus on-disk target presence. Covered by deploy/teardown CLI and service tests. |
| 3 | Full-tree actions follow `apps.y[a]ml` declaration order, while stale marked targets are tolerated only for full-tree actions and appended deterministically. | ✓ VERIFIED | `resolve_full_tree_targets()` iterates declared keys from `load_declared_environments(...)` first, then appends remaining build-only targets in sorted order. `resolve_scoped_target()` rejects undeclared stale targets. Covered by `tests/unit/test_deploy_tree.py::test_full_tree_targets_preserve_declared_order_and_append_stale_targets`. |
| 4 | Full-tree deploy and teardown stop on first failure, and scoped actions execute exactly one validated target without widening scope. | ✓ VERIFIED | `_run_runtime_action()` in `src/unraid_actuator/deploy.py` raises on first non-zero `CommandResult`; scoped path resolves a single target tuple only. Covered by `test_deploy_full_is_ordered_and_fail_fast`, `test_teardown_full_is_ordered_and_fail_fast`, and scoped service tests. |
| 5 | Compose commands are explicit and safe: explicit project identity, no `--remove-orphans`, `COMPOSE_REMOVE_ORPHANS=0`, and inherited host environment. | ✓ VERIFIED | `src/unraid_actuator/compose_runtime.py` builds explicit `docker compose -p ... --project-directory ... --env-file ... -f ... up -d|down` specs with `env={"COMPOSE_REMOVE_ORPHANS": "0"}` and `inherit_env=True`. `runner.py` merges inherited env when `inherit_env=True`. Covered by `tests/unit/test_compose_runtime.py`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/unraid_actuator/deploy_models.py` | Typed runtime target/result DTOs | ✓ VERIFIED | Defines `RuntimeTarget` and `RuntimeActionResult`; imported by compose/service/CLI tests. |
| `src/unraid_actuator/deploy_tree.py` | Marker trust, scoped validity, declaration-order selection | ✓ VERIFIED | Substantive implementation for marker checks, full-tree ordering, stale-target handling, and scoped validation. |
| `src/unraid_actuator/compose_runtime.py` | Explicit Compose up/down command factories | ✓ VERIFIED | Builds exact deploy/teardown `CommandSpec` values with forced orphan-removal-safe env. |
| `src/unraid_actuator/deploy.py` | Fail-fast deploy/teardown orchestration | ✓ VERIFIED | Wires target resolution to compose spec factories through the runner abstraction and stops on first failure. |
| `src/unraid_actuator/cli.py` | Public `deploy`/`teardown` commands with paired scope handling | ✓ VERIFIED | Adds subcommands, safe parser guards, service dispatch, and `ValueError`/`YAMLValidationError` exit-path handling. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `deploy_tree.py` | `build_paths.py` | `BUILD_MARKER_NAME` | ✓ WIRED | Direct import and use in `require_marked_runtime_tree()`. |
| `deploy_tree.py` | `schemas.py` | `load_declared_environments(...)` | ✓ WIRED | `_declared_keys()` loads current host declarations from schema-backed apps YAML. |
| `compose_runtime.py` | `validation_rules.py` | `compose_project_name(...)` | ✓ WIRED | Both deploy and teardown derive the same project identity from the shared validator. |
| `deploy.py` | `deploy_tree.py` | `resolve_full_tree_targets(...)` / `resolve_scoped_target(...)` | ✓ WIRED | Services do not reimplement trust/scope logic. |
| `deploy.py` | `compose_runtime.py` | `compose_up_spec(...)` / `compose_down_spec(...)` | ✓ WIRED | Services execute only the explicit Compose specs defined in Phase 4. |
| `cli.py` | `deploy.py` | `run_deploy(...)` / `run_teardown(...)` | ✓ WIRED | Public CLI dispatches directly into the runtime services. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/unraid_actuator/deploy_tree.py` | `declared_keys` | `load_active_config()` → host root → `load_declared_environments()` | Yes | ✓ FLOWING |
| `src/unraid_actuator/deploy_tree.py` | `targets_by_key` | On-disk marked build tree scanned from `build_root` | Yes | ✓ FLOWING |
| `src/unraid_actuator/deploy.py` | `targets` | `resolve_full_tree_targets()` or `resolve_scoped_target()` | Yes | ✓ FLOWING |
| `src/unraid_actuator/compose_runtime.py` | `project_name` / `CommandSpec` | `compose_project_name(app, environment)` + `RuntimeTarget` paths | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 4 unit coverage passes | `uv run pytest tests/unit/test_deploy_tree.py tests/unit/test_compose_runtime.py tests/unit/test_deploy_service.py tests/unit/test_teardown_service.py tests/unit/test_deploy_cli.py -q` | `16 passed in 0.05s` | ✓ PASS |
| Public deploy command exposes safe scope/build-root surface | `uv run unraid-actuator deploy --help` | Help includes `--build-root`, `--app`, `--environment` | ✓ PASS |
| Public teardown command exposes safe scope/build-root surface | `uv run unraid-actuator teardown --help` | Help includes `--build-root`, `--app`, `--environment` | ✓ PASS |
| Incomplete scoped deploy fails safely | `uv run unraid-actuator deploy --app nextcloud` | Exit code `2` | ✓ PASS |
| Incomplete scoped teardown fails safely | `uv run unraid-actuator teardown --environment production` | Exit code `2` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `DEP-01` | `04-01`, `04-02` | Operator can deploy a full build tree only when it is marked as an actuator-generated running configuration | ✓ SATISFIED | Marker gate in `deploy_tree.py`, service usage in `deploy.py`, plus marked-tree tests. |
| `DEP-02` | `04-01`, `04-02`, `04-03` | Operator can deploy a single app/environment only when both selectors are provided and that target is valid for the current host | ✓ SATISFIED | CLI paired-scope checks, service paired-scope checks, and `resolve_scoped_target()` membership+presence validation. |
| `DEP-03` | `04-01`, `04-02`, `04-03` | Operator can tear down a full build tree or a single valid app/environment from the built configuration | ✓ SATISFIED | `run_teardown()` uses the same trusted/scoped target resolution and explicit `compose_down_spec()` command contract. |
| `DEP-04` | `04-02`, `04-03` | Operator receives safe argument handling when only one of app or environment is provided | ✓ SATISFIED | `cli.py` parser errors on partial scope; `deploy.py` also raises `ValueError` on partial scope outside CLI. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | No blocker anti-patterns found in Phase 4 implementation files | — | Grep hits were limited to benign list/dict initializations in implementation and test fixtures, not placeholders or hollow logic. |

### Manual Host Checks Remaining (Non-Blocking)

Docker Compose is unavailable in this environment, so these host-level checks remain recommended after merge even though the code and test seams satisfy the Phase 4 contract:

1. **Live full-tree deploy**
   - **Test:** Run `unraid-actuator deploy --build-root <marked-root>` on a Docker host.
   - **Expected:** `docker compose up -d` runs with `-p`, `--project-directory`, `--env-file`, `-f`, and no `--remove-orphans`.
2. **Live full-tree teardown**
   - **Test:** Run `unraid-actuator teardown --build-root <marked-root>` on a Docker host.
   - **Expected:** Matching project is torn down with plain `down` only; no `-v`, `--rmi`, or orphan-removal flags.
3. **Live fail-fast batch behavior**
   - **Test:** Use a marked tree with one later broken target and run full-tree deploy/teardown.
   - **Expected:** Batch stops immediately on the first failing target.

### Gaps Summary

No automated gaps found. Phase 4 code substantively implements the roadmap goal and all four deploy requirements, including the locked safety decisions around marker trust, scoped revalidation, declaration-order execution, fail-fast behavior, stale full-tree tolerance, and Compose orphan-removal safety. Remaining work is limited to manual host verification because Docker is not available in this verification environment.

---

_Verified: 2026-04-22T19:07:02Z_
_Verifier: the agent (gsd-verifier)_
