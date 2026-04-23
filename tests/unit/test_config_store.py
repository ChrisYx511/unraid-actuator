from pathlib import Path

import pytest

from unraid_actuator.config import (
    ActiveConfig,
    YAMLValidationError,
    load_active_config,
    save_active_config,
)


def test_save_and_load_active_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "nested" / "actuator-cfg.yml"
    config = ActiveConfig(
        repo_url="https://example.com/infrastructure.git",
        deploy_branch="deploy",
        hostname="PotatoServer",
        source_path=Path("/mnt/user/appdata/unraid-actuator/source"),
    )

    save_active_config(config, path=config_path)

    assert config_path.exists()
    assert load_active_config(path=config_path) == config


def test_load_rejects_extra_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "actuator-cfg.yml"
    config_path.write_text(
        "\n".join(
            [
                "repo_url: https://example.com/infrastructure.git",
                "deploy_branch: deploy",
                "hostname: PotatoServer",
                "source_path: /mnt/user/appdata/unraid-actuator/source",
                "extra_key: nope",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(YAMLValidationError):
        load_active_config(path=config_path)


def test_load_rejects_missing_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "actuator-cfg.yml"
    config_path.write_text(
        "\n".join(
            [
                "repo_url: https://example.com/infrastructure.git",
                "hostname: PotatoServer",
                "source_path: /mnt/user/appdata/unraid-actuator/source",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(YAMLValidationError):
        load_active_config(path=config_path)
