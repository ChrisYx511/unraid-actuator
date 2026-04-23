# Phase 4: Safe Deploy & Teardown - Research

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full-tree deploy and full-tree teardown should stop immediately on the first failed target and report that failure, rather than continuing through the rest of the build tree.
- **D-02:** When `--app` and `--environment` are provided together, the selected target must exist in the built tree **and** still be valid for the current host declaration before deploy or teardown can proceed.
- **D-03:** Full-tree deploy and teardown should follow the declaration order in `apps.y[a]ml`, not alphabetical `(app, environment)` order.
- **D-04:** Phase 4 deploy should **not** use `docker compose up --remove-orphans`.

### the agent's Discretion
- Exact internal module split for deploy-tree validation, target selection, Compose command construction, and CLI/service wiring.
- Exact wording/format of deploy and teardown success messages, as long as failures remain explicit and safe.
- Exact helper strategy for preserving declaration order from `apps.y[a]ml` while still reusing existing schema/discovery code.

### Deferred Ideas (OUT OF SCOPE)
- `--remove-orphans` deploy behavior — explicitly deferred by the locked Phase 4 safety decision
- Reconcile-driven removal/apply behavior — belongs to Phase 5, not direct Phase 4 deploy/teardown
- Richer operator observability or notification behavior for deploy/teardown — Phase 5 concern
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-01 | Operator can deploy a full build tree only when it is marked as an actuator-generated running configuration | Root marker gate, build-tree contract checks, ordered full-tree target enumeration |
| DEP-02 | Operator can deploy a single app/environment only when both selectors are provided and that target is valid for the current host | Paired-flag CLI rule, scoped target validation against both build tree and current declared host targets |
| DEP-03 | Operator can tear down a full build tree or a single valid app/environment from the built configuration | Explicit `docker compose down` command factory, same target identity rules as deploy, fail-fast batch loop |
| DEP-04 | Operator receives safe argument handling when only one of app or environment is provided | Reuse existing argparse paired-scope error pattern in both `deploy` and `teardown` commands |
</phase_requirements>

**Researched:** 2026-04-22  
**Domain:** Docker Compose deploy/teardown orchestration over an actuator-built runtime tree  
**Confidence:** HIGH

## Project Constraints (from copilot-instructions.md)

- Keep work inside the GSD workflow; don't plan direct ad-hoc repo edits outside it.
- Must fit normal Unraid constraints: cron-driven execution, ramfs-heavy temp storage, persistent USB media sensitivity.
- Must remain a `uv_build` Python package importable by other `uv` projects.
- YAML parsing should continue using `strictyaml`; don't introduce ad hoc YAML parsing.
- Decrypted secrets should only exist in intentionally generated runtime trees.
- `git` and `docker compose` CLI behavior are part of the runtime contract; keep clear error surfaces, dry-run support, and testable wrappers.

## Summary

Phase 4 should stay thin: validate the built runtime tree, select targets safely, then shell out to `docker compose up -d` or `docker compose down` through the existing `CommandRunner`. No new deployment library is needed. The safest design is a small deploy/teardown service layer plus a compose-command factory that always passes explicit project identity and file paths.

The most important operational caveat is project identity. `docker compose` chooses project names from multiple sources, but `-p` has highest precedence. Always pass the same computed `compose_project_name(app, environment)` on both deploy and teardown. Also avoid ambient Compose behavior leaking in: Docker Compose source shows `COMPOSE_REMOVE_ORPHANS` can change default orphan-removal behavior for both `up` and `down` if you don't scrub/override it.

**Primary recommendation:** Build Phase 4 around `run_deploy()` / `run_teardown()` services that (1) gate on the build-root marker, (2) resolve targets in `apps.y[a]ml` declaration order, (3) enforce paired scope args, and (4) execute explicit `docker compose -p ... --project-directory ... --env-file ... -f ... up -d|down` specs through `CommandRunner`, stopping on first failure.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---|---:|---|---|
| Docker Compose CLI | v2 runtime contract; exact host version must be verified on target host | Actual apply/teardown engine | Project requirement explicitly says runtime contract is `docker compose` |
| Python stdlib `argparse` | stdlib | CLI paired-argument handling | Already locked in Phase 1 and used successfully in `validate` |
| Internal `CommandRunner` / `DryRunRunner` / `RecordingRunner` | current repo | Execution, dry-run, test seams | Already established project pattern for all external commands |
| `strictyaml` | 1.7.3 | Load current `apps.y[a]ml` and preserve declared targets | Already project-standard schema boundary |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---|---:|---|---|
| `pytest` via `uv run` | 8.4.2 | Unit/CLI orchestration tests | All Phase 4 verification without live Docker |
| `uv` | 0.8.15 | Test runner entrypoint in this repo | Local/test execution |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| `docker compose` CLI | Docker SDK / custom orchestration | Reject: conflicts with runtime contract and makes operator debugging harder |
| Implicit cwd / implicit `.env` / implicit project name | Explicit `-p`, `--project-directory`, `--env-file`, `-f` | Use explicit flags; safer and deterministic |
| Native Compose `--dry-run` | Existing `DryRunRunner` | Use existing runner; it works without Docker installed and matches project dry-run contract |

**Installation:** No new Python package is required for Phase 4. Host runtime still needs `docker compose` installed.

**Version verification:**
- `pytest`: verified locally with `uv run pytest --version` -> `8.4.2`
- `strictyaml`: verified from `uv.lock` -> `1.7.3`
- `docker compose`: **not installed in this planning environment**; planner should require host verification with `docker compose version`

## Architecture Patterns

### Recommended Project Structure

```text
src/unraid_actuator/
├── deploy.py            # deploy/teardown orchestration entrypoints
├── deploy_models.py     # target/result DTOs (optional but clean)
├── deploy_tree.py       # marker + target-shape + scope validation helpers
├── compose_runtime.py   # compose command factory helpers
└── cli.py               # thin subcommand wiring only
```

### Pattern 1: Runtime-tree gate before any Compose call
**What:** Validate the build root first. For full-tree: require root dir + marker + valid target file shape. For scoped: same, plus selected target must exist in tree and still be declared for current host.  
**When to use:** Every deploy or teardown path.

**Example:**
```python
from pathlib import Path

from .build_paths import BUILD_MARKER_NAME
from .schemas import load_declared_environments
from .config import load_active_config

def require_marked_runtime_tree(build_root: Path) -> None:
    if not build_root.is_dir():
        raise ValueError(f"build root does not exist: {build_root}")
    marker = build_root / BUILD_MARKER_NAME
    if not marker.is_file():
        raise ValueError(f"build root is not an actuator-managed runtime tree: {build_root}")

def declared_targets_in_order(config_path: Path) -> tuple[tuple[str, str], ...]:
    config = load_active_config(path=config_path)
    host_root = config.source_path / config.hostname
    declared = load_declared_environments(host_root)
    return tuple((item.app, item.environment) for item in declared)
```
Source: current repo `build_paths.py`, `schemas.py`, `config.py`

### Pattern 2: Explicit Compose identity on every call
**What:** Always pass `-p`, `--project-directory`, `--env-file`, and `-f`.  
**When to use:** All `up` and `down` calls.

**Example:**
```python
from .runner import CommandSpec
from .validation_rules import compose_project_name

def compose_up_spec(output_dir, app: str, environment: str) -> CommandSpec:
    project_name = compose_project_name(app, environment)
    return CommandSpec(
        argv=(
            "docker", "compose",
            "-p", project_name,
            "--project-directory", str(output_dir),
            "--env-file", str(output_dir / ".env"),
            "-f", str(output_dir / "docker-compose.yml"),
            "up", "-d",
        ),
        cwd=output_dir,
        env={"COMPOSE_REMOVE_ORPHANS": "0"},
        inherit_env=True,  # or replace with a later allowlisted env helper
    )
```
Source: Docker Compose official docs for `-p`, `--project-directory`, `--env-file`, `up -d`

### Pattern 3: Fail-fast ordered batch executor
**What:** Full-tree deploy/teardown loops over targets in declaration order and stops immediately on first non-zero result.  
**When to use:** Full-tree operations only.

**Example:**
```python
def run_batch(targets, spec_factory, runner):
    for target in targets:
        result = runner.run(spec_factory(target))
        if result.exit_code != 0:
            raise ValueError(
                f"{target.app}/{target.environment} failed: "
                f"{result.stderr or result.stdout or 'compose command failed'}"
            )
```
Source: locked Phase 4 decision D-01 + current `runner.py` pattern

### Anti-Patterns to Avoid
- **Alphabetical full-tree execution:** current `build.py` sorts declared targets; Phase 4 must not copy that behavior.
- **Implicit project identity:** never rely on directory name or Compose `name:` fallback.
- **Ambient Compose defaults:** don't let `COMPOSE_REMOVE_ORPHANS` change behavior implicitly.
- **Guessing scope:** one of `--app` / `--environment` alone must error, not infer.
- **Native-Docker-only tests:** Phase 4 should be unit-testable with `RecordingRunner`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Container apply/teardown | Custom Docker orchestration logic | `docker compose up -d` / `docker compose down` | Project runtime contract is Compose CLI |
| Dry-run simulation | Ad hoc fake shell wrappers | `DryRunRunner` / `RecordingRunner` | Already established and testable |
| Scope validation | Custom parser tricks | Existing argparse paired-flag pattern | Already proven in `validate` |
| Project naming | Directory-derived names | `compose_project_name(app, environment)` + `-p` | Keeps deploy and teardown identity stable |
| `.env` loading for runtime | Manual parsing for Compose invocation | Compose `--env-file` | Lets Compose resolve the runtime file directly |

**Key insight:** Phase 4 is mostly about safe target selection and deterministic command construction, not about inventing a new deployment subsystem.

## Common Pitfalls

### Pitfall 1: Ambient orphan-removal behavior
**What goes wrong:** `up` or `down` removes orphans even though Phase 4 says deploy must not use `--remove-orphans`.  
**Why it happens:** Docker Compose source uses `COMPOSE_REMOVE_ORPHANS` as the default when the flag is not explicitly changed.  
**How to avoid:** Override or scrub this env var for actuator-run Compose calls.  
**Warning signs:** Behavior differs between shells/hosts without code changes.

### Pitfall 2: Wrong project identity on teardown
**What goes wrong:** `down` targets the wrong project or fails to match containers created by earlier `up`.  
**Why it happens:** Compose project-name precedence falls back to env vars, top-level `name:`, project directory basename, or current directory if `-p` is omitted.  
**How to avoid:** Always pass the same `-p {compose_project_name(app, environment)}` for both up and down.  
**Warning signs:** Container names don't match expected `app-environment-*` prefix.

### Pitfall 3: Destructive teardown flags
**What goes wrong:** Data or images disappear unexpectedly.  
**Why it happens:** `docker compose down -v` removes named and anonymous volumes; `--rmi` removes images; `--remove-orphans` removes extra containers.  
**How to avoid:** Use plain `down` for Phase 4 unless the requirement explicitly expands scope later.  
**Warning signs:** Teardown affects persistent data, not just running Compose resources.

### Pitfall 4: Losing declaration order
**What goes wrong:** Full-tree operations execute in filesystem/alphabetical order instead of `apps.y[a]ml` order.  
**Why it happens:** Current `discover_host_tree()` and `run_build()` both sort.  
**How to avoid:** Use `load_declared_environments()` output order as the source of truth for batch order.  
**Warning signs:** `immich` runs before `nextcloud` when YAML declared the reverse.

### Pitfall 5: Scoped target exists in build tree but is stale
**What goes wrong:** Operator deploys/tears down a subtree that still exists on disk but is no longer valid for current host declaration.  
**Why it happens:** A build tree can outlive source changes.  
**How to avoid:** For scoped operations, require both build-tree existence and current declaration membership.  
**Warning signs:** Target dir exists under build root but no longer appears in `apps.y[a]ml`.

## Code Examples

### Safe scoped/full-tree CLI guard
```python
if bool(args.app) != bool(args.environment):
    parser.error("--app and --environment must be provided together")
```
Source: current repo `src/unraid_actuator/cli.py`

### Teardown command spec
```python
def compose_down_spec(output_dir, app: str, environment: str) -> CommandSpec:
    project_name = compose_project_name(app, environment)
    return CommandSpec(
        argv=(
            "docker", "compose",
            "-p", project_name,
            "--project-directory", str(output_dir),
            "--env-file", str(output_dir / ".env"),
            "-f", str(output_dir / "docker-compose.yml"),
            "down",
        ),
        cwd=output_dir,
        env={"COMPOSE_REMOVE_ORPHANS": "0"},
        inherit_env=True,
    )
```
Source: Docker Compose official `down` docs + current `runner.py`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Implicit project identity from cwd / file location | Explicit `-p` on every call | Current Docker docs | Prevents mismatched teardown |
| Implicit `.env` and cwd resolution | Explicit `--env-file` and `--project-directory` | Current Docker docs | Makes build-tree execution deterministic |
| Repo-executed `build.py` generation | Phase 3 normalized build tree from `template.yml` / static Compose | Phase 3 project decision | Phase 4 should consume build artifacts only |
| Live-Docker-only testing | Runner-based dry-run and recording tests | Phase 1 | Makes Phase 4 testable without Docker |

**Deprecated/outdated:**
- Deploying from repo source paths directly: outdated for this project; Phase 4 should consume the build tree, not re-derive source state.
- Relying on default Compose project-name resolution: outdated for this safety-sensitive workflow.

## Open Questions

1. **Should full-tree actions reject a marked build root if its target set no longer matches the current declared host set?**
   - What we know: scoped actions must revalidate against current host declaration; full-tree ordering also depends on current declaration.
   - What's unclear: whether product wants to allow "stale but marked" full-tree runs.
   - Recommendation: plan the stricter behavior unless the owner explicitly wants looser semantics.

2. **How aggressively should Compose env be scrubbed?**
   - What we know: `COMPOSE_REMOVE_ORPHANS` can alter behavior; other Compose env vars exist.
   - What's unclear: whether Unraid deployments need inherited `DOCKER_*` / config vars.
   - Recommendation: at minimum force `COMPOSE_REMOVE_ORPHANS=0`; ideally add a small allowlisted env helper if runtime testing confirms it works on target hosts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---:|---|---|
| `docker compose` | Actual DEP-01 / DEP-03 execution | ✗ | — | No runtime fallback; use `RecordingRunner` for tests only |
| `python3` | Implementation / tests | ✓ | 3.14.3 | — |
| `uv` | Repo-standard test execution | ✓ | 0.8.15 | — |
| `pytest` via `uv run` | Unit tests | ✓ | 8.4.2 | Use `uv run pytest ...` instead of broken global `pytest` shim |

**Missing dependencies with no fallback:**
- `docker compose` — blocks real deploy/teardown execution and live integration/UAT in this environment.

**Missing dependencies with fallback:**
- None for runtime; for development tests, `RecordingRunner` avoids needing Docker.

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest 8.4.2 |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/unit/test_deploy_service.py tests/unit/test_deploy_cli.py -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| DEP-01 | full-tree deploy requires marked runtime tree | unit | `uv run pytest tests/unit/test_deploy_service.py::test_deploy_full_requires_marker -q` | ❌ Wave 0 |
| DEP-01 | full-tree deploy follows declaration order and stops on first failure | unit | `uv run pytest tests/unit/test_deploy_service.py::test_deploy_full_is_ordered_and_fail_fast -q` | ❌ Wave 0 |
| DEP-02 | scoped deploy requires both selectors, build-tree existence, and current-host validity | unit | `uv run pytest tests/unit/test_deploy_service.py::test_deploy_scoped_requires_current_host_valid_target -q` | ❌ Wave 0 |
| DEP-03 | teardown full/scoped builds correct `down` specs and is fail-fast for full-tree | unit | `uv run pytest tests/unit/test_teardown_service.py -q` | ❌ Wave 0 |
| DEP-04 | incomplete scope args fail safely in CLI | unit | `uv run pytest tests/unit/test_deploy_cli.py::test_deploy_requires_both_scope_flags -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/test_deploy_service.py tests/unit/test_teardown_service.py tests/unit/test_deploy_cli.py -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_deploy_service.py` — full-tree marker trust, scoped validity, ordered/fail-fast deploy
- [ ] `tests/unit/test_teardown_service.py` — full/scoped teardown command specs and failure handling
- [ ] `tests/unit/test_deploy_cli.py` — `deploy`/`teardown` paired-flag handling and service wiring
- [ ] Optional shared helper for marked build-tree fixtures in `tests/conftest.py`

## Sources

### Primary (HIGH confidence)
- Current repo `src/unraid_actuator/cli.py` — existing paired-scope argparse pattern
- Current repo `src/unraid_actuator/build.py` — current build-tree shape and current alphabetical sort that Phase 4 must avoid
- Current repo `src/unraid_actuator/build_paths.py` — build-root marker contract
- Current repo `src/unraid_actuator/runner.py` — dry-run and recording-runner seam
- Current repo `src/unraid_actuator/schemas.py` — declared-environment loading from `apps.y[a]ml`
- Current repo `src/unraid_actuator/validation_rules.py` — stable project-name helper
- Docker Compose official reference: `https://raw.githubusercontent.com/docker/compose/main/docs/reference/compose_up.md`
- Docker Compose official reference: `https://raw.githubusercontent.com/docker/compose/main/docs/reference/compose_down.md`
- Docker Compose official reference: `https://raw.githubusercontent.com/docker/compose/main/docs/reference/compose.md`
- Docker official docs: `https://raw.githubusercontent.com/docker/docs/main/content/manuals/compose/how-tos/project-name.md`
- Docker official docs: `https://raw.githubusercontent.com/docker/docs/main/content/reference/compose-file/version-and-name.md`
- Docker Compose source: `https://raw.githubusercontent.com/docker/compose/main/cmd/compose/up.go`
- Docker Compose source: `https://raw.githubusercontent.com/docker/compose/main/cmd/compose/down.go`

### Secondary (MEDIUM confidence)
- None needed

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — no new dependency is needed; runtime contract and existing repo patterns are explicit
- Architecture: **HIGH** — based on current code structure plus official Compose CLI docs/source
- Pitfalls: **HIGH** — orphan-removal, project-name precedence, and destructive `down` flags are all directly documented or visible in official source

**Research date:** 2026-04-22  
**Valid until:** 2026-05-22

---

## RESEARCH COMPLETE

**Phase:** 4 - Safe Deploy & Teardown  
**Confidence:** HIGH

### Key Findings
- No new library is needed; Phase 4 should be a thin service layer over the existing runner and Docker Compose CLI.
- Always pass explicit Compose identity: `-p`, `--project-directory`, `--env-file`, `-f`.
- Full-tree actions must derive order from `apps.y[a]ml`, not from filesystem sort or current `run_build()` ordering.
- Scoped actions must validate both build-tree existence and current-host declaration membership.
- `COMPOSE_REMOVE_ORPHANS` is a real safety caveat; planner should scrub/override it so deploy behavior cannot drift.

### File Intended
`/Users/chrisyx511/Documents/Code/unraid-actuator/.planning/phases/04-safe-deploy-teardown/04-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|---|---|---|
| Standard Stack | HIGH | Explicit runtime contract and existing repo patterns |
| Architecture | HIGH | Strong alignment between current codebase and official Compose behavior |
| Pitfalls | HIGH | Based on official docs/source, not guesswork |

### Open Questions
- Whether full-tree should reject stale marked roots that no longer match current declared targets
- Whether Phase 4 should use full env scrubbing or a smaller allowlist around Docker-related vars

### Ready for Planning
