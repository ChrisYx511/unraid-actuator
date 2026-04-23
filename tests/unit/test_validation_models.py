from pathlib import Path

from unraid_actuator.validation_models import (
    DeclaredEnvironment,
    DiscoveredEnvironment,
    FindingSeverity,
    SourceKind,
    ValidationFinding,
    ValidationReport,
)


def test_validation_report_groups_errors_and_warnings() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(severity=FindingSeverity.ERROR, code="E1", message="bad"),
            ValidationFinding(severity=FindingSeverity.WARNING, code="W1", message="warn"),
        ),
        checked_targets=(DeclaredEnvironment(app="app", environment="prod"),),
    )

    assert report.error_count == 1
    assert report.warning_count == 1
    assert report.has_errors is True
    assert report.errors[0].code == "E1"
    assert report.warnings[0].code == "W1"


def test_discovered_environment_preserves_source_classification_fields() -> None:
    candidate = DiscoveredEnvironment(
        app="nextcloud",
        environment="production",
        path=Path("/tmp/nextcloud/production"),
        declared=True,
        source_kind=SourceKind.COMPOSE,
        compose_files=(Path("docker-compose.yml"),),
        template_file=None,
        values_file=None,
    )

    assert candidate.app == "nextcloud"
    assert candidate.environment == "production"
    assert candidate.source_kind == SourceKind.COMPOSE
    assert candidate.compose_files == (Path("docker-compose.yml"),)
    assert candidate.template_file is None
    assert candidate.values_file is None


def test_validation_finding_preserves_scope_and_path() -> None:
    finding = ValidationFinding(
        severity=FindingSeverity.ERROR,
        code="SOURCE_XOR",
        message="ambiguous",
        app="nextcloud",
        environment="production",
        path=Path("/tmp/nextcloud/production"),
    )

    assert finding.code == "SOURCE_XOR"
    assert finding.app == "nextcloud"
    assert finding.environment == "production"
    assert finding.path == Path("/tmp/nextcloud/production")
