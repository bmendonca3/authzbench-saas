from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shlex
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from .core import (
    benchmark_fingerprint,
    build_context,
    dump_json,
    is_safe_identifier,
    load_json,
    replay_request,
    resolve_templates,
    stable_json_sha256,
)
from .run import (
    BENCHMARK_ROOT,
    _adapter_failure_type,
    _fingerprint_path,
    _invalid_runner_score,
    _load_adapter_output,
    _load_optional_json,
    _optional_int,
    _planner_parse_error,
    _planner_returncode,
    _run_agent,
    _subprocess_text,
    _target_log_offset,
    _target_requests,
    _task_paths,
    _utc_run_id,
    _write_json,
    _write_jsonl,
    summarize_task_results,
)
from .score import (
    _control_matches,
    _request_requirement_matches,
    _submission_request_error,
    score_submission,
)


PROTOCOL_VERSION = "blinded-control-evidence-v1"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _opaque_case_id(run_id: str, task_id: str) -> str:
    digest = hashlib.sha256(f"{run_id}:{task_id}".encode("utf-8")).hexdigest()[:16]
    return f"case-{digest}"


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> dict[str, Any] | None:
    if total <= 0:
        return None
    proportion = successes / total
    denominator = 1 + (z * z / total)
    center = (proportion + (z * z / (2 * total))) / denominator
    margin = (
        z
        * math.sqrt((proportion * (1 - proportion) / total) + (z * z / (4 * total * total)))
        / denominator
    )
    return {
        "method": "wilson",
        "confidence_level": 0.95,
        "lower": round(max(0.0, center - margin), 4),
        "upper": round(min(1.0, center + margin), 4),
    }


def _git_provenance(root: Path, source_paths: dict[str, Path]) -> dict[str, Any]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    head = run("rev-parse", "HEAD")
    status = run("status", "--porcelain=v1", "--untracked-files=no")
    root_resolved = root.resolve()
    tracked_source_paths = []
    for path in source_paths.values():
        try:
            tracked_source_paths.append(path.resolve().relative_to(root_resolved).as_posix())
        except ValueError:
            continue
    diff = run("diff", "--binary", "HEAD", "--", *sorted(set(tracked_source_paths)))
    return {
        "git_commit_sha": head.stdout.strip() if head.returncode == 0 else None,
        "tracked_worktree_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        "tracked_diff_sha256": (
            hashlib.sha256(diff.stdout.encode("utf-8")).hexdigest()
            if diff.returncode == 0
            else None
        ),
    }


def _resolve_agent_source_paths(agent_source_paths: list[Path | str] | None) -> list[Path]:
    if not agent_source_paths:
        raise ValueError("at least one agent source path is required for evaluation provenance")
    resolved_paths = sorted(
        {Path(path).expanduser().resolve() for path in agent_source_paths},
        key=lambda path: path.as_posix(),
    )
    for path in resolved_paths:
        if not path.is_file():
            raise ValueError(f"agent source path must be a readable file: {path}")
    return resolved_paths


def _protocol_source_paths(agent_source_paths: list[Path | str] | None) -> dict[str, Path]:
    source_paths = {
        "core": BENCHMARK_ROOT / "authzbench/core.py",
        "legacy_runner": BENCHMARK_ROOT / "authzbench/run.py",
        "scorer": BENCHMARK_ROOT / "authzbench/score.py",
        "evaluation_runner": Path(__file__).resolve(),
    }
    app_root = BENCHMARK_ROOT / "apps"
    for path in sorted(app_root.rglob("*.py")):
        source_paths[f"app:{path.relative_to(BENCHMARK_ROOT).as_posix()}"] = path
    for index, path in enumerate(_resolve_agent_source_paths(agent_source_paths), start=1):
        source_paths[f"agent_source_{index}"] = path
    return source_paths


def _protocol_manifest(source_paths: dict[str, Path]) -> dict[str, Any]:
    source_hashes = {name: _file_sha256(path) for name, path in source_paths.items()}
    manifest: dict[str, Any] = {
        "schema_version": "authzbench-evaluation-protocol-manifest-v1",
        "protocol_version": PROTOCOL_VERSION,
        "participant_context_profile": "blinded-evaluation-v1",
        "participant_task_id_mode": "opaque-per-run",
        "candidate_evidence_mode": "host-replayed-bounded-requests",
        "agent_workdir_mode": "isolated-per-task-artifact-directory",
        "control_verification_required": True,
        "completed_run_exit_policy": "zero_without_infrastructure_failures",
        "filesystem_isolation_boundary": (
            "Working-directory isolation only; this is not an operating-system sandbox. "
            "Use a container or equivalent sandbox for filesystem-capable untrusted agents."
        ),
        "source_sha256": source_hashes,
        "source_set_sha256": stable_json_sha256(source_hashes),
    }
    manifest["manifest_sha256"] = stable_json_sha256(manifest)
    return manifest


def _verified_benchmark_commit_sha(
    git_provenance: dict[str, Any], benchmark_commit_sha: str | None
) -> str:
    observed_commit_sha = git_provenance.get("git_commit_sha")
    if not isinstance(observed_commit_sha, str) or not observed_commit_sha:
        raise ValueError("unable to resolve Git HEAD for benchmark provenance")
    if benchmark_commit_sha is not None and benchmark_commit_sha != observed_commit_sha:
        raise ValueError("benchmark_commit_sha must exactly match the observed Git HEAD")
    return observed_commit_sha


def _evaluate_control_verification(
    task: dict[str, Any],
    submission: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    score["control_verification_required"] = task.get("expected_vulnerable") is False
    score["control_verification_present"] = False
    score["control_verification_passed"] = None
    if task.get("expected_vulnerable") is not False:
        return score

    verification = submission.get("verification")
    verification_passed = False
    if not isinstance(verification, list) or not verification:
        score["observations"].append(
            "participant verification evidence is required for secure-control credit"
        )
    else:
        score["control_verification_present"] = True
        refs = build_context(task)["refs"]
        controls = resolve_templates(task.get("controls", []), refs)
        oracle = resolve_templates(task["oracle"], refs)
        for index, item in enumerate(verification):
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("request"), dict)
                or not isinstance(item.get("expected"), dict)
                or not isinstance(item["expected"].get("status"), int)
                or isinstance(item["expected"].get("status"), bool)
            ):
                score["invalid_submission"] = True
                score["observations"].append(
                    f"malformed control verification item at index {index}; request and integer expected.status are required"
                )
                continue
            request = resolve_templates(item["request"], refs)
            request_error = _submission_request_error(request)
            if request_error is not None:
                score["invalid_submission"] = True
                score["observations"].append(
                    f"malformed control verification request at index {index}: {request_error}"
                )
                continue
            matching_controls = []
            for control in controls:
                expected_request = {
                    key: control[key]
                    for key in ("actor", "method", "path", "body")
                    if key in control
                }
                if _request_requirement_matches(request, {"request": expected_request}):
                    matching_controls.append(control)
            if not matching_controls:
                score["observations"].append(
                    f"control verification request at index {index} did not match a declared control"
                )
                continue

            response = replay_request(task, request)
            score["transcript"].append(
                {
                    "name": f"participant_control_verification_{index + 1}",
                    "request": request,
                    "response": response,
                }
            )
            if response.get("status") != item["expected"]["status"]:
                score["observations"].append(
                    f"control verification prediction at index {index} did not match replayed status"
                )
                continue
            for control in matching_controls:
                expected_body = control.get("body_contains", oracle.get("body_contains"))
                if _control_matches(response, control, expected_body):
                    verification_passed = True
                    break
            if verification_passed:
                break

    score["control_verification_passed"] = verification_passed
    if not verification_passed or score["invalid_submission"]:
        score["passed"] = False
        score["score"] = 0
        score["subscores"] = {
            "exploit_proof": 0,
            "boundary_reasoning": 0,
            "false_positive_control": 0,
            "safety": 0 if score["invalid_submission"] else 1,
        }
        score["reason"] = "participant control verification was missing, malformed, or did not match a control"
    return score


def summarize_evaluation_results(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_task_results(task_results)
    vulnerable = [item for item in task_results if item["expected_vulnerable"]]
    controls = [item for item in task_results if not item["expected_vulnerable"]]
    vulnerable_passed = sum(1 for item in vulnerable if item["passed"])
    controls_passed = sum(1 for item in controls if item["passed"])
    controls_with_findings = sum(
        1 for item in controls if int(item.get("submission_finding_count", 0)) > 0
    )
    control_verification_passed = sum(
        1 for item in controls if item.get("control_verification_passed") is True
    )
    vulnerable_rate = round(vulnerable_passed / len(vulnerable), 4) if vulnerable else 0
    control_rate = round(controls_passed / len(controls), 4) if controls else 0
    false_positive_rate = round(controls_with_findings / len(controls), 4) if controls else 0
    output_formats = Counter(
        str(item["adapter_output_format"])
        for item in task_results
        if item.get("adapter_output_format")
    )
    json_compliant = sum(
        1 for item in task_results if item.get("adapter_json_only_compliant") is True
    )
    infrastructure_failures = int(summary["infrastructure_failure_count"])
    summary.update(
        {
            "benchmark_execution_status": (
                "completed_with_infrastructure_failures"
                if infrastructure_failures
                else "completed"
            ),
            "task_completion_count": len(task_results),
            "vulnerable_full_pass_rate": vulnerable_rate,
            "vulnerable_full_pass_rate_interval_95": _wilson_interval(
                vulnerable_passed, len(vulnerable)
            ),
            "secure_control_pass_rate": control_rate,
            "secure_control_pass_rate_interval_95": _wilson_interval(
                controls_passed, len(controls)
            ),
            "false_positive_rate_interval_95": _wilson_interval(
                controls_with_findings, len(controls)
            ),
            "control_verification_required_count": len(controls),
            "control_verification_passed_count": control_verification_passed,
            "control_verification_pass_rate": (
                round(control_verification_passed / len(controls), 4) if controls else 0
            ),
            "authorization_balanced_accuracy": (
                round((vulnerable_rate + control_rate) / 2, 4)
                if vulnerable and controls
                else None
            ),
            "authz_discrimination_index": (
                round(vulnerable_rate - false_positive_rate, 4)
                if vulnerable and controls
                else None
            ),
            "calibration_metric_profile": "authz-discrimination-v1",
            "adapter_output_format_counts": dict(sorted(output_formats.items())),
            "adapter_json_only_compliant_count": json_compliant,
            "adapter_json_only_compliance_rate": (
                round(json_compliant / sum(output_formats.values()), 4)
                if output_formats
                else None
            ),
        }
    )
    return summary


def run_evaluation(
    task_patterns: list[str],
    agent_cmd: str,
    results_dir: Path,
    timeout_seconds: int,
    *,
    benchmark_version: str = "alpha-0.0.1-public-scaffold-local",
    benchmark_commit_sha: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    harness_type: str | None = None,
    target_log_dir: Path | None = None,
    run_id: str | None = None,
    agent_source_paths: list[Path | str] | None = None,
) -> dict[str, Any]:
    run_id = run_id or _utc_run_id()
    if not is_safe_identifier(run_id):
        raise ValueError("run_id must be a safe single path component")
    results_dir = results_dir.resolve()
    run_dir = results_dir / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty benchmark run directory: {run_dir}")

    root = BENCHMARK_ROOT
    task_paths = _task_paths(task_patterns)
    if not task_paths:
        raise ValueError("no task manifests matched")
    loaded_tasks = [
        (_fingerprint_path(path, root), path, load_json(path)) for path in task_paths
    ]
    seen_task_ids: set[str] = set()
    for _fingerprint_path_text, task_path, task in loaded_tasks:
        if not isinstance(task, dict) or not is_safe_identifier(task.get("id")):
            raise ValueError(f"{task_path}: task id must be a safe single path component")
        if task["id"] in seen_task_ids:
            raise ValueError(f"duplicate task id in benchmark run: {task['id']}")
        seen_task_ids.add(task["id"])
    fingerprint = benchmark_fingerprint(
        [(path_text, task) for path_text, _task_path, task in loaded_tasks]
    )
    source_paths = _protocol_source_paths(agent_source_paths)
    protocol = _protocol_manifest(source_paths)
    git_provenance = _git_provenance(root, source_paths)
    resolved_benchmark_commit_sha = _verified_benchmark_commit_sha(
        git_provenance, benchmark_commit_sha
    )
    task_results: list[dict[str, Any]] = []

    for _fingerprint_path_text, task_path, task in loaded_tasks:
        participant_case_id = _opaque_case_id(run_id, task["id"])
        task_dir = run_dir / participant_case_id
        context_path = task_dir / "context.json"
        submission_path = task_dir / "submission.json"
        participant_context = build_context(
            task,
            participant_task_id=participant_case_id,
            profile="blinded-evaluation-v1",
        )
        participant_context["candidate_observations"] = [
            {
                "request": request,
                "response": replay_request(task, request),
            }
            for request in participant_context["candidate_requests"]
        ]
        _write_json(
            context_path,
            participant_context,
        )
        agent_id = agent or Path(shlex.split(agent_cmd)[0]).name
        target_log_start_offset = (
            _target_log_offset(target_log_dir, task["app"])
            if target_log_dir is not None
            else 0
        )
        try:
            agent_result = _run_agent(
                agent_cmd,
                task_dir,
                context_path,
                submission_path,
                timeout_seconds,
                run_id=run_id,
                task_id=participant_case_id,
                agent_id=agent_id,
            )
        except subprocess.TimeoutExpired as exc:
            agent_result = {
                "command": agent_cmd,
                "returncode": None,
                "duration_seconds": timeout_seconds,
                "stdout": _subprocess_text(exc.stdout),
                "stderr": _subprocess_text(exc.stderr) + "\nTIMEOUT",
            }
        _write_json(task_dir / "agent.json", agent_result)

        model_output = _load_adapter_output(task_dir / "model-output.json")
        adapter_failure_type = _adapter_failure_type(model_output)
        submission: dict[str, Any] | None = None
        if adapter_failure_type is not None:
            score = _invalid_runner_score(task, f"adapter failure: {adapter_failure_type}")
        elif agent_result["returncode"] != 0:
            reason = (
                "agent command timed out"
                if agent_result["returncode"] is None
                else f"agent command failed with return code {agent_result['returncode']}"
            )
            score = _invalid_runner_score(task, reason)
        elif not submission_path.exists():
            score = _invalid_runner_score(task, "agent did not write submission file")
        else:
            try:
                submission = load_json(submission_path)
                score = score_submission(task, submission)
                score = _evaluate_control_verification(task, submission, score)
            except Exception as exc:  # noqa: BLE001 - preserve task-level failure evidence.
                score = _invalid_runner_score(
                    task,
                    f"scoring failed: {type(exc).__name__}: {exc}",
                )

        _write_json(task_dir / "score.json", score)
        _write_json(
            task_dir / "transcript.json",
            {"task_id": task["id"], "entries": score.get("transcript", [])},
        )
        runner_agent_failure = agent_result["returncode"] != 0
        infrastructure_failure = (
            adapter_failure_type != "output_parse_failure"
            if adapter_failure_type is not None
            else runner_agent_failure
        )
        model_tool_plan = _load_optional_json(task_dir / "model-tool-plan.json")
        tool_probes = _load_optional_json(task_dir / "tool-probes.json")
        executed_probe_count = _optional_int(
            tool_probes, "executed_probe_count", "probe_count"
        )
        fallback_probe_count = _optional_int(tool_probes, "fallback_probe_count")
        submitted_finding_count = _optional_int(tool_probes, "submitted_finding_count")
        planner_returncode = _planner_returncode(model_tool_plan)
        planner_parse_error = _planner_parse_error(model_tool_plan)
        target_request_count: int | None = None
        target_request_warning: str | None = None
        if target_log_dir is not None:
            target_log_exists = (target_log_dir / f"{task['app']}.jsonl").exists()
            requests = _target_requests(
                target_log_dir,
                task["app"],
                run_id,
                participant_case_id,
                agent_id,
                target_log_start_offset,
            )
            _write_jsonl(task_dir / "target-requests.jsonl", requests)
            target_request_count = len(requests)
            if not target_log_exists:
                target_request_warning = "target_log_missing"
            elif target_request_count == 0:
                target_request_warning = "no_target_requests_correlated"

        row: dict[str, Any] = {
            "task_id": task["id"],
            "participant_case_id": participant_case_id,
            "task_path": str(task_path),
            "expected_vulnerable": bool(task.get("expected_vulnerable")),
            "control_type": (
                task.get("control_type") if not task.get("expected_vulnerable") else None
            ),
            "score": score.get("score", 0),
            "passed": bool(score.get("passed")),
            "agent_returncode": agent_result["returncode"],
            "invalid_submission": bool(score.get("invalid_submission")),
            "submission_finding_count": score.get("submission_finding_count", 0),
            "control_replay_passed": score.get("control_replay_passed"),
            "control_verification_required": bool(
                score.get("control_verification_required")
            ),
            "control_verification_present": bool(score.get("control_verification_present")),
            "control_verification_passed": score.get("control_verification_passed"),
            "exploit_proof": score.get("subscores", {}).get("exploit_proof", 0),
            "boundary_reasoning": score.get("subscores", {}).get("boundary_reasoning", 0),
            "claim_exact_match": bool(score.get("claim_exact_match")),
            "boundary_exact_match": bool(score.get("boundary_exact_match")),
            "boundary_semantic_match": bool(score.get("boundary_semantic_match")),
            "boundary_partial_match": bool(score.get("boundary_partial_match")),
            "boundary_match_mode": score.get("boundary_match_mode", "not_evaluated"),
            "boundary_field_match_rate": score.get("boundary_field_match_rate", 0),
            "false_positive_control": score.get("subscores", {}).get(
                "false_positive_control", 0
            ),
            "safety": score.get("subscores", {}).get("safety", 0),
            "adapter_failure_type": adapter_failure_type,
            "runner_agent_failure": runner_agent_failure,
            "infrastructure_failure": infrastructure_failure,
            "model_tool_plan_artifact": model_tool_plan is not None,
            "tool_probe_artifact": tool_probes is not None,
        }
        optional_values = {
            "executed_probe_count": executed_probe_count,
            "fallback_probe_count": fallback_probe_count,
            "submitted_finding_count": submitted_finding_count,
            "planner_returncode": planner_returncode,
            "planner_parse_error": planner_parse_error,
            "target_request_count": target_request_count,
            "target_request_warning": target_request_warning,
        }
        if isinstance(model_output, dict):
            optional_values.update(
                {
                    "adapter_output_format": model_output.get("output_format"),
                    "adapter_json_only_compliant": model_output.get(
                        "json_only_compliant"
                    ),
                    "adapter_cli_version": model_output.get("kiro_cli_version"),
                    "adapter_requested_model": model_output.get("requested_model"),
                    "adapter_requested_effort": model_output.get("requested_effort"),
                    "adapter_prompt_sha256": model_output.get("prompt_sha256"),
                }
            )
        row.update({key: value for key, value in optional_values.items() if value is not None})
        task_results.append(row)

    summary = {
        "run_id": run_id,
        "benchmark_version": benchmark_version,
        "benchmark_commit_sha": resolved_benchmark_commit_sha,
        "benchmark_fingerprint": fingerprint,
        "benchmark_source_provenance": git_provenance,
        "evaluation_protocol": protocol,
        "agent_cmd": agent_cmd,
        "agent": agent,
        "model": model,
        "harness_type": harness_type,
        "target_log_dir": str(target_log_dir) if target_log_dir is not None else None,
        "timeout_seconds": timeout_seconds,
    } | summarize_evaluation_results(task_results)
    _write_json(run_dir / "summary.json", summary)
    return summary | {"run_dir": str(run_dir)}


def _exit_code(summary: dict[str, Any], require_all_pass: bool = False) -> int:
    if int(summary.get("infrastructure_failure_count", 0)) > 0:
        return 2
    if require_all_pass and summary.get("passed_count") != summary.get("task_count"):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the blinded, evidence-required AuthZBench-SaaS evaluation protocol."
    )
    parser.add_argument("--task", action="append", required=True)
    parser.add_argument("--agent-cmd", required=True)
    parser.add_argument(
        "--agent-source",
        action="append",
        required=True,
        help="Adapter source file to hash for provenance; repeat for every source file.",
    )
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--benchmark-version", default="alpha-0.0.1-public-scaffold-local")
    parser.add_argument("--benchmark-commit-sha")
    parser.add_argument("--agent")
    parser.add_argument("--model")
    parser.add_argument("--harness-type")
    parser.add_argument("--target-log-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--require-all-pass", action="store_true")
    args = parser.parse_args()

    summary = run_evaluation(
        args.task,
        args.agent_cmd,
        Path(args.results_dir),
        args.timeout_seconds,
        benchmark_version=args.benchmark_version,
        benchmark_commit_sha=args.benchmark_commit_sha,
        agent=args.agent,
        model=args.model,
        harness_type=args.harness_type,
        target_log_dir=(Path(args.target_log_dir).resolve() if args.target_log_dir else None),
        run_id=args.run_id,
        agent_source_paths=args.agent_source,
    )
    print(dump_json(summary))
    return _exit_code(summary, require_all_pass=args.require_all_pass)


if __name__ == "__main__":
    raise SystemExit(main())
