from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, TypedDict, cast

import strictyaml
from strictyaml import Any as StrictAny
from strictyaml import Map, MapPattern, Seq, Str, YAMLValidationError

from .validation_models import DeclaredEnvironment

APPS_SCHEMA = Map({"apps": MapPattern(Str(), Seq(Str()))})
TEMPLATE_SCHEMA = Map({"template": Map({"include": Seq(Str())})})
VALUES_SCHEMA = MapPattern(Str(), StrictAny())
PUBLIC_KEY_RE = re.compile(r"^[0-9a-f]{64}$")
ENV_KEY_RE = re.compile(r"^[A-Z0-9_]+$")
STRICT_LOAD = cast(Any, strictyaml.load)


class AppsYamlData(TypedDict):
    apps: dict[str, list[str]]


class TemplateDescriptorSection(TypedDict):
    include: list[str]


class TemplateDescriptorData(TypedDict):
    template: TemplateDescriptorSection


def load_apps_yaml(path: Path) -> tuple[DeclaredEnvironment, ...]:
    document = STRICT_LOAD(path.read_text(encoding="utf-8"), APPS_SCHEMA)
    data = cast(AppsYamlData, document.data)
    declared: list[DeclaredEnvironment] = []
    for app, environments in data["apps"].items():
        for environment in environments:
            declared.append(DeclaredEnvironment(app=app, environment=environment))
    return tuple(declared)


def resolve_host_apps_path(host_root: Path) -> Path:
    return resolve_yaml_path(host_root, "apps")


def load_declared_environments(host_root: Path) -> tuple[DeclaredEnvironment, ...]:
    return load_apps_yaml(resolve_host_apps_path(host_root))


def resolve_template_path(environment_root: Path) -> Path:
    return resolve_yaml_path(environment_root, "template")


def resolve_values_path(environment_root: Path) -> Path:
    return resolve_yaml_path(environment_root, "values")


def load_template_descriptor(path: Path) -> tuple[str, ...]:
    document = STRICT_LOAD(path.read_text(encoding="utf-8"), TEMPLATE_SCHEMA)
    data = cast(TemplateDescriptorData, document.data)
    return tuple(data["template"]["include"])


def load_values_yaml(path: Path) -> dict[str, object]:
    document = STRICT_LOAD(path.read_text(encoding="utf-8"), VALUES_SCHEMA)
    return dict(cast(dict[str, object], document.data))


def validate_secret_env_structure(path: Path) -> None:
    try:
        data = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError as exc:
        raise ValueError(f"secret-env.ejson not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"secret-env.ejson is not valid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("secret-env.ejson must contain a top-level object")

    typed_data = cast(dict[str, object], data)
    public_key = typed_data.get("_public_key")
    if not isinstance(public_key, str) or not PUBLIC_KEY_RE.fullmatch(public_key):
        raise ValueError("secret-env.ejson must include a 64-character lowercase hex _public_key")

    for app, environments in typed_data.items():
        if app.startswith("_"):
            continue
        if not isinstance(environments, dict):
            raise ValueError(f"secret-env.ejson app entry '{app}' must be an object keyed by environment")
        typed_environments = cast(dict[str, object], environments)
        for environment, values in typed_environments.items():
            if environment.startswith("_"):
                continue
            if not isinstance(values, dict):
                raise ValueError(
                    f"secret-env.ejson environment entry '{app}/{environment}' must be an object keyed by variable name"
                )
            typed_values = cast(dict[str, object], values)
            for key, value in typed_values.items():
                if key.startswith("_"):
                    continue
                if not ENV_KEY_RE.fullmatch(key):
                    raise ValueError(f"secret-env.ejson variable '{app}/{environment}/{key}' is not env-style")
                if not isinstance(value, str):
                    raise ValueError(f"secret-env.ejson variable '{app}/{environment}/{key}' must be a string")


def resolve_yaml_path(directory: Path, stem: str) -> Path:
    matches = [
        candidate
        for candidate in (
            directory / f"{stem}.yaml",
            directory / f"{stem}.yml",
        )
        if candidate.is_file()
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"{stem}.yaml or {stem}.yml not found in {directory}")
    names = ", ".join(path.name for path in matches)
    raise ValueError(f"multiple {stem} YAML files found in {directory}: {names}")


__all__ = [
    "APPS_SCHEMA",
    "TEMPLATE_SCHEMA",
    "VALUES_SCHEMA",
    "YAMLValidationError",
    "load_apps_yaml",
    "load_declared_environments",
    "load_template_descriptor",
    "load_values_yaml",
    "resolve_host_apps_path",
    "resolve_template_path",
    "resolve_values_path",
    "resolve_yaml_path",
    "validate_secret_env_structure",
]
