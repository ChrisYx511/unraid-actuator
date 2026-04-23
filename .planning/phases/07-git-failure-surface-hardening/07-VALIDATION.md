---
phase: 07
slug: git-failure-surface-hardening
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-22
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for preserving intentional git RuntimeError bubbling and aligning stale planning docs.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run pytest` |
| **Quick run command** | `uv run pytest tests/unit/test_init_command.py tests/unit/test_reconcile_cli.py -q` |
| **Doc alignment command** | `uv run python -c "from pathlib import Path; roadmap=Path('.planning/ROADMAP.md').read_text(); project=Path('.planning/PROJECT.md').read_text(); audit=Path('.planning/v1.0-MILESTONE-AUDIT.md').read_text(); assert 'bubble' in roadmap.lower(); assert 'bubble' in project.lower(); assert 'bubble' in audit.lower(); text='\\n'.join([roadmap, project, audit]).lower(); banned=['normalize git failure handling','clean operator-facing cli','uncaught tracebacks','not yet normalized at the cli boundary','runtime error handling not normalized','git failure cli normalization']; assert all(item not in text for item in banned); print('ok')"` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After Task 1:** Run the quick run command.
- **After Task 2:** Run the doc alignment command, then rerun the quick run command.
- **Before `/gsd-verify-work`:** Both automated commands must be green.
- **Max feedback latency:** <10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement / Decision | Test Type | Automated Command | File Exists | Status |
|---------|------|------|------------------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 07-01 | 1 | GAP-02, D-01, D-03 | unit | `uv run pytest tests/unit/test_init_command.py tests/unit/test_reconcile_cli.py -q` | updates existing | ⬜ pending |
| 07-01-02 | 07-01 | 1 | GAP-02, D-02, D-04 | artifact | `uv run python -c "from pathlib import Path; roadmap=Path('.planning/ROADMAP.md').read_text(); project=Path('.planning/PROJECT.md').read_text(); audit=Path('.planning/v1.0-MILESTONE-AUDIT.md').read_text(); assert 'bubble' in roadmap.lower(); assert 'bubble' in project.lower(); assert 'bubble' in audit.lower(); text='\\n'.join([roadmap, project, audit]).lower(); banned=['normalize git failure handling','clean operator-facing cli','uncaught tracebacks','not yet normalized at the cli boundary','runtime error handling not normalized','git failure cli normalization']; assert all(item not in text for item in banned); print('ok')"` | updates existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Planned Test Coverage

- [ ] `tests/unit/test_init_command.py` — init CLI regression proving git clone `RuntimeError` bubbles instead of being converted into stderr/exit-code handling
- [ ] `tests/unit/test_reconcile_cli.py` — reconcile CLI regression proving git `RuntimeError` bubbles while existing `ValueError` and `YAMLValidationError` handling stay intact
- [ ] `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `.planning/v1.0-MILESTONE-AUDIT.md` — wording alignment to the approved bubbling policy

---

## Manual Scope Exclusions

These are intentionally **not** part of Phase 7 execution:

| Excluded Scope | Why Excluded | Where Tracked |
|----------------|--------------|---------------|
| Reformatting git failures into clean CLI stderr/exit-code-1 output | D-01 explicitly rejects broad catches and suppression | `07-CONTEXT.md`, `07-DISCUSSION-LOG.md` |
| Generic RuntimeError cleanup outside git-related init/reconcile paths | D-04 keeps the phase narrow | `07-CONTEXT.md` |
| Refactoring `reconcile_git.py`, `init.py`, or unrelated helpers beyond what tests prove is necessary | The shipped behavior already exists; Phase 7 is documentation/regression hardening | `07-CONTEXT.md` |
| Live Git remote failure drills on a real host | Not needed for this in-repo regression/documentation phase | Existing unit suite plus milestone audit narrative |

---

## Required Automated Bundles

1. **CLI bubbling regression bundle**
   - `uv run pytest tests/unit/test_init_command.py tests/unit/test_reconcile_cli.py -q`
2. **Phase 7 doc-alignment bundle**
   - `uv run python -c "from pathlib import Path; roadmap=Path('.planning/ROADMAP.md').read_text(); project=Path('.planning/PROJECT.md').read_text(); audit=Path('.planning/v1.0-MILESTONE-AUDIT.md').read_text(); assert 'bubble' in roadmap.lower(); assert 'bubble' in project.lower(); assert 'bubble' in audit.lower(); text='\\n'.join([roadmap, project, audit]).lower(); banned=['normalize git failure handling','clean operator-facing cli','uncaught tracebacks','not yet normalized at the cli boundary','runtime error handling not normalized','git failure cli normalization']; assert all(item not in text for item in banned); print('ok')"`

---

## Validation Sign-Off

- [x] Every planned task has an automated verification command
- [x] Existing tests are extended instead of creating unnecessary new scaffolding
- [x] D-01 is enforced by explicit exclusions against broad CLI catches
- [x] Documentation drift is validated with a narrow artifact assertion
- [x] No unrelated runtime or helper refactors are planned

**Approval:** pending
