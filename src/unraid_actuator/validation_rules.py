import re
from pathlib import Path

from .validation_models import (
    DeclaredEnvironment,
    DiscoveredEnvironment,
    FindingSeverity,
    SourceKind,
    ValidationFinding,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def compose_project_name(app: str, environment: str) -> str:
    if not SLUG_RE.fullmatch(app):
        raise ValueError(f"app name '{app}' must match {SLUG_RE.pattern}")
    if not SLUG_RE.fullmatch(environment):
        raise ValueError(f"environment name '{environment}' must match {SLUG_RE.pattern}")
    return f"{app}-{environment}"


def findings_for_missing_declared(
    host_root: Path, missing: tuple[DeclaredEnvironment, ...]
) -> tuple[ValidationFinding, ...]:
    return tuple(
        ValidationFinding(
            severity=FindingSeverity.ERROR,
            code="DECLARED_MISSING",
            message="Declared app/environment is missing from disk.",
            app=target.app,
            environment=target.environment,
            path=host_root / target.app / target.environment,
        )
        for target in missing
    )


def findings_for_discovered(
    candidate: DiscoveredEnvironment,
) -> tuple[ValidationFinding, ...]:
    if candidate.source_kind in {SourceKind.COMPOSE, SourceKind.TEMPLATE}:
        return ()

    code = "SOURCE_XOR" if candidate.source_kind == SourceKind.AMBIGUOUS else "SOURCE_MISSING"
    message = (
        "Environment must define exactly one supported source: one docker-compose "
        "file or one template descriptor paired with one values file."
        if code == "SOURCE_XOR"
        else "Environment must define docker-compose.yml/docker-compose.yaml or "
        "template.yml/template.yaml with matching values.yml/values.yaml."
    )
    return (
        ValidationFinding(
            severity=_severity(candidate.declared),
            code=code,
            message=message,
            app=candidate.app,
            environment=candidate.environment,
            path=candidate.path,
        ),
    )


def findings_for_project_names(
    discovered: tuple[DiscoveredEnvironment, ...],
    missing: tuple[DeclaredEnvironment, ...],
    host_root: Path,
) -> tuple[ValidationFinding, ...]:
    targets: list[tuple[str, str, bool, Path | None]] = [
        (candidate.app, candidate.environment, candidate.declared, candidate.path) for candidate in discovered
    ]
    targets.extend(
        (
            target.app,
            target.environment,
            True,
            host_root / target.app / target.environment,
        )
        for target in missing
    )

    findings: list[ValidationFinding] = []
    names: dict[str, list[tuple[str, str, bool, Path | None]]] = {}

    for app, environment, declared, path in targets:
        try:
            project_name = compose_project_name(app, environment)
        except ValueError as exc:
            findings.append(
                ValidationFinding(
                    severity=_severity(declared),
                    code="INVALID_PROJECT_NAME",
                    message=str(exc),
                    app=app,
                    environment=environment,
                    path=path,
                )
            )
            continue
        names.setdefault(project_name, []).append((app, environment, declared, path))

    for project_name, collisions in names.items():
        if len(collisions) < 2:
            continue
        for app, environment, declared, path in collisions:
            findings.append(
                ValidationFinding(
                    severity=_severity(declared),
                    code="PROJECT_NAME_COLLISION",
                    message=f"Compose project name '{project_name}' collides with another host target.",
                    app=app,
                    environment=environment,
                    path=path,
                )
            )

    return tuple(findings)


def _severity(declared: bool) -> FindingSeverity:
    return FindingSeverity.ERROR if declared else FindingSeverity.WARNING
