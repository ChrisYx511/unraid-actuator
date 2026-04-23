from unraid_actuator.report import render_validation_report
from unraid_actuator.validation_models import (
    DeclaredEnvironment,
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
)


def test_report_renderer_groups_sections_even_when_one_is_empty() -> None:
    report = ValidationReport(
        findings=(),
        checked_targets=(DeclaredEnvironment(app="nextcloud", environment="production"),),
    )

    rendered = render_validation_report(report, hostname="PotatoServer")

    assert "Errors (0)" in rendered
    assert "Warnings (0)" in rendered
    assert "- none" in rendered


def test_report_renderer_includes_scope_and_summary_counts() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                severity=FindingSeverity.ERROR,
                code="SOURCE_XOR",
                message="ambiguous source",
                app="nextcloud",
                environment="production",
            ),
            ValidationFinding(
                severity=FindingSeverity.WARNING,
                code="SOURCE_MISSING",
                message="missing source",
                app="immich",
                environment="preview",
            ),
        ),
        checked_targets=(
            DeclaredEnvironment(app="nextcloud", environment="production"),
            DeclaredEnvironment(app="immich", environment="preview"),
        ),
    )

    rendered = render_validation_report(report, hostname="PotatoServer")

    assert "- [nextcloud/production] SOURCE_XOR: ambiguous source" in rendered
    assert "- [immich/preview] SOURCE_MISSING: missing source" in rendered
    assert "Summary: checked=2 errors=1 warnings=1" in rendered
