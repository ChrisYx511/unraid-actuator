---
phase: 03-runtime-build-secret-materialization
verified: 2026-04-22
status: passed
score: 5/5 must-haves verified
reverified_in: 06-build-safety-verification-recovery
---

# Phase 3: Runtime Build & Secret Materialization Verification Report

**Phase Goal:** Operators can build a deterministic, actuator-managed runtime tree with normalized Compose output and merged environment data in ephemeral storage.  
**Verified:** 2026-04-22  
**Status:** passed  
**Re-verification:** Yes — recovered during Phase 6 after the milestone audit found missing Phase 3 summary and verification artifacts.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Discovery, schema parsing, and build-path helpers implement the shipped template/value workflow and shared `.yaml`/`.yml` resolution. | ✓ VERIFIED | `src/unraid_actuator/validation_models.py`, `src/unraid_actuator/schemas.py`, `src/unraid_actuator/discovery.py`, and `src/unraid_actuator/build_paths.py` define `SourceKind.TEMPLATE`, shared `apps.y[a]ml` resolution, strict template/value loaders, and output-root safety helpers. Covered by `tests/unit/test_discovery.py`, `tests/unit/test_schemas.py`, and `tests/unit/test_build_paths.py`. |
| 2 | Template sources render deterministically and both static/template inputs normalize through secret-free Compose commands. | ✓ VERIFIED | `src/unraid_actuator/template_render.py` enforces ordered includes, containment, and `StrictUndefined`; `src/unraid_actuator/compose_build.py` normalizes both source kinds with `--no-interpolate --format yaml` and `COMPOSE_DISABLE_ENV_FILE=1`. Covered by `tests/unit/test_template_render.py` and `tests/unit/test_compose_build.py`. |
| 3 | Secret decryption and `.env` materialization stay isolated from templates and produce deterministic merged output. | ✓ VERIFIED | `src/unraid_actuator/secrets.py` decrypts EJSON and extracts per-environment secrets, while `src/unraid_actuator/env_materialize.py` merges repo `.env` values with secret precedence. Covered by `tests/unit/test_secrets.py` and `tests/unit/test_env_materialize.py`. |
| 4 | The build service materializes only declared targets into a staged runtime tree, writes the build marker on success, and preserves the prior final root on failure. | ✓ VERIFIED | `src/unraid_actuator/build.py` builds declared targets only, stages under a sibling temp directory, writes `.UNRAID_RUNNING_CONFIGURATION`, and promotes only after success. Covered by `tests/unit/test_build_service.py`. |
| 5 | Validation and the public CLI share the shipped template/value contract, and the build entrypoint is operator-facing and safe. | ✓ VERIFIED | `src/unraid_actuator/compose_validation.py`, `src/unraid_actuator/validate.py`, and `src/unraid_actuator/cli.py` share template-aware preflight behavior and expose `unraid-actuator build`. Covered by `tests/unit/test_compose_validation.py`, `tests/unit/test_validate_service.py`, and `tests/unit/test_build_cli.py`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `03-01-SUMMARY.md` through `03-05-SUMMARY.md` | Complete Phase 3 execution trail | ✓ VERIFIED | All five plan summaries are present and map the shipped implementation to Phase 3 requirements. |
| `src/unraid_actuator/build.py` / `build_models.py` | Staged runtime-tree orchestration and typed result contracts | ✓ VERIFIED | Build service produces declared-only runtime trees and typed results. |
| `src/unraid_actuator/template_render.py` / `compose_build.py` | Template rendering and Compose normalization | ✓ VERIFIED | Shared helpers implement the template/value workflow and secret-free normalization path. |
| `src/unraid_actuator/secrets.py` / `env_materialize.py` | Secret boundary and deterministic `.env` output | ✓ VERIFIED | Secret handling is isolated and serialized deterministically. |
| `src/unraid_actuator/validate.py` / `cli.py` | Template-aware validation and public build command | ✓ VERIFIED | Validation/build share source rules and the CLI exposes `build` safely. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 3 unit bundle passes | `uv run pytest tests/unit/test_build_paths.py tests/unit/test_template_render.py tests/unit/test_compose_build.py tests/unit/test_secrets.py tests/unit/test_env_materialize.py tests/unit/test_build_service.py tests/unit/test_compose_validation.py tests/unit/test_validate_service.py tests/unit/test_build_cli.py -q` | `36 passed` | ✓ PASS |
| Packaging remains valid after build-gap closure | `uv build` | passed | ✓ PASS |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
| --- | --- | --- | --- |
| `BLD-01` | Build all current host app/environment configurations into `/tmp/unraid-actuator/build` by default | ✓ SATISFIED | `src/unraid_actuator/build_paths.py` defines the default root and `src/unraid_actuator/build.py` builds declared targets into that managed runtime tree. |
| `BLD-02` | Build into a custom output path only when it is empty before build starts | ✓ SATISFIED | `validate_output_root(...)` accepts only missing/empty custom roots. Covered by `tests/unit/test_build_paths.py` and exercised through `tests/unit/test_build_service.py`. |
| `BLD-03` | Safe failure when a non-default build output path is non-empty | ✓ SATISFIED | Custom non-empty roots fail before staging/build work. Covered by `tests/unit/test_build_paths.py`. |
| `BLD-04` | Normalized `docker-compose.yml` for every built environment | ✓ SATISFIED | `normalize_static_compose(...)` and `normalize_rendered_compose(...)` canonicalize both source kinds before write. |
| `BLD-05` | Merged `.env` output combining decrypted secrets and non-secret env data | ✓ SATISFIED | `materialize_env_file(...)` merges base env values with secret override precedence and writes deterministic output per built environment. |
| `BLD-06` | Build failure when required secret decryption cannot complete | ✓ SATISFIED | `decrypt_secret_env(...)` raises on decrypt failure or malformed JSON, and the build service preserves the prior final tree on failure. |
| `BLD-07` | Build root marker file `.UNRAID_RUNNING_CONFIGURATION` on each successful tree | ✓ SATISFIED | `src/unraid_actuator/build.py` writes the marker into the staged root immediately before promotion. |

### Cross-Phase Context

Phase 6 additionally closed the later-discovered `validate -> build` wiring gap by making the build service call `run_validate_for_host(...)` before any output-root staging or secret decryption. That closure restores the intended operator safety flow, but it does not change the underlying Phase 3 requirement ownership or the shipped runtime-tree contract summarized here.

### Manual Host Checks Remaining (Non-Blocking)

These checks remain recommended on a real Docker/EJSON-equipped Unraid host because they are outside this in-repo verification scope:

1. **Real Compose normalization**
   - Run `unraid-actuator build` against one static environment and one template-driven environment on a Docker host and confirm the generated `docker-compose.yml` files are canonical and uninterpolated.
2. **Real EJSON decrypt compatibility**
   - Run `unraid-actuator build` on a host with valid EJSON key material and confirm secret-bearing environments emit the expected merged `.env`.

### Gaps Summary

No blocking Phase 3 gaps remain. The missing audit artifacts were restored in Phase 6, and the shipped Phase 3 implementation satisfies `BLD-01..07` with in-repo evidence plus explicitly separated host-only follow-up checks.

---

_Verified: 2026-04-22_  
_Verifier: the agent_
