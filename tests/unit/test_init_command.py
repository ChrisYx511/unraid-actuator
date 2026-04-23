from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator.cli import main
from unraid_actuator.config import load_active_config
from unraid_actuator.runner import RecordingRunner


def test_init_creates_missing_directories_runs_clone_and_persists_config(tmp_path: Path) -> None:
    source_path = tmp_path / "managed" / "source"
    config_path = tmp_path / "actuator-cfg.yml"
    runner = RecordingRunner(executed=True)

    exit_code = main(
        [
            "init",
            "--repo-url",
            "https://example.com/infrastructure.git",
            "--deploy-branch",
            "deploy",
            "--hostname",
            "PotatoServer",
            "--source-path",
            str(source_path),
        ],
        runner=runner,
        config_path=config_path,
    )

    assert exit_code == 0
    assert source_path.exists()
    assert runner.calls[0].argv == (
        "git",
        "clone",
        "--branch",
        "deploy",
        "--single-branch",
        "https://example.com/infrastructure.git",
        str(source_path),
    )
    stored = load_active_config(path=config_path)
    assert stored.hostname == "PotatoServer"
    assert stored.source_path == source_path


def test_init_reuses_non_empty_directory_without_recloning(tmp_path: Path) -> None:
    source_path = tmp_path / "managed" / "source"
    source_path.mkdir(parents=True)
    (source_path / ".keep").write_text("existing", encoding="utf-8")
    config_path = tmp_path / "actuator-cfg.yml"
    runner = RecordingRunner(executed=True)

    exit_code = main(
        [
            "init",
            "--repo-url",
            "https://example.com/infrastructure.git",
            "--deploy-branch",
            "deploy",
            "--hostname",
            "PotatoServer",
            "--source-path",
            str(source_path),
        ],
        runner=runner,
        config_path=config_path,
    )

    assert exit_code == 0
    assert runner.calls == []
    assert load_active_config(path=config_path).source_path == source_path


def test_init_dry_run_reports_clone_without_writing_config(tmp_path: Path) -> None:
    source_path = tmp_path / "managed" / "source"
    config_path = tmp_path / "actuator-cfg.yml"
    runner = RecordingRunner(stdout="DRY RUN: git clone", executed=False)

    exit_code = main(
        [
            "--dry-run",
            "init",
            "--repo-url",
            "https://example.com/infrastructure.git",
            "--deploy-branch",
            "deploy",
            "--hostname",
            "PotatoServer",
            "--source-path",
            str(source_path),
        ],
        runner=runner,
        config_path=config_path,
    )

    assert exit_code == 0
    assert len(runner.calls) == 1
    assert not source_path.exists()
    assert not config_path.exists()


def test_init_git_runtime_error_bubbles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "actuator-cfg.yml"

    monkeypatch.setattr(
        "unraid_actuator.cli.run_init",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("git clone failed")),
    )

    with pytest.raises(RuntimeError, match="git clone failed"):
        main(
            [
                "init",
                "--repo-url",
                "https://example.com/infrastructure.git",
                "--deploy-branch",
                "deploy",
                "--hostname",
                "PotatoServer",
                "--source-path",
                str(tmp_path / "managed" / "source"),
            ],
            config_path=config_path,
        )
