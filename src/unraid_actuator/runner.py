from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import shlex
import subprocess
from typing import Mapping, Protocol


@dataclass(frozen=True)
class CommandSpec:
    argv: tuple[str, ...]
    cwd: Path | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    stdin_text: str | None = None
    inherit_env: bool = True


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: Path | None
    env: dict[str, str]
    stdin_text: str | None
    inherit_env: bool
    exit_code: int
    stdout: str
    stderr: str
    executed: bool


class CommandRunner(Protocol):
    def run(self, spec: CommandSpec) -> CommandResult: ...


def format_command(argv: tuple[str, ...]) -> str:
    return shlex.join(argv)


class SubprocessRunner:
    def run(self, spec: CommandSpec) -> CommandResult:
        completed = subprocess.run(
            spec.argv,
            cwd=spec.cwd,
            env={**os.environ, **spec.env} if spec.inherit_env else dict(spec.env),
            text=True,
            capture_output=True,
            input=spec.stdin_text,
            check=False,
        )
        return CommandResult(
            argv=spec.argv,
            cwd=spec.cwd,
            env=dict(spec.env),
            stdin_text=spec.stdin_text,
            inherit_env=spec.inherit_env,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            executed=True,
        )


class DryRunRunner:
    def run(self, spec: CommandSpec) -> CommandResult:
        return CommandResult(
            argv=spec.argv,
            cwd=spec.cwd,
            env=dict(spec.env),
            stdin_text=spec.stdin_text,
            inherit_env=spec.inherit_env,
            exit_code=0,
            stdout=f"DRY RUN: {format_command(spec.argv)}",
            stderr="",
            executed=False,
        )


class RecordingRunner:
    def __init__(
        self,
        *,
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
        executed: bool = False,
        results: list[CommandResult] | None = None,
    ) -> None:
        self.calls: list[CommandSpec] = []
        self._exit_code = exit_code
        self._stdout = stdout
        self._stderr = stderr
        self._executed = executed
        self._results = list(results or [])

    def run(self, spec: CommandSpec) -> CommandResult:
        self.calls.append(spec)
        if self._results:
            result = self._results.pop(0)
            return CommandResult(
                argv=spec.argv,
                cwd=spec.cwd,
                env=dict(spec.env),
                stdin_text=spec.stdin_text,
                inherit_env=spec.inherit_env,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                executed=result.executed,
            )
        return CommandResult(
            argv=spec.argv,
            cwd=spec.cwd,
            env=dict(spec.env),
            stdin_text=spec.stdin_text,
            inherit_env=spec.inherit_env,
            exit_code=self._exit_code,
            stdout=self._stdout,
            stderr=self._stderr,
            executed=self._executed,
        )
