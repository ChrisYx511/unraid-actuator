from pathlib import Path

import pytest

from unraid_actuator.cli import main
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.validation_models import (
    DeclaredEnvironment,
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
)


def test_validate_requires_both_scope_flags(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = _write_active_config(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        main(["validate", "--app", "nextcloud"], config_path=config_path)

    assert excinfo.value.code == 2
    assert "--app and --environment must be provided together" in capsys.readouterr().err


def test_validate_warnings_only_returns_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = _write_active_config(tmp_path)
    report = ValidationReport(
        findings=(
            ValidationFinding(
                severity=FindingSeverity.WARNING,
                code="SOURCE_MISSING",
                message="warning only",
                app="immich",
                environment="preview",
            ),
        ),
        checked_targets=(DeclaredEnvironment(app="immich", environment="preview"),),
    )
    monkeypatch.setattr("unraid_actuator.cli.run_validate", lambda **_: report)

    exit_code = main(["validate"], config_path=config_path)

    assert exit_code == 0
    assert "Warnings (1)" in capsys.readouterr().out


def test_validate_hard_error_returns_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = _write_active_config(tmp_path)
    report = ValidationReport(
        findings=(
            ValidationFinding(
                severity=FindingSeverity.ERROR,
                code="DECLARED_MISSING",
                message="hard error",
                app="postgres",
                environment="production",
            ),
        ),
        checked_targets=(DeclaredEnvironment(app="postgres", environment="production"),),
    )
    monkeypatch.setattr("unraid_actuator.cli.run_validate", lambda **_: report)

    exit_code = main(["validate"], config_path=config_path)

    assert exit_code == 1
    assert "Errors (1)" in capsys.readouterr().out


def test_validate_schema_error_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = tmp_path / "bad-actuator-cfg.yml"
    config_path.write_text("repo_url: https://example.com/repo.git\n", encoding="utf-8")

    exit_code = main(["validate"], config_path=config_path)

    assert exit_code == 1
    assert "while parsing a mapping" in capsys.readouterr().err


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
