from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .build import run_build
from .config import ACTIVE_CONFIG_PATH, ActiveConfig
from .deploy import run_deploy, run_teardown
from .deploy_models import RuntimeActionResult
from .init import InitResult, run_init
from .reconcile import run_reconcile
from .reconcile_models import ReconcileResult
from .report import render_validation_report
from .runner import CommandRunner, DryRunRunner, SubprocessRunner
from .schemas import YAMLValidationError
from .validate import run_validate


def _build_common_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="Print external actions without executing them.",
    )
    return common


def build_parser() -> argparse.ArgumentParser:
    common = _build_common_parser()
    parser = argparse.ArgumentParser(
        prog="unraid-actuator",
        description="Reconcile Git-managed Docker Compose state for a single Unraid host.",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Save active source settings and optionally clone the source repository.",
        description="Configure the managed infrastructure source checkout for this host.",
    )
    init_parser.add_argument("--repo-url", required=True, help="Git URL for the source repository.")
    init_parser.add_argument(
        "--deploy-branch",
        required=True,
        help="Branch to reconcile and deploy from.",
    )
    init_parser.add_argument("--hostname", required=True, help="Host directory to target in the repo.")
    init_parser.add_argument(
        "--source-path",
        default="/mnt/user/appdata/unraid-actuator/source",
        help="Managed checkout path for the source repository.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate the configured host tree or one specific app/environment.",
        description="Validate declared and discovered host state before build or deploy.",
    )
    validate_parser.add_argument("--app", help="Validate only one app when paired with --environment.")
    validate_parser.add_argument(
        "--environment",
        help="Validate only one environment when paired with --app.",
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Build a normalized runtime tree for the configured host.",
        description="Render, normalize, and materialize the configured host tree into an actuator-managed output path.",
    )
    build_parser.add_argument(
        "--output-path",
        help="Custom output path. If omitted, the default /tmp/unraid-actuator/build is used.",
    )

    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Apply one actuator-built runtime tree or one scoped target.",
        description="Deploy the default or selected actuator-built runtime tree with safe scope handling.",
    )
    deploy_parser.add_argument(
        "--build-root",
        help="Custom runtime-tree root. If omitted, the default /tmp/unraid-actuator/build is used.",
    )
    deploy_parser.add_argument("--app", help="Deploy only one app when paired with --environment.")
    deploy_parser.add_argument(
        "--environment",
        help="Deploy only one environment when paired with --app.",
    )

    teardown_parser = subparsers.add_parser(
        "teardown",
        help="Tear down one actuator-built runtime tree or one scoped target.",
        description="Run docker compose down against the default or selected actuator-built runtime tree.",
    )
    teardown_parser.add_argument(
        "--build-root",
        help="Custom runtime-tree root. If omitted, the default /tmp/unraid-actuator/build is used.",
    )
    teardown_parser.add_argument("--app", help="Tear down only one app when paired with --environment.")
    teardown_parser.add_argument(
        "--environment",
        help="Tear down only one environment when paired with --app.",
    )

    reconcile_parser = subparsers.add_parser(
        "reconcile",
        help="Reconcile the configured deploy branch into the running host state.",
        description=(
            "Fetch, validate, build, and apply the configured deploy branch with explicit reconcile dry-run semantics."
        ),
    )
    reconcile_parser.add_argument(
        "--dry-run",
        dest="reconcile_dry_run",
        action="store_true",
        help="Inspect and plan reconcile work without mutating the managed source or runtime tree.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    config_path: Path = ACTIVE_CONFIG_PATH,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        config = ActiveConfig(
            repo_url=args.repo_url,
            deploy_branch=args.deploy_branch,
            hostname=args.hostname,
            source_path=Path(args.source_path),
        )
        selected_runner = runner or _resolve_runner(args.dry_run)
        result = run_init(
            config,
            runner=selected_runner,
            dry_run=args.dry_run,
            config_path=config_path,
        )
        print(_format_init_result(result))
        return 0

    if args.command == "validate":
        if bool(args.app) != bool(args.environment):
            parser.error("--app and --environment must be provided together")
        selected_runner = runner or _resolve_runner(args.dry_run)
        try:
            report = run_validate(
                runner=selected_runner,
                config_path=config_path,
                app=args.app,
                environment=args.environment,
            )
        except (YAMLValidationError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        hostname = _load_hostname(config_path)
        print(render_validation_report(report, hostname=hostname))
        return 1 if report.has_errors else 0

    if args.command == "build":
        selected_runner = runner or _resolve_runner(args.dry_run)
        try:
            result = run_build(
                runner=selected_runner,
                config_path=config_path,
                output_root=Path(args.output_path) if args.output_path else None,
            )
        except (YAMLValidationError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Built runtime tree at {result.output_root}")
        return 0

    if args.command == "deploy":
        if bool(args.app) != bool(args.environment):
            parser.error("--app and --environment must be provided together")
        selected_runner = runner or _resolve_runner(args.dry_run)
        try:
            result = run_deploy(
                runner=selected_runner,
                config_path=config_path,
                build_root=Path(args.build_root) if args.build_root else None,
                app=args.app,
                environment=args.environment,
            )
        except (YAMLValidationError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(_format_runtime_action("Deployed", result))
        return 0

    if args.command == "teardown":
        if bool(args.app) != bool(args.environment):
            parser.error("--app and --environment must be provided together")
        selected_runner = runner or _resolve_runner(args.dry_run)
        try:
            result = run_teardown(
                runner=selected_runner,
                config_path=config_path,
                build_root=Path(args.build_root) if args.build_root else None,
                app=args.app,
                environment=args.environment,
            )
        except (YAMLValidationError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(_format_runtime_action("Tore down", result))
        return 0

    if args.command == "reconcile":
        reconcile_dry_run = args.dry_run or getattr(args, "reconcile_dry_run", False)
        selected_runner = runner or SubprocessRunner()
        try:
            result = run_reconcile(
                runner=selected_runner,
                config_path=config_path,
                dry_run=reconcile_dry_run,
            )
        except (YAMLValidationError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(_format_reconcile_result(result))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


def _resolve_runner(dry_run: bool) -> CommandRunner:
    if dry_run:
        return DryRunRunner()
    return SubprocessRunner()


def _format_init_result(result: InitResult) -> str:
    if result.clone_result is not None:
        if result.clone_result.stdout:
            return result.clone_result.stdout
        return f"Cloned source tree to {result.config.source_path}"
    if result.reused_existing:
        return f"Reusing existing source tree at {result.config.source_path}"
    return f"Initialized source tree at {result.config.source_path}"


def _format_runtime_action(prefix: str, result: RuntimeActionResult) -> str:
    return f"{prefix} {len(result.targets)} target(s) from {result.build_root}"


def _format_reconcile_result(result: ReconcileResult) -> str:
    parts = [f"Reconcile {result.status}"]
    if result.candidate_sha:
        parts.append(f"candidate={result.candidate_sha}")
    if result.detail:
        parts.append(result.detail)
    return " ".join(parts)


def _load_hostname(config_path: Path) -> str:
    try:
        from .config import load_active_config

        return load_active_config(path=config_path).hostname
    except YAMLValidationError:
        return "unknown-host"
