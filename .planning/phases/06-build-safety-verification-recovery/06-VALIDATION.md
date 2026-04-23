---
phase: 06
slug: build-safety-verification-recovery
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-22
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for build-safety gap closure and audit recovery.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run pytest` |
| **Quick run command** | `uv run pytest tests/unit/test_build_service.py tests/unit/test_build_cli.py tests/unit/test_validate_service.py -q` |
| **Audit recovery command** | `uv run pytest tests/unit/test_build_paths.py tests/unit/test_template_render.py tests/unit/test_compose_build.py tests/unit/test_secrets.py tests/unit/test_env_materialize.py tests/unit/test_build_service.py tests/unit/test_compose_validation.py tests/unit/test_validate_service.py tests/unit/test_build_cli.py -q` |
| **Packaging sanity** | `uv build` |
| **Estimated runtime** | ~10 seconds for targeted tests; longer for `uv build` |

---

## Sampling Rate

- **After each 06-01 task:** Run the quick build-safety regression command.
- **After 06-01 completion:** Re-run the quick regression command before creating summary evidence.
- **After 06-02 completion:** Run the audit recovery command and `uv build`.
- **Before `/gsd-verify-work`:** Both automated command sets must be green.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 06-01 | 1 | BLD-01, BLD-05, BLD-06, BLD-07 | unit | `uv run pytest tests/unit/test_build_service.py -q` | updates existing | ⬜ pending |
| 06-01-02 | 06-01 | 1 | BLD-01..BLD-07 | unit | `uv run pytest tests/unit/test_build_cli.py -q` | updates existing | ⬜ pending |
| 06-02-01 | 06-02 | 2 | BLD-01, BLD-02, BLD-03, BLD-04, BLD-05, BLD-06 | artifact | `uv run python -c "from pathlib import Path; files=[Path('.planning/phases/03-runtime-build-secret-materialization/03-01-SUMMARY.md'),Path('.planning/phases/03-runtime-build-secret-materialization/03-02-SUMMARY.md'),Path('.planning/phases/03-runtime-build-secret-materialization/03-03-SUMMARY.md')]; [(_ for _ in ()).throw(AssertionError(str(p))) for p in files if not p.exists()]; print('ok')"` | task creates | ⬜ pending |
| 06-02-02 | 06-02 | 2 | BLD-01..BLD-07 | artifact | `uv run python -c "from pathlib import Path; p=Path('.planning/phases/03-runtime-build-secret-materialization/03-VERIFICATION.md'); assert p.exists(); text=p.read_text(); [(_ for _ in ()).throw(AssertionError(req)) for req in ['BLD-01','BLD-02','BLD-03','BLD-04','BLD-05','BLD-06','BLD-07'] if req not in text]; print('ok')"` | task creates | ⬜ pending |
| 06-02-03 | 06-02 | 2 | BLD-04 | artifact | `uv run python -c "from pathlib import Path; text='\\n'.join(Path(p).read_text() for p in ['.planning/PROJECT.md','.planning/ROADMAP.md','.planning/REQUIREMENTS.md','.planning/v1.0-MILESTONE-AUDIT.md']); assert 'template' in text and 'values' in text; print('ok')"` | updates existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Manual Scope Exclusions

These are intentionally **not** part of Phase 6 execution:

| Excluded Scope | Why Excluded | Where Tracked |
|----------------|--------------|---------------|
| Real Docker-host validation/build/deploy/UAT runs | D-01 requires in-repo closure only; host-only checks remain out of scope for this phase | Existing non-blocking host checks in earlier verification reports |
| Live EJSON/decryption verification on a host | Host-only and not required for Phase 6 gap closure planning | Phase 3/Phase 5 manual follow-up guidance |
| Git failure CLI hardening for `init` / `reconcile` | Explicitly reserved for Phase 7 | `GAP-02`, Phase 7 roadmap entry |

---

## Required Automated Bundles

1. **Build-safety bundle**
   - `uv run pytest tests/unit/test_build_service.py tests/unit/test_build_cli.py tests/unit/test_validate_service.py -q`
2. **Phase 3 audit recovery bundle**
   - `uv run pytest tests/unit/test_build_paths.py tests/unit/test_template_render.py tests/unit/test_compose_build.py tests/unit/test_secrets.py tests/unit/test_env_materialize.py tests/unit/test_build_service.py tests/unit/test_compose_validation.py tests/unit/test_validate_service.py tests/unit/test_build_cli.py -q`
3. **Packaging sanity**
   - `uv build`

---

## Validation Sign-Off

- [x] Every planned task has an automated verification command.
- [x] Host-only work is explicitly excluded from this phase per D-01.
- [x] Validate-before-build enforcement is covered by automated service/CLI regressions.
- [x] Audit recovery includes artifact existence and requirement-reference checks.
- [x] Phase 7 git hardening is explicitly excluded.

**Approval:** pending
