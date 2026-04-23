from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path

from dotenv import dotenv_values

_RAW_ENV_VALUE_RE = re.compile(r"^[A-Za-z0-9_./:-]+$")


def materialize_env_file(*, env_file: Path | None, secrets: Mapping[str, str]) -> str:
    base_values: dict[str, str] = {}
    if env_file is not None and env_file.is_file():
        parsed = dotenv_values(env_file, interpolate=False)
        for key, value in parsed.items():
            if value is None:
                raise ValueError(f".env entry '{key}' must include an explicit value")
            base_values[key] = value

    merged = {**base_values, **dict(secrets)}
    lines = [f"{key}={_serialize_env_value(value)}" for key, value in sorted(merged.items())]
    return "\n".join(lines) + "\n"


def _serialize_env_value(value: str) -> str:
    if _RAW_ENV_VALUE_RE.fullmatch(value):
        return value
    return json.dumps(value)


__all__ = ["materialize_env_file"]
