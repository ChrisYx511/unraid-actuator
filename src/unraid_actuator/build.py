import shutil
from pathlib import Path

from .build_models import BuildResult, BuildTarget
from .build_paths import (
    BUILD_MARKER_NAME,
    create_stage_root,
    promote_runtime_root,
    resolve_output_root,
    validate_output_root,
)
from .compose_build import normalize_rendered_compose, normalize_static_compose
from .config import ACTIVE_CONFIG_PATH, load_active_config
from .discovery import discover_host_tree
from .env_materialize import materialize_env_file
from .runner import CommandRunner, DryRunRunner
from .schemas import load_declared_environments
from .secrets import decrypt_secret_env, extract_environment_secrets
from .template_render import render_template_environment
from .validate import run_validate_for_host
from .validation_models import SourceKind, ValidationReport
from .validation_rules import compose_project_name


def run_build(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
    output_root: Path | None = None,
) -> BuildResult:
    config = load_active_config(path=config_path)
    return run_build_for_host(
        runner=runner,
        host_root=config.source_path / config.hostname,
        output_root=output_root,
    )


def run_build_for_host(
    *,
    runner: CommandRunner,
    host_root: Path,
    output_root: Path | None = None,
) -> BuildResult:
    validation_report = run_validate_for_host(runner=runner, host_root=host_root)
    if validation_report.has_errors:
        raise ValueError(_format_validation_block(validation_report))

    declared = tuple(
        sorted(
            load_declared_environments(host_root),
            key=lambda item: (item.app, item.environment),
        )
    )
    discovered = discover_host_tree(host_root, declared)
    discovered_by_key = {(item.app, item.environment): item for item in discovered}

    for target in declared:
        candidate = discovered_by_key.get((target.app, target.environment))
        if candidate is None or candidate.source_kind in {
            SourceKind.MISSING,
            SourceKind.AMBIGUOUS,
        }:
            raise ValueError(f"declared environment is not buildable: {target.app}/{target.environment}")

    final_root = resolve_output_root(output_root)
    validate_output_root(final_root)
    built_targets = tuple(
        BuildTarget(
            app=target.app,
            environment=target.environment,
            output_dir=final_root / target.app / target.environment,
        )
        for target in declared
    )
    if isinstance(runner, DryRunRunner):
        return BuildResult(output_root=final_root, built_targets=built_targets)

    stage_root: Path | None = None
    try:
        stage_root = create_stage_root(final_root)
        secrets_payload = decrypt_secret_env(host_root=host_root, runner=runner)
        for target in declared:
            candidate = discovered_by_key[(target.app, target.environment)]
            project_name = compose_project_name(target.app, target.environment)
            output_dir = stage_root / target.app / target.environment
            output_dir.mkdir(parents=True, exist_ok=True)

            if candidate.source_kind == SourceKind.COMPOSE:
                compose_text = normalize_static_compose(
                    source_env_dir=candidate.path,
                    compose_file=candidate.compose_files[0],
                    project_name=project_name,
                    runner=runner,
                )
            elif candidate.source_kind == SourceKind.TEMPLATE:
                assert candidate.template_file is not None
                assert candidate.values_file is not None
                rendered = render_template_environment(
                    env_root=candidate.path,
                    template_path=candidate.template_file,
                    values_path=candidate.values_file,
                )
                compose_text = normalize_rendered_compose(
                    source_env_dir=candidate.path,
                    rendered_text=rendered,
                    project_name=project_name,
                    runner=runner,
                )
            else:
                raise ValueError(f"declared environment is not buildable: {target.app}/{target.environment}")

            (output_dir / "docker-compose.yml").write_text(compose_text, encoding="utf-8")
            env_text = materialize_env_file(
                env_file=candidate.path / ".env",
                secrets=extract_environment_secrets(
                    secrets_payload,
                    app=target.app,
                    environment=target.environment,
                ),
            )
            (output_dir / ".env").write_text(env_text, encoding="utf-8")

        (stage_root / BUILD_MARKER_NAME).write_text("", encoding="utf-8")
        promote_runtime_root(stage_root, final_root)
        stage_root = None
        return BuildResult(output_root=final_root, built_targets=built_targets)
    except Exception:
        if stage_root is not None and stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)
        raise


def _format_validation_block(report: ValidationReport) -> str:
    descriptors: list[str] = []
    for finding in report.errors:
        if finding.app and finding.environment:
            descriptors.append(f"{finding.app}/{finding.environment} ({finding.code})")
        else:
            descriptors.append(finding.code)
    unique_descriptors = ", ".join(dict.fromkeys(descriptors))
    return f"build blocked by validation errors: {unique_descriptors}"


__all__ = ["run_build", "run_build_for_host"]
