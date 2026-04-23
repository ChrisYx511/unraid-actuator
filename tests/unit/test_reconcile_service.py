from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from unraid_actuator.build_models import BuildResult
from unraid_actuator.config import ActiveConfig, save_active_config
from unraid_actuator.deploy_models import RuntimeActionResult, RuntimeTarget
from unraid_actuator.reconcile import run_reconcile
from unraid_actuator.reconcile_models import (
    CandidateWorkspace,
    ManagedCheckoutState,
    ReconcileStatus,
    RemovedTargetsPlan,
)
from unraid_actuator.runner import CommandResult, RecordingRunner
from unraid_actuator.validation_models import DeclaredEnvironment, FindingSeverity, ValidationFinding, ValidationReport


def test_reconcile_noop_returns_success_without_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = _write_active_config(tmp_path)
    visibility = FakeVisibility()
    monkeypatch.setattr(
        "unraid_actuator.reconcile.acquire_reconcile_lock",
        lambda: _fake_lock(),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.open_reconcile_log",
        lambda **_: visibility,
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.inspect_managed_checkout",
        lambda **_: ManagedCheckoutState(
            current_sha="abc123",
            candidate_sha="abc123",
            source_path=tmp_path / "source",
            branch="deploy",
        ),
    )

    result = run_reconcile(runner=RecordingRunner(), config_path=config_path)

    assert result.status == ReconcileStatus.NOOP
    assert visibility.started is True
    assert visibility.completed == [(False, "reconcile complete")]
    assert visibility.failures == []


def test_reconcile_invalid_candidate_fails_before_removal_or_apply(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    visibility = FakeVisibility()
    calls: list[str] = []
    monkeypatch.setattr("unraid_actuator.reconcile.acquire_reconcile_lock", lambda: _fake_lock())
    monkeypatch.setattr("unraid_actuator.reconcile.open_reconcile_log", lambda **_: visibility)
    monkeypatch.setattr("unraid_actuator.reconcile.resolve_output_root", lambda _: tmp_path / "current-build")
    monkeypatch.setattr(
        "unraid_actuator.reconcile.inspect_managed_checkout",
        lambda **_: ManagedCheckoutState(
            current_sha="abc123",
            candidate_sha="def456",
            source_path=tmp_path / "source",
            branch="deploy",
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.prepare_candidate_checkout",
        lambda **_: CandidateWorkspace(
            checkout_root=tmp_path / "incoming" / "checkout",
            host_root=tmp_path / "incoming" / "checkout" / "PotatoServer",
            build_root=tmp_path / "incoming" / "build",
            candidate_sha="def456",
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_validate_for_host",
        lambda **_: ValidationReport(
            findings=(
                ValidationFinding(
                    severity=FindingSeverity.ERROR,
                    code="INVALID",
                    message="broken",
                ),
            ),
            checked_targets=(),
        ),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.run_build_for_host", lambda **_: calls.append("build"))
    monkeypatch.setattr("unraid_actuator.reconcile.plan_removed_targets", lambda **_: calls.append("plan"))

    with pytest.raises(ValueError, match="incoming candidate validation failed"):
        run_reconcile(runner=RecordingRunner(), config_path=config_path)

    assert calls == []
    assert visibility.failures == ["incoming candidate validation failed with 1 error(s)"]


def test_reconcile_rebuilds_current_runtime_before_teardown_and_stops_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    visibility = FakeVisibility()
    current_host_root = tmp_path / "source" / "PotatoServer"
    current_runtime_root = tmp_path / "current-build"
    workspace = CandidateWorkspace(
        checkout_root=tmp_path / "incoming" / "checkout",
        host_root=tmp_path / "incoming" / "checkout" / "PotatoServer",
        build_root=tmp_path / "incoming" / "build",
        candidate_sha="def456",
    )
    removal_target = RuntimeTarget(
        app="immich",
        environment="preview",
        output_dir=current_runtime_root / "immich" / "preview",
        compose_file=current_runtime_root / "immich" / "preview" / "docker-compose.yml",
        env_file=current_runtime_root / "immich" / "preview" / ".env",
    )
    build_calls: list[Path] = []
    plan_calls = {"count": 0}
    deploy_calls: list[str] = []

    monkeypatch.setattr("unraid_actuator.reconcile.acquire_reconcile_lock", lambda: _fake_lock())
    monkeypatch.setattr("unraid_actuator.reconcile.open_reconcile_log", lambda **_: visibility)
    monkeypatch.setattr("unraid_actuator.reconcile.resolve_output_root", lambda _: current_runtime_root)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.inspect_managed_checkout",
        lambda **_: ManagedCheckoutState(
            current_sha="abc123",
            candidate_sha="def456",
            source_path=tmp_path / "source",
            branch="deploy",
        ),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.prepare_candidate_checkout", lambda **_: workspace)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_validate_for_host",
        lambda **_: ValidationReport(findings=(), checked_targets=()),
    )

    def fake_run_build_for_host(*, host_root: Path, output_root: Path | None = None, **_):
        build_calls.append(host_root)
        return BuildResult(output_root=output_root or tmp_path / "unused", built_targets=())

    def fake_plan_removed_targets(**_):
        plan_calls["count"] += 1
        if plan_calls["count"] == 1:
            return RemovedTargetsPlan(
                removed_declarations=(DeclaredEnvironment(app="immich", environment="preview"),),
                removed_targets=(),
                requires_current_rebuild=True,
            )
        return RemovedTargetsPlan(
            removed_declarations=(DeclaredEnvironment(app="immich", environment="preview"),),
            removed_targets=(removal_target,),
            requires_current_rebuild=False,
        )

    monkeypatch.setattr("unraid_actuator.reconcile.run_build_for_host", fake_run_build_for_host)
    monkeypatch.setattr("unraid_actuator.reconcile.plan_removed_targets", fake_plan_removed_targets)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_teardown",
        lambda **_: (_ for _ in ()).throw(ValueError("teardown failed for immich/preview: broke")),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.run_deploy", lambda **_: deploy_calls.append("deploy"))
    monkeypatch.setattr("unraid_actuator.reconcile.promote_runtime_root", lambda *_: deploy_calls.append("promote"))
    monkeypatch.setattr(
        "unraid_actuator.reconcile.fast_forward_managed_checkout",
        lambda **_: deploy_calls.append("fast-forward"),
    )

    with pytest.raises(ValueError, match="teardown failed for immich/preview: broke"):
        run_reconcile(runner=RecordingRunner(), config_path=config_path)

    assert build_calls == [workspace.host_root, current_host_root]
    assert plan_calls["count"] == 2
    assert deploy_calls == []
    assert "rebuilt current runtime tree from managed checkout for removals" in visibility.events
    assert visibility.failures == ["teardown failed for immich/preview: broke"]


def test_reconcile_applies_candidate_logs_runtime_actions_and_fast_forwards_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    visibility = FakeVisibility()
    current_runtime_root = tmp_path / "current-build"
    workspace = CandidateWorkspace(
        checkout_root=tmp_path / "incoming" / "checkout",
        host_root=tmp_path / "incoming" / "checkout" / "PotatoServer",
        build_root=tmp_path / "incoming" / "build",
        candidate_sha="def456",
    )
    removed_target = RuntimeTarget(
        app="immich",
        environment="preview",
        output_dir=current_runtime_root / "immich" / "preview",
        compose_file=current_runtime_root / "immich" / "preview" / "docker-compose.yml",
        env_file=current_runtime_root / "immich" / "preview" / ".env",
    )
    desired_target = RuntimeTarget(
        app="nextcloud",
        environment="production",
        output_dir=workspace.build_root / "nextcloud" / "production",
        compose_file=workspace.build_root / "nextcloud" / "production" / "docker-compose.yml",
        env_file=workspace.build_root / "nextcloud" / "production" / ".env",
    )
    order: list[str] = []

    monkeypatch.setattr("unraid_actuator.reconcile.acquire_reconcile_lock", lambda: _fake_lock())
    monkeypatch.setattr("unraid_actuator.reconcile.open_reconcile_log", lambda **_: visibility)
    monkeypatch.setattr("unraid_actuator.reconcile.resolve_output_root", lambda _: current_runtime_root)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.inspect_managed_checkout",
        lambda **_: ManagedCheckoutState(
            current_sha="abc123",
            candidate_sha="def456",
            source_path=tmp_path / "source",
            branch="deploy",
        ),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.prepare_candidate_checkout", lambda **_: workspace)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_validate_for_host",
        lambda **_: ValidationReport(findings=(), checked_targets=()),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_build_for_host",
        lambda **_: BuildResult(output_root=workspace.build_root, built_targets=()),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.plan_removed_targets",
        lambda **_: RemovedTargetsPlan(
            removed_declarations=(DeclaredEnvironment(app="immich", environment="preview"),),
            removed_targets=(removed_target,),
            requires_current_rebuild=False,
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_teardown",
        lambda **_: RuntimeActionResult(
            build_root=current_runtime_root,
            targets=(removed_target,),
            command_results=(_result(("docker", "compose", "down"), stdout="removed"),),
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_deploy",
        lambda **_: RuntimeActionResult(
            build_root=workspace.build_root,
            targets=(desired_target,),
            command_results=(_result(("docker", "compose", "up", "-d"), stdout="applied"),),
        ),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.promote_runtime_root",
        lambda *_: order.append("promote"),
    )
    monkeypatch.setattr(
        "unraid_actuator.reconcile.fast_forward_managed_checkout",
        lambda **_: order.append("fast-forward") or _result(("git", "merge", "--ff-only", "def456")),
    )

    result = run_reconcile(runner=RecordingRunner(), config_path=config_path)

    assert result.status == ReconcileStatus.APPLIED
    assert result.removed_targets == (removed_target,)
    assert order == ["promote", "fast-forward"]
    assert visibility.completed == [(True, "reconcile complete")]
    assert [
        (entry["summary"], entry["include_output"]) for entry in visibility.command_logs
    ] == [
        ("teardown immich/preview", True),
        ("deploy desired state", True),
        ("fast-forward managed checkout", False),
    ]


def test_reconcile_dry_run_reports_planned_rebuild_without_mutating(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_active_config(tmp_path)
    visibility = FakeVisibility()
    workspace = CandidateWorkspace(
        checkout_root=tmp_path / "incoming" / "checkout",
        host_root=tmp_path / "incoming" / "checkout" / "PotatoServer",
        build_root=tmp_path / "incoming" / "build",
        candidate_sha="def456",
    )
    calls: list[str] = []

    monkeypatch.setattr("unraid_actuator.reconcile.acquire_reconcile_lock", lambda: _fake_lock())
    monkeypatch.setattr("unraid_actuator.reconcile.open_reconcile_log", lambda **_: visibility)
    monkeypatch.setattr("unraid_actuator.reconcile.resolve_output_root", lambda _: tmp_path / "current-build")
    monkeypatch.setattr(
        "unraid_actuator.reconcile.inspect_managed_checkout",
        lambda **_: ManagedCheckoutState(
            current_sha="abc123",
            candidate_sha="def456",
            source_path=tmp_path / "source",
            branch="deploy",
        ),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.prepare_candidate_checkout", lambda **_: workspace)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.run_validate_for_host",
        lambda **_: ValidationReport(findings=(), checked_targets=()),
    )

    def fake_run_build_for_host(**_):
        calls.append("build")
        return BuildResult(output_root=workspace.build_root, built_targets=())

    monkeypatch.setattr("unraid_actuator.reconcile.run_build_for_host", fake_run_build_for_host)
    monkeypatch.setattr(
        "unraid_actuator.reconcile.plan_removed_targets",
        lambda **_: RemovedTargetsPlan(
            removed_declarations=(DeclaredEnvironment(app="immich", environment="preview"),),
            removed_targets=(),
            requires_current_rebuild=True,
        ),
    )
    monkeypatch.setattr("unraid_actuator.reconcile.run_teardown", lambda **_: calls.append("teardown"))
    monkeypatch.setattr("unraid_actuator.reconcile.run_deploy", lambda **_: calls.append("deploy"))
    monkeypatch.setattr("unraid_actuator.reconcile.promote_runtime_root", lambda *_: calls.append("promote"))
    monkeypatch.setattr(
        "unraid_actuator.reconcile.fast_forward_managed_checkout",
        lambda **_: calls.append("fast-forward"),
    )

    result = run_reconcile(runner=RecordingRunner(), config_path=config_path, dry_run=True)

    assert result.status == ReconcileStatus.DRY_RUN
    assert result.requires_current_rebuild is True
    assert result.detail == "would rebuild current runtime tree before removals"
    assert calls == ["build"]
    assert visibility.completed == [(False, "reconcile complete")]
    assert "would rebuild current runtime tree before removals" in visibility.events[-1]


class FakeVisibility:
    def __init__(self) -> None:
        self.started = False
        self.completed: list[tuple[bool, str]] = []
        self.failures: list[str] = []
        self.events: list[str] = []
        self.command_logs: list[dict[str, object]] = []
        self.log_path = Path("/tmp/reconcile.log")

    def __enter__(self) -> FakeVisibility:
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        return None

    def log_started(self) -> None:
        self.started = True

    def log_completed(self, *, notify: bool = False, message: str = "reconcile complete") -> None:
        self.completed.append((notify, message))

    def log_event(self, message: str, *, syslog: bool = False) -> None:
        self.events.append(message)

    def log_failure(self, message: str) -> None:
        self.failures.append(message)

    def log_command_result(self, result: CommandResult, *, summary: str | None = None, include_output: bool = False) -> None:
        self.command_logs.append(
            {
                "result": result,
                "summary": summary,
                "include_output": include_output,
            }
        )


@contextmanager
def _fake_lock():
    yield Path("/tmp/reconcile.lock")


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


def _result(argv: tuple[str, ...], *, stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(
        argv=argv,
        cwd=None,
        env={},
        stdin_text=None,
        inherit_env=True,
        exit_code=0,
        stdout=stdout,
        stderr=stderr,
        executed=True,
    )
