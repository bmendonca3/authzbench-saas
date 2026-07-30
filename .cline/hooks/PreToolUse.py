#!/usr/bin/env python3
"""Defense-in-depth PreToolUse policy for the Qwen/Cline executor harness.

Cline 3.0.47 continues when a hook crashes, times out, or emits malformed
output. The outer OS sandbox and post-run manifest are therefore the enforcing
controls; this hook supplies fast cancellation and an independently-audited
tool ledger.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


POLICY_ENV = "QWEN_HARNESS_POLICY"
AUDIT_ENV = "QWEN_HARNESS_AUDIT"
REQUIRED_ENV = "QWEN_HARNESS_REQUIRED"
MAX_INPUT_BYTES = 2 * 1024 * 1024
PATH_KEYS = {
    "path",
    "file",
    "filepath",
    "file_path",
    "target_path",
    "source_path",
    "destination_path",
}
READ_PATH_TOOLS = {"read_files", "list_files", "list_code_definition_names"}
WRITE_PATH_TOOLS = {
    "editor",
    "write_to_file",
    "replace_in_file",
    "apply_patch",
}


class PolicyDenied(Exception):
    """Raised when a tool call violates the executor policy."""


def _emit(output: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(output, separators=(",", ":")) + "\n")


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PolicyDenied("harness policy must be a JSON object")
    return data


def _iter_path_values(value: Any, key: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            normalized_key = str(child_key).replace("-", "_").lower()
            if normalized_key in PATH_KEYS and isinstance(child_value, str):
                yield child_value
            elif normalized_key in {"files", "paths", "file_paths"} and isinstance(
                child_value, list
            ):
                for item in child_value:
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, dict) and isinstance(item.get("path"), str):
                        yield item["path"]
            else:
                yield from _iter_path_values(child_value, normalized_key)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_path_values(item, key)


def _matches_pattern(relative_path: str, pattern: str) -> bool:
    clean_pattern = pattern.strip().replace("\\", "/").strip("/")
    if not clean_pattern:
        return False
    if not any(character in clean_pattern for character in "*?["):
        return relative_path == clean_pattern or relative_path.startswith(clean_pattern + "/")
    return fnmatch.fnmatchcase(relative_path, clean_pattern)


def _relative_workspace_path(raw_path: str, workspace_root: Path) -> str:
    if "\x00" in raw_path:
        raise PolicyDenied("path contains a NUL byte")
    candidate_text = raw_path.strip()
    if not candidate_text:
        raise PolicyDenied("empty path is not allowed")
    candidate = Path(candidate_text)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    resolved = candidate.resolve(strict=False)
    if resolved != workspace_root and workspace_root not in resolved.parents:
        raise PolicyDenied("path resolves outside the disposable workspace")
    return resolved.relative_to(workspace_root).as_posix()


def _validate_path(
    raw_path: str,
    *,
    workspace_root: Path,
    denied_patterns: list[str],
    allowed_read_patterns: list[str],
    allowed_write_paths: set[str],
    write: bool,
) -> str:
    relative_path = _relative_workspace_path(raw_path, workspace_root)
    if any(_matches_pattern(relative_path, pattern) for pattern in denied_patterns):
        raise PolicyDenied("path is denied by the harness contract")
    if write:
        if relative_path not in allowed_write_paths:
            raise PolicyDenied("write path is not in the exact write allowlist")
    elif not any(_matches_pattern(relative_path, pattern) for pattern in allowed_read_patterns):
        raise PolicyDenied("read path is not in the read allowlist")
    return relative_path


def _commands_from_input(tool_input: Any) -> list[str]:
    if not isinstance(tool_input, dict):
        raise PolicyDenied("command tool input must be an object")
    commands = tool_input.get("commands")
    if isinstance(commands, list) and all(isinstance(command, str) for command in commands):
        return commands
    command = tool_input.get("command")
    if isinstance(command, str):
        return [command]
    raise PolicyDenied("command tool input does not contain string commands")


def _tool_call(payload: dict[str, Any]) -> tuple[str, str, Any]:
    call = payload.get("tool_call")
    if isinstance(call, dict) and isinstance(call.get("name"), str):
        return str(call.get("id", "")), call["name"], call.get("input")
    pre_tool = payload.get("preToolUse")
    if isinstance(pre_tool, dict) and isinstance(pre_tool.get("toolName"), str):
        return "", pre_tool["toolName"], pre_tool.get("parameters", {})
    raise PolicyDenied("hook payload does not contain a tool call")


def _audit(
    audit_path: Path,
    *,
    call_id: str,
    tool_name: str,
    allowed: bool,
    reason: str,
    paths: list[str],
    commands: list[str],
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "call_id": call_id,
        "tool": tool_name,
        "allowed": allowed,
        "reason": reason,
        "paths": paths,
        "command_fingerprints": [
            {
                "sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
                "length": len(command),
            }
            for command in commands
        ],
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    policy_value = os.environ.get(POLICY_ENV, "").strip()
    if not policy_value:
        if os.environ.get(REQUIRED_ENV, "").strip() == "1":
            _emit(
                {
                    "cancel": True,
                    "errorMessage": "required Qwen harness policy is missing",
                    "contextModification": "Stop: the executor harness policy is unavailable.",
                }
            )
        else:
            _emit({})
        return 0

    audit_value = os.environ.get(AUDIT_ENV, "").strip()
    call_id = ""
    tool_name = "unknown"
    paths: list[str] = []
    commands: list[str] = []
    try:
        raw_payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw_payload) > MAX_INPUT_BYTES:
            raise PolicyDenied("hook payload exceeds the size limit")
        payload = json.loads(raw_payload.decode("utf-8"))
        if not isinstance(payload, dict):
            raise PolicyDenied("hook payload must be a JSON object")
        policy = _load_json(Path(policy_value).resolve(strict=True))
        if policy.get("schema_version") != "qwen-cline-tool-policy-v1":
            raise PolicyDenied("unsupported harness policy schema")
        workspace_root = Path(str(policy["workspace_root"])).resolve(strict=True)
        payload_roots = payload.get("workspaceRoots")
        if isinstance(payload_roots, list) and payload_roots:
            resolved_roots = {
                Path(str(item)).resolve(strict=False)
                for item in payload_roots
                if isinstance(item, str)
            }
            if resolved_roots != {workspace_root}:
                raise PolicyDenied("hook workspace roots do not match the disposable workspace")
        call_id, tool_name, tool_input = _tool_call(payload)

        allowed_tools = {str(item) for item in policy.get("allowed_tools", [])}
        if tool_name not in allowed_tools:
            raise PolicyDenied("tool is not in the harness allowlist")

        denied_patterns = [str(item) for item in policy.get("denied_paths", [])]
        read_patterns = [str(item) for item in policy.get("allowed_read_paths", [])]
        write_paths = {str(item) for item in policy.get("allowed_write_paths", [])}

        if tool_name in READ_PATH_TOOLS:
            raw_paths = list(_iter_path_values(tool_input))
            if not raw_paths:
                raise PolicyDenied("read tool did not provide an inspectable path")
            paths = [
                _validate_path(
                    raw_path,
                    workspace_root=workspace_root,
                    denied_patterns=denied_patterns,
                    allowed_read_patterns=read_patterns,
                    allowed_write_paths=write_paths,
                    write=False,
                )
                for raw_path in raw_paths
            ]
        elif tool_name in WRITE_PATH_TOOLS:
            raw_paths = list(_iter_path_values(tool_input))
            if not raw_paths:
                raise PolicyDenied("write tool did not provide an inspectable path")
            paths = [
                _validate_path(
                    raw_path,
                    workspace_root=workspace_root,
                    denied_patterns=denied_patterns,
                    allowed_read_patterns=read_patterns,
                    allowed_write_paths=write_paths,
                    write=True,
                )
                for raw_path in raw_paths
            ]
        elif tool_name == "run_commands":
            commands = _commands_from_input(tool_input)
            allowed_commands = {str(item) for item in policy.get("allowed_commands", [])}
            if any(command not in allowed_commands for command in commands):
                raise PolicyDenied("command is not listed exactly in the harness contract")
        elif tool_name not in {"submit_and_exit"}:
            raise PolicyDenied("allowed tool has no policy validator")

        if not audit_value:
            raise PolicyDenied("hook audit path is not configured")
        _audit(
            Path(audit_value),
            call_id=call_id,
            tool_name=tool_name,
            allowed=True,
            reason="allowed",
            paths=paths,
            commands=commands,
        )
        _emit({})
        return 0
    except Exception as exc:
        reason = str(exc) if isinstance(exc, PolicyDenied) else "hook policy evaluation failed"
        if audit_value:
            try:
                _audit(
                    Path(audit_value),
                    call_id=call_id,
                    tool_name=tool_name,
                    allowed=False,
                    reason=reason,
                    paths=paths,
                    commands=commands,
                )
            except Exception:
                reason = "hook policy evaluation and audit both failed"
        _emit(
            {
                "cancel": True,
                "errorMessage": reason,
                "contextModification": (
                    "The Qwen harness denied this tool call. Stop and report the exact missing "
                    "grant; do not retry through another tool or encoding."
                ),
            }
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
