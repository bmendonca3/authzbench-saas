from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_harbor_dataset_skeleton import build_harbor_dataset_skeleton
from scripts.validate_harbor_dataset_skeleton import validate_harbor_dataset_skeleton
from authzbench_harbor.adapter import (
    PLANNED_UNSUPPORTED_HARNESS_LANES,
    SUPPORTED_HARNESS_LANES,
)


SCHEMA_VERSION = "harbor-local-execution-preflight-v1"
DEFAULT_TASK = "tasks/project_mgmt/pm_same_tenant_read_control.json"


def _resolve_harbor_command(harbor_command: str) -> str:
    """Prefer direct Harbor, but use the documented uvx package path when needed."""
    parts = shlex.split(harbor_command)
    if not parts:
        return harbor_command
    if shutil.which(parts[0]) is not None:
        return harbor_command
    if harbor_command == "harbor" and shutil.which("uvx") is not None:
        return "uvx harbor"
    return harbor_command


def _harbor_command_is_runnable(harbor_command: str) -> bool:
    parts = shlex.split(harbor_command)
    if not parts:
        return False
    if shutil.which(parts[0]) is None:
        return False
    try:
        subprocess.run(
            [*parts, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def check_harbor_local_execution(
    *,
    task_patterns: list[str] | None = None,
    harness_lane: str = "no_tools",
    harbor_command: str = "harbor",
    require_harbor: bool = False,
    discover_harbor_cli: bool = True,
) -> dict[str, Any]:
    """Check whether a generated skeleton and Harbor command are runnable.

    This preflight intentionally does not invoke `harbor run`; it only records
    whether the CLI/package command is runnable and whether our generated public
    skeleton passes local structural/redaction validation.
    """
    task_patterns = task_patterns or [DEFAULT_TASK]
    if harness_lane in PLANNED_UNSUPPORTED_HARNESS_LANES:
        return {
            "schema_version": SCHEMA_VERSION,
            "evidence_status": "planned_unsupported",
            "public_claim_boundary": (
                "The live_http_tool_agent lane is a planning contract only. "
                "This preflight is not Harbor execution evidence, parity evidence, "
                "or v1 readiness."
            ),
            "harbor_command": harbor_command,
            "harbor_cli_check_status": "not_checked",
            "harbor_cli_found": False,
            "harbor_cli_runnable": False,
            "generated_skeleton_validated": False,
            "harness_lane": harness_lane,
            "harness_lane_status": "planned_unsupported",
            "task_count": 0,
            "local_harbor_run_runnable": False,
            "ready_for_local_harbor_run": False,
            "harbor_execution_verified": False,
            "local_run_template": None,
            "blocked_until": [
                "the packaged adapter implements target-service orchestration",
                "request-correlation capture is implemented and verified",
            ],
            "skeleton_errors": [
                "live_http_tool_agent is planned_unsupported by the packaged adapter"
            ],
        }
    if harness_lane not in SUPPORTED_HARNESS_LANES:
        return {
            "schema_version": SCHEMA_VERSION,
            "evidence_status": "invalid_configuration",
            "public_claim_boundary": (
                "This preflight is not Harbor execution evidence, parity evidence, "
                "or v1 readiness."
            ),
            "harbor_command": harbor_command,
            "harbor_cli_check_status": "not_checked",
            "harbor_cli_found": False,
            "harbor_cli_runnable": False,
            "generated_skeleton_validated": False,
            "harness_lane": harness_lane,
            "harness_lane_status": "unsupported",
            "task_count": 0,
            "local_harbor_run_runnable": False,
            "ready_for_local_harbor_run": False,
            "harbor_execution_verified": False,
            "local_run_template": None,
            "blocked_until": ["select an implemented harness lane"],
            "skeleton_errors": [f"unsupported harness lane: {harness_lane}"],
        }

    with tempfile.TemporaryDirectory(prefix="authzbench-harbor-preflight-") as tmp:
        output_dir = Path(tmp) / "generated-dataset"
        manifest = build_harbor_dataset_skeleton(
            task_patterns,
            output_dir,
            harness_lane=harness_lane,
            clean=True,
        )
        skeleton_result = validate_harbor_dataset_skeleton(output_dir)

    effective_harbor_command = _resolve_harbor_command(harbor_command) if discover_harbor_cli else harbor_command
    harbor_cli_runnable = (
        _harbor_command_is_runnable(effective_harbor_command)
        if discover_harbor_cli
        else False
    )
    harbor_cli_check_status = (
        "runnable"
        if harbor_cli_runnable
        else "not_runnable"
        if discover_harbor_cli
        else "not_checked"
    )
    blocked_until: list[str] = []
    if not discover_harbor_cli:
        blocked_until.append("Harbor CLI runnable state was not checked")
    elif not harbor_cli_runnable:
        blocked_until.append("Harbor CLI/package is not installed or not on PATH")
    if not skeleton_result["passed"]:
        blocked_until.append("generated public Harbor skeleton does not validate")

    local_run_runnable = harbor_cli_runnable and skeleton_result["passed"]
    if local_run_runnable:
        blocked_until.append("real Harbor execution has not been run by this preflight")

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_status": "local_preflight_only",
        "public_claim_boundary": "This preflight is not Harbor execution evidence, not parity evidence, and not v1 readiness. It does not run Harbor.",
        "harbor_command": effective_harbor_command,
        "harbor_cli_check_status": harbor_cli_check_status,
        "harbor_cli_found": harbor_cli_runnable,
        "harbor_cli_runnable": harbor_cli_runnable,
        "generated_skeleton_validated": skeleton_result["passed"],
        "harness_lane": harness_lane,
        "harness_lane_status": "implemented",
        "task_count": manifest["task_count"],
        "local_harbor_run_runnable": local_run_runnable,
        "ready_for_local_harbor_run": local_run_runnable,
        "harbor_execution_verified": False,
        "local_run_template": f"cd <generated-harbor-dataset-path> && {effective_harbor_command} run -c run_authzbench_saas.yaml --yes",
        "blocked_until": blocked_until,
        "skeleton_errors": skeleton_result["errors"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Public-safe local Harbor execution preflight.")
    parser.add_argument("--task", action="append", help="Public task manifest glob. Repeatable.")
    parser.add_argument("--harness-lane", choices=["no_tools", "live_http_tool_agent"], default="no_tools")
    parser.add_argument("--harbor-command", default="harbor")
    parser.add_argument("--require-harbor", action="store_true", help="Exit non-zero when the Harbor CLI is not available.")
    parser.add_argument(
        "--skip-harbor-discovery",
        action="store_true",
        help="Do not inspect PATH for Harbor; useful for deterministic public fixtures.",
    )
    args = parser.parse_args()

    result = check_harbor_local_execution(
        task_patterns=args.task,
        harness_lane=args.harness_lane,
        harbor_command=args.harbor_command,
        require_harbor=args.require_harbor,
        discover_harbor_cli=not args.skip_harbor_discovery,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_harbor and not result["harbor_cli_found"]:
        return 1
    return 0 if result["generated_skeleton_validated"] else 1


if __name__ == "__main__":
    sys.exit(main())
