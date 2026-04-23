from pathlib import Path

import pytest

from unraid_actuator import build_paths
from unraid_actuator.build import run_build, run_build_for_host
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.runner import CommandResult, RecordingRunner
from unraid_actuator.validation_models import (
    DeclaredEnvironment,
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
)


def test_builds_all_to_default_tmp_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    default_root = tmp_path / "runtime-build"
    monkeypatch.setattr(build_paths, "DEFAULT_BUILD_ROOT", default_root)
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yml",
        apps_text="apps:\n  nextcloud:\n    - production\n  immich:\n    - preview\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","immich":{"preview":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    _write_template_env(host_root, "immich", "preview")
    runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: busybox\n"),
            _result(stdout="services:\n  app:\n    image: nginx:latest\n"),
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","immich":{"preview":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: nginx:latest\n"),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )

    result = run_build(runner=runner, config_path=config_path)

    assert result.output_root == default_root
    assert [(target.app, target.environment) for target in result.built_targets] == [
        ("immich", "preview"),
        ("nextcloud", "production"),
    ]
    assert (default_root / ".UNRAID_RUNNING_CONFIGURATION").exists()
    assert (default_root / "nextcloud" / "production" / "docker-compose.yaml").exists()
    assert (default_root / "immich" / "preview" / ".env").read_text(
        encoding="utf-8"
    ) == "DB_PASSWORD=cipher\nIMAGE=wrong\n"


def test_build_copies_static_environment_contents_and_overwrites_runtime_outputs(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    env_root = host_root / "nextcloud" / "production"
    (env_root / "docker-compose.yaml").write_text("services:\n  app:\n    image: alpine\n", encoding="utf-8")
    (env_root / ".env").write_text("SOURCE=1\n", encoding="utf-8")
    (env_root / "config" / "prometheus.yml").parent.mkdir(parents=True, exist_ok=True)
    (env_root / "config" / "prometheus.yml").write_text("scrape_configs: []\n", encoding="utf-8")
    (env_root / ".dockerignore").write_text("tmp/\n", encoding="utf-8")
    runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: busybox\n"),
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )

    result = run_build(runner=runner, config_path=config_path, output_root=tmp_path / "build")

    output_dir = result.output_root / "nextcloud" / "production"
    assert (output_dir / "config" / "prometheus.yml").read_text(encoding="utf-8") == "scrape_configs: []\n"
    assert (output_dir / ".dockerignore").read_text(encoding="utf-8") == "tmp/\n"
    assert (output_dir / "docker-compose.yaml").read_text(encoding="utf-8") == (
        "services:\n  app:\n    image: busybox\n"
    )
    assert (output_dir / ".env").read_text(encoding="utf-8") == "DB_PASSWORD=cipher\nSOURCE=1\n"


def test_build_copies_template_environment_sources_alongside_rendered_output(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  immich:\n    - preview\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","immich":{"preview":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_template_env(host_root, "immich", "preview")
    env_root = host_root / "immich" / "preview"
    (env_root / "assets" / "redis.conf").parent.mkdir(parents=True, exist_ok=True)
    (env_root / "assets" / "redis.conf").write_text("appendonly yes\n", encoding="utf-8")
    runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: nginx:latest\n"),
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","immich":{"preview":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: nginx:latest\n"),
        ],
        executed=True,
    )

    result = run_build(runner=runner, config_path=config_path, output_root=tmp_path / "build")

    output_dir = result.output_root / "immich" / "preview"
    assert (output_dir / "template.yaml").read_text(encoding="utf-8").startswith("template:\n")
    assert (output_dir / "compose.yaml.j2").read_text(encoding="utf-8").startswith("services:\n")
    assert (output_dir / "values.yaml").read_text(encoding="utf-8") == "IMAGE: nginx:latest\n"
    assert (output_dir / "assets" / "redis.conf").read_text(encoding="utf-8") == "appendonly yes\n"
    assert (output_dir / "docker-compose.yaml").read_text(encoding="utf-8") == (
        "services:\n  app:\n    image: nginx:latest\n"
    )
    assert (output_dir / ".env").read_text(encoding="utf-8") == "DB_PASSWORD=cipher\nIMAGE=wrong\n"


def test_build_fails_before_decrypt_for_missing_or_ambiguous_declared_targets(
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n  postgres:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '"}',
    )
    _write_compose_env(host_root, "nextcloud", "production")

    runner = RecordingRunner(executed=True)

    with pytest.raises(
        ValueError,
        match=r"build blocked by validation errors: postgres/production \(DECLARED_MISSING\)",
    ):
        run_build(runner=runner, config_path=config_path, output_root=tmp_path / "build")

    assert all(call.argv[0] != "ejson" for call in runner.calls)


def test_failed_decrypt_leaves_previous_output_root_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    default_root = tmp_path / "runtime-build"
    monkeypatch.setattr(build_paths, "DEFAULT_BUILD_ROOT", default_root)
    default_root.mkdir()
    (default_root / "sentinel.txt").write_text("keep\n", encoding="utf-8")
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '"}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: busybox\n"),
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=True,
                exit_code=1,
                stdout="",
                stderr="decrypt failed",
                executed=True,
            ),
        ],
        executed=True,
    )

    with pytest.raises(ValueError, match="failed to decrypt"):
        run_build(runner=runner, config_path=config_path)

    assert (default_root / "sentinel.txt").read_text(encoding="utf-8") == "keep\n"
    assert not any(path.name.startswith("runtime-build-staging-") for path in tmp_path.iterdir())


def test_run_build_for_host_matches_wrapper_behavior(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    wrapper_runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: busybox\n"),
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )
    direct_runner = RecordingRunner(
        results=[
            _result(stdout="services:\n  app:\n    image: busybox\n"),
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )

    wrapper_result = run_build(
        runner=wrapper_runner,
        config_path=config_path,
        output_root=tmp_path / "wrapper-build",
    )
    direct_result = run_build_for_host(
        runner=direct_runner,
        host_root=host_root,
        output_root=tmp_path / "direct-build",
    )

    assert [(target.app, target.environment) for target in wrapper_result.built_targets] == [
        ("nextcloud", "production")
    ]
    assert [(target.app, target.environment) for target in direct_result.built_targets] == [("nextcloud", "production")]
    assert (wrapper_result.output_root / "nextcloud" / "production" / ".env").read_text(encoding="utf-8") == (
        direct_result.output_root / "nextcloud" / "production" / ".env"
    ).read_text(encoding="utf-8")
    assert [call.argv for call in wrapper_runner.calls] == [call.argv for call in direct_runner.calls]


def test_promote_runtime_root_replaces_existing_tree(tmp_path: Path) -> None:
    final_root = tmp_path / "runtime"
    final_root.mkdir(parents=True, exist_ok=True)
    (final_root / "old.txt").write_text("old\n", encoding="utf-8")
    stage_root = tmp_path / "stage"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "new.txt").write_text("new\n", encoding="utf-8")

    build_paths.promote_runtime_root(stage_root, final_root)

    assert (final_root / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert not (final_root / "old.txt").exists()
    assert not stage_root.exists()


def test_build_runs_validation_before_output_root_and_decrypt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_active_config(tmp_path)
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    calls: list[str] = []
    runner = RecordingRunner(
        results=[
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )

    monkeypatch.setattr(
        "unraid_actuator.build.run_validate_for_host",
        lambda **_: calls.append("validate")
        or ValidationReport(
            findings=(),
            checked_targets=(DeclaredEnvironment(app="nextcloud", environment="production"),),
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.validate_output_root",
        lambda path: calls.append(f"validate-output:{path.name}"),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.create_stage_root",
        lambda path: calls.append(f"stage:{path.name}") or (tmp_path / "stage"),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.decrypt_secret_env",
        lambda **_: calls.append("decrypt")
        or {
            "_public_key": "a" * 64,
            "nextcloud": {"production": {"DB_PASSWORD": "cipher"}},
        },
    )

    run_build(runner=runner, config_path=config_path, output_root=tmp_path / "build")

    assert calls[:4] == ["validate", "validate-output:build", "stage:build", "decrypt"]


def test_build_validation_errors_block_before_stage_or_decrypt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '"}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    runner = RecordingRunner(executed=True)

    monkeypatch.setattr(
        "unraid_actuator.build.run_validate_for_host",
        lambda **_: ValidationReport(
            findings=(
                ValidationFinding(
                    severity=FindingSeverity.ERROR,
                    code="DECLARED_MISSING",
                    message="missing",
                    app="nextcloud",
                    environment="production",
                ),
            ),
            checked_targets=(DeclaredEnvironment(app="nextcloud", environment="production"),),
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.validate_output_root",
        lambda path: (_ for _ in ()).throw(AssertionError("validate_output_root should not run")),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.create_stage_root",
        lambda path: (_ for _ in ()).throw(AssertionError("create_stage_root should not run")),
    )
    monkeypatch.setattr(
        "unraid_actuator.build.decrypt_secret_env",
        lambda **_: (_ for _ in ()).throw(AssertionError("decrypt_secret_env should not run")),
    )

    with pytest.raises(
        ValueError,
        match=r"build blocked by validation errors: nextcloud/production \(DECLARED_MISSING\)",
    ):
        run_build_for_host(runner=runner, host_root=host_root, output_root=tmp_path / "build")


def test_build_validation_warnings_do_not_block_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host_root = tmp_path / "source" / "PotatoServer"
    _write_host_contracts(
        host_root,
        apps_name="apps.yaml",
        apps_text="apps:\n  nextcloud:\n    - production\n",
        secret_text='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}',
    )
    _write_compose_env(host_root, "nextcloud", "production")
    runner = RecordingRunner(
        results=[
            _result(stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}'),
            _result(stdout="services:\n  app:\n    image: busybox\n"),
        ],
        executed=True,
    )

    monkeypatch.setattr(
        "unraid_actuator.build.run_validate_for_host",
        lambda **_: ValidationReport(
            findings=(
                ValidationFinding(
                    severity=FindingSeverity.WARNING,
                    code="SOURCE_XOR",
                    message="warning",
                    app="sidecar",
                    environment="preview",
                ),
            ),
            checked_targets=(DeclaredEnvironment(app="nextcloud", environment="production"),),
        ),
    )

    result = run_build_for_host(runner=runner, host_root=host_root, output_root=tmp_path / "build")

    assert result.output_root == tmp_path / "build"
    assert (result.output_root / ".UNRAID_RUNNING_CONFIGURATION").exists()


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


def _write_host_contracts(host_root: Path, *, apps_name: str, apps_text: str, secret_text: str) -> None:
    host_root.mkdir(parents=True, exist_ok=True)
    (host_root / apps_name).write_text(apps_text, encoding="utf-8")
    (host_root / "secret-env.ejson").write_text(secret_text, encoding="utf-8")


def _write_compose_env(host_root: Path, app: str, environment: str) -> None:
    target = host_root / app / environment
    target.mkdir(parents=True, exist_ok=True)
    (target / "docker-compose.yaml").write_text("services:\n  app:\n    image: busybox\n", encoding="utf-8")


def _write_template_env(host_root: Path, app: str, environment: str) -> None:
    target = host_root / app / environment
    target.mkdir(parents=True, exist_ok=True)
    (target / "template.yaml").write_text("template:\n  include:\n    - compose.yaml.j2\n", encoding="utf-8")
    (target / "compose.yaml.j2").write_text("services:\n  app:\n    image: {{ IMAGE }}\n", encoding="utf-8")
    (target / "values.yaml").write_text("IMAGE: nginx:latest\n", encoding="utf-8")
    (target / ".env").write_text("IMAGE=wrong\n", encoding="utf-8")


def _result(*, stdout: str) -> CommandResult:
    return CommandResult(
        argv=(),
        cwd=None,
        env={},
        stdin_text=None,
        inherit_env=False,
        exit_code=0,
        stdout=stdout,
        stderr="",
        executed=True,
    )
