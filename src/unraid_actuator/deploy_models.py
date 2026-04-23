from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .runner import CommandResult


@dataclass(frozen=True)
class RuntimeTarget:
    app: str
    environment: str
    output_dir: Path
    compose_file: Path
    env_file: Path


@dataclass(frozen=True)
class RuntimeActionResult:
    build_root: Path
    targets: tuple[RuntimeTarget, ...]
    command_results: tuple[CommandResult, ...]


__all__ = ["RuntimeActionResult", "RuntimeTarget"]
