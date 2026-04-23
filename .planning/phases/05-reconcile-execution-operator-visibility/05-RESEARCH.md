# Phase 5: Reconcile Execution & Operator Visibility - Research

**Researched:** 2026-04-22  
**Domain:** Safe Git-driven reconcile orchestration for Unraid Docker Compose  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Managed source safety
- **D-01:** If the managed source checkout has uncommitted changes or local commits that are not a clean fast-forward from the configured deploy branch, reconcile should fail immediately and require operator cleanup.
- **D-02:** Reconcile should continue to evaluate incoming candidate state from a separate incoming checkout/work area before mutating the managed source checkout or the current runtime tree.

### Runtime mutation ordering
- **D-03:** After the incoming candidate has been fetched, validated, and built successfully, reconcile should tear down removed app/environments first and only then apply the desired runtime tree.
- **D-04:** If teardown of a removed app/environment fails during reconcile, stop the entire reconcile immediately and do not apply the incoming desired state.
- **D-05:** v1 reconcile success is defined by successful `docker compose up` execution, not by post-apply container health checks.
- **D-06:** If removals are required but the current marked runtime tree is missing or malformed, reconcile should first rebuild that current runtime tree from the current known-good managed checkout and only fail if that rebuild cannot be produced safely.

### Operator visibility
- **D-07:** If the expected Unraid notification command is unavailable, reconcile should continue, emit a warning, and still write syslog/file logs.
- **D-08:** When reconcile finds no new commits to apply, record the no-op success in syslog and reconcile log files only; reserve Unraid notifications for applied success and failures.
- **D-09:** Reconcile should create one timestamped log file per run under `/var/log/unraid-actuator/`, rather than appending to a single rolling log.

### Dry-run and execution safety
- **D-10:** Phase 5 should include a public `reconcile --dry-run` mode with explicit non-mutating behavior rather than relying on accidental composition of the existing service dry-run paths.
- **D-11:** Phase 5 should include a single-run reconcile lock and fail when another reconcile is already active.

### the agent's Discretion
- Exact internal module split for Git candidate inspection, reconcile logging, notification adapters, and source fast-forward helpers.
- Exact log filename format and timestamp representation, as long as each reconcile run gets its own file.
- Exact warning/success message wording for syslog, files, and notifications, as long as the visibility contract above remains explicit.

### Deferred Ideas (OUT OF SCOPE)
- Container health-based reconcile success criteria — explicitly deferred; v1 success is `docker compose up` succeeding
- Richer log retention/rotation policy beyond timestamped per-run files
- Broader manual deploy/teardown notification behavior outside reconcile
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REC-01 | Operator can run reconcile and get a no-op success when the configured deploy branch has no new commits | Use `git fetch` + `git status --porcelain=v2 --branch` + exact SHA comparison before any build/apply |
| REC-02 | Operator can reconcile against a fetched candidate commit without mutating the managed source checkout first | Use isolated incoming checkout/work area plus isolated candidate build root |
| REC-03 | Operator gets a reconcile failure when the incoming candidate configuration is invalid | Reuse validation/build on the incoming checkout; do not compute removals until candidate validates/builds |
| REC-04 | Operator can tear down app/environments removed from the declared host state | Diff current declared targets vs incoming declared targets in current declaration order; teardown from the current marked build tree or a rebuilt current tree from the managed known-good checkout when needed |
| REC-05 | Operator can apply the current desired host state by running `docker compose up` against the generated runtime tree | Reuse `run_deploy(build_root=...)` against the candidate build root |
| REC-06 | Operator only advances the managed source tree to the new commit after a successful build and apply sequence | Fast-forward managed checkout to the exact candidate SHA only after teardown/apply/promotion succeed |
| OPS-01 | Operator gets `reconcile started` and `reconcile complete` lifecycle events in syslog | Add explicit syslog adapter around `logger` CLI and emit start/finish events |
| OPS-02 | Operator gets reconcile failures reported to syslog and Unraid notifications | Add failure fan-out: file log + syslog + Unraid `notify`; missing notify is warning-only |
| OPS-03 | Operator gets reconcile log files, including compose apply output, written under `/var/log/unraid-actuator/` | Add per-run file sink; record command, exit code, stdout, stderr for Git/build/compose/notify/syslog steps |
</phase_requirements>

## Summary

Phase 5 should be implemented as an orchestration layer, not a rewrite of existing build/deploy logic. The safest shape is: verify the managed checkout is clean and fast-forwardable, fetch the deploy branch, materialize the incoming candidate in a separate checkout, validate/build that candidate into a separate build root, compute removed targets from declared host state, tear those removed targets down from the current runtime tree, apply the candidate runtime tree with existing deploy services, then promote the candidate build root and fast-forward the managed checkout to the exact candidate commit.

The biggest design trap is preserving the current runtime tree long enough to tear down removed targets. `run_build()` currently swaps its output into place, so reconcile must not build the candidate directly into `/tmp/unraid-actuator/build` before removals run. Build the candidate into a fresh reconcile-only temp root first, then promote it after successful apply.

Operator visibility should stay simple and explicit: one per-run file log under `/var/log/unraid-actuator/`, short lifecycle events to syslog, and Unraid notifications only for applied success and failure. Missing `notify` is already a locked warning-only case, so the notification adapter should be optional and preflight its command path before invoking the runner.

**Primary recommendation:** Implement reconcile as a coordinator over four reusable surfaces: Git safety helpers, candidate validate/build helpers, existing deploy/teardown services, and a fan-out visibility adapter.

## Project Constraints (from copilot-instructions.md)

- Must run within normal Unraid constraints: cron execution, ramfs-heavy temporary storage, and persistent USB-backed boot media.
- Must remain a Python project consumable by other `uv` projects via `uv_build`.
- YAML parsing must continue to use `strictyaml`.
- Decrypted secret material must only exist in intentionally generated runtime trees.
- `git` and `docker compose` CLI behavior are part of the runtime contract; command execution needs clear error surfaces, dry-run support, and testable wrappers.
- Keep the CLI thin and stdlib `argparse` based.
- No project skill directories were present under `.github/skills/` or `.agents/skills/`.

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Git CLI | 2.x (`git` docs reviewed; local env 2.50.1) | Fetch, branch safety checks, candidate commit comparison, final fast-forward | Official scripting surfaces exist for status porcelain, ancestry checks, and `--ff-only` merges |
| Docker Compose CLI | v2 | Apply and tear down runtime trees | Already the project runtime contract and existing deploy service target |
| Python stdlib (`pathlib`, `tempfile`, `shutil`, `datetime`) | Python 3.13+ | Candidate work areas, build-root promotion, timestamped logs | No new dependency needed; fits cron-first CLI tooling |
| Unraid `notify` script | Bundled with Unraid WebGUI | Operator notifications | Official platform notification surface; avoids custom transport logic |

### Supporting
| Library / Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `strictyaml` | 1.7.3 (current PyPI latest verified 2023-03-10) | Load current/incoming `apps.y[a]ml` and active config | Reuse existing schema-backed host parsing |
| `pytest` | 8.4.2 in lockfile (`uv run pytest`), 9.0.3 latest on PyPI | Unit-test reconcile orchestration and adapters | Use project-resolved 8.4.2 via `uv`; do not upgrade in this phase |
| `logger` CLI | system tool | Syslog lifecycle/failure events | Prefer minimal `logger -t ...` usage through `runner.py` |
| `ejson` CLI | 1.5.4 in local env | Candidate build secret decryption | Required indirectly because reconcile reuses `run_build()` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate incoming clone/check-out dir | `git worktree add --detach` | `git worktree` is standard, but it writes extra metadata into the managed repo; that weakens the “separate incoming work area before mutation” posture |
| `logger` CLI adapter | Python `logging.handlers.SysLogHandler` | `SysLogHandler` assumes socket/address details; `logger` keeps syslog as an external command and matches the project runner pattern |
| Stdlib file writer / `FileHandler` | Third-party logging package | No real benefit for v1; per-run files are simple and already locked as the logging model |

**Installation:**
```bash
uv sync
```

**Version verification:**
- `jinja2` latest verified: 3.1.6 (PyPI upload 2025-03-05)
- `python-dotenv` latest verified: 1.2.2 (PyPI upload 2026-03-01)
- `strictyaml` latest verified: 1.7.3 (PyPI upload 2023-03-10)
- `pytest` latest verified: 9.0.3 (PyPI upload 2026-04-07); project lock currently resolves 8.4.2
- `uv_build` latest verified: 0.11.7 (PyPI upload 2026-04-15)

No new Python dependency is recommended for Phase 5.

## Architecture Patterns

### Recommended Project Structure
```text
src/unraid_actuator/
├── reconcile.py          # top-level reconcile service/orchestrator
├── reconcile_git.py      # fetch, cleanliness, ancestry, candidate checkout, final fast-forward
├── reconcile_plan.py     # declared-target diffing / removal planning helpers
├── reconcile_visibility.py # per-run file log + syslog + notification fan-out
└── cli.py                # thin argparse wiring for `reconcile`
```

### Pattern 1: Two-Phase Candidate Reconcile
**What:** Separate “inspect/build candidate” from “mutate current state”.
**When to use:** Always; this is the core locked Phase 5 workflow.
**Example:**
```python
candidate_sha = fetch_and_resolve_candidate(...)
if candidate_sha == current_sha:
    log_noop(...)
    return

candidate_checkout = prepare_candidate_checkout(...)
validate_candidate(...)
candidate_build_root = build_candidate(...)

removed = planned_removals(current_declared, incoming_declared)
teardown_removed_from_current_runtime_tree(removed)
apply_candidate_runtime_tree(candidate_build_root)
promote_candidate_build_root(candidate_build_root)
fast_forward_managed_checkout(candidate_sha)
```
**Why:** This is the only sequencing that preserves the current runtime tree long enough to tear down removals and still avoids mutating the managed checkout before candidate validation succeeds.

### Pattern 2: Ordered Removal Diff From Declared Host State
**What:** Compute removals from declaration keys, not from compose file contents or runtime-tree directory listings.
**When to use:** When deciding which app/environments were intentionally removed by the incoming candidate.
**Example:**
```python
def removal_plan(current_declared, incoming_declared):
    incoming_keys = {(item.app, item.environment) for item in incoming_declared}
    return tuple(
        item for item in current_declared
        if (item.app, item.environment) not in incoming_keys
    )
```
**Why:** `load_declared_environments()` already defines the trusted host intent surface and preserves declaration order needed for predictable teardown order.

### Pattern 3: Reuse Services by Lowering the Config Boundary
**What:** Factor config-loading wrappers from core services so reconcile can point validate/build helpers at either the managed checkout or the incoming checkout without writing temp active-config files.
**When to use:** For candidate validate/build reuse.
**Example:**
```python
def run_build_for_host(*, host_root: Path, output_root: Path, runner: CommandRunner) -> BuildResult:
    ...

def run_build(*, runner: CommandRunner, config_path: Path = ACTIVE_CONFIG_PATH, output_root: Path | None = None) -> BuildResult:
    config = load_active_config(path=config_path)
    return run_build_for_host(
        host_root=config.source_path / config.hostname,
        output_root=resolve_output_root(output_root),
        runner=runner,
    )
```
**Why:** Reconcile should reuse logic, not reuse the persisted active-config file as mutable state.

### Anti-Patterns to Avoid
- **Building the candidate into the default build root before removals:** this destroys the compose/env artifacts needed for `docker compose down` on removed targets.
- **Using `git worktree` directly against the managed checkout:** it adds linked-worktree metadata under the managed repo; that is weaker isolation than a separate incoming checkout.
- **Computing removals from build-root contents alone:** stale or missing build roots can lie; removals must come from declared host intent.
- **Fast-forwarding to the remote tip after apply instead of the exact candidate SHA:** the applied state and source checkout can drift if the remote moves during reconcile.
- **Treating an invalid candidate as an empty desired state:** invalid incoming state must fail safe, not trigger removals.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git branch safety parsing | Parsing human `git status` text | `git status --porcelain=v2 --branch` + `git merge-base --is-ancestor` | Stable machine-readable output plus exact ancestry checks |
| Fast-forward-only source advance | Manual ref editing | `git merge --ff-only <candidate_sha>` | Official fast-forward safety gate |
| Candidate notification transport | Custom HTTP/webhook client | Unraid `notify` script | Official platform surface already handles agents and UI integration |
| Syslog socket integration | Raw socket writes | `logger` CLI through `runner.py` | Simpler, testable, fewer platform assumptions |
| Removed-target detection | Compose YAML diffs / filesystem heuristics | Declared target set diff from `apps.y[a]ml` | Intent is defined by declaration, not rendered artifact detail |

**Key insight:** Phase 5 is mostly coordination. New code should compose existing validated surfaces instead of inventing a second build/deploy stack inside reconcile.

## Common Pitfalls

### Pitfall 1: Replacing the build root too early
**What goes wrong:** Removed targets cannot be torn down because their compose/env files were overwritten by the candidate build.
**Why it happens:** `run_build()` swaps output into place atomically.
**How to avoid:** Always build the candidate into a fresh reconcile-only temp root first, then promote after successful apply.
**Warning signs:** Removal list is non-empty and current build-root paths disappear before teardown begins.

### Pitfall 2: Treating invalid candidate state as removals
**What goes wrong:** A broken incoming `apps.yaml`, secrets file, or compose source looks like “all current targets were removed”.
**Why it happens:** Removal diff is computed before the candidate is trusted.
**How to avoid:** Only compute and execute removals after candidate validate/build succeeds.
**Warning signs:** Candidate validation fails but reconcile still attempts teardown.

### Pitfall 3: Advancing the managed checkout to a moving remote tip
**What goes wrong:** The running state matches one commit, but the managed checkout lands on a newer commit that was never validated/applied.
**Why it happens:** Final source advance uses `origin/<branch>` instead of the exact candidate SHA.
**How to avoid:** Persist the fetched candidate SHA and fast-forward to that exact commit only.
**Warning signs:** `git fetch` runs again after apply or the final merge target is a ref name instead of a SHA.

### Pitfall 4: Assuming current dry-run behavior composes end-to-end
**What goes wrong:** Candidate build produces no real files in dry-run, then deploy/teardown helpers fail because the marked runtime tree does not exist.
**Why it happens:** `DryRunRunner` suppresses external execution, and `run_build()` returns without materializing a build root.
**How to avoid:** Test reconcile with `RecordingRunner` + temp dirs; if public `reconcile --dry-run` is added, define explicit semantics instead of assuming existing service composition.
**Warning signs:** Dry-run reconcile fails at build-root trust checks.

### Pitfall 5: Missing current runtime tree when removals exist
**What goes wrong:** The desired candidate is valid, but there is no safe compose/env source for `docker compose down` on removed targets.
**Why it happens:** The current build root lives under `/tmp` and may be gone after reboot or cleanup.
**How to avoid:** Rebuild the current runtime tree from the current known-good managed checkout before teardown, and only fail if that rebuild cannot be produced safely.
**Warning signs:** Removed targets are planned, `require_marked_runtime_tree()` fails on the current build root, and the managed checkout cannot be rebuilt cleanly.

## Code Examples

Verified patterns from official sources:

### Stable Git status parsing
```bash
git status --porcelain=v2 --branch
```
Source: https://raw.githubusercontent.com/git/git/master/Documentation/git-status.adoc

### Exact ancestry check for fast-forward safety
```bash
git merge-base --is-ancestor HEAD "$candidate_sha"
```
Source: https://raw.githubusercontent.com/git/git/master/Documentation/git-merge-base.adoc

### Fast-forward-only source advance
```bash
git merge --ff-only "$candidate_sha"
```
Source: https://raw.githubusercontent.com/git/git/master/Documentation/git-merge.adoc

### Official Unraid notification surface
```bash
/usr/local/emhttp/webGui/scripts/notify \
  -e "unraid-actuator" \
  -s "Reconcile failed" \
  -d "Candidate validation failed" \
  -i "alert"
```
Source: https://raw.githubusercontent.com/unraid/webgui/master/emhttp/plugins/dynamix/scripts/notify

### Timestamped log filenames with UTC
```python
from datetime import datetime, timezone

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
log_path = Path("/var/log/unraid-actuator") / f"reconcile-{stamp}.log"
```
Source pattern: Python stdlib datetime/logging guidance  
https://docs.python.org/3/library/logging.html

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parse human `git status` output | Use porcelain status formats for scripts | Longstanding Git scripting guidance; v2 adds structured branch headers | Safer no-op/dirty/divergence detection |
| Apply directly from mutable source checkout | Build isolated runtime tree, then apply built artifact | Already established by Phases 3-4 | Reconcile should stay artifact-driven |
| Single rolling reconcile log | One timestamped file per run | Locked Phase 5 decision | Simpler auditing; no rotation design needed in v1 |
| Socket-level syslog assumptions | External syslog command adapter | Current codebase favors runner-wrapped commands | Better dry-run/testing alignment |

**Deprecated/outdated:**
- `git worktree` for the candidate path in this project: technically valid Git, but weaker isolation than the locked separate incoming checkout posture.
- Building the candidate into `/tmp/unraid-actuator/build` before removals: incompatible with REC-04 under current build semantics.

## Open Questions

1. **What should reconcile do if removed targets exist but the current marked build root is missing?**
   - What we know: removed-target teardown needs the current compose/env artifact set; current build roots live under `/tmp`.
   - What's unclear: whether Phase 5 should fail safe immediately or rebuild the current source tree just to recover removal artifacts.
   - Recommendation: Plan an explicit safe failure for v1 unless the team wants a separate “rebuild current runtime artifact” recovery path.

2. **Should public `reconcile --dry-run` be fully supported in Phase 5?**
   - What we know: the CLI has a shared `--dry-run`, but current build/deploy helpers do not compose end-to-end under dry-run.
   - What's unclear: whether the user expects reconcile dry-run beyond unit-test seams.
   - Recommendation: Either scope dry-run semantics explicitly in the plan or treat it as non-goal for this phase and keep dry-run coverage at the adapter/service-test level.

3. **Is concurrent reconcile locking required in v1?**
   - What we know: cron + manual invocation can overlap on Unraid.
   - What's unclear: whether a lockfile/flock step belongs in Phase 5 scope.
   - Recommendation: Mention this in planning review; if added, keep it minimal and local to reconcile orchestration.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | CLI/runtime/tests | ✓ | 3.14.3 | — |
| `uv` | test execution | ✓ | 0.8.15 | — |
| Git CLI | fetch/safety/final fast-forward | ✓ | 2.50.1 | — |
| Docker CLI / Compose v2 | teardown/apply execution | ✗ | — | — |
| `ejson` | candidate build via existing `run_build()` | ✓ | 1.5.4 | — |
| `logger` | syslog lifecycle/failure events | ✓ | present (`/usr/bin/logger`) | file log only during local dev if syslog is not validated |
| Unraid `notify` script | notifications | ✗ on this machine | — | Warning-only skip is already a locked decision |

**Missing dependencies with no fallback:**
- Docker Compose is not available on this machine, so end-to-end apply/teardown verification cannot run locally here.

**Missing dependencies with fallback:**
- Unraid `notify` is absent locally; unit tests should use `RecordingRunner`, and runtime behavior should degrade to warning-only when the command is missing.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 via `uv run pytest` |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/unit/test_reconcile_service.py -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REC-01 | No-op reconcile after fetch when candidate SHA == current SHA | unit | `uv run pytest tests/unit/test_reconcile_service.py::test_reconcile_noop_logs_without_notify -q` | ❌ Wave 0 |
| REC-02 | Candidate evaluated from separate checkout/work area before mutation | unit | `uv run pytest tests/unit/test_reconcile_git.py::test_candidate_checkout_isolated_from_managed_source -q` | ❌ Wave 0 |
| REC-03 | Invalid candidate fails before teardown/apply/fast-forward | unit | `uv run pytest tests/unit/test_reconcile_service.py::test_invalid_candidate_stops_before_runtime_mutation -q` | ❌ Wave 0 |
| REC-04 | Removed targets are torn down first in current declaration order | unit | `uv run pytest tests/unit/test_reconcile_service.py::test_removed_targets_teardown_before_apply -q` | ❌ Wave 0 |
| REC-05 | Candidate build root applied with existing deploy service | unit | `uv run pytest tests/unit/test_reconcile_service.py::test_apply_uses_candidate_build_root -q` | ❌ Wave 0 |
| REC-06 | Managed source advances only after successful apply | unit | `uv run pytest tests/unit/test_reconcile_git.py::test_fast_forward_happens_after_success_only -q` | ❌ Wave 0 |
| OPS-01 | Syslog start/complete events emitted | unit | `uv run pytest tests/unit/test_reconcile_visibility.py::test_syslog_lifecycle_events -q` | ❌ Wave 0 |
| OPS-02 | Failures go to syslog and notify; missing notify is warning-only | unit | `uv run pytest tests/unit/test_reconcile_visibility.py::test_failure_notifies_and_missing_notify_warns -q` | ❌ Wave 0 |
| OPS-03 | Per-run log file contains compose/apply output | unit | `uv run pytest tests/unit/test_reconcile_visibility.py::test_reconcile_log_file_captures_command_output -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/test_reconcile_service.py -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_reconcile_service.py` — core sequencing, no-op, invalid-candidate, removal/apply ordering
- [ ] `tests/unit/test_reconcile_git.py` — dirty checkout, local-ahead/diverged failure, exact-candidate fast-forward
- [ ] `tests/unit/test_reconcile_visibility.py` — file/syslog/notify adapters and missing-notify behavior
- [ ] `tests/unit/test_reconcile_cli.py` — thin CLI wiring, exit codes, and stdout/stderr behavior

## Sources

### Primary (HIGH confidence)
- Project code: `src/unraid_actuator/init.py`, `build.py`, `deploy.py`, `deploy_tree.py`, `validate.py`, `runner.py`, `cli.py` — current reusable surfaces and constraints
- Git official docs:
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-status.adoc — porcelain v1/v2 and branch headers
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-merge-base.adoc — `--is-ancestor`
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-merge.adoc — `--ff-only`
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-fetch.adoc — fetch / remote-tracking / `FETCH_HEAD`
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-worktree.adoc — linked worktree metadata behavior
  - https://raw.githubusercontent.com/git/git/master/Documentation/git-clone.adoc — local/shared/reference clone behavior
- Unraid official WebGUI sources:
  - https://raw.githubusercontent.com/unraid/webgui/master/emhttp/plugins/dynamix/scripts/notify — notification CLI surface and usage
  - https://raw.githubusercontent.com/unraid/webgui/master/emhttp/plugins/dynamix/include/Notify.php — how Unraid itself builds notify invocations
  - https://raw.githubusercontent.com/unraid/webgui/master/emhttp/plugins/dynamix/agents/Discord.xml — official example usage
- Python official docs:
  - https://docs.python.org/3/library/logging.html — stdlib logging/file patterns
  - https://raw.githubusercontent.com/python/cpython/main/Doc/library/logging.handlers.rst — `SysLogHandler`, file handler guidance
- Package/version verification:
  - `pyproject.toml`
  - `uv.lock`
  - https://pypi.org/pypi/jinja2/json
  - https://pypi.org/pypi/python-dotenv/json
  - https://pypi.org/pypi/strictyaml/json
  - https://pypi.org/pypi/pytest/json
  - https://pypi.org/pypi/uv-build/json

### Secondary (MEDIUM confidence)
- GitHub code search examples of `/usr/local/emhttp/webGui/scripts/notify` usage in `unraid/webgui` and community Unraid scripts, cross-checked against the official `notify` script.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependency recommendation; Git/Unraid/Python surfaces were verified from official sources and project code.
- Architecture: MEDIUM - Core sequencing is strongly supported by current code behavior, but there is no live Unraid/Docker validation on this machine.
- Pitfalls: HIGH - Most pitfalls come directly from existing build/deploy semantics and locked phase decisions.

**Research date:** 2026-04-22  
**Valid until:** 2026-05-22
