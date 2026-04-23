from __future__ import annotations

from pathlib import Path

from unraid_actuator.build_models import BuildResult, BuildTarget
from unraid_actuator.cli import main
from unraid_actuator.config import ActiveConfig, save_active_config


def test_build_uses_default_output_path(monkeypatch, tmp_path: Path, capsys) -> None:
    config_path = _write_active_config(tmp_path)
    called: dict[str, object] = {}

    def fake_run_build(**kwargs):
        called.update(kwargs)
        return BuildResult(output_root=Path("/tmp/unraid-actuator/build"), built_targets=())

    monkeypatch.setattr("unraid_actuator.cli.run_build", fake_run_build)

    exit_code = main(["build"], config_path=config_path)

    assert exit_code == 0
    assert called["output_root"] is None
    assert "Built runtime tree at /tmp/unraid-actuator/build" in capsys.readouterr().out


def test_build_passes_custom_output_path(monkeypatch, tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    called: dict[str, object] = {}

    def fake_run_build(**kwargs):
        called.update(kwargs)
        return BuildResult(
            output_root=Path("/custom/build"),
            built_targets=(
                BuildTarget(
                    app="nextcloud",
                    environment="production",
                    output_dir=Path("/custom/build/nextcloud/production"),
                ),
            ),
        )

    monkeypatch.setattr("unraid_actuator.cli.run_build", fake_run_build)

    exit_code = main(["build", "--output-path", "/custom/build"], config_path=config_path)

    assert exit_code == 0
    assert called["output_root"] == Path("/custom/build")


def test_build_failure_returns_one(monkeypatch, tmp_path: Path, capsys) -> None:
    config_path = _write_active_config(tmp_path)
    monkeypatch.setattr(
        "unraid_actuator.cli.run_build",
        lambda **_: (_ for _ in ()).throw(ValueError("bad build")),
    )

    exit_code = main(["build"], config_path=config_path)

    assert exit_code == 1
    assert "bad build" in capsys.readouterr().err


def test_build_validation_block_returns_one_with_service_message(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    config_path = _write_active_config(tmp_path)
    monkeypatch.setattr(
        "unraid_actuator.cli.run_build",
        lambda **_: (_ for _ in ()).throw(
            ValueError("build blocked by validation errors: nextcloud/production (DECLARED_MISSING)")
        ),
    )

    exit_code = main(["build"], config_path=config_path)

    assert exit_code == 1
    assert "build blocked by validation errors: nextcloud/production (DECLARED_MISSING)" in capsys.readouterr().err


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
