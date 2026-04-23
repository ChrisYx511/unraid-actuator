from dataclasses import dataclass
from pathlib import Path

from .config import ACTIVE_CONFIG_PATH, ActiveConfig, save_active_config
from .runner import CommandResult, CommandRunner, CommandSpec


@dataclass(frozen=True)
class InitResult:
    config: ActiveConfig
    clone_result: CommandResult | None
    cloned: bool
    reused_existing: bool


def run_init(
    config: ActiveConfig,
    *,
    runner: CommandRunner,
    dry_run: bool,
    config_path: Path = ACTIVE_CONFIG_PATH,
) -> InitResult:
    source_path = config.source_path

    if source_path.exists() and not source_path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_path}")

    should_clone = not source_path.exists() or _is_empty_directory(source_path)

    clone_result: CommandResult | None = None
    if should_clone:
        if not dry_run:
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.mkdir(parents=True, exist_ok=True)
        clone_result = runner.run(
            CommandSpec(
                argv=(
                    "git",
                    "clone",
                    "--branch",
                    config.deploy_branch,
                    "--single-branch",
                    config.repo_url,
                    str(source_path),
                )
            )
        )
        if clone_result.exit_code != 0:
            detail = clone_result.stderr or clone_result.stdout or "git clone failed"
            raise RuntimeError(detail)

    if not dry_run:
        save_active_config(config, path=config_path)

    return InitResult(
        config=config,
        clone_result=clone_result,
        cloned=should_clone,
        reused_existing=not should_clone,
    )


def _is_empty_directory(path: Path) -> bool:
    if not path.exists():
        return True
    return not any(path.iterdir())
