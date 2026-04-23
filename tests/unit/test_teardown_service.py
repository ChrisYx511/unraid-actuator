from pathlib import Path

import pytest

from unraid_actuator.build_paths import BUILD_MARKER_NAME
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.deploy import run_teardown
from unraid_actuator.runner import CommandResult, RecordingRunner


def test_teardown_full_is_ordered_and_fail_fast(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yml").write_text(
        "apps:\n  nextcloud:\n    - production\n  immich:\n    - preview\n",
        encoding="utf-8",
    )
    build_root = _write_marked_runtime_tree(
        tmp_path,
        ("nextcloud", "production"),
        ("immich", "preview"),
    )
    runner = RecordingRunner(
        results=[
            _result(exit_code=0, stdout="stopped"),
            _result(exit_code=1, stderr="down failed"),
        ],
        executed=True,
    )

    with pytest.raises(ValueError, match="teardown failed for immich/preview: down failed"):
        run_teardown(runner=runner, config_path=config_path, build_root=build_root)

    assert [call.argv[-1] for call in runner.calls] == ["down", "down"]
    assert [call.argv[3] for call in runner.calls] == [
        "nextcloud-production",
        "immich-preview",
    ]


def test_teardown_scoped_requires_current_host_valid_target(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / "apps.yaml").write_text("apps:\n  nextcloud:\n    - production\n", encoding="utf-8")
    build_root = _write_marked_runtime_tree(
        tmp_path,
        ("nextcloud", "production"),
        ("oldapp", "legacy"),
    )
    runner = RecordingRunner(results=[_result(exit_code=0, stdout="stopped")], executed=False)

    result = run_teardown(
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
        run_teardown(
            runner=runner,
            config_path=config_path,
            build_root=build_root,
            app="oldapp",
            environment="legacy",
        )


def test_teardown_requires_both_scope_selectors(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)

    with pytest.raises(ValueError, match="--app and --environment must be provided together"):
        run_teardown(runner=RecordingRunner(), config_path=config_path, environment="production")


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
