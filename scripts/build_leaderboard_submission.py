from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import (
    BENCHMARK_FINGERPRINT_VERSION,
    EVIDENCE_CONTRACT_VERSION,
    SCORE_POLICY_VERSION,
    dump_json,
    load_json,
)
from scripts.validate_leaderboard_submission import (
    ELIGIBILITY_POLICY_VERSION,
    HISTORICAL_ELIGIBILITY_POLICY_VERSION,
    HISTORICAL_LEADERBOARD_SCHEMA_VERSION,
    LEADERBOARD_SCHEMA_VERSION,
    _validate_eligible_source_summary,
    comparability_key,
)


PRIMARY_FIELDS = (
    "agent",
    "model",
    "harness_type",
    "benchmark_version",
    "benchmark_commit_sha",
    "benchmark_execution_status",
    "benchmark_fingerprint",
    "benchmark_fingerprint_provenance",
    "benchmark_source_state",
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
    "evidence_chain_complete_count",
    "vulnerable_full_pass_count",
    "control_false_report_rate",
    "control_execution_pass_rate",
    "authorized_allow_pass_rate",
    "false_positive_rate",
    "boundary_reasoning_pass_rate",
    "target_request_coverage_rate",
    "mean_score",
    "safety_violations",
    "adapter_json_only_compliant_count",
    "adapter_json_only_compliance_rate",
    "core_passed_count",
    "evaluation_protocol",
    "infrastructure_failure_count",
    "model_identity_status",
    "model_label_verified_task_count",
    "requested_model_labels",
    "requested_model_label_match_task_count",
    "effective_model_labels",
    "effective_model_label_match_task_count",
    "promotion_eligible_count",
    "promotion_eligibility_rate",
    "safety_observation_status_counts",
    "target_request_correlated_task_count",
    "task_completion_count",
    "vulnerable_safety_observation_coverage_rate",
    "vulnerable_safety_pass_rate",
    "private_pack_id",
    "private_pack_version",
    "private_pack_fingerprint_sha256",
    "private_pack_fingerprint_provenance",
    "private_pack_loaded_fingerprint_sha256",
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
    fingerprints = [summary.get("benchmark_fingerprint") for summary in summaries]
    current_contract = all(
        isinstance(fingerprint, dict)
        and fingerprint.get("schema_version") == BENCHMARK_FINGERPRINT_VERSION
        and fingerprint.get("score_policy_version") == SCORE_POLICY_VERSION
        and fingerprint.get("scorer_contract")
        == "authz-evidence-chain-v3-observed-mutation-safety"
        and fingerprint.get("evidence_contract_version")
        == EVIDENCE_CONTRACT_VERSION
        for fingerprint in fingerprints
    )
    if leaderboard_eligible and not current_contract:
        raise ValueError(
            "leaderboard_eligible rows require current score-policy-v3, "
            "evidence-chain, and benchmark-fingerprint-v2 source summaries"
        )
    if not current_contract and any(
        isinstance(fingerprint, dict)
        and fingerprint.get("schema_version") == BENCHMARK_FINGERPRINT_VERSION
        for fingerprint in fingerprints
    ):
        raise ValueError("source summaries mix or incompletely implement the current benchmark contract")
    if leaderboard_eligible:
        source_errors: list[str] = []
        source_warnings: list[str] = []
        for path, summary in zip(source_paths, summaries):
            location = _display_path(path)
            _validate_eligible_source_summary(
                summary,
                source_errors,
                source_warnings,
                location=location,
                current_contract=True,
            )
        if source_errors:
            raise ValueError(
                "source summaries do not satisfy current leaderboard eligibility: "
                + "; ".join(source_errors)
            )

    values = [summary.get(variance_metric) for summary in summaries]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError(f"{variance_metric} must be numeric in every source summary")
    stddev = statistics.pstdev(float(value) for value in values)
    task_count = int(primary["task_count"])
    split = str(primary.get("split"))
    row = {field: primary.get(field) for field in PRIMARY_FIELDS}
    agent_name = str(primary.get("agent", ""))
    model_name = str(primary.get("model", ""))
    is_schema_sanity = (
        "empty-response" in agent_name
        or "empty-response" in model_name
        or "heuristic" in agent_name
        or "heuristic" in model_name
    )
    row.update(
        {
            "baseline_kind": baseline_kind,
            "capability_baseline": not is_schema_sanity,
            "cohort": "schema-sanity" if is_schema_sanity else "capability",
            "comparability_key": "",
            "eligibility_policy_version": (
                ELIGIBILITY_POLICY_VERSION
                if current_contract
                else HISTORICAL_ELIGIBILITY_POLICY_VERSION
            ),
            "leaderboard_eligible": leaderboard_eligible,
            "leaderboard_schema_version": (
                LEADERBOARD_SCHEMA_VERSION
                if current_contract
                else HISTORICAL_LEADERBOARD_SCHEMA_VERSION
            ),
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
