from pathlib import Path

from .deploy_models import RuntimeTarget
from .deploy_tree import require_marked_runtime_tree
from .reconcile_models import RemovedTargetsPlan
from .schemas import load_declared_environments
from .validation_models import DeclaredEnvironment


def plan_removed_targets(
    *,
    current_host_root: Path,
    incoming_host_root: Path,
    current_runtime_root: Path,
) -> RemovedTargetsPlan:
    current_declared = load_declared_environments(current_host_root)
    incoming_keys = {(target.app, target.environment) for target in load_declared_environments(incoming_host_root)}
    removed = tuple(target for target in current_declared if (target.app, target.environment) not in incoming_keys)
    if not removed:
        return RemovedTargetsPlan(
            removed_declarations=(),
            removed_targets=(),
            requires_current_rebuild=False,
        )

    try:
        removed_targets = _resolve_removed_targets(current_runtime_root, removed)
    except ValueError:
        return RemovedTargetsPlan(
            removed_declarations=removed,
            removed_targets=(),
            requires_current_rebuild=True,
        )

    return RemovedTargetsPlan(
        removed_declarations=removed,
        removed_targets=removed_targets,
        requires_current_rebuild=False,
    )


def _resolve_removed_targets(
    current_runtime_root: Path,
    removed: tuple[DeclaredEnvironment, ...],
) -> tuple[RuntimeTarget, ...]:
    build_root = require_marked_runtime_tree(current_runtime_root)
    return tuple(
        _load_removed_target(build_root=build_root, app=target.app, environment=target.environment)
        for target in removed
    )


def _load_removed_target(
    *,
    build_root: Path,
    app: str,
    environment: str,
) -> RuntimeTarget:
    target_dir = build_root / app / environment
    compose_file = target_dir / "docker-compose.yml"
    env_file = target_dir / ".env"
    if not target_dir.is_dir() or not compose_file.is_file() or not env_file.is_file():
        raise ValueError(f"runtime target is malformed: {app}/{environment}")
    return RuntimeTarget(
        app=app,
        environment=environment,
        output_dir=target_dir,
        compose_file=compose_file,
        env_file=env_file,
    )


__all__ = ["plan_removed_targets"]
