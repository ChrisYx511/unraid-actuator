---
phase: 02-desired-state-discovery-validation
verified: 2026-04-22T05:51:38Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "Run `unraid-actuator validate` on a Docker-equipped host against one static Compose environment and one `build.py` environment."
    expected: "Static `docker-compose.yml` and stdin-fed `build.py` output both pass through real `docker compose config -q`, grouped output is printed once, warnings-only exits 0, and hard errors exit 1."
    why_human: "Live Docker Compose integration is an external runtime dependency and is not available in this verification environment."
---

# Phase 2: Desired-State Discovery & Validation Verification Report

**Phase Goal:** Operators can trust that the desired host state is discovered and validated strictly before secrets are decrypted or runtime changes are attempted.
**Verified:** 2026-04-22T05:51:38Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Operator can validate either the full managed host tree or one specific app/environment when both selectors are provided. | ✓ VERIFIED | `src/unraid_actuator/cli.py` adds `validate`, enforces paired `--app/--environment`, and routes to `run_validate()`; `tests/unit/test_validate_service.py` and `tests/unit/test_validate_cli.py` pass. |
| 2 | Validation fails for declared app/environments that are missing, malformed, ambiguously defined, contain both `docker-compose.y[a]ml` and `build.py`, or produce invalid Compose project naming inputs. | ✓ VERIFIED | `src/unraid_actuator/discovery.py`, `src/unraid_actuator/validation_rules.py`, and `src/unraid_actuator/validate.py` produce `DECLARED_MISSING`, `SOURCE_XOR`, `SOURCE_MISSING`, `INVALID_PROJECT_NAME`, and `PROJECT_NAME_COLLISION`; covered by `test_discovery.py`, `test_validation_rules.py`, and `test_validate_service.py`. |
| 3 | Undeclared invalid app/environments surface as warnings instead of stopping validation for the declared host state. | ✓ VERIFIED | Severity is declaration-driven in `src/unraid_actuator/validation_rules.py`; CLI exits `0` for warnings-only via `report.has_errors` in `src/unraid_actuator/cli.py`; covered by `test_validation_rules.py` and `test_validate_cli.py`. |
| 4 | Dynamic `build.py` environments are validated by rendering through `docker compose config -f -`, and malformed `apps.yaml` or actuator config files return schema-driven `strictyaml` errors. | ✓ VERIFIED | `src/unraid_actuator/compose_validation.py` runs `python -I build.py` then `docker compose -p ... -f - config -q`; `src/unraid_actuator/schemas.py` and `src/unraid_actuator/config.py` use `strictyaml`; covered by `test_compose_validation.py`, `test_schemas.py`, and `test_validate_cli.py`. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/unraid_actuator/validation_models.py` | Shared validation DTOs/report contract | ✓ VERIFIED | Exists, substantive, and used by schemas/rules/report/service/tests. |
| `src/unraid_actuator/schemas.py` | Strict `apps.yaml` + secret-env structural validation | ✓ VERIFIED | Uses `strictyaml` for YAML and JSON-only structural checks for `secret-env.ejson`; no decryption path present. |
| `src/unraid_actuator/discovery.py` | Host-tree discovery and source classification | ✓ VERIFIED | Scans `host/app/environment`, classifies Compose vs `build.py` vs missing/ambiguous. |
| `src/unraid_actuator/validation_rules.py` | Declared/undeclared severity, XOR, naming rules | ✓ VERIFIED | Emits typed findings and collision checks against canonical `{app}-{environment}` names. |
| `src/unraid_actuator/runner.py` | Stdin-aware, scrubbed command execution | ✓ VERIFIED | Supports `stdin_text` and `inherit_env=False` for Compose preflight isolation. |
| `src/unraid_actuator/compose_validation.py` | Static/dynamic Compose preflight adapters | ✓ VERIFIED | Uses runner for `docker compose ... config -q` and stdin-fed dynamic validation. |
| `src/unraid_actuator/report.py` | Grouped human-readable validation report | ✓ VERIFIED | Renders Errors/Warnings/Summary from `ValidationReport`. |
| `src/unraid_actuator/validate.py` | End-to-end validation orchestration | ✓ VERIFIED | Loads active config, validates host-root contracts, runs discovery/rules/preflight, returns one report. |
| `src/unraid_actuator/cli.py` | Thin validate CLI and exit-code policy | ✓ VERIFIED | Wires subcommand, scope checks, schema error handling, report rendering, and exit codes. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/unraid_actuator/schemas.py` | `src/unraid_actuator/config.py` | StrictYAML contract handling | ✓ WIRED | `gsd-tools verify key-links` passed for plan `02-01`. |
| `src/unraid_actuator/discovery.py` | `src/unraid_actuator/validation_rules.py` | `DiscoveredEnvironment` inputs feed rule evaluation | ✓ WIRED | `src/unraid_actuator/validate.py` imports both and passes discovered candidates into rule helpers. |
| `src/unraid_actuator/validation_rules.py` | `src/unraid_actuator/validation_models.py` | Typed `ValidationFinding` severities | ✓ WIRED | Rules construct `ValidationFinding` with `FindingSeverity`. |
| `src/unraid_actuator/compose_validation.py` | `src/unraid_actuator/runner.py` | `CommandSpec` / `CommandRunner` execution | ✓ WIRED | Compose helpers build `CommandSpec(..., stdin_text=..., inherit_env=False)` and call `runner.run(...)`. |
| `src/unraid_actuator/cli.py` | `src/unraid_actuator/validate.py` | Parsed validate args routed into service | ✓ WIRED | `run_validate(...)` called directly from validate command branch. |
| `src/unraid_actuator/validate.py` | `src/unraid_actuator/report.py` | Service report rendered once before exit decision | ✓ WIRED | CLI renders returned `ValidationReport` via `render_validation_report(...)`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/unraid_actuator/validate.py` | `findings`, `checked_targets` | `load_active_config()` → `load_apps_yaml()` / `validate_secret_env_structure()` → `discover_host_tree()` → rules → Compose preflight | Yes | ✓ FLOWING |
| `src/unraid_actuator/report.py` | `report.errors`, `report.warnings` | `ValidationReport` returned by `run_validate()` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 2 validation unit coverage is green | `uv run pytest tests/unit/test_validation_models.py tests/unit/test_schemas.py tests/unit/test_discovery.py tests/unit/test_validation_rules.py tests/unit/test_compose_validation.py tests/unit/test_report_renderer.py tests/unit/test_validate_service.py tests/unit/test_validate_cli.py -q` | `24 passed in 0.04s` | ✓ PASS |
| Packaged CLI exposes validate scope flags | `uv run unraid-actuator validate --help` | Help shows `--app` and `--environment` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `VAL-01` | `02-04-PLAN.md` | Operator can validate all host configurations in the managed source tree | ✓ SATISFIED | `run_validate()` performs full-host validation when no selectors are given; `test_validate_all_host_configurations`. |
| `VAL-02` | `02-04-PLAN.md` | Operator can validate a single app/environment when both app and environment are specified | ✓ SATISFIED | CLI enforces paired flags and service scopes to one target; `test_validate_requires_both_scope_flags`, `test_validate_selected_scope_only_retains_collision_context`. |
| `VAL-03` | `02-02-PLAN.md` | Failure when both Compose and `build.py` exist | ✓ SATISFIED | Discovery classifies ambiguous sources and rules emit `SOURCE_XOR`; `test_source_classification_covers_missing_and_ambiguous_inputs`, `test_declared_missing_or_invalid_targets_are_errors`. |
| `VAL-04` | `02-02-PLAN.md` | Declared missing/invalid app/environment fails | ✓ SATISFIED | Missing declared targets emit `DECLARED_MISSING`; declared invalid discovered targets are errors; covered in rules/service tests. |
| `VAL-05` | `02-02-PLAN.md` | Undeclared invalid app/environment warns only | ✓ SATISFIED | `_severity()` returns warning for undeclared targets; `test_undeclared_invalid_targets_are_warnings`; CLI exits 0 for warnings-only runs. |
| `VAL-06` | `02-03-PLAN.md` | `build.py` output is validated through `docker compose config -f -` | ✓ SATISFIED | `validate_dynamic_build()` pipes stdout into Compose via `stdin_text`; `test_build_output_is_piped_to_compose_from_stdin`. |
| `VAL-07` | `02-01-PLAN.md`, `02-04-PLAN.md` | Malformed YAML surfaces schema-driven StrictYAML errors | ✓ SATISFIED | `config.py` and `schemas.py` parse with `strictyaml`; CLI catches and prints `YAMLValidationError`; `test_apps_yaml_schema_errors_are_reported`, `test_validate_schema_error_returns_one`. |
| `VAL-08` | `02-02-PLAN.md` | Invalid or ambiguous Compose project naming fails | ✓ SATISFIED | `compose_project_name()` enforces canonical slug inputs and collision detection; `test_invalid_or_ambiguous_project_names_fail`. |

No orphaned Phase 2 requirements were found in `.planning/REQUIREMENTS.md`; all `VAL-01` through `VAL-08` are claimed by phase plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | No blocker stub/placeholder anti-patterns detected in scanned Phase 2 source and test files. | ℹ️ Info | Validation path appears substantive rather than placeholder-only. |

### Human Verification Required

### 1. Real Docker Compose Preflight

**Test:** Run `unraid-actuator validate` on a Docker-equipped host against one valid static Compose environment and one valid `build.py` environment.  
**Expected:** Static Compose validation uses real `docker compose config -q`; dynamic `build.py` output is piped through `docker compose -f - config -q`; grouped report prints once; warnings-only exits `0`; hard errors exit `1`.  
**Why human:** This environment lacks Docker Compose, so external CLI compatibility cannot be fully verified programmatically here.

### Gaps Summary

No automated implementation gaps were found. The phase goal appears achieved in code: validation is schema-first, host discovery and rule evaluation are wired, dynamic Compose preflight is modeled correctly, and the validate CLI exits safely without introducing secret decryption or runtime mutation steps. Remaining work is only live host confirmation of Docker Compose integration.

---

_Verified: 2026-04-22T05:51:38Z_  
_Verifier: the agent (gsd-verifier)_
