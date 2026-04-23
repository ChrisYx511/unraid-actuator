# Phase 7: Git Failure Surface Hardening - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Realign the remaining Phase 7 work to the user's preferred error-handling policy. This phase no longer aims to catch and reprint git-related `RuntimeError` failures from `init` and `reconcile`. Instead, it should preserve intentional exception bubbling, codify that behavior with tests, and remove the stale roadmap/audit language that still treats uncaught git exceptions as a blocker. It does not broaden into generic exception handling, build/deploy behavior, or other CLI cleanup.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Git-related `RuntimeError` exceptions in `init` and `reconcile` should be allowed to bubble up. Do not add broad CLI catches that print and suppress them.
- **D-02:** Phase 7 should update stale roadmap/project/audit language that currently describes exception bubbling as a blocker.
- **D-03:** Unit tests should explicitly prove the intended propagation behavior from the `init` and `reconcile` CLI paths.
- **D-04:** Keep this phase narrow: no generic exception normalization, no broader git helper refactors, and no new operator-facing formatting layer.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md` § Phase 7
- `.planning/PROJECT.md`
- `.planning/v1.0-MILESTONE-AUDIT.md`
- `.planning/STATE.md`
- `src/unraid_actuator/cli.py`
- `src/unraid_actuator/init.py`
- `src/unraid_actuator/reconcile.py`
- `src/unraid_actuator/reconcile_git.py`

</canonical_refs>

<specifics>
## Specific Planning Inputs

1. The current roadmap/audit narrative assumes uncaught git exceptions are a bug; the user explicitly overrode that assumption.
2. `cli.py` currently catches `YAMLValidationError` and `ValueError` for `init`/`reconcile`, but does not broadly catch `RuntimeError`.
3. `init.py` and `reconcile_git.py` already raise `RuntimeError` on git command failures, so the likely implementation work is documentation and regression coverage rather than new runtime behavior.

</specifics>

---

*Phase: 07-git-failure-surface-hardening*
*Context gathered: 2026-04-22*
