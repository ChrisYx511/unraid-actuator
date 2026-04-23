from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator.runner import CommandSpec


@pytest.fixture
def sample_command_spec(tmp_path: Path) -> CommandSpec:
    return CommandSpec(
        argv=("git", "status"),
        cwd=tmp_path,
        env={"EXAMPLE_FLAG": "1"},
    )
