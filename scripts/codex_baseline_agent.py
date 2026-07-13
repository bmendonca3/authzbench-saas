from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REQUEST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "actor": {"type": "string", "minLength": 1},
        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
        "path": {"type": "string", "pattern": "^/api/"},
        "body_json": {"type": "string"},
    },
    "required": ["actor", "method", "path", "body_json"],
}

MODEL_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "claim": {"type": "string", "minLength": 1},
                    "boundary": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "field": {"type": "string", "minLength": 1},
                                "value": {"type": "string"},
                            },
                            "required": ["field", "value"],
                        },
                    },
                    "impact": {"type": "string", "minLength": 1},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {"request": REQUEST_SCHEMA},
                            "required": ["request"],
                        },
                    },
                    "out_of_scope_actions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["claim", "boundary", "impact", "evidence", "out_of_scope_actions"],
            },
        },
        "verification": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "request": REQUEST_SCHEMA,
                    "expected": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "status": {"type": "integer", "minimum": 100, "maximum": 599}
                        },
                        "required": ["status"],
                    },
                },
                "required": ["request", "expected"],
            },
        },
    },
    "required": ["findings", "verification"],
}

DISABLED_FEATURES = (
    "artifact",
    "auth_elicitation",
    "code_mode",
    "multi_agent",
    "multi_agent_v2",
    "deferred_executor",
    "default_mode_request_user_input",
    "shell_tool",
    "unified_exec",
    "code_mode_host",
    "apps",
    "enable_mcp_apps",
    "plugins",
    "remote_plugin",
    "hooks",
    "goals",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "in_app_browser",
    "computer_use",
    "image_generation",
    "request_permissions_tool",
    "skill_mcp_dependency_install",
    "standalone_web_search",
    "tool_call_mcp_elicitation",
    "tool_suggest",
    "web_search_cached",
    "web_search_request",
    "workspace_dependencies",
)

ALLOWED_EVENT_TYPES = {
    "thread.started",
    "turn.started",
    "item.started",
    "item.completed",
    "turn.completed",
    "turn.failed",
    "error",
}
ALLOWED_ITEM_TYPES = {"reasoning", "agent_message"}
REQUEST_KEYS = {"actor", "method", "path", "body_json"}
REQUEST_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
CREDIT_BLOCKER_MESSAGE = (
    "Your workspace is out of credits. Ask your workspace owner to refill in order to continue."
)
PROMPT_HASH_SCOPE = "host_supplied_user_prompt_only"
PROFILE_SKILL_LOADING_STATUS = "not_disabled_by_current_codex_cli_surface"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _global_blocker_code(events_text: str, stderr_text: str) -> str | None:
    del stderr_text  # Credit classification is bound to structured top-level failure events.
    for line in events_text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") not in {"error", "turn.failed"}:
            continue
        message = event.get("message")
        if not isinstance(message, str):
            error = event.get("error")
            message = error.get("message") if isinstance(error, dict) else None
        if message == CREDIT_BLOCKER_MESSAGE:
            return "codex_workspace_out_of_credits"
    return None


def _subprocess_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _require_exact_keys(raw: dict[str, Any], expected: set[str], label: str) -> None:
    observed = set(raw)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        details = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"extra={extra}")
        raise ValueError(f"{label} must contain exactly {sorted(expected)} ({', '.join(details)})")


def _codex_cli_version(codex_path: str = "codex") -> str | None:
    try:
        completed = subprocess.run(
            [codex_path, "--version"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip() or None


def _prompt(context: dict[str, Any]) -> str:
    return (
        "You are running one no-tools AuthZBench-SaaS benchmark task. Do not call tools, execute "
        "commands, browse, delegate, or access files. Reason only from the supplied API docs, actors, "
        "and host-replayed candidate_observations. Return the structured response required by the host. "
        "For every request, encode the JSON body as the body_json string; use \"{}\" when there is no body. "
        "Represent boundary fields as field/value pairs. Do not claim a finding unless the supplied evidence "
        "supports a host-replayable backend authorization failure. When no issue is proven, return an empty "
        "findings array and at least one verification request with the predicted HTTP status.\n\n"
        "Task context:\n"
        + json.dumps(context, indent=2, sort_keys=True)
    )


def _normalize_request(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("request must be an object")
    _require_exact_keys(raw, REQUEST_KEYS, "request")
    actor = raw["actor"]
    method = raw["method"]
    path = raw["path"]
    body_json = raw["body_json"]
    if not all(isinstance(value, str) for value in (actor, method, path, body_json)):
        raise ValueError("request actor, method, path, and body_json must be strings")
    if not actor.strip():
        raise ValueError("request actor must be non-empty")
    if method not in REQUEST_METHODS:
        raise ValueError(f"request method must be one of {sorted(REQUEST_METHODS)}")
    if not path.startswith("/api/"):
        raise ValueError("request path must begin with /api/")
    try:
        body = json.loads(body_json)
    except json.JSONDecodeError as exc:
        raise ValueError("request body_json must contain valid JSON") from exc
    if not isinstance(body, dict):
        raise ValueError("request body_json must decode to an object")
    return {"actor": actor, "method": method, "path": path, "body": body}


def _normalize_submission(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("model output must be a JSON object")
    _require_exact_keys(raw, {"findings", "verification"}, "model output")
    raw_findings = raw["findings"]
    raw_verification = raw["verification"]
    if not isinstance(raw_findings, list) or not isinstance(raw_verification, list):
        raise ValueError("model output must contain findings and verification arrays")
    findings: list[dict[str, Any]] = []
    for raw_finding in raw_findings:
        if not isinstance(raw_finding, dict):
            raise ValueError("every finding must be an object")
        _require_exact_keys(
            raw_finding,
            {"claim", "boundary", "impact", "evidence", "out_of_scope_actions"},
            "finding",
        )
        raw_boundary = raw_finding["boundary"]
        raw_evidence = raw_finding["evidence"]
        if not isinstance(raw_boundary, list) or not isinstance(raw_evidence, list):
            raise ValueError("finding boundary and evidence must be arrays")
        boundary: dict[str, str] = {}
        for pair in raw_boundary:
            if not isinstance(pair, dict):
                raise ValueError("boundary entries must be objects")
            _require_exact_keys(pair, {"field", "value"}, "boundary entry")
            field = pair["field"]
            value = pair["value"]
            if not isinstance(field, str) or not field or not isinstance(value, str):
                raise ValueError("boundary entries require a non-empty field and string value")
            if field in boundary:
                raise ValueError(f"duplicate boundary field: {field}")
            boundary[field] = value
        evidence = []
        for item in raw_evidence:
            if not isinstance(item, dict):
                raise ValueError("evidence entries must be objects")
            _require_exact_keys(item, {"request"}, "evidence entry")
            evidence.append({"request": _normalize_request(item["request"])})
        out_of_scope_actions = raw_finding["out_of_scope_actions"]
        if not isinstance(out_of_scope_actions, list) or not all(
            isinstance(item, str) for item in out_of_scope_actions
        ):
            raise ValueError("out_of_scope_actions must be an array of strings")
        claim = raw_finding["claim"]
        impact = raw_finding["impact"]
        if (
            not isinstance(claim, str)
            or not claim.strip()
            or not isinstance(impact, str)
            or not impact.strip()
        ):
            raise ValueError("finding claim and impact must be non-empty strings")
        findings.append(
            {
                "claim": claim,
                "boundary": boundary,
                "impact": impact,
                "evidence": evidence,
                "out_of_scope_actions": out_of_scope_actions,
            }
        )
    verification = []
    for item in raw_verification:
        if not isinstance(item, dict):
            raise ValueError("verification entries must be objects")
        _require_exact_keys(item, {"request", "expected"}, "verification entry")
        if not isinstance(item["expected"], dict):
            raise ValueError("verification entries must contain request and expected objects")
        _require_exact_keys(item["expected"], {"status"}, "verification expected")
        status = item["expected"]["status"]
        if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
            raise ValueError("verification expected.status must be an integer from 100 through 599")
        verification.append(
            {"request": _normalize_request(item["request"]), "expected": {"status": status}}
        )
    return {"findings": findings, "verification": verification}


def _model_labels(value: Any) -> set[str]:
    labels: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"model", "model_name", "effective_model"} and isinstance(child, str):
                labels.add(child)
            else:
                labels.update(_model_labels(child))
    elif isinstance(value, list):
        for child in value:
            labels.update(_model_labels(child))
    return labels


def _parse_event_stream(text: str, requested_model: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    malformed = False
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed = True
            continue
        if not isinstance(event, dict):
            malformed = True
            continue
        events.append(event)

    unknown_event_types: set[str] = set()
    unknown_item_types: set[str] = set()
    tool_attempts: set[tuple[str, str]] = set()
    terminal_completed = False
    terminal_failed = False
    stream_error = False
    item_error_count = 0
    usage: dict[str, Any] | None = None
    observed_labels: set[str] = set()

    event_types = [event.get("type") for event in events]
    thread_start_indexes = [
        index for index, event_type in enumerate(event_types) if event_type == "thread.started"
    ]
    turn_start_indexes = [
        index for index, event_type in enumerate(event_types) if event_type == "turn.started"
    ]
    terminal_indexes = [
        index
        for index, event_type in enumerate(event_types)
        if event_type in {"turn.completed", "turn.failed"}
    ]
    lifecycle_errors: list[str] = []
    if len(thread_start_indexes) != 1:
        lifecycle_errors.append("expected exactly one thread.started event")
    if len(turn_start_indexes) != 1:
        lifecycle_errors.append("expected exactly one turn.started event")
    if len(terminal_indexes) != 1:
        lifecycle_errors.append("expected exactly one terminal turn event")
    if thread_start_indexes and thread_start_indexes[0] != 0:
        lifecycle_errors.append("thread.started must be the first event")
    if thread_start_indexes and turn_start_indexes and thread_start_indexes[0] >= turn_start_indexes[0]:
        lifecycle_errors.append("turn.started must follow thread.started")
    if turn_start_indexes and terminal_indexes and turn_start_indexes[0] >= terminal_indexes[0]:
        lifecycle_errors.append("terminal turn event must follow turn.started")
    if terminal_indexes and terminal_indexes[-1] != len(events) - 1:
        lifecycle_errors.append("terminal turn event must be the final event")
    if turn_start_indexes and terminal_indexes:
        turn_start_index = turn_start_indexes[0]
        terminal_index = terminal_indexes[0]
        for index, event_type in enumerate(event_types):
            if event_type in {"item.started", "item.completed"} and not (
                turn_start_index < index < terminal_index
            ):
                lifecycle_errors.append("item events must occur between turn start and terminal")
                break

    for index, event in enumerate(events):
        event_type = event.get("type")
        if not isinstance(event_type, str) or event_type not in ALLOWED_EVENT_TYPES:
            unknown_event_types.add(str(event_type))
        observed_labels.update(_model_labels(event))
        if event_type in {"item.started", "item.completed"}:
            item = event.get("item")
            if not isinstance(item, dict):
                unknown_item_types.add("missing_item")
                continue
            item_type = item.get("type")
            if item_type == "error":
                item_error_count += 1
            elif item_type not in ALLOWED_ITEM_TYPES:
                item_type_text = str(item_type)
                unknown_item_types.add(item_type_text)
                item_id = item.get("id")
                tool_attempts.add((str(item_id) if item_id is not None else f"event-{index}", item_type_text))
        elif event_type == "turn.completed":
            terminal_completed = True
            if isinstance(event.get("usage"), dict):
                usage = event["usage"]
        elif event_type == "turn.failed":
            terminal_failed = True
        elif event_type == "error":
            stream_error = True

    terminal_event_seen = bool(terminal_indexes)
    lifecycle_valid = not lifecycle_errors
    event_stream_complete = (
        not malformed
        and not unknown_event_types
        and not unknown_item_types
        and lifecycle_valid
    )
    telemetry_status = "complete" if event_stream_complete else ("partial" if events else "unobserved")
    effective_model_label = next(iter(observed_labels)) if len(observed_labels) == 1 else None
    model_label_verified: bool | None
    if not observed_labels:
        model_label_verified = None
        model_identity_status = "requested_only_unverified"
    elif observed_labels == {requested_model}:
        model_label_verified = True
        model_identity_status = "verified"
    else:
        model_label_verified = False
        model_identity_status = "mismatch_or_ambiguous"
    return {
        "events": events,
        "event_count": len(events),
        "event_stream_malformed": malformed,
        "event_stream_complete": event_stream_complete,
        "lifecycle_valid": lifecycle_valid,
        "lifecycle_errors": lifecycle_errors,
        "terminal_event_seen": terminal_event_seen,
        "terminal_completed": terminal_completed,
        "terminal_failed": terminal_failed,
        "stream_error": stream_error,
        "item_error_count": item_error_count,
        "unknown_event_types": sorted(unknown_event_types),
        "unknown_item_types": sorted(unknown_item_types),
        "tool_attempt_telemetry_status": telemetry_status,
        "tool_attempt_count": len(tool_attempts),
        "tool_attempt_types": sorted({item_type for _item_id, item_type in tool_attempts}),
        "effective_model_label": effective_model_label,
        "model_label_verified": model_label_verified,
        "model_identity_status": model_identity_status,
        "observed_model_labels": sorted(observed_labels),
        "usage": usage,
    }


def _command(
    codex_path: str,
    model: str,
    effort: str,
    workdir: Path,
    schema_path: Path,
    final_path: Path,
) -> list[str]:
    command = [
        codex_path,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(final_path),
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{effort}"',
        "--config",
        'approval_policy="never"',
        "--cd",
        str(workdir),
    ]
    for feature in DISABLED_FEATURES:
        command.extend(["--disable", feature])
    command.append("-")
    return command


def run_codex(
    context: dict[str, Any],
    model: str,
    effort: str,
    timeout_seconds: int,
    *,
    codex_path: str = "codex",
    codex_cli_version: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    prompt = _prompt(context)
    schema_text = json.dumps(MODEL_OUTPUT_SCHEMA, indent=2, sort_keys=True) + "\n"
    provenance = {
        "adapter_name": "codex-cli-no-tools-v1",
        "cli_name": "codex",
        "cli_version": codex_cli_version,
        "model": model,
        "requested_model": model,
        "requested_effort": effort,
        "model_selection_evidence": "explicit_codex_cli_model_and_reasoning_effort_options",
        "prompt_sha256": _sha256_text(prompt),
        "prompt_hash_scope": PROMPT_HASH_SCOPE,
        "profile_skill_loading_status": PROFILE_SKILL_LOADING_STATUS,
        "output_schema_sha256": _sha256_text(schema_text),
        "command": (
            "codex exec <isolated no-tools flags> --model <model> "
            "--config model_reasoning_effort=<effort> -"
        ),
        "events_file": "codex-events.jsonl",
        "stderr_file": "codex-stderr.txt",
    }
    with tempfile.TemporaryDirectory(prefix="authzbench-codex-") as tmp:
        workdir = Path(tmp)
        schema_path = workdir / "submission.schema.json"
        final_path = workdir / "final.json"
        schema_path.write_text(schema_text, encoding="utf-8")
        command = _command(codex_path, model, effort, workdir, schema_path, final_path)
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                cwd=workdir,
            )
        except subprocess.TimeoutExpired as exc:
            events_text = _subprocess_text(exc.stdout)
            stderr_text = _subprocess_text(exc.stderr)
            telemetry = _parse_event_stream(events_text, model)
            return None, {
                **provenance,
                **{key: value for key, value in telemetry.items() if key != "events"},
                "returncode": 124,
                "codex_cli_returncode": None,
                "events_sha256": _sha256_text(events_text),
                "stderr_sha256": _sha256_text(stderr_text),
                "parse_error": "codex command timed out",
                "_events_text": events_text,
                "_stderr_text": stderr_text,
            }

        events_text = completed.stdout
        stderr_text = completed.stderr
        telemetry = _parse_event_stream(events_text, model)
        metadata = {
            **provenance,
            **{key: value for key, value in telemetry.items() if key != "events"},
            "returncode": completed.returncode,
            "codex_cli_returncode": completed.returncode,
            "events_sha256": _sha256_text(events_text),
            "stderr_sha256": _sha256_text(stderr_text),
            "_events_text": events_text,
            "_stderr_text": stderr_text,
        }
        global_blocker = _global_blocker_code(events_text, stderr_text)
        if global_blocker:
            metadata["global_blocker"] = global_blocker
        if completed.returncode != 0:
            return None, metadata | {"parse_error": "codex command failed"}
        policy_errors = []
        if not telemetry["event_stream_complete"]:
            policy_errors.append("event stream was incomplete or contained unknown events")
        if not telemetry["terminal_completed"] or telemetry["terminal_failed"] or telemetry["stream_error"]:
            policy_errors.append("codex turn did not complete successfully")
        if telemetry["tool_attempt_count"]:
            policy_errors.append("model attempted a disabled tool")
        if telemetry["model_label_verified"] is False:
            policy_errors.append("observed model label did not match the requested model")
        if policy_errors:
            return None, metadata | {
                "returncode": 3,
                "parse_error": "; ".join(policy_errors),
            }
        if not final_path.is_file():
            return None, metadata | {"parse_error": "codex did not write the structured final response"}
        try:
            raw_submission = json.loads(final_path.read_text(encoding="utf-8"))
            submission = _normalize_submission(raw_submission)
        except Exception as exc:  # noqa: BLE001 - preserve fail-closed normalization evidence.
            return None, metadata | {"parse_error": f"invalid structured model output: {exc}"}
        return submission, metadata | {
            "output_format": "structured_json",
            "json_only_compliant": True,
        }


def _write_adapter_result(
    submission_path: Path,
    submission: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> int:
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(metadata)
    events_text = str(metadata.pop("_events_text", ""))
    stderr_text = str(metadata.pop("_stderr_text", ""))
    (submission_path.parent / "codex-events.jsonl").write_text(events_text, encoding="utf-8")
    (submission_path.parent / "codex-stderr.txt").write_text(stderr_text, encoding="utf-8")
    (submission_path.parent / "model-output.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if submission is None:
        submission_path.unlink(missing_ok=True)
        return 2
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex CLI no-tools baseline adapter for AuthZBench-SaaS.")
    parser.add_argument("--model", default=os.environ.get("AUTHZBENCH_CODEX_MODEL", "gpt-5.4-mini"))
    parser.add_argument("--effort", default=os.environ.get("AUTHZBENCH_CODEX_EFFORT", "low"))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--codex-path", default=os.environ.get("AUTHZBENCH_CODEX_PATH", "codex"))
    args = parser.parse_args()

    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    blocker_path = submission_path.parent.parent / "codex-global-blocker.json"
    blocker = None
    if blocker_path.is_file():
        try:
            blocker_data = json.loads(blocker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            blocker_data = None
        if isinstance(blocker_data, dict) and blocker_data.get("code") == "codex_workspace_out_of_credits":
            blocker = "codex_workspace_out_of_credits"
    if blocker:
        submission = None
        metadata = {
            "adapter_name": "codex-cli-no-tools-v1",
            "cli_name": "codex",
            "cli_version": _codex_cli_version(args.codex_path),
            "model": args.model,
            "requested_model": args.model,
            "requested_effort": args.effort,
            "returncode": 75,
            "codex_cli_returncode": None,
            "global_blocker": blocker,
            "event_count": 0,
            "event_stream_complete": False,
            "terminal_event_seen": False,
            "tool_attempt_telemetry_status": "unobserved",
            "tool_attempt_count": None,
            "model_label_verified": None,
            "model_identity_status": "requested_only_unverified",
            "prompt_hash_scope": PROMPT_HASH_SCOPE,
            "profile_skill_loading_status": PROFILE_SKILL_LOADING_STATUS,
            "parse_error": "codex execution skipped after a run-level workspace credit blocker",
            "_events_text": "",
            "_stderr_text": "",
        }
    else:
        submission, metadata = run_codex(
            context,
            args.model,
            args.effort,
            args.timeout_seconds,
            codex_path=args.codex_path,
            codex_cli_version=_codex_cli_version(args.codex_path),
        )
        if metadata.get("global_blocker") == "codex_workspace_out_of_credits":
            blocker_path.write_text(
                json.dumps({"code": "codex_workspace_out_of_credits"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    return _write_adapter_result(submission_path, submission, metadata)


if __name__ == "__main__":
    raise SystemExit(main())
