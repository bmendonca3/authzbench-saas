from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from scripts.validate_leaderboard_submission import comparability_key


PRIMARY_FIELDS = (
    "agent",
    "model",
    "harness_type",
    "benchmark_version",
    "benchmark_commit_sha",
    "benchmark_fingerprint",
    "benchmark_fingerprint_provenance",
    "task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
    "v0_metric_profile",
    "v0_passed_count",
    "v0_mean_score",
    "invalid_submission_count",
    "invalid_submission_rate",
    "exploit_proven_task_count",
    "exploit_proven_success_rate",
    "vulnerable_full_pass_count",
    "control_false_report_rate",
    "control_execution_pass_rate",
    "authorized_allow_pass_rate",
    "false_positive_rate",
    "boundary_reasoning_pass_rate",
    "target_request_coverage_rate",
    "mean_score",
    "safety_violations",
    "private_pack_fingerprint_sha256",
)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def build_submission(
    source_paths: list[Path],
    *,
    primary_run_id: str,
    baseline_kind: str,
    variance_metric: str = "v0_mean_score",
    leaderboard_eligible: bool = False,
) -> dict[str, Any]:
    if not source_paths:
        raise ValueError("at least one source summary is required")
    summaries = [load_json(path) for path in source_paths]
    by_run_id = {str(summary.get("run_id")): summary for summary in summaries}
    if len(by_run_id) != len(summaries) or any(not run_id or run_id == "None" for run_id in by_run_id):
        raise ValueError("source summaries must have unique non-empty run_id values")
    if primary_run_id not in by_run_id:
        raise ValueError("primary_run_id must match one source summary")
    primary = by_run_id[primary_run_id]

    values = [summary.get(variance_metric) for summary in summaries]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError(f"{variance_metric} must be numeric in every source summary")
    stddev = statistics.pstdev(float(value) for value in values)
    task_count = int(primary["task_count"])
    split = str(primary.get("split"))
    row = {field: primary.get(field) for field in PRIMARY_FIELDS}
    row.update(
        {
            "baseline_kind": baseline_kind,
            "comparability_key": "",
            "eligibility_policy_version": "leaderboard-eligibility-v1",
            "leaderboard_eligible": leaderboard_eligible,
            "leaderboard_schema_version": "leaderboard-submission-v1",
            "median_duration_seconds": primary.get("median_duration_seconds"),
            "private_holdout_task_count": task_count if split == "private-holdout" else 0,
            "public_task_count": task_count if split == "public" else 0,
            "repeat_evidence": {
                "aggregation": "primary_run" if len(summaries) > 1 else "single_run",
                "primary_run_id": primary_run_id,
                "source_run_ids": sorted(by_run_id),
                "variance_metric": variance_metric,
            },
            "run_count": len(summaries),
            "run_id": primary_run_id,
            "source_run_summaries": [_display_path(path) for path in source_paths],
            "source_run_summary": _display_path(source_paths[summaries.index(primary)]),
            "split": split,
            "variance_or_ci": f"stddev={stddev:.4f}" if len(summaries) > 1 else "not_repeated",
        }
    )
    row["comparability_key"] = comparability_key(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a leaderboard row from protected run summaries.")
    parser.add_argument("--source-summary", action="append", required=True)
    parser.add_argument("--primary-run-id", required=True)
    parser.add_argument("--baseline-kind", choices=["model_baseline", "tool_agent_baseline"], required=True)
    parser.add_argument("--variance-metric", default="v0_mean_score")
    parser.add_argument("--leaderboard-eligible", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    row = build_submission(
        [Path(path) for path in args.source_summary],
        primary_run_id=args.primary_run_id,
        baseline_kind=args.baseline_kind,
        variance_metric=args.variance_metric,
        leaderboard_eligible=args.leaderboard_eligible,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(dump_json(row) + "\n", encoding="utf-8")
    print(dump_json(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
