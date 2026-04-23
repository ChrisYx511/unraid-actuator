from collections import defaultdict
from pathlib import Path

from .compose_validation import validate_static_compose, validate_template_source
from .config import ACTIVE_CONFIG_PATH, load_active_config
from .discovery import discover_host_tree, find_missing_declared_environments
from .runner import CommandRunner
from .schemas import load_declared_environments, validate_secret_env_structure
from .validation_models import (
    DeclaredEnvironment,
    DiscoveredEnvironment,
    FindingSeverity,
    SourceKind,
    ValidationFinding,
    ValidationReport,
)
from .validation_rules import (
    compose_project_name,
    findings_for_discovered,
    findings_for_missing_declared,
    findings_for_project_names,
)


def run_validate(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
    app: str | None = None,
    environment: str | None = None,
) -> ValidationReport:
    config = load_active_config(path=config_path)
    return run_validate_for_host(
        runner=runner,
        host_root=config.source_path / config.hostname,
        app=app,
        environment=environment,
    )


def run_validate_for_host(
    *,
    runner: CommandRunner,
    host_root: Path,
    app: str | None = None,
    environment: str | None = None,
) -> ValidationReport:
    declared = load_declared_environments(host_root)

    checked_targets = _full_checked_targets(declared, ())
    host_findings: list[ValidationFinding] = []
    try:
        validate_secret_env_structure(host_root / "secret-env.ejson")
    except ValueError as exc:
        host_findings.append(
            ValidationFinding(
                severity=FindingSeverity.ERROR,
                code="INVALID_SECRET_ENV",
                message=str(exc),
                path=host_root / "secret-env.ejson",
            )
        )

    discovered = discover_host_tree(host_root, declared)
    missing_declared = find_missing_declared_environments(host_root, declared)
    checked_targets = _full_checked_targets(declared, discovered)

    per_target_findings: dict[tuple[str, str], list[ValidationFinding]] = defaultdict(list)
    for finding in findings_for_missing_declared(host_root, missing_declared):
        per_target_findings[(finding.app or "", finding.environment or "")].append(finding)
    for candidate in discovered:
        per_target_findings[(candidate.app, candidate.environment)].extend(findings_for_discovered(candidate))
    for finding in findings_for_project_names(discovered, missing_declared, host_root):
        per_target_findings[(finding.app or "", finding.environment or "")].append(finding)

    selected_key = (app, environment) if app and environment else None
    if selected_key is not None:
        known_targets = {(target.app, target.environment) for target in checked_targets}
        if selected_key not in known_targets:
            assert app is not None
            assert environment is not None
            return ValidationReport(
                findings=tuple(
                    host_findings
                    + [
                        ValidationFinding(
                            severity=FindingSeverity.ERROR,
                            code="TARGET_NOT_FOUND",
                            message="Selected app/environment was not found in the configured host tree.",
                            app=app,
                            environment=environment,
                            path=host_root / app / environment,
                        )
                    ]
                ),
                checked_targets=(DeclaredEnvironment(app=app, environment=environment),),
            )

    findings: list[ValidationFinding] = list(host_findings)
    findings.extend(_selected_target_findings(per_target_findings, selected_key))

    candidates_by_key = {(candidate.app, candidate.environment): candidate for candidate in discovered}
    preflight_keys = _preflight_keys(checked_targets, selected_key)
    for key in preflight_keys:
        candidate = candidates_by_key.get((key.app, key.environment))
        if candidate is None:
            continue
        if per_target_findings.get((candidate.app, candidate.environment)):
            continue
        findings.extend(_preflight_findings(candidate, runner=runner))

    return ValidationReport(
        findings=tuple(findings),
        checked_targets=(DeclaredEnvironment(app=app, environment=environment),)
        if app and environment
        else checked_targets,
    )


def _full_checked_targets(
    declared: tuple[DeclaredEnvironment, ...],
    discovered: tuple[DiscoveredEnvironment, ...],
) -> tuple[DeclaredEnvironment, ...]:
    ordered: dict[tuple[str, str], DeclaredEnvironment] = {
        (target.app, target.environment): target for target in declared
    }
    for candidate in sorted(discovered, key=lambda item: (item.app, item.environment)):
        ordered.setdefault(
            (candidate.app, candidate.environment),
            DeclaredEnvironment(app=candidate.app, environment=candidate.environment),
        )
    return tuple(ordered.values())


def _selected_target_findings(
    per_target_findings: dict[tuple[str, str], list[ValidationFinding]],
    selected_key: tuple[str, str] | None,
) -> list[ValidationFinding]:
    if selected_key is None:
        ordered_keys = sorted(per_target_findings)
        findings: list[ValidationFinding] = []
        for key in ordered_keys:
            findings.extend(per_target_findings[key])
        return findings
    return list(per_target_findings.get(selected_key, ()))


def _preflight_keys(
    checked_targets: tuple[DeclaredEnvironment, ...],
    selected_key: tuple[str, str] | None,
) -> tuple[DeclaredEnvironment, ...]:
    if selected_key is None:
        return checked_targets
    for target in checked_targets:
        if (target.app, target.environment) == selected_key:
            return (target,)
    return ()


def _preflight_findings(candidate: DiscoveredEnvironment, *, runner: CommandRunner) -> tuple[ValidationFinding, ...]:
    project_name = compose_project_name(candidate.app, candidate.environment)
    if candidate.source_kind == SourceKind.COMPOSE:
        return validate_static_compose(candidate, project_name, runner=runner)
    if candidate.source_kind == SourceKind.TEMPLATE:
        return validate_template_source(candidate, project_name, runner=runner)
    return ()


__all__ = ["run_validate", "run_validate_for_host"]
