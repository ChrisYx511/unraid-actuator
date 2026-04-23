---
phase: 05
slug: reconcile-execution-operator-visibility
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-22
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 via `uv run pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/unit/test_reconcile_git.py tests/unit/test_reconcile_plan.py tests/unit/test_reconcile_visibility.py tests/unit/test_reconcile_lock.py tests/unit/test_build_service.py tests/unit/test_validate_service.py tests/unit/test_reconcile_service.py tests/unit/test_reconcile_cli.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~12 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific command below
- **After every plan wave:** Run the quick run command above
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 12 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement / Decision | Test Type | Automated Command | File Exists | Status |
|---------|------|------|------------------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 05-01 | 1 | REC-01, REC-02, REC-06 | unit | `uv run pytest tests/unit/test_reconcile_git.py -q` | task creates | ⬜ pending |
| 05-01-02 | 05-01 | 1 | REC-03, REC-04 | unit | `uv run pytest tests/unit/test_reconcile_plan.py -q` | task creates | ⬜ pending |
| 05-02-01 | 05-02 | 1 | OPS-01, OPS-02, OPS-03 | unit | `uv run pytest tests/unit/test_reconcile_visibility.py -q` | task creates | ⬜ pending |
| 05-02-02 | 05-02 | 1 | D-11 | unit | `uv run pytest tests/unit/test_reconcile_lock.py -q` | task creates | ⬜ pending |
| 05-03-01 | 05-03 | 2 | REC-02, REC-03 | unit | `uv run pytest tests/unit/test_build_service.py tests/unit/test_validate_service.py -q` | already exists | ⬜ pending |
| 05-03-02 | 05-03 | 2 | REC-01, REC-02, REC-03, REC-04, REC-05, REC-06, OPS-01, OPS-02, OPS-03 | unit | `uv run pytest tests/unit/test_reconcile_service.py -q` | task creates | ⬜ pending |
| 05-04-01 | 05-04 | 3 | REC-01, REC-02, OPS-01 | unit | `uv run pytest tests/unit/test_reconcile_cli.py -q` | task creates | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Planned Test Coverage

- [ ] `tests/unit/test_reconcile_git.py` — dirty/diverged checkout failure, exact candidate SHA resolution, isolated incoming checkout preparation, and exact-SHA fast-forward behavior
- [ ] `tests/unit/test_reconcile_plan.py` — declaration-driven removal diffing, current-runtime target resolution, and D-06 rebuild-required signaling when removal inputs are missing/malformed
- [ ] `tests/unit/test_reconcile_visibility.py` — per-run file log creation, syslog lifecycle events, notification fan-out, and missing-notify warning-only behavior
- [ ] `tests/unit/test_reconcile_lock.py` — non-blocking single-run lock acquisition/release and overlap failure behavior
- [ ] `tests/unit/test_build_service.py` — parity coverage for new `run_build_for_host(...)` and shared runtime-root promotion helper
- [ ] `tests/unit/test_validate_service.py` — parity coverage for new `run_validate_for_host(...)`
- [ ] `tests/unit/test_reconcile_service.py` — no-op, invalid candidate, removal failure, successful apply/promotion/fast-forward, and explicit dry-run flows
- [ ] `tests/unit/test_reconcile_cli.py` — public reconcile command dispatch, dry-run flag routing, and exit-code/error-surface coverage

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real no-op reconcile writes one new timestamped run log plus syslog start/complete events and sends no Unraid notification | REC-01, OPS-01, OPS-03 | Requires a real Git remote, syslog, and Unraid host environment | On an Unraid host with the managed checkout already at the deploy-branch tip, run `unraid-actuator reconcile`, then confirm a new file appears under `/var/log/unraid-actuator/`, `logger` output is visible in syslog, and no WebGUI notification is emitted |
| Real applied reconcile tears down removed targets before applying the desired runtime tree and reports applied success visibly | REC-04, REC-05, REC-06, OPS-01, OPS-02, OPS-03 | Requires live Docker Compose plus an Unraid notification surface | Create a candidate commit that removes one declared target and changes another, run `unraid-actuator reconcile`, then confirm the removed target is brought down before the desired tree is applied, `docker compose up` success marks reconcile complete, the default runtime root now matches the candidate build, and a success notification appears |
| Removal-required reconcile rebuilds the current runtime tree from the managed known-good checkout before teardown when the current marked runtime tree is missing or malformed | REC-04 | Requires manipulating the real runtime tree on a Docker host | Stop after a successful prior deploy, remove the current `.UNRAID_RUNNING_CONFIGURATION` marker or a removed target's compose/env files, create a candidate commit that removes that target, run `unraid-actuator reconcile`, and confirm reconcile first rebuilds the current runtime tree from the managed checkout and only proceeds to teardown/apply if that rebuild succeeds safely |
| Missing `notify` remains warning-only while syslog/file logs still capture the run | OPS-02, OPS-03 | Depends on Unraid-specific `notify` command availability | Temporarily move or mask the `notify` command on a test host, trigger one failing reconcile and one successful applied reconcile, and confirm both runs still log to file/syslog while only a warning notes the missing notification command |
| `reconcile --dry-run` performs candidate evaluation without mutating the managed checkout or current runtime tree, including skipping any D-06 rebuild step | REC-02, REC-03 | Requires a real repo plus current runtime state to compare before/after | Record the current managed checkout SHA and current runtime-tree contents, run `unraid-actuator reconcile --dry-run` against a candidate commit that would require removals, and confirm the command reports the candidate SHA/planned removals and any would-rebuild note while the managed checkout SHA and current runtime root remain unchanged after the run |
| Overlapping reconciles are blocked by the single-run lock | REC-01 | Requires concurrent processes on a host | Start one long-running reconcile (or pause it in a debugger), launch a second `unraid-actuator reconcile`, and confirm the second exits immediately with the lock error and does not write a second mutation sequence |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing test files
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
