from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import benchmark_fingerprint, dump_json, is_safe_identifier, load_json, stable_json_sha256
from authzbench.run import BENCHMARK_ROOT, _adapter_failure_type, _load_adapter_output, summarize_task_results
from authzbench.score import score_submission


RESCORE_SCHEMA_VERSION = "public-run-rescore-v1"

PUBLIC_SOURCE_SUMMARY_FIELDS = (
    "run_id",
    "benchmark_version",
    "agent",
    "model",
    "harness_type",
    "timeout_seconds",
)

PUBLIC_SOURCE_TASK_BOOL_FIELDS = (
    "model_tool_plan_artifact",
    "tool_probe_artifact",
)

PUBLIC_SOURCE_TASK_INT_FIELDS = (
    "executed_probe_count",
    "fallback_probe_count",
    "submitted_finding_count",
    "planner_returncode",
    "target_request_count",
)

PUBLIC_TARGET_REQUEST_WARNINGS = {"target_log_missing", "no_target_requests_correlated"}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_commit_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=BENCHMARK_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    value = completed.stdout.strip()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("unable to resolve a 40-character target benchmark commit SHA")
    return value


def _require_commit_exists(value: str) -> None:
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=BENCHMARK_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("target_benchmark_commit_sha does not resolve to a local Git commit")


def _require_clean_target_checkout(target_commit: str) -> None:
    current_commit = _current_commit_sha()
    if current_commit != target_commit:
        raise ValueError("target_benchmark_commit_sha must match the checked-out Git HEAD")
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=BENCHMARK_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        raise ValueError("unable to verify that the target benchmark worktree is clean")
    if status.stdout.strip():
        raise ValueError("rescore requires a clean worktree at the target benchmark commit")


def _public_relative_path(value: str, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"{field} must be a public-safe relative path without parent traversal")
    return path.as_posix()


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(data) + "\n", encoding="utf-8")


def _task_path(row: dict[str, Any]) -> Path:
    raw_path = row.get("task_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"{row.get('task_id', '<unknown>')}: task_path must be a non-empty string")
    candidate = (BENCHMARK_ROOT / raw_path).resolve()
    try:
        candidate.relative_to(BENCHMARK_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{row.get('task_id', '<unknown>')}: task_path escapes repository root") from exc
    if not candidate.is_file():
        raise ValueError(f"{row.get('task_id', '<unknown>')}: task manifest does not exist: {raw_path}")
    return candidate


def _invalid_score(task: dict[str, Any], reason: str) -> dict[str, Any]:
    result = score_submission(task, None)
    result["reason"] = reason
    result["observations"] = [reason]
    return result


def _updated_task_row(
    source_row: dict[str, Any],
    task: dict[str, Any],
    public_task_path: str,
    score: dict[str, Any],
    *,
    adapter_failure_type: str | None,
    runner_agent_failure: bool,
) -> dict[str, Any]:
    infrastructure_failure = (
        adapter_failure_type != "output_parse_failure"
        if adapter_failure_type is not None
        else runner_agent_failure
    )
    public_source_fields: dict[str, Any] = {}
    agent_returncode = source_row.get("agent_returncode")
    if agent_returncode is None or (
        isinstance(agent_returncode, int) and not isinstance(agent_returncode, bool)
    ):
        public_source_fields["agent_returncode"] = agent_returncode
    for field in PUBLIC_SOURCE_TASK_BOOL_FIELDS:
        if isinstance(source_row.get(field), bool):
            public_source_fields[field] = source_row[field]
    for field in PUBLIC_SOURCE_TASK_INT_FIELDS:
        value = source_row.get(field)
        if isinstance(value, int) and not isinstance(value, bool):
            public_source_fields[field] = value
    planner_parse_error = source_row.get("planner_parse_error")
    if planner_parse_error is not None and planner_parse_error != "":
        public_source_fields["planner_parse_error"] = True
    target_request_warning = source_row.get("target_request_warning")
    if target_request_warning in PUBLIC_TARGET_REQUEST_WARNINGS:
        public_source_fields["target_request_warning"] = target_request_warning
    return public_source_fields | {
        "task_id": task["id"],
        "task_path": public_task_path,
        "expected_vulnerable": bool(task.get("expected_vulnerable")),
        "control_type": task.get("control_type") if not task.get("expected_vulnerable") else None,
        "score": score.get("score", 0),
        "passed": bool(score.get("passed")),
        "invalid_submission": bool(score.get("invalid_submission")),
        "submission_finding_count": score.get("submission_finding_count", 0),
        "control_replay_passed": score.get("control_replay_passed"),
        "exploit_proof": score.get("subscores", {}).get("exploit_proof", 0),
        "boundary_reasoning": score.get("subscores", {}).get("boundary_reasoning", 0),
        "claim_exact_match": bool(score.get("claim_exact_match")),
        "boundary_exact_match": bool(score.get("boundary_exact_match")),
        "boundary_semantic_match": bool(score.get("boundary_semantic_match")),
        "boundary_partial_match": bool(score.get("boundary_partial_match")),
        "boundary_match_mode": score.get("boundary_match_mode", "not_evaluated"),
        "boundary_field_match_rate": score.get("boundary_field_match_rate", 0),
        "false_positive_control": score.get("subscores", {}).get("false_positive_control", 0),
        "safety": score.get("subscores", {}).get("safety", 0),
        "adapter_failure_type": adapter_failure_type,
        "runner_agent_failure": runner_agent_failure,
        "infrastructure_failure": infrastructure_failure,
    }


def rescore_run(
    source_run_dir: Path,
    output_dir: Path,
    *,
    public_target_log_dir_label: str | None = None,
    target_benchmark_commit_sha: str | None = None,
) -> dict[str, Any]:
    source_run_dir = source_run_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir == source_run_dir:
        raise ValueError("output_dir must differ from source_run_dir")
    if output_dir.is_relative_to(source_run_dir) or source_run_dir.is_relative_to(output_dir):
        raise ValueError("source_run_dir and output_dir must not contain one another")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output_dir must be empty: {output_dir}")
    target_commit = target_benchmark_commit_sha or _current_commit_sha()
    if not re.fullmatch(r"[0-9a-f]{40}", target_commit):
        raise ValueError("target_benchmark_commit_sha must be a 40-character lowercase Git SHA")
    _require_commit_exists(target_commit)
    _require_clean_target_checkout(target_commit)

    source_summary_path = source_run_dir / "summary.json"
    source_summary = load_json(source_summary_path)
    if not isinstance(source_summary, dict) or not isinstance(source_summary.get("tasks"), list):
        raise ValueError("source summary must be an object with a tasks list")
    run_id = source_summary.get("run_id")
    if not isinstance(run_id, str) or run_id != source_run_dir.name:
        raise ValueError("source summary run_id must match source run directory name")
    source_fingerprint = source_summary.get("benchmark_fingerprint")
    target_log_dir = source_summary.get("target_log_dir")
    if public_target_log_dir_label is not None:
        public_target_log_dir_label = _public_relative_path(
            public_target_log_dir_label,
            "public_target_log_dir_label",
        )
    if isinstance(target_log_dir, str) and Path(target_log_dir).is_absolute():
        if not public_target_log_dir_label:
            raise ValueError("absolute source target_log_dir requires --public-target-log-dir-label")
        target_log_dir = public_target_log_dir_label
    elif isinstance(target_log_dir, str):
        target_log_dir = _public_relative_path(target_log_dir, "source target_log_dir")
    elif target_log_dir is not None:
        raise ValueError("source target_log_dir must be a string or null")

    rescored_rows: list[dict[str, Any]] = []
    fingerprint_items: list[tuple[str, dict[str, Any]]] = []
    submission_hashes: list[dict[str, str | None]] = []
    source_score_hashes: list[dict[str, str | None]] = []
    source_model_output_hashes: list[dict[str, str | None]] = []
    rescored_score_hashes: list[dict[str, str]] = []

    for source_row in source_summary["tasks"]:
        if not isinstance(source_row, dict):
            raise ValueError("every source summary task row must be an object")
        task_id = source_row.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("every source summary task row must have a task_id")
        if not is_safe_identifier(task_id):
            raise ValueError(f"{task_id!r}: task_id must be a safe single path component")
        task_path = _task_path(source_row)
        public_task_path = task_path.relative_to(BENCHMARK_ROOT.resolve()).as_posix()
        task = load_json(task_path)
        if task.get("id") != task_id:
            raise ValueError(f"{task_id}: source row does not match task manifest id")
        fingerprint_items.append((task_path.relative_to(BENCHMARK_ROOT).as_posix(), task))

        source_task_dir = source_run_dir / task_id
        submission_path = source_task_dir / "submission.json"
        source_score_path = source_task_dir / "score.json"
        model_output_path = source_task_dir / "model-output.json"
        model_output = _load_adapter_output(model_output_path)
        adapter_failure_type = _adapter_failure_type(model_output)
        runner_agent_failure = source_row.get("agent_returncode") != 0

        submission_hashes.append(
            {"task_id": task_id, "sha256": _file_sha256(submission_path) if submission_path.is_file() else None}
        )
        source_score_hashes.append(
            {"task_id": task_id, "sha256": _file_sha256(source_score_path) if source_score_path.is_file() else None}
        )
        source_model_output_hashes.append(
            {
                "task_id": task_id,
                "sha256": _file_sha256(model_output_path) if model_output_path.is_file() else None,
            }
        )

        if adapter_failure_type is not None:
            score = _invalid_score(task, f"source adapter failure: {adapter_failure_type}")
        elif runner_agent_failure:
            score = _invalid_score(task, "source runner agent failure")
        elif not submission_path.is_file():
            score = _invalid_score(task, "source run did not preserve submission.json")
        else:
            try:
                submission = load_json(submission_path)
            except Exception as exc:  # noqa: BLE001 - participant JSON must fail closed.
                score = _invalid_score(
                    task,
                    f"source submission is invalid JSON: {type(exc).__name__}",
                )
            else:
                score = score_submission(task, submission)

        _write_json(output_dir / task_id / "score.json", score)
        _write_json(
            output_dir / task_id / "transcript.json",
            {"task_id": task_id, "entries": score.get("transcript", [])},
        )
        rescored_score_hashes.append(
            {"task_id": task_id, "sha256": stable_json_sha256(score)}
        )
        rescored_rows.append(
            _updated_task_row(
                source_row,
                task,
                public_task_path,
                score,
                adapter_failure_type=adapter_failure_type,
                runner_agent_failure=runner_agent_failure,
            )
        )

    current_fingerprint = benchmark_fingerprint(fingerprint_items)

    summary = {
        field: source_summary[field]
        for field in PUBLIC_SOURCE_SUMMARY_FIELDS
        if field in source_summary
    }
    summary["benchmark_commit_sha"] = target_commit
    summary["target_log_dir"] = target_log_dir
    summary["benchmark_fingerprint"] = current_fingerprint
    summary.update(summarize_task_results(rescored_rows))
    summary["rescore_provenance"] = {
        "schema_version": RESCORE_SCHEMA_VERSION,
        "derivation": "offline_rescore_from_saved_public_submissions",
        "source_run_id": run_id,
        "source_benchmark_commit_sha": source_summary.get("benchmark_commit_sha"),
        "target_benchmark_commit_sha": target_commit,
        "source_score_policy_version": (
            source_fingerprint.get("score_policy_version") if isinstance(source_fingerprint, dict) else None
        ),
        "target_score_policy_version": current_fingerprint["score_policy_version"],
        "source_summary_sha256": _file_sha256(source_summary_path),
        "source_submission_set_sha256": stable_json_sha256(submission_hashes),
        "source_score_set_sha256": stable_json_sha256(source_score_hashes),
        "source_model_output_set_sha256": stable_json_sha256(source_model_output_hashes),
        "rescored_score_set_sha256": stable_json_sha256(rescored_score_hashes),
        "rescored_task_rows_sha256": stable_json_sha256(rescored_rows),
        "scorer_source_sha256": _file_sha256(BENCHMARK_ROOT / "authzbench" / "score.py"),
        "runner_source_sha256": _file_sha256(BENCHMARK_ROOT / "authzbench" / "run.py"),
        "rescore_tool_sha256": _file_sha256(Path(__file__)),
        "adapter_failure_policy": "fail_closed_from_model_output_and_agent_returncode",
        "claim_exact_match_scored": False,
        "partial_boundary_credit_scored": False,
        "model_execution_repeated": False,
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-score a saved public AuthZBench-SaaS run without repeating model execution."
    )
    parser.add_argument("--source-run-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--public-target-log-dir-label",
        help="Public-safe relative replacement for an absolute source target_log_dir.",
    )
    parser.add_argument(
        "--target-benchmark-commit-sha",
        help="Checked-out clean target scorer/task source SHA (defaults to git rev-parse HEAD).",
    )
    args = parser.parse_args()
    summary = rescore_run(
        Path(args.source_run_dir),
        Path(args.output_dir),
        public_target_log_dir_label=args.public_target_log_dir_label,
        target_benchmark_commit_sha=args.target_benchmark_commit_sha,
    )
    print(
        dump_json(
            {
                "run_id": summary["run_id"],
                "task_count": summary["task_count"],
                "passed_count": summary["passed_count"],
                "mean_score": summary["mean_score"],
                "invalid_submission_count": summary["invalid_submission_count"],
                "adapter_failure_count": summary["adapter_failure_count"],
                "infrastructure_failure_count": summary["infrastructure_failure_count"],
                "boundary_reasoning_pass_rate": summary["boundary_reasoning_pass_rate"],
                "boundary_field_match_mean": summary["boundary_field_match_mean"],
                "score_policy_version": summary["benchmark_fingerprint"]["score_policy_version"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
