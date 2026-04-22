# Stack Research

**Domain:** Git-driven Docker Compose reconciler/actuator CLI for a single Unraid host
**Researched:** 2026-04-22
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Core implementation language | Strong stdlib for subprocess, pathlib, logging, tempfile, and dataclasses; good fit for a cron-driven systems utility. The current scaffold uses `>=3.13`, but relaxing to `3.12+` is likely friendlier for Unraid adoption. |
| `uv_build` | current `uv` backend | Package build backend | Matches the requirement that the project be importable by other `uv` projects and built with `uv build`; keeps packaging aligned with Astral tooling. |
| `strictyaml` | current stable | Parsing and validating `apps.yaml` and actuator config files | Schema-driven parsing, duplicate-key protection, and readable errors with line numbers are better suited than permissive YAML loaders. |
| Docker Compose CLI | Compose v2 | Compose validation and apply engine | `docker compose config -q` is the authoritative validation path, and `docker compose up/down` are the real runtime contract on Unraid. |
| Git CLI | modern git with fetch/ff-only support | Source synchronization and commit tracking | Reconcile logic depends on exact branch/ref behavior; shelling out to git avoids reimplementing low-level Git semantics. |
| EJSON CLI | current stable | Secret decryption at build time | The project already assumes `secret-env.ejson`; using the supported CLI preserves the expected key lookup and decryption behavior. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.x | Unit and integration testing | Use for domain rules, planner logic, adapter contracts, and CLI behavior with fixture repos. |
| `coverage[toml]` | 7.x | Coverage measurement | Use to enforce good safety-net coverage around validation, build, and reconcile behavior. |
| `typing-extensions` | latest if needed | Typing backports | Only if Python baseline needs newer typing helpers than the minimum runtime provides. |
| `python-json-logger` | current stable | Structured log formatting | Use if plain stdlib logging is not enough for log file analysis and syslog correlation. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `uv` | Dependency management and build frontend | Official `uv build` flow depends on a real build backend declared in `[build-system]`. |
| `pytest` | Test runner | Should support fake runners and fixture repositories without requiring Docker during most tests. |
| `ruff` | Linting/formatting | Good low-friction fit for a small Python package, though not required by the project spec. |

## Installation

```bash
# Core Python dependencies
uv add strictyaml

# Testing
uv add --dev pytest coverage[toml]

# Optional structured logging
uv add python-json-logger
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `strictyaml` | `PyYAML` / `ruamel.yaml` | Only if round-tripping or broad YAML compatibility becomes more important than strict validation. For this project, strictness is the point. |
| Git CLI via subprocess | GitPython | Use GitPython only if you need deep object-model access. For branch/commit/ff-only workflows, CLI calls are simpler and closer to operator expectations. |
| Docker Compose CLI | Docker SDK / Compose wrappers | Use SDKs only if the runtime contract stops being Compose CLI based. Right now the deployment surface is explicitly `docker compose`. |
| stdlib `argparse` or a very thin CLI layer | heavy CLI frameworks | Use a richer CLI framework only if ergonomics or shell completion materially improve operator experience without complicating tests. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| permissive YAML parsing | Makes ambiguous configs and duplicate keys easier to miss | `strictyaml` schemas |
| deploying directly from the mutable checkout | Increases risk of secret persistence, drift, and partial state updates | immutable candidate/build tree in `/tmp` or another tmpfs path |
| directory-derived Compose project identity | Temp paths change names and can create duplicate stacks | explicit deterministic project naming via `-p` or `COMPOSE_PROJECT_NAME` |
| Docker API abstractions for core lifecycle | Can drift from how operators debug the system on Unraid | centralized CLI adapters over `docker compose` |

## Stack Patterns by Variant

**If operator trust in `build.py` is high:**
- Support dynamic Compose generation through a dedicated subprocess adapter.
- Record commit SHA and script path/hash in logs for auditability.

**If operator trust in `build.py` is low:**
- Allow a config switch to disable dynamic builds entirely.
- Restrict v1 usage to static `docker-compose.y[a]ml` sources.

**If custom build output path is used:**
- Require the directory to be empty before writing.
- Strongly recommend tmpfs/ramfs-backed paths because merged `.env` files contain plaintext secrets.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `uv build` | a declared `[build-system]` backend such as `uv_build` | `uv` is the build frontend; artifact details come from the backend configuration. |
| Docker Compose v2 | explicit project naming and `config -q` validation | Needed for deterministic project identity and final rendered config checks. |
| `strictyaml` | Python package schema definitions | Best used with explicit schemas for `apps.yaml` and actuator config files. |

## Sources

- https://docs.astral.sh/uv/concepts/projects/build/ — verified `uv build` as frontend behavior and build backend requirement
- https://hitchdev.com/strictyaml/ — verified schema-driven parsing, duplicate-key safety, and error behavior
- https://docs.docker.com/reference/cli/docker/compose/config/ — verified `docker compose config` validation behavior
- https://docs.docker.com/compose/how-tos/project-name/ — verified explicit project naming precedence and constraints
- https://github.com/Shopify/ejson — verified EJSON workflow and decryption model

---
*Stack research for: Git-driven Docker Compose reconciler/actuator CLI for a single Unraid host*
*Researched: 2026-04-22*
