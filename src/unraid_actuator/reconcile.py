from __future__ import annotations

from pathlib import Path

from .build import run_build_for_host
from .build_paths import promote_runtime_root, resolve_output_root
from .config import ACTIVE_CONFIG_PATH, load_active_config
from .deploy import run_deploy, run_teardown
from .reconcile_git import fast_forward_managed_checkout, inspect_managed_checkout, prepare_candidate_checkout
from .reconcile_lock import acquire_reconcile_lock
from .reconcile_models import ReconcileResult, ReconcileStatus, RemovedTargetsPlan
from .reconcile_plan import plan_removed_targets
from .reconcile_visibility import open_reconcile_log
from .runner import CommandRunner
from .validate import run_validate_for_host


def run_reconcile(
    *,
    runner: CommandRunner,
    config_path: Path = ACTIVE_CONFIG_PATH,
    dry_run: bool = False,
) -> ReconcileResult:
    with acquire_reconcile_lock():
        with open_reconcile_log(runner=runner) as visibility:
            visibility.log_started()
            try:
                config = load_active_config(path=config_path)
                current_host_root = config.source_path / config.hostname
                current_runtime_root = resolve_output_root(None)
                managed_state = inspect_managed_checkout(runner=runner, config_path=config_path)

                if managed_state.current_sha == managed_state.candidate_sha:
                    visibility.log_completed(notify=False)
                    return ReconcileResult(
                        status=ReconcileStatus.NOOP,
                        current_sha=managed_state.current_sha,
                        candidate_sha=managed_state.candidate_sha,
                        dry_run=dry_run,
                        removed_targets=(),
                        log_path=visibility.log_path,
                    )

                candidate_workspace = prepare_candidate_checkout(
                    runner=runner,
                    managed_state=managed_state,
                    config_path=config_path,
                )
                validation_report = run_validate_for_host(
                    runner=runner,
                    host_root=candidate_workspace.host_root,
                )
                if validation_report.has_errors:
                    raise ValueError(
                        f"incoming candidate validation failed with {validation_report.error_count} error(s)"
                    )
                candidate_build = run_build_for_host(
                    runner=runner,
                    host_root=candidate_workspace.host_root,
                    output_root=candidate_workspace.build_root,
                )
                removal_plan = plan_removed_targets(
                    current_host_root=current_host_root,
                    incoming_host_root=candidate_workspace.host_root,
                    current_runtime_root=current_runtime_root,
                )

                if dry_run:
                    detail = _dry_run_detail(removal_plan)
                    visibility.log_event(
                        f"reconcile dry-run candidate={managed_state.candidate_sha} removed={len(removal_plan.removed_declarations)} {detail}"
                    )
                    visibility.log_completed(notify=False)
                    return ReconcileResult(
                        status=ReconcileStatus.DRY_RUN,
                        current_sha=managed_state.current_sha,
                        candidate_sha=managed_state.candidate_sha,
                        dry_run=True,
                        removed_targets=removal_plan.removed_targets,
                        requires_current_rebuild=removal_plan.requires_current_rebuild,
                        detail=detail,
                        log_path=visibility.log_path,
                    )

                removal_plan = _ensure_current_runtime_for_removals(
                    runner=runner,
                    config_path=config_path,
                    current_host_root=current_host_root,
                    current_runtime_root=current_runtime_root,
                    incoming_host_root=candidate_workspace.host_root,
                    removal_plan=removal_plan,
                    visibility=visibility,
                )

                for target in removal_plan.removed_declarations:
                    teardown_result = run_teardown(
                        runner=runner,
                        config_path=config_path,
                        build_root=current_runtime_root,
                        app=target.app,
                        environment=target.environment,
                    )
                    _log_runtime_action(
                        visibility,
                        teardown_result.command_results,
                        summary=f"teardown {target.app}/{target.environment}",
                    )

                deploy_result = run_deploy(
                    runner=runner,
                    config_path=config_path,
                    build_root=candidate_build.output_root,
                )
                _log_runtime_action(
                    visibility,
                    deploy_result.command_results,
                    summary="deploy desired state",
                )
                promote_runtime_root(candidate_build.output_root, current_runtime_root)
                fast_forward_result = fast_forward_managed_checkout(
                    runner=runner,
                    managed_state=managed_state,
                )
                visibility.log_command_result(
                    fast_forward_result,
                    summary="fast-forward managed checkout",
                    include_output=False,
                )
                visibility.log_completed(notify=True)
                return ReconcileResult(
                    status=ReconcileStatus.APPLIED,
                    current_sha=managed_state.current_sha,
                    candidate_sha=managed_state.candidate_sha,
                    dry_run=False,
                    removed_targets=removal_plan.removed_targets,
                    log_path=visibility.log_path,
                )
            except Exception as exc:
                visibility.log_failure(str(exc))
                raise


def _ensure_current_runtime_for_removals(
    *,
    runner: CommandRunner,
    config_path: Path,
    current_host_root: Path,
    current_runtime_root: Path,
    incoming_host_root: Path,
    removal_plan: RemovedTargetsPlan,
    visibility,
) -> RemovedTargetsPlan:
    if not removal_plan.requires_current_rebuild:
        return removal_plan

    run_build_for_host(
        runner=runner,
        host_root=current_host_root,
        output_root=current_runtime_root,
    )
    visibility.log_event("rebuilt current runtime tree from managed checkout for removals")
    refreshed_plan = plan_removed_targets(
        current_host_root=current_host_root,
        incoming_host_root=incoming_host_root,
        current_runtime_root=current_runtime_root,
    )
    if refreshed_plan.requires_current_rebuild:
        raise ValueError("current runtime tree could not be rebuilt safely for removals")
    return refreshed_plan


def _log_runtime_action(visibility, command_results, *, summary: str) -> None:
    for result in command_results:
        visibility.log_command_result(result, summary=summary, include_output=True)


def _dry_run_detail(removal_plan: RemovedTargetsPlan) -> str:
    if removal_plan.requires_current_rebuild:
        return "would rebuild current runtime tree before removals"
    if removal_plan.removed_declarations:
        return "would tear down removed targets before apply"
    return "no removals required"


__all__ = ["run_reconcile"]
