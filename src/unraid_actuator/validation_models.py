from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FindingSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class SourceKind(StrEnum):
    COMPOSE = "compose"
    TEMPLATE = "template"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class DeclaredEnvironment:
    app: str
    environment: str


@dataclass(frozen=True)
class DiscoveredEnvironment:
    app: str
    environment: str
    path: Path
    declared: bool
    source_kind: SourceKind
    compose_files: tuple[Path, ...]
    template_file: Path | None
    values_file: Path | None


@dataclass(frozen=True)
class ValidationFinding:
    severity: FindingSeverity
    code: str
    message: str
    app: str | None = None
    environment: str | None = None
    path: Path | None = None


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[ValidationFinding, ...]
    checked_targets: tuple[DeclaredEnvironment, ...]

    @property
    def errors(self) -> tuple[ValidationFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == FindingSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == FindingSeverity.WARNING)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0


__all__ = [
    "DeclaredEnvironment",
    "DiscoveredEnvironment",
    "FindingSeverity",
    "SourceKind",
    "ValidationFinding",
    "ValidationReport",
]
