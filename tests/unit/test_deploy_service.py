from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator import build_paths
from unraid_actuator.build_paths import BUILD_MARKER_NAME
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.deploy import run_deploy
from unraid_actuator.runner import CommandResult, RecordingRunner


def test_deploy_full_is_ordered_and_fail_fast(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
        ("nextcloud", "production"),
    )
    monkeypatch.setattr(build_paths, "DEFAULT_BUILD_ROOT", build_root)
    runner = RecordingRunner(
        results=[
            _result(exit_code=0, stdout="started"),
            _result(exit_code=1, stderr="compose broke"),
        ],
        executed=True,
    )

    with pytest.raises(ValueError, match="deploy failed for immich/preview: compose broke"):
        run_deploy(runner=runner, config_path=config_path)

    assert [call.argv[-2:] for call in runner.calls] == [("up", "-d"), ("up", "-d")]
    assert [call.argv[3] for call in runner.calls] == ["nextcloud-production", "immich-preview"]


def test_deploy_scoped_requires_current_host_valid_target(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yaml").write_text("apps:\n  nextcloud:\n    - production\n", encoding="utf-8")
    build_root = _write_marked_runtime_tree(
        tmp_path,
        ("nextcloud", "production"),
        ("oldapp", "legacy"),
    )
    runner = RecordingRunner(results=[_result(exit_code=0, stdout="started")], executed=False)

    result = run_deploy(
        runner=runner,
        config_path=config_path,
        build_root=build_root,
        app="nextcloud",
        environment="production",
    )

    assert [(target.app, target.environment) for target in result.targets] == [("nextcloud", "production")]
    assert len(runner.calls) == 1
    assert runner.calls[0].argv[3] == "nextcloud-production"

    with pytest.raises(ValueError, match="not declared for current host: oldapp/legacy"):
        run_deploy(
            runner=runner,
            config_path=config_path,
            build_root=build_root,
            app="oldapp",
            environment="legacy",
        )


def test_deploy_requires_both_scope_selectors(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)

    with pytest.raises(ValueError, match="--app and --environment must be provided together"):
        run_deploy(runner=RecordingRunner(), config_path=config_path, app="nextcloud")


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


def _write_marked_runtime_tree(tmp_path: Path, *targets: tuple[str, str]) -> Path:
    build_root = tmp_path / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / BUILD_MARKER_NAME).write_text("", encoding="utf-8")
    for app, environment in targets:
        target_dir = build_root / app / environment
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        (target_dir / ".env").write_text("KEY=value\n", encoding="utf-8")
    return build_root


def _result(*, exit_code: int, stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(
        argv=(),
        cwd=None,
        env={},
        stdin_text=None,
        inherit_env=True,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        executed=True,
    )
