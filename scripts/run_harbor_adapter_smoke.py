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
import shlex
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
from authzbench_harbor.schemas import ADAPTER_SMOKE_SCHEMA_VERSION

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
        "adapter_version": ADAPTER_VERSION,
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

    job_dirs = sorted((dataset_dir / "harbor-jobs").glob("*/result.json")) if (dataset_dir / "harbor-jobs").is_dir() else []
    if not job_dirs:
        return "Harbor run completed but no result.json found in harbor-jobs/"

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
    }


def _native_scores(dataset_dir: Path) -> dict[str, Any]:
    """Compute native AuthZBench scores for tasks in the dataset using empty-submission baseline."""
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
            "score": score.get("score", 0),
            "passed": score.get("passed", False),
            "submission_shape": "empty_findings_baseline",
        }
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

    # Build dataset
    print(f"Building Harbor dataset: {dataset_dir} (limit={args.task_count})", file=sys.stderr)
    try:
        manifest = build_dataset(
            [args.tasks],
            dataset_dir,
            harness_lane=args.harness_lane,
            limit=args.task_count,
            overwrite=True,
        )
    except ValueError as exc:
        blocked = _blocked_output(f"dataset build failed: {exc}")
        _write_output(blocked)
        return 1

    task_ids = [t["id"] for t in manifest.get("tasks", [])]
    task_count = manifest.get("task_count", 0)

    harbor_available = _harbor_command()
    if harbor_available is None:
        blocked = _blocked_output("Harbor CLI/package is not installed or not on PATH")
        blocked["dataset_built"] = True
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        _write_output(blocked)
        return 1

    harbor_cmd, harbor_version = harbor_available
    print(f"Harbor available: {' '.join(harbor_cmd)} ({harbor_version})", file=sys.stderr)

    # Compute native scores
    native_scores = _native_scores(dataset_dir)

    # Run Harbor
    print("Running Harbor ...", file=sys.stderr)
    harbor_result = _run_harbor(dataset_dir, harbor_cmd)

    if isinstance(harbor_result, str):
        blocked = _blocked_output(f"Harbor execution failed: {harbor_result}")
        blocked["dataset_built"] = True
        blocked["harbor_version"] = harbor_version
        blocked["task_count"] = task_count
        blocked["task_ids"] = task_ids
        blocked["native_scores"] = native_scores
        _write_output(blocked)
        return 1

    now = datetime.datetime.utcnow().isoformat() + "Z"
    evidence = {
        "schema_version": ADAPTER_SMOKE_SCHEMA_VERSION,
        "evidence_status": "harbor_adapter_smoke",
        "public_claim_boundary": PUBLIC_CLAIM_BOUNDARY,
        "generated_at": now,
        "adapter_version": ADAPTER_VERSION,
        "harbor_version": harbor_version,
        "harness_lane": args.harness_lane,
        "task_count": task_count,
        "task_ids": task_ids,
        "passed": True,
        "blocked": False,
        "harbor_execution_verified": True,
        "harbor_results": harbor_result,
        "native_scores": native_scores,
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
