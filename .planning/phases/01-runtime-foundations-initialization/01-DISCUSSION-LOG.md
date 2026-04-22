# Phase 1: Runtime Foundations & Initialization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 01-Runtime Foundations & Initialization
**Areas discussed:** Python compatibility target for Unraid, CLI framework and command style, persisted config contents, public dry-run support

---

## Python compatibility target for Unraid

| Option | Description | Selected |
|--------|-------------|----------|
| Python 3.12+ | Broaden compatibility while keeping modern typing/features | |
| Python 3.11+ | Maximize compatibility further | |
| Keep Python 3.13+ | Preserve current scaffold baseline and avoid broadening scope in Phase 1 | ✓ |

**User's choice:** Keep Python 3.13+
**Notes:** This intentionally keeps the current scaffold requirement instead of widening support during the foundation phase.

---

## CLI framework and command style

| Option | Description | Selected |
|--------|-------------|----------|
| Thin stdlib argparse subcommands | Minimal-dependency CLI with explicit subcommands and easy testing | ✓ |
| Typer-based CLI | Richer ergonomics and annotations via third-party dependency | |
| Click-based CLI | Explicit command objects with a mature CLI ecosystem | |

**User's choice:** Thin stdlib argparse subcommands
**Notes:** The Phase 1 CLI should stay lightweight and cron/admin-tool friendly.

---

## What exactly gets persisted in /tmp/actuator-cfg.yml

| Option | Description | Selected |
|--------|-------------|----------|
| Single active config with repo URL, deploy branch, hostname, and managed source path | Minimal but complete active runtime contract | ✓ |
| Only deploy branch, hostname, and managed source path | Strictly match the original minimum field list | |
| Richer metadata including timestamps and init history | Start with a more stateful config record | |

**User's choice:** Single active config with repo URL, deploy branch, hostname, and managed source path
**Notes:** Repo URL is included even though it was not part of the minimum original list, so later commands and diagnostics have the full active source definition available.

---

## How public dry-run support should be in v1

| Option | Description | Selected |
|--------|-------------|----------|
| Add a public `--dry-run` path now and make the shared runner power future commands too | Establish the user-facing contract and reusable architecture in Phase 1 | ✓ |
| Keep dry-run internal for tests in Phase 1 and expose it publicly later | Delay operator-facing dry-run behavior | |
| Expose dry-run only for future mutating commands, not `init` yet | Keep Phase 1 more internal | |

**User's choice:** Add a public `--dry-run` path now and make the shared runner power future commands too
**Notes:** Dry-run is part of the public CLI contract from the foundation phase onward.

---

## the agent's Discretion

- Exact internal package/module boundaries under `src/unraid_actuator/`
- Exact runner protocol and DTO naming
- Exact helper layout for errors and logging in the foundation layer

## Deferred Ideas

- Richer config metadata beyond the active single-config contract
- Heavier CLI frameworks
- Broader Python compatibility targets
