from pathlib import Path

import pytest

from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.runner import RecordingRunner
from unraid_actuator.schemas import YAMLValidationError
from unraid_actuator.validate import run_validate, run_validate_for_host


def test_validate_all_host_configurations(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yml",
        apps_text="apps:\n  nextcloud:\n    - production\n  postgres:\n    - production\n",
    )
    _write_compose_env(host_root, "nextcloud", "production")
    _write_ambiguous_env(host_root, "immich", "preview")
    runner = RecordingRunner(executed=True)

    report = run_validate(runner=runner, config_path=config_path)

    assert report.has_errors is True
    assert any(finding.code == "DECLARED_MISSING" for finding in report.errors)
    assert any(finding.code == "SOURCE_XOR" and finding.app == "immich" for finding in report.warnings)
    assert runner.calls[0].argv[:3] == ("docker", "compose", "-p")


def test_validate_selected_scope_only_retains_collision_context(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  app:\n    - one-prod\n  app-one:\n    - prod\n",
    )
    _write_compose_env(host_root, "app", "one-prod")
    _write_compose_env(host_root, "app-one", "prod")
    runner = RecordingRunner(executed=True)

    report = run_validate(
        runner=runner,
        config_path=config_path,
        app="app",
        environment="one-prod",
    )

    assert report.checked_targets[0].app == "app"
    assert any(finding.code == "PROJECT_NAME_COLLISION" for finding in report.errors)
    assert runner.calls == []


def test_validate_schema_errors_propagate(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    environments:\n      - production\n",
    )

    with pytest.raises(YAMLValidationError):
        run_validate(runner=RecordingRunner(), config_path=config_path)


def test_run_validate_for_host_matches_wrapper_behavior(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
    )
    _write_compose_env(host_root, "nextcloud", "production")
    wrapper_runner = RecordingRunner(executed=True)
    direct_runner = RecordingRunner(executed=True)

    wrapper_report = run_validate(runner=wrapper_runner, config_path=config_path)
    direct_report = run_validate_for_host(runner=direct_runner, host_root=host_root)

    assert wrapper_report.checked_targets == direct_report.checked_targets
    assert [(finding.code, finding.app, finding.environment) for finding in wrapper_report.findings] == [
        (finding.code, finding.app, finding.environment) for finding in direct_report.findings
    ]
    assert [call.argv for call in wrapper_runner.calls] == [call.argv for call in direct_runner.calls]


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


def _write_host_contracts(host_root: Path, *, apps_name: str, apps_text: str) -> None:
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / apps_name).write_text(apps_text, encoding="utf-8")
    (host_root / "secret-env.ejson").write_text(
        '{"_public_key":"' + ("a" * 64) + '"}',
        encoding="utf-8",
    )


def _write_compose_env(host_root: Path, app: str, environment: str) -> None:
    target = host_root / app / environment
    target.mkdir(parents=True, exist_ok=True)
    (target / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")


def _write_ambiguous_env(host_root: Path, app: str, environment: str) -> None:
    target = host_root / app / environment
    target.mkdir(parents=True, exist_ok=True)
    (target / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (target / "template.yml").write_text("template:\n  include:\n    - compose.yaml.j2\n", encoding="utf-8")
    (target / "values.yml").write_text("image: busybox\n", encoding="utf-8")
