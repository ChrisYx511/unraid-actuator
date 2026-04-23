---
phase: 05-reconcile-execution-operator-visibility
verified: 2026-04-22T20:35:00Z
status: passed
score: 5/5 must-haves verified
---

# Phase 5: Reconcile Execution & Operator Visibility Verification Report

**Phase Goal:** Operators can reconcile new desired state from Git safely, apply it with `docker compose up`, and see what happened.
**Verified:** 2026-04-22T20:35:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Dirty or locally diverged managed checkouts fail before reconcile mutates runtime or source state. | ✓ VERIFIED | `src/unraid_actuator/reconcile_git.py` uses `git status --porcelain=v2 --branch`, `git fetch --prune`, and `git merge-base --is-ancestor` to reject dirty/diverged state. Covered by `tests/unit/test_reconcile_git.py`. |
| 2 | Candidate validation/build happen from an isolated incoming checkout before reconcile mutates the managed checkout. | ✓ VERIFIED | `prepare_candidate_checkout()` creates a separate incoming checkout, and `run_reconcile()` validates/builds `candidate_workspace.host_root` and `candidate_workspace.build_root` first. Covered by `tests/unit/test_reconcile_git.py` and `tests/unit/test_reconcile_service.py`. |
| 3 | Reconcile tears removed targets down before apply, rebuilding the current runtime tree first when D-06 requires it. | ✓ VERIFIED | `src/unraid_actuator/reconcile.py` plans removals, rebuilds the current runtime tree from the managed host root when `requires_current_rebuild` is set, then executes scoped `run_teardown(...)` before `run_deploy(...)`. Covered by `tests/unit/test_reconcile_plan.py` and `tests/unit/test_reconcile_service.py`. |
| 4 | Reconcile visibility includes per-run log files, syslog lifecycle/failure events, notify fan-out, and single-run locking. | ✓ VERIFIED | `src/unraid_actuator/reconcile_visibility.py` and `src/unraid_actuator/reconcile_lock.py` implement the logging/notify/lock contracts. Covered by `tests/unit/test_reconcile_visibility.py` and `tests/unit/test_reconcile_lock.py`. |
| 5 | The public CLI exposes `reconcile` and explicit reconcile dry-run semantics without delegating dry-run behavior to the generic DryRunRunner path. | ✓ VERIFIED | `src/unraid_actuator/cli.py` routes reconcile to `run_reconcile(...)` with `SubprocessRunner()` by default and passes a dedicated dry-run boolean. Covered by `tests/unit/test_reconcile_cli.py`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/unraid_actuator/reconcile_models.py` | Shared DTOs for reconcile state/workspaces/results | ✓ VERIFIED | Defines `ManagedCheckoutState`, `CandidateWorkspace`, `RemovedTargetsPlan`, `ReconcileResult`, and `ReconcileStatus`. |
| `src/unraid_actuator/reconcile_git.py` | Managed checkout safety, candidate checkout, fast-forward helpers | ✓ VERIFIED | Implements exact-SHA inspection, candidate workspace creation, and post-apply source advancement. |
| `src/unraid_actuator/reconcile_plan.py` | Declaration-driven removal planning | ✓ VERIFIED | Diffs current vs incoming declarations and explicitly distinguishes teardown-ready vs rebuild-required current runtime state. |
| `src/unraid_actuator/reconcile_visibility.py` / `reconcile_lock.py` | Logging/notify fan-out and overlap prevention | ✓ VERIFIED | Provides per-run log sink, syslog/notify helpers, and non-blocking flock-based lock. |
| `src/unraid_actuator/reconcile.py` / `cli.py` | Core reconcile coordinator and public CLI | ✓ VERIFIED | Wires candidate trust, teardown-before-apply, promotion, fast-forward, and public `reconcile` command dispatch. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 5 targeted coverage passes | `uv run pytest tests/unit/test_build_service.py tests/unit/test_validate_service.py tests/unit/test_reconcile_git.py tests/unit/test_reconcile_plan.py tests/unit/test_reconcile_visibility.py tests/unit/test_reconcile_lock.py tests/unit/test_reconcile_service.py tests/unit/test_reconcile_cli.py -q` | `35 passed` | ✓ PASS |
| Full repository coverage passes after Phase 5 | `uv run pytest -q` | `108 passed` | ✓ PASS |
| Packaging still succeeds after Phase 5 | `uv build` | passed | ✓ PASS |
| Public CLI exposes reconcile | `uv run python -m unraid_actuator reconcile --help` | Help includes reconcile-specific `--dry-run` | ✓ PASS |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
| --- | --- | --- | --- |
| `REC-01` | No-op reconcile success when no new commits are available | ✓ SATISFIED | `run_reconcile()` short-circuits on equal SHAs and tests assert no mutation. |
| `REC-02` | Reconcile evaluates a fetched candidate without mutating the managed source first | ✓ SATISFIED | Candidate checkout/build happen in a separate incoming workspace. |
| `REC-03` | Invalid incoming candidate configuration fails reconcile | ✓ SATISFIED | `run_reconcile()` rejects validation errors before removals/apply. |
| `REC-04` | Removed app/environments are torn down during reconcile | ✓ SATISFIED | Declaration-driven removal planning plus scoped `run_teardown(...)` loop. |
| `REC-05` | Desired state is applied with `docker compose up` | ✓ SATISFIED | `run_deploy(...)` is called against the candidate build root. |
| `REC-06` | Managed source advances only after successful build and apply | ✓ SATISFIED | Promotion happens before `fast_forward_managed_checkout(...)`; failure stops advancement. |
| `OPS-01` | Syslog lifecycle events | ✓ SATISFIED | Visibility adapter emits `reconcile started` / `reconcile complete` through `logger`. |
| `OPS-02` | Failures reported to syslog and Unraid notifications | ✓ SATISFIED | `log_failure(...)` emits syslog and notify, with warning-only fallback when notify is missing. |
| `OPS-03` | Reconcile log files include compose apply output under `/var/log/unraid-actuator/` | ✓ SATISFIED | Visibility adapter writes per-run log files and reconcile forwards teardown/deploy command results with output enabled. |

### Manual Host Checks Remaining (Non-Blocking)

These checks remain recommended on a real Unraid host because Docker Compose, syslog, and the real `notify` command are not available in this environment:

1. **True no-op reconcile**
   - Confirm one timestamped log file is written, syslog shows started/completed, and no Unraid notification is emitted.
2. **Applied reconcile with removals**
   - Confirm removed targets are brought down before desired-state apply and a success notification appears.
3. **D-06 rebuild path**
   - Remove or corrupt the current runtime marker/tree, run reconcile with a removed target, and confirm reconcile rebuilds the current runtime tree before teardown.
4. **Lock contention**
   - Start one reconcile and confirm a second exits immediately with the overlap error.

### Gaps Summary

No blocking gaps found. Phase 5 implementation satisfies the plan set, the mapped reconciliation and observability requirements, and the locked decisions around candidate isolation, teardown-before-apply ordering, D-06 rebuild handling, notify fallback, timestamped logs, explicit dry-run semantics, and single-run locking.

---

_Verified: 2026-04-22T20:35:00Z_
_Verifier: the agent (gsd-verifier)_
