from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json
from scripts.validate_holdout_pack import validate_holdout_pack


DEFAULT_PATTERNS = ["tasks_private/holdout/**/*.json"]
DEFAULT_PUBLIC_PATTERNS = ["tasks/*/*.json"]


def _git_tracked_holdout_count(pathspec: str = "tasks_private/holdout") -> int | None:
    try:
        result = subprocess.run(
            ["git", "ls-files", pathspec],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return len([line for line in result.stdout.splitlines() if line.strip()])


def summarize_holdout_pack(
    patterns: list[str] | None = None,
    public_patterns: list[str] | None = None,
) -> dict[str, Any]:
    validation = validate_holdout_pack(
        patterns or DEFAULT_PATTERNS,
        public_patterns=public_patterns or DEFAULT_PUBLIC_PATTERNS,
        min_count=20,
        preferred_count=24,
        max_count=30,
        min_vulnerable=12,
        min_controls=8,
        min_apps=6,
        max_per_app=8,
        min_denial_controls=4,
        min_authorized_allow_controls=4,
        min_route_variants=6,
        min_decoy_variants=6,
    )
    tracked_count = _git_tracked_holdout_count()
    git_check_available = tracked_count is not None
    app_counts = validation.get("app_counts") if isinstance(validation.get("app_counts"), dict) else {}
    max_tasks_per_app = max((int(count) for count in app_counts.values()), default=0)
    public_safe_passed = (
        validation.get("passed") is True
        and validation.get("leaderboard_suitable") is True
        and tracked_count == 0
    )
    return {
        "schema_version": "holdout-public-safe-summary-v1",
        "public_safe_summary": True,
        "publication_safety": {
            "contains_task_ids": False,
            "contains_task_seeds": False,
            "contains_route_paths": False,
            "contains_oracle_bodies": False,
            "contains_private_file_paths": False,
            "contains_private_diagnostics": False,
        },
        "passed": public_safe_passed,
        "leaderboard_suitable": validation.get("leaderboard_suitable") is True,
        "git_tracking_check_available": git_check_available,
        "private_holdouts_untracked": tracked_count == 0 if git_check_available else False,
        "git_tracked_holdout_manifest_count": tracked_count,
        "validation_error_count": len(validation.get("errors", [])),
        "validation_warning_count": len(validation.get("warnings", [])),
        "counts": {
            "manifest_count": validation.get("manifest_count", 0),
            "private_holdout_count": validation.get("private_holdout_count", 0),
            "vulnerable_count": validation.get("vulnerable_count", 0),
            "control_count": validation.get("control_count", 0),
            "denial_control_count": validation.get("denial_control_count", 0),
            "authorized_allow_control_count": validation.get("authorized_allow_control_count", 0),
            "app_count": len(app_counts),
            "max_tasks_per_app": max_tasks_per_app,
            "route_variant_count": validation.get("route_variant_count", 0),
            "decoy_variant_count": validation.get("decoy_variant_count", 0),
            "rehearsal_manifest_count": validation.get("rehearsal_manifest_count", 0),
            "public_structure_overlap_count": validation.get("public_structure_overlap_count", 0),
        },
        "v0_shape_requirements": {
            "min_count": validation.get("min_count", 20),
            "preferred_count": validation.get("preferred_count", 24),
            "max_count": validation.get("max_count", 30),
            "min_vulnerable": validation.get("min_vulnerable", 12),
            "min_controls": validation.get("min_controls", 8),
            "min_apps": validation.get("min_apps", 6),
            "max_per_app": validation.get("max_per_app", 8),
            "min_denial_controls": validation.get("min_denial_controls", 4),
            "min_authorized_allow_controls": validation.get("min_authorized_allow_controls", 4),
            "min_route_variants": validation.get("min_route_variants", 6),
            "min_decoy_variants": validation.get("min_decoy_variants", 6),
        },
        "notes": (
            "This summary is intentionally count-level only. Do not publish private "
            "holdout manifests, seeds, routes, oracle bodies, raw diagnostics, or run artifacts."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit a public-safe count summary for an ignored private holdout pack."
    )
    parser.add_argument("--task", action="append", help="Private holdout manifest glob. Can be repeated.")
    parser.add_argument("--public-task", action="append", help="Public task manifest glob. Can be repeated.")
    parser.add_argument("--output", help="Optional output JSON path for the redacted summary.")
    args = parser.parse_args()

    summary = summarize_holdout_pack(args.task, args.public_task)
    rendered = dump_json(summary) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
