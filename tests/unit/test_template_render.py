from pathlib import Path

import pytest

from unraid_actuator.template_render import render_template_environment


def test_template_render_preserves_include_order(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yaml").write_text(
        "template:\n  include:\n    - 01-header.j2\n    - 02-body.j2\n",
        encoding="utf-8",
    )
    (env_root / "values.yml").write_text("image: nginx:latest\n", encoding="utf-8")
    (env_root / "01-header.j2").write_text("services:\n", encoding="utf-8")
    (env_root / "02-body.j2").write_text("  app:\n    image: {{ image }}\n", encoding="utf-8")

    rendered = render_template_environment(
        env_root=env_root,
        template_path=env_root / "template.yaml",
        values_path=env_root / "values.yml",
    )

    assert rendered == "services:\n  app:\n    image: nginx:latest"


def test_template_render_rejects_paths_outside_environment_root(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yml").write_text("template:\n  include:\n    - ../shared.j2\n", encoding="utf-8")
    (env_root / "values.yaml").write_text("image: nginx:latest\n", encoding="utf-8")
    (tmp_path / "nextcloud" / "shared.j2").write_text("services: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes environment root"):
        render_template_environment(
            env_root=env_root,
            template_path=env_root / "template.yml",
            values_path=env_root / "values.yaml",
        )


def test_template_render_fails_on_undefined_values(tmp_path: Path) -> None:
    env_root = tmp_path / "nextcloud" / "production"
    env_root.mkdir(parents=True)
    (env_root / "template.yml").write_text("template:\n  include:\n    - compose.j2\n", encoding="utf-8")
    (env_root / "values.yaml").write_text("tag: latest\n", encoding="utf-8")
    (env_root / "compose.j2").write_text("image: {{ image }}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="undefined"):
        render_template_environment(
            env_root=env_root,
            template_path=env_root / "template.yml",
            values_path=env_root / "values.yaml",
        )
