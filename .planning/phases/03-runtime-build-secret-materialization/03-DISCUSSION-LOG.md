# Phase 3: Runtime Build & Secret Materialization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 03-runtime-build-secret-materialization
**Areas discussed:** Dynamic Compose generation model, template rendering inputs, include-path scope, merged `.env` precedence, missing secret entries behavior

## Dynamic Compose generation model

| Option | Description | Selected |
|--------|-------------|----------|
| Separate-process `build.py` with minimal environment | Keep repo-executed Python but tighten trust boundaries | |
| Separate-process `build.py` with inherited environment | Keep executable Python with broader environment access | |
| Declarative `template.yml` + included Jinja templates + `values.yaml` | Replace executable repo code with data-driven rendering | ✓ |

**User's choice:** Replace `build.py` with declarative `template.yml` rendering to avoid executable code in the infrastructure definition repository.

## Template rendering inputs

| Option | Description | Selected |
|--------|-------------|----------|
| `values.yaml` only | Non-secret declarative rendering input | ✓ |
| `values.yaml` plus decrypted secrets | Allow secrets into rendered Compose text | |
| `values.yaml`, decrypted secrets, and process environment | Broad implicit rendering context | |

**User's choice:** Templates should render from `values.yaml` only. Decrypted secrets should stay out of Jinja and flow only into the built `.env`.

**Follow-up confirmation:** Undefined or missing Jinja values should hard-fail the build rather than render partially. Confirmed from the user's stated requirement.

## Include-path scope

| Option | Description | Selected |
|--------|-------------|----------|
| Same app/environment tree only | Includes stay within the current environment subtree | ✓ |
| Any relative path under the current host directory | Allow cross-environment sharing within a host | |
| Any relative path inside the repository | Allow repo-wide shared template fragments | |

**User's choice:** Restrict template includes to files inside the same app/environment directory tree.

**Follow-up confirmation:** YAML-backed actuator inputs should accept both `.yaml` and `.yml` extensions wherever that file type is supported.

## Merged `.env` precedence

| Option | Description | Selected |
|--------|-------------|----------|
| Decrypted secret overrides `.env` | Secret values win when duplicate keys exist | ✓ |
| `.env` overrides decrypted secret | Checked-in non-secret value can replace secret | |
| Duplicate keys are an error | Require fully disjoint key sets | |

**User's choice:** Decrypted secret values override `.env` values in the built output.

## Missing secret entries behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Treat missing secret block as empty | Declared environment may have no secrets | ✓ |
| Require every declared environment to have a secret block | Missing secret entry is a build error | |
| Allow missing secret block only when `.env` is also absent | Secret presence tied to plain env-file presence | |

**User's choice:** Missing secret entries are allowed and should be treated as an empty secret set.

## the agent's Discretion

- Internal module boundaries for rendering, parsing, and build orchestration
- Exact `strictyaml` schemas for `template.yml` and `values.yaml`
- Exact failure-message formatting and dry-run internals

## Deferred Ideas

- Shared template fragments outside the current environment tree
- Any future return to repo-executed dynamic generation
