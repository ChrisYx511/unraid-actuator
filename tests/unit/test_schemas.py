from pathlib import Path

import pytest

from unraid_actuator.schemas import (
    YAMLValidationError,
    load_apps_yaml,
    load_declared_environments,
    load_template_descriptor,
    load_values_yaml,
    resolve_host_apps_path,
    resolve_template_path,
    resolve_values_path,
    validate_secret_env_structure,
)
from unraid_actuator.validation_models import DeclaredEnvironment


def test_apps_yaml_schema_errors_are_reported(tmp_path: Path) -> None:
    apps_path = tmp_path / "apps.yaml"
    apps_path.write_text("apps:\n  nextcloud:\n    environments:\n      - production\n", encoding="utf-8")

    with pytest.raises(YAMLValidationError):
        load_apps_yaml(apps_path)


def test_valid_apps_yml_loads_declared_environments(tmp_path: Path) -> None:
    host_root = tmp_path / "PotatoServer"
    host_root.mkdir()
    apps_path = host_root / "apps.yml"
    apps_path.write_text("apps:\n  nextcloud:\n    - production\n    - staging\n", encoding="utf-8")

    assert resolve_host_apps_path(host_root) == apps_path
    assert load_declared_environments(host_root) == (
        DeclaredEnvironment(app="nextcloud", environment="production"),
        DeclaredEnvironment(app="nextcloud", environment="staging"),
    )


def test_template_and_values_yaml_support_both_extensions(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yml").write_text("template:\n  include:\n    - compose.yaml.j2\n", encoding="utf-8")
    (env_root / "values.yaml").write_text("image: nginx:latest\n", encoding="utf-8")

    assert resolve_template_path(env_root).name == "template.yml"
    assert resolve_values_path(env_root).name == "values.yaml"
    assert load_template_descriptor(resolve_template_path(env_root)) == ("compose.yaml.j2",)
    assert load_values_yaml(resolve_values_path(env_root)) == {"image": "nginx:latest"}


def test_values_yaml_requires_mapping_root(tmp_path: Path) -> None:
    values_path = tmp_path / "values.yml"
    values_path.write_text("- nginx:latest\n", encoding="utf-8")

    with pytest.raises(YAMLValidationError):
        load_values_yaml(values_path)


def test_secret_env_structure_rejects_invalid_shapes(tmp_path: Path) -> None:
    secret_path = tmp_path / "secret-env.ejson"
    secret_path.write_text(
        '{"_public_key":"short","nextcloud":{"production":{"bad-key":123}}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        validate_secret_env_structure(secret_path)


def test_secret_env_structure_accepts_nested_host_values(tmp_path: Path) -> None:
    secret_path = tmp_path / "secret-env.ejson"
    secret_path.write_text(
        '{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"ciphertext"}}}',
        encoding="utf-8",
    )

    validate_secret_env_structure(secret_path)
