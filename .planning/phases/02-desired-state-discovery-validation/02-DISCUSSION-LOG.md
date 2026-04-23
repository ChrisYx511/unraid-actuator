# Phase 2: Desired-State Discovery & Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 02-desired-state-discovery-validation
**Areas discussed:** Secret handling during validation, Compose project naming, Validation outcomes, Validation report style

## Secret handling during validation

| Option | Description | Selected |
|--------|-------------|----------|
| Secret-free structural validation | Do not decrypt secrets in Phase 2; validate structure and only what can be checked without secret use | |
| Secret-free but strict | Do not decrypt secrets, but fail declared configs that cannot render without them | |
| Full secret-backed validation | Allow secret decryption during validate for full render fidelity | ✓ (initial pick, then refined) |

**User's choice:** Initial answer favored full validation, then clarified the actual desired rule: *validate `secret-env.ejson` format separately and do not decrypt secrets during Phase 2*.

**Follow-up confirmation:** Phase 2 should avoid decrypting secrets entirely and leave secret use to build. Confirmed.

## Compose project naming

| Option | Description | Selected |
|--------|-------------|----------|
| `{hostname}-{app}-{environment}` normalized | Include hostname in project names | |
| `{app}-{environment}` normalized | Use app/environment only | ✓ |
| Another deterministic naming rule | Different fixed scheme | |

**User's choice:** `{app}-{environment}` normalized.

**Follow-up:** Unsafe or ambiguous naming inputs should fail validation rather than be silently normalized. Confirmed.

## Validation outcomes

| Option | Description | Selected |
|--------|-------------|----------|
| Exit 0 and report warnings | Warnings-only runs stay green | ✓ |
| Exit non-zero even for warnings-only runs | Treat warnings as failure | |

**User's choice:** Exit 0 and report warnings when only undeclared invalid app/environments are found.

| Option | Description | Selected |
|--------|-------------|----------|
| Collect all hard errors, then fail | Show full declared broken state in one run | ✓ |
| Stop at the first hard error | Fail fast | |

**User's choice:** Collect all hard errors before failing.

## Validation report style

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped human-readable report with errors, warnings, and final counts | Operator-facing summary format | ✓ |
| Simple one-line-per-issue stream with no summary | Minimal stream output | |

**User's choice:** Grouped human-readable report with errors, warnings, and final counts.

## the agent's Discretion

- Internal validation module boundaries
- Exact schemas and DTO shapes
- Exact command-wrapping helpers and report formatting mechanics

## Deferred Ideas

None.
