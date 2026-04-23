from pathlib import Path

import pytest

from unraid_actuator.env_materialize import materialize_env_file


def test_secret_values_override_non_secret_env(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("A=1\nSECRET=plain\n", encoding="utf-8")

    rendered = materialize_env_file(env_file=env_file, secrets={"SECRET": "cipher", "Z": "last"})

    assert rendered == "A=1\nSECRET=cipher\nZ=last\n"


def test_missing_env_file_still_materializes_secrets() -> None:
    rendered = materialize_env_file(env_file=None, secrets={"SECRET": "cipher"})

    assert rendered == "SECRET=cipher\n"


def test_bare_env_key_is_rejected(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("BROKEN\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must include an explicit value"):
        materialize_env_file(env_file=env_file, secrets={})


def test_env_serialization_is_stable_and_quotes_special_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("PLAIN=value\n", encoding="utf-8")

    rendered = materialize_env_file(env_file=env_file, secrets={"SPACED": "hello world", "HASHY": "a#b"})

    assert rendered == 'HASHY="a#b"\nPLAIN=value\nSPACED="hello world"\n'
