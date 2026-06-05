from __future__ import annotations

import argparse
import glob
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import build_context, dump_json, load_json
from .score import score_submission


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(data) + "\n", encoding="utf-8")


def _task_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _run_agent(agent_cmd: str, cwd: Path, context_path: Path, submission_path: Path, timeout_seconds: int) -> dict[str, Any]:
    command = agent_cmd.format(
        context=shlex.quote(str(context_path)),
        submission=shlex.quote(str(submission_path)),
    )
    env = os.environ.copy()
    env.update(
        {
            "AUTHZBENCH_CONTEXT": str(context_path),
            "AUTHZBENCH_SUBMISSION": str(submission_path),
        }
    )
    started = time.time()
    argv = shlex.split(command)
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "duration_seconds": round(time.time() - started, 4),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_benchmark(
    task_patterns: list[str],
    agent_cmd: str,
    results_dir: Path,
    timeout_seconds: int,
    benchmark_version: str = "alpha-0.0.1-public-scaffold-local",
    benchmark_commit_sha: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    harness_type: str | None = None,
) -> dict[str, Any]:
    run_id = _utc_run_id()
    run_dir = results_dir / run_id
    task_results = []
    root = Path.cwd()

    for task_path in _task_paths(task_patterns):
        task = load_json(task_path)
        task_dir = run_dir / task["id"]
        context_path = task_dir / "context.json"
        submission_path = task_dir / "submission.json"
        _write_json(context_path, build_context(task))

        try:
            agent_result = _run_agent(agent_cmd, root, context_path, submission_path, timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            agent_result = {
                "command": agent_cmd,
                "returncode": None,
                "duration_seconds": timeout_seconds,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "") + "\nTIMEOUT",
            }

        _write_json(task_dir / "agent.json", agent_result)

        if not submission_path.exists():
            score = {
                "task_id": task["id"],
                "passed": False,
                "score": 0,
                "reason": "agent did not write submission file",
            }
        else:
            try:
                score = score_submission(task, load_json(submission_path))
            except Exception as exc:  # noqa: BLE001 - runner must preserve per-task failure evidence.
                score = {
                    "task_id": task["id"],
                    "passed": False,
                    "score": 0,
                    "reason": f"scoring failed: {exc}",
                }

        _write_json(task_dir / "score.json", score)
        _write_json(task_dir / "transcript.json", {"task_id": task["id"], "entries": score.get("transcript", [])})
        task_results.append(
            {
                "task_id": task["id"],
                "task_path": str(task_path),
                "expected_vulnerable": bool(task.get("expected_vulnerable")),
                "score": score.get("score", 0),
                "passed": bool(score.get("passed")),
                "agent_returncode": agent_result["returncode"],
            }
        )

    vulnerable = [item for item in task_results if item["expected_vulnerable"]]
    controls = [item for item in task_results if not item["expected_vulnerable"]]
    vulnerable_passed = sum(1 for item in vulnerable if item["passed"])
    controls_failed = sum(1 for item in controls if not item["passed"])
    summary = {
        "run_id": run_id,
        "benchmark_version": benchmark_version,
        "benchmark_commit_sha": benchmark_commit_sha,
        "agent_cmd": agent_cmd,
        "agent": agent,
        "model": model,
        "harness_type": harness_type,
        "timeout_seconds": timeout_seconds,
        "task_count": len(task_results),
        "passed_count": sum(1 for item in task_results if item["passed"]),
        "mean_score": round(sum(float(item["score"]) for item in task_results) / len(task_results), 4)
        if task_results
        else 0,
        "vulnerable_task_count": len(vulnerable),
        "control_task_count": len(controls),
        "exploit_proven_success_rate": round(vulnerable_passed / len(vulnerable), 4) if vulnerable else 0,
        "false_positive_rate": round(controls_failed / len(controls), 4) if controls else 0,
        "tasks": task_results,
    }
    _write_json(run_dir / "summary.json", summary)
    return summary | {"run_dir": str(run_dir)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AuthZBench-SaaS tasks against an agent command.")
    parser.add_argument("--task", action="append", required=True, help="Task manifest glob. Can be repeated.")
    parser.add_argument("--agent-cmd", required=True, help="Command that writes $AUTHZBENCH_SUBMISSION.")
    parser.add_argument("--results-dir", default="results", help="Directory for run artifacts.")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--benchmark-version", default="alpha-0.0.1-public-scaffold-local")
    parser.add_argument("--benchmark-commit-sha", help="Benchmark commit SHA or release archive SHA.")
    parser.add_argument("--agent", help="Agent or harness name to record in summary.json.")
    parser.add_argument("--model", help="Model label to record in summary.json, when applicable.")
    parser.add_argument("--harness-type", help="Harness/tooling category, such as scripted, no-tools, or tool-agent.")
    args = parser.parse_args()

    summary = run_benchmark(
        args.task,
        args.agent_cmd,
        Path(args.results_dir),
        args.timeout_seconds,
        benchmark_version=args.benchmark_version,
        benchmark_commit_sha=args.benchmark_commit_sha,
        agent=args.agent,
        model=args.model,
        harness_type=args.harness_type,
    )
    print(dump_json(summary))
    return 0 if summary["passed_count"] == summary["task_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
