from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import build_context, dump_json, load_json
from authzbench.score import score_submission


SCHEMA_VERSION = "submission-runner-smoke-v1"
DEFAULT_IMAGE = "python:3.11-alpine"
VALID_EXECUTION_SCOPES = {"rehearsal", "release_candidate"}
MAX_OUTPUT_FILE_BYTES = 1_048_576
DOCKER_CONTROL_TIMEOUT_SECONDS = 30
REQUIRED_CONTAINER_CONSTRAINTS = {
    "network=none",
    "read_only_rootfs",
    "cap_drop=ALL",
    "no_new_privileges",
    "non_root_user",
    "resource_limits",
    "rendered_context_mount_only",
    "output_file_size_limit",
}
SENSITIVE_KEYS = {
    "task_id",
    "task_path",
    "task",
    "manifest",
    "seed",
    "route",
    "oracle",
    "controls",
    "scorer_result",
    "raw_result",
    "per_task",
    "private_path",
    "private_pack_path",
}
SENSITIVE_STRING_MARKERS = (
    "/Users/",
    "/home/",
    "/private/",
    "tasks_private/holdout",
    "results/",
    "captures/",
)


def _manifest_paths(pack_path: Path) -> list[Path]:
    return sorted(path for path in pack_path.glob("*/*.json") if path.is_file())


def _private_pack_fingerprint(pack_path: Path) -> str:
    digest = hashlib.sha256()
    for manifest_path in _manifest_paths(pack_path):
        relative = manifest_path.relative_to(pack_path).as_posix()
        manifest = load_json(manifest_path)
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(canonical.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _select_control_task(pack_path: Path) -> dict[str, Any]:
    for manifest_path in _manifest_paths(pack_path):
        task = load_json(manifest_path)
        if task.get("split") == "private_holdout" and task.get("expected_vulnerable") is False:
            return task
    raise ValueError("private pack must contain at least one secure control task for the smoke")


def _sensitive_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in SENSITIVE_KEYS:
                findings.append(f"{child_path}: sensitive key is not allowed")
            findings.extend(_sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for marker in SENSITIVE_STRING_MARKERS:
            if marker in value:
                findings.append(f"{path}: sensitive path marker is not allowed")
        if re.search(r"(?<![A-Za-z0-9_.-/])/[A-Za-z0-9_.-]+/", value):
            findings.append(f"{path}: absolute path is not allowed")
    return findings


def validate_smoke_evidence(
    evidence: dict[str, Any],
    *,
    allow_rehearsal: bool = False,
    expected_benchmark_source_sha: str | None = None,
    expected_private_pack_fingerprint_sha256: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if evidence.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    execution_scope = evidence.get("execution_scope")
    if execution_scope not in VALID_EXECUTION_SCOPES:
        errors.append("execution_scope must be rehearsal or release_candidate")
    elif execution_scope == "rehearsal" and not allow_rehearsal:
        errors.append("rehearsal smoke evidence is not release-candidate evidence")
    if evidence.get("result") != "passed":
        errors.append("result must be passed")
    benchmark_source_sha = evidence.get("benchmark_source_sha")
    if not isinstance(benchmark_source_sha, str) or re.fullmatch(r"[0-9a-f]{40}", benchmark_source_sha) is None:
        errors.append("benchmark_source_sha must be a 40-character lowercase Git SHA")
    elif expected_benchmark_source_sha is not None and benchmark_source_sha != expected_benchmark_source_sha:
        errors.append("benchmark_source_sha does not match expected source SHA")
    fingerprint = evidence.get("private_pack_fingerprint_sha256")
    if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
        errors.append("private_pack_fingerprint_sha256 must be a lowercase SHA-256 digest")
    elif (
        expected_private_pack_fingerprint_sha256 is not None
        and fingerprint != expected_private_pack_fingerprint_sha256
    ):
        errors.append("private_pack_fingerprint_sha256 does not match expected active pack")
    for field in (
        "runner_image_or_hosted_version",
        "private_pack_version",
        "isolation_model",
        "command",
    ):
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            errors.append(f"{field} is required")
    for field in (
        "submitter_private_manifest_read_denied",
        "scorer_controlled_private_eval",
        "cleanup_completed",
        "privacy_scan_passed",
    ):
        if evidence.get(field) is not True:
            errors.append(f"{field} must be true")
    if evidence.get("public_output_private_artifacts_included") is not False:
        errors.append("public_output_private_artifacts_included must be false")
    constraints = evidence.get("container_constraints")
    if not isinstance(constraints, list) or not REQUIRED_CONTAINER_CONSTRAINTS.issubset(set(constraints)):
        errors.append("container_constraints are incomplete")
    errors.extend(_sensitive_findings(evidence))
    return errors


def _image_identity(image: str) -> str:
    completed = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=DOCKER_CONTROL_TIMEOUT_SECONDS,
    )
    return f"{image}@{completed.stdout.strip()}"


def _probe_program() -> str:
    return """
import json
from pathlib import Path

context = json.loads(Path("/input/context.json").read_text(encoding="utf-8"))
attempts = {}
for candidate in (
    Path("/private-holdout/rotation-metadata.json"),
    Path("/workspace/tasks_private/holdout"),
    Path("/repo/tasks_private/holdout"),
):
    try:
        candidate.read_bytes()
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError, PermissionError, OSError):
        attempts[str(candidate)] = False
    else:
        attempts[str(candidate)] = True

Path("/output/submission.json").write_text(
    json.dumps({"findings": []}, sort_keys=True) + "\\n",
    encoding="utf-8",
)
Path("/output/probe.json").write_text(
    json.dumps(
        {
            "context_readable": isinstance(context, dict),
            "private_paths_readable": attempts,
        },
        sort_keys=True,
    )
    + "\\n",
    encoding="utf-8",
)
""".strip()


def _option_values(command: list[str], option: str) -> list[str]:
    values: list[str] = []
    for index, value in enumerate(command[:-1]):
        if value == option:
            values.append(command[index + 1])
    return values


def _require_single_option(
    command: list[str],
    option: str,
    expected_value: str,
    errors: list[str],
) -> None:
    values = _option_values(command, option)
    if values != [expected_value]:
        errors.append(f"{option} must be exactly {expected_value}")


def _validated_container_constraints(command: list[str], input_dir: Path, output_dir: Path) -> list[str]:
    errors: list[str] = []
    for flag in ("--rm", "--read-only"):
        if command.count(flag) != 1:
            errors.append(f"{flag} must be present exactly once")
    for option, expected_value in (
        ("--network", "none"),
        ("--cap-drop", "ALL"),
        ("--security-opt", "no-new-privileges"),
        ("--pids-limit", "64"),
        ("--memory", "128m"),
        ("--cpus", "0.5"),
        ("--user", "65534:65534"),
        ("--tmpfs", "/tmp:rw,noexec,nosuid,size=16m"),
        ("--ulimit", f"fsize={MAX_OUTPUT_FILE_BYTES}:{MAX_OUTPUT_FILE_BYTES}"),
    ):
        _require_single_option(command, option, expected_value, errors)
    expected_mounts = {
        f"type=bind,src={input_dir.resolve()},dst=/input,readonly",
        f"type=bind,src={output_dir.resolve()},dst=/output",
    }
    mounts = set(_option_values(command, "--mount"))
    if mounts != expected_mounts:
        errors.append("container mounts must be exactly readonly /input and writable /output")
    if errors:
        raise ValueError("invalid container isolation command: " + "; ".join(errors))
    return sorted(REQUIRED_CONTAINER_CONSTRAINTS)


def _load_bounded_json(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_OUTPUT_FILE_BYTES:
        raise ValueError(f"{path.name} exceeds {MAX_OUTPUT_FILE_BYTES} bytes")
    return load_json(path)


def run_smoke(
    private_pack: Path,
    *,
    output_path: Path,
    benchmark_source_sha: str,
    private_pack_version: str,
    execution_scope: str,
    image: str = DEFAULT_IMAGE,
) -> dict[str, Any]:
    if execution_scope not in VALID_EXECUTION_SCOPES:
        raise ValueError("execution_scope must be rehearsal or release_candidate")
    task = _select_control_task(private_pack)
    context = build_context(task)
    container_name = f"authzbench-submission-smoke-{uuid.uuid4().hex[:12]}"
    fingerprint = _private_pack_fingerprint(private_pack)

    with tempfile.TemporaryDirectory(prefix="authzbench-submission-smoke.") as tmp:
        temp_root = Path(tmp)
        input_dir = temp_root / "input"
        output_dir = temp_root / "output"
        input_dir.mkdir()
        input_dir.chmod(0o755)
        output_dir.mkdir()
        output_dir.chmod(0o733)
        context_path = input_dir / "context.json"
        context_path.write_text(dump_json(context) + "\n", encoding="utf-8")
        context_path.chmod(0o644)

        command = [
            "docker",
            "run",
            "--name",
            container_name,
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            "128m",
            "--cpus",
            "0.5",
            "--user",
            "65534:65534",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--ulimit",
            f"fsize={MAX_OUTPUT_FILE_BYTES}:{MAX_OUTPUT_FILE_BYTES}",
            "--mount",
            f"type=bind,src={input_dir.resolve()},dst=/input,readonly",
            "--mount",
            f"type=bind,src={output_dir.resolve()},dst=/output",
            image,
            "python",
            "-c",
            _probe_program(),
        ]
        container_constraints = _validated_container_constraints(command, input_dir, output_dir)
        completed = None
        run_error = None
        try:
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
        except subprocess.SubprocessError as exc:
            run_error = exc
        finally:
            cleanup_completed = False
            try:
                subprocess.run(
                    ["docker", "container", "rm", "--force", container_name],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=DOCKER_CONTROL_TIMEOUT_SECONDS,
                )
                remaining = subprocess.run(
                    [
                        "docker",
                        "container",
                        "ls",
                        "--all",
                        "--filter",
                        f"name=^/{container_name}$",
                        "--format",
                        "{{.Names}}",
                    ],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=DOCKER_CONTROL_TIMEOUT_SECONDS,
                )
                cleanup_completed = remaining.returncode == 0 and not remaining.stdout.strip()
            except subprocess.SubprocessError:
                cleanup_completed = False
        probe_path = output_dir / "probe.json"
        submission_path = output_dir / "submission.json"
        probe_present = probe_path.is_file()
        submission_present = submission_path.is_file()
        output_error = None
        try:
            probe = _load_bounded_json(probe_path) if probe_present else {}
            submission = _load_bounded_json(submission_path) if submission_present else {}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            output_error = exc
            probe = {}
            submission = {}
        score = score_submission(task, submission)
        private_reads = probe.get("private_paths_readable")
        private_manifest_read_denied = (
            isinstance(private_reads, dict)
            and bool(private_reads)
            and all(value is False for value in private_reads.values())
        )
        passed = (
            run_error is None
            and output_error is None
            and completed is not None
            and completed.returncode == 0
            and probe_present
            and submission_present
            and probe.get("context_readable") is True
            and private_manifest_read_denied
            and score.get("passed") is True
            and cleanup_completed
        )

    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "execution_scope": execution_scope,
        "result": "passed" if passed else "failed",
        "benchmark_source_sha": benchmark_source_sha,
        "runner_image_or_hosted_version": _image_identity(image),
        "private_pack_version": private_pack_version,
        "private_pack_fingerprint_sha256": fingerprint,
        "isolation_model": "docker-bind-rendered-context-only",
        "command": (
            "python3 scripts/containerized_submission_smoke.py "
            "--private-pack <protected> --output <public-safe-evidence>"
        ),
        "submitter_private_manifest_read_denied": private_manifest_read_denied,
        "scorer_controlled_private_eval": True,
        "cleanup_completed": cleanup_completed,
        "privacy_scan_passed": False,
        "public_output_private_artifacts_included": False,
        "container_constraints": container_constraints,
    }
    evidence["privacy_scan_passed"] = not _sensitive_findings(evidence)
    validation_errors = validate_smoke_evidence(
        evidence,
        allow_rehearsal=execution_scope == "rehearsal",
        expected_benchmark_source_sha=benchmark_source_sha,
        expected_private_pack_fingerprint_sha256=fingerprint,
    )
    if validation_errors:
        evidence["result"] = "failed"
        evidence["privacy_scan_passed"] = not _sensitive_findings(evidence)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_json(evidence) + "\n", encoding="utf-8")
    if validation_errors:
        raise RuntimeError("submission runner smoke failed: " + "; ".join(validation_errors))
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove containerized submitter isolation from host-side private manifests."
    )
    parser.add_argument("--private-pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--benchmark-source-sha", required=True)
    parser.add_argument("--private-pack-version", required=True)
    parser.add_argument(
        "--execution-scope",
        choices=sorted(VALID_EXECUTION_SCOPES),
        default="release_candidate",
    )
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args()
    try:
        evidence = run_smoke(
            args.private_pack,
            output_path=args.output,
            benchmark_source_sha=args.benchmark_source_sha,
            private_pack_version=args.private_pack_version,
            execution_scope=args.execution_scope,
            image=args.image,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"submission runner smoke failed: {exc}", file=sys.stderr)
        return 1
    print(dump_json(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
