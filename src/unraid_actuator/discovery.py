from pathlib import Path

from .validation_models import DeclaredEnvironment, DiscoveredEnvironment, SourceKind


def discover_host_tree(host_root: Path, declared: tuple[DeclaredEnvironment, ...]) -> tuple[DiscoveredEnvironment, ...]:
    declared_set = {(item.app, item.environment) for item in declared}
    discovered: list[DiscoveredEnvironment] = []

    if not host_root.exists():
        return ()

    for app_dir in sorted(
        (path for path in host_root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    ):
        for environment_dir in sorted(
            (path for path in app_dir.iterdir() if path.is_dir()),
            key=lambda path: path.name,
        ):
            compose_files = tuple(
                candidate
                for candidate in (
                    environment_dir / "docker-compose.yml",
                    environment_dir / "docker-compose.yaml",
                )
                if candidate.is_file()
            )
            template_files = tuple(
                candidate
                for candidate in (
                    environment_dir / "template.yaml",
                    environment_dir / "template.yml",
                )
                if candidate.is_file()
            )
            values_files = tuple(
                candidate
                for candidate in (
                    environment_dir / "values.yaml",
                    environment_dir / "values.yml",
                )
                if candidate.is_file()
            )
            discovered.append(
                DiscoveredEnvironment(
                    app=app_dir.name,
                    environment=environment_dir.name,
                    path=environment_dir,
                    declared=(app_dir.name, environment_dir.name) in declared_set,
                    source_kind=_classify_source(compose_files, template_files, values_files),
                    compose_files=compose_files,
                    template_file=template_files[0] if len(template_files) == 1 else None,
                    values_file=values_files[0] if len(values_files) == 1 else None,
                )
            )

    return tuple(discovered)


def find_missing_declared_environments(
    host_root: Path,
    declared: tuple[DeclaredEnvironment, ...],
) -> tuple[DeclaredEnvironment, ...]:
    missing = [target for target in declared if not (host_root / target.app / target.environment).is_dir()]
    return tuple(missing)


def _classify_source(
    compose_files: tuple[Path, ...],
    template_files: tuple[Path, ...],
    values_files: tuple[Path, ...],
) -> SourceKind:
    if len(compose_files) == 1 and not template_files and not values_files:
        return SourceKind.COMPOSE
    if not compose_files and len(template_files) == 1 and len(values_files) == 1:
        return SourceKind.TEMPLATE
    if not compose_files and not template_files and not values_files:
        return SourceKind.MISSING
    return SourceKind.AMBIGUOUS
