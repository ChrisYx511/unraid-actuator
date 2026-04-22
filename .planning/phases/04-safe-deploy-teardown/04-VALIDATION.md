---
phase: 04
slug: safe-deploy-teardown
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-22
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 via `uv run pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/unit/test_deploy_tree.py tests/unit/test_compose_runtime.py tests/unit/test_deploy_service.py tests/unit/test_teardown_service.py tests/unit/test_deploy_cli.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific command below
- **After every plan wave:** Run `uv run pytest tests/unit/test_deploy_tree.py tests/unit/test_compose_runtime.py tests/unit/test_deploy_service.py tests/unit/test_teardown_service.py tests/unit/test_deploy_cli.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 04-01 | 1 | DEP-01, DEP-02, DEP-03 | unit | `uv run pytest tests/unit/test_deploy_tree.py -q` | ❌ Wave 0 | ⬜ pending |
| 04-01-02 | 04-01 | 1 | DEP-01, DEP-03 | unit | `uv run pytest tests/unit/test_compose_runtime.py -q` | ❌ Wave 0 | ⬜ pending |
| 04-02-01 | 04-02 | 2 | DEP-01, DEP-02 | unit | `uv run pytest tests/unit/test_deploy_service.py -q` | ❌ Wave 0 | ⬜ pending |
| 04-02-02 | 04-02 | 2 | DEP-03 | unit | `uv run pytest tests/unit/test_teardown_service.py -q` | ❌ Wave 0 | ⬜ pending |
| 04-03-01 | 04-03 | 3 | DEP-02, DEP-04 | unit | `uv run pytest tests/unit/test_deploy_cli.py -q` | ❌ Wave 0 | ⬜ pending |
| 04-03-02 | 04-03 | 3 | DEP-03, DEP-04 | unit | `uv run pytest tests/unit/test_deploy_cli.py -q` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_deploy_tree.py` — marker trust, scoped current-host validity, declaration-order selection, and stale full-tree tolerance
- [ ] `tests/unit/test_compose_runtime.py` — exact `docker compose up -d` / `down` command-spec coverage with forced `COMPOSE_REMOVE_ORPHANS=0`
- [ ] `tests/unit/test_deploy_service.py` — fail-fast ordered deploy orchestration and scoped dispatch coverage
- [ ] `tests/unit/test_teardown_service.py` — fail-fast ordered teardown orchestration and scoped dispatch coverage
- [ ] `tests/unit/test_deploy_cli.py` — paired-scope parser rules, build-root dispatch, and error-exit coverage for both `deploy` and `teardown`
- [ ] Optional fixture helper in `tests/conftest.py` for marked runtime-tree builders if setup duplication grows

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real `docker compose up -d` execution from a marked runtime tree uses explicit project identity and does not remove orphans | DEP-01, DEP-02 | Docker Compose is unavailable in this environment | On a Docker-equipped host, run `unraid-actuator deploy --build-root <marked-root>` for a known target, then inspect the resulting containers and the dry-run/recorded command output to confirm `-p`, `--project-directory`, `--env-file`, `-f`, `up -d`, and no `--remove-orphans` |
| Real `docker compose down` from the same marked runtime tree tears down the correct project without destructive extra flags | DEP-03 | Docker Compose is unavailable in this environment | On a Docker-equipped host, run `unraid-actuator teardown --build-root <marked-root>` and confirm the matching project stops while persistent volumes/images remain untouched because no `-v` or `--rmi` flags are used |
| Full-tree fail-fast behavior stops on the first bad target | DEP-01, DEP-03 | Requires an actual Docker host and a deliberately broken target to observe batch stop behavior | Build a marked runtime tree with two targets where the second target has invalid Compose or env data, run full-tree `deploy` and `teardown`, and confirm the batch aborts immediately after the first failing target instead of continuing |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing test files
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
