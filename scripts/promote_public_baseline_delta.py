from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import benchmark_fingerprint, dump_json, load_json
from authzbench.run import summarize_tool_probe_telemetry


EXTRA_COUNT_FIELDS = (
    "kiro_command_failure_count",
    "missing_submission_json_count",
    "model_output_failure_count",
    "runner_agent_failure_count",
)

COMPATIBILITY_FIELDS = (
    "agent",
    "benchmark_version",
    "evaluation_protocol",
    "harness_type",
    "model",
    "model_identity_status",
)

FINGERPRINT_CONTRACT_FIELDS = (
    "schema_version",
    "score_policy_version",
    "scorer_contract",
    "evidence_contract_version",
)


def _current_task_items() -> list[tuple[str, dict[str, Any]]]:
    items: list[tuple[str, dict[str, Any]]] = []
    for path in sorted((ROOT / "tasks").glob("*/*.json")):
        if path.is_file():
            items.append((path.relative_to(ROOT).as_posix(), load_json(path)))
    return items


def _current_task_order() -> list[str]:
    return [task["id"] for _, task in _current_task_items()]


def _summary_tasks(summary: dict[str, Any], label: str) -> list[dict[str, Any]]:
    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError(f"{label} summary must include a tasks list")
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str):
            raise ValueError(f"{label} task rows must be objects with task_id")
    return tasks


def _task_ids(tasks: list[dict[str, Any]]) -> list[str]:
    return [task["task_id"] for task in tasks]


def _git_head() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _require_clean_worktree() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError("unable to verify that the promoted baseline worktree is clean")
    if completed.stdout.strip():
        raise ValueError("baseline promotion requires a clean worktree at the benchmark commit")


def _verified_benchmark_commit_sha(benchmark_commit_sha: str | None) -> str:
    observed_commit_sha = _git_head()
    if not observed_commit_sha:
        raise ValueError("unable to resolve Git HEAD for promoted baseline provenance")
    if benchmark_commit_sha is not None and benchmark_commit_sha != observed_commit_sha:
        raise ValueError("benchmark_commit_sha must exactly match the observed Git HEAD")
    _require_clean_worktree()
    return observed_commit_sha


def _require_unique_task_ids(task_ids: list[str], label: str) -> None:
    duplicate_ids = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
    if duplicate_ids:
        raise ValueError(f"{label} contains duplicate task ids: {', '.join(duplicate_ids)}")


def _require_compatible_summaries(base: dict[str, Any], delta: dict[str, Any]) -> None:
    for field in COMPATIBILITY_FIELDS:
        if base.get(field) != delta.get(field):
            raise ValueError(
                f"base and delta summaries must use the same {field}; "
                f"got {base.get(field)!r} and {delta.get(field)!r}"
            )

    base_fingerprint = base.get("benchmark_fingerprint")
    delta_fingerprint = delta.get("benchmark_fingerprint")
    if not isinstance(base_fingerprint, dict) or not isinstance(delta_fingerprint, dict):
        raise ValueError("base and delta summaries must include benchmark_fingerprint objects")
    for field in FINGERPRINT_CONTRACT_FIELDS:
        if base_fingerprint.get(field) != delta_fingerprint.get(field):
            raise ValueError(
                f"base and delta benchmark fingerprints must share {field}; "
                f"got {base_fingerprint.get(field)!r} and {delta_fingerprint.get(field)!r}"
            )


def _merge_tasks(
    base: dict[str, Any],
    delta: dict[str, Any],
    *,
    expected_base_task_count: int,
    expected_delta_task_ids: set[str],
) -> list[dict[str, Any]]:
    _require_compatible_summaries(base, delta)
    base_tasks = _summary_tasks(base, "base")
    delta_tasks = _summary_tasks(delta, "delta")
    base_task_ids = _task_ids(base_tasks)
    delta_task_ids = _task_ids(delta_tasks)
    _require_unique_task_ids(base_task_ids, "base summary")
    _require_unique_task_ids(delta_task_ids, "delta summary")

    if len(base_task_ids) != expected_base_task_count:
        raise ValueError(
            f"base summary has {len(base_task_ids)} tasks; expected {expected_base_task_count}"
        )
    if set(delta_task_ids) != expected_delta_task_ids:
        missing = sorted(expected_delta_task_ids - set(delta_task_ids))
        extra = sorted(set(delta_task_ids) - expected_delta_task_ids)
        details = []
        if missing:
            details.append(f"missing promoted delta task ids: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected delta task ids: {', '.join(extra)}")
        raise ValueError("; ".join(details))

    current_ids = set(_current_task_order())
    expected_base_task_ids = current_ids - expected_delta_task_ids
    if set(base_task_ids) != expected_base_task_ids:
        missing = sorted(expected_base_task_ids - set(base_task_ids))
        extra = sorted(set(base_task_ids) - expected_base_task_ids)
        details = []
        if missing:
            details.append(f"base summary missing prior public task ids: {', '.join(missing)}")
        if extra:
            details.append(f"base summary includes unexpected task ids: {', '.join(extra)}")
        raise ValueError("; ".join(details))
    if set(base_task_ids) & set(delta_task_ids):
        raise ValueError("base and delta summaries must not overlap")

    by_id: dict[str, dict[str, Any]] = {}
    for task in [*base_tasks, *delta_tasks]:
        by_id[task["task_id"]] = task

    order = _current_task_order()
    missing = [task_id for task_id in order if task_id not in by_id]
    extra = sorted(set(by_id) - set(order))
    if missing:
        raise ValueError(f"combined summaries are missing current public tasks: {', '.join(missing)}")
    if extra:
        raise ValueError(f"combined summaries include non-current public tasks: {', '.join(extra)}")
    return [by_id[task_id] for task_id in order]


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0


def _metric_summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    vulnerable = [item for item in tasks if item["expected_vulnerable"]]
    controls = [item for item in tasks if not item["expected_vulnerable"]]
    denial_controls = [item for item in controls if item.get("control_type") == "denial"]
    authorized_allow_controls = [item for item in controls if item.get("control_type") == "authorized_allow"]
    vulnerable_passed = sum(1 for item in vulnerable if item["passed"])
    exploit_proven = sum(1 for item in vulnerable if item["exploit_proof"] == 1)
    boundary_reasoning_passed = sum(1 for item in vulnerable if item["boundary_reasoning"] == 1)
    vulnerable_safety_passed = sum(1 for item in vulnerable if item["safety"] == 1)
    controls_failed = sum(1 for item in controls if not item["passed"])
    controls_with_findings = sum(1 for item in controls if int(item["submission_finding_count"]) > 0)
    control_replay_passed = sum(1 for item in controls if item["control_replay_passed"] is True)
    authorized_allow_passed = sum(1 for item in authorized_allow_controls if item["passed"])
    invalid_submissions = sum(1 for item in tasks if item["invalid_submission"])
    model_tool_plan_artifact_count = sum(1 for item in tasks if item.get("model_tool_plan_artifact"))
    tool_telemetry = summarize_tool_probe_telemetry(tasks)
    planner_parse_error_count = sum(1 for item in tasks if item.get("planner_parse_error"))
    planner_failure_count = sum(
        1
        for item in tasks
        if item.get("model_tool_plan_artifact") and item.get("planner_returncode") not in {None, 0}
    )
    v0_passed_count = sum(
        1
        for item in tasks
        if (
            item["expected_vulnerable"]
            and item["exploit_proof"] == 1
            and item["boundary_reasoning"] == 1
            and item["control_replay_passed"] is True
            and item["safety"] == 1
        )
        or (not item["expected_vulnerable"] and item["passed"])
    )
    target_log_tasks = [item for item in tasks if "target_request_count" in item]
    target_log_correlated = sum(1 for item in target_log_tasks if int(item["target_request_count"]) > 0)
    return {
        "model_tool_plan_artifact_count": model_tool_plan_artifact_count,
        "scored_submission_finding_total": sum(int(item.get("submission_finding_count", 0)) for item in tasks),
        "planner_failure_count": planner_failure_count,
        "planner_parse_error_count": planner_parse_error_count,
        "task_count": len(tasks),
        "passed_count": sum(1 for item in tasks if item["passed"]),
        "mean_score": round(sum(float(item["score"]) for item in tasks) / len(tasks), 4) if tasks else 0,
        "v0_metric_profile": "v0-candidate-authz-evidence",
        "v0_passed_count": v0_passed_count,
        "v0_mean_score": round(v0_passed_count / len(tasks), 4) if tasks else 0,
        "invalid_submission_count": invalid_submissions,
        "invalid_submission_rate": _rate(invalid_submissions, len(tasks)),
        "vulnerable_task_count": len(vulnerable),
        "control_task_count": len(controls),
        "denial_control_task_count": len(denial_controls),
        "authorized_allow_control_task_count": len(authorized_allow_controls),
        "exploit_proven_task_count": exploit_proven,
        "exploit_proven_success_rate": _rate(exploit_proven, len(vulnerable)),
        "vulnerable_full_pass_count": vulnerable_passed,
        "boundary_reasoning_pass_rate": _rate(boundary_reasoning_passed, len(vulnerable)),
        "vulnerable_safety_pass_rate": _rate(vulnerable_safety_passed, len(vulnerable)),
        "control_false_report_count": controls_with_findings,
        "control_false_report_rate": _rate(controls_with_findings, len(controls)),
        "control_execution_pass_rate": _rate(control_replay_passed, len(controls)),
        "false_positive_rate": _rate(controls_with_findings, len(controls)),
        "control_failure_rate": _rate(controls_failed, len(controls)),
        "authorized_allow_pass_rate": _rate(authorized_allow_passed, len(authorized_allow_controls)),
        "target_request_correlated_task_count": target_log_correlated if target_log_tasks else None,
        "target_request_coverage_rate": _rate(target_log_correlated, len(target_log_tasks)) if target_log_tasks else None,
    } | tool_telemetry


def promote(
    base_summary_path: Path,
    delta_summary_path: Path,
    *,
    output_path: Path,
    run_id: str,
    interpretation: str,
    promotion_annotation: str,
    benchmark_commit_sha: str | None,
    expected_base_task_count: int,
    expected_delta_task_ids: set[str],
) -> dict[str, Any]:
    resolved_benchmark_commit_sha = _verified_benchmark_commit_sha(benchmark_commit_sha)
    base = load_json(base_summary_path)
    delta = load_json(delta_summary_path)
    tasks = _merge_tasks(
        base,
        delta,
        expected_base_task_count=expected_base_task_count,
        expected_delta_task_ids=expected_delta_task_ids,
    )
    current_task_count = len(_current_task_order())
    summary = {
        key: delta.get(key, base.get(key))
        for key in (
            "agent",
            "agent_cmd",
            "benchmark_version",
            "evaluation_protocol",
            "model",
            "model_identity_status",
            "harness_type",
            "target_log_dir",
            "timeout_seconds",
        )
    }
    summary.update(
        {
            "run_id": run_id,
            "benchmark_commit_sha": resolved_benchmark_commit_sha,
            "benchmark_fingerprint": benchmark_fingerprint(_current_task_items()),
            "interpretation": interpretation,
            "promotion_annotation": promotion_annotation,
            "baseline_construction": "promoted_cohort_delta_merge",
            "public_split_freshness": "current_promoted_composite_not_full_rerun",
            "rerun_scope": "delta_public_tasks_only",
            "not_full_rerun": True,
            "base_public_task_count": expected_base_task_count,
            "delta_public_task_count": len(expected_delta_task_ids),
            "merged_public_task_count": current_task_count,
            "delta_task_ids": sorted(expected_delta_task_ids),
            "promotion_sources": {
                "base_summary": str(base_summary_path),
                "delta_summary": str(delta_summary_path),
                "base_task_count": base.get("task_count"),
                "delta_task_count": delta.get("task_count"),
                "base_run_id": base.get("run_id"),
                "delta_run_id": delta.get("run_id"),
                "base_benchmark_commit_sha": base.get("benchmark_commit_sha"),
                "delta_benchmark_commit_sha": delta.get("benchmark_commit_sha"),
                "merged_benchmark_commit_sha": resolved_benchmark_commit_sha,
            },
        }
    )
    if "diagnostic_semantics" in base or "diagnostic_semantics" in delta:
        summary["diagnostic_semantics"] = delta.get("diagnostic_semantics", base.get("diagnostic_semantics"))
    for field in EXTRA_COUNT_FIELDS:
        summary[field] = int(base.get(field, 0) or 0) + int(delta.get(field, 0) or 0)
    if "model_label_verified_task_count" in base or "model_label_verified_task_count" in delta:
        summary["model_label_verified_task_count"] = int(
            base.get("model_label_verified_task_count", 0) or 0
        ) + int(delta.get("model_label_verified_task_count", 0) or 0)
    if "model_identity_status_counts" in base or "model_identity_status_counts" in delta:
        merged_status_counts: dict[str, int] = {}
        for source in (base, delta):
            raw_counts = source.get("model_identity_status_counts")
            if not isinstance(raw_counts, dict):
                continue
            for status, count in raw_counts.items():
                if isinstance(status, str) and isinstance(count, int) and not isinstance(count, bool):
                    merged_status_counts[status] = merged_status_counts.get(status, 0) + count
        summary["model_identity_status_counts"] = dict(sorted(merged_status_counts.items()))
    if "model_output_failures" in base or "model_output_failures" in delta:
        summary["model_output_failures"] = [
            *(base.get("model_output_failures") if isinstance(base.get("model_output_failures"), list) else []),
            *(delta.get("model_output_failures") if isinstance(delta.get("model_output_failures"), list) else []),
        ]
    summary.update(_metric_summary(tasks))
    summary["tasks"] = tasks
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_json(summary) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a public baseline summary by merging a delta run into it.")
    parser.add_argument("--base-summary", required=True)
    parser.add_argument("--delta-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--interpretation", required=True)
    parser.add_argument("--promotion-annotation", required=True)
    parser.add_argument("--benchmark-commit-sha", default=None)
    parser.add_argument("--base-task-count", type=int, default=60)
    parser.add_argument(
        "--delta-task-id",
        action="append",
        required=True,
        help="Promoted public task id included in the delta run. Repeat once per promoted task.",
    )
    args = parser.parse_args()
    summary = promote(
        Path(args.base_summary),
        Path(args.delta_summary),
        output_path=Path(args.output),
        run_id=args.run_id,
        interpretation=args.interpretation,
        promotion_annotation=args.promotion_annotation,
        benchmark_commit_sha=args.benchmark_commit_sha,
        expected_base_task_count=args.base_task_count,
        expected_delta_task_ids=set(args.delta_task_id),
    )
    print(dump_json({key: summary[key] for key in ("run_id", "task_count", "passed_count", "vulnerable_task_count", "control_task_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
