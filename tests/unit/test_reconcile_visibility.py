from __future__ import annotations

from pathlib import Path

from unraid_actuator.reconcile_visibility import open_reconcile_log
from unraid_actuator.runner import CommandResult, RecordingRunner


def test_open_reconcile_log_creates_timestamped_file_and_only_logs_selected_output(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "logs"
    runner = RecordingRunner(executed=True)

    with open_reconcile_log(
        runner=runner,
        log_dir=log_dir,
        notify_resolver=lambda _: None,
        timestamp_factory=lambda: "20260422T010203Z",
    ) as visibility:
        visibility.log_event("planning reconcile")
        visibility.log_command_result(_result(("git", "fetch"), stdout="secret-token"), include_output=False)
        visibility.log_command_result(
            _result(("docker", "compose", "up", "-d"), stdout="compose ok"),
            include_output=True,
        )

    log_path = log_dir / "reconcile-20260422T010203Z.log"
    assert log_path.exists()
    text = log_path.read_text(encoding="utf-8")
    assert "planning reconcile" in text
    assert "compose ok" in text
    assert "secret-token" not in text


def test_noop_completion_logs_to_file_and_syslog_without_notify(tmp_path: Path) -> None:
    runner = RecordingRunner(executed=True)

    with open_reconcile_log(
        runner=runner,
        log_dir=tmp_path / "logs",
        notify_resolver=lambda _: "/usr/local/emhttp/webGui/scripts/notify",
        timestamp_factory=lambda: "20260422T010204Z",
    ) as visibility:
        visibility.log_started()
        visibility.log_completed(notify=False)

    assert [call.argv[0] for call in runner.calls] == ["logger", "logger"]
    assert all(call.argv[0] != "/usr/local/emhttp/webGui/scripts/notify" for call in runner.calls)


def test_success_notification_runs_when_notify_is_available(tmp_path: Path) -> None:
    runner = RecordingRunner(executed=True)

    with open_reconcile_log(
        runner=runner,
        log_dir=tmp_path / "logs",
        notify_resolver=lambda _: "/usr/local/emhttp/webGui/scripts/notify",
        timestamp_factory=lambda: "20260422T010205Z",
    ) as visibility:
        visibility.log_success("reconcile complete", notify=True)

    assert [call.argv[0] for call in runner.calls] == [
        "logger",
        "/usr/local/emhttp/webGui/scripts/notify",
    ]


def test_missing_notify_is_warning_only_for_failures(tmp_path: Path) -> None:
    runner = RecordingRunner(executed=True)

    with open_reconcile_log(
        runner=runner,
        log_dir=tmp_path / "logs",
        notify_resolver=lambda _: None,
        timestamp_factory=lambda: "20260422T010206Z",
    ) as visibility:
        visibility.log_failure("reconcile failed")

    text = (tmp_path / "logs" / "reconcile-20260422T010206Z.log").read_text(encoding="utf-8")
    assert "reconcile failed" in text
    assert "notify command unavailable" in text
    assert [call.argv[0] for call in runner.calls] == ["logger", "logger"]


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
