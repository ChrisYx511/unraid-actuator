from pathlib import Path

import pytest

from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.reconcile_git import (
    fast_forward_managed_checkout,
    inspect_managed_checkout,
    prepare_candidate_checkout,
)
from unraid_actuator.reconcile_models import ManagedCheckoutState
from unraid_actuator.runner import CommandResult, RecordingRunner


def test_inspect_managed_checkout_rejects_dirty_checkout(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    runner = RecordingRunner(results=[_result(stdout="# branch.oid abc123\n1 .M N... 100644 100644 100644 file\n")])

    with pytest.raises(ValueError, match="managed source checkout has uncommitted changes"):
        inspect_managed_checkout(runner=runner, config_path=config_path)

    assert runner.calls[0].argv == ("git", "status", "--porcelain=v2", "--branch")


def test_inspect_managed_checkout_rejects_locally_diverged_source(
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    runner = RecordingRunner(
        results=[
            _result(stdout="# branch.oid abc123\n"),
            _result(),
            _result(stdout="abc123\n"),
            _result(stdout="def456\n"),
            _result(exit_code=1),
        ]
    )

    with pytest.raises(ValueError, match="not a clean fast-forward ancestor"):
        inspect_managed_checkout(runner=runner, config_path=config_path)

    assert runner.calls[-1].argv == (
        "git",
        "merge-base",
        "--is-ancestor",
        "HEAD",
        "FETCH_HEAD",
    )


def test_inspect_managed_checkout_resolves_exact_candidate_sha(tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    runner = RecordingRunner(
        results=[
            _result(stdout="# branch.oid abc123\n"),
            _result(),
            _result(stdout="abc123\n"),
            _result(stdout="abc123\n"),
            _result(),
        ]
    )

    state = inspect_managed_checkout(runner=runner, config_path=config_path)

    assert state.current_sha == "abc123"
    assert state.candidate_sha == "abc123"
    assert state.source_path == source_path
    assert state.branch == "deploy"


def test_prepare_candidate_checkout_and_fast_forward_use_exact_candidate_sha(
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    managed_state = ManagedCheckoutState(
        current_sha="abc123",
        candidate_sha="def456",
        source_path=tmp_path / "source",
        branch="deploy",
    )
    managed_state.source_path.mkdir(parents=True, exist_ok=True)
    runner = RecordingRunner(results=[_result(), _result(), _result()])

    workspace = prepare_candidate_checkout(
        runner=runner,
        managed_state=managed_state,
        config_path=config_path,
        work_root=tmp_path / "incoming",
    )

    assert workspace.checkout_root == tmp_path / "incoming" / "def456" / "checkout"
    assert workspace.host_root == workspace.checkout_root / "PotatoServer"
    assert workspace.build_root == tmp_path / "incoming" / "def456" / "build"
    assert workspace.candidate_sha == "def456"
    assert workspace.checkout_root != managed_state.source_path
    assert runner.calls[0].argv == (
        "git",
        "clone",
        "--branch",
        "deploy",
        "--single-branch",
        "https://example.com/infrastructure.git",
        str(workspace.checkout_root),
    )
    assert runner.calls[1].argv == ("git", "checkout", "--detach", "def456")

    fast_forward_managed_checkout(runner=runner, managed_state=managed_state)

    assert runner.calls[2].argv == ("git", "merge", "--ff-only", "def456")
    assert runner.calls[2].cwd == managed_state.source_path


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


def _result(*, exit_code: int = 0, stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(
        argv=(),
        cwd=None,
        env={},
        stdin_text=None,
        inherit_env=True,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        executed=True,
    )
