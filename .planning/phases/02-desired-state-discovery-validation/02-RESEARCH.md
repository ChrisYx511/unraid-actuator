# Phase 2: Desired-State Discovery & Validation - Research

**Researched:** 2026-04-22
**Domain:** Secret-free desired-state discovery, schema validation, and Compose preflight validation for one managed Unraid host
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | Operator can validate all host configurations in the managed source tree | Full-host discovery pipeline rooted at active config hostname; aggregate findings across declared/discovered envs |
| VAL-02 | Operator can validate a single app/environment when both app and environment are specified | Paired `--app` + `--environment` selectors only; validate selected target plus host-root contracts |
| VAL-03 | Operator receives a validation failure when an environment contains both `docker-compose.y[a]ml` and `build.py` | Per-environment XOR rule in discovery classifier |
| VAL-04 | Operator receives a validation failure when an app/environment declared in `apps.yaml` is missing or invalid | Strict declared-set vs discovered-set comparison; declared findings are hard errors |
| VAL-05 | Operator receives a warning, not a failure, when an undeclared app/environment exists but is invalid | Severity policy keyed by declaration status; warnings-only exit 0 |
| VAL-06 | Operator can validate dynamically generated Compose output by piping `build.py` output through `docker compose config -f -` | Use subprocess isolation for `build.py`, then `docker compose -f - config -q` |
| VAL-07 | Operator receives schema-driven validation errors for malformed `apps.yaml` or actuator config files parsed with `strictyaml` | Keep all YAML contracts on StrictYAML and surface `YAMLValidationError` details |
| VAL-08 | Operator receives a validation failure when compose project naming inputs are invalid or ambiguous for a managed app/environment | Single canonical slug policy, collision detection, explicit failure on unsafe inputs |
</phase_requirements>

## Project Constraints (from copilot-instructions.md)

- Must fit normal Unraid constraints: cron execution, ramfs-heavy temp storage, and avoidance of persistent plaintext secrets.
- Must remain a Python project consumable by other `uv` projects via `uv_build`.
- YAML parsing must use `strictyaml`; do not switch to permissive YAML parsing.
- Decrypted secret material must only exist in intentionally generated runtime trees; Phase 2 must therefore stay secret-free.
- `git` and `docker compose` CLI behavior are part of the runtime contract; external command execution must keep clear errors, dry-run support, and testable wrappers.

## Summary

Phase 2 should be implemented as a pure validation pipeline layered on top of the Phase 1 active-config loader and command runner. The command should load the active config, resolve the configured host directory, parse host-root contracts (`apps.yaml`, active actuator config, and `secret-env.ejson` structurally only), discover app/environment directories, classify each environment as static-Compose or dynamic-`build.py`, and then validate only the chosen scope. Declared invalid targets are hard errors; undeclared invalid targets are warnings.

The safest standard path is: keep YAML parsing on `strictyaml`, keep secret handling out of validation entirely, use explicit Compose project names derived from a single canonical slug policy, and delegate Compose syntax validation to `docker compose config -q` rather than custom parsing. For dynamic environments, run `build.py` in a subprocess with a minimal environment and pipe its stdout into `docker compose -f - config -q`; do not decrypt secrets and do not execute `build.py` in-process.

**Primary recommendation:** Build one `validate` service that produces a typed `ValidationReport` from strict discovery rules, then render a grouped human-readable report and exit `0` for warnings-only / `1` for any hard errors.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13+ | Runtime and subprocess orchestration | Locked in Phase 1; matches current package contract |
| `strictyaml` | 1.7.3 | Exact-schema parsing for active config and `apps.yaml` | Prevents ambiguous YAML behavior and surfaces schema-driven errors |
| Docker Compose CLI | v2.x | Authoritative Compose validator via `config -q` | Official Compose parser; avoids hand-rolled Compose validation |
| stdlib `json` + `re` | Python stdlib | Structural `secret-env.ejson` validation without decryption | Enough for secret-free formal checks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.4.2 via `uv run` | Unit and CLI validation tests | Default test runner for all new Phase 2 coverage |
| `uv_build` | 0.11.7 | Existing package/build backend | Keep existing packaging path unchanged |
| stdlib `argparse` | Python stdlib | Thin `validate` CLI subcommand | Locked Phase 1 CLI approach |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `strictyaml` | PyYAML + manual checks | Contradicts project constraint; weaker schema errors |
| `docker compose config -q` | custom Compose/YAML linting | Misses real Compose semantics and interpolation behavior |
| thin `argparse` subcommand | Click/Typer | Contradicts locked CLI decision and adds dependency weight |
| stdlib `json` structural checks for EJSON | `ejson decrypt` during validation | Violates secret-free Phase 2 decision |

**Installation:**
```bash
uv add strictyaml
uv add --dev pytest
```

**Version verification:**
- `strictyaml` latest on PyPI: **1.7.3** (uploaded 2023-03-10)
- `uv-build` latest on PyPI: **0.11.7** (uploaded 2026-04-15)
- `pytest` latest on PyPI: **9.0.3** (uploaded 2026-04-07), but the project currently constrains `<9`; keep Phase 2 test additions on the existing 8.x-compatible contract unless a deliberate upgrade is planned
- Docker Compose CLI was not installed in this environment, so an exact local version could not be verified here

## Architecture Patterns

### Recommended Project Structure
```text
src/
└── unraid_actuator/
    ├── cli.py                    # argparse wiring
    ├── validate.py               # validate orchestration entrypoint
    ├── discovery.py              # host/app/env filesystem discovery
    ├── validation_models.py      # finding/report dataclasses + enums
    ├── validation_rules.py       # pure declared/undeclared/naming/XOR checks
    └── report.py                 # grouped human-readable rendering
```

### Pattern 1: Discover → Classify → Validate → Report
**What:** separate filesystem discovery from policy checks and from CLI output.
**When to use:** always.
**Example:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class EnvironmentCandidate:
    app: str
    environment: str
    path: Path
    source_kind: str  # "compose" | "build_py" | "invalid"
    declared: bool
```

Use discovery to emit candidates only; all severity and exit-code policy belongs in validation/report layers.

### Pattern 2: One Canonical Naming Function
**What:** derive Compose project names from one canonical slug function, then detect ambiguity before using the result.
**When to use:** every declared app/environment.
**Example:**
```python
import re

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def compose_project_name(app: str, environment: str) -> str:
    if not SLUG_RE.fullmatch(app) or not SLUG_RE.fullmatch(environment):
        raise ValueError("app/environment names must already be canonical slugs")
    return f"{app}-{environment}"
```
// Source: https://docs.docker.com/compose/how-tos/project-name/

This matches the locked decision to fail on unsafe or ambiguous inputs instead of silently rewriting them.

### Pattern 3: External Validation Through the Existing Runner
**What:** all Compose checks and dynamic build execution go through `CommandRunner`.
**When to use:** static Compose validation and `build.py` validation.
**Example:**
```python
CommandSpec(
    argv=("docker", "compose", "-p", project_name, "-f", "-", "config", "-q"),
    cwd=environment_path,
    env={},
)
```
// Source: https://docs.docker.com/reference/cli/docker/compose.md and https://docs.docker.com/reference/cli/docker/compose/config/

### Pattern 4: Aggregated Findings, Single Exit Decision
**What:** collect all findings in-memory, render once, then map to exit code.
**When to use:** full-host and selected-scope validation.
**Example exit policy:**
- `errors > 0` → exit `1`
- `errors == 0` and `warnings >= 0` → exit `0`

### Recommended Validation Flow
1. Load active config with existing `load_active_config()`.
2. Resolve `host_root = source_path / hostname`.
3. Parse `apps.yaml` with `strictyaml`; fail with schema error details if invalid.
4. Parse `secret-env.ejson` as JSON only; require top-level object and `_public_key`.
5. Discover filesystem app/environment candidates.
6. Enforce source XOR: exactly one of the `docker-compose.yaml` / `docker-compose.yml` / `build.py` family, with `docker-compose.yaml` and `docker-compose.yml` treated as equivalent Compose sources.
7. Validate naming inputs for every declared target before any Compose subprocess call.
8. For static Compose: `docker compose -p <name> -f <compose-file> config -q`.
9. For dynamic `build.py`: run isolated subprocess, capture YAML stdout, then `docker compose -p <name> -f - config -q`.
10. Render grouped report: Errors, Warnings, Summary counts.

### Anti-Patterns to Avoid
- **Decrypting `secret-env.ejson` in validation:** violates locked Phase 2 boundary.
- **Executing `build.py` in-process:** mixes untrusted repo code into validator state and complicates testing.
- **Deriving project names from directories or temp paths:** risks Compose identity drift.
- **Fail-fast traversal:** contradicts the locked aggregate-error reporting rule.
- **Ad-hoc print statements during validation:** prevents grouped final report formatting.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Compose validation | custom YAML/Compose parser | `docker compose config -q` | Only Compose itself knows full merge/interpolation semantics |
| YAML schema enforcement | `yaml.safe_load` + manual dict checks | `strictyaml` schemas | Better exact-key validation and clearer operator errors |
| EJSON formal validation | secret decryption or shell parsing | `json.loads` + `_public_key` / key-shape checks | Stays secret-free and sufficient for Phase 2 |
| Exit/report policy | scattered `print()` + early returns | `ValidationFinding` + `ValidationReport` model | Enables aggregate errors and testable rendering |
| Name validation | scattered string munging | single slug validator + collision set | Prevents silent rewrites and ambiguous project names |

**Key insight:** Phase 2 is mostly policy orchestration, not parsing invention. Reuse official validators and keep project-specific logic in small pure functions.

## Common Pitfalls

### Pitfall 1: Treating undeclared invalid state as a hard failure
**What goes wrong:** unrelated junk directories stop validation of the declared host state.
**Why it happens:** declaration status is not tracked separately from validity.
**How to avoid:** compute `declared` first from `apps.yaml`, then set severity from `declared + valid/invalid`.
**Warning signs:** invalid undeclared targets produce exit `1`.

### Pitfall 2: Silent name normalization
**What goes wrong:** `My_App/prod` and `my-app/prod` collapse to the same Compose identity.
**Why it happens:** normalization rewrites inputs without collision checks.
**How to avoid:** require canonical slug inputs for declared names and fail when raw names are not already safe.
**Warning signs:** validator changes names in output instead of reporting them.

### Pitfall 3: Ambient environment affecting Compose validation
**What goes wrong:** `docker compose config` succeeds locally and fails under cron, or vice versa.
**Why it happens:** Compose interpolation can read shell and `.env` sources with documented precedence.
**How to avoid:** use a scrubbed subprocess environment during validation and keep Phase 2 secret-free.
**Warning signs:** same repo commit validates differently between shells.

### Pitfall 4: `build.py` validation becoming implicit privileged execution
**What goes wrong:** repo code runs with too much inherited environment or process state.
**Why it happens:** `build.py` is treated like harmless templating.
**How to avoid:** run it out-of-process with `sys.executable -I`, explicit cwd, and minimal env; log the script path being validated, not its output.
**Warning signs:** `build.py` can see unrelated host env vars or imports from ambient paths.

### Pitfall 5: Compose-source XOR checks that miss filename variants
**What goes wrong:** an environment with both `docker-compose.yaml` and `docker-compose.yml`, or with any Compose file plus `build.py`, slips through.
**Why it happens:** validation checks only one filename or checks too late.
**How to avoid:** classify source files before any deeper validation and treat both Compose filenames as the same source class.
**Warning signs:** validation reaches `docker compose config` before reporting source ambiguity.

## Code Examples

Verified patterns from official sources:

### Strict YAML contract for host declarations
```python
from strictyaml import Map, MapPattern, Seq, Str

APPS_SCHEMA = Map(
    {
        "apps": MapPattern(
            Str(),
            Map({"environments": Seq(Str())}),
        )
    }
)
```
// Source: https://hitchdev.com/strictyaml/using/alpha/compound/mapping/

### Validate dynamic Compose output from stdin
```python
compose_check = CommandSpec(
    argv=("docker", "compose", "-p", project_name, "-f", "-", "config", "-q"),
    cwd=environment_path,
    env={},
)
```
// Source: https://docs.docker.com/reference/cli/docker/compose.md and https://docs.docker.com/reference/cli/docker/compose/config/

### Secret-free EJSON structural check
```python
import json
import re

PUBLIC_KEY_RE = re.compile(r"^[0-9a-f]{64}$")

data = json.loads(secret_env_path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise ValueError("secret-env.ejson must contain a top-level object")
if not isinstance(data.get("_public_key"), str) or not PUBLIC_KEY_RE.fullmatch(data["_public_key"]):
    raise ValueError("secret-env.ejson must define a 64-char hex _public_key")
```
// Source: https://raw.githubusercontent.com/Shopify/ejson/master/README.md

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Directory-derived Compose identity | Explicit project naming with `-p` | Current Docker Compose docs | Stable stack identity across paths and temp workspaces |
| Permissive YAML loading + manual validation | Schema-driven `strictyaml` parsing | Current project constraint / current library usage | Better operator-facing validation errors |
| Fail-fast validation | Aggregate all hard errors, warn on undeclared invalid state | Locked Phase 2 decision | One run exposes the whole broken desired state |

**Deprecated/outdated:**
- Inferring Compose project identity from checkout/build directory names: replaced by explicit `-p` naming.
- Using `ejson decrypt` as a validator: replaced here by structural JSON-only checks because Phase 2 must remain secret-free.

## Open Questions

1. **Exact `apps.yaml` declaration shape**
   - What we know: it must declare the allowed app/environment set and be parsed by `strictyaml`.
   - What's unclear: whether the project wants room for future per-app metadata now.
   - Recommendation: use `apps: {app: {environments: [...]}}` now; it is strict, extensible, and simple to diff.

2. **Whether undeclared-but-valid app/environments should warn or stay silent**
   - What we know: undeclared invalid ones must warn, not fail.
   - What's unclear: desired operator noise level for valid but unmanaged directories.
   - Recommendation: warn once per undeclared valid target as “ignored undeclared environment”; this makes drift visible without blocking declared-state validation.

3. **How strict to be on `secret-env.ejson` value shape**
   - What we know: EJSON is just JSON and requires a top-level `_public_key`.
   - What's unclear: whether later build logic wants only flat env-var strings or more general JSON.
   - Recommendation: validate a flat object of env-style keys to string values plus underscore-prefixed metadata keys; this matches later `.env` materialization best.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | CLI, schema parsing, report rendering | ✓ | 3.14.3 | — |
| `uv` | Managed test execution | ✓ | 0.8.15 | `python -m pip` if absolutely necessary, but not preferred |
| Git | Existing active workflow and source checkout assumptions | ✓ | 2.50.1 | — |
| Docker Compose CLI | Static/dynamic Compose validation (`VAL-06`) | ✗ | — | Unit-test command specs with `RecordingRunner`; do live integration/manual validation on a target host with Docker installed |
| `pytest` | Test suite execution | ✓ via `uv run` | 8.4.2 | `uv run pytest` |

**Missing dependencies with no fallback:**
- Docker Compose CLI for live local integration verification of `docker compose config` behavior

**Missing dependencies with fallback:**
- Standalone `pytest` executable is broken in this shell, but `uv run pytest` works and should be the standard command

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 via `uv run pytest` |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/unit -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | validate full host tree | unit | `uv run pytest tests/unit/test_validate_service.py::test_validate_all_host_configurations -q` | ❌ Wave 0 |
| VAL-02 | paired app/environment scoped validation | unit | `uv run pytest tests/unit/test_validate_cli.py::test_validate_requires_both_scope_flags tests/unit/test_validate_service.py::test_validate_selected_scope_only -q` | ❌ Wave 0 |
| VAL-03 | fail when both Compose and `build.py` exist | unit | `uv run pytest tests/unit/test_discovery.py::test_source_xor_violation_is_error -q` | ❌ Wave 0 |
| VAL-04 | declared missing/invalid targets fail | unit | `uv run pytest tests/unit/test_validation_rules.py::test_declared_missing_or_invalid_targets_are_errors -q` | ❌ Wave 0 |
| VAL-05 | undeclared invalid targets warn only | unit | `uv run pytest tests/unit/test_validation_rules.py::test_undeclared_invalid_targets_are_warnings -q` | ❌ Wave 0 |
| VAL-06 | dynamic `build.py` output validated through Compose stdin | unit + guarded integration | `uv run pytest tests/unit/test_compose_validation.py::test_build_output_is_piped_to_compose_from_stdin -q` | ❌ Wave 0 |
| VAL-07 | malformed YAML surfaces StrictYAML errors | unit | `uv run pytest tests/unit/test_schemas.py::test_apps_yaml_schema_errors_are_reported -q` | ❌ Wave 0 |
| VAL-08 | invalid or ambiguous project naming fails | unit | `uv run pytest tests/unit/test_validation_rules.py::test_invalid_or_ambiguous_project_names_fail -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_validate_cli.py` — CLI scope parsing and exit-code behavior
- [ ] `tests/unit/test_discovery.py` — filesystem classification and XOR rules
- [ ] `tests/unit/test_schemas.py` — `apps.yaml`, active-config, and `secret-env.ejson` structural failures
- [ ] `tests/unit/test_validation_rules.py` — declared vs undeclared severity policy and naming collisions
- [ ] `tests/unit/test_compose_validation.py` — command-spec generation for static Compose and stdin Compose validation
- [ ] `tests/unit/test_report_renderer.py` — grouped human-readable report with counts
- [ ] Optional guarded integration test for real `docker compose config` behavior once Docker is available

## Sources

### Primary (HIGH confidence)
- Official Docker Compose reference: https://docs.docker.com/reference/cli/docker/compose/config/ — verified `config -q` as validation-only mode
- Official Docker Compose reference: https://docs.docker.com/reference/cli/docker/compose/ — verified `-f -` reads Compose config from stdin
- Official Docker Compose docs: https://docs.docker.com/compose/how-tos/project-name/ — verified project-name character rules and precedence
- Official Docker Compose docs: https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/ — verified env precedence risk during validation
- Official Python docs: https://docs.python.org/3/using/cmdline.html — verified `python -I` isolated mode behavior
- Official StrictYAML docs: https://hitchdev.com/strictyaml/using/alpha/compound/mapping/ — verified strict mapping schema pattern
- Official EJSON README: https://raw.githubusercontent.com/Shopify/ejson/master/README.md — verified EJSON JSON format and required top-level `_public_key`

### Secondary (MEDIUM confidence)
- `.planning/phases/02-desired-state-discovery-validation/02-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/PROJECT.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/PITFALLS.md`
- Existing code in `src/unraid_actuator/cli.py`, `config.py`, `runner.py`, `init.py`

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - existing project choices plus official Docker/StrictYAML docs align cleanly
- Architecture: **MEDIUM** - module split and exact schema shapes are still discretionary even though the validation pipeline is clear
- Pitfalls: **HIGH** - the highest-risk errors are directly reinforced by locked decisions and official Compose behavior

**Research date:** 2026-04-22
**Valid until:** 2026-05-22
