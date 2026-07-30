"""Run a native-vs-Harbor parity experiment.

Builds a public Harbor dataset, runs Harbor if available, computes native
AuthZBench scores for the same tasks/submissions, and produces a public-safe
parity evidence file.

Claim boundary: This script produces local parity experiment evidence only.
It does not claim Harbor platform acceptance, external review, or hosted
leaderboard readiness. parity_verified is only set to true when both
native and Harbor reward distributions are computed from real runs.

Usage:
    python3 scripts/run_harbor_parity_experiment.py \\
        --output artifact/harbor-parity-experiment.json \\
        --dataset-dir artifact/harbor-dataset-public-smoke
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import benchmark_git_source_state, dump_json, load_json
from authzbench.score import score_submission
from authzbench_harbor.adapter import ADAPTER_VERSION, build_dataset
from authzbench_harbor.redaction import scan_for_violations
from authzbench_harbor.schemas import (
    DEFAULT_REWARD_TOLERANCE,
    REQUIRED_MATCH_RATE,
    PARITY_EXPERIMENT_SCHEMA_VERSION,
)
from scripts.validate_harbor_dataset_skeleton import (
    validate_harbor_dataset_skeleton,
)

PUBLIC_CLAIM_BOUNDARY = (
    "This parity experiment evidence covers public tasks only. "
    "It does not claim Harbor platform acceptance, Kaggle acceptance, "
    "hosted public leaderboard readiness, SaaS-provider validation, "
    "external review, or third-party submissions."
)


def _harbor_command() -> tuple[list[str], str] | None:
    for candidate in (["uvx", "harbor"], ["harbor"]):
        if not shutil.which(candidate[0]):
            continue
        try:
            result = subprocess.run(
                [*candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                version = (result.stdout or result.stderr).strip().splitlines()[-1].strip()
                return candidate, version
        except Exception:
            continue
    return None


def _run_harbor(dataset_dir: Path, harbor_cmd: list[str], *, timeout: int = 300) -> dict[str, Any] | str:
    run_config = dataset_dir / "run_authzbench_saas.yaml"
    if not run_config.is_file():
        return f"run config not found: {run_config}"
    jobs_root = dataset_dir / "harbor-jobs"
    try:
        existing_job_dirs = (
            {path.resolve() for path in jobs_root.iterdir() if path.is_dir()}
            if jobs_root.is_dir()
            else set()
        )
    except OSError as exc:
        return f"failed to snapshot existing Harbor job directories: {exc}"

    cmd = [*harbor_cmd, "run", "-c", "run_authzbench_saas.yaml", "--yes"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(dataset_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Harbor run timed out after {timeout}s"
    except Exception as exc:
        return f"Harbor run failed: {exc}"

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[-500:]
        return f"Harbor run exited {result.returncode}: {stderr}"

    result_paths = sorted(jobs_root.glob("*/result.json")) if jobs_root.is_dir() else []
    new_result_paths = [
        path for path in result_paths if path.parent.resolve() not in existing_job_dirs
    ]
    if len(new_result_paths) != 1:
        return (
            "Harbor run must create exactly one newly created job result; "
            f"found {len(new_result_paths)}"
        )

    result_path = new_result_paths[0]
    try:
        run_result = load_json(result_path)
    except (ValueError, OSError) as exc:
        return f"failed to read Harbor result.json: {exc}"
    if not isinstance(run_result, dict):
        return "Harbor result.json must be a JSON object"

    stats = run_result.get("stats") or {}
    evals = stats.get("evals") or {}
    eval_data = next(iter(evals.values()), {})
    metrics = eval_data.get("metrics") or []
    reward_mean = None
    if metrics and isinstance(metrics[0], dict):
        reward_mean = metrics[0].get("mean")

    return {
        "harbor_run_id": run_result.get("id"),
        "n_total_trials": run_result.get("n_total_trials"),
        "n_completed_trials": stats.get("n_completed_trials"),
        "n_errored_trials": stats.get("n_errored_trials"),
        "reward_mean": reward_mean,
        "job_dir": str(result_path.parent),
    }


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _manifest_task_ids(manifest: dict[str, Any]) -> tuple[list[str], str | None]:
    task_rows = manifest.get("tasks")
    if not isinstance(task_rows, list) or not task_rows:
        return [], "dataset manifest tasks must be a non-empty list"

    task_ids: list[str] = []
    for index, row in enumerate(task_rows):
        if not isinstance(row, dict):
            return [], f"dataset manifest tasks[{index}] must be an object"
        task_id = row.get("id")
        if not isinstance(task_id, str) or not task_id:
            return [], f"dataset manifest tasks[{index}].id must be a non-empty string"
        task_ids.append(task_id)

    duplicates = sorted(
        {task_id for task_id in task_ids if task_ids.count(task_id) > 1}
    )
    if duplicates:
        return [], f"dataset manifest contains duplicate task ids: {duplicates}"

    task_count = manifest.get("task_count")
    if (
        not isinstance(task_count, int)
        or isinstance(task_count, bool)
        or task_count != len(task_rows)
    ):
        return (
            [],
            "dataset manifest task_count must exactly match the number of task rows",
        )
    return task_ids, None


def _native_results_error(
    task_ids: list[str],
    native_results: dict[str, Any],
) -> str | None:
    if set(native_results) != set(task_ids):
        return (
            "native result task keys must exactly match dataset task ids; "
            f"missing={sorted(set(task_ids) - set(native_results))}, "
            f"unexpected={sorted(set(native_results) - set(task_ids))}"
        )
    for task_id in task_ids:
        row = native_results.get(task_id)
        if not isinstance(row, dict) or not _is_finite_number(row.get("score")):
            return f"native result for task '{task_id}' must contain a finite numeric score"
        if row.get("error"):
            return f"native result for task '{task_id}' contains a scoring error"
    return None


def _harbor_summary_error(
    harbor_result: dict[str, Any],
    task_count: int,
) -> str | None:
    run_id = harbor_result.get("harbor_run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return "Harbor result must contain a non-empty harbor_run_id"

    counts: dict[str, int] = {}
    for field in ("n_total_trials", "n_completed_trials", "n_errored_trials"):
        value = harbor_result.get(field)
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            return f"Harbor result {field} must be a non-negative integer"
        counts[field] = value

    if counts["n_total_trials"] != task_count:
        return (
            "Harbor n_total_trials must exactly match dataset task_count; "
            f"got {counts['n_total_trials']}, expected {task_count}"
        )
    if counts["n_completed_trials"] + counts["n_errored_trials"] != counts["n_total_trials"]:
        return (
            "Harbor completed and errored trial counts must sum to n_total_trials"
        )
    if not _is_finite_number(harbor_result.get("reward_mean")):
        return "Harbor result reward_mean must be a finite number"
    return None


def _trial_task_key(
    trial_data: dict[str, Any],
    expected_task_ids: list[str],
) -> str:
    task_name = trial_data.get("task_name")
    if isinstance(task_name, str) and task_name:
        exact_matches = [
            task_id
            for task_id in expected_task_ids
            if task_name == task_id or task_name.endswith(f"/{task_id}")
        ]
        if len(exact_matches) == 1:
            return exact_matches[0]
        return task_name.rsplit("/", 1)[-1]

    trial_name = trial_data.get("id") or trial_data.get("trial_name")
    if not isinstance(trial_name, str):
        return ""
    prefix_matches = [
        task_id
        for task_id in expected_task_ids
        if trial_name == task_id or trial_name.startswith(f"{task_id}__")
    ]
    return prefix_matches[0] if len(prefix_matches) == 1 else trial_name


def _collect_harbor_trial_rewards(
    job_dir: Path,
    expected_task_ids: list[str],
) -> dict[str, float] | str:
    if len(set(expected_task_ids)) != len(expected_task_ids):
        return "expected task ids contain duplicates"

    trial_paths = sorted(job_dir.glob("*/result.json"))
    if len(trial_paths) != len(expected_task_ids):
        return (
            "Harbor trial result count must exactly match task count; "
            f"found {len(trial_paths)}, expected {len(expected_task_ids)}"
        )

    expected = set(expected_task_ids)
    rewards_by_task: dict[str, float] = {}
    for trial_path in trial_paths:
        try:
            trial_data = load_json(trial_path)
        except (ValueError, OSError) as exc:
            return f"failed to read Harbor trial result: {exc}"
        if not isinstance(trial_data, dict):
            return "Harbor trial result must be a JSON object"

        task_id = _trial_task_key(trial_data, expected_task_ids)
        if task_id not in expected:
            return f"unknown trial task key: {task_id!r}"
        if task_id in rewards_by_task:
            return f"duplicate trial task key: {task_id!r}"

        verifier_result = trial_data.get("verifier_result")
        rewards = (
            verifier_result.get("rewards")
            if isinstance(verifier_result, dict)
            else None
        )
        reward = rewards.get("reward") if isinstance(rewards, dict) else None
        if not _is_finite_number(reward):
            return f"trial task '{task_id}' must contain a finite numeric reward"
        rewards_by_task[task_id] = float(reward)

    if set(rewards_by_task) != expected:
        return (
            "Harbor trial task keys must exactly match dataset task ids; "
            f"missing={sorted(expected - set(rewards_by_task))}, "
            f"unexpected={sorted(set(rewards_by_task) - expected)}"
        )
    return rewards_by_task


def _native_results(dataset_dir: Path) -> dict[str, Any]:
    """Compute native scores using empty-findings baseline for all tasks in dataset."""
    manifest_path = dataset_dir / "dataset-manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = load_json(manifest_path)
    except (ValueError, OSError):
        return {}

    scores = {}
    for task_entry in manifest.get("tasks", []):
        task_dir = dataset_dir / task_entry["harbor_task_dir"]
        verifier_manifest = task_dir / "verifier" / "task_manifest.json"
        if not verifier_manifest.is_file():
            continue
        try:
            task = load_json(verifier_manifest)
        except Exception:
            continue
        if task.get("id") != task_entry.get("id"):
            scores[task_entry["id"]] = {
                "score": 0.0,
                "passed": False,
                "submission_shape": "empty_findings_baseline",
                "error": "verifier task id does not match dataset manifest row",
            }
            continue
        empty_submission = {"findings": []}
        try:
            score = score_submission(task, empty_submission)
        except Exception as exc:
            score = {"task_id": task.get("id"), "passed": False, "score": 0, "error": str(exc)}
        if not isinstance(score, dict):
            score = {
                "task_id": task.get("id"),
                "passed": False,
                "score": None,
                "error": "native scorer returned a non-object result",
            }
        raw_score = score.get("score")
        normalized_score: object = (
            float(raw_score) if _is_finite_number(raw_score) else raw_score
        )
        scores[task_entry["id"]] = {
            "score": normalized_score,
            "passed": bool(score.get("passed")),
            "submission_shape": "empty_findings_baseline",
        }
        if score.get("error"):
            scores[task_entry["id"]]["error"] = str(score["error"])
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Run native-vs-Harbor parity experiment")
    parser.add_argument("--output", default="artifact/harbor-parity-experiment.json")
    parser.add_argument("--dataset-dir", default="artifact/harbor-dataset-public-smoke")
    parser.add_argument(
        "--parity-methodology",
        choices=("per_task_pairing", "aggregate_means"),
        default="per_task_pairing",
        help=(
            "Parity methodology. New evidence must use per_task_pairing. "
            "aggregate_means is provided for back-compat with historical evidence only."
        ),
    )
    parser.add_argument("--task-count", type=int, default=6)
    parser.add_argument("--tasks", default="tasks/**/*.json")
    parser.add_argument("--harness-lane", choices=["no_tools", "live_http_tool_agent"], default="no_tools")
    parser.add_argument(
        "--oracle-solution-mode",
        choices=["none", "secure-control-empty-findings"],
        default="secure-control-empty-findings",
    )
    parser.add_argument("--rebuild-dataset", action="store_true", help="Rebuild dataset even if it exists")
    args = parser.parse_args()

    if args.parity_methodology != "per_task_pairing":
        print(
            "ERROR: new parity evidence must use per_task_pairing; "
            "aggregate_means is historical validation compatibility only",
            file=sys.stderr,
        )
        return 2

    output_path = Path(args.output)
    dataset_dir = Path(args.dataset_dir)

    def _write(data: dict[str, Any]) -> None:
        violations = scan_for_violations(data, "parity experiment output")
        if violations:
            print(f"ERROR: public-safety violations: {violations}", file=sys.stderr)
            sys.exit(1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dump_json(data) + "\n", encoding="utf-8")

    now = datetime.datetime.utcnow().isoformat() + "Z"
    source_state = benchmark_git_source_state()
    if source_state.get("benchmark_source_state") != "exact-commit-clean":
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [
                "parity execution requires executable benchmark sources to "
                "exactly match a Git commit"
            ],
            "benchmark_source_state": source_state.get("benchmark_source_state"),
            "generated_at": now,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1
    benchmark_source_sha = source_state["benchmark_commit_sha"]

    # Build or reuse dataset
    if not dataset_dir.is_dir() or args.rebuild_dataset:
        print(f"Building Harbor dataset: {dataset_dir}", file=sys.stderr)
        try:
            manifest = build_dataset(
                [args.tasks],
                dataset_dir,
                harness_lane=args.harness_lane,
                limit=args.task_count,
                overwrite=True,
                oracle_solution_mode=args.oracle_solution_mode,
                benchmark_source_sha=benchmark_source_sha,
            )
        except ValueError as exc:
            blocked = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "blocked",
                "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
                "parity_verified": False,
                "blocked_until": [f"dataset build failed: {exc}"],
                "generated_at": now,
            }
            _write(blocked)
            return 1
    else:
        manifest_path = dataset_dir / "dataset-manifest.json"
        try:
            manifest = load_json(manifest_path) if manifest_path.is_file() else {}
        except (ValueError, OSError):
            manifest = {}

    if not isinstance(manifest, dict):
        manifest = {}
    task_ids, manifest_error = _manifest_task_ids(manifest)
    if manifest_error:
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [f"invalid dataset manifest: {manifest_error}"],
            "adapter_version": ADAPTER_VERSION,
            "generated_at": now,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1
    task_count = len(task_ids)
    if manifest.get("benchmark_source_sha") != benchmark_source_sha:
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [
                "dataset manifest benchmark_source_sha does not match the "
                "exact executable benchmark commit"
            ],
            "benchmark_source_sha": benchmark_source_sha,
            "benchmark_source_state": "exact-commit-clean",
            "adapter_version": ADAPTER_VERSION,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1
    dataset_validation = validate_harbor_dataset_skeleton(dataset_dir)
    if not dataset_validation["passed"]:
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [
                "generated dataset failed canonical public integrity validation "
                f"with {len(dataset_validation['errors'])} error(s)"
            ],
            "adapter_version": ADAPTER_VERSION,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1

    harbor_available = _harbor_command()
    if harbor_available is None:
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": ["Harbor CLI/package is not installed or not on PATH"],
            "adapter_version": ADAPTER_VERSION,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        print("Blocked: Harbor CLI not available", file=sys.stderr)
        return 1

    harbor_cmd, harbor_version = harbor_available
    print(f"Harbor: {' '.join(harbor_cmd)} ({harbor_version})", file=sys.stderr)

    native_results = _native_results(dataset_dir)
    native_error = _native_results_error(task_ids, native_results)
    if native_error:
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [f"native scoring failed integrity checks: {native_error}"],
            "adapter_version": ADAPTER_VERSION,
            "harbor_version": harbor_version,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1

    print("Running Harbor for parity ...", file=sys.stderr)
    harbor_result = _run_harbor(dataset_dir, harbor_cmd)

    if isinstance(harbor_result, str):
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [f"Harbor execution failed: {harbor_result}"],
            "adapter_version": ADAPTER_VERSION,
            "harbor_version": harbor_version,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "native_authzbench_results": native_results,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1

    job_dir_str = harbor_result.pop("job_dir", None)
    summary_error = _harbor_summary_error(harbor_result, task_count)
    if summary_error or not isinstance(job_dir_str, str):
        reason = summary_error or "Harbor result is not bound to a newly created job directory"
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [f"Harbor execution failed integrity checks: {reason}"],
            "adapter_version": ADAPTER_VERSION,
            "harbor_version": harbor_version,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "native_authzbench_results": native_results,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1

    collected_rewards = _collect_harbor_trial_rewards(Path(job_dir_str), task_ids)
    if isinstance(collected_rewards, str):
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [
                f"Harbor trial collection failed integrity checks: {collected_rewards}"
            ],
            "adapter_version": ADAPTER_VERSION,
            "harbor_version": harbor_version,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "native_authzbench_results": native_results,
            "harbor_results": harbor_result,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1
    harbor_per_task_rewards = collected_rewards

    native_per_task_scores = {
        task_id: float(native_results[task_id]["score"])
        for task_id in task_ids
    }
    native_mean = sum(native_per_task_scores.values()) / task_count
    harbor_reward_mean = sum(harbor_per_task_rewards.values()) / task_count
    if not math.isclose(
        float(harbor_result["reward_mean"]),
        harbor_reward_mean,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        blocked = {
            "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
            "evidence_status": "blocked",
            "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
            "parity_verified": False,
            "blocked_until": [
                "Harbor aggregate reward_mean does not match recomputed per-task mean"
            ],
            "adapter_version": ADAPTER_VERSION,
            "harbor_version": harbor_version,
            "generated_at": now,
            "task_count": task_count,
            "task_ids": task_ids,
            "native_authzbench_results": native_results,
            "harbor_results": harbor_result,
            "raw_harbor_jobs_tracked": False,
            "private_artifacts_tracked": False,
        }
        _write(blocked)
        return 1

    per_task_match = {}
    per_task_disagreements = []
    parity_match_threshold = REQUIRED_MATCH_RATE
    reward_tolerance = DEFAULT_REWARD_TOLERANCE
    required_match_rate = REQUIRED_MATCH_RATE

    for tid in task_ids:
        native_score = native_per_task_scores[tid]
        harbor_reward = harbor_per_task_rewards[tid]
        match = abs(native_score - harbor_reward) <= reward_tolerance
        per_task_match[tid] = match
        if not match:
            per_task_disagreements.append(tid)

    per_task_match_count = sum(per_task_match.values())
    per_task_match_rate = per_task_match_count / len(task_ids) if task_ids else 0.0

    reward_parity_failures: list[str] = []
    if per_task_match_rate != required_match_rate:
        reward_parity_failures.append(
            f"Per-task match rate is {per_task_match_rate:.2f}, "
            f"expected {required_match_rate:.2f}"
        )
    if harbor_result["n_completed_trials"] != task_count:
        reward_parity_failures.append(
            "Completed trial count does not exactly match task count"
        )
    if harbor_result["n_errored_trials"] != 0:
        reward_parity_failures.append(
            f"Harbor reported {harbor_result['n_errored_trials']} errored trial(s)"
        )

    # Methodology split: per_task_pairing is the default for new evidence.
    # parity_verified is recomputed from per-task data only, not from aggregate
    # means, so the validator cannot be fooled by aggregate-mean comparison.
    methodology = args.parity_methodology

    if methodology == "per_task_pairing":
        parity_verified = (
            per_task_match_rate == required_match_rate
            and len(per_task_disagreements) == 0
            and per_task_match_count == len(task_ids)
            and harbor_result["n_total_trials"] == task_count
            and harbor_result["n_completed_trials"] == task_count
            and harbor_result["n_errored_trials"] == 0
        )
    else:
        # aggregate_means path kept for back-compat only. Generator does not
        # use it for new evidence; if explicitly requested, fall back to the
        # aggregate-mean comparison.
        parity_verified = (
            abs(harbor_reward_mean - native_mean) <= reward_tolerance
            and harbor_result["n_total_trials"] == task_count
            and harbor_result["n_completed_trials"] == task_count
            and harbor_result["n_errored_trials"] == 0
        )

    experiment = {
        "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
        "evidence_status": "current",
        "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
        "generated_at": now,
        "benchmark_source_sha": benchmark_source_sha,
        "benchmark_source_state": "exact-commit-clean",
        "adapter_version": ADAPTER_VERSION,
        "harbor_version": harbor_version,
        "harness_lane": args.harness_lane,
        "task_count": task_count,
        "task_ids": task_ids,
        "native_authzbench_results": native_results,
        "harbor_results": harbor_result,
        "native_mean_score": native_mean,
        "harbor_reward_mean": harbor_reward_mean,
        "harbor_per_task_rewards": harbor_per_task_rewards,
        "native_per_task_scores": native_per_task_scores,
        "per_task_match": per_task_match,
        "per_task_match_count": per_task_match_count,
        "per_task_match_rate": per_task_match_rate,
        "per_task_disagreements": per_task_disagreements,
        "parity_match_threshold": parity_match_threshold,
        "parity_methodology": methodology,
        "required_match_rate": required_match_rate,
        "reward_tolerance": reward_tolerance,
        "methodology_note": (
            "Generator-emitted parity evidence. New evidence uses "
            "per_task_pairing; aggregate_means is reserved for historical "
            "back-compat. Recompute parity_verified from per-task data only."
        ),
        "parity_verified": parity_verified,
        "current_claim_eligible": parity_verified,
        "requires_rerun_before_current_claim": not parity_verified,
        "reward_parity_failures": reward_parity_failures,
        "redaction_status": "passed",
        "raw_harbor_jobs_tracked": False,
        "private_artifacts_tracked": False,
        "limitations": [
            "Public smoke only",
            "No platform acceptance claimed",
            "No private task content published",
            "Empty-findings baseline used for native scoring",
            "Parity verified only via per_task_pairing across matching Harbor and native run artifacts; broader per-agent and per-model pairing remains a v2-deferred external-validation track.",
        ],
    }
    _write(experiment)
    print(dump_json(experiment))
    if parity_verified:
        print(f"Parity verified: native_mean={native_mean:.3f} harbor_mean={harbor_reward_mean:.3f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
