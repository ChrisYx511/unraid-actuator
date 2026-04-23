from pathlib import Path

from .build_paths import BUILD_MARKER_NAME, RUNTIME_COMPOSE_FILENAME
from .config import ACTIVE_CONFIG_PATH, load_active_config
from .deploy_models import RuntimeTarget
from .schemas import load_declared_environments


def require_marked_runtime_tree(build_root: Path) -> Path:
    if not build_root.exists():
        raise ValueError(f"build root does not exist: {build_root}")
    if not build_root.is_dir():
        raise ValueError(f"build root must be a directory: {build_root}")
    marker = build_root / BUILD_MARKER_NAME
    if not marker.is_file():
        raise ValueError(f"build root is not an actuator-managed runtime tree: {build_root}")
    return build_root


def resolve_full_tree_targets(
    *,
    build_root: Path,
    config_path: Path = ACTIVE_CONFIG_PATH,
) -> tuple[RuntimeTarget, ...]:
    build_root = require_marked_runtime_tree(build_root)
    targets_by_key = _load_runtime_targets(build_root)
    declared_keys = _declared_keys(config_path=config_path)

    ordered_targets: list[RuntimeTarget] = []
    seen: set[tuple[str, str]] = set()
    for key in declared_keys:
        target = targets_by_key.get(key)
        if target is None:
            continue
        ordered_targets.append(target)
        seen.add(key)

    for key in sorted(targets_by_key):
        if key in seen:
            continue
        ordered_targets.append(targets_by_key[key])

    return tuple(ordered_targets)


def resolve_scoped_target(
    *,
    build_root: Path,
    config_path: Path = ACTIVE_CONFIG_PATH,
    app: str,
    environment: str,
) -> RuntimeTarget:
    build_root = require_marked_runtime_tree(build_root)
    key = (app, environment)
    declared_keys = set(_declared_keys(config_path=config_path))
    if key not in declared_keys:
        raise ValueError(f"scoped target is not declared for current host: {app}/{environment}")

    target_dir = build_root / app / environment
    if not target_dir.is_dir():
        raise ValueError(f"scoped target is not present in build root: {app}/{environment}")

    return _load_runtime_target(target_dir, app=app, environment=environment)


def _declared_keys(*, config_path: Path) -> tuple[tuple[str, str], ...]:
    config = load_active_config(path=config_path)
    host_root = config.source_path / config.hostname
    return tuple((item.app, item.environment) for item in load_declared_environments(host_root))


def _load_runtime_targets(build_root: Path) -> dict[tuple[str, str], RuntimeTarget]:
    targets: dict[tuple[str, str], RuntimeTarget] = {}
    for app_dir in sorted(path for path in build_root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        for env_dir in sorted(path for path in app_dir.iterdir() if path.is_dir() and not path.name.startswith(".")):
            key = (app_dir.name, env_dir.name)
            targets[key] = _load_runtime_target(env_dir, app=app_dir.name, environment=env_dir.name)
    return targets


def _load_runtime_target(target_dir: Path, *, app: str, environment: str) -> RuntimeTarget:
    compose_file = target_dir / RUNTIME_COMPOSE_FILENAME
    env_file = target_dir / ".env"
    if not compose_file.is_file() or not env_file.is_file():
        raise ValueError(f"runtime target is malformed: {app}/{environment}")
    return RuntimeTarget(
        app=app,
        environment=environment,
        output_dir=target_dir,
        compose_file=compose_file,
        env_file=env_file,
    )


__all__ = [
    "require_marked_runtime_tree",
    "resolve_full_tree_targets",
    "resolve_scoped_target",
]
