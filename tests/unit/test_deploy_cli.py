from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator.cli import build_parser, main
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.deploy_models import RuntimeActionResult, RuntimeTarget


def test_deploy_requires_both_scope_flags(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = _write_active_config(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        main(["deploy", "--app", "nextcloud"], config_path=config_path)

    assert excinfo.value.code == 2
    assert "--app and --environment must be provided together" in capsys.readouterr().err


def test_deploy_dispatches_default_and_custom_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    config_path = _write_active_config(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run_deploy(**kwargs):
        calls.append(kwargs)
        return RuntimeActionResult(
            build_root=Path("/tmp/unraid-actuator/build") if kwargs["build_root"] is None else kwargs["build_root"],
            targets=(),
            command_results=(),
        )

    monkeypatch.setattr("unraid_actuator.cli.run_deploy", fake_run_deploy)

    exit_code = main(["deploy"], config_path=config_path)
    assert exit_code == 0
    assert calls[0]["build_root"] is None
    assert calls[0]["app"] is None
    assert "Deployed 0 target(s) from /tmp/unraid-actuator/build" in capsys.readouterr().out

    exit_code = main(
        [
            "deploy",
            "--build-root",
            "/custom/build",
            "--app",
            "nextcloud",
            "--environment",
            "production",
        ],
        config_path=config_path,
    )
    assert exit_code == 0
    assert calls[1]["build_root"] == Path("/custom/build")
    assert calls[1]["app"] == "nextcloud"
    assert calls[1]["environment"] == "production"


def test_teardown_dispatches_and_returns_one_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys,
) -> None:
    config_path = _write_active_config(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run_teardown(**kwargs):
        calls.append(kwargs)
        if kwargs["build_root"] == Path("/broken"):
            raise ValueError("bad teardown")
        target = RuntimeTarget(
            app="nextcloud",
            environment="production",
            output_dir=Path("/custom/build/nextcloud/production"),
            compose_file=Path("/custom/build/nextcloud/production/docker-compose.yml"),
            env_file=Path("/custom/build/nextcloud/production/.env"),
        )
        return RuntimeActionResult(
            build_root=Path("/custom/build"),
            targets=(target,),
            command_results=(),
        )

    monkeypatch.setattr("unraid_actuator.cli.run_teardown", fake_run_teardown)

    exit_code = main(
        [
            "teardown",
            "--build-root",
            "/custom/build",
            "--app",
            "nextcloud",
            "--environment",
            "production",
        ],
        config_path=config_path,
    )

    assert exit_code == 0
    assert calls[0]["build_root"] == Path("/custom/build")
    assert "Tore down 1 target(s) from /custom/build" in capsys.readouterr().out

    exit_code = main(["teardown", "--build-root", "/broken"], config_path=config_path)

    assert exit_code == 1
    assert "bad teardown" in capsys.readouterr().err


def test_teardown_requires_both_scope_flags(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = _write_active_config(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        main(["teardown", "--environment", "production"], config_path=config_path)

    assert excinfo.value.code == 2
    assert "--app and --environment must be provided together" in capsys.readouterr().err


def test_parser_help_exposes_deploy_and_teardown() -> None:
    help_text = build_parser().format_help()

    assert "deploy" in help_text
    assert "teardown" in help_text


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
