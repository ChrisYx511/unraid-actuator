from pathlib import Path

import pytest

from unraid_actuator.runner import CommandResult, RecordingRunner
from unraid_actuator.secrets import decrypt_secret_env, extract_environment_secrets


def test_decrypt_secret_env_runs_ejson_decrypt(tmp_path: Path) -> None:
    host_root = tmp_path / "PotatoServer"
    host_root.mkdir()
    (host_root / "secret-env.ejson").write_text(
        '{"_public_key":"' + ("a" * 64) + '"}',
        encoding="utf-8",
    )
    runner = RecordingRunner(
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=True,
                exit_code=0,
                stdout='{"_public_key":"' + ("a" * 64) + '","nextcloud":{"production":{"DB_PASSWORD":"cipher"}}}',
                stderr="",
                executed=True,
            )
        ]
    )

    payload = decrypt_secret_env(host_root=host_root, runner=runner)

    assert payload["nextcloud"]["production"]["DB_PASSWORD"] == "cipher"
    assert runner.calls[0].argv == ("ejson", "decrypt", "secret-env.ejson")
    assert runner.calls[0].cwd == host_root


def test_decrypt_secret_env_rejects_malformed_json(tmp_path: Path) -> None:
    host_root = tmp_path / "PotatoServer"
    host_root.mkdir()
    (host_root / "secret-env.ejson").write_text(
        '{"_public_key":"' + ("a" * 64) + '"}',
        encoding="utf-8",
    )
    runner = RecordingRunner(
        results=[
            CommandResult(
                argv=(),
                cwd=None,
                env={},
                stdin_text=None,
                inherit_env=True,
                exit_code=0,
                stdout="{not-json",
                stderr="",
                executed=True,
            )
        ]
    )

    with pytest.raises(ValueError, match="not valid JSON"):
        decrypt_secret_env(host_root=host_root, runner=runner)


def test_extract_environment_secrets_allows_missing_blocks() -> None:
    assert extract_environment_secrets({"nextcloud": {}}, app="nextcloud", environment="production") == {}
