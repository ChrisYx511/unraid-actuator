# Phase 6: Build Safety & Verification Recovery - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the milestone-audit build gap without reopening host-only validation work. This phase covers enforcing validate-before-build safety inside the in-repo build workflow, restoring the missing Phase 3 verification/summaries so `BLD-01..07` are no longer orphaned, and realigning stale build-related docs to the shipped template/value workflow. It does not include manual host-UAT execution or the separate git-failure CLI hardening gap now assigned to Phase 7.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Phase 6 is **in-repo closure only**. Do not include host-only validation/UAT execution in this phase.
- **D-02:** The build workflow must enforce validation before secret decryption or staged materialization begins.
- **D-03:** Phase 3 audit recovery should verify the shipped build implementation as it exists now rather than trying to recreate historical execution exactly.
- **D-04:** Documentation updates in this phase should focus on stale build-related wording (`build.py` drift, Phase 3 artifact status, current-state docs), not broad project cleanup outside the reopened build subsystem.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/v1.0-MILESTONE-AUDIT.md`
- `.planning/ROADMAP.md` § Phase 6
- `.planning/REQUIREMENTS.md` § BLD-01..BLD-07
- `.planning/phases/03-runtime-build-secret-materialization/03-04-PLAN.md`
- `.planning/phases/03-runtime-build-secret-materialization/03-05-PLAN.md`
- `src/unraid_actuator/build.py`
- `src/unraid_actuator/validate.py`
- `src/unraid_actuator/cli.py`

</canonical_refs>

<specifics>
## Specific Gaps To Close

1. `BLD-01..07` are orphaned because Phase 3 has no `03-VERIFICATION.md` and no `03-*-SUMMARY.md`.
2. `GAP-01`: direct `unraid-actuator build` is not gated by validation; invalid host trees can reach secret decryption/materialization.
3. Build-related docs still describe `build.py` behavior even though the implementation uses declarative template/value sources.

</specifics>

---

*Phase: 06-build-safety-verification-recovery*
*Context gathered: 2026-04-22*
