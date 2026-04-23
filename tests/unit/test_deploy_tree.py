from pathlib import Path

import pytest

from unraid_actuator.build_paths import BUILD_MARKER_NAME
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.deploy_tree import (
    require_marked_runtime_tree,
    resolve_full_tree_targets,
    resolve_scoped_target,
)


def test_full_tree_targets_preserve_declared_order_and_append_stale_targets(
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yml").write_text(
        "apps:\n  nextcloud:\n    - production\n  immich:\n    - preview\n",
        encoding="utf-8",
    )
    build_root = _write_marked_runtime_tree(
        tmp_path,
        ("immich", "preview"),
        ("oldapp", "legacy"),
        ("nextcloud", "production"),
    )

    targets = resolve_full_tree_targets(build_root=build_root, config_path=config_path)

    assert [(target.app, target.environment) for target in targets] == [
        ("nextcloud", "production"),
        ("immich", "preview"),
        ("oldapp", "legacy"),
    ]


def test_scoped_target_must_exist_and_still_be_declared(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yaml").write_text(
        "apps:\n  nextcloud:\n    - production\n",
        encoding="utf-8",
    )
    build_root = _write_marked_runtime_tree(
        tmp_path,
        ("nextcloud", "production"),
        ("oldapp", "legacy"),
    )

    target = resolve_scoped_target(
        build_root=build_root,
        config_path=config_path,
        app="nextcloud",
        environment="production",
    )

    assert target.output_dir == build_root / "nextcloud" / "production"

    with pytest.raises(ValueError, match="not declared for current host: oldapp/legacy"):
        resolve_scoped_target(
            build_root=build_root,
            config_path=config_path,
            app="oldapp",
            environment="legacy",
        )


def test_runtime_tree_must_be_marked_and_well_formed(tmp_path: Path) -> None:
    unmarked_root = tmp_path / "unmarked"
    unmarked_root.mkdir()

    with pytest.raises(ValueError, match="not an actuator-managed runtime tree"):
        require_marked_runtime_tree(unmarked_root)

    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yaml").write_text("apps:\n  nextcloud:\n    - production\n", encoding="utf-8")
    malformed_root = _write_marked_runtime_tree(tmp_path, ("nextcloud", "production"), root_name="malformed")
    (malformed_root / "nextcloud" / "production" / ".env").unlink()

    with pytest.raises(ValueError, match="runtime target is malformed: nextcloud/production"):
        resolve_full_tree_targets(build_root=malformed_root, config_path=config_path)


def _write_active_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "actuator-cfg.yml"
    save_active_config(
        ActiveConfig(
            repo_url="https://example.com/infrastructure.git",
            deploy_branch="deploy",
            hostname="PotatoServer",
            source_path=tmp_path / "source",
        ),
        path=config_path,
    )
    return config_path


def _write_marked_runtime_tree(
    tmp_path: Path,
    *targets: tuple[str, str],
    root_name: str = "build",
) -> Path:
    build_root = tmp_path / root_name
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / BUILD_MARKER_NAME).write_text("", encoding="utf-8")
    for app, environment in targets:
        target_dir = build_root / app / environment
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        (target_dir / ".env").write_text("KEY=value\n", encoding="utf-8")
    return build_root
