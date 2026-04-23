from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strictyaml import Map, Str, YAMLValidationError, as_document, load

ACTIVE_CONFIG_PATH = Path("/tmp/actuator-cfg.yml")
ACTIVE_CONFIG_SCHEMA = Map(
    {
        "repo_url": Str(),
        "deploy_branch": Str(),
        "hostname": Str(),
        "source_path": Str(),
    }
)


@dataclass(frozen=True)
class ActiveConfig:
    repo_url: str
    deploy_branch: str
    hostname: str
    source_path: Path


def save_active_config(config: ActiveConfig, *, path: Path = ACTIVE_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = as_document(
        {
            "repo_url": config.repo_url,
            "deploy_branch": config.deploy_branch,
            "hostname": config.hostname,
            "source_path": str(config.source_path),
        },
        ACTIVE_CONFIG_SCHEMA,
    )
    path.write_text(document.as_yaml(), encoding="utf-8")


def load_active_config(*, path: Path = ACTIVE_CONFIG_PATH) -> ActiveConfig:
    document = load(path.read_text(encoding="utf-8"), ACTIVE_CONFIG_SCHEMA)
    data = document.data
    return ActiveConfig(
        repo_url=data["repo_url"],
        deploy_branch=data["deploy_branch"],
        hostname=data["hostname"],
        source_path=Path(data["source_path"]),
    )


__all__ = [
    "ACTIVE_CONFIG_PATH",
    "ACTIVE_CONFIG_SCHEMA",
    "ActiveConfig",
    "YAMLValidationError",
    "load_active_config",
    "save_active_config",
]
