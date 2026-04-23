from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator.compose_build import normalize_rendered_compose, normalize_static_compose
from unraid_actuator.runner import CommandResult, RecordingRunner


def test_normalize_static_compose_uses_no_interpolate_and_scrubbed_env(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    compose_file = env_root / "docker-compose.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    runner = RecordingRunner(
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=False,
                exit_code=0,
                stdout="services: {}\n",
                stderr="",
                executed=True,
            )
        ]
    )

    output = normalize_static_compose(
        source_env_dir=env_root,
        compose_file=compose_file,
        project_name="nextcloud-production",
        runner=runner,
    )

    assert output == "services: {}\n"
    assert runner.calls[0].argv == (
        "docker",
        "compose",
        "-p",
        "nextcloud-production",
        "--project-directory",
        str(env_root),
        "-f",
        "docker-compose.yml",
        "config",
        "--no-interpolate",
        "--format",
        "yaml",
    )
    assert runner.calls[0].env == {"COMPOSE_DISABLE_ENV_FILE": "1"}
    assert runner.calls[0].inherit_env is False


def test_normalize_rendered_compose_uses_stdin(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    runner = RecordingRunner(
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=False,
                exit_code=0,
                stdout="services: {}\n",
                stderr="",
                executed=True,
            )
        ]
    )

    output = normalize_rendered_compose(
        source_env_dir=env_root,
        rendered_text="services:\n  app:\n    image: busybox\n",
        project_name="nextcloud-production",
        runner=runner,
    )

    assert output == "services: {}\n"
    assert runner.calls[0].stdin_text == "services:\n  app:\n    image: busybox\n"


def test_compose_normalize_failures_raise_value_error(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    compose_file = env_root / "docker-compose.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    runner = RecordingRunner(
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=False,
                exit_code=1,
                stdout="",
                stderr="bad compose",
                executed=True,
            )
        ]
    )

    with pytest.raises(ValueError, match="bad compose"):
        normalize_static_compose(
            source_env_dir=env_root,
            compose_file=compose_file,
            project_name="nextcloud-production",
            runner=runner,
        )
