from __future__ import annotations

from .validation_models import ValidationFinding, ValidationReport


def render_validation_report(report: ValidationReport, *, hostname: str) -> str:
    lines = [f"Validation report for {hostname}", "", f"Errors ({report.error_count})"]
    lines.extend(_render_findings(report.errors))
    lines.extend(["", f"Warnings ({report.warning_count})"])
    lines.extend(_render_findings(report.warnings))
    lines.extend(
        [
            "",
            f"Summary: checked={len(report.checked_targets)} errors={report.error_count} warnings={report.warning_count}",
        ]
    )
    return "\n".join(lines)


def _render_findings(findings: tuple[ValidationFinding, ...]) -> list[str]:
    if not findings:
        return ["- none"]

    rendered: list[str] = []
    for finding in findings:
        scope = ""
        if finding.app and finding.environment:
            scope = f"[{finding.app}/{finding.environment}] "
        rendered.append(f"- {scope}{finding.code}: {finding.message}")
    return rendered
