from __future__ import annotations

import argparse
import glob
import json
import os
import shlex
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import benchmark_fingerprint, build_context, dump_json, load_json
from .score import score_submission


BENCHMARK_ROOT = Path(__file__).resolve().parents[1]


def _utc_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(data) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, sort_keys=True) for entry in entries]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = load_json(path)
    except Exception:  # noqa: BLE001 - optional tool artifacts should not invalidate scoring.
        return None
    return data if isinstance(data, dict) else None


def _optional_int(data: dict[str, Any] | None, *keys: str) -> int | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if isinstance(value, int):
            return value
    return None


def _planner_returncode(model_tool_plan: dict[str, Any] | None) -> int | None:
    if not isinstance(model_tool_plan, dict):
        return None
    metadata = model_tool_plan.get("metadata")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("returncode")
    return value if isinstance(value, int) else None


def _planner_parse_error(model_tool_plan: dict[str, Any] | None) -> Any | None:
    if not isinstance(model_tool_plan, dict):
        return None
    metadata = model_tool_plan.get("metadata")
    if not isinstance(metadata, dict):
        return None
    return metadata.get("parse_error")


def _target_log_offset(target_log_dir: Path, app_name: str) -> int:
    log_path = target_log_dir / f"{app_name}.jsonl"
    if not log_path.exists():
        return 0
    return log_path.stat().st_size


def _target_requests(
    target_log_dir: Path,
    app_name: str,
    run_id: str,
    task_id: str,
    agent_id: str,
    start_offset: int,
) -> list[dict[str, Any]]:
    log_path = target_log_dir / f"{app_name}.jsonl"
    if not log_path.exists():
        return []
    entries = []
    with log_path.open("r", encoding="utf-8") as fh:
        fh.seek(start_offset)
        lines = fh.read().splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            entry.get("app") == app_name
            and entry.get("run_id") == run_id
            and entry.get("task_id") == task_id
            and entry.get("agent_id") == agent_id
        ):
            entries.append(entry | {"correlation": {"matched_on": ["run_id", "task_id", "agent_id"], "source_log": str(log_path)}})
    return entries


def _task_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _fingerprint_path(path: Path, root: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return resolved.as_posix()


def _run_agent(
    agent_cmd: str,
    cwd: Path,
    context_path: Path,
    submission_path: Path,
    timeout_seconds: int,
    *,
    run_id: str,
    task_id: str,
    agent_id: str,
) -> dict[str, Any]:
    command = agent_cmd.format(
        context=shlex.quote(str(context_path)),
        submission=shlex.quote(str(submission_path)),
    )
    env = os.environ.copy()
    env.update(
        {
            "AUTHZBENCH_CONTEXT": str(context_path),
            "AUTHZBENCH_SUBMISSION": str(submission_path),
            "AUTHZBENCH_RUN_ID": run_id,
            "AUTHZBENCH_TASK_ID": task_id,
            "AUTHZBENCH_AGENT_ID": agent_id,
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
    score_policy_version: str = "score-policy-v1",
    benchmark_commit_sha: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    harness_type: str | None = None,
    target_log_dir: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id = run_id or _utc_run_id()
    run_dir = results_dir / run_id
    task_results = []
    root = BENCHMARK_ROOT
    loaded_tasks = [(_fingerprint_path(task_path, root), task_path, load_json(task_path)) for task_path in _task_paths(task_patterns)]
    fingerprint = benchmark_fingerprint(
        [(fingerprint_path, task) for fingerprint_path, _task_path, task in loaded_tasks],
        score_policy_version=score_policy_version,
    )

    for _fingerprint_path_text, task_path, task in loaded_tasks:
        task_dir = run_dir / task["id"]
        context_path = task_dir / "context.json"
        submission_path = task_dir / "submission.json"
        _write_json(context_path, build_context(task, score_policy_version=score_policy_version))
        agent_id = agent or Path(shlex.split(agent_cmd)[0]).name
        target_log_start_offset = _target_log_offset(target_log_dir, task["app"]) if target_log_dir is not None else 0

        try:
            agent_result = _run_agent(
                agent_cmd,
                root,
                context_path,
                submission_path,
                timeout_seconds,
                run_id=run_id,
                task_id=task["id"],
                agent_id=agent_id,
            )
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
                "invalid_submission": True,
                "submission_finding_count": 0,
                "control_replay_passed": None,
                "reason": "agent did not write submission file",
            }
        else:
            try:
                score = score_submission(
                    task,
                    load_json(submission_path),
                    score_policy_version=score_policy_version,
                )
            except Exception as exc:  # noqa: BLE001 - runner must preserve per-task failure evidence.
                score = {
                    "task_id": task["id"],
                    "passed": False,
                    "score": 0,
                    "invalid_submission": True,
                    "submission_finding_count": 0,
                    "control_replay_passed": None,
                    "reason": f"scoring failed: {exc}",
                }

        _write_json(task_dir / "score.json", score)
        _write_json(task_dir / "transcript.json", {"task_id": task["id"], "entries": score.get("transcript", [])})
        model_tool_plan = _load_optional_json(task_dir / "model-tool-plan.json")
        tool_probes = _load_optional_json(task_dir / "tool-probes.json")
        model_output = _load_optional_json(task_dir / "model-output.json")
        executed_probe_count = _optional_int(tool_probes, "executed_probe_count", "probe_count")
        fallback_probe_count = _optional_int(tool_probes, "fallback_probe_count")
        submitted_finding_count = _optional_int(tool_probes, "submitted_finding_count")
        planner_returncode = _planner_returncode(model_tool_plan)
        planner_parse_error = _planner_parse_error(model_tool_plan)
        adapter_returncode = _optional_int(model_output, "returncode")
        adapter_parse_error = model_output.get("parse_error") if isinstance(model_output, dict) else None
        model_label_verified = model_output.get("model_label_verified") if isinstance(model_output, dict) else None
        adapter_failed = bool(model_output and (model_output.get("adapter_failed") or adapter_parse_error))
        target_request_count: int | None = None
        target_request_warning: str | None = None
        if target_log_dir is not None:
            target_log_exists = (target_log_dir / f"{task['app']}.jsonl").exists()
            requests = _target_requests(target_log_dir, task["app"], run_id, task["id"], agent_id, target_log_start_offset)
            _write_jsonl(task_dir / "target-requests.jsonl", requests)
            target_request_count = len(requests)
            if not target_log_exists:
                target_request_warning = "target_log_missing"
            elif target_request_count == 0:
                target_request_warning = "no_target_requests_correlated"

        task_results.append(
            {
                "task_id": task["id"],
                "task_path": str(task_path),
                "expected_vulnerable": bool(task.get("expected_vulnerable")),
                "control_type": task.get("control_type") if not task.get("expected_vulnerable") else None,
                "score": score.get("score", 0),
                "passed": bool(score.get("passed")),
                "agent_returncode": agent_result["returncode"],
                "invalid_submission": bool(score.get("invalid_submission")),
                "submission_finding_count": score.get("submission_finding_count", 0),
                "control_replay_passed": score.get("control_replay_passed"),
                "exploit_proof": score.get("subscores", {}).get("exploit_proof", 0),
                "boundary_reasoning": score.get("subscores", {}).get("boundary_reasoning", 0),
                "false_positive_control": score.get("subscores", {}).get("false_positive_control", 0),
                "safety": score.get("subscores", {}).get("safety", 0),
                "model_tool_plan_artifact": model_tool_plan is not None,
                "tool_probe_artifact": tool_probes is not None,
            }
            | (
                {"model_output_artifact": True, "adapter_failed": adapter_failed}
                if model_output is not None
                else {}
            )
            | (
                {"adapter_returncode": adapter_returncode}
                if adapter_returncode is not None
                else {}
            )
            | (
                {"adapter_parse_error": adapter_parse_error}
                if isinstance(adapter_parse_error, str) and adapter_parse_error
                else {}
            )
            | (
                {"model_label_verified": model_label_verified}
                if isinstance(model_label_verified, bool)
                else {}
            )
            | (
                {"executed_probe_count": executed_probe_count}
                if executed_probe_count is not None
                else {}
            )
            | (
                {"fallback_probe_count": fallback_probe_count}
                if fallback_probe_count is not None
                else {}
            )
            | (
                {"submitted_finding_count": submitted_finding_count}
                if submitted_finding_count is not None
                else {}
            )
            | (
                {"planner_returncode": planner_returncode}
                if planner_returncode is not None
                else {}
            )
            | (
                {"planner_parse_error": planner_parse_error}
                if planner_parse_error
                else {}
            )
            | ({"target_request_count": target_request_count} if target_request_count is not None else {})
            | ({"target_request_warning": target_request_warning} if target_request_warning is not None else {})
        )

    vulnerable = [item for item in task_results if item["expected_vulnerable"]]
    controls = [item for item in task_results if not item["expected_vulnerable"]]
    denial_controls = [item for item in controls if item.get("control_type") == "denial"]
    authorized_allow_controls = [item for item in controls if item.get("control_type") == "authorized_allow"]
    vulnerable_passed = sum(1 for item in vulnerable if item["passed"])
    exploit_proven = sum(1 for item in vulnerable if item["exploit_proof"] == 1)
    boundary_reasoning_passed = sum(1 for item in vulnerable if item["boundary_reasoning"] == 1)
    boundary_health_status = (
        "not_applicable"
        if not vulnerable
        else "review_required"
        if exploit_proven > 0 and boundary_reasoning_passed == 0
        else "healthy"
    )
    vulnerable_safety_passed = sum(1 for item in vulnerable if item["safety"] == 1)
    controls_failed = sum(1 for item in controls if not item["passed"])
    controls_with_findings = sum(1 for item in controls if int(item["submission_finding_count"]) > 0)
    control_replay_passed = sum(1 for item in controls if item["control_replay_passed"] is True)
    authorized_allow_passed = sum(1 for item in authorized_allow_controls if item["passed"])
    invalid_submissions = sum(1 for item in task_results if item["invalid_submission"])
    executed_tool_probe_total = sum(int(item.get("executed_probe_count", 0)) for item in task_results)
    fallback_probe_total = sum(int(item.get("fallback_probe_count", 0)) for item in task_results)
    scored_submission_finding_total = 0
    submitted_finding_total = 0
    for task_result in task_results:
        scored_submission_finding_total += int(task_result.get("submission_finding_count", 0))
        submitted_finding_total += int(task_result.get("submitted_finding_count", 0))
    model_tool_plan_artifact_count = sum(1 for item in task_results if item.get("model_tool_plan_artifact"))
    per_task_tool_probe_artifact_count = sum(1 for item in task_results if item.get("tool_probe_artifact"))
    model_output_artifact_count = sum(1 for item in task_results if item.get("model_output_artifact"))
    adapter_failure_count = sum(1 for item in task_results if item.get("adapter_failed"))
    model_label_unverified_count = sum(1 for item in task_results if item.get("model_label_verified") is False)
    planner_parse_error_count = sum(1 for item in task_results if item.get("planner_parse_error"))
    planner_failure_count = sum(
        1
        for item in task_results
        if item.get("model_tool_plan_artifact") and item.get("planner_returncode") not in {None, 0}
    )
    v0_passed_count = sum(
        1
        for item in task_results
        if (
            item["expected_vulnerable"]
            and item["exploit_proof"] == 1
            and item["boundary_reasoning"] == 1
            and item["control_replay_passed"] is True
            and item["safety"] == 1
        )
        or (not item["expected_vulnerable"] and item["passed"])
    )
    target_log_tasks = [item for item in task_results if "target_request_count" in item]
    target_log_correlated = sum(1 for item in target_log_tasks if int(item["target_request_count"]) > 0)
    summary = {
        "run_id": run_id,
        "benchmark_version": benchmark_version,
        "score_policy_version": score_policy_version,
        "benchmark_commit_sha": benchmark_commit_sha,
        "benchmark_fingerprint": fingerprint,
        "agent_cmd": agent_cmd,
        "agent": agent,
        "model": model,
        "harness_type": harness_type,
        "target_log_dir": str(target_log_dir) if target_log_dir is not None else None,
        "timeout_seconds": timeout_seconds,
        "model_tool_plan_artifact_count": model_tool_plan_artifact_count,
        "per_task_tool_probe_artifact_count": per_task_tool_probe_artifact_count,
        "model_output_artifact_count": model_output_artifact_count,
        "adapter_failure_count": adapter_failure_count,
        "adapter_failure_rate": round(adapter_failure_count / model_output_artifact_count, 4)
        if model_output_artifact_count
        else None,
        "model_label_unverified_count": model_label_unverified_count,
        "executed_tool_probe_total": executed_tool_probe_total,
        "fallback_probe_total": fallback_probe_total,
        "scored_submission_finding_total": scored_submission_finding_total,
        "submitted_finding_total": submitted_finding_total,
        "planner_failure_count": planner_failure_count,
        "planner_parse_error_count": planner_parse_error_count,
        "task_count": len(task_results),
        "passed_count": sum(1 for item in task_results if item["passed"]),
        "mean_score": round(sum(float(item["score"]) for item in task_results) / len(task_results), 4)
        if task_results
        else 0,
        "v0_metric_profile": "v0-candidate-authz-evidence",
        "v0_passed_count": v0_passed_count,
        "v0_mean_score": round(v0_passed_count / len(task_results), 4) if task_results else 0,
        "invalid_submission_count": invalid_submissions,
        "invalid_submission_rate": round(invalid_submissions / len(task_results), 4) if task_results else 0,
        "vulnerable_task_count": len(vulnerable),
        "control_task_count": len(controls),
        "denial_control_task_count": len(denial_controls),
        "authorized_allow_control_task_count": len(authorized_allow_controls),
        "exploit_proven_task_count": exploit_proven,
        "exploit_proven_success_rate": round(exploit_proven / len(vulnerable), 4) if vulnerable else 0,
        "vulnerable_full_pass_count": vulnerable_passed,
        "boundary_reasoning_pass_rate": round(boundary_reasoning_passed / len(vulnerable), 4) if vulnerable else 0,
        "boundary_health": {
            "status": boundary_health_status,
            "exploit_proven_task_count": exploit_proven,
            "boundary_reasoning_passed_task_count": boundary_reasoning_passed,
        },
        "vulnerable_safety_pass_rate": round(vulnerable_safety_passed / len(vulnerable), 4) if vulnerable else 0,
        "control_false_report_count": controls_with_findings,
        "control_false_report_rate": round(controls_with_findings / len(controls), 4) if controls else 0,
        "control_execution_pass_rate": round(control_replay_passed / len(controls), 4) if controls else 0,
        "false_positive_rate": round(controls_failed / len(controls), 4) if controls else 0,
        "authorized_allow_pass_rate": round(authorized_allow_passed / len(authorized_allow_controls), 4)
        if authorized_allow_controls
        else 0,
        "target_request_correlated_task_count": target_log_correlated if target_log_tasks else None,
        "target_request_coverage_rate": round(target_log_correlated / len(target_log_tasks), 4) if target_log_tasks else None,
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
    parser.add_argument(
        "--score-policy-version",
        choices=("score-policy-v1", "score-policy-v2"),
        default="score-policy-v1",
        help="Named scoring policy for the run and benchmark fingerprint.",
    )
    parser.add_argument("--benchmark-commit-sha", help="Benchmark commit SHA or release archive SHA.")
    parser.add_argument("--agent", help="Agent or harness name to record in summary.json.")
    parser.add_argument("--model", help="Model label to record in summary.json, when applicable.")
    parser.add_argument("--harness-type", help="Harness/tooling category, such as scripted, no-tools, or tool-agent.")
    parser.add_argument("--target-log-dir", help="Directory containing target-side <app>.jsonl logs to correlate per task.")
    args = parser.parse_args()

    summary = run_benchmark(
        args.task,
        args.agent_cmd,
        Path(args.results_dir),
        args.timeout_seconds,
        benchmark_version=args.benchmark_version,
        score_policy_version=args.score_policy_version,
        benchmark_commit_sha=args.benchmark_commit_sha,
        agent=args.agent,
        model=args.model,
        harness_type=args.harness_type,
        target_log_dir=Path(args.target_log_dir).resolve() if args.target_log_dir else None,
    )
    print(dump_json(summary))
    return 0 if summary["passed_count"] == summary["task_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
