from pathlib import Path

from unraid_actuator.discovery import (
    discover_host_tree,
    find_missing_declared_environments,
)
from unraid_actuator.validation_models import DeclaredEnvironment, SourceKind


def test_discovery_walks_host_tree_and_marks_declared_targets(tmp_path: Path) -> None:
    host_root = tmp_path / "PotatoServer"
    declared = (DeclaredEnvironment(app="nextcloud", environment="production"),)
    (host_root / "nextcloud" / "production").mkdir(parents=True)
    (host_root / "nextcloud" / "production" / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (host_root / "immich" / "preview").mkdir(parents=True)
    (host_root / "immich" / "preview" / "template.yaml").write_text(
        "template:\n  include:\n    - compose.yaml.j2\n",
        encoding="utf-8",
    )
    (host_root / "immich" / "preview" / "values.yml").write_text("image: busybox\n", encoding="utf-8")

    discovered = discover_host_tree(host_root, declared)

    assert [(item.app, item.environment, item.declared) for item in discovered] == [
        ("immich", "preview", False),
        ("nextcloud", "production", True),
    ]
    assert discovered[0].source_kind == SourceKind.TEMPLATE
    assert discovered[1].source_kind == SourceKind.COMPOSE


def test_source_classification_covers_missing_and_ambiguous_inputs(
    tmp_path: Path,
) -> None:
    host_root = tmp_path / "PotatoServer"
    (host_root / "missing" / "prod").mkdir(parents=True)
    (host_root / "ambiguous" / "prod").mkdir(parents=True)
    (host_root / "ambiguous" / "prod" / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (host_root / "ambiguous" / "prod" / "template.yml").write_text(
        "template:\n  include:\n    - compose.yaml.j2\n",
        encoding="utf-8",
    )
    (host_root / "ambiguous" / "prod" / "values.yaml").write_text("image: busybox\n", encoding="utf-8")
    (host_root / "duplicate-template" / "prod").mkdir(parents=True)
    (host_root / "duplicate-template" / "prod" / "template.yml").write_text(
        "template:\n  include:\n    - one.j2\n",
        encoding="utf-8",
    )
    (host_root / "duplicate-template" / "prod" / "template.yaml").write_text(
        "template:\n  include:\n    - two.j2\n",
        encoding="utf-8",
    )
    (host_root / "duplicate-template" / "prod" / "values.yml").write_text("image: busybox\n", encoding="utf-8")

    discovered = discover_host_tree(host_root, ())

    kinds = {(item.app, item.environment): item.source_kind for item in discovered}
    assert kinds[("missing", "prod")] == SourceKind.MISSING
    assert kinds[("ambiguous", "prod")] == SourceKind.AMBIGUOUS
    assert kinds[("duplicate-template", "prod")] == SourceKind.AMBIGUOUS


def test_find_missing_declared_environments_reports_absent_paths(
    tmp_path: Path,
) -> None:
    host_root = tmp_path / "PotatoServer"
    (host_root / "nextcloud" / "production").mkdir(parents=True)
    declared = (
        DeclaredEnvironment(app="nextcloud", environment="production"),
        DeclaredEnvironment(app="postgres", environment="production"),
    )

    missing = find_missing_declared_environments(host_root, declared)

    assert missing == (DeclaredEnvironment(app="postgres", environment="production"),)
