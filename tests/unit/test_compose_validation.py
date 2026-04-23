from pathlib import Path

from unraid_actuator.compose_validation import (
    validate_static_compose,
    validate_template_source,
)
from unraid_actuator.runner import CommandResult, RecordingRunner
from unraid_actuator.validation_models import DiscoveredEnvironment, SourceKind


def test_static_compose_validation_builds_expected_command_spec() -> None:
    candidate = DiscoveredEnvironment(
        app="nextcloud",
        environment="production",
        path=Path("/tmp/nextcloud/production"),
        declared=True,
        source_kind=SourceKind.COMPOSE,
        compose_files=(Path("/tmp/nextcloud/production/docker-compose.yml"),),
        template_file=None,
        values_file=None,
    )
    runner = RecordingRunner(executed=True)

    findings = validate_static_compose(candidate, "nextcloud-production", runner=runner)

    assert findings == ()
    assert runner.calls[0].argv == (
        "docker",
        "compose",
        "-p",
        "nextcloud-production",
        "--project-directory",
        str(candidate.path),
        "-f",
        "docker-compose.yml",
        "config",
        "--no-interpolate",
        "--format",
        "yaml",
    )
    assert runner.calls[0].cwd == candidate.path
    assert runner.calls[0].inherit_env is False
    assert runner.calls[0].env == {"COMPOSE_DISABLE_ENV_FILE": "1"}


def test_template_output_is_piped_to_compose_from_stdin(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yml").write_text("template:\n  include:\n    - compose.yaml.j2\n", encoding="utf-8")
    (env_root / "compose.yaml.j2").write_text("services:\n  app:\n    image: {{ image }}\n", encoding="utf-8")
    (env_root / "values.yml").write_text("image: busybox\n", encoding="utf-8")
    candidate = DiscoveredEnvironment(
        app="nextcloud",
        environment="production",
        path=env_root,
        declared=True,
        source_kind=SourceKind.TEMPLATE,
        compose_files=(),
        template_file=env_root / "template.yml",
        values_file=env_root / "values.yml",
    )
    runner = RecordingRunner(
        executed=True,
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=False,
                exit_code=0,
                stdout="services:\n  app:\n    image: busybox\n",
                stderr="",
                executed=True,
            ),
        ],
    )

    findings = validate_template_source(candidate, "nextcloud-production", runner=runner)

    assert findings == ()
    assert runner.calls[0].argv == (
        "docker",
        "compose",
        "-p",
        "nextcloud-production",
        "--project-directory",
        str(candidate.path),
        "-f",
        "-",
        "config",
        "--no-interpolate",
        "--format",
        "yaml",
    )
    assert "image: busybox" in runner.calls[0].stdin_text
    assert runner.calls[0].inherit_env is False


def test_template_validation_reports_render_failures(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yaml").write_text("template:\n  include:\n    - compose.yaml.j2\n", encoding="utf-8")
    (env_root / "compose.yaml.j2").write_text("services:\n  app:\n    image: {{ image }}\n", encoding="utf-8")
    (env_root / "values.yaml").write_text("tag: latest\n", encoding="utf-8")
    candidate = DiscoveredEnvironment(
        app="nextcloud",
        environment="production",
        path=env_root,
        declared=True,
        source_kind=SourceKind.TEMPLATE,
        compose_files=(),
        template_file=env_root / "template.yaml",
        values_file=env_root / "values.yaml",
    )

    findings = validate_template_source(candidate, "nextcloud-production", runner=RecordingRunner())

    assert findings[0].code == "TEMPLATE_RENDER_FAILED"
