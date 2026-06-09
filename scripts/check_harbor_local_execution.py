from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_harbor_dataset_skeleton import build_harbor_dataset_skeleton
from scripts.validate_harbor_dataset_skeleton import validate_harbor_dataset_skeleton


SCHEMA_VERSION = "harbor-local-execution-preflight-v1"
DEFAULT_TASK = "tasks/project_mgmt/pm_same_tenant_read_control.json"


def check_harbor_local_execution(
    *,
    task_patterns: list[str] | None = None,
    harness_lane: str = "no_tools",
    harbor_command: str = "harbor",
    require_harbor: bool = False,
    discover_harbor_cli: bool = True,
) -> dict[str, Any]:
    """Check whether a verified generated skeleton is ready for a future Harbor run.

    This preflight intentionally does not invoke `harbor run`; it only records
    whether the CLI is discoverable and whether our generated public skeleton
    passes local structural/redaction validation.
    """
    task_patterns = task_patterns or [DEFAULT_TASK]
    with tempfile.TemporaryDirectory(prefix="authzbench-harbor-preflight-") as tmp:
        output_dir = Path(tmp) / "generated-dataset"
        manifest = build_harbor_dataset_skeleton(
            task_patterns,
            output_dir,
            harness_lane=harness_lane,
            clean=True,
        )
        skeleton_result = validate_harbor_dataset_skeleton(output_dir)

    harbor_path = shutil.which(harbor_command) if discover_harbor_cli else None
    harbor_cli_found = harbor_path is not None
    blocked_until: list[str] = []
    if not harbor_cli_found:
        blocked_until.append("Harbor CLI/package is not installed or not on PATH")
    if not skeleton_result["passed"]:
        blocked_until.append("generated public Harbor skeleton does not validate")

    ready_for_local_run = harbor_cli_found and skeleton_result["passed"]
    if require_harbor and not harbor_cli_found:
        ready_for_local_run = False

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_status": "local_preflight_only",
        "public_claim_boundary": "This preflight is not Harbor execution evidence, not parity evidence, and not v1 readiness. It does not run Harbor.",
        "harbor_command": harbor_command,
        "harbor_cli_found": harbor_cli_found,
        "generated_skeleton_validated": skeleton_result["passed"],
        "harness_lane": harness_lane,
        "task_count": manifest["task_count"],
        "ready_for_local_harbor_run": ready_for_local_run,
        "harbor_execution_verified": False,
        "local_run_template": "harbor run -p <generated-harbor-dataset-path> -a <agent> -m <model>",
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
