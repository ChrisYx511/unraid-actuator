---
phase: 02
slug: desired-state-discovery-validation
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-22
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 via `uv run pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/unit -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 02-01 | 1 | VAL-07 | unit | `uv run pytest tests/unit/test_validation_models.py -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 02-01 | 1 | VAL-07 | unit | `uv run pytest tests/unit/test_schemas.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02-02 | 2 | VAL-03, VAL-04, VAL-05, VAL-08 | unit | `uv run pytest tests/unit/test_discovery.py tests/unit/test_validation_rules.py -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02-02 | 2 | VAL-03, VAL-04, VAL-05, VAL-08 | unit | `uv run pytest tests/unit/test_discovery.py tests/unit/test_validation_rules.py -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 02-03 | 2 | VAL-06 | unit | `uv run pytest tests/unit/test_runner.py tests/unit/test_compose_validation.py -q` | ❌ W0 | ⬜ pending |
| 02-03-02 | 02-03 | 2 | VAL-06 | unit | `uv run pytest tests/unit/test_report_renderer.py -q` | ❌ W0 | ⬜ pending |
| 02-04-01 | 02-04 | 3 | VAL-01, VAL-02, VAL-07 | unit | `uv run pytest tests/unit/test_validate_service.py -q` | ❌ W0 | ⬜ pending |
| 02-04-02 | 02-04 | 3 | VAL-01, VAL-02, VAL-07 | unit | `uv run pytest tests/unit/test_validate_cli.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_validation_models.py` — verification stubs for shared validation DTOs
- [ ] `tests/unit/test_schemas.py` — strict `apps.yaml` and `secret-env.ejson` structural checks
- [ ] `tests/unit/test_discovery.py` — filesystem discovery and source XOR coverage
- [ ] `tests/unit/test_validation_rules.py` — declared-vs-undeclared severity and naming collision coverage
- [ ] `tests/unit/test_compose_validation.py` — static Compose and stdin-fed dynamic validation coverage
- [ ] `tests/unit/test_report_renderer.py` — grouped operator-facing report coverage
- [ ] `tests/unit/test_validate_service.py` — end-to-end validation orchestration coverage
- [ ] `tests/unit/test_validate_cli.py` — CLI scope, exit-code, and schema-error coverage

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real `docker compose config` compatibility on a target host | VAL-06 | Docker Compose CLI is not installed in this planning environment | Run `unraid-actuator validate` on an Unraid or Docker-equipped host against one static and one `build.py` environment and confirm grouped output plus exit behavior |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
