#!/usr/bin/env python3
"""Run Qwen 3.8 Max Preview as a bounded, observable Cline executor.

The model receives only explicitly hashed public inputs in a disposable
workspace. Cline runs under macOS sandbox-exec with a sanitized environment,
loopback-only provider access, an audited PreToolUse hook, exact writable
files, and a post-run manifest. Accepted output is exported as a candidate
patch and is never applied to the canonical checkout.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import difflib
import hashlib
import http.server
import json
import os
import platform
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
HOOK_SOURCE = ROOT / ".cline" / "hooks" / "PreToolUse.py"
RUNTIME_PIN_PATH = ROOT / ".cline" / "qwen-runtime-pin.json"
CONTRACT_SCHEMA = "qwen-cline-task-v1"
POLICY_SCHEMA = "qwen-cline-tool-policy-v1"
ALLOWED_TOOLS = ("read_files", "editor", "submit_and_exit")
MAX_INPUT_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_INPUT_BYTES = 32 * 1024 * 1024
MAX_PROMPT_CHARS = 20_000
CREATE_FILE_SENTINEL = "<!-- QWEN_HARNESS_CREATE_FILE: replace this entire line -->"
TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DENIED_COMPONENTS = {
    ".agents",
    ".claude",
    ".git",
    ".handoff",
    ".kiro",
    ".pytest_cache",
    "__pycache__",
    "browser_state",
    "cache",
    "caches",
    "captures",
    "results",
    "tasks_private",
}
RESERVED_TOP_LEVEL = {"AGENTS.md", ".cline"}
KNOWN_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "source_commit",
    "task",
    "packet_path",
    "input_files",
    "create_files",
    "write_files",
    "required_change_files",
    "expected_output_sha256",
    "verification_commands",
    "model",
    "thinking",
    "retries",
    "timeout_seconds",
}


class HarnessError(RuntimeError):
    """A fail-closed harness validation or execution error."""


@dataclasses.dataclass(frozen=True)
class RuntimePin:
    platform: str
    machine: str
    cline_version: str
    cline_binary_sha256: str
    provider: str
    model: str
    thinking: str
    bridge_base_url: str
    bridge_health_url: str
    bridge_host: str
    bridge_port: int


@dataclasses.dataclass(frozen=True)
class TaskContract:
    task_id: str
    source_commit: str
    task: str
    packet_path: str
    input_files: dict[str, str]
    create_files: tuple[str, ...]
    write_files: tuple[str, ...]
    required_change_files: tuple[str, ...]
    verification_commands: tuple[tuple[str, ...], ...]
    model: str
    thinking: str
    retries: int
    timeout_seconds: int
    expected_output_sha256: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class FileRecord:
    kind: str
    mode: int
    size: int = 0
    sha256: str = ""


@dataclasses.dataclass
class StreamLedger:
    terminal_results: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    tool_calls: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    tool_violations: list[str] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    malformed_json_lines: list[int] = dataclasses.field(default_factory=list)
    abort_events: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    event_counts: dict[str, int] = dataclasses.field(default_factory=dict)
    tool_failures: list[str] = dataclasses.field(default_factory=list)
    tool_failure_counts: dict[str, int] = dataclasses.field(default_factory=dict)
    stop_reason: str | None = None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError(f"{path} must contain a JSON object")
    return value


def load_runtime_pin(path: Path = RUNTIME_PIN_PATH) -> RuntimePin:
    data = _read_json_object(path)
    if data.get("schema_version") != "qwen-cline-runtime-pin-v1":
        raise HarnessError("unsupported Qwen/Cline runtime pin schema")
    try:
        pin = RuntimePin(
            platform=str(data["platform"]),
            machine=str(data["machine"]),
            cline_version=str(data["cline_version"]),
            cline_binary_sha256=str(data["cline_binary_sha256"]),
            provider=str(data["provider"]),
            model=str(data["model"]),
            thinking=str(data["thinking"]),
            bridge_base_url=str(data["bridge_base_url"]),
            bridge_health_url=str(data["bridge_health_url"]),
            bridge_host=str(data["bridge_host"]),
            bridge_port=int(data["bridge_port"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HarnessError(f"invalid runtime pin: {exc}") from exc
    if not SHA256_RE.fullmatch(pin.cline_binary_sha256):
        raise HarnessError("runtime pin has an invalid Cline binary SHA-256")
    if pin.model != "qwen3.8-max-preview":
        raise HarnessError("runtime pin must use exact model qwen3.8-max-preview")
    if pin.thinking != "xhigh":
        raise HarnessError("runtime pin must use xhigh thinking")
    if pin.bridge_host not in {"127.0.0.1", "localhost"} or pin.bridge_port != 8790:
        raise HarnessError("runtime pin must use the approved loopback bridge on port 8790")
    return pin


def validate_relative_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw:
        raise HarnessError("contract paths must be non-empty strings")
    if raw != unicodedata.normalize("NFC", raw):
        raise HarnessError(f"path is not NFC-normalized: {raw!r}")
    if "\\" in raw or "\x00" in raw or any(ord(char) < 32 for char in raw):
        raise HarnessError(f"path contains a forbidden character: {raw!r}")
    candidate = Path(raw)
    if candidate.is_absolute() or raw.startswith("/") or raw.endswith("/"):
        raise HarnessError(f"path must be relative and name a file: {raw!r}")
    parts = candidate.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise HarnessError(f"path traversal or empty component is forbidden: {raw!r}")
    if candidate.as_posix() != raw:
        raise HarnessError(f"path is not in canonical POSIX form: {raw!r}")
    if parts[0] in RESERVED_TOP_LEVEL:
        raise HarnessError(f"path is reserved for harness controls: {raw!r}")
    if any(part.casefold() in DENIED_COMPONENTS for part in parts):
        raise HarnessError(f"path uses a denied component: {raw!r}")
    if any(part.casefold().startswith(".env") for part in parts):
        raise HarnessError(f"environment files are forbidden: {raw!r}")
    return raw


def _string_list(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise HarnessError(f"{key} must be an array")
    return tuple(validate_relative_path(item) for item in value)


def _verification_commands(value: Any) -> tuple[tuple[str, ...], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise HarnessError("verification_commands must be an array of argv arrays")
    commands: list[tuple[str, ...]] = []
    for index, command in enumerate(value):
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(arg, str) and arg and "\x00" not in arg for arg in command)
        ):
            raise HarnessError(
                f"verification_commands[{index}] must be a non-empty string argv array"
            )
        commands.append(tuple(command))
    return tuple(commands)


def validate_contract_data(data: dict[str, Any], pin: RuntimePin) -> TaskContract:
    extra = sorted(set(data) - KNOWN_CONTRACT_KEYS)
    if extra:
        raise HarnessError(f"unknown contract keys: {', '.join(extra)}")
    if data.get("schema_version") != CONTRACT_SCHEMA:
        raise HarnessError(f"schema_version must be {CONTRACT_SCHEMA}")
    task_id = data.get("task_id")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise HarnessError("task_id must be a lowercase safe identifier")
    source_commit = data.get("source_commit")
    if not isinstance(source_commit, str) or not COMMIT_RE.fullmatch(source_commit):
        raise HarnessError("source_commit must be a lowercase 40-character Git SHA")
    task = data.get("task")
    if not isinstance(task, str) or not task.strip() or len(task) > MAX_PROMPT_CHARS:
        raise HarnessError(f"task must contain 1-{MAX_PROMPT_CHARS} characters")
    packet_path = validate_relative_path(data.get("packet_path"))
    raw_inputs = data.get("input_files")
    if not isinstance(raw_inputs, dict) or not raw_inputs:
        raise HarnessError("input_files must be a non-empty path-to-SHA-256 object")
    input_files: dict[str, str] = {}
    for raw_path, raw_digest in raw_inputs.items():
        path = validate_relative_path(raw_path)
        if not isinstance(raw_digest, str) or not SHA256_RE.fullmatch(raw_digest):
            raise HarnessError(f"input_files[{path!r}] must be a lowercase SHA-256")
        input_files[path] = raw_digest
    create_files = _string_list(data, "create_files")
    write_files = _string_list(data, "write_files")
    required_change_files = _string_list(data, "required_change_files")
    raw_expected_outputs = data.get("expected_output_sha256", {})
    if not isinstance(raw_expected_outputs, dict):
        raise HarnessError("expected_output_sha256 must be a path-to-SHA-256 object")
    expected_output_sha256: dict[str, str] = {}
    for raw_path, raw_digest in raw_expected_outputs.items():
        path = validate_relative_path(raw_path)
        if not isinstance(raw_digest, str) or not SHA256_RE.fullmatch(raw_digest):
            raise HarnessError(f"expected_output_sha256[{path!r}] must be a lowercase SHA-256")
        expected_output_sha256[path] = raw_digest
    all_declared = list(input_files) + list(create_files)
    folded: dict[str, str] = {}
    for path in all_declared:
        key = unicodedata.normalize("NFC", path).casefold()
        if key in folded:
            raise HarnessError(f"case/Unicode-colliding paths: {folded[key]!r} and {path!r}")
        folded[key] = path
    if len(set(create_files)) != len(create_files):
        raise HarnessError("create_files contains duplicates")
    if len(set(write_files)) != len(write_files):
        raise HarnessError("write_files contains duplicates")
    if len(set(required_change_files)) != len(required_change_files):
        raise HarnessError("required_change_files contains duplicates")
    if set(input_files) & set(create_files):
        raise HarnessError("a file cannot be both an input and a create file")
    materialized = set(input_files) | set(create_files)
    if packet_path not in input_files:
        raise HarnessError("packet_path must be a hashed input file")
    if not write_files or not set(write_files) <= materialized:
        raise HarnessError("write_files must be a non-empty subset of materialized files")
    if not set(required_change_files) <= set(write_files):
        raise HarnessError("required_change_files must be a subset of write_files")
    if not set(expected_output_sha256) <= set(write_files):
        raise HarnessError("expected_output_sha256 paths must be a subset of write_files")
    model = data.get("model", pin.model)
    thinking = data.get("thinking", pin.thinking)
    retries = data.get("retries", 3)
    timeout_seconds = data.get("timeout_seconds", 0)
    if model != pin.model:
        raise HarnessError(f"model must be exact runtime pin {pin.model}")
    if thinking != pin.thinking:
        raise HarnessError(f"thinking must be exact runtime pin {pin.thinking}")
    if not isinstance(retries, int) or isinstance(retries, bool) or not 1 <= retries <= 6:
        raise HarnessError("retries must be an integer from 1 through 6")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or not 0 <= timeout_seconds <= 86_400
    ):
        raise HarnessError("timeout_seconds must be 0 through 86400")
    return TaskContract(
        task_id=task_id,
        source_commit=source_commit,
        task=task.strip(),
        packet_path=packet_path,
        input_files=input_files,
        create_files=create_files,
        write_files=write_files,
        required_change_files=required_change_files,
        verification_commands=_verification_commands(data.get("verification_commands")),
        model=model,
        thinking=thinking,
        retries=retries,
        timeout_seconds=timeout_seconds,
        expected_output_sha256=expected_output_sha256,
    )


def load_contract(path: Path, pin: RuntimePin) -> TaskContract:
    return validate_contract_data(_read_json_object(path), pin)


def _git_output(source_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(source_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise HarnessError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def source_state_fingerprint(source_root: Path) -> str:
    head = _git_output(source_root, "rev-parse", "HEAD").strip()
    status = _git_output(
        source_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    return sha256_bytes(head + b"\0" + status)


def _assert_regular_source_file(source_root: Path, relative: str, expected_hash: str) -> Path:
    source_root = source_root.resolve(strict=True)
    current = source_root
    for part in Path(relative).parts:
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:
            raise HarnessError(f"declared input is unavailable: {relative}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise HarnessError(f"symlink components are forbidden: {relative}")
    info = current.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise HarnessError(f"declared input is not a regular file: {relative}")
    if info.st_nlink != 1:
        raise HarnessError(f"hardlinked inputs are forbidden: {relative}")
    if info.st_size > MAX_INPUT_FILE_BYTES:
        raise HarnessError(f"declared input exceeds {MAX_INPUT_FILE_BYTES} bytes: {relative}")
    try:
        current.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HarnessError(f"declared input must be readable UTF-8 text: {relative}") from exc
    actual_hash = sha256_file(current)
    if actual_hash != expected_hash:
        raise HarnessError(
            f"declared input hash drifted: {relative} expected {expected_hash}, got {actual_hash}"
        )
    return current


def verify_source_contract(source_root: Path, contract: TaskContract) -> None:
    head = _git_output(source_root, "rev-parse", "HEAD").decode().strip()
    if head != contract.source_commit:
        raise HarnessError(
            f"source_commit drifted: contract {contract.source_commit}, current {head}"
        )
    total = 0
    for relative, digest in contract.input_files.items():
        source = _assert_regular_source_file(source_root, relative, digest)
        total += source.stat().st_size
    if total > MAX_TOTAL_INPUT_BYTES:
        raise HarnessError(f"declared inputs exceed {MAX_TOTAL_INPUT_BYTES} total bytes")
    for relative in contract.create_files:
        candidate = source_root / relative
        if candidate.exists() or candidate.is_symlink():
            raise HarnessError(f"create file already exists in the source checkout: {relative}")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_contract_rule(contract: TaskContract) -> str:
    reads = "\n".join(f"- `{path}`" for path in contract.input_files)
    writes = "\n".join(f"- `{path}`" for path in contract.write_files)
    required = "\n".join(f"- `{path}`" for path in contract.required_change_files) or "- none"
    creates = "\n".join(f"- `{path}`" for path in contract.create_files) or "- none"
    expected = (
        "\n".join(
            f"- `{path}` must have SHA-256 `{digest}`"
            for path, digest in contract.expected_output_sha256.items()
        )
        or "- none"
    )
    return (
        "# Generated Qwen Executor Contract\n\n"
        "This rule is generated by the parent harness. It is not authority to broaden scope.\n\n"
        f"- Task ID: `{contract.task_id}`\n"
        f"- Frozen source commit: `{contract.source_commit}`\n"
        f"- Packet: `{contract.packet_path}`\n"
        f"- Model: `{contract.model}`\n"
        f"- Thinking: `{contract.thinking}`\n\n"
        "## Exact readable task files\n\n"
        f"{reads}\n\n"
        "The harness control files `AGENTS.md` and this rule are also readable.\n\n"
        "## Exact writable files\n\n"
        f"{writes}\n\n"
        "## Predeclared new files\n\n"
        f"{creates}\n\n"
        "Predeclared new files contain this exact temporary marker:\n\n"
        f"`{CREATE_FILE_SENTINEL.strip()}`\n\n"
        "Replace the complete marker line with the requested content; do not use "
        "`insert_line` on it.\n\n"
        "## Files that must change\n\n"
        f"{required}\n\n"
        "## Exact expected output hashes\n\n"
        f"{expected}\n\n"
        "Only `read_files`, `editor`, and `submit_and_exit` are admitted. Do not use "
        "search, shell, web, skills, MCP, plugins, subagents, teams, Git, or any "
        "other tool. Read the packet and named inputs, make the smallest exact edit, "
        "then submit a concise result.\n"
    )


def materialize_workspace(
    source_root: Path,
    contract: TaskContract,
    evidence_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    workspace = evidence_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    baselines: dict[str, Any] = {}
    for relative, digest in contract.input_files.items():
        source = _assert_regular_source_file(source_root, relative, digest)
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, stat.S_IMODE(source.stat().st_mode) & 0o755)
        baselines[relative] = {
            "source": "canonical-input",
            "sha256": digest,
            "text": destination.read_text(encoding="utf-8"),
        }
    for relative in contract.create_files:
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(CREATE_FILE_SENTINEL, encoding="utf-8")
        os.chmod(destination, 0o644)
        baselines[relative] = {
            "source": "precreated-sentinel",
            "sha256": sha256_bytes(CREATE_FILE_SENTINEL.encode("utf-8")),
            "text": "",
            "workspace_initial_text": CREATE_FILE_SENTINEL,
        }
    agents_destination = workspace / "AGENTS.md"
    hook_destination = workspace / ".cline" / "hooks" / "PreToolUse.py"
    rule_destination = workspace / ".cline" / "rules" / "00-qwen-harness-contract.md"
    agents_destination.write_bytes((source_root / "AGENTS.md").read_bytes())
    hook_destination.parent.mkdir(parents=True, exist_ok=True)
    rule_destination.parent.mkdir(parents=True, exist_ok=True)
    hook_destination.write_bytes(HOOK_SOURCE.read_bytes())
    os.chmod(hook_destination, 0o755)
    rule_destination.write_text(render_contract_rule(contract), encoding="utf-8")
    policy = {
        "schema_version": POLICY_SCHEMA,
        "workspace_root": str(workspace.resolve()),
        "allowed_tools": list(ALLOWED_TOOLS),
        "allowed_read_paths": [
            "AGENTS.md",
            ".cline/rules/00-qwen-harness-contract.md",
            *contract.input_files.keys(),
            *contract.create_files,
        ],
        "allowed_write_paths": list(contract.write_files),
        "allowed_commands": [],
        "denied_paths": [
            "tasks_private/**",
            ".git/**",
            ".agents/**",
            ".env*",
            "**/.env*",
            "**/results/**",
            "**/captures/**",
            "**/cache/**",
            "**/caches/**",
        ],
    }
    policy_path = evidence_dir / "tool-policy.json"
    _write_json(policy_path, policy)
    _write_json(evidence_dir / "baseline-files.json", baselines)
    assert_safe_tree(workspace)
    return workspace, policy_path, baselines


def assert_safe_tree(root: Path) -> None:
    seen: set[tuple[int, int]] = set()
    for current_root, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current_root)
        for name in [*directories, *files]:
            path = current_path / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise HarnessError(f"workspace contains a symlink: {path.relative_to(root)}")
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise HarnessError(f"workspace contains a special file: {path.relative_to(root)}")
            if stat.S_ISREG(info.st_mode):
                key = (info.st_dev, info.st_ino)
                if key in seen or info.st_nlink != 1:
                    raise HarnessError(f"workspace contains a hardlink: {path.relative_to(root)}")
                seen.add(key)


def snapshot_tree(root: Path) -> dict[str, FileRecord]:
    assert_safe_tree(root)
    records: dict[str, FileRecord] = {}
    for current_root, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current_root)
        for name in sorted(directories):
            path = current_path / name
            info = path.lstat()
            records[path.relative_to(root).as_posix()] = FileRecord(
                kind="directory",
                mode=stat.S_IMODE(info.st_mode),
            )
        for name in sorted(files):
            path = current_path / name
            info = path.lstat()
            records[path.relative_to(root).as_posix()] = FileRecord(
                kind="file",
                mode=stat.S_IMODE(info.st_mode),
                size=info.st_size,
                sha256=sha256_file(path),
            )
    return records


def compare_snapshots(
    before: dict[str, FileRecord],
    after: dict[str, FileRecord],
    contract: TaskContract,
) -> tuple[list[str], list[str]]:
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    violations: list[str] = []
    allowed = set(contract.write_files)
    for path in changed:
        previous = before.get(path)
        current = after.get(path)
        if path not in allowed:
            violations.append(f"out-of-scope workspace change: {path}")
            continue
        if previous is None or current is None:
            violations.append(f"allowed file was created/deleted instead of edited in place: {path}")
            continue
        if previous.kind != "file" or current.kind != "file":
            violations.append(f"allowed path is no longer a regular file: {path}")
        if previous.mode != current.mode:
            violations.append(f"allowed file mode changed: {path}")
    for path in contract.required_change_files:
        if path not in changed:
            violations.append(f"required file did not change: {path}")
    return changed, violations


def expected_output_violations(workspace: Path, contract: TaskContract) -> list[str]:
    violations: list[str] = []
    for relative, expected in contract.expected_output_sha256.items():
        path = workspace / relative
        if not path.is_file() or path.is_symlink():
            violations.append(f"expected output is not a regular file: {relative}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            violations.append(
                f"expected output hash mismatch: {relative} expected {expected}, got {actual}"
            )
    return violations


def resolve_cline_binary() -> Path:
    override = os.environ.get("QWEN_HARNESS_CLINE_BIN", "").strip()
    if override:
        return Path(override).expanduser().resolve(strict=True)
    wrapper = shutil.which("cline")
    if not wrapper:
        raise HarnessError("cline is not on PATH")
    resolved_wrapper = Path(wrapper).resolve(strict=True)
    compiled = resolved_wrapper.parent / ".cline"
    if not compiled.is_file():
        raise HarnessError(f"compiled Cline binary not found beside wrapper: {compiled}")
    return compiled.resolve(strict=True)


def verify_runtime(pin: RuntimePin, cline_binary: Path) -> None:
    if platform.system().lower() != pin.platform or platform.machine().lower() != pin.machine:
        raise HarnessError(
            f"runtime platform mismatch: expected {pin.platform}/{pin.machine}, "
            f"got {platform.system().lower()}/{platform.machine().lower()}"
        )
    actual_hash = sha256_file(cline_binary)
    if actual_hash != pin.cline_binary_sha256:
        raise HarnessError(
            f"Cline binary hash mismatch: expected {pin.cline_binary_sha256}, got {actual_hash}"
        )
    result = subprocess.run(
        [str(cline_binary), "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(Path.home())},
    )
    if result.returncode != 0 or result.stdout.strip() != pin.cline_version:
        raise HarnessError(
            f"Cline version mismatch: expected {pin.cline_version}, "
            f"got rc={result.returncode} stdout={result.stdout.strip()!r}"
        )


def check_bridge_health(pin: RuntimePin) -> None:
    request = urllib.request.Request(pin.bridge_health_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            body = response.read(4096)
            status = response.status
    except (OSError, urllib.error.URLError) as exc:
        raise HarnessError(f"Qwen bridge health check failed: {exc}") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HarnessError("Qwen bridge health response is not JSON") from exc
    if status != 200 or not isinstance(payload, dict) or payload.get("status") != "ok":
        raise HarnessError(f"Qwen bridge is unhealthy: HTTP {status}, payload={payload!r}")


def _sandbox_string(value: str) -> str:
    return json.dumps(value)


def build_sandbox_profile(
    *,
    user_home: Path,
    cline_binary: Path,
    workspace: Path,
    state_dir: Path,
    run_home: Path,
    temp_dir: Path,
    policy_path: Path,
    hook_audit_path: Path,
    runtime_hook_log_path: Path,
    write_files: Iterable[Path],
    bridge_port: int,
) -> str:
    lines = [
        "(version 1)",
        "(deny default)",
        "(allow process*)",
        "(allow sysctl-read)",
        "(allow mach-lookup)",
        # macOS/Bun requires metadata traversal and a root-directory read, but
        # file contents remain allowlisted below.
        "(allow file-read-metadata)",
        '(allow file-read-data (literal "/"))',
    ]
    del user_home  # Retained in the API so callers explicitly identify the protected home.
    system_read_subpaths = {
        Path("/System"),
        Path("/usr"),
        Path("/bin"),
        Path("/sbin"),
        Path("/Library"),
        Path("/private/etc"),
        Path("/private/var/db/timezone"),
        Path("/dev"),
    }
    for path in sorted(system_read_subpaths, key=lambda item: str(item)):
        lines.append(f"(allow file-read-data (subpath {_sandbox_string(str(path))}))")
    read_subpaths = {
        cline_binary.parent.resolve(),
        workspace.resolve(),
        state_dir.resolve(),
        run_home.resolve(),
        temp_dir.resolve(),
    }
    for path in sorted(read_subpaths, key=lambda item: str(item)):
        lines.append(f"(allow file-read-data (subpath {_sandbox_string(str(path))}))")
    for path in sorted(
        {policy_path.resolve(), hook_audit_path.resolve(), runtime_hook_log_path.resolve()},
        key=lambda item: str(item),
    ):
        lines.append(f"(allow file-read-data (literal {_sandbox_string(str(path))}))")
    for path in sorted({state_dir.resolve(), run_home.resolve(), temp_dir.resolve()}, key=str):
        lines.append(f"(allow file-write* (subpath {_sandbox_string(str(path))}))")
    for path in sorted({item.resolve(strict=False) for item in write_files}, key=str):
        lines.append(f"(allow file-write* (literal {_sandbox_string(str(path))}))")
    lines.extend(
        [
            f"(allow file-write* (literal {_sandbox_string(str(hook_audit_path.resolve()))}))",
            f"(allow file-write* (literal {_sandbox_string(str(runtime_hook_log_path.resolve()))}))",
            '(allow file-write* (literal "/dev/null"))',
            f'(allow network-outbound (remote tcp "localhost:{bridge_port}"))',
        ]
    )
    return "\n".join(lines) + "\n"


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        return


def sandbox_self_test(
    profile_text: str,
    *,
    workspace: Path,
    outside_sentinel: Path,
    bridge_health_url: str,
) -> dict[str, bool]:
    sandbox_exec = Path("/usr/bin/sandbox-exec")
    if not sandbox_exec.is_file():
        raise HarnessError("macOS sandbox-exec is unavailable; refusing an unsandboxed run")
    allowed_read = subprocess.run(
        [str(sandbox_exec), "-p", profile_text, "/bin/cat", str(workspace / "AGENTS.md")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    denied_read = subprocess.run(
        [str(sandbox_exec), "-p", profile_text, "/bin/cat", str(outside_sentinel)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    original = outside_sentinel.read_bytes()
    denied_write = subprocess.run(
        [
            str(sandbox_exec),
            "-p",
            profile_text,
            "/usr/bin/python3",
            "-c",
            "from pathlib import Path; Path(__import__('sys').argv[1]).write_text('escaped')",
            str(outside_sentinel),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    write_unchanged = outside_sentinel.read_bytes() == original
    allowed_network = subprocess.run(
        [
            str(sandbox_exec),
            "-p",
            profile_text,
            "/usr/bin/curl",
            "--fail",
            "--silent",
            "--max-time",
            "3",
            bridge_health_url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        blocked_network = subprocess.run(
            [
                str(sandbox_exec),
                "-p",
                profile_text,
                "/usr/bin/curl",
                "--silent",
                "--max-time",
                "2",
                f"http://127.0.0.1:{server.server_port}/",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    checks = {
        "workspace_read_allowed": allowed_read.returncode == 0,
        "outside_read_denied": denied_read.returncode != 0,
        "outside_write_denied": denied_write.returncode != 0 and write_unchanged,
        "bridge_network_allowed": allowed_network.returncode == 0,
        "other_loopback_network_denied": blocked_network.returncode != 0,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise HarnessError(f"sandbox self-test failed: {', '.join(failed)}")
    return checks


def hostile_hook_self_test(
    *,
    workspace: Path,
    policy_path: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    audit_path = evidence_dir / "hook-self-test-audit.jsonl"
    payload = {
        "hookName": "tool_call",
        "workspaceRoots": [str(workspace.resolve())],
        "tool_call": {
            "id": "hostile-private-read-probe",
            "name": "read_files",
            "input": {
                "files": [
                    {
                        "path": str(
                            workspace / "tasks_private" / "must-never-be-readable.json"
                        )
                    }
                ]
            },
        },
    }
    environment = {
        "HOME": str(evidence_dir / "home"),
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "QWEN_HARNESS_AUDIT": str(audit_path),
        "QWEN_HARNESS_POLICY": str(policy_path),
        "QWEN_HARNESS_REQUIRED": "1",
    }
    result = subprocess.run(
        [sys.executable, str(workspace / ".cline" / "hooks" / "PreToolUse.py")],
        input=json.dumps(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        check=False,
    )
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HarnessError("hostile hook self-test returned malformed JSON") from exc
    records, errors = read_hook_audit(audit_path)
    passed = (
        result.returncode == 0
        and isinstance(output, dict)
        and output.get("cancel") is True
        and not errors
        and len(records) == 1
        and records[0].get("allowed") is False
        and records[0].get("call_id") == "hostile-private-read-probe"
    )
    summary = {
        "passed": passed,
        "returncode": result.returncode,
        "cancel": output.get("cancel") if isinstance(output, dict) else None,
        "audit_record_count": len(records),
        "audit_errors": errors,
        "stderr_present": bool(result.stderr.strip()),
    }
    _write_json(evidence_dir / "hook-self-test.json", summary)
    if not passed:
        raise HarnessError(f"hostile hook self-test failed: {summary}")
    return summary


def create_state_config(state_dir: Path, pin: RuntimePin) -> None:
    settings = state_dir / "settings"
    settings.mkdir(parents=True, exist_ok=True)
    provider = {
        "version": 1,
        "lastUsedProvider": pin.provider,
        "providers": {
            pin.provider: {
                "settings": {
                    "provider": pin.provider,
                    "apiKey": "qwen-harness-loopback-only",
                    "model": pin.model,
                    "baseUrl": pin.bridge_base_url,
                },
                # Cline 3.0.47's provider manifest requires RFC 3339 UTC with
                # a literal Z; a +00:00 offset makes it discard the profile.
                "updatedAt": dt.datetime.now(dt.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tokenSource": "manual",
            }
        },
    }
    _write_json(settings / "providers.json", provider)
    _write_json(settings / "cline_mcp_settings.json", {"mcpServers": {}})


def _paths_from_tool_input(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            found.extend(_paths_from_tool_input(item))
        return found
    if not isinstance(value, dict):
        return found
    for key, item in value.items():
        normalized = str(key).replace("-", "_").lower()
        if normalized in {
            "path",
            "file",
            "filepath",
            "file_path",
            "target_path",
            "source_path",
            "destination_path",
        } and isinstance(item, str):
            found.append(item)
        elif normalized in {"files", "paths", "file_paths"}:
            found.extend(_paths_from_tool_input(item))
        elif isinstance(item, (dict, list)):
            found.extend(_paths_from_tool_input(item))
    return found


def _relative_tool_path(raw: str, workspace: Path) -> str:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    resolved = candidate.resolve(strict=False)
    resolved_workspace = workspace.resolve(strict=True)
    if resolved != resolved_workspace and resolved_workspace not in resolved.parents:
        raise HarnessError("tool path resolves outside the disposable workspace")
    return resolved.relative_to(resolved_workspace).as_posix()


def validate_stream_tool_call(
    tool_name: Any,
    tool_input: Any,
    workspace: Path,
    contract: TaskContract,
) -> str | None:
    if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
        return f"streamed tool is not admitted: {tool_name!r}"
    if tool_name == "submit_and_exit":
        return None
    paths = _paths_from_tool_input(tool_input)
    if not paths:
        return f"streamed {tool_name} call has no inspectable path"
    admitted_reads = {
        "AGENTS.md",
        ".cline/rules/00-qwen-harness-contract.md",
        *contract.input_files,
        *contract.create_files,
    }
    for raw in paths:
        try:
            relative = _relative_tool_path(raw, workspace)
        except HarnessError as exc:
            return str(exc)
        if tool_name == "read_files" and relative not in admitted_reads:
            return f"streamed read is outside the exact allowlist: {relative}"
        if tool_name == "editor" and relative not in set(contract.write_files):
            return f"streamed write is outside the exact allowlist: {relative}"
    return None


def _event_tool_call(event: dict[str, Any]) -> tuple[str, Any, str] | None:
    if event.get("type") != "agent_event" or not isinstance(event.get("event"), dict):
        return None
    inner = event["event"]
    if inner.get("type") == "content_start" and inner.get("contentType") == "tool":
        return (
            str(inner.get("toolName", "")),
            inner.get("input"),
            str(inner.get("toolCallId", "")),
        )
    return None


def compact_event(event: dict[str, Any]) -> str | None:
    event_type = str(event.get("type", "unknown"))
    if event_type == "agent_event" and isinstance(event.get("event"), dict):
        inner = event["event"]
        inner_type = str(inner.get("type", "unknown"))
        if inner_type in {"iteration_start", "iteration_end"}:
            return f"{inner_type} iteration={inner.get('iteration', '?')}"
        if inner_type == "content_start":
            content_type = inner.get("contentType")
            if content_type == "tool":
                return f"tool_start {inner.get('toolName', '?')} id={inner.get('toolCallId', '?')}"
            # Cline emits reasoning/text token deltas as repeated
            # content_start events. Raw NDJSON retains them; the compact stream
            # waits for content_end so humans see coherent thoughts.
            return None
        if inner_type == "content_end":
            content_type = inner.get("contentType")
            if content_type == "tool":
                suffix = " error" if _tool_event_failed(inner) else " ok"
                return (
                    f"tool_end {inner.get('toolName', '?')} "
                    f"id={inner.get('toolCallId', '?')}{suffix}"
                )
            if content_type == "reasoning":
                text = " ".join(str(inner.get("reasoning", "")).split())
                return f"reasoning {text[:600]}" if text else "reasoning [redacted]"
            if content_type == "text":
                text = " ".join(str(inner.get("text", "")).split())
                return f"text {text[:600]}" if text else None
        if inner_type in {"usage", "done"}:
            return f"{inner_type} {json.dumps(inner, sort_keys=True)[:320]}"
        return None
    if event_type == "run_result":
        observed_model = event.get("model")
        if isinstance(observed_model, dict):
            model_text = f"{observed_model.get('provider')}/{observed_model.get('id')}"
        else:
            model_text = str(observed_model)
        return (
            f"run_result finish={event.get('finishReason')} model={model_text} "
            f"iterations={event.get('iterations')}"
        )
    if event_type in {"run_aborted", "error"}:
        return f"{event_type} {json.dumps(event, sort_keys=True)[:320]}"
    if event_type == "hook_event":
        return f"hook {event.get('hookEventName')} tool={event.get('toolName', '')}".rstrip()
    return None


def _tool_event_failed(inner: dict[str, Any]) -> bool:
    if inner.get("error"):
        return True
    output = inner.get("output")
    if isinstance(output, dict):
        return output.get("success") is False or bool(output.get("error"))
    return False


def _record_tool_failure(ledger: StreamLedger, inner: dict[str, Any]) -> None:
    if not _tool_event_failed(inner):
        return
    call_id = str(inner.get("toolCallId", ""))
    call = ledger.tool_calls.get(call_id, {})
    tool_name = str(call.get("tool") or inner.get("toolName") or "unknown")
    paths = _paths_from_tool_input(call.get("input"))
    key = f"{tool_name}:{'|'.join(sorted(paths))}"
    count = ledger.tool_failure_counts.get(key, 0) + 1
    ledger.tool_failure_counts[key] = count
    ledger.tool_failures.append(f"{call_id or 'unknown'}: {key}")
    if count >= 3 and ledger.stop_reason is None:
        ledger.stop_reason = (
            f"repetition breaker: {tool_name} failed {count} times on the same path set"
        )


def ingest_stream_line(
    line: str,
    line_number: int,
    ledger: StreamLedger,
    workspace: Path,
    contract: TaskContract,
) -> str | None:
    stripped = line.rstrip("\r\n")
    if not stripped:
        return None
    try:
        event = json.loads(stripped)
    except json.JSONDecodeError:
        if stripped.lstrip().startswith(("{", "[")):
            ledger.malformed_json_lines.append(line_number)
            return f"malformed_json line={line_number}"
        ledger.warnings.append(stripped)
        return f"warning {stripped[:240]}"
    if not isinstance(event, dict):
        ledger.malformed_json_lines.append(line_number)
        return f"malformed_json line={line_number}"
    event_type = str(event.get("type", "unknown"))
    ledger.event_counts[event_type] = ledger.event_counts.get(event_type, 0) + 1
    if event_type == "run_result":
        ledger.terminal_results.append(event)
    elif event_type == "run_aborted":
        ledger.abort_events.append(event)
    tool_call = _event_tool_call(event)
    if tool_call is not None:
        tool_name, tool_input, call_id = tool_call
        key = call_id or f"missing-id-{line_number}"
        ledger.tool_calls[key] = {"tool": tool_name, "input": tool_input}
        violation = validate_stream_tool_call(tool_name, tool_input, workspace, contract)
        if violation:
            ledger.tool_violations.append(f"{key}: {violation}")
    if (
        event_type == "agent_event"
        and isinstance(event.get("event"), dict)
        and event["event"].get("type") == "content_end"
        and event["event"].get("contentType") == "tool"
    ):
        _record_tool_failure(ledger, event["event"])
    return compact_event(event)


def _pump_stream(
    stream: BinaryIO,
    raw_path: Path,
    compact_path: Path,
    ledger: StreamLedger,
    workspace: Path,
    contract: TaskContract,
    display_prefix: str,
) -> None:
    with raw_path.open("wb") as raw, compact_path.open("a", encoding="utf-8") as compact:
        for line_number, raw_line in enumerate(iter(stream.readline, b""), start=1):
            raw.write(raw_line)
            raw.flush()
            decoded = raw_line.decode("utf-8", errors="replace")
            rendered = ingest_stream_line(
                decoded,
                line_number,
                ledger,
                workspace,
                contract,
            )
            if rendered:
                output = f"[{display_prefix}] {rendered}"
                compact.write(output + "\n")
                compact.flush()
                print(output, flush=True)


def read_hook_audit(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return records, ["hook audit file is missing"]
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"hook audit line {line_number} is malformed")
            continue
        if not isinstance(value, dict):
            errors.append(f"hook audit line {line_number} is not an object")
            continue
        records.append(value)
    return records, errors


def assess_run(
    *,
    returncode: int,
    ledger: StreamLedger,
    hook_records: list[dict[str, Any]],
    hook_errors: list[str],
    contract: TaskContract,
    changed_files: list[str],
    snapshot_violations: list[str],
    source_unchanged: bool,
) -> list[str]:
    reasons: list[str] = []
    if returncode != 0:
        reasons.append(f"Cline exited nonzero: {returncode}")
    if len(ledger.terminal_results) != 1:
        reasons.append(f"expected exactly one run_result, got {len(ledger.terminal_results)}")
    else:
        terminal = ledger.terminal_results[0]
        if terminal.get("finishReason") != "completed":
            reasons.append(f"terminal finishReason is {terminal.get('finishReason')!r}")
        observed_model = terminal.get("model")
        if not (
            isinstance(observed_model, dict)
            and observed_model.get("id") == contract.model
            and observed_model.get("provider") == "openai-compatible"
        ):
            reasons.append(
                "terminal model mismatch: expected "
                f"openai-compatible/{contract.model}, got {observed_model!r}"
            )
    if ledger.abort_events:
        reasons.append("run emitted an abort event")
    if ledger.malformed_json_lines:
        reasons.append(f"malformed JSON event lines: {ledger.malformed_json_lines}")
    reasons.extend(ledger.tool_violations)
    if ledger.stop_reason:
        reasons.append(ledger.stop_reason)
    reasons.extend(hook_errors)
    denied = [record for record in hook_records if record.get("allowed") is not True]
    if denied:
        reasons.append(f"hook denied {len(denied)} tool call(s)")
    streamed_ids = {call_id for call_id in ledger.tool_calls if not call_id.startswith("missing-id-")}
    audited_ids = {
        str(record.get("call_id"))
        for record in hook_records
        if record.get("allowed") is True and record.get("call_id")
    }
    if streamed_ids != audited_ids:
        reasons.append(
            "stream/hook tool ledger mismatch: "
            f"streamed={sorted(streamed_ids)}, audited={sorted(audited_ids)}"
        )
    reasons.extend(snapshot_violations)
    if not source_unchanged:
        reasons.append("canonical source state or declared input hashes changed during the run")
    if not changed_files:
        reasons.append("candidate made no workspace changes")
    return reasons


def export_candidate_patch(
    workspace: Path,
    evidence_dir: Path,
    baselines: dict[str, Any],
    changed_files: Iterable[str],
) -> tuple[Path, Path]:
    candidate_dir = evidence_dir / "candidate"
    patch_path = evidence_dir / "candidate.patch"
    candidate_dir.mkdir(parents=True, exist_ok=False)
    patch_lines: list[str] = []
    for relative in sorted(changed_files):
        if relative not in baselines:
            continue
        after_path = workspace / relative
        before_text = str(baselines[relative]["text"])
        after_text = after_path.read_text(encoding="utf-8")
        destination = candidate_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(after_path, destination)
        before_label = (
            "/dev/null"
            if str(baselines[relative]["source"]).startswith("precreated-")
            else f"a/{relative}"
        )
        after_label = f"b/{relative}"
        for part in difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=before_label,
            tofile=after_label,
        ):
            if part.endswith(("\n", "\r")):
                patch_lines.append(part)
            else:
                patch_lines.extend([part + "\n", "\\ No newline at end of file\n"])
    patch_path.write_text("".join(patch_lines), encoding="utf-8")
    return patch_path, candidate_dir


def _default_evidence_root() -> Path:
    configured = os.environ.get("QWEN_HARNESS_STATE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".local" / "state" / "qwen-cline-harness"


def create_evidence_dir(task_id: str, root: Path | None = None) -> Path:
    base = (root or _default_evidence_root()).resolve()
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(tempfile.mkdtemp(prefix=f"{stamp}-{task_id}-", dir=base))
    os.chmod(path, 0o700)
    return path


def build_prompt(contract: TaskContract) -> str:
    return (
        "You are Qwen running as a bounded implementation executor. "
        "First read AGENTS.md and .cline/rules/00-qwen-harness-contract.md, "
        f"then read {contract.packet_path}. Perform this exact task: {contract.task}\n\n"
        "Use only read_files, editor, and submit_and_exit. Make the smallest admitted "
        "edit promptly. Do not search or investigate beyond the named files. If an "
        "input or grant is missing, stop and report it without attempting another tool."
    )


def run_cline(
    *,
    cline_binary: Path,
    profile_text: str,
    pin: RuntimePin,
    contract: TaskContract,
    workspace: Path,
    state_dir: Path,
    run_home: Path,
    temp_dir: Path,
    policy_path: Path,
    hook_audit_path: Path,
    runtime_hook_log_path: Path,
    evidence_dir: Path,
) -> tuple[int, StreamLedger, bool]:
    command = [
        "/usr/bin/sandbox-exec",
        "-p",
        profile_text,
        str(cline_binary),
        "--json",
        "--yolo",
        "--cwd",
        str(workspace),
        "--thinking",
        contract.thinking,
        "--compaction",
        "agentic",
        "--provider",
        pin.provider,
        "--model",
        contract.model,
        "--retries",
        str(contract.retries),
    ]
    if contract.timeout_seconds > 0:
        command.extend(["--timeout", str(contract.timeout_seconds)])
    command.extend(["--data-dir", str(state_dir), build_prompt(contract)])
    environment = {
        "CI": "1",
        "CLINE_DATA_DIR": str(state_dir),
        "CLINE_DIR": str(state_dir),
        "CLINE_DISABLE_CLINE_PASS_NOTICE": "1",
        "CLINE_HOOKS_LOG_PATH": str(runtime_hook_log_path),
        "CLINE_MCP_SETTINGS_PATH": str(state_dir / "settings" / "cline_mcp_settings.json"),
        "CLINE_NO_AUTO_UPDATE": "1",
        "DO_NOT_TRACK": "1",
        "HOME": str(run_home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "QWEN_HARNESS_AUDIT": str(hook_audit_path),
        "QWEN_HARNESS_POLICY": str(policy_path),
        "QWEN_HARNESS_REQUIRED": "1",
        "TERM": "dumb",
        "TMPDIR": str(temp_dir),
    }
    ledger = StreamLedger()
    raw_stdout = evidence_dir / "cline.stdout.ndjson"
    raw_stderr = evidence_dir / "cline.stderr.log"
    compact_path = evidence_dir / "cline.compact.log"
    compact_path.touch()
    process = subprocess.Popen(
        command,
        cwd=workspace,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        close_fds=True,
    )
    assert process.stdout is not None and process.stderr is not None
    stdout_thread = threading.Thread(
        target=_pump_stream,
        args=(
            process.stdout,
            raw_stdout,
            compact_path,
            ledger,
            workspace,
            contract,
            "qwen",
        ),
        daemon=True,
    )

    def pump_stderr() -> None:
        with raw_stderr.open("wb") as handle:
            for chunk in iter(process.stderr.readline, b""):
                handle.write(chunk)
                handle.flush()

    stderr_thread = threading.Thread(target=pump_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    interrupted = False
    try:
        while process.poll() is None:
            if ledger.stop_reason:
                interrupted = True
                os.killpg(process.pid, signal.SIGINT)
                break
            time.sleep(0.1)
        returncode = process.wait()
    except KeyboardInterrupt:
        interrupted = True
        os.killpg(process.pid, signal.SIGINT)
        try:
            returncode = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            returncode = process.wait()
    stdout_thread.join(timeout=10)
    stderr_thread.join(timeout=10)
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        interrupted = True
    return returncode, ledger, interrupted


def _source_inputs_still_match(source_root: Path, contract: TaskContract) -> bool:
    try:
        if _git_output(source_root, "rev-parse", "HEAD").decode().strip() != contract.source_commit:
            return False
        for relative, digest in contract.input_files.items():
            if sha256_file(_assert_regular_source_file(source_root, relative, digest)) != digest:
                return False
    except HarnessError:
        return False
    return True


def execute_contract(
    contract_path: Path,
    *,
    source_root: Path = ROOT,
    evidence_root: Path | None = None,
    preflight_only: bool = False,
) -> tuple[int, dict[str, Any]]:
    pin = load_runtime_pin()
    contract_path = contract_path.resolve(strict=True)
    contract = load_contract(contract_path, pin)
    source_root = source_root.resolve(strict=True)
    verify_source_contract(source_root, contract)
    source_fingerprint_before = source_state_fingerprint(source_root)
    cline_binary = resolve_cline_binary()
    verify_runtime(pin, cline_binary)
    check_bridge_health(pin)
    evidence_dir = create_evidence_dir(contract.task_id, evidence_root)
    shutil.copyfile(contract_path, evidence_dir / "task-contract.json")
    control_hashes = {
        "task_contract": sha256_file(contract_path),
        "harness_script": sha256_file(Path(__file__)),
        "hook_source": sha256_file(HOOK_SOURCE),
        "runtime_pin": sha256_file(RUNTIME_PIN_PATH),
        "agents": sha256_file(source_root / "AGENTS.md"),
    }
    workspace, policy_path, baselines = materialize_workspace(
        source_root,
        contract,
        evidence_dir,
    )
    state_dir = evidence_dir / "cline-state"
    run_home = evidence_dir / "home"
    temp_dir = evidence_dir / "tmp"
    for path in (state_dir, run_home, temp_dir):
        path.mkdir(parents=True, exist_ok=True)
    create_state_config(state_dir, pin)
    hook_audit_path = evidence_dir / "hook-audit.jsonl"
    runtime_hook_log_path = evidence_dir / "cline-runtime-hooks.jsonl"
    hook_audit_path.touch()
    runtime_hook_log_path.touch()
    outside_sentinel = evidence_dir / "outside-sentinel.txt"
    outside_sentinel.write_text("sandbox-self-test-sentinel\n", encoding="utf-8")
    write_paths = [workspace / relative for relative in contract.write_files]
    profile_text = build_sandbox_profile(
        user_home=Path.home(),
        cline_binary=cline_binary,
        workspace=workspace,
        state_dir=state_dir,
        run_home=run_home,
        temp_dir=temp_dir,
        policy_path=policy_path,
        hook_audit_path=hook_audit_path,
        runtime_hook_log_path=runtime_hook_log_path,
        write_files=write_paths,
        bridge_port=pin.bridge_port,
    )
    sandbox_profile_path = evidence_dir / "sandbox.sb"
    sandbox_profile_path.write_text(profile_text, encoding="utf-8")
    control_hashes.update(
        {
            "tool_policy": sha256_file(policy_path),
            "sandbox_profile": sha256_file(sandbox_profile_path),
            "workspace_rule": sha256_file(
                workspace / ".cline" / "rules" / "00-qwen-harness-contract.md"
            ),
        }
    )
    sandbox_checks = sandbox_self_test(
        profile_text,
        workspace=workspace,
        outside_sentinel=outside_sentinel,
        bridge_health_url=pin.bridge_health_url,
    )
    hook_self_test = hostile_hook_self_test(
        workspace=workspace,
        policy_path=policy_path,
        evidence_dir=evidence_dir,
    )
    before = snapshot_tree(workspace)
    _write_json(
        evidence_dir / "workspace-before.json",
        {path: dataclasses.asdict(record) for path, record in before.items()},
    )
    if preflight_only:
        summary = {
            "schema_version": "qwen-cline-run-summary-v1",
            "accepted": False,
            "preflight_only": True,
            "task_id": contract.task_id,
            "model": contract.model,
            "thinking": contract.thinking,
            "cline_version": pin.cline_version,
            "evidence_dir": str(evidence_dir),
            "sandbox_checks": sandbox_checks,
            "hook_self_test": hook_self_test,
            "control_sha256": control_hashes,
        }
        _write_json(evidence_dir / "summary.json", summary)
        return 0, summary
    returncode, ledger, interrupted = run_cline(
        cline_binary=cline_binary,
        profile_text=profile_text,
        pin=pin,
        contract=contract,
        workspace=workspace,
        state_dir=state_dir,
        run_home=run_home,
        temp_dir=temp_dir,
        policy_path=policy_path,
        hook_audit_path=hook_audit_path,
        runtime_hook_log_path=runtime_hook_log_path,
        evidence_dir=evidence_dir,
    )
    after = snapshot_tree(workspace)
    _write_json(
        evidence_dir / "workspace-after.json",
        {path: dataclasses.asdict(record) for path, record in after.items()},
    )
    changed_files, snapshot_violations = compare_snapshots(before, after, contract)
    snapshot_violations.extend(expected_output_violations(workspace, contract))
    hook_records, hook_errors = read_hook_audit(hook_audit_path)
    source_unchanged = (
        source_state_fingerprint(source_root) == source_fingerprint_before
        and _source_inputs_still_match(source_root, contract)
    )
    rejection_reasons = assess_run(
        returncode=returncode,
        ledger=ledger,
        hook_records=hook_records,
        hook_errors=hook_errors,
        contract=contract,
        changed_files=changed_files,
        snapshot_violations=snapshot_violations,
        source_unchanged=source_unchanged,
    )
    if interrupted:
        rejection_reasons.append("run was interrupted or a stream pump did not terminate")
    accepted = not rejection_reasons
    patch_path: Path | None = None
    candidate_dir: Path | None = None
    if accepted:
        patch_path, candidate_dir = export_candidate_patch(
            workspace,
            evidence_dir,
            baselines,
            changed_files,
        )
    terminal = ledger.terminal_results[0] if len(ledger.terminal_results) == 1 else {}
    observed_model = terminal.get("model")
    summary = {
        "schema_version": "qwen-cline-run-summary-v1",
        "accepted": accepted,
        "preflight_only": False,
        "task_id": contract.task_id,
        "source_commit": contract.source_commit,
        "source_unchanged": source_unchanged,
        "model_expected": contract.model,
        "provider_expected": pin.provider,
        "model_observed": observed_model.get("id")
        if isinstance(observed_model, dict)
        else observed_model,
        "provider_observed": observed_model.get("provider")
        if isinstance(observed_model, dict)
        else None,
        "thinking": contract.thinking,
        "cline_version": pin.cline_version,
        "cline_binary_sha256": pin.cline_binary_sha256,
        "finish_reason": terminal.get("finishReason"),
        "iterations": terminal.get("iterations"),
        "usage": terminal.get("usage"),
        "returncode": returncode,
        "changed_files": changed_files,
        "required_change_files": list(contract.required_change_files),
        "expected_output_sha256": contract.expected_output_sha256,
        "rejection_reasons": rejection_reasons,
        "tool_calls": [
            {"call_id": call_id, "tool": item["tool"]}
            for call_id, item in sorted(ledger.tool_calls.items())
        ],
        "hook_record_count": len(hook_records),
        "warning_line_count": len(ledger.warnings),
        "malformed_json_lines": ledger.malformed_json_lines,
        "sandbox_checks": sandbox_checks,
        "hook_self_test": hook_self_test,
        "control_sha256": control_hashes,
        "verification_commands_parent_only": [
            list(command) for command in contract.verification_commands
        ],
        "candidate_patch": str(patch_path) if patch_path else None,
        "candidate_dir": str(candidate_dir) if candidate_dir else None,
        "evidence_dir": str(evidence_dir),
    }
    _write_json(evidence_dir / "summary.json", summary)
    print(
        f"[harness] {'ACCEPTED' if accepted else 'REJECTED'} "
        f"evidence={evidence_dir}",
        flush=True,
    )
    if rejection_reasons:
        for reason in rejection_reasons:
            print(f"[harness] reject: {reason}", flush=True)
    return (0 if accepted else 1), summary


def create_contract_from_args(args: argparse.Namespace) -> dict[str, Any]:
    source_root = Path(args.source_root).resolve(strict=True)
    pin = load_runtime_pin()
    read_paths = [validate_relative_path(path) for path in args.read]
    write_paths = [validate_relative_path(path) for path in args.write]
    create_paths = [validate_relative_path(path) for path in args.create]
    packet = validate_relative_path(args.packet)
    ordered_inputs = list(dict.fromkeys([packet, *read_paths, *write_paths]))
    create_set = set(create_paths)
    expected_output_sha256: dict[str, str] = {}
    for item in args.expect_output_sha:
        if "=" not in item:
            raise HarnessError("--expect-output-sha must use PATH=SHA256")
        raw_path, digest = item.split("=", 1)
        path = validate_relative_path(raw_path)
        if path in expected_output_sha256:
            raise HarnessError(f"duplicate expected output hash: {path}")
        expected_output_sha256[path] = digest
    input_files: dict[str, str] = {}
    for relative in ordered_inputs:
        if relative in create_set:
            continue
        source = source_root / relative
        if not source.is_file():
            raise HarnessError(f"cannot hash missing input: {relative}")
        input_files[relative] = sha256_file(source)
    data = {
        "schema_version": CONTRACT_SCHEMA,
        "task_id": args.task_id,
        "source_commit": _git_output(source_root, "rev-parse", "HEAD").decode().strip(),
        "task": args.task,
        "packet_path": packet,
        "input_files": input_files,
        "create_files": create_paths,
        "write_files": write_paths,
        "required_change_files": args.require_change,
        "expected_output_sha256": expected_output_sha256,
        "verification_commands": [],
        "model": pin.model,
        "thinking": pin.thinking,
        "retries": args.retries,
        "timeout_seconds": args.timeout,
    }
    validate_contract_data(data, pin)
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="create a hash-bound task contract")
    init_parser.add_argument("--task-id", required=True)
    init_parser.add_argument("--task", required=True)
    init_parser.add_argument("--packet", required=True)
    init_parser.add_argument("--read", action="append", default=[])
    init_parser.add_argument("--write", action="append", default=[])
    init_parser.add_argument("--create", action="append", default=[])
    init_parser.add_argument("--require-change", action="append", default=[])
    init_parser.add_argument(
        "--expect-output-sha",
        action="append",
        default=[],
        metavar="PATH=SHA256",
    )
    init_parser.add_argument("--retries", type=int, default=3)
    init_parser.add_argument("--timeout", type=int, default=0)
    init_parser.add_argument("--source-root", default=str(ROOT))
    init_parser.add_argument("--output", required=True)
    for name, help_text in (
        ("preflight", "validate, materialize, and self-test without calling Qwen"),
        ("run", "execute Qwen and export only an accepted candidate patch"),
    ):
        run_parser = subparsers.add_parser(name, help=help_text)
        run_parser.add_argument("--contract", required=True)
        run_parser.add_argument("--source-root", default=str(ROOT))
        run_parser.add_argument("--evidence-root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            data = create_contract_from_args(args)
            output = Path(args.output).expanduser().resolve()
            _write_json(output, data)
            print(f"wrote contract: {output}")
            return 0
        evidence_root = (
            Path(args.evidence_root).expanduser().resolve() if args.evidence_root else None
        )
        code, summary = execute_contract(
            Path(args.contract).expanduser().resolve(strict=True),
            source_root=Path(args.source_root),
            evidence_root=evidence_root,
            preflight_only=args.command == "preflight",
        )
        print(json.dumps(summary, sort_keys=True))
        return code
    except HarnessError as exc:
        print(f"qwen harness error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
