# Requirements: unraid-actuator

**Defined:** 2026-04-22
**Core Value:** The running Docker Compose state for one Unraid host can be reconciled to Git safely, predictably, and without applying invalid or ambiguous configuration.

## v1 Requirements

Requirements for the initial release. These define the committed scope for the first roadmap.

### Initialization & Configuration

- [ ] **INIT-01**: Operator can initialize the actuator with infrastructure repository URL, deploy branch, hostname, and managed source path
- [ ] **INIT-02**: Operator can initialize the actuator into a missing source directory and the command creates required folders automatically
- [ ] **INIT-03**: Operator can initialize without recloning when the managed source directory is already non-empty
- [ ] **INIT-04**: Operator can persist active actuator settings to `/tmp/actuator-cfg.yml`

### Discovery & Validation

- [ ] **VAL-01**: Operator can validate all host configurations in the managed source tree
- [ ] **VAL-02**: Operator can validate a single app/environment when both app and environment are specified
- [ ] **VAL-03**: Operator receives a validation failure when an environment contains both `docker-compose.y[a]ml` and `build.py`
- [ ] **VAL-04**: Operator receives a validation failure when an app/environment declared in `apps.yaml` is missing or invalid
- [ ] **VAL-05**: Operator receives a warning, not a failure, when an undeclared app/environment exists but is invalid
- [ ] **VAL-06**: Operator can validate dynamically generated Compose output by piping `build.py` output through `docker compose config -f -`
- [ ] **VAL-07**: Operator receives schema-driven validation errors for malformed `apps.yaml` or actuator config files parsed with `strictyaml`
- [ ] **VAL-08**: Operator receives a validation failure when compose project naming inputs are invalid or ambiguous for a managed app/environment

### Build & Secrets

- [ ] **BLD-01**: Operator can build all current host app/environment configurations into `/tmp/unraid-actuator/build` by default
- [ ] **BLD-02**: Operator can build into a custom output path only when that path is empty before the build starts
- [ ] **BLD-03**: Operator receives a safe failure when a non-default build output path is non-empty
- [ ] **BLD-04**: Operator gets a normalized `docker-compose.yml` for every built environment regardless of whether the source came from a static Compose file or `build.py`
- [ ] **BLD-05**: Operator gets a merged `.env` file per built environment that combines decrypted secret values with non-secret `.env` data
- [ ] **BLD-06**: Operator gets a build failure when required secret decryption cannot complete for the selected host
- [ ] **BLD-07**: Operator gets a build marker file named `.UNRAID_RUNNING_CONFIGURATION` at the root of each successful build tree

### Deploy & Teardown

- [ ] **DEP-01**: Operator can deploy a full build tree only when it is marked as an actuator-generated running configuration
- [ ] **DEP-02**: Operator can deploy a single app/environment only when both selectors are provided and that target is valid for the current host
- [ ] **DEP-03**: Operator can tear down a full build tree or a single valid app/environment from the built configuration
- [ ] **DEP-04**: Operator receives safe argument handling when only one of app or environment is provided

### Reconciliation

- [ ] **REC-01**: Operator can run reconcile and get a no-op success when the configured deploy branch has no new commits
- [ ] **REC-02**: Operator can reconcile against a fetched candidate commit without mutating the managed source checkout first
- [ ] **REC-03**: Operator gets a reconcile failure when the incoming candidate configuration is invalid
- [ ] **REC-04**: Operator can tear down app/environments removed from the declared host state
- [ ] **REC-05**: Operator can apply the current desired host state by running `docker compose up` against the generated runtime tree
- [ ] **REC-06**: Operator only advances the managed source tree to the new commit after a successful build and apply sequence

### Observability & Testability

- [ ] **OPS-01**: Operator gets `reconcile started` and `reconcile complete` lifecycle events in syslog
- [ ] **OPS-02**: Operator gets reconcile failures reported to syslog and Unraid notifications
- [ ] **OPS-03**: Operator gets reconcile log files, including compose apply output, written under `/var/log/unraid-actuator/`
- [ ] **OPS-04**: Operator can inspect or simulate external command execution through a dry-run-friendly command runner architecture

### Packaging & Developer Experience

- [ ] **PKG-01**: Developer can build the project as a distributable Python package with `uv build`
- [ ] **PKG-02**: Developer can import core actuator functionality from another `uv` project after installation
- [ ] **PKG-03**: Developer can run unit tests that verify planning and command orchestration behavior without requiring live Docker, Git, or EJSON binaries for most cases

## v2 Requirements

Deferred until the core lifecycle is proven.

### Hardening

- **HARD-01**: Operator can require services to become running or healthy before deploy/reconcile is marked successful
- **HARD-02**: Operator receives policy warnings or failures for dangerous Compose settings such as privileged containers or risky host mounts
- **HARD-03**: Operator can inspect structured machine-readable reconcile reports in addition to plain log files

### Recovery & Extensibility

- **EXT-01**: Operator can roll back to the last successful deployment state with an explicit rollback workflow
- **EXT-02**: Operator can use secret backends beyond host-root `secret-env.ejson`

## Out of Scope

Explicitly excluded from the initial milestone.

| Feature | Reason |
|---------|--------|
| Multi-host orchestration from one actuator instance | Each installation is intentionally single-host to keep reconciliation safe and predictable |
| Non-Docker-Compose deployment targets | The runtime contract for v1 is specifically `docker compose` on Unraid |
| Implicit success gates based on container health | Deferred to v2 so the first release can ship a simpler, explicit success model |

## Traceability

Which phases cover which requirements. This section is updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INIT-01 | TBD | Pending |
| INIT-02 | TBD | Pending |
| INIT-03 | TBD | Pending |
| INIT-04 | TBD | Pending |
| VAL-01 | TBD | Pending |
| VAL-02 | TBD | Pending |
| VAL-03 | TBD | Pending |
| VAL-04 | TBD | Pending |
| VAL-05 | TBD | Pending |
| VAL-06 | TBD | Pending |
| VAL-07 | TBD | Pending |
| VAL-08 | TBD | Pending |
| BLD-01 | TBD | Pending |
| BLD-02 | TBD | Pending |
| BLD-03 | TBD | Pending |
| BLD-04 | TBD | Pending |
| BLD-05 | TBD | Pending |
| BLD-06 | TBD | Pending |
| BLD-07 | TBD | Pending |
| DEP-01 | TBD | Pending |
| DEP-02 | TBD | Pending |
| DEP-03 | TBD | Pending |
| DEP-04 | TBD | Pending |
| REC-01 | TBD | Pending |
| REC-02 | TBD | Pending |
| REC-03 | TBD | Pending |
| REC-04 | TBD | Pending |
| REC-05 | TBD | Pending |
| REC-06 | TBD | Pending |
| OPS-01 | TBD | Pending |
| OPS-02 | TBD | Pending |
| OPS-03 | TBD | Pending |
| OPS-04 | TBD | Pending |
| PKG-01 | TBD | Pending |
| PKG-02 | TBD | Pending |
| PKG-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 0
- Unmapped: 36 ⚠️

---
*Requirements defined: 2026-04-22*
*Last updated: 2026-04-22 after initial definition*
