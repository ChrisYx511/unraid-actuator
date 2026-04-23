# Quick Task 260423-mhh: Standardize YAML extension handling across inputs, outputs, and documentation

## Goal

Make YAML extension handling consistent across the project: accept both `.yaml` and `.yml` for user-provided inputs, fail on duplicate twin files, emit only `.yaml` for actuator-generated files, and update documentation/examples to prefer the full `.yaml` extension.

## Tasks

1. **Standardize runtime output and validation wording**
   - Files: `src/unraid_actuator/build_paths.py`, `src/unraid_actuator/build.py`, `src/unraid_actuator/deploy_tree.py`, `src/unraid_actuator/reconcile_plan.py`, `src/unraid_actuator/discovery.py`, `src/unraid_actuator/validation_rules.py`
   - Action: Centralize the generated Compose filename as `docker-compose.yaml`, keep input discovery tolerant of both extensions, and ensure validation/help text prefers `.yaml` ordering.
   - Verify: Build, deploy, teardown, and reconcile runtime loaders all agree on the generated Compose filename.
   - Done when: Actuator-generated runtime trees contain only `docker-compose.yaml`, and user input resolution still accepts both `.yaml` and `.yml`.

2. **Update tests and documentation to match**
   - Files: `tests/unit/...`, `README.md`, `.planning/**/*.md`
   - Action: Refresh runtime/output assertions, add duplicate-extension coverage, and normalize documentation/examples to `.yaml` while keeping dual-extension acceptance documented where relevant.
   - Verify: Existing tests pass and repo documentation no longer mixes example extensions inconsistently.
   - Done when: Tests encode the new contract clearly and documentation uses `.yaml` consistently for examples and outputs.
