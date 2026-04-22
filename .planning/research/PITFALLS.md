# Pitfalls Research

**Domain:** Git-driven Docker Compose reconciliation for a single-host Unraid actuator
**Researched:** 2026-04-22
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Advancing Git state before the host proves it can run it

**What goes wrong:** the actuator fast-forwards its managed checkout before validation/build/apply succeed, so the host points at bad desired state.

**Why it happens:** projects use the working checkout as both source-of-truth and deployment input.

**How to avoid:** fetch first, build and validate a candidate tree from the target commit, and only advance persistent source state after a successful apply.

**Warning signs:** dirty managed checkout after failure; reconcile logic built around `git pull` instead of explicit target commit handling.

**Phase to address:** validation/reconcile foundation.

---

### Pitfall 2: Treating invalid desired state as intentional deletion

**What goes wrong:** a broken app/environment config is treated as “removed”, so healthy workloads get torn down because a bad commit could not be parsed or rendered.

**Why it happens:** tooling collapses “absent”, “invalid”, and “undeclared” into the same bucket.

**How to avoid:** model desired state explicitly; only tear down previously managed workloads that are absent from a fully valid desired state.

**Warning signs:** delete actions and validation failures appear in the same reconcile plan.

**Phase to address:** validation semantics and reconcile planning.

---

### Pitfall 3: Unstable Compose project naming

**What goes wrong:** temp build paths or directory names change Compose project identity, causing duplicate stacks or missed teardowns.

**Why it happens:** Compose defaults to directory-derived project naming unless told otherwise.

**How to avoid:** derive a deterministic project name from `host + app + environment` and pass it explicitly.

**Warning signs:** container/network names differ between runs for the same app/environment.

**Phase to address:** validation/build normalization.

---

### Pitfall 4: Secret leakage to persistent storage or logs

**What goes wrong:** decrypted EJSON material lands on flash/disk, in syslog, or in verbose command output.

**Why it happens:** projects focus on decryption success, not plaintext containment.

**How to avoid:** keep decrypted output in ephemeral storage by default, write sensitive files with restrictive permissions, redact logs, and avoid passing secrets via argv.

**Warning signs:** plaintext `.env` under the repo checkout, verbose debug output showing merged env vars, or notifications containing command lines.

**Phase to address:** build/secrets handling and hardening.

---

### Pitfall 5: `build.py` as silent arbitrary host code execution

**What goes wrong:** a compromised or mistaken infrastructure repo executes arbitrary Python on the Unraid host during build.

**Why it happens:** dynamic config generation is treated like harmless templating when it is really privileged code execution.

**How to avoid:** make the trust model explicit, allow dynamic builds to be disabled, execute `build.py` out-of-process with a minimal environment, and log commit/script identity.

**Warning signs:** `build.py` inherits the full host environment or runs without auditability.

**Phase to address:** trust model and build execution.

---

### Pitfall 6: Nondeterministic environment resolution

**What goes wrong:** the same Git commit renders differently under cron vs interactive shells because Compose interpolation pulls from ambient environment state.

**Why it happens:** Compose environment precedence is subtle and host env often leaks into validation or deploy steps.

**How to avoid:** materialize `.env` explicitly in the build tree, scrub subprocess environments, and fail unresolved variables during validation.

**Warning signs:** “works manually, fails in cron” behavior or different config output from the same commit.

**Phase to address:** validation/build normalization.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| deploy directly from checkout | fewer copies | drift, secret persistence, hard-to-debug failures | never |
| shell commands embedded in CLI handlers | fast initial coding | weak tests and poor dry-run support | never |
| no persistent applied-state record | less file management | impossible to distinguish target commit from last good deploy | never |
| permissive YAML parsing | fewer schema decisions early | ambiguous behavior and weaker validation | never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Docker Compose | relying on directory names for identity | pass explicit stable project names |
| Docker Compose | treating `up -d` exit code as full success | combine with wait/health checks where feasible |
| EJSON | decrypting into persistent repo paths | decrypt only into tmpfs-style build output |
| Git | using blind `pull` as reconcile input | fetch target commit explicitly, then fast-forward only after success |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| logging merged environment data | secret disclosure | redact env content and log only metadata |
| enabling `build.py` without explicit trust framing | host compromise | make dynamic build execution privileged and optional |
| blindly applying risky Compose settings | privilege escalation or host exposure | add validation/policy checks for dangerous fields |

## "Looks Done But Isn't" Checklist

- [ ] **Validation:** declared app/env pairs fail hard when invalid, undeclared invalid pairs warn only
- [ ] **Build:** generated compose output is validated, not just written
- [ ] **Reconcile:** managed source ref only advances after successful build/apply
- [ ] **Deploy:** project identity is stable and independent of temp directories
- [ ] **Logging:** command outcomes are recorded without leaking secrets

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| checkout advanced too early | reconcile engine | failed candidate does not move last successful state |
| invalid treated as removed | validation + planner | broken config blocks reconcile without teardown |
| unstable project naming | build normalization | repeated deploys target same Compose project |
| secret leakage | build/secrets | plaintext appears only in ephemeral runtime trees |
| untrusted `build.py` execution | trust model/build | dynamic builds are auditable and optionally disable-able |
| ambient env drift | validation/build | cron and interactive runs render the same config |

## Sources

- `.planning/PROJECT.md`
- https://docs.docker.com/reference/cli/docker/compose/config/
- https://docs.docker.com/reference/cli/docker/compose/up/
- https://docs.docker.com/reference/cli/docker/compose/down/
- https://docs.docker.com/compose/how-tos/project-name/
- https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/

---
*Pitfalls research for: Git-driven Docker Compose reconciliation for a single-host Unraid actuator*
*Researched: 2026-04-22*
