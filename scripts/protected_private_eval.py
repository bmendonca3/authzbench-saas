from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import (
    benchmark_fingerprint,
    benchmark_git_source_state,
    build_context,
    dump_json,
    is_safe_identifier,
    load_json,
    runner_integrity_envelope,
    stable_json_sha256,
)
from authzbench.run import summarize_tool_probe_telemetry
from authzbench.score import score_submission


_TARGET_CORRELATION_FIELDS = ("app", "seed", "run_id", "task_id", "agent_id")
_TARGET_LOG_QUIET_SECONDS = 0.3
_TARGET_LOG_MAX_WAIT_SECONDS = 1.0
_TARGET_LOG_POLL_SECONDS = 0.05


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


def _subprocess_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _load_json_artifact(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        artifact = load_json(path)
    except Exception:  # noqa: BLE001 - untrusted agent output must fail closed.
        return None, "invalid_json"
    if not isinstance(artifact, dict):
        return None, "invalid_root"
    return artifact, "valid"


def _adapter_failure_type(
    model_output: dict[str, Any] | None,
    artifact_status: str,
) -> str | None:
    if artifact_status == "missing":
        return None
    if artifact_status != "valid" or not isinstance(model_output, dict):
        return "adapter_metadata_failure"
    returncode = model_output.get("returncode")
    if isinstance(returncode, bool) or not isinstance(returncode, int):
        return "adapter_metadata_failure"
    parse_error = str(model_output.get("parse_error", "")).casefold()
    if returncode != 0 or "command failed" in parse_error or "timed out" in parse_error:
        return "command_failure"
    if model_output.get("model_label_verified") is False:
        return "model_label_failure"
    if model_output.get("parse_error") or model_output.get("json_only_compliant") is False:
        return "output_parse_failure"
    return None


def _optional_int(data: dict[str, Any] | None, *keys: str) -> int | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
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
    try:
        return log_path.stat().st_size
    except OSError:
        return 0


def _strict_json_log_entry(raw_line: bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        entry: dict[str, Any] = {}
        for key, value in pairs:
            if key in entry:
                raise ValueError(f"duplicate JSON key: {key}")
            entry[key] = value
        return entry

    def reject_nonfinite(value: str) -> Any:
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(
        raw_line,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )


def _target_request_snapshot(
    target_log_dir: Path,
    app_name: str,
    seed: str,
    run_id: str,
    task_id: str,
    agent_id: str,
    start_offset: int,
) -> dict[str, Any]:
    log_path = target_log_dir / f"{app_name}.jsonl"
    if not log_path.exists():
        return {
            "captured_entries": [],
            "matched_entries": [],
            "file_exists": False,
            "file_size": 0,
            "log_truncated": False,
            "malformed_line_count": 0,
            "mismatched_correlation_count": 0,
            "post_offset_line_count": 0,
        }

    try:
        file_size = log_path.stat().st_size
        log_truncated = file_size < start_offset
        seek_offset = 0 if log_truncated else start_offset
        with log_path.open("rb") as fh:
            fh.seek(seek_offset)
            raw_lines = fh.read().splitlines()
    except OSError:
        return {
            "captured_entries": [
                {
                    "capture_status": "target_log_read_error",
                    "line_number_after_offset": 0,
                }
            ],
            "matched_entries": [],
            "file_exists": log_path.exists(),
            "file_size": 0,
            "log_truncated": False,
            "malformed_line_count": 1,
            "mismatched_correlation_count": 0,
            "post_offset_line_count": 1,
        }

    expected = {
        "app": app_name,
        "seed": seed,
        "run_id": run_id,
        "task_id": task_id,
        "agent_id": agent_id,
    }
    captured_entries: list[dict[str, Any]] = []
    matched_entries: list[dict[str, Any]] = []
    malformed_line_count = 0
    for line_number, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        try:
            entry = _strict_json_log_entry(line)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            malformed_line_count += 1
            captured_entries.append(
                {
                    "capture_status": "malformed_json",
                    "line_number_after_offset": line_number,
                    "raw_line_sha256": hashlib.sha256(line).hexdigest(),
                }
            )
            continue
        if not isinstance(entry, dict):
            malformed_line_count += 1
            captured_entries.append(
                {
                    "capture_status": "invalid_json_root",
                    "line_number_after_offset": line_number,
                    "raw_line_sha256": hashlib.sha256(line).hexdigest(),
                }
            )
            continue
        mismatched_fields = [
            field for field in _TARGET_CORRELATION_FIELDS if entry.get(field) != expected[field]
        ]
        correlation = {
            "matched_on": list(_TARGET_CORRELATION_FIELDS),
            "mismatched_fields": mismatched_fields,
            "source_log": log_path.name,
            "status": "matched" if not mismatched_fields else "mismatch",
        }
        captured = entry | {"correlation": correlation}
        captured_entries.append(captured)
        if not mismatched_fields:
            matched_entries.append(captured)

    return {
        "captured_entries": captured_entries,
        "matched_entries": matched_entries,
        "file_exists": True,
        "file_size": file_size,
        "log_truncated": log_truncated,
        "malformed_line_count": malformed_line_count,
        "mismatched_correlation_count": len(captured_entries)
        - len(matched_entries)
        - malformed_line_count,
        "post_offset_line_count": len(captured_entries),
    }


def _target_requests_after_settle(
    target_log_dir: Path,
    app_name: str,
    seed: str,
    run_id: str,
    task_id: str,
    agent_id: str,
    start_offset: int,
    *,
    quiet_seconds: float = _TARGET_LOG_QUIET_SECONDS,
    max_wait_seconds: float = _TARGET_LOG_MAX_WAIT_SECONDS,
    poll_seconds: float = _TARGET_LOG_POLL_SECONDS,
) -> dict[str, Any]:
    started = time.monotonic()
    last_change = started
    last_signature: tuple[Any, ...] | None = None
    latest: dict[str, Any] | None = None
    while True:
        latest = _target_request_snapshot(
            target_log_dir,
            app_name,
            seed,
            run_id,
            task_id,
            agent_id,
            start_offset,
        )
        signature = (
            latest["file_exists"],
            latest["file_size"],
            latest["post_offset_line_count"],
            latest["malformed_line_count"],
            latest["mismatched_correlation_count"],
        )
        now = time.monotonic()
        if signature != last_signature:
            last_signature = signature
            last_change = now
        has_post_offset_data = bool(latest["post_offset_line_count"])
        if now - started >= max_wait_seconds:
            latest["quiescence_reached"] = (
                has_post_offset_data and now - last_change >= quiet_seconds
            )
            latest["observation_window_seconds"] = round(now - started, 4)
            return latest
        time.sleep(poll_seconds)


def _target_observation_status(observation: dict[str, Any]) -> str:
    if not observation.get("file_exists"):
        return "target_log_missing"
    if observation.get("log_truncated"):
        return "target_log_truncated"
    if int(observation.get("post_offset_line_count", 0)) == 0:
        return "no_target_requests_correlated"
    if not observation.get("quiescence_reached"):
        return "target_log_quiescence_timeout"
    if int(observation.get("malformed_line_count", 0)) > 0:
        return "target_log_malformed"
    if int(observation.get("mismatched_correlation_count", 0)) > 0:
        return "target_request_correlation_mismatch"
    if not observation.get("matched_entries"):
        return "no_target_requests_correlated"
    return "correlated"


def _run_agent_protected(
    agent_cmd: str,
    context: dict[str, Any],
    timeout_seconds: int,
    *,
    run_id: str,
    task_id: str,
    agent_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
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
        command_args = shlex.split(command)
        isolation_backend = "workspace-only"
        host_private_paths_denied = False
        sandbox_exec = shutil.which("sandbox-exec")
        if sandbox_exec:
            profile_path = temp_root / "agent.sb"
            denied_paths = [
                ROOT / "tasks_private" / "holdout",
                ROOT / "results",
                ROOT / "captures",
                ROOT / "docs" / "reviews" / "panel-logs",
            ]
            profile_lines = ["(version 1)", "(allow default)"]
            profile_lines.extend(
                f'(deny file-read* (subpath {json.dumps(str(path.resolve()))}))'
                for path in denied_paths
            )
            profile_path.write_text("\n".join(profile_lines) + "\n", encoding="utf-8")
            command_args = [sandbox_exec, "-f", str(profile_path), *command_args]
            isolation_backend = "macos-sandbox-exec"
            host_private_paths_denied = True
        try:
            completed = subprocess.run(
                command_args,
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
                "failure_type": "timeout",
                "stdout": _subprocess_text(exc.stdout),
                "stderr": _subprocess_text(exc.stderr) + "\nTIMEOUT",
            }
        except OSError as exc:
            agent_result = {
                "command": agent_cmd,
                "returncode": None,
                "duration_seconds": round(time.time() - started, 4),
                "failure_type": "launch_error",
                "stdout": "",
                "stderr": f"LAUNCH_ERROR: {type(exc).__name__}",
            }

        submission, submission_status = _load_json_artifact(submission_path)
        copied_artifacts: dict[str, Any] = {}
        artifact_statuses: dict[str, str] = {"submission.json": submission_status}
        for artifact_name in ("submission.json", "model-output.json", "model-tool-plan.json", "tool-probes.json"):
            artifact_path = temp_root / artifact_name
            artifact, artifact_status = _load_json_artifact(artifact_path)
            artifact_statuses[artifact_name] = artifact_status
            if artifact is not None:
                copied_artifacts[artifact_name] = artifact
        protection = {
            "agent_workspace_empty_at_start": True,
            "agent_cwd": "temporary-empty-workspace",
            "context_location": "temporary-rendered-context",
            "private_manifest_location": "not-in-agent-workspace",
            "private_task_manifest_exposed_to_agent": False,
            "host_private_paths_denied": host_private_paths_denied,
            "isolation_backend": isolation_backend,
        }
        return agent_result, submission, {
            "artifacts": copied_artifacts,
            "artifact_statuses": artifact_statuses,
            "protection": protection,
        }


def _invalid_protected_score(task: dict[str, Any], reason: str) -> dict[str, Any]:
    try:
        result = score_submission(task, None)
    except Exception:  # noqa: BLE001 - scorer failure still needs a stable task result.
        result = {
            "task_id": task.get("id"),
            "passed": False,
            "core_passed": False,
            "promotion_eligible": False,
            "score": 0,
            "invalid_submission": True,
            "submission_finding_count": 0,
            "control_replay_passed": None,
            "subscores": {
                "exploit_proof": 0,
                "boundary_reasoning": 0,
                "false_positive_control": 0,
                "safety": None,
            },
            "evidence_chain_complete": False,
            "safety_observation_status": "unobserved",
            "transcript": [],
        }
    result["passed"] = False
    result["core_passed"] = False
    result["promotion_eligible"] = False
    result["score"] = 0
    result["invalid_submission"] = True
    result["reason"] = reason
    result["observations"] = [reason]
    return result


def _loaded_pack_root(task_paths: list[Path]) -> Path:
    if not task_paths:
        raise ValueError("protected private evaluation requires at least one task manifest")
    private_holdout_root = (ROOT / "tasks_private" / "holdout").resolve(strict=False)
    relative_private_paths: list[Path] = []
    for task_path in task_paths:
        try:
            relative_private_paths.append(
                task_path.resolve(strict=False).relative_to(private_holdout_root)
            )
        except ValueError:
            relative_private_paths = []
            break
    if relative_private_paths and all(len(path.parts) >= 3 for path in relative_private_paths):
        pack_ids = {path.parts[0] for path in relative_private_paths}
        if len(pack_ids) == 1:
            return private_holdout_root / next(iter(pack_ids))
    common_parent = Path(
        os.path.commonpath(
            [str(path.resolve(strict=False).parent) for path in task_paths]
        )
    )
    return common_parent


def _loaded_pack_fingerprint(
    loaded_tasks: list[tuple[Path, dict[str, Any]]],
) -> str:
    pack_root = _loaded_pack_root([path for path, _task in loaded_tasks])
    digest = hashlib.sha256()
    for manifest_path, manifest in sorted(
        loaded_tasks,
        key=lambda item: item[0].resolve(strict=False).as_posix(),
    ):
        relative = manifest_path.resolve(strict=False).relative_to(pack_root).as_posix()
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(canonical.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_private_pack_binding(
    loaded_tasks: list[tuple[Path, dict[str, Any]]],
    *,
    supplied_fingerprint: str | None,
    private_pack_id: str | None,
    private_pack_version: str | None,
) -> dict[str, Any]:
    computed_fingerprint = _loaded_pack_fingerprint(loaded_tasks)
    if supplied_fingerprint is not None:
        if not isinstance(supplied_fingerprint, str):
            raise ValueError("private pack fingerprint must be a string")
        normalized = supplied_fingerprint.strip()
        if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
            raise ValueError("private pack fingerprint must be a lowercase SHA-256 hex digest")
        if normalized != computed_fingerprint:
            raise ValueError(
                "supplied private pack fingerprint does not match the loaded manifest set"
            )
    for field_name, value in (
        ("private pack id", private_pack_id),
        ("private pack version", private_pack_version),
    ):
        if value is not None and (
            not isinstance(value, str) or not value.strip()
        ):
            raise ValueError(f"{field_name} must be a non-empty string")
    has_pack_id = isinstance(private_pack_id, str) and bool(private_pack_id.strip())
    has_pack_version = isinstance(private_pack_version, str) and bool(
        private_pack_version.strip()
    )
    if (has_pack_id or has_pack_version) and supplied_fingerprint is None:
        raise ValueError(
            "private pack id/version may be emitted only with a supplied fingerprint "
            "that matches the loaded manifest set"
        )
    if has_pack_id != has_pack_version:
        raise ValueError(
            "private pack id and version must be supplied together"
        )
    return {
        "private_pack_fingerprint_sha256": computed_fingerprint,
        "private_pack_loaded_fingerprint_sha256": computed_fingerprint,
        "private_pack_fingerprint_provenance": "runner-computed-loaded-manifests",
    } | (
        {"private_pack_id": private_pack_id.strip()}
        if has_pack_id
        else {}
    ) | (
        {"private_pack_version": private_pack_version.strip()}
        if has_pack_version
        else {}
    )


def _model_identity_observation(
    model_output: dict[str, Any] | None,
    run_model: str | None,
) -> dict[str, Any]:
    if not isinstance(model_output, dict) or not model_output:
        return {}
    requested = model_output.get("requested_model")
    effective = model_output.get("effective_model_label")
    raw_verified = model_output.get("model_label_verified")
    raw_status = model_output.get("model_identity_status")
    requested_label = requested if isinstance(requested, str) and requested else None
    effective_label = effective if isinstance(effective, str) and effective else None
    observed_labels = [
        value for value in (requested_label, effective_label) if value is not None
    ]
    mismatch = bool(
        run_model is not None and any(value != run_model for value in observed_labels)
    )
    fully_bound = bool(
        run_model is not None
        and requested_label == run_model
        and effective_label == run_model
        and raw_verified is True
    )
    if mismatch or raw_verified is False:
        verified: bool | None = False
        status = "mismatch_or_ambiguous"
    elif fully_bound:
        verified = True
        status = "verified"
    else:
        verified = None
        status = (
            str(raw_status)
            if isinstance(raw_status, str)
            and raw_status
            and raw_status != "verified"
            else "requested_only_unverified"
        )
    return {
        "adapter_model_label_mismatch": mismatch,
        "adapter_model_label_verified": verified,
        "adapter_model_identity_status": status,
    } | (
        {"adapter_requested_model": requested_label}
        if requested_label is not None
        else {}
    ) | (
        {"adapter_effective_model_label": effective_label}
        if effective_label is not None
        else {}
    )


def _metric_summary(
    task_results: list[dict[str, Any]],
    *,
    run_id: str,
    benchmark_version: str,
    benchmark_commit_sha: str | None,
    benchmark_source_state: str,
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
    vulnerable_full_passed = sum(1 for item in vulnerable if item["passed"])
    control_replay_passed = sum(1 for item in controls if item["control_replay_passed"] is True)
    controls_with_findings = sum(1 for item in controls if int(item["submission_finding_count"]) > 0)
    authorized_allow_passed = sum(1 for item in authorized_allow_controls if item["passed"])
    v0_passed_count = sum(1 for item in task_results if item["passed"])
    promotion_eligible_count = sum(
        1 for item in task_results if item.get("promotion_eligible") is True
    )
    safety_observed = [
        item for item in task_results if item.get("safety") in {0, 1}
    ]
    vulnerable_safety_observed = [
        item for item in vulnerable if item.get("safety") in {0, 1}
    ]
    vulnerable_safety_passed = sum(
        1 for item in vulnerable_safety_observed if item.get("safety") == 1
    )
    safety_violations = sum(1 for item in safety_observed if item["safety"] == 0)
    target_log_tasks = [
        item for item in task_results if "target_request_count" in item
    ]
    target_log_correlated = sum(
        1
        for item in target_log_tasks
        if item.get("target_request_observation_status") == "correlated"
    )
    task_count = len(task_results)
    completed_tasks = [
        item for item in task_results if item.get("task_execution_status") == "completed"
    ]
    infrastructure_failures = [
        item for item in task_results if item.get("infrastructure_failure") is True
    ]
    execution_statuses = Counter(
        str(item.get("task_execution_status", "unknown")) for item in task_results
    )
    adapter_failures = [
        item for item in task_results if item.get("adapter_failure_type")
    ]
    vulnerable_count = len(vulnerable)
    control_count = len(controls)
    scored_submission_finding_total = sum(
        int(item.get("submission_finding_count", 0)) for item in task_results
    )
    model_tool_plan_artifact_count = sum(1 for item in task_results if item.get("model_tool_plan_artifact"))
    tool_telemetry = summarize_tool_probe_telemetry(task_results)
    planner_parse_error_count = sum(1 for item in task_results if item.get("planner_parse_error"))
    planner_failure_count = sum(
        1
        for item in task_results
        if item.get("model_tool_plan_artifact") and item.get("planner_returncode") not in {None, 0}
    )
    output_formats = Counter(
        str(item["adapter_output_format"])
        for item in task_results
        if item.get("adapter_output_format")
    )
    json_compliant = sum(
        1 for item in task_results if item.get("adapter_json_only_compliant") is True
    )
    identity_statuses = Counter(
        str(item["adapter_model_identity_status"])
        for item in task_results
        if item.get("adapter_model_identity_status")
    )
    requested_model_labels = sorted(
        {
            str(item["adapter_requested_model"])
            for item in task_results
            if isinstance(item.get("adapter_requested_model"), str)
            and item["adapter_requested_model"]
        }
    )
    effective_model_labels = sorted(
        {
            str(item["adapter_effective_model_label"])
            for item in task_results
            if isinstance(item.get("adapter_effective_model_label"), str)
            and item["adapter_effective_model_label"]
        }
    )
    requested_model_matches = sum(
        1
        for item in task_results
        if model is not None and item.get("adapter_requested_model") == model
    )
    effective_model_matches = sum(
        1
        for item in task_results
        if model is not None and item.get("adapter_effective_model_label") == model
    )
    model_label_mismatches = sum(
        1 for item in task_results if item.get("adapter_model_label_mismatch") is True
    )
    model_identity_status = (
        next(iter(identity_statuses))
        if len(identity_statuses) == 1
        and sum(identity_statuses.values()) == task_count
        else "mixed_or_unobserved"
    )
    return {
        "agent": agent,
        "authorized_allow_control_task_count": len(authorized_allow_controls),
        "authorized_allow_pass_rate": round(authorized_allow_passed / len(authorized_allow_controls), 4)
        if authorized_allow_controls
        else None,
        "benchmark_commit_sha": benchmark_commit_sha,
        "benchmark_version": benchmark_version,
        "benchmark_execution_status": (
            "completed"
            if task_count > 0
            and len(completed_tasks) == task_count
            and not infrastructure_failures
            else "completed_with_infrastructure_failures"
            if task_count > 0
            else "incomplete"
        ),
        "benchmark_source_state": benchmark_source_state,
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
        "evaluation_protocol": {
            "protocol_version": "protected-private-task-authored-v1",
            "participant_context_profile": "legacy-task-authored-v1",
            "candidate_evidence_mode": "agent-submitted-findings-host-replayed",
            "control_verification_required": False,
        },
        "exploit_proven_success_rate": round(exploit_proven / vulnerable_count, 4) if vulnerable_count else None,
        "exploit_proven_task_count": exploit_proven,
        "false_positive_rate": round(controls_with_findings / control_count, 4) if control_count else None,
        "harness_type": harness_type,
        "invalid_submission_count": invalid_submissions,
        "invalid_submission_rate": round(invalid_submissions / task_count, 4) if task_count else None,
        "adapter_json_only_compliant_count": json_compliant,
        "adapter_json_only_compliance_rate": (
            round(json_compliant / sum(output_formats.values()), 4)
            if output_formats
            else None
        ),
        "adapter_failure_count": len(adapter_failures),
        "adapter_failure_type_counts": dict(
            sorted(
                Counter(
                    str(item["adapter_failure_type"]) for item in adapter_failures
                ).items()
            )
        ),
        "adapter_metadata_failure_count": sum(
            1
            for item in adapter_failures
            if item.get("adapter_failure_type") == "adapter_metadata_failure"
        ),
        "adapter_output_parse_failure_count": sum(
            1
            for item in adapter_failures
            if item.get("adapter_failure_type") == "output_parse_failure"
        ),
        "infrastructure_failure_count": len(infrastructure_failures),
        "infrastructure_failure_rate": (
            round(len(infrastructure_failures) / task_count, 4)
            if task_count
            else None
        ),
        "invalid_submission_artifact_count": sum(
            1
            for item in task_results
            if item.get("submission_artifact_status") in {"invalid_json", "invalid_root"}
        ),
        "missing_submission_count": sum(
            1
            for item in task_results
            if item.get("submission_artifact_status") == "missing"
        ),
        "mean_score": round(sum(float(item["score"]) for item in task_results) / task_count, 4) if task_count else 0,
        "model": model,
        "effective_model_labels": effective_model_labels,
        "effective_model_label_match_task_count": effective_model_matches,
        "model_identity_status": model_identity_status,
        "model_identity_status_counts": dict(sorted(identity_statuses.items())),
        "model_label_mismatch_task_count": model_label_mismatches,
        "model_label_verified_task_count": sum(
            1 for item in task_results if item.get("adapter_model_label_verified") is True
        ),
        "requested_model_labels": requested_model_labels,
        "requested_model_label_match_task_count": requested_model_matches,
        "model_tool_plan_artifact_count": model_tool_plan_artifact_count,
        "passed_count": sum(1 for item in task_results if item["passed"]),
        "core_passed_count": sum(
            1 for item in task_results if item.get("core_passed") is True
        ),
        "promotion_eligible_count": promotion_eligible_count,
        "promotion_eligibility_rate": (
            round(promotion_eligible_count / task_count, 4)
            if task_count
            else None
        ),
        "planner_failure_count": planner_failure_count,
        "planner_parse_error_count": planner_parse_error_count,
        "runner_agent_failure_count": sum(
            1 for item in task_results if item.get("runner_agent_failure") is True
        ),
        "scoring_failure_count": sum(
            1 for item in task_results if item.get("scoring_failure") is True
        ),
        "protected_execution": {
            "agent_cwd": "temporary-empty-workspace",
            "agent_received": "rendered-context-only",
            "host_private_paths_denied": all(
                item.get("protected_execution", {}).get("host_private_paths_denied") is True
                for item in task_results
            ),
            "isolation_backend": next(
                (
                    item.get("protected_execution", {}).get("isolation_backend")
                    for item in task_results
                    if item.get("protected_execution", {}).get("isolation_backend")
                ),
                "workspace-only",
            ),
            "private_manifests_readable_in_agent_workspace": False,
            "raw_result_bundle_tracked": bool(_git_ls_files("results")),
            "tracked_private_manifest_count": len(_git_ls_files("tasks_private/holdout")),
        },
        "run_id": run_id,
        "scored_submission_finding_total": scored_submission_finding_total,
        "split": "private-holdout",
        "safety_observation_coverage_rate": (
            round(len(safety_observed) / task_count, 4)
            if task_count
            else None
        ),
        "safety_observation_status_counts": dict(
            sorted(
                {
                    status: sum(
                        1
                        for item in task_results
                        if item.get("safety_observation_status") == status
                    )
                    for status in {
                        str(item.get("safety_observation_status", "unobserved"))
                        for item in task_results
                    }
                }.items()
            )
        ),
        "safety_violations": safety_violations,
        "target_request_correlated_task_count": (
            target_log_correlated if target_log_tasks else None
        ),
        "target_request_coverage_rate": (
            round(target_log_correlated / len(target_log_tasks), 4)
            if target_log_tasks
            else None
        ),
        "target_request_correlation_mismatch_count": (
            sum(
                int(item.get("target_request_correlation_mismatch_count", 0))
                for item in target_log_tasks
            )
            if target_log_tasks
            else None
        ),
        "target_request_malformed_line_count": (
            sum(
                int(item.get("target_request_malformed_line_count", 0))
                for item in target_log_tasks
            )
            if target_log_tasks
            else None
        ),
        "target_request_observation_status_counts": (
            dict(
                sorted(
                    Counter(
                        str(item.get("target_request_observation_status", "unknown"))
                        for item in target_log_tasks
                    ).items()
                )
            )
            if target_log_tasks
            else {}
        ),
        "target_request_post_offset_total": (
            sum(
                int(item.get("target_post_offset_request_count", 0))
                for item in target_log_tasks
            )
            if target_log_tasks
            else None
        ),
        "task_count": task_count,
        "task_completion_count": len(completed_tasks),
        "task_incomplete_count": task_count - len(completed_tasks),
        "task_execution_status_counts": dict(sorted(execution_statuses.items())),
        "tasks": task_results,
        "v0_mean_score": round(v0_passed_count / task_count, 4) if task_count else 0,
        "v0_metric_profile": "deprecated-alias-score-policy-v3-core-authz",
        "v0_passed_count": v0_passed_count,
        "vulnerable_full_pass_count": vulnerable_full_passed,
        "evidence_chain_complete_count": sum(
            1
            for item in vulnerable
            if item.get("evidence_chain_complete") is True
        ),
        "vulnerable_safety_observation_coverage_rate": (
            round(len(vulnerable_safety_observed) / vulnerable_count, 4)
            if vulnerable_count
            else None
        ),
        "vulnerable_safety_pass_rate": (
            round(vulnerable_safety_passed / len(vulnerable_safety_observed), 4)
            if vulnerable_safety_observed
            else None
        ),
        "vulnerable_task_count": vulnerable_count,
    } | tool_telemetry


def redacted_summary(summary: dict[str, Any]) -> dict[str, Any]:
    protected = summary.get("protected_execution") if isinstance(summary.get("protected_execution"), dict) else {}
    redacted = {
        "agent": summary.get("agent"),
        "authorized_allow_control_task_count": summary.get("authorized_allow_control_task_count"),
        "authorized_allow_pass_rate": summary.get("authorized_allow_pass_rate"),
        "benchmark_commit_sha": summary.get("benchmark_commit_sha"),
        "benchmark_execution_status": summary.get("benchmark_execution_status"),
        "benchmark_fingerprint": summary.get("benchmark_fingerprint"),
        "benchmark_fingerprint_provenance": "runner-emitted",
        "benchmark_source_state": summary.get("benchmark_source_state"),
        "benchmark_version": summary.get("benchmark_version"),
        "boundary_reasoning_pass_rate": summary.get("boundary_reasoning_pass_rate"),
        "control_execution_pass_rate": summary.get("control_execution_pass_rate"),
        "control_false_report_count": summary.get("control_false_report_count"),
        "control_false_report_rate": summary.get("control_false_report_rate"),
        "control_task_count": summary.get("control_task_count"),
        "denial_control_task_count": summary.get("denial_control_task_count"),
        "executed_tool_probe_total": summary.get("executed_tool_probe_total"),
        "evaluation_protocol": summary.get("evaluation_protocol"),
        "exploit_proven_success_rate": summary.get("exploit_proven_success_rate"),
        "exploit_proven_task_count": summary.get("exploit_proven_task_count"),
        "fallback_probe_total": summary.get("fallback_probe_total"),
        "false_positive_rate": summary.get("false_positive_rate"),
        "full_result_bundle_tracked": bool(protected.get("raw_result_bundle_tracked")),
        "harness_type": summary.get("harness_type"),
        "invalid_submission_count": summary.get("invalid_submission_count"),
        "invalid_submission_rate": summary.get("invalid_submission_rate"),
        "adapter_json_only_compliant_count": summary.get(
            "adapter_json_only_compliant_count"
        ),
        "adapter_json_only_compliance_rate": summary.get(
            "adapter_json_only_compliance_rate"
        ),
        "adapter_failure_count": summary.get("adapter_failure_count"),
        "adapter_failure_type_counts": summary.get("adapter_failure_type_counts"),
        "adapter_metadata_failure_count": summary.get(
            "adapter_metadata_failure_count"
        ),
        "adapter_output_parse_failure_count": summary.get(
            "adapter_output_parse_failure_count"
        ),
        "core_passed_count": summary.get("core_passed_count"),
        "evidence_chain_complete_count": summary.get(
            "evidence_chain_complete_count"
        ),
        "infrastructure_failure_count": summary.get("infrastructure_failure_count"),
        "infrastructure_failure_rate": summary.get("infrastructure_failure_rate"),
        "invalid_submission_artifact_count": summary.get(
            "invalid_submission_artifact_count"
        ),
        "missing_submission_count": summary.get("missing_submission_count"),
        "mean_score": summary.get("mean_score"),
        "model": summary.get("model"),
        "effective_model_labels": summary.get("effective_model_labels"),
        "effective_model_label_match_task_count": summary.get(
            "effective_model_label_match_task_count"
        ),
        "model_identity_status": summary.get("model_identity_status"),
        "model_identity_status_counts": summary.get("model_identity_status_counts"),
        "model_label_mismatch_task_count": summary.get(
            "model_label_mismatch_task_count"
        ),
        "model_label_verified_task_count": summary.get(
            "model_label_verified_task_count"
        ),
        "requested_model_labels": summary.get("requested_model_labels"),
        "requested_model_label_match_task_count": summary.get(
            "requested_model_label_match_task_count"
        ),
        "model_tool_plan_artifact_count": summary.get("model_tool_plan_artifact_count"),
        "per_task_tool_probe_artifact_count": summary.get("per_task_tool_probe_artifact_count"),
        "tool_probe_telemetry_complete_task_count": summary.get(
            "tool_probe_telemetry_complete_task_count"
        ),
        "tool_probe_telemetry_coverage_rate": summary.get("tool_probe_telemetry_coverage_rate"),
        "tool_probe_telemetry_status": summary.get("tool_probe_telemetry_status"),
        "planner_failure_count": summary.get("planner_failure_count"),
        "planner_parse_error_count": summary.get("planner_parse_error_count"),
        "private_holdout_task_count": summary.get("task_count"),
        "private_pack_fingerprint_sha256": summary.get("private_pack_fingerprint_sha256"),
        "private_pack_loaded_fingerprint_sha256": summary.get(
            "private_pack_loaded_fingerprint_sha256"
        ),
        "private_pack_fingerprint_provenance": summary.get(
            "private_pack_fingerprint_provenance"
        ),
        "private_pack_id": summary.get("private_pack_id"),
        "private_pack_version": summary.get("private_pack_version"),
        "protected_execution": {
            "agent_cwd": protected.get("agent_cwd"),
            "agent_received": protected.get("agent_received"),
            "host_private_paths_denied": protected.get("host_private_paths_denied"),
            "isolation_backend": protected.get("isolation_backend"),
            "private_manifests_readable_in_agent_workspace": protected.get(
                "private_manifests_readable_in_agent_workspace"
            ),
            "tracked_private_manifest_count": protected.get("tracked_private_manifest_count"),
        },
        "public_task_count": 0,
        "raw_private_artifacts_tracked": bool(protected.get("raw_result_bundle_tracked")),
        "redacted_private_holdout_source": True,
        "promotion_eligible_count": summary.get("promotion_eligible_count"),
        "promotion_eligibility_rate": summary.get("promotion_eligibility_rate"),
        "run_count": 1,
        "run_id": str(summary.get("run_id", "")) + "-redacted",
        "runner_agent_failure_count": summary.get("runner_agent_failure_count"),
        "scoring_failure_count": summary.get("scoring_failure_count"),
        "safety_observation_coverage_rate": summary.get(
            "safety_observation_coverage_rate"
        ),
        "safety_observation_status_counts": summary.get(
            "safety_observation_status_counts"
        ),
        "safety_violations": summary.get("safety_violations"),
        "scored_submission_finding_total": summary.get("scored_submission_finding_total"),
        "split": "private-holdout",
        "submitted_finding_total": summary.get("submitted_finding_total"),
        "target_request_correlated_task_count": summary.get("target_request_correlated_task_count"),
        "target_request_correlation_mismatch_count": summary.get(
            "target_request_correlation_mismatch_count"
        ),
        "target_request_coverage_rate": summary.get("target_request_coverage_rate"),
        "target_request_malformed_line_count": summary.get(
            "target_request_malformed_line_count"
        ),
        "target_request_observation_status_counts": summary.get(
            "target_request_observation_status_counts"
        ),
        "target_request_post_offset_total": summary.get(
            "target_request_post_offset_total"
        ),
        "task_count": summary.get("task_count"),
        "task_completion_count": summary.get("task_completion_count"),
        "task_incomplete_count": summary.get("task_incomplete_count"),
        "task_execution_status_counts": summary.get(
            "task_execution_status_counts"
        ),
        "tracked_private_manifest_count": protected.get("tracked_private_manifest_count"),
        "v0_mean_score": summary.get("v0_mean_score"),
        "v0_metric_profile": summary.get("v0_metric_profile"),
        "v0_passed_count": summary.get("v0_passed_count"),
        "vulnerable_full_pass_count": summary.get("vulnerable_full_pass_count"),
        "vulnerable_safety_observation_coverage_rate": summary.get(
            "vulnerable_safety_observation_coverage_rate"
        ),
        "vulnerable_safety_pass_rate": summary.get("vulnerable_safety_pass_rate"),
        "vulnerable_task_count": summary.get("vulnerable_task_count"),
    }
    for optional_pack_field in ("private_pack_id", "private_pack_version"):
        if redacted.get(optional_pack_field) is None:
            redacted.pop(optional_pack_field, None)
    raw_summary_payload = {
        key: value for key, value in summary.items() if key != "runner_integrity"
    }
    task_rows = summary.get("tasks")
    if not isinstance(task_rows, list):
        task_rows = []
    task_row_hashes = [
        stable_json_sha256(row) for row in task_rows if isinstance(row, dict)
    ]
    adapter_artifact_hashes = sorted(
        str(row["adapter_model_output_sha256"])
        for row in task_rows
        if isinstance(row, dict)
        and isinstance(row.get("adapter_model_output_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", row["adapter_model_output_sha256"])
    )
    redacted["runner_integrity"] = runner_integrity_envelope(
        redacted,
        generator="scripts/protected_private_eval.py",
        raw_summary_sha256=stable_json_sha256(raw_summary_payload),
        task_rows_digest_sha256=stable_json_sha256(task_row_hashes),
        adapter_artifact_set_sha256=(
            stable_json_sha256(adapter_artifact_hashes)
            if adapter_artifact_hashes
            else None
        ),
    )
    return redacted


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
    private_pack_fingerprint_sha256: str | None = None,
    private_pack_id: str | None = None,
    private_pack_version: str | None = None,
) -> dict[str, Any]:
    if not isinstance(agent_cmd, str) or not agent_cmd.strip():
        raise ValueError("agent_cmd must be a non-empty command string")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout_seconds must be positive")
    run_id = run_id or _utc_run_id()
    if not is_safe_identifier(run_id):
        raise ValueError("run_id must be a safe single path component")
    benchmark_source = benchmark_git_source_state(benchmark_commit_sha)
    task_paths = _task_paths(task_patterns)
    loaded_tasks = [(path, load_json(path)) for path in task_paths]
    seen_task_ids: set[str] = set()
    for task_path, task in loaded_tasks:
        if not isinstance(task, dict) or not is_safe_identifier(task.get("id")):
            raise ValueError(
                f"{task_path}: task id must be a safe single path component"
            )
        if task["id"] in seen_task_ids:
            raise ValueError(f"duplicate task id in protected evaluation: {task['id']}")
        seen_task_ids.add(task["id"])
        if task.get("split") != "private_holdout":
            raise ValueError(
                "protected private evaluation only accepts split=private_holdout manifests"
            )
    pack_binding = _validate_private_pack_binding(
        loaded_tasks,
        supplied_fingerprint=private_pack_fingerprint_sha256,
        private_pack_id=private_pack_id,
        private_pack_version=private_pack_version,
    )
    run_dir = results_dir / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError(
            f"refusing to overwrite non-empty protected evaluation directory: {run_dir}"
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    task_results: list[dict[str, Any]] = []

    for task_path, task in loaded_tasks:
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
        _write_json(task_dir / "protected-artifacts.json", protected_artifacts)
        for artifact_name, artifact_data in protected_artifacts["artifacts"].items():
            _write_json(task_dir / artifact_name, artifact_data)
        tool_probe_data = protected_artifacts["artifacts"].get("tool-probes.json")
        if not isinstance(tool_probe_data, dict):
            tool_probe_data = {}
        model_tool_plan_data = protected_artifacts["artifacts"].get("model-tool-plan.json")
        if not isinstance(model_tool_plan_data, dict):
            model_tool_plan_data = {}
        model_output_data = protected_artifacts["artifacts"].get("model-output.json")
        if not isinstance(model_output_data, dict):
            model_output_data = {}
        artifact_statuses = protected_artifacts.get("artifact_statuses", {})
        submission_artifact_status = str(
            artifact_statuses.get("submission.json", "missing")
        )
        model_output_artifact_status = str(
            artifact_statuses.get("model-output.json", "missing")
        )
        model_identity = _model_identity_observation(model_output_data, model)
        adapter_failure_type = _adapter_failure_type(
            model_output_data or None,
            model_output_artifact_status,
        )
        if model_identity.get("adapter_model_label_mismatch") is True:
            adapter_failure_type = "model_label_failure"
        planner_returncode = _planner_returncode(model_tool_plan_data)
        planner_parse_error = _planner_parse_error(model_tool_plan_data)
        executed_probe_count = _optional_int(tool_probe_data, "executed_probe_count", "probe_count")
        fallback_probe_count = _optional_int(tool_probe_data, "fallback_probe_count")
        submitted_finding_count = _optional_int(tool_probe_data, "submitted_finding_count")

        observed_requests: list[dict[str, Any]] | None = None
        target_request_count: int | None = None
        target_request_warning: str | None = None
        target_observation: dict[str, Any] | None = None
        target_observation_status: str | None = None
        if target_log_dir is not None:
            target_observation = _target_requests_after_settle(
                target_log_dir,
                task["app"],
                task["seed"],
                run_id,
                task["id"],
                agent_id,
                target_log_start_offset,
            )
            _write_jsonl(
                task_dir / "target-requests.jsonl",
                target_observation["captured_entries"],
            )
            target_request_count = len(target_observation["matched_entries"])
            target_observation_status = _target_observation_status(
                target_observation
            )
            if target_observation_status != "correlated":
                target_request_warning = target_observation_status
            else:
                observed_requests = target_observation["matched_entries"]

        runner_agent_failure = agent_result["returncode"] != 0
        task_execution_status = "completed"
        if agent_result.get("failure_type") == "launch_error":
            task_execution_status = "agent_launch_failure"
        elif agent_result["returncode"] is None:
            task_execution_status = "agent_timeout"
        elif agent_result["returncode"] != 0:
            task_execution_status = "agent_command_failure"
        elif submission_artifact_status == "missing":
            task_execution_status = "submission_missing"
        elif submission_artifact_status != "valid":
            task_execution_status = "submission_invalid"
        elif adapter_failure_type is not None:
            task_execution_status = "adapter_failure"
        elif (
            target_log_dir is not None
            and target_observation_status != "correlated"
        ):
            task_execution_status = "target_observation_failure"

        scoring_failure = False
        if task_execution_status != "completed":
            score = _invalid_protected_score(
                task,
                f"protected execution failed: {task_execution_status}",
            )
        else:
            try:
                score = score_submission(
                    task,
                    submission,
                    observed_requests=observed_requests,
                )
            except Exception as exc:  # noqa: BLE001 - preserve per-task failure evidence.
                scoring_failure = True
                task_execution_status = "scorer_failure"
                score = _invalid_protected_score(
                    task,
                    f"scoring failed: {type(exc).__name__}",
                )
        infrastructure_failure = task_execution_status != "completed"
        _write_json(task_dir / "score.json", score)
        _write_json(task_dir / "transcript.json", {"task_id": task["id"], "entries": score.get("transcript", [])})
        task_results.append(
            {
                "agent_returncode": agent_result["returncode"],
                "adapter_failure_type": adapter_failure_type,
                "boundary_reasoning": score.get("subscores", {}).get("boundary_reasoning", 0),
                "control_replay_passed": score.get("control_replay_passed"),
                "control_type": task.get("control_type") if not task.get("expected_vulnerable") else None,
                "evidence_chain_complete": bool(
                    score.get("evidence_chain_complete")
                ),
                "expected_vulnerable": bool(task.get("expected_vulnerable")),
                "exploit_proof": score.get("subscores", {}).get("exploit_proof", 0),
                "false_positive_control": score.get("subscores", {}).get("false_positive_control", 0),
                "infrastructure_failure": infrastructure_failure,
                "invalid_submission": bool(score.get("invalid_submission")),
                "model_tool_plan_artifact": "model-tool-plan.json" in protected_artifacts["artifacts"],
                "observed_mutation_count": score.get("observed_mutation_count"),
                "observed_out_of_scope_mutation_count": score.get(
                    "observed_out_of_scope_mutation_count"
                ),
                "observed_request_count": score.get("observed_request_count"),
                "passed": bool(score.get("passed")),
                "runner_agent_failure": runner_agent_failure,
                "safety": score.get("subscores", {}).get("safety"),
                "core_passed": bool(score.get("core_passed")),
                "promotion_eligible": bool(score.get("promotion_eligible")),
                "safety_observation_status": score.get(
                    "safety_observation_status",
                    "unobserved",
                ),
                "score": score.get("score", 0),
                "scoring_failure": scoring_failure,
                "submission_artifact_status": submission_artifact_status,
                "submission_finding_count": score.get("submission_finding_count", 0),
                "task_id": task["id"],
                "task_execution_status": task_execution_status,
                "tool_probe_artifact": "tool-probes.json" in protected_artifacts["artifacts"],
                "protected_execution": protected_artifacts["protection"],
            }
            | ({"executed_probe_count": executed_probe_count} if executed_probe_count is not None else {})
            | ({"fallback_probe_count": fallback_probe_count} if fallback_probe_count is not None else {})
            | ({"submitted_finding_count": submitted_finding_count} if submitted_finding_count is not None else {})
            | ({"planner_returncode": planner_returncode} if planner_returncode is not None else {})
            | ({"planner_parse_error": planner_parse_error} if planner_parse_error else {})
            | ({"target_request_count": target_request_count} if target_request_count is not None else {})
            | ({"target_request_warning": target_request_warning} if target_request_warning else {})
            | (
                {
                    "target_post_offset_request_count": int(
                        target_observation["post_offset_line_count"]
                    ),
                    "target_request_correlation_mismatch_count": int(
                        target_observation["mismatched_correlation_count"]
                    ),
                    "target_request_malformed_line_count": int(
                        target_observation["malformed_line_count"]
                    ),
                    "target_request_observation_status": target_observation_status,
                    "target_request_quiescence_reached": bool(
                        target_observation["quiescence_reached"]
                    ),
                }
                if target_observation is not None
                else {}
            )
            | (
                {
                    "adapter_model_output_sha256": stable_json_sha256(
                        model_output_data
                    ),
                    "adapter_json_only_compliant": model_output_data.get(
                        "json_only_compliant"
                    ),
                    "adapter_output_format": model_output_data.get("output_format"),
                }
                if model_output_data
                else {}
            )
            | model_identity
        )

    summary = _metric_summary(
        task_results,
        run_id=run_id,
        benchmark_version=benchmark_version,
        benchmark_commit_sha=benchmark_source["benchmark_commit_sha"],
        benchmark_source_state=benchmark_source["benchmark_source_state"],
        agent=agent,
        model=model,
        harness_type=harness_type,
    )
    summary.update(pack_binding)
    summary["benchmark_fingerprint"] = benchmark_fingerprint(
        [
            (
                str(task_path.relative_to(ROOT)) if task_path.is_relative_to(ROOT) else task_path.name,
                task,
            )
            for task_path, task in loaded_tasks
        ]
    )
    if target_log_dir is not None:
        target_log_tasks = [item for item in task_results if "target_request_count" in item]
        target_log_correlated = sum(
            1
            for item in target_log_tasks
            if item.get("target_request_observation_status") == "correlated"
        )
        summary["target_log_dir"] = str(target_log_dir)
        summary["target_request_correlated_task_count"] = target_log_correlated
        summary["target_request_coverage_rate"] = (
            round(target_log_correlated / len(target_log_tasks), 4)
            if target_log_tasks
            else None
        )
    _write_json(run_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run private holdouts without exposing manifests to agent cwd.")
    parser.add_argument("--task", action="append")
    parser.add_argument("--agent-cmd", required=True)
    parser.add_argument("--results-dir", default="results/protected-private-eval")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--benchmark-version", default="alpha-0.0.1-public-scaffold-local")
    parser.add_argument("--benchmark-commit-sha")
    parser.add_argument("--agent")
    parser.add_argument("--model")
    parser.add_argument("--harness-type")
    parser.add_argument(
        "--target-log-dir",
        help="Directory containing target-side <app>.jsonl logs to correlate per task.",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--private-pack-fingerprint-sha256")
    parser.add_argument("--private-pack-id")
    parser.add_argument("--private-pack-version")
    parser.add_argument("--redacted-summary-output")
    args = parser.parse_args()

    summary = run_protected_private_eval(
        args.task or ["tasks_private/holdout/**/*.json"],
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
        private_pack_fingerprint_sha256=args.private_pack_fingerprint_sha256,
        private_pack_id=args.private_pack_id,
        private_pack_version=args.private_pack_version,
    )
    if args.redacted_summary_output:
        output = Path(args.redacted_summary_output)
        _write_json(output, redacted_summary(summary))
    print(dump_json(redacted_summary(summary)))
    return 0 if summary.get("benchmark_execution_status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
