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
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench.score import score_submission
from authzbench_harbor.adapter import ADAPTER_VERSION, build_dataset
from authzbench_harbor.redaction import scan_for_violations
from authzbench_harbor.schemas import (
    DEFAULT_REWARD_TOLERANCE,
    REQUIRED_MATCH_RATE,
    PARITY_EXPERIMENT_SCHEMA_VERSION,
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

    job_dirs = sorted((dataset_dir / "harbor-jobs").glob("*/result.json")) if (dataset_dir / "harbor-jobs").is_dir() else []
    if not job_dirs:
        return "Harbor run completed but no result.json found"

    result_path = job_dirs[-1]
    try:
        run_result = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"failed to read Harbor result.json: {exc}"

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


def _native_results(dataset_dir: Path) -> dict[str, Any]:
    """Compute native scores using empty-findings baseline for all tasks in dataset."""
    manifest_path = dataset_dir / "dataset-manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
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
        empty_submission = {"findings": []}
        try:
            score = score_submission(task, empty_submission)
        except Exception as exc:
            score = {"task_id": task.get("id"), "passed": False, "score": 0, "error": str(exc)}
        scores[task_entry["id"]] = {
            "score": float(score.get("score") or 0),
            "passed": bool(score.get("passed")),
            "submission_shape": "empty_findings_baseline",
        }
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
    parser.add_argument("--rebuild-dataset", action="store_true", help="Rebuild dataset even if it exists")
    args = parser.parse_args()

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
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
        except (json.JSONDecodeError, OSError):
            manifest = {}

    task_ids = [t["id"] for t in manifest.get("tasks", [])]
    task_count = manifest.get("task_count", len(task_ids))

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

    # Compare parity
    harbor_reward_mean = harbor_result.get("reward_mean")
    native_scores_list = [v.get("score", 0) for v in native_results.values()]
    native_mean = sum(native_scores_list) / len(native_scores_list) if native_scores_list else None

    # Compute per-task parity
    job_dir_str = harbor_result.pop("job_dir", None)
    harbor_per_task_rewards = {}
    if job_dir_str:
        for trial_result_path in Path(job_dir_str).glob("*/result.json"):
            try:
                trial_data = json.loads(trial_result_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            task_id = trial_data.get("task_name")
            if task_id and "/" in task_id:
                # Harbor prefixes task_name with the dataset name (e.g. "authzbench-saas/tok_foo").
                # Strip the prefix so the key matches native_authzbench_results and task_ids.
                task_id = task_id.rsplit("/", 1)[-1]
            if not task_id:
                trial_name = trial_data.get("id") or trial_data.get("trial_name", "")
                if "__" in trial_name:
                    task_id = trial_name.rsplit("__", 1)[0]
                else:
                    task_id = trial_name

            verifier_result = trial_data.get("verifier_result") or {}
            rewards = verifier_result.get("rewards") or {}
            if "reward" in rewards:
                harbor_per_task_rewards[task_id] = float(rewards["reward"])

    native_per_task_scores = {tid: float(res.get("score", 0.0)) for tid, res in native_results.items()}

    per_task_match = {}
    per_task_disagreements = []
    parity_match_threshold = 1.0  # Exact match (0.0 tolerance in difference, or required similarity)

    for tid in task_ids:
        native_score = native_per_task_scores.get(tid, 0.0)
        harbor_reward = harbor_per_task_rewards.get(tid)

        if harbor_reward is None:
            per_task_match[tid] = False
            per_task_disagreements.append(tid)
        else:
            # using an exact match comparison
            match = abs(native_score - harbor_reward) < 1e-5
            per_task_match[tid] = match
            if not match:
                per_task_disagreements.append(tid)

    per_task_match_count = sum(per_task_match.values())
    per_task_match_rate = per_task_match_count / len(task_ids) if task_ids else 0.0

    reward_parity_failures: list[str] = []
    parity_verified = False
    if harbor_reward_mean is not None and native_mean is not None:
        if per_task_match_rate == 1.0:
            parity_verified = True
        else:
            reward_parity_failures.append(f"Per-task match rate is {per_task_match_rate:.2f}, expected 1.0")
    else:
        reward_parity_failures.append("Harbor reward mean or native mean not computable")

    # Methodology split: per_task_pairing is the default for new evidence.
    # parity_verified is recomputed from per-task data only, not from aggregate
    # means, so the validator cannot be fooled by aggregate-mean comparison.
    methodology = args.parity_methodology
    reward_tolerance = DEFAULT_REWARD_TOLERANCE
    required_match_rate = REQUIRED_MATCH_RATE

    if methodology == "per_task_pairing":
        # Strict equality: per-task match count + rate + empty disagreements.
        parity_verified = (
            per_task_match_rate >= required_match_rate
            and len(per_task_disagreements) == 0
            and per_task_match_count == len(task_ids)
        )
    else:
        # aggregate_means path kept for back-compat only. Generator does not
        # use it for new evidence; if explicitly requested, fall back to the
        # aggregate-mean comparison.
        parity_verified = (
            harbor_reward_mean is not None
            and native_mean is not None
            and abs(harbor_reward_mean - native_mean) < reward_tolerance
        )

    experiment = {
        "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
        "evidence_status": "current",
        "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
        "generated_at": now,
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
