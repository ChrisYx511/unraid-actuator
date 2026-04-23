from pathlib import Path

import pytest

from unraid_actuator.cli import build_parser, main
from unraid_actuator.config import ActiveConfig, load_active_config, save_active_config
from unraid_actuator.reconcile_models import ReconcileResult, ReconcileStatus
from unraid_actuator.runner import CommandRunner, SubprocessRunner


def test_reconcile_dispatches_successfully(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = _write_active_config(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run_reconcile(**kwargs):
        calls.append(kwargs)
        return ReconcileResult(
            status=ReconcileStatus.NOOP,
            current_sha="abc123",
            candidate_sha="abc123",
            dry_run=False,
            removed_targets=(),
        )

    injected_runner = StubRunner()
    monkeypatch.setattr("unraid_actuator.cli.run_reconcile", fake_run_reconcile)

    exit_code = main(["reconcile"], runner=injected_runner, config_path=config_path)

    assert exit_code == 0
    assert calls[0]["runner"] is injected_runner
    assert calls[0]["config_path"] == config_path
    assert calls[0]["dry_run"] is False
    assert "Reconcile noop candidate=abc123" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [["--dry-run", "reconcile"], ["reconcile", "--dry-run"]])
def test_reconcile_dry_run_passes_flag_without_switching_to_global_dry_run_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
) -> None:
    config_path = _write_active_config(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run_reconcile(**kwargs):
        calls.append(kwargs)
        return ReconcileResult(
            status=ReconcileStatus.DRY_RUN,
            current_sha="abc123",
            candidate_sha="def456",
            dry_run=True,
            removed_targets=(),
            detail="would rebuild current runtime tree before removals",
        )

    monkeypatch.setattr("unraid_actuator.cli.run_reconcile", fake_run_reconcile)

    exit_code = main(argv, config_path=config_path)

    assert exit_code == 0
    assert isinstance(calls[0]["runner"], SubprocessRunner)
    assert calls[0]["dry_run"] is True


def test_reconcile_failures_return_one_and_print_original_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = _write_active_config(tmp_path)

    def fake_run_reconcile(**kwargs):
        raise ValueError("reconcile broke")

    monkeypatch.setattr("unraid_actuator.cli.run_reconcile", fake_run_reconcile)

    exit_code = main(["reconcile"], config_path=config_path)

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == "reconcile broke"


def test_reconcile_git_runtime_error_bubbles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)

    monkeypatch.setattr(
        "unraid_actuator.cli.run_reconcile",
        lambda **_: (_ for _ in ()).throw(RuntimeError("git fetch failed")),
    )

    with pytest.raises(RuntimeError, match="git fetch failed"):
        main(["reconcile"], config_path=config_path)


def test_reconcile_yaml_validation_errors_still_return_one(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = _write_active_config(tmp_path)
    expected_error = _yaml_validation_error(tmp_path)

    def fake_run_reconcile(**kwargs):
        raise expected_error

    monkeypatch.setattr("unraid_actuator.cli.run_reconcile", fake_run_reconcile)

    exit_code = main(["reconcile"], config_path=config_path)

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == str(expected_error)


def test_parser_help_exposes_reconcile() -> None:
    help_text = build_parser().format_help()

    assert "reconcile" in help_text


class StubRunner(CommandRunner):
    def run(self, spec):  # pragma: no cover - runner is only passed through.
        raise AssertionError("stub runner should not be invoked directly")


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


def _yaml_validation_error(tmp_path: Path):
    try:
        bad_config = tmp_path / "bad-actuator-cfg.yml"
        bad_config.write_text("repo_url: https://example.com/repo.git\n", encoding="utf-8")
        load_active_config(path=bad_config)
    except Exception as exc:  # pragma: no cover - helper creates the exact parser exception for the test.
        return exc
    raise AssertionError("expected YAML validation error")
