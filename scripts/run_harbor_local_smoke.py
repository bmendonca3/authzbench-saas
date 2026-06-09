from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_harbor_dataset_skeleton import build_harbor_dataset_skeleton
from scripts.validate_harbor_dataset_skeleton import validate_harbor_dataset_skeleton
from scripts.validate_harbor_local_evidence import SCHEMA_VERSION


DEFAULT_TASK = "tasks/project_mgmt/pm_same_tenant_read_control.json"
DEFAULT_OUTPUT = ROOT / "artifact" / "harbor-local-execution-smoke.json"


def _run_capture(cmd: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _command_version(command: str, version_args: list[str]) -> str:
    parts = shlex.split(command)
    if not parts or shutil.which(parts[0]) is None:
        raise RuntimeError(f"command not available: {command}")
    result = _run_capture([*parts, *version_args], timeout=30)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[:1]
        raise RuntimeError(f"{command} {' '.join(version_args)} failed: {'; '.join(detail)}")
    return (result.stdout or result.stderr).strip().splitlines()[-1].strip()


def _docker_server_version() -> str:
    result = _run_capture(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=30)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[:1]
        raise RuntimeError(f"docker info failed: {'; '.join(detail)}")
    return result.stdout.strip()


def _harbor_result(dataset_dir: Path) -> dict[str, Any]:
    result_paths = sorted(dataset_dir.glob("harbor-jobs/*/result.json"))
    if len(result_paths) != 1:
        raise RuntimeError(f"expected exactly one Harbor result.json, found {len(result_paths)}")
    result = json.loads(result_paths[0].read_text(encoding="utf-8"))
    stats = result.get("stats") or {}
    evals = stats.get("evals") or {}
    eval_data = next(iter(evals.values()), {})
    metrics = eval_data.get("metrics") or []
    reward_mean = None
    if metrics and isinstance(metrics[0], dict):
        reward_mean = metrics[0].get("mean")
    reward_files = sorted({path.name for path in result_paths[0].parent.glob("*/verifier/reward.*")})
    return {
        "harbor_run_id": result.get("id"),
        "n_total_trials": result.get("n_total_trials"),
        "n_completed_trials": stats.get("n_completed_trials"),
        "n_errored_trials": stats.get("n_errored_trials"),
        "reward_mean": reward_mean,
        "verifier_reward_files": reward_files,
    }


def build_harbor_local_smoke(
    *,
    task: str,
    output: Path,
    harbor_command: str,
) -> dict[str, Any]:
    harbor_version = _command_version(harbor_command, ["--version"])
    docker_version = _docker_server_version()
    benchmark_source_sha = _run_capture(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=30).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="authzbench-harbor-smoke-") as tmp:
        dataset_dir = Path(tmp) / "dataset"
        manifest = build_harbor_dataset_skeleton([task], dataset_dir, harness_lane="no_tools", clean=True)
        validation = validate_harbor_dataset_skeleton(dataset_dir)
        if not validation["passed"]:
            raise RuntimeError("generated Harbor dataset skeleton failed validation: " + json.dumps(validation["errors"]))

        harbor_parts = shlex.split(harbor_command)
        run_result = _run_capture(
            [*harbor_parts, "run", "-c", "run_authzbench_saas.yaml", "--yes", "--debug"],
            cwd=dataset_dir,
            timeout=180,
        )
        if run_result.returncode != 0:
            detail = (run_result.stderr or run_result.stdout).strip().splitlines()[-5:]
            raise RuntimeError("Harbor run failed: " + " | ".join(detail))
        harbor_summary = _harbor_result(dataset_dir)

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "evidence_status": "local_harbor_execution_smoke",
        "public_claim_boundary": (
            "This is local Harbor task/agent/verifier smoke evidence only; "
            "not parity evidence, not hosted leaderboard readiness, not external review evidence, "
            "and not v1 readiness."
        ),
        "benchmark_source_sha": benchmark_source_sha,
        "harbor_command": harbor_command,
        "harbor_version": harbor_version,
        "docker_server_version": docker_version,
        "run_command_template": "cd <generated-public-dataset> && harbor run -c run_authzbench_saas.yaml --yes --debug",
        "task_ids": [task["id"] for task in manifest["tasks"]],
        "task_count": manifest["task_count"],
        "harness_lane": "no_tools",
        "harbor_execution_verified": True,
        "parity_verified": False,
        "public_outputs_redacted": True,
        "private_artifacts_tracked": False,
        "raw_harbor_jobs_tracked": False,
        "expected_zero_reward_reason": "The generated skeleton oracle does not write an agent submission, so verifier completion is expected to produce zero reward for missing submission.",
        "blocked_until": [
            "a public-safe agent or adapter writes a valid submission.json",
            "matching native AuthZBench-SaaS public-run evidence is generated",
            "parity_experiment.json is computed from real Harbor and native run artifacts",
        ],
        **harbor_summary,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a public-safe local Harbor skeleton smoke and write redacted evidence.")
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--harbor-command", default="uvx harbor")
    args = parser.parse_args()
    evidence = build_harbor_local_smoke(task=args.task, output=args.output, harbor_command=args.harbor_command)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
