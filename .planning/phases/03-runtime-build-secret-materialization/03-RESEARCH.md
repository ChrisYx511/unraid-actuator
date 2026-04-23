# Phase 3: Runtime Build & Secret Materialization - Research

**Researched:** 2026-04-22  
**Domain:** Deterministic runtime-tree build, Jinja2 template rendering, EJSON decryption, and `.env` materialization for Docker Compose on Unraid  
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Replace `build.py` support with a declarative `template.yml` mechanism. Phase 3 should not execute repository-provided Python to generate Compose output.
- **D-02:** `template.yml` should declare includes as:
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
- **D-07:** Decrypted secret values belong only in the built `.env` output, not in template rendering inputs.
- **D-08:** When the same key exists in both decrypted secrets and a non-secret `.env` file, the decrypted secret value overrides the `.env` value in the built output.
- **D-09:** A declared app/environment may omit a matching secret block in `secret-env.ejson`; treat that case as an empty secret set rather than a build failure.
- **D-10:** Keep the build output ephemeral and normalized under the actuator-managed runtime-tree contract already implied by the roadmap: each successful environment must emit a normalized `docker-compose.yml`, a merged `.env`, and the build root marker file `.UNRAID_RUNNING_CONFIGURATION`.
- **D-11:** Wherever the actuator accepts YAML-backed configuration files under its contract, it should accept both `.yaml` and `.yml` extensions rather than treating one as canonical-only.

### the agent's Discretion
- Exact internal module split for template loading, Jinja rendering, secret decryption, `.env` parsing/merging, and build-tree writing.
- Exact `strictyaml` schemas and helper DTOs for `template.yml` / `template.yaml` and `values.yml` / `values.yaml`, as long as they enforce the locked rendering rules above.
- Exact error/report formatting for build failures, as long as undefined template values and secret decryption failures surface clearly.
- Exact file-permission and temp-directory helper details, as long as the runtime tree remains ephemeral and safe by default on Unraid.

### Deferred Ideas (OUT OF SCOPE)
- Shared template libraries outside an individual app/environment tree — explicitly deferred by the locked include-path decision.
- Any future alternate secret backend beyond host-root `secret-env.ejson` — already covered by `EXT-02`, not part of Phase 3.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BLD-01 | Operator can build all current host app/environment configurations into `/tmp/unraid-actuator/build` by default | Use stage-then-swap build root under `/tmp/unraid-actuator`, with final path fixed at `/tmp/unraid-actuator/build` |
| BLD-02 | Operator can build into a custom output path only when that path is empty before the build starts | Validate custom target is missing or an empty real directory before any work begins |
| BLD-03 | Operator receives a safe failure when a non-default build output path is non-empty | Reject non-empty custom targets before decryption/rendering; never partially write into them |
| BLD-04 | Operator gets a normalized `docker-compose.yml` for every built environment regardless of whether the source came from a static Compose file or `build.py` | Superseded by locked Phase 3 context: normalize static Compose or declarative `template.yml` source via `docker compose config --no-interpolate --format yaml` |
| BLD-05 | Operator gets a merged `.env` file per built environment that combines decrypted secret values with non-secret `.env` data | Parse `.env` with `python-dotenv`, merge secret map last, serialize deterministically |
| BLD-06 | Operator gets a build failure when required secret decryption cannot complete for the selected host | Use `ejson decrypt` via runner; fail host build before final swap on non-zero exit or malformed decrypted JSON |
| BLD-07 | Operator gets a build marker file named `.UNRAID_RUNNING_CONFIGURATION` at the root of each successful build tree | Write marker into staged tree just before final swap so only successful trees are marked |
</phase_requirements>

## Project Constraints (from copilot-instructions.md)

- Must run within normal Unraid constraints: cron execution, ramfs-heavy temp storage, persistent USB-backed boot media.
- Must remain a Python package consumable by other `uv` projects via `uv_build`.
- YAML must be parsed with `strictyaml`.
- Decrypted secret material must only exist in intentionally generated runtime trees.
- `git` and `docker compose` CLI behavior are part of the runtime contract.
- Command execution needs clear error surfaces, dry-run support, and testable wrappers.

## Summary

Phase 3 should build a normalized runtime tree from two allowed source shapes only: static `docker-compose.y[a]ml` or declarative `template.y[a]ml` plus `values.y[a]ml`. The safest contract is a strict three-step pipeline per environment: classify source, render/normalize Compose without interpolation, then materialize a merged `.env` where decrypted secrets override non-secret values. Do not let secrets into Jinja inputs, Compose interpolation, or logs.

The most important implementation detail is to keep Compose normalization secret-free and deterministic. Docker Compose interpolates environment values by default, so normalization must use `docker compose config --no-interpolate --format yaml` and disable automatic `.env` loading (`COMPOSE_DISABLE_ENV_FILE=1`). Otherwise the same repo can render differently under cron vs interactive shells, or worse, bake secret values into `docker-compose.yml`.

For build-root safety, use a stage-then-swap strategy. Build into a sibling staging directory, and only replace the final output path after all environments succeed and the root marker is present. This gives safe failure semantics for both the default tmp path and custom output paths while preserving the “ephemeral by default” Unraid posture.

**Primary recommendation:** Build a shared source-classification + staged-build pipeline that renders templates with `Jinja2.StrictUndefined`, normalizes Compose with `docker compose config --no-interpolate`, and materializes `.env` separately with secret precedence.

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1.6 (PyPI, 2025-03-05) | Render concatenated template fragments | Official, stable templating engine with `StrictUndefined` |
| python-dotenv | 1.2.2 (PyPI, 2026-03-01) | Parse repo `.env` safely without mutating process env | Avoids hand-rolled dotenv parsing edge cases |
| strictyaml | 1.7.3 (PyPI, 2023-03-10) | Parse `template.y[a]ml` and `values.y[a]ml` contracts | Already project-standard and required by project constraints |
| Docker Compose CLI | current v2 docs | Normalize Compose to canonical YAML | Official runtime authority; expands short syntax consistently |
| EJSON CLI | 1.5.4 (local) | Decrypt `secret-env.ejson` | Existing approved secret backend |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `pathlib` | stdlib | Safe path resolution and tree checks | Enforce include/output path containment |
| Python `json` | stdlib | Parse decrypted EJSON output | Extract host/app/environment secret maps |
| Python `tempfile` / `shutil` | stdlib | Build staging + swap | Safe failure and cleanup behavior |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 | custom string replacement | Rejected: no strict undefined semantics, too easy to get wrong |
| python-dotenv | custom `.env` parser | Rejected: quoting/interpolation/comment rules are deceptively complex |
| `docker compose config` | custom YAML normalization | Rejected: Compose CLI is the runtime authority |
| `build.py` | repo-executed Python | Rejected by locked decision D-01 |
| PyYAML | strictyaml | Rejected by project constraint |

**Installation:**
```bash
uv add "Jinja2>=3.1.6,<4" "python-dotenv>=1.2.2,<2"
```

**Version verification:**
- `Jinja2` → 3.1.6, published 2025-03-05
- `python-dotenv` → 1.2.2, published 2026-03-01
- `strictyaml` → 1.7.3, published 2023-03-10

## Architecture Patterns

### Recommended Project Structure
```text
src/unraid_actuator/
├── build.py                 # run_build orchestration
├── build_models.py          # BuildRequest, BuildResult, BuildTarget, SourceKind
├── build_paths.py           # output-root validation, staging, marker handling
├── template_render.py       # template descriptor parsing + include resolution + Jinja render
├── env_materialize.py       # .env parse/merge/serialize
├── secrets.py               # ejson decrypt adapter + decrypted JSON extraction
├── compose_build.py         # normalize static/rendered Compose through docker compose
├── discovery.py             # shared source classification updated to template descriptors
└── schemas.py               # strict schemas for template/values YAML
```

### Pattern 1: Shared Source Classification
**What:** Define exactly one source kind per environment: static compose or template descriptor.  
**When to use:** discovery, validation, and build.  
**Example:**
```python
# Source: repo constraints + existing discovery.py pattern
compose_files = tuple(
    candidate for candidate in (
        env_dir / "docker-compose.yml",
        env_dir / "docker-compose.yaml",
    ) if candidate.is_file()
)
template_files = tuple(
    candidate for candidate in (
        env_dir / "template.yml",
        env_dir / "template.yaml",
    ) if candidate.is_file()
)
if len(compose_files) == 1 and not template_files:
    return SourceKind.COMPOSE
if len(template_files) == 1 and not compose_files:
    return SourceKind.TEMPLATE
return SourceKind.AMBIGUOUS_OR_MISSING
```

### Pattern 2: Descriptor-First Template Rendering
**What:** Parse `template.y[a]ml`, resolve each include path against the environment root, concatenate in declared order, then render one Jinja template with values only.  
**When to use:** template-driven environments.  
**Example:**
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
from pathlib import Path
from jinja2 import Environment, StrictUndefined

def render_template(env_root: Path, includes: list[str], values: dict) -> str:
    root = env_root.resolve()
    fragments: list[str] = []
    for rel in includes:
        candidate = (env_root / rel).resolve(strict=True)
        if not candidate.is_relative_to(root):
            raise ValueError(f"template include escapes environment root: {rel}")
        fragments.append(candidate.read_text(encoding="utf-8"))
    combined = "\n".join(fragments)
    jinja = Environment(undefined=StrictUndefined, autoescape=False)
    return jinja.from_string(combined).render(**values)
```

### Pattern 3: Secret-Free Compose Normalization
**What:** Normalize Compose through Docker Compose without interpolation and with default `.env` loading disabled.  
**When to use:** both static compose and rendered template output.  
**Example:**
```python
# Source: https://docs.docker.com/reference/cli/docker/compose/config/
# Source: https://docs.docker.com/compose/how-tos/environment-variables/envvars/
from unraid_actuator.runner import CommandSpec

spec = CommandSpec(
    argv=(
        "docker", "compose",
        "-p", project_name,
        "--project-directory", str(source_env_dir),
        "-f", "-",
        "config",
        "--no-interpolate",
        "--format", "yaml",
    ),
    cwd=source_env_dir,
    env={"COMPOSE_DISABLE_ENV_FILE": "1"},
    stdin_text=rendered_compose_text,
    inherit_env=False,
)
```

### Pattern 4: Stage Then Swap
**What:** Build a complete tree in a staging directory; write marker only on success; replace final output path last.  
**When to use:** every build command.  
**Example:**
```python
# Source: project requirement BLD-01..07
stage_root = create_stage_dir(parent=final_root.parent)
build_every_environment(stage_root)
(stage_root / ".UNRAID_RUNNING_CONFIGURATION").write_text("", encoding="utf-8")
swap_stage_into_place(stage_root, final_root)
```

### Anti-Patterns to Avoid
- **Rendering templates with process environment:** violates D-05 and causes nondeterminism.
- **Running `docker compose config` without `--no-interpolate`:** can substitute env values and leak secrets into normalized Compose.
- **Building directly in the final directory:** creates partial trees on failure.
- **Using Jinja file includes as the include mechanism:** bypasses locked descriptor rules.
- **Keeping `build.py` logic in discovery/build code paths:** stale requirement wording must not drive implementation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template rendering | ad hoc string substitution | Jinja2 `StrictUndefined` | Hard failures for missing values; standard syntax |
| `.env` parsing | `line.split("=", 1)` parser | `python-dotenv` | Comments, quoting, empty values, multiline values |
| Compose normalization | custom YAML post-processor | `docker compose config --no-interpolate --format yaml` | Compose CLI is authoritative |
| Secret decryption | custom crypto/parser | `ejson decrypt` | Existing supported backend |
| YAML contract parsing | permissive loader | `strictyaml` | Deterministic schema enforcement |

**Key insight:** The risky parts here are not “writing files”; they are interpolation, path containment, dotenv syntax, and partial-failure behavior.

## Common Pitfalls

### Pitfall 1: Default Compose interpolation leaks nondeterminism
**What goes wrong:** normalized output changes based on shell env or repo `.env`.  
**Why it happens:** `docker compose config` interpolates env by default and Compose auto-loads `.env`.  
**How to avoid:** always use `--no-interpolate`, `inherit_env=False`, and `COMPOSE_DISABLE_ENV_FILE=1` during normalization.  
**Warning signs:** same input renders differently under cron vs terminal.

### Pitfall 2: Bare dotenv keys silently parse as `None`
**What goes wrong:** merged `.env` contains ambiguous or missing values.  
**Why it happens:** `python-dotenv` treats `FOO` differently from `FOO=`.  
**How to avoid:** fail build if parsed repo `.env` yields any `None` values.  
**Warning signs:** parsed config contains `None` for a key.

### Pitfall 3: Include path escape via `..` or symlink traversal
**What goes wrong:** template fragments can read outside the environment tree.  
**Why it happens:** checking only raw relative strings is insufficient.  
**How to avoid:** resolve each candidate path with `Path.resolve(strict=True)` and require it to remain under the environment root.  
**Warning signs:** includes use `../`, absolute paths, or symlinked directories.

### Pitfall 4: Partial build trees on secret or render failure
**What goes wrong:** final output path contains half-built environments.  
**Why it happens:** build writes directly into final target.  
**How to avoid:** stage in sibling temp dir and swap only after all environments succeed.  
**Warning signs:** custom output path contains some apps after a failed run.

### Pitfall 5: Validation/build source-shape drift
**What goes wrong:** validation accepts one source contract and build expects another.  
**Why it happens:** Phase 2 assumptions still reference `build.py`.  
**How to avoid:** move source classification into shared discovery/schema code now: compose XOR template descriptor, both `.yaml` and `.yml`.  
**Warning signs:** duplicated source-kind logic in validation and build modules.

## Code Examples

Verified patterns from official/current sources:

### Strict undefined Jinja rendering
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
from jinja2 import Environment, StrictUndefined

env = Environment(undefined=StrictUndefined, autoescape=False)
text = env.from_string("image: {{ image }}\n").render(image="nginx:latest")
```

### Parse `.env` without mutating process environment
```python
# Source: https://github.com/theskumar/python-dotenv
from dotenv import dotenv_values

base_env = dotenv_values(".env")  # returns dict, does not update os.environ
```

### Compose canonicalization without interpolation
```bash
# Source: https://docs.docker.com/reference/cli/docker/compose/config/
docker compose -p app-prod -f - config --no-interpolate --format yaml
```

### EJSON decrypt to stdout
```bash
# Source: local ejson help + https://github.com/Shopify/ejson
ejson decrypt secret-env.ejson
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| repo-executed `build.py` | declarative `template.y[a]ml` + fragments + `values.y[a]ml` | user decision in Phase 3 context, 2026-04-22 | removes arbitrary repo code execution from build path |
| plain `docker compose config` | `docker compose config --no-interpolate --format yaml` with `.env` auto-load disabled | current research | keeps secrets out of normalized compose and reduces env drift |
| ad hoc dotenv parsing | `python-dotenv` parsing + deterministic merge/write | current research | avoids parser bugs and ambiguity |

**Deprecated/outdated:**
- `build.py` as a Phase 3 source kind: superseded by locked decision D-01.
- Any recommendation that templates can consume decrypted secrets: superseded by D-05 and D-07.

## Open Questions

1. **Should non-project `env_file:` references inside Compose be supported in v1?**
   - What we know: Phase scope explicitly requires merged project `.env`; extra `env_file:` contracts are not defined.
   - What's unclear: whether source Compose files may legally depend on additional env files.
   - Recommendation: keep v1 narrow—support only the project-root `.env` merge contract; treat additional env-file behaviors as unsupported unless explicitly added.

2. **Should EJSON keydir become explicit actuator config?**
   - What we know: EJSON defaults to `/opt/ejson/keys` and supports `EJSON_KEYDIR` / `--keydir`.
   - What's unclear: whether operators need first-class config or env-based override is enough.
   - Recommendation: for this phase, rely on default EJSON behavior plus adapter injection for tests; add explicit config only if an operator workflow requires it.

3. **What should `build --dry-run` promise?**
   - What we know: project architecture requires dry-run-friendly seams.
   - What's unclear: whether build dry-run must avoid all writes and decryption, or may stage non-secret planning only.
   - Recommendation: plan pure “build plan” DTOs and fake-runner tests now; if CLI dry-run semantics are not already locked, keep the first implementation conservative and secret-free.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | package runtime | ✓ | 3.14.3 | — |
| uv | dependency/test execution | ✓ | 0.8.15 | — |
| pytest | test execution | ✓ via `uv run pytest` | 8.4.2 | use `uv run pytest`, not bare `pytest` |
| EJSON CLI | secret decryption | ✓ | 1.5.4 | — |
| Docker Compose CLI | Compose normalization | ✗ | — | none |
| Jinja2 | template rendering | ✗ in repo env | — | add project dependency |
| python-dotenv | `.env` parsing | ✗ in repo env | — | add project dependency |

**Missing dependencies with no fallback:**
- Docker Compose CLI for live normalization/integration testing

**Missing dependencies with fallback:**
- Bare `pytest` executable is broken locally; use `uv run pytest`
- Jinja2 and python-dotenv are not installed yet; add them to project dependencies

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/unit -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BLD-01 | default build root is `/tmp/unraid-actuator/build` | unit | `uv run pytest tests/unit/test_build_service.py::test_builds_all_to_default_tmp_path -q` | ❌ Wave 0 |
| BLD-02 | custom output path allowed only when empty | unit | `uv run pytest tests/unit/test_build_paths.py::test_custom_output_path_must_be_empty_or_missing -q` | ❌ Wave 0 |
| BLD-03 | non-empty custom path fails safely without partial writes | unit | `uv run pytest tests/unit/test_build_paths.py::test_non_default_non_empty_path_fails_before_build -q` | ❌ Wave 0 |
| BLD-04 | static compose and template source both normalize to `docker-compose.yml` | unit + manual integration | `uv run pytest tests/unit/test_compose_build.py::test_normalizes_static_and_template_sources -q` | ❌ Wave 0 |
| BLD-05 | merged `.env` gives secret precedence | unit | `uv run pytest tests/unit/test_env_materialize.py::test_secret_values_override_non_secret_env -q` | ❌ Wave 0 |
| BLD-06 | ejson failure aborts build safely | unit | `uv run pytest tests/unit/test_secrets.py::test_decrypt_failure_aborts_build -q` | ❌ Wave 0 |
| BLD-07 | marker file written only for successful trees | unit | `uv run pytest tests/unit/test_build_service.py::test_successful_build_writes_marker_file -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** unit suite green, plus one manual/integration proof on a machine with Docker Compose and EJSON

### Wave 0 Gaps
- [ ] `tests/unit/test_build_service.py` — orchestration, staging, marker, default root
- [ ] `tests/unit/test_build_paths.py` — custom-path validation and safe failure
- [ ] `tests/unit/test_template_render.py` — descriptor parse, include ordering, path containment, strict undefined
- [ ] `tests/unit/test_env_materialize.py` — dotenv parsing, merge precedence, deterministic serialization
- [ ] `tests/unit/test_secrets.py` — ejson command construction and decrypted JSON extraction
- [ ] `tests/unit/test_compose_build.py` — static/template normalization command specs
- [ ] Dependency install: `uv add "Jinja2>=3.1.6,<4" "python-dotenv>=1.2.2,<2"`

## Sources

### Primary (HIGH confidence)
- https://jinja.palletsprojects.com/en/stable/api/ — `StrictUndefined`, template environment behavior, loader behavior
- https://docs.docker.com/reference/cli/docker/compose/config/ — canonical Compose rendering, `--no-interpolate`, `--format yaml`
- https://docs.docker.com/reference/cli/docker/compose/ — `-f -` stdin behavior, `--project-directory`
- https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/ — `.env` syntax and precedence
- https://docs.docker.com/compose/how-tos/environment-variables/envvars/ — `COMPOSE_DISABLE_ENV_FILE`
- PyPI JSON API for `Jinja2`, `python-dotenv`, `strictyaml` — current package versions and publish dates
- local `ejson help` / `ejson help decrypt` — installed CLI behavior and options

### Secondary (MEDIUM confidence)
- https://github.com/theskumar/python-dotenv — README for `dotenv_values`; source confirms `interpolate` support
- https://github.com/Shopify/ejson — README for keydir behavior, stdout decrypt behavior, `_public_key` rules
- https://docs.python.org/3/library/pathlib.html — `Path.resolve()` and `is_relative_to()` for containment checks

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified from PyPI and behavior checked against official docs/current source
- Architecture: MEDIUM-HIGH — key contracts are clear, but exact module split and dry-run UX remain discretionary
- Pitfalls: HIGH — directly supported by Docker Compose behavior, EJSON behavior, and project constraints

**Research date:** 2026-04-22  
**Valid until:** 2026-05-22
