"""Run a multi-task Harbor adapter smoke test using the authzbench_harbor package.

Builds a public Harbor dataset from a small task subset, runs Harbor if available,
collects native AuthZBench scores for comparison, and writes public-safe evidence.

If Harbor CLI is unavailable, outputs a blocked evidence file and exits non-zero.
Does NOT fabricate pass evidence when Harbor cannot run.

Claim boundary: This script produces local smoke evidence only. It does not claim
Harbor platform acceptance, external review, or hosted leaderboard readiness.

Usage:
    python3 scripts/run_harbor_adapter_smoke.py \\
        --output artifact/harbor-adapter-smoke.json \\
        --dataset-dir artifact/harbor-dataset-public-smoke \\
        --task-count 6
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import shlex
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
from authzbench_harbor.schemas import ADAPTER_SMOKE_SCHEMA_VERSION
from scripts.validate_harbor_dataset_skeleton import (
    validate_harbor_dataset_skeleton,
)

PUBLIC_CLAIM_BOUNDARY = (
    "This is local Harbor adapter smoke evidence only. "
    "It does not claim Harbor platform acceptance, Kaggle acceptance, "
    "hosted public leaderboard readiness, SaaS-provider validation, "
    "external review, or third-party submissions."
)


def _blocked_output(blocker: str) -> dict[str, Any]:
    return {
        "schema_version": ADAPTER_SMOKE_SCHEMA_VERSION,
        "evidence_status": "blocked",
        "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
        "passed": False,
        "blocked": True,
        "blocker": blocker,
        "harbor_execution_verified": False,
        "current_claim_eligible": False,
        "requires_rerun_before_current_claim": True,
        "adapter_version": ADAPTER_VERSION,
        "external_review_complete": False,
        "harbor_acceptance_claimed": False,
        "hosted_execution_verified": False,
        "hosted_public_leaderboard_claimed": False,
        "kaggle_acceptance_claimed": False,
        "platform_acceptance_claimed": False,
        "saas_provider_validation_complete": False,
        "public_outputs_redacted": True,
        "raw_harbor_jobs_tracked": False,
        "private_artifacts_tracked": False,
    }


def _harbor_command() -> tuple[list[str], str] | None:
    """Return (cmd_parts, version_string) if Harbor is available, else None."""
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
    """Run Harbor on the dataset. Returns result dict or error string."""
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
        return f"Harbor run failed with exception: {exc}"

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
    if not isinstance(stats, dict):
        return "Harbor result stats must be an object"
    evals = stats.get("evals") or {}
    if not isinstance(evals, dict) or len(evals) != 1:
        return "Harbor result stats.evals must contain exactly one eval"
    eval_data = next(iter(evals.values()))
    if not isinstance(eval_data, dict):
        return "Harbor result eval data must be an object"
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
    }


def _manifest_task_ids(manifest: dict[str, Any]) -> tuple[list[str], str | None]:
    rows = manifest.get("tasks")
    if not isinstance(rows, list) or not rows:
        return [], "dataset manifest tasks must be a non-empty list"
    task_ids: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return [], f"dataset manifest tasks[{index}] must be an object"
        task_id = row.get("id")
        if not isinstance(task_id, str) or not task_id:
            return [], f"dataset manifest tasks[{index}].id must be a non-empty string"
        task_ids.append(task_id)
    if len(set(task_ids)) != len(task_ids):
        return [], "dataset manifest contains duplicate task ids"
    if manifest.get("task_count") != len(task_ids):
        return [], "dataset manifest task_count must exactly match task rows"
    return task_ids, None


def _harbor_result_error(result: dict[str, Any], task_count: int) -> str | None:
    run_id = result.get("harbor_run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return "Harbor result must contain a non-empty harbor_run_id"
    for field in ("n_total_trials", "n_completed_trials", "n_errored_trials"):
        value = result.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return f"Harbor result {field} must be a non-negative integer"
    if result["n_total_trials"] != task_count:
        return "Harbor n_total_trials must exactly match dataset task_count"
    if result["n_completed_trials"] != task_count or result["n_errored_trials"] != 0:
        return "Harbor smoke requires every task to complete without trial errors"
    reward_mean = result.get("reward_mean")
    if (
        not isinstance(reward_mean, (int, float))
        or isinstance(reward_mean, bool)
        or not math.isfinite(float(reward_mean))
    ):
        return "Harbor result reward_mean must be a finite number"
    return None


def _native_scores(dataset_dir: Path) -> dict[str, Any] | str:
    """Compute native AuthZBench scores for tasks in the dataset using empty-submission baseline."""
    manifest_path = dataset_dir / "dataset-manifest.json"
    if not manifest_path.is_file():
        return "dataset manifest is missing"
    try:
        manifest = load_json(manifest_path)
    except (ValueError, OSError) as exc:
        return f"failed to read dataset manifest: {exc}"
    if not isinstance(manifest, dict):
        return "dataset manifest must be a JSON object"
    task_ids, task_error = _manifest_task_ids(manifest)
    if task_error:
        return task_error

    scores: dict[str, Any] = {}
    for task_entry in manifest["tasks"]:
        task_dir_name = task_entry.get("harbor_task_dir")
        if not isinstance(task_dir_name, str) or not task_dir_name:
            return f"dataset manifest task {task_entry.get('id')!r} lacks harbor_task_dir"
        task_dir = dataset_dir / task_dir_name
        verifier_manifest = task_dir / "verifier" / "task_manifest.json"
        if not verifier_manifest.is_file():
            return f"verifier task manifest is missing for {task_entry['id']}"
        try:
            task = load_json(verifier_manifest)
        except (ValueError, OSError) as exc:
            return f"failed to read verifier task manifest for {task_entry['id']}: {exc}"
        if not isinstance(task, dict) or task.get("id") != task_entry["id"]:
            return f"verifier task manifest id mismatch for {task_entry['id']}"
        empty_submission = {"findings": []}
        try:
            score = score_submission(task, empty_submission)
        except Exception as exc:
            return f"native scoring failed for {task_entry['id']}: {exc}"
        score_value = score.get("score")
        if (
            not isinstance(score_value, (int, float))
            or isinstance(score_value, bool)
            or not math.isfinite(float(score_value))
        ):
            return f"native score for {task_entry['id']} must be finite"
        scores[task_entry["id"]] = {
            "score": score_value,
            "passed": score.get("passed", False),
            "submission_shape": "empty_findings_baseline",
        }
    if set(scores) != set(task_ids):
        return "native score task keys must exactly match dataset task ids"
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Run multi-task Harbor adapter smoke test")
    parser.add_argument("--output", default="artifact/harbor-adapter-smoke.json")
    parser.add_argument("--dataset-dir", default="artifact/harbor-dataset-public-smoke")
    parser.add_argument("--task-count", type=int, default=6)
    parser.add_argument("--tasks", default="tasks/**/*.json")
    parser.add_argument("--harness-lane", choices=["no_tools", "live_http_tool_agent"], default="no_tools")
    args = parser.parse_args()

    output_path = Path(args.output)
    dataset_dir = Path(args.dataset_dir)

    def _write_output(data: dict[str, Any]) -> None:
        violations = scan_for_violations(data, "smoke output")
        if violations:
            print(f"ERROR: public-safety violations in smoke output: {violations}", file=sys.stderr)
            sys.exit(1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dump_json(data) + "\n", encoding="utf-8")
        print(dump_json(data))

    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )
    source_state = benchmark_git_source_state()
    if source_state.get("benchmark_source_state") != "exact-commit-clean":
        blocked = _blocked_output(
            "local smoke execution requires executable benchmark sources to "
            "exactly match a Git commit"
        )
        blocked["generated_at"] = now
        blocked["benchmark_source_state"] = source_state.get(
            "benchmark_source_state"
        )
        _write_output(blocked)
        return 1
    benchmark_source_sha = source_state["benchmark_commit_sha"]

    # Build dataset
    print(f"Building Harbor dataset: {dataset_dir} (limit={args.task_count})", file=sys.stderr)
    try:
        manifest = build_dataset(
            [args.tasks],
            dataset_dir,
            harness_lane=args.harness_lane,
            limit=args.task_count,
            overwrite=True,
            benchmark_source_sha=benchmark_source_sha,
        )
    except ValueError as exc:
        blocked = _blocked_output(f"dataset build failed: {exc}")
        blocked["generated_at"] = now
        _write_output(blocked)
        return 1

    task_ids, manifest_error = _manifest_task_ids(manifest)
    if manifest_error:
        blocked = _blocked_output(f"invalid dataset manifest: {manifest_error}")
        blocked["generated_at"] = now
        _write_output(blocked)
        return 1
    task_count = len(task_ids)
    if manifest.get("benchmark_source_sha") != benchmark_source_sha:
        blocked = _blocked_output(
            "dataset manifest benchmark_source_sha does not match the exact "
            "executable benchmark commit"
        )
        blocked["generated_at"] = now
        _write_output(blocked)
        return 1
    dataset_validation = validate_harbor_dataset_skeleton(dataset_dir)
    if not dataset_validation["passed"]:
        blocked = _blocked_output(
            "generated dataset failed canonical public integrity validation "
            f"with {len(dataset_validation['errors'])} error(s)"
        )
        blocked["generated_at"] = now
        _write_output(blocked)
        return 1

    harbor_available = _harbor_command()
    if harbor_available is None:
        blocked = _blocked_output("Harbor CLI/package is not installed or not on PATH")
        blocked["generated_at"] = now
        blocked["benchmark_source_sha"] = benchmark_source_sha
        blocked["benchmark_source_state"] = "exact-commit-clean"
        blocked["dataset_built"] = True
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        _write_output(blocked)
        return 1

    harbor_cmd, harbor_version = harbor_available
    print(f"Harbor available: {' '.join(harbor_cmd)} ({harbor_version})", file=sys.stderr)

    # Compute native scores
    native_scores = _native_scores(dataset_dir)
    if isinstance(native_scores, str):
        blocked = _blocked_output(f"native scoring failed: {native_scores}")
        blocked["generated_at"] = now
        blocked["benchmark_source_sha"] = benchmark_source_sha
        blocked["benchmark_source_state"] = "exact-commit-clean"
        blocked["dataset_built"] = True
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        _write_output(blocked)
        return 1

    # Run Harbor
    print("Running Harbor ...", file=sys.stderr)
    harbor_result = _run_harbor(dataset_dir, harbor_cmd)

    if isinstance(harbor_result, str):
        blocked = _blocked_output(f"Harbor execution failed: {harbor_result}")
        blocked["generated_at"] = now
        blocked["benchmark_source_sha"] = benchmark_source_sha
        blocked["benchmark_source_state"] = "exact-commit-clean"
        blocked["dataset_built"] = True
        blocked["harbor_version"] = harbor_version
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        blocked["native_scores"] = native_scores
        _write_output(blocked)
        return 1

    harbor_result_error = _harbor_result_error(harbor_result, task_count)
    if harbor_result_error:
        blocked = _blocked_output(
            f"Harbor execution failed integrity checks: {harbor_result_error}"
        )
        blocked["generated_at"] = now
        blocked["benchmark_source_sha"] = benchmark_source_sha
        blocked["benchmark_source_state"] = "exact-commit-clean"
        blocked["dataset_built"] = True
        blocked["harbor_version"] = harbor_version
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        blocked["native_scores"] = native_scores
        _write_output(blocked)
        return 1

    evidence = {
        "schema_version": ADAPTER_SMOKE_SCHEMA_VERSION,
        "evidence_status": "local_source_bound_smoke",
        "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
        "generated_at": now,
        "benchmark_source_sha": benchmark_source_sha,
        "benchmark_source_state": "exact-commit-clean",
        "adapter_version": ADAPTER_VERSION,
        "harbor_version": harbor_version,
        "harness_lane": args.harness_lane,
        "task_count": task_count,
        "task_ids": task_ids,
        "passed": True,
        "blocked": False,
        "harbor_execution_verified": True,
        "current_claim_eligible": True,
        "requires_rerun_before_current_claim": False,
        "harbor_results": harbor_result,
        "native_scores": native_scores,
        "external_review_complete": False,
        "harbor_acceptance_claimed": False,
        "hosted_execution_verified": False,
        "hosted_public_leaderboard_claimed": False,
        "kaggle_acceptance_claimed": False,
        "platform_acceptance_claimed": False,
        "saas_provider_validation_complete": False,
        "public_outputs_redacted": True,
        "raw_harbor_jobs_tracked": False,
        "private_artifacts_tracked": False,
        "limitations": [
            "Public smoke only",
            "No platform acceptance claimed",
            "No private task content published",
            "Empty-findings baseline used for native score comparison",
        ],
    }
    _write_output(evidence)
    print(f"Smoke passed: {task_count} task(s) via Harbor", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
