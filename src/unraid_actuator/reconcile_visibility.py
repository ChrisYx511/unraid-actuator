from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Callable, TextIO

from .runner import CommandResult, CommandRunner, CommandSpec, format_command

DEFAULT_RECONCILE_LOG_DIR = Path("/var/log/unraid-actuator")


class ReconcileVisibility(AbstractContextManager["ReconcileVisibility"]):
    def __init__(
        self,
        *,
        runner: CommandRunner,
        file_handle: TextIO,
        log_path: Path,
        notify_resolver: Callable[[str], str | None],
    ) -> None:
        self._runner = runner
        self._file_handle = file_handle
        self.log_path = log_path
        self._notify_resolver = notify_resolver

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self._file_handle.close()
        return None

    def log_started(self) -> None:
        self.log_event("reconcile started", syslog=True)

    def log_completed(self, *, notify: bool = False, message: str = "reconcile complete") -> None:
        self.log_success(message, notify=notify)

    def log_event(self, message: str, *, syslog: bool = False) -> None:
        self._write_lines("EVENT", message)
        if syslog:
            self._emit_syslog(message)

    def log_warning(self, message: str) -> None:
        self._write_lines("WARNING", message)
        self._emit_syslog(f"warning: {message}")

    def log_failure(self, message: str) -> None:
        self._write_lines("ERROR", message)
        self._emit_syslog(message)
        self._send_notify(message)

    def log_success(self, message: str, *, notify: bool = False) -> None:
        self._write_lines("SUCCESS", message)
        self._emit_syslog(message)
        if notify:
            self._send_notify(message)

    def log_command_result(
        self,
        result: CommandResult,
        *,
        summary: str | None = None,
        include_output: bool = False,
    ) -> None:
        lines = [
            f"COMMAND: {summary or format_command(result.argv)}",
            f"  exit_code={result.exit_code} executed={result.executed}",
        ]
        if include_output and result.stdout:
            lines.extend(("  stdout:", *[f"    {line}" for line in result.stdout.rstrip().splitlines()]))
        if include_output and result.stderr:
            lines.extend(("  stderr:", *[f"    {line}" for line in result.stderr.rstrip().splitlines()]))
        self._write_lines(*lines)

    def _emit_syslog(self, message: str) -> None:
        _ = self._runner.run(
            CommandSpec(
                argv=("logger", "-t", "unraid-actuator", message),
            )
        )

    def _send_notify(self, message: str) -> None:
        notify_path = self._notify_resolver("notify")
        if notify_path is None:
            self.log_warning("notify command unavailable; skipping Unraid notification")
            return
        _ = self._runner.run(
            CommandSpec(
                argv=(
                    notify_path,
                    "-e",
                    "unraid-actuator",
                    "-s",
                    "unraid-actuator",
                    "-d",
                    message,
                )
            )
        )

    def _write_lines(self, *lines: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for line in lines:
            _ = self._file_handle.write(f"[{timestamp}] {line}\n")
        self._file_handle.flush()


def open_reconcile_log(
    *,
    runner: CommandRunner,
    log_dir: Path = DEFAULT_RECONCILE_LOG_DIR,
    notify_resolver: Callable[[str], str | None] = shutil.which,
    timestamp_factory: Callable[[], str] | None = None,
) -> ReconcileVisibility:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp_factory() if timestamp_factory is not None else _default_log_timestamp()
    log_path = log_dir / f"reconcile-{timestamp}.log"
    file_handle = log_path.open("w", encoding="utf-8")
    return ReconcileVisibility(
        runner=runner,
        file_handle=file_handle,
        log_path=log_path,
        notify_resolver=notify_resolver,
    )


def _default_log_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


__all__ = ["DEFAULT_RECONCILE_LOG_DIR", "ReconcileVisibility", "open_reconcile_log"]
