---
phase: 03
slug: runtime-build-secret-materialization
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-22
---

# Phase 03 — Validation Strategy

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
| 03-01-01 | 03-01 | 1 | BLD-04 | unit | `uv run pytest tests/unit/test_discovery.py tests/unit/test_schemas.py -q` | updates existing | ⬜ pending |
| 03-01-02 | 03-01 | 1 | BLD-02, BLD-03 | unit | `uv run pytest tests/unit/test_build_paths.py -q` | task creates | ⬜ pending |
| 03-02-01 | 03-02 | 2 | BLD-04 | unit | `uv run pytest tests/unit/test_template_render.py -q` | task creates | ⬜ pending |
| 03-02-02 | 03-02 | 2 | BLD-04 | unit | `uv run pytest tests/unit/test_compose_build.py -q` | task creates | ⬜ pending |
| 03-03-01 | 03-03 | 2 | BLD-06 | unit | `uv run pytest tests/unit/test_secrets.py -q` | task creates | ⬜ pending |
| 03-03-02 | 03-03 | 2 | BLD-05 | unit | `uv run pytest tests/unit/test_env_materialize.py -q` | task creates | ⬜ pending |
| 03-04-01 | 03-04 | 3 | BLD-01, BLD-02, BLD-03, BLD-05, BLD-06, BLD-07 | unit | `uv run pytest tests/unit/test_build_service.py -q` | task creates | ⬜ pending |
| 03-05-01 | 03-05 | 4 | BLD-04 | unit | `uv run pytest tests/unit/test_compose_validation.py tests/unit/test_validate_service.py -q` | updates existing | ⬜ pending |
| 03-05-02 | 03-05 | 4 | BLD-01, BLD-05, BLD-07 | unit | `uv run pytest tests/unit/test_build_cli.py -q` | task creates | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_build_paths.py` — default/custom output-root validation and safe-failure coverage
- [ ] `tests/unit/test_template_render.py` — descriptor parsing, include ordering, containment, and strict undefined coverage
- [ ] `tests/unit/test_env_materialize.py` — dotenv parsing, merge precedence, and deterministic serialization coverage
- [ ] `tests/unit/test_secrets.py` — ejson decrypt command construction and decrypted JSON extraction coverage
- [ ] `tests/unit/test_compose_build.py` — static/template normalization command-spec coverage
- [ ] `tests/unit/test_build_service.py` — staged build orchestration, marker, and swap coverage
- [ ] `tests/unit/test_build_cli.py` — CLI argument and exit behavior coverage
- [ ] Dependency install: `uv add "Jinja2>=3.1.6,<4" "python-dotenv>=1.2.2,<2"`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real `docker compose config --no-interpolate --format yaml` compatibility for both static and template sources | BLD-04 | Docker Compose CLI is not installed in this planning environment | On a Docker-equipped host, run `unraid-actuator build` against one static compose environment and one template-driven environment; confirm both emit normalized `docker-compose.yml` files without interpolated secret values |
| Real EJSON decrypt compatibility on the target host | BLD-06 | Secret handling depends on installed EJSON keys/runtime outside this environment | On a host with EJSON configured, copy the host key material into `/opt/ejson/keys`, run `unraid-actuator build`, and confirm successful `.env` generation for a known secret-bearing environment |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
