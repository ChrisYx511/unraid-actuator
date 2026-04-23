from __future__ import annotations

from pathlib import Path

from .runner import CommandRunner, CommandSpec

_COMPOSE_ENV = {"COMPOSE_DISABLE_ENV_FILE": "1"}


def normalize_static_compose(
    *,
    source_env_dir: Path,
    compose_file: Path,
    project_name: str,
    runner: CommandRunner,
) -> str:
    result = runner.run(
        CommandSpec(
            argv=(
                "docker",
                "compose",
                "-p",
                project_name,
                "--project-directory",
                str(source_env_dir),
                "-f",
                compose_file.name,
                "config",
                "--no-interpolate",
                "--format",
                "yaml",
            ),
            cwd=source_env_dir,
            env=_COMPOSE_ENV,
            inherit_env=False,
        )
    )
    if result.exit_code != 0:
        raise ValueError(result.stderr or result.stdout or "Compose normalization failed.")
    if not result.executed:
        return compose_file.read_text(encoding="utf-8")
    return result.stdout


def normalize_rendered_compose(
    *,
    source_env_dir: Path,
    rendered_text: str,
    project_name: str,
    runner: CommandRunner,
) -> str:
    result = runner.run(
        CommandSpec(
            argv=(
                "docker",
                "compose",
                "-p",
                project_name,
                "--project-directory",
                str(source_env_dir),
                "-f",
                "-",
                "config",
                "--no-interpolate",
                "--format",
                "yaml",
            ),
            cwd=source_env_dir,
            env=_COMPOSE_ENV,
            stdin_text=rendered_text,
            inherit_env=False,
        )
    )
    if result.exit_code != 0:
        raise ValueError(result.stderr or result.stdout or "Compose normalization failed.")
    if not result.executed:
        return rendered_text
    return result.stdout


__all__ = ["normalize_rendered_compose", "normalize_static_compose"]
