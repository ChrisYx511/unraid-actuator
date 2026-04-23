from __future__ import annotations

from pathlib import Path

from unraid_actuator.validation_models import DeclaredEnvironment, DiscoveredEnvironment, FindingSeverity, SourceKind
from unraid_actuator.validation_rules import (
    compose_project_name,
    findings_for_discovered,
    findings_for_missing_declared,
    findings_for_project_names,
)


def test_declared_missing_or_invalid_targets_are_errors(tmp_path: Path) -> None:
    host_root = tmp_path / "PotatoServer"
    missing = findings_for_missing_declared(
        host_root,
        (DeclaredEnvironment(app="nextcloud", environment="production"),),
    )
    ambiguous = findings_for_discovered(
        DiscoveredEnvironment(
            app="nextcloud",
            environment="production",
            path=host_root / "nextcloud" / "production",
            declared=True,
            source_kind=SourceKind.AMBIGUOUS,
            compose_files=(Path("docker-compose.yml"),),
            template_file=Path("template.yml"),
            values_file=Path("values.yml"),
        )
    )

    assert missing[0].severity == FindingSeverity.ERROR
    assert missing[0].code == "DECLARED_MISSING"
    assert ambiguous[0].severity == FindingSeverity.ERROR
    assert ambiguous[0].code == "SOURCE_XOR"


def test_undeclared_invalid_targets_are_warnings() -> None:
    candidate = DiscoveredEnvironment(
        app="immich",
        environment="preview",
        path=Path("/tmp/immich/preview"),
        declared=False,
        source_kind=SourceKind.MISSING,
        compose_files=(),
        template_file=None,
        values_file=None,
    )

    findings = findings_for_discovered(candidate)

    assert findings[0].severity == FindingSeverity.WARNING
    assert findings[0].code == "SOURCE_MISSING"


def test_invalid_or_ambiguous_project_names_fail() -> None:
    assert compose_project_name("nextcloud", "production") == "nextcloud-production"

    invalid = findings_for_project_names(
        (
            DiscoveredEnvironment(
                app="Nextcloud",
                environment="production",
                path=Path("/tmp/Nextcloud/production"),
                declared=True,
                source_kind=SourceKind.COMPOSE,
                compose_files=(Path("docker-compose.yml"),),
                template_file=None,
                values_file=None,
            ),
        ),
        (),
        Path("/tmp/host"),
    )
    collisions = findings_for_project_names(
        (
            DiscoveredEnvironment(
                app="app",
                environment="one-prod",
                path=Path("/tmp/app/one-prod"),
                declared=True,
                source_kind=SourceKind.COMPOSE,
                compose_files=(Path("docker-compose.yml"),),
                template_file=None,
                values_file=None,
            ),
            DiscoveredEnvironment(
                app="app-one",
                environment="prod",
                path=Path("/tmp/app-one/prod"),
                declared=True,
                source_kind=SourceKind.COMPOSE,
                compose_files=(Path("docker-compose.yml"),),
                template_file=None,
                values_file=None,
            ),
        ),
        (),
        Path("/tmp/host"),
    )

    assert invalid[0].code == "INVALID_PROJECT_NAME"
    assert {finding.code for finding in collisions} == {"PROJECT_NAME_COLLISION"}
    assert len(collisions) == 2
