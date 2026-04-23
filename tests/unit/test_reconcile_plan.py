from __future__ import annotations

from pathlib import Path

import pytest

from strictyaml import YAMLValidationError

from unraid_actuator.build_paths import BUILD_MARKER_NAME
from unraid_actuator.reconcile_plan import plan_removed_targets


def test_plan_removed_targets_uses_current_declaration_order(tmp_path: Path) -> None:
    current_host_root = tmp_path / "current"
    incoming_host_root = tmp_path / "incoming"
    _write_apps(
        current_host_root,
        "apps:\n  nextcloud:\n    - production\n  immich:\n    - preview\n  postgres:\n    - production\n",
    )
    _write_apps(
        incoming_host_root,
        "apps:\n  nextcloud:\n    - production\n",
    )
    runtime_root = _write_marked_runtime_tree(
        tmp_path / "build",
        ("postgres", "production"),
        ("immich", "preview"),
        ("nextcloud", "production"),
    )

    plan = plan_removed_targets(
        current_host_root=current_host_root,
        incoming_host_root=incoming_host_root,
        current_runtime_root=runtime_root,
    )

    assert [(item.app, item.environment) for item in plan.removed_declarations] == [
        ("immich", "preview"),
        ("postgres", "production"),
    ]
    assert [(item.app, item.environment) for item in plan.removed_targets] == [
        ("immich", "preview"),
        ("postgres", "production"),
    ]
    assert plan.requires_current_rebuild is False


@pytest.mark.parametrize("mode", ["missing", "unmarked", "malformed"])
def test_plan_removed_targets_requires_rebuild_for_untrusted_runtime_tree(tmp_path: Path, mode: str) -> None:
    current_host_root = tmp_path / "current"
    incoming_host_root = tmp_path / "incoming"
    _write_apps(current_host_root, "apps:\n  immich:\n    - preview\n")
    _write_apps(incoming_host_root, "apps:\n  nextcloud:\n    - production\n")
    runtime_root = tmp_path / "build"

    if mode == "unmarked":
        _write_runtime_target(runtime_root, "immich", "preview")
    elif mode == "malformed":
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / BUILD_MARKER_NAME).write_text("", encoding="utf-8")
        target_dir = runtime_root / "immich" / "preview"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")

    plan = plan_removed_targets(
        current_host_root=current_host_root,
        incoming_host_root=incoming_host_root,
        current_runtime_root=runtime_root,
    )

    assert [(item.app, item.environment) for item in plan.removed_declarations] == [("immich", "preview")]
    assert plan.removed_targets == ()
    assert plan.requires_current_rebuild is True


def test_plan_removed_targets_propagates_invalid_incoming_state(tmp_path: Path) -> None:
    current_host_root = tmp_path / "current"
    incoming_host_root = tmp_path / "incoming"
    _write_apps(current_host_root, "apps:\n  immich:\n    - preview\n")
    incoming_host_root.mkdir(parents=True, exist_ok=True)
    (incoming_host_root / "apps.yaml").write_text("apps:\n  immich:\n    environments:\n      - preview\n", encoding="utf-8")

    with pytest.raises(YAMLValidationError):
        plan_removed_targets(
            current_host_root=current_host_root,
            incoming_host_root=incoming_host_root,
            current_runtime_root=tmp_path / "build",
        )


def _write_apps(host_root: Path, content: str) -> None:
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yaml").write_text(content, encoding="utf-8")


def _write_marked_runtime_tree(build_root: Path, *targets: tuple[str, str]) -> Path:
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / BUILD_MARKER_NAME).write_text("", encoding="utf-8")
    for app, environment in targets:
        _write_runtime_target(build_root, app, environment)
    return build_root


def _write_runtime_target(build_root: Path, app: str, environment: str) -> None:
    target_dir = build_root / app / environment
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (target_dir / ".env").write_text("KEY=value\n", encoding="utf-8")
