from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .deploy_models import RuntimeTarget
from .validation_models import DeclaredEnvironment


class ReconcileStatus(StrEnum):
    NOOP = "noop"
    DRY_RUN = "dry-run"
    APPLIED = "applied"


@dataclass(frozen=True)
class ManagedCheckoutState:
    current_sha: str
    candidate_sha: str
    source_path: Path
    branch: str


@dataclass(frozen=True)
class CandidateWorkspace:
    checkout_root: Path
    host_root: Path
    build_root: Path
    candidate_sha: str


@dataclass(frozen=True)
class RemovedTargetsPlan:
    removed_declarations: tuple[DeclaredEnvironment, ...]
    removed_targets: tuple[RuntimeTarget, ...]
    requires_current_rebuild: bool


@dataclass(frozen=True)
class ReconcileResult:
    status: ReconcileStatus
    current_sha: str
    candidate_sha: str | None
    dry_run: bool
    removed_targets: tuple[RuntimeTarget, ...]
    requires_current_rebuild: bool = False
    detail: str | None = None
    log_path: Path | None = None


__all__ = [
    "CandidateWorkspace",
    "ManagedCheckoutState",
    "ReconcileResult",
    "ReconcileStatus",
    "RemovedTargetsPlan",
]
