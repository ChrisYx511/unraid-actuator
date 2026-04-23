from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

DEFAULT_BUILD_ROOT = Path("/tmp/unraid-actuator/build")
BUILD_MARKER_NAME = ".UNRAID_RUNNING_CONFIGURATION"


def resolve_output_root(output_root: Path | None) -> Path:
    return output_root if output_root is not None else DEFAULT_BUILD_ROOT


def validate_output_root(final_root: Path) -> None:
    if final_root == DEFAULT_BUILD_ROOT:
        if final_root.exists() and not final_root.is_dir():
            raise ValueError(f"build output path must be a directory: {final_root}")
        return

    if not final_root.exists():
        return
    if not final_root.is_dir():
        raise ValueError(f"custom build output path must be empty before build: {final_root}")
    if any(final_root.iterdir()):
        raise ValueError(f"custom build output path must be empty before build: {final_root}")


def create_stage_root(final_root: Path) -> Path:
    final_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{final_root.name}-staging-", dir=final_root.parent))


def promote_runtime_root(stage_root: Path, final_root: Path) -> None:
    if final_root.exists():
        if final_root.is_dir():
            shutil.rmtree(final_root)
        else:
            final_root.unlink()
    final_root.parent.mkdir(parents=True, exist_ok=True)
    stage_root.replace(final_root)


__all__ = [
    "BUILD_MARKER_NAME",
    "DEFAULT_BUILD_ROOT",
    "create_stage_root",
    "promote_runtime_root",
    "resolve_output_root",
    "validate_output_root",
]
