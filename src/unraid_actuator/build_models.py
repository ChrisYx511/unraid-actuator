from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildTarget:
    app: str
    environment: str
    output_dir: Path


@dataclass(frozen=True)
class BuildResult:
    output_root: Path
    built_targets: tuple[BuildTarget, ...]


__all__ = ["BuildResult", "BuildTarget"]
