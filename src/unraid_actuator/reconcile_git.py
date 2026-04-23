import shutil
from pathlib import Path

from .config import ACTIVE_CONFIG_PATH, load_active_config
from .reconcile_models import CandidateWorkspace, ManagedCheckoutState
from .runner import CommandResult, CommandRunner, CommandSpec

DEFAULT_INCOMING_ROOT = Path("/tmp/unraid-actuator/incoming")


def inspect_managed_checkout(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
) -> ManagedCheckoutState:
    config = load_active_config(path=config_path)
    source_path = config.source_path

    status_result = _run_git(
        runner,
        source_path,
        "status",
        "--porcelain=v2",
        "--branch",
    )
    if _has_worktree_changes(status_result.stdout):
        raise ValueError("managed source checkout has uncommitted changes")

    _run_git(runner, source_path, "fetch", "--prune", "origin", config.deploy_branch)
    current_sha = _read_git_stdout(runner, source_path, "rev-parse", "HEAD")
    candidate_sha = _read_git_stdout(runner, source_path, "rev-parse", "FETCH_HEAD")

    ancestry_result = runner.run(
        CommandSpec(
            argv=("git", "merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD"),
            cwd=source_path,
        )
    )
    if ancestry_result.exit_code != 0:
        raise ValueError(
            f"managed source checkout is not a clean fast-forward ancestor of origin/{config.deploy_branch}"
        )

    return ManagedCheckoutState(
        current_sha=current_sha,
        candidate_sha=candidate_sha,
        source_path=source_path,
        branch=config.deploy_branch,
    )


def prepare_candidate_checkout(
    *,
    runner: CommandRunner,
    managed_state: ManagedCheckoutState,
    config_path: Path = ACTIVE_CONFIG_PATH,
    work_root: Path = DEFAULT_INCOMING_ROOT,
) -> CandidateWorkspace:
    config = load_active_config(path=config_path)
    workspace_root = work_root / managed_state.candidate_sha
    checkout_root = workspace_root / "checkout"
    build_root = workspace_root / "build"

    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)

    _run_git(
        runner,
        None,
        "clone",
        "--branch",
        managed_state.branch,
        "--single-branch",
        config.repo_url,
        str(checkout_root),
    )
    checkout_root.mkdir(parents=True, exist_ok=True)
    _run_git(runner, checkout_root, "checkout", "--detach", managed_state.candidate_sha)

    return CandidateWorkspace(
        checkout_root=checkout_root,
        host_root=checkout_root / config.hostname,
        build_root=build_root,
        candidate_sha=managed_state.candidate_sha,
    )


def fast_forward_managed_checkout(
    *,
    runner: CommandRunner,
    managed_state: ManagedCheckoutState,
) -> CommandResult:
    return _run_git(
        runner,
        managed_state.source_path,
        "merge",
        "--ff-only",
        managed_state.candidate_sha,
    )


def _read_git_stdout(
    runner: CommandRunner,
    cwd: Path,
    *args: str,
) -> str:
    result = _run_git(runner, cwd, *args)
    return result.stdout.strip()


def _run_git(
    runner: CommandRunner,
    cwd: Path | None,
    *args: str,
) -> CommandResult:
    result = runner.run(CommandSpec(argv=("git", *args), cwd=cwd))
    if result.exit_code != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(detail)
    return result


def _has_worktree_changes(stdout: str) -> bool:
    return any(line and not line.startswith("#") for line in stdout.splitlines())


__all__ = [
    "DEFAULT_INCOMING_ROOT",
    "fast_forward_managed_checkout",
    "inspect_managed_checkout",
    "prepare_candidate_checkout",
]
