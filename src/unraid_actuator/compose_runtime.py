from __future__ import annotations

from .deploy_models import RuntimeTarget
from .runner import CommandSpec
from .validation_rules import compose_project_name


def compose_up_spec(target: RuntimeTarget) -> CommandSpec:
    return _compose_spec(target, "up", "-d")


def compose_down_spec(target: RuntimeTarget) -> CommandSpec:
    return _compose_spec(target, "down")


def _compose_spec(target: RuntimeTarget, *action: str) -> CommandSpec:
    project_name = compose_project_name(target.app, target.environment)
    return CommandSpec(
        argv=(
            "docker",
            "compose",
            "-p",
            project_name,
            "--project-directory",
            str(target.output_dir),
            "--env-file",
            str(target.env_file),
            "-f",
            str(target.compose_file),
            *action,
        ),
        cwd=target.output_dir,
        env={"COMPOSE_REMOVE_ORPHANS": "0"},
        inherit_env=True,
    )


__all__ = ["compose_down_spec", "compose_up_spec"]
