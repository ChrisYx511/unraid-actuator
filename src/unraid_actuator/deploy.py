from collections.abc import Callable
from pathlib import Path

from .build_paths import resolve_output_root
from .compose_runtime import compose_down_spec, compose_up_spec
from .config import ACTIVE_CONFIG_PATH
from .deploy_models import RuntimeActionResult, RuntimeTarget
from .deploy_tree import resolve_full_tree_targets, resolve_scoped_target
from .runner import CommandResult, CommandRunner, CommandSpec


def run_deploy(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
    build_root: Path | None = None,
    app: str | None = None,
    environment: str | None = None,
) -> RuntimeActionResult:
    return _run_runtime_action(
        action_name="deploy",
        default_failure_detail="docker compose up -d failed",
        spec_factory=compose_up_spec,
        runner=runner,
        config_path=config_path,
        build_root=build_root,
        app=app,
        environment=environment,
    )


def run_teardown(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
    build_root: Path | None = None,
    app: str | None = None,
    environment: str | None = None,
) -> RuntimeActionResult:
    return _run_runtime_action(
        action_name="teardown",
        default_failure_detail="docker compose down failed",
        spec_factory=compose_down_spec,
        runner=runner,
        config_path=config_path,
        build_root=build_root,
        app=app,
        environment=environment,
    )


def _run_runtime_action(
    *,
    action_name: str,
    default_failure_detail: str,
    spec_factory: Callable[[RuntimeTarget], CommandSpec],
    runner: CommandRunner,
    config_path: Path,
    build_root: Path | None,
    app: str | None,
    environment: str | None,
) -> RuntimeActionResult:
    if bool(app) != bool(environment):
        raise ValueError("--app and --environment must be provided together")

    resolved_build_root = resolve_output_root(build_root)
    targets = _resolve_targets(
        build_root=resolved_build_root,
        config_path=config_path,
        app=app,
        environment=environment,
    )

    command_results: list[CommandResult] = []
    for target in targets:
        result = runner.run(spec_factory(target))
        command_results.append(result)
        if result.exit_code != 0:
            detail = result.stderr.strip() or result.stdout.strip() or default_failure_detail
            raise ValueError(f"{action_name} failed for {target.app}/{target.environment}: {detail}")

    return RuntimeActionResult(
        build_root=resolved_build_root,
        targets=targets,
        command_results=tuple(command_results),
    )


def _resolve_targets(
    *,
    build_root: Path,
    config_path: Path,
    app: str | None,
    environment: str | None,
) -> tuple[RuntimeTarget, ...]:
    if app is None:
        return resolve_full_tree_targets(build_root=build_root, config_path=config_path)
    return (
        resolve_scoped_target(
            build_root=build_root,
            config_path=config_path,
            app=app,
            environment=environment or "",
        ),
    )


__all__ = ["run_deploy", "run_teardown"]
