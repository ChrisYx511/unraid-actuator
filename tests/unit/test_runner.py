from __future__ import annotations

from unraid_actuator.runner import (
    CommandSpec,
    DryRunRunner,
    RecordingRunner,
    format_command,
)


def test_dry_run_runner_returns_non_executed_result(sample_command_spec) -> None:
    result = DryRunRunner().run(sample_command_spec)

    assert result.executed is False
    assert result.exit_code == 0
    assert result.argv == sample_command_spec.argv
    assert result.cwd == sample_command_spec.cwd
    assert result.env == {"EXAMPLE_FLAG": "1"}
    assert result.stdin_text is None
    assert result.inherit_env is True
    assert result.stdout == "DRY RUN: git status"


def test_recording_runner_captures_call(sample_command_spec) -> None:
    runner = RecordingRunner(stdout="ok", executed=False)

    result = runner.run(sample_command_spec)

    assert runner.calls == [sample_command_spec]
    assert result.stdout == "ok"
    assert result.executed is False


def test_command_spec_supports_stdin_and_env_scrubbing() -> None:
    spec = CommandSpec(
        argv=("docker", "compose", "config"),
        stdin_text="services: {}\n",
        inherit_env=False,
    )

    result = RecordingRunner(executed=True).run(spec)

    assert result.stdin_text == "services: {}\n"
    assert result.inherit_env is False


def test_format_command_quotes_arguments() -> None:
    assert format_command(("python", "-c", "print('hello world')")) == "python -c 'print('\"'\"'hello world'\"'\"')'"
