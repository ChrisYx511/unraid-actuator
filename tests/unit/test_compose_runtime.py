from pathlib import Path

from unraid_actuator.compose_runtime import compose_down_spec, compose_up_spec
from unraid_actuator.deploy_models import RuntimeTarget


def test_compose_up_spec_is_explicit_and_no_orphan_removal() -> None:
    target = _target()

    spec = compose_up_spec(target)

    assert spec.argv == (
        "docker",
        "compose",
        "-p",
        "nextcloud-production",
        "--project-directory",
        "/runtime/nextcloud/production",
        "--env-file",
        "/runtime/nextcloud/production/.env",
        "-f",
        "/runtime/nextcloud/production/docker-compose.yaml",
        "up",
        "-d",
    )
    assert spec.cwd == target.output_dir
    assert spec.env == {"COMPOSE_REMOVE_ORPHANS": "0"}
    assert spec.inherit_env is True
    assert "--remove-orphans" not in spec.argv


def test_compose_down_spec_uses_plain_down_only() -> None:
    target = _target()

    spec = compose_down_spec(target)

    assert spec.argv == (
        "docker",
        "compose",
        "-p",
        "nextcloud-production",
        "--project-directory",
        "/runtime/nextcloud/production",
        "--env-file",
        "/runtime/nextcloud/production/.env",
        "-f",
        "/runtime/nextcloud/production/docker-compose.yaml",
        "down",
    )
    assert "-v" not in spec.argv
    assert "--rmi" not in spec.argv
    assert "--remove-orphans" not in spec.argv
    assert spec.env == {"COMPOSE_REMOVE_ORPHANS": "0"}
    assert spec.inherit_env is True


def _target() -> RuntimeTarget:
    output_dir = Path("/runtime/nextcloud/production")
    return RuntimeTarget(
        app="nextcloud",
        environment="production",
        output_dir=output_dir,
        compose_file=output_dir / "docker-compose.yaml",
        env_file=output_dir / ".env",
    )
