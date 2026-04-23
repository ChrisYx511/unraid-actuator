from __future__ import annotations

from .compose_build import normalize_rendered_compose, normalize_static_compose
from .runner import CommandRunner
from .template_render import render_template_environment
from .validation_models import DiscoveredEnvironment, FindingSeverity, ValidationFinding


def validate_static_compose(
    candidate: DiscoveredEnvironment,
    project_name: str,
    *,
    runner: CommandRunner,
) -> tuple[ValidationFinding, ...]:
    try:
        normalize_static_compose(
            source_env_dir=candidate.path,
            compose_file=candidate.compose_files[0],
            project_name=project_name,
            runner=runner,
        )
        return ()
    except ValueError as exc:
        return (_command_failure(candidate, "COMPOSE_CONFIG_FAILED", str(exc)),)


def validate_template_source(
    candidate: DiscoveredEnvironment,
    project_name: str,
    *,
    runner: CommandRunner,
) -> tuple[ValidationFinding, ...]:
    assert candidate.template_file is not None
    assert candidate.values_file is not None
    try:
        rendered = render_template_environment(
            env_root=candidate.path,
            template_path=candidate.template_file,
            values_path=candidate.values_file,
        )
    except ValueError as exc:
        return (_command_failure(candidate, "TEMPLATE_RENDER_FAILED", str(exc)),)

    if not rendered.strip():
        return (
            _command_failure(
                candidate,
                "TEMPLATE_OUTPUT_EMPTY",
                "template rendering produced no Compose YAML output.",
            ),
        )

    try:
        normalize_rendered_compose(
            source_env_dir=candidate.path,
            rendered_text=rendered,
            project_name=project_name,
            runner=runner,
        )
        return ()
    except ValueError as exc:
        return (_command_failure(candidate, "COMPOSE_CONFIG_FAILED", str(exc)),)


def _command_failure(candidate: DiscoveredEnvironment, code: str, message: str) -> ValidationFinding:
    return ValidationFinding(
        severity=FindingSeverity.ERROR if candidate.declared else FindingSeverity.WARNING,
        code=code,
        message=message,
        app=candidate.app,
        environment=candidate.environment,
        path=candidate.path,
    )
