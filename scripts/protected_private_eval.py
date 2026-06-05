from __future__ import annotations

import argparse
import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import build_context, dump_json, load_json
from authzbench.score import score_submission


def _utc_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(data) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, sort_keys=True) for entry in entries]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


def _task_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _git_ls_files(pathspec: str) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", pathspec],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


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
    entries: list[dict[str, Any]] = []
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


def _target_requests_after_settle(
    target_log_dir: Path,
    app_name: str,
    run_id: str,
    task_id: str,
    agent_id: str,
    start_offset: int,
) -> list[dict[str, Any]]:
    for attempt in range(6):
        entries = _target_requests(target_log_dir, app_name, run_id, task_id, agent_id, start_offset)
        if entries or attempt == 5:
            return entries
        time.sleep(0.1)
    return []


def _run_agent_protected(
    agent_cmd: str,
    context: dict[str, Any],
    timeout_seconds: int,
    *,
    run_id: str,
    task_id: str,
    agent_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="authzbench-protected-agent.") as tmp:
        temp_root = Path(tmp)
        agent_workspace = temp_root / "agent-workspace"
        agent_workspace.mkdir()
        context_path = temp_root / "context.json"
        submission_path = temp_root / "submission.json"
        _write_json(context_path, context)

        command = agent_cmd.format(
            context=shlex.quote(str(context_path)),
            submission=shlex.quote(str(submission_path)),
        )
        env = os.environ.copy()
        env.pop("AUTHZBENCH_TARGET_LOG_DIR", None)
        env.pop("AUTHZBENCH_REQUEST_LOG_DIR", None)
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
        try:
            completed = subprocess.run(
                shlex.split(command),
                cwd=agent_workspace,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            agent_result = {
                "command": command,
                "returncode": completed.returncode,
                "duration_seconds": round(time.time() - started, 4),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            agent_result = {
                "command": agent_cmd,
                "returncode": None,
                "duration_seconds": timeout_seconds,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "") + "\nTIMEOUT",
            }

        submission = load_json(submission_path) if submission_path.exists() else {"findings": []}
        copied_artifacts: dict[str, Any] = {}
        for artifact_name in ("submission.json", "model-output.json", "model-tool-plan.json", "tool-probes.json"):
            artifact_path = temp_root / artifact_name
            if artifact_path.exists():
                copied_artifacts[artifact_name] = load_json(artifact_path)
        protection = {
            "agent_workspace_empty_at_start": True,
            "agent_cwd": "temporary-empty-workspace",
            "context_location": "temporary-rendered-context",
            "private_manifest_location": "not-in-agent-workspace",
            "private_task_manifest_exposed_to_agent": False,
        }
        return agent_result, submission, {"artifacts": copied_artifacts, "protection": protection}


def _metric_summary(
    task_results: list[dict[str, Any]],
    *,
    run_id: str,
    benchmark_version: str,
    benchmark_commit_sha: str | None,
    agent: str | None,
    model: str | None,
    harness_type: str | None,
) -> dict[str, Any]:
    vulnerable = [item for item in task_results if item["expected_vulnerable"]]
    controls = [item for item in task_results if not item["expected_vulnerable"]]
    denial_controls = [item for item in controls if item.get("control_type") == "denial"]
    authorized_allow_controls = [item for item in controls if item.get("control_type") == "authorized_allow"]
    invalid_submissions = sum(1 for item in task_results if item["invalid_submission"])
    exploit_proven = sum(1 for item in vulnerable if item["exploit_proof"] == 1)
    vulnerable_full_passed = sum(
        1
        for item in vulnerable
        if item["exploit_proof"] == 1
        and item["boundary_reasoning"] == 1
        and item["control_replay_passed"] is True
        and item["safety"] == 1
    )
    control_replay_passed = sum(1 for item in controls if item["control_replay_passed"] is True)
    controls_with_findings = sum(1 for item in controls if int(item["submission_finding_count"]) > 0)
    authorized_allow_passed = sum(1 for item in authorized_allow_controls if item["passed"])
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
    task_count = len(task_results)
    vulnerable_count = len(vulnerable)
    control_count = len(controls)
    executed_probe_count = sum(int(item.get("executed_probe_count", 0)) for item in task_results)
    fallback_probe_count = sum(int(item.get("fallback_probe_count", 0)) for item in task_results)
    model_tool_plan_artifact_count = sum(1 for item in task_results if item.get("model_tool_plan_artifact"))
    per_task_tool_probe_artifact_count = sum(1 for item in task_results if item.get("tool_probe_artifact"))
    return {
        "agent": agent,
        "authorized_allow_control_task_count": len(authorized_allow_controls),
        "authorized_allow_pass_rate": round(authorized_allow_passed / len(authorized_allow_controls), 4)
        if authorized_allow_controls
        else None,
        "benchmark_commit_sha": benchmark_commit_sha,
        "benchmark_version": benchmark_version,
        "boundary_reasoning_pass_rate": round(
            sum(1 for item in vulnerable if item["boundary_reasoning"] == 1) / vulnerable_count, 4
        )
        if vulnerable_count
        else None,
        "control_execution_pass_rate": round(control_replay_passed / control_count, 4) if control_count else None,
        "control_false_report_count": controls_with_findings,
        "control_false_report_rate": round(controls_with_findings / control_count, 4) if control_count else None,
        "control_task_count": control_count,
        "denial_control_task_count": len(denial_controls),
        "executed_probe_count": executed_probe_count,
        "exploit_proven_success_rate": round(exploit_proven / vulnerable_count, 4) if vulnerable_count else None,
        "exploit_proven_task_count": exploit_proven,
        "fallback_probe_count": fallback_probe_count,
        "false_positive_rate": round(controls_with_findings / control_count, 4) if control_count else None,
        "harness_type": harness_type,
        "invalid_submission_count": invalid_submissions,
        "invalid_submission_rate": round(invalid_submissions / task_count, 4) if task_count else None,
        "mean_score": round(sum(float(item["score"]) for item in task_results) / task_count, 4) if task_count else 0,
        "model": model,
        "model_tool_plan_artifact_count": model_tool_plan_artifact_count,
        "passed_count": sum(1 for item in task_results if item["passed"]),
        "per_task_tool_probe_artifact_count": per_task_tool_probe_artifact_count,
        "protected_execution": {
            "agent_cwd": "temporary-empty-workspace",
            "agent_received": "rendered-context-only",
            "private_manifests_readable_in_agent_workspace": False,
            "raw_result_bundle_tracked": bool(_git_ls_files("results")),
            "tracked_private_manifest_count": len(_git_ls_files("tasks_private/holdout")),
        },
        "run_id": run_id,
        "split": "private-holdout",
        "target_request_coverage_rate": None,
        "task_count": task_count,
        "tasks": task_results,
        "v0_mean_score": round(v0_passed_count / task_count, 4) if task_count else 0,
        "v0_metric_profile": "v0-candidate-authz-evidence",
        "v0_passed_count": v0_passed_count,
        "vulnerable_full_pass_count": vulnerable_full_passed,
        "vulnerable_task_count": vulnerable_count,
    }


def redacted_summary(summary: dict[str, Any]) -> dict[str, Any]:
    protected = summary.get("protected_execution") if isinstance(summary.get("protected_execution"), dict) else {}
    return {
        "agent": summary.get("agent"),
        "authorized_allow_control_task_count": summary.get("authorized_allow_control_task_count"),
        "authorized_allow_pass_rate": summary.get("authorized_allow_pass_rate"),
        "benchmark_commit_sha": summary.get("benchmark_commit_sha"),
        "benchmark_version": summary.get("benchmark_version"),
        "boundary_reasoning_pass_rate": summary.get("boundary_reasoning_pass_rate"),
        "control_execution_pass_rate": summary.get("control_execution_pass_rate"),
        "control_false_report_count": summary.get("control_false_report_count"),
        "control_false_report_rate": summary.get("control_false_report_rate"),
        "control_task_count": summary.get("control_task_count"),
        "denial_control_task_count": summary.get("denial_control_task_count"),
        "executed_probe_count": summary.get("executed_probe_count"),
        "exploit_proven_success_rate": summary.get("exploit_proven_success_rate"),
        "exploit_proven_task_count": summary.get("exploit_proven_task_count"),
        "fallback_probe_count": summary.get("fallback_probe_count"),
        "false_positive_rate": summary.get("false_positive_rate"),
        "full_result_bundle_tracked": bool(protected.get("raw_result_bundle_tracked")),
        "harness_type": summary.get("harness_type"),
        "invalid_submission_count": summary.get("invalid_submission_count"),
        "invalid_submission_rate": summary.get("invalid_submission_rate"),
        "mean_score": summary.get("mean_score"),
        "model": summary.get("model"),
        "model_tool_plan_artifact_count": summary.get("model_tool_plan_artifact_count"),
        "per_task_tool_probe_artifact_count": summary.get("per_task_tool_probe_artifact_count"),
        "private_holdout_task_count": summary.get("task_count"),
        "protected_execution": {
            "agent_cwd": protected.get("agent_cwd"),
            "agent_received": protected.get("agent_received"),
            "private_manifests_readable_in_agent_workspace": protected.get(
                "private_manifests_readable_in_agent_workspace"
            ),
            "tracked_private_manifest_count": protected.get("tracked_private_manifest_count"),
        },
        "public_task_count": 0,
        "raw_private_artifacts_tracked": bool(protected.get("raw_result_bundle_tracked")),
        "redacted_private_holdout_source": True,
        "run_count": 1,
        "run_id": str(summary.get("run_id", "")) + "-redacted",
        "safety_violations": 0,
        "split": "private-holdout",
        "target_request_correlated_task_count": summary.get("target_request_correlated_task_count"),
        "target_request_coverage_rate": summary.get("target_request_coverage_rate"),
        "task_count": summary.get("task_count"),
        "tracked_private_manifest_count": protected.get("tracked_private_manifest_count"),
        "v0_mean_score": summary.get("v0_mean_score"),
        "v0_metric_profile": summary.get("v0_metric_profile"),
        "v0_passed_count": summary.get("v0_passed_count"),
        "vulnerable_full_pass_count": summary.get("vulnerable_full_pass_count"),
        "vulnerable_task_count": summary.get("vulnerable_task_count"),
    }


def run_protected_private_eval(
    task_patterns: list[str],
    *,
    agent_cmd: str,
    results_dir: Path,
    timeout_seconds: int,
    benchmark_version: str,
    benchmark_commit_sha: str | None,
    agent: str | None,
    model: str | None,
    harness_type: str | None,
    target_log_dir: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id = run_id or _utc_run_id()
    run_dir = results_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    task_results: list[dict[str, Any]] = []

    for task_path in _task_paths(task_patterns):
        task = load_json(task_path)
        if task.get("split") != "private_holdout":
            raise ValueError("protected private evaluation only accepts split=private_holdout manifests")
        task_dir = run_dir / task["id"]
        context = build_context(task)
        agent_id = agent or Path(shlex.split(agent_cmd)[0]).name
        target_log_start_offset = _target_log_offset(target_log_dir, task["app"]) if target_log_dir is not None else 0
        agent_result, submission, protected_artifacts = _run_agent_protected(
            agent_cmd,
            context,
            timeout_seconds,
            run_id=run_id,
            task_id=task["id"],
            agent_id=agent_id,
        )
        _write_json(task_dir / "agent.json", agent_result)
        _write_json(task_dir / "submission.json", submission)
        _write_json(task_dir / "protected-artifacts.json", protected_artifacts)
        for artifact_name, artifact_data in protected_artifacts["artifacts"].items():
            _write_json(task_dir / artifact_name, artifact_data)
        tool_probe_data = protected_artifacts["artifacts"].get("tool-probes.json")
        if not isinstance(tool_probe_data, dict):
            tool_probe_data = {}

        try:
            score = score_submission(task, submission)
        except Exception as exc:  # noqa: BLE001 - preserve per-task failure evidence.
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
        target_request_count: int | None = None
        target_request_warning: str | None = None
        if target_log_dir is not None:
            target_log_exists = (target_log_dir / f"{task['app']}.jsonl").exists()
            requests = _target_requests_after_settle(
                target_log_dir,
                task["app"],
                run_id,
                task["id"],
                agent_id,
                target_log_start_offset,
            )
            _write_jsonl(task_dir / "target-requests.jsonl", requests)
            target_request_count = len(requests)
            if not target_log_exists:
                target_request_warning = "target_log_missing"
            elif target_request_count == 0:
                target_request_warning = "no_target_requests_correlated"
        task_results.append(
            {
                "agent_returncode": agent_result["returncode"],
                "boundary_reasoning": score.get("subscores", {}).get("boundary_reasoning", 0),
                "control_replay_passed": score.get("control_replay_passed"),
                "control_type": task.get("control_type") if not task.get("expected_vulnerable") else None,
                "expected_vulnerable": bool(task.get("expected_vulnerable")),
                "executed_probe_count": int(tool_probe_data.get("executed_probe_count", 0)),
                "exploit_proof": score.get("subscores", {}).get("exploit_proof", 0),
                "fallback_probe_count": int(tool_probe_data.get("fallback_probe_count", 0)),
                "false_positive_control": score.get("subscores", {}).get("false_positive_control", 0),
                "invalid_submission": bool(score.get("invalid_submission")),
                "model_tool_plan_artifact": "model-tool-plan.json" in protected_artifacts["artifacts"],
                "passed": bool(score.get("passed")),
                "safety": score.get("subscores", {}).get("safety", 0),
                "score": score.get("score", 0),
                "submission_finding_count": score.get("submission_finding_count", 0),
                "task_id": task["id"],
                "tool_probe_artifact": "tool-probes.json" in protected_artifacts["artifacts"],
            }
            | ({"target_request_count": target_request_count} if target_request_count is not None else {})
            | ({"target_request_warning": target_request_warning} if target_request_warning else {})
        )

    summary = _metric_summary(
        task_results,
        run_id=run_id,
        benchmark_version=benchmark_version,
        benchmark_commit_sha=benchmark_commit_sha,
        agent=agent,
        model=model,
        harness_type=harness_type,
    )
    if target_log_dir is not None:
        target_log_tasks = [item for item in task_results if "target_request_count" in item]
        target_log_correlated = sum(1 for item in target_log_tasks if int(item["target_request_count"]) > 0)
        summary["target_log_dir"] = str(target_log_dir)
        summary["target_request_correlated_task_count"] = target_log_correlated
        summary["target_request_coverage_rate"] = round(target_log_correlated / len(target_log_tasks), 4) if target_log_tasks else None
    _write_json(run_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run private holdouts without exposing manifests to agent cwd.")
    parser.add_argument("--task", action="append", default=["tasks_private/holdout/**/*.json"])
    parser.add_argument("--agent-cmd", required=True)
    parser.add_argument("--results-dir", default="results/protected-private-eval")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--benchmark-version", default="alpha-0.0.1-public-scaffold-local")
    parser.add_argument("--benchmark-commit-sha")
    parser.add_argument("--agent")
    parser.add_argument("--model")
    parser.add_argument("--harness-type")
    parser.add_argument("--target-log-dir", help="Directory containing target-side <app>.jsonl logs to correlate per task.")
    parser.add_argument("--run-id")
    parser.add_argument("--redacted-summary-output")
    args = parser.parse_args()

    summary = run_protected_private_eval(
        args.task,
        agent_cmd=args.agent_cmd,
        results_dir=Path(args.results_dir),
        timeout_seconds=args.timeout_seconds,
        benchmark_version=args.benchmark_version,
        benchmark_commit_sha=args.benchmark_commit_sha,
        agent=args.agent,
        model=args.model,
        harness_type=args.harness_type,
        target_log_dir=Path(args.target_log_dir).resolve() if args.target_log_dir else None,
        run_id=args.run_id,
    )
    if args.redacted_summary_output:
        output = Path(args.redacted_summary_output)
        _write_json(output, redacted_summary(summary))
    print(dump_json(redacted_summary(summary)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
