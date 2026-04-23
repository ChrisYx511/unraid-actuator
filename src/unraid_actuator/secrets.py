import json
from pathlib import Path
from typing import cast

from .runner import CommandRunner, CommandSpec
from .schemas import validate_secret_env_structure


def decrypt_secret_env(*, host_root: Path, runner: CommandRunner) -> dict[str, object]:
    secret_path = host_root / "secret-env.ejson"
    validate_secret_env_structure(secret_path)
    result = runner.run(
        CommandSpec(
            argv=("ejson", "decrypt", "secret-env.ejson"),
            cwd=host_root,
            env={},
            inherit_env=True,
        )
    )
    if result.exit_code != 0:
        message = result.stderr or result.stdout or "ejson decrypt failed"
        raise ValueError(f"failed to decrypt secret-env.ejson: {message}")
    payload_text = "{}" if not result.executed else result.stdout
    try:
        payload = cast(object, json.loads(payload_text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"decrypted secret-env.ejson is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("decrypted secret-env.ejson must contain a top-level object")
    return cast(dict[str, object], payload)


def extract_environment_secrets(payload: dict[str, object], *, app: str, environment: str) -> dict[str, str]:
    app_payload = payload.get(app, {})
    if not isinstance(app_payload, dict):
        raise ValueError(f"decrypted secret-env.ejson app entry '{app}' must be an object")
    typed_app_payload = cast(dict[str, object], app_payload)
    environment_payload = typed_app_payload.get(environment, {})
    if not isinstance(environment_payload, dict):
        raise ValueError(f"decrypted secret-env.ejson environment entry '{app}/{environment}' must be an object")

    secrets: dict[str, str] = {}
    typed_environment_payload = cast(dict[str, object], environment_payload)
    for key, value in typed_environment_payload.items():
        if key.startswith("_"):
            continue
        if not isinstance(value, str):
            raise ValueError(f"decrypted secret-env.ejson variable '{app}/{environment}/{key}' must be a string")
        secrets[key] = value
    return secrets


__all__ = ["decrypt_secret_env", "extract_environment_secrets"]
