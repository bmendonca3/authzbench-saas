from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from authzbench.core import benchmark_fingerprint  # noqa: E402

try:
    from .codex_baseline_agent import (
        MODEL_OUTPUT_SCHEMA,
        PROFILE_SKILL_LOADING_STATUS,
        PROMPT_HASH_SCOPE,
        _global_blocker_code,
    )
except ImportError:  # Direct script execution adds scripts/, rather than the repository root, to sys.path.
    from codex_baseline_agent import (  # type: ignore[no-redef]
        MODEL_OUTPUT_SCHEMA,
        PROFILE_SKILL_LOADING_STATUS,
        PROMPT_HASH_SCOPE,
        _global_blocker_code,
    )


DEFAULT_MATRIX = ROOT / "artifact" / "openai-codex-model-effort-matrix-2026-07-12.json"
DEFAULT_ADMISSION_TASK = "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
DEFAULT_FULL_TASK_PATTERN = "tasks/*/*.json"
EMPTY_DIFF_SHA256 = hashlib.sha256(b"").hexdigest()
MODEL_ORDER = {
    "gpt-5.4-mini": 0,
    "gpt-5.6-luna": 1,
    "gpt-5.4": 2,
    "gpt-5.5": 3,
    "gpt-5.6-terra": 4,
    "gpt-5.6-sol": 5,
}
EFFORT_ORDER = {"low": 0, "medium": 1, "high": 2, "xhigh": 3, "max": 4}
EXPECTED_OUTPUT_SCHEMA_SHA256 = hashlib.sha256(
    (json.dumps(MODEL_OUTPUT_SCHEMA, indent=2, sort_keys=True) + "\n").encode("utf-8")
).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _expected_protocol_manifest(matrix_path: Path) -> dict[str, Any]:
    source_paths: dict[str, Path] = {
        "core": ROOT / "authzbench" / "core.py",
        "legacy_runner": ROOT / "authzbench" / "run.py",
        "scorer": ROOT / "authzbench" / "score.py",
        "evaluation_runner": ROOT / "authzbench" / "evaluate.py",
    }
    for path in sorted((ROOT / "apps").rglob("*.py")):
        source_paths[f"app:{path.relative_to(ROOT).as_posix()}"] = path
    agent_paths = sorted(
        {
            (ROOT / "scripts" / "codex_baseline_agent.py").resolve(),
            Path(__file__).resolve(),
            matrix_path.resolve(),
            _catalog_path_from_matrix(matrix_path),
        },
        key=lambda path: path.as_posix(),
    )
    for index, path in enumerate(agent_paths, start=1):
        source_paths[f"agent_source_{index}"] = path
    source_hashes = {name: _file_sha256(path) for name, path in source_paths.items()}
    manifest: dict[str, Any] = {
        "schema_version": "authzbench-evaluation-protocol-manifest-v1",
        "protocol_version": "blinded-control-evidence-v1",
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
        "source_set_sha256": _stable_json_sha256(source_hashes),
    }
    manifest["manifest_sha256"] = _stable_json_sha256(manifest)
    return manifest


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def _catalog_path_from_matrix(matrix_path: Path) -> Path:
    matrix = _load_json(matrix_path)
    value = matrix.get("normalized_catalog_artifact")
    if not isinstance(value, str) or not value:
        raise ValueError("matrix normalized_catalog_artifact must be a non-empty path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("matrix normalized catalog path must be a safe repository-relative path")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("matrix normalized catalog path escapes repository root") from exc
    if not resolved.is_file():
        raise ValueError("matrix normalized catalog artifact does not exist")
    return resolved


def _expected_task_binding(task_pattern: str) -> dict[str, Any]:
    paths = (
        [ROOT / task_pattern]
        if "*" not in task_pattern
        else sorted(ROOT.glob(task_pattern))
    )
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError(f"expected task pattern is incomplete: {task_pattern}")
    items = []
    identities = []
    for path in paths:
        relative_path = path.relative_to(ROOT).as_posix()
        task = _load_json(path)
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"expected task has no valid id: {relative_path}")
        items.append((relative_path, task))
        identities.append((task_id, relative_path))
    return {
        "fingerprint": benchmark_fingerprint(items),
        "identities": sorted(identities),
    }


def _expected_cli_version(matrix_path: Path) -> str:
    value = _load_json(matrix_path).get("codex_cli_version")
    if not isinstance(value, str) or not value:
        raise ValueError("matrix codex_cli_version must be a non-empty string")
    return value


def _require_codex_cli_version(codex_path: Path, matrix_path: Path) -> str:
    completed = subprocess.run(
        [str(codex_path), "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    observed = (completed.stdout or completed.stderr).strip()
    expected = _expected_cli_version(matrix_path)
    if completed.returncode != 0 or observed != expected:
        raise ValueError(
            f"Codex CLI version does not match matrix: expected {expected!r}, observed {observed!r}"
        )
    return observed


def _task_binding_reasons(summary: dict[str, Any], task_pattern: str) -> list[str]:
    expected = _expected_task_binding(task_pattern)
    reasons: list[str] = []
    if summary.get("benchmark_fingerprint") != expected["fingerprint"]:
        reasons.append("benchmark fingerprint does not match the exact current task set")
    tasks = summary.get("tasks")
    observed_identities = []
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict):
                task_id = task.get("task_id")
                task_path = task.get("task_path")
                observed_identities.append(
                    (
                        task_id if isinstance(task_id, str) else "",
                        task_path if isinstance(task_path, str) else "",
                    )
                )
    if sorted(observed_identities) != expected["identities"]:
        reasons.append("task ids and paths do not match the exact current task set")
    return reasons


def load_matrix(path: Path) -> list[dict[str, str]]:
    data = _load_json(path)
    configurations = data.get("configurations")
    if not isinstance(configurations, list) or not configurations:
        raise ValueError("matrix configurations must be a non-empty array")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    for raw in configurations:
        if not isinstance(raw, dict):
            raise ValueError("every matrix configuration must be an object")
        config_id = raw.get("id")
        model = raw.get("model")
        effort = raw.get("effort")
        if not all(isinstance(value, str) and value for value in (config_id, model, effort)):
            raise ValueError("matrix id, model, and effort must be non-empty strings")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", config_id):
            raise ValueError(f"unsafe matrix configuration id: {config_id}")
        if config_id in seen_ids or (model, effort) in seen:
            raise ValueError(f"duplicate matrix configuration: {config_id}")
        seen_ids.add(config_id)
        seen.add((model, effort))
        normalized.append({"id": config_id, "model": model, "effort": effort})
    if data.get("configuration_count") != len(normalized):
        raise ValueError("matrix configuration_count does not match configurations length")
    catalog_path = _catalog_path_from_matrix(path)
    if _file_sha256(catalog_path) != data.get("normalized_catalog_sha256"):
        raise ValueError("matrix normalized catalog digest does not match the artifact")
    catalog = _load_json(catalog_path)
    source = catalog.get("source")
    if not isinstance(source, dict):
        raise ValueError("normalized catalog source metadata is missing")
    if source.get("raw_catalog_sha256") != data.get("catalog_sha256"):
        raise ValueError("matrix raw catalog digest does not match the normalized catalog source")
    if source.get("client_version") != data.get("catalog_client_version"):
        raise ValueError("matrix catalog client version does not match the normalized catalog")
    if source.get("fetched_at") != data.get("catalog_fetched_at"):
        raise ValueError("matrix catalog fetch time does not match the normalized catalog")
    catalog_models = catalog.get("models")
    if not isinstance(catalog_models, list):
        raise ValueError("normalized catalog models must be an array")
    derived_pairs: set[tuple[str, str]] = set()
    for model in catalog_models:
        if not isinstance(model, dict):
            raise ValueError("normalized catalog model rows must be objects")
        if model.get("included_in_benchmark") is not True:
            continue
        slug = model.get("slug")
        efforts = model.get("reasoning_efforts")
        if not isinstance(slug, str) or not slug or not isinstance(efforts, list):
            raise ValueError("included catalog models require a slug and reasoning-effort array")
        for effort in efforts:
            if not isinstance(effort, dict):
                raise ValueError("normalized catalog reasoning-effort rows must be objects")
            name = effort.get("effort")
            automatic_delegation = effort.get("automatic_delegation")
            if not isinstance(name, str) or not name or not isinstance(
                automatic_delegation, bool
            ):
                raise ValueError(
                    "normalized catalog reasoning efforts require a name and delegation flag"
                )
            if not automatic_delegation:
                derived_pairs.add((slug, name))
    if derived_pairs != seen:
        raise ValueError("matrix configurations do not match the normalized catalog derivation")
    if catalog.get("selected_non_delegating_configuration_count") != len(normalized):
        raise ValueError("normalized catalog selected configuration count does not match matrix")
    return sorted(
        normalized,
        key=lambda item: (
            MODEL_ORDER.get(item["model"], 100),
            EFFORT_ORDER.get(item["effort"], 100),
        ),
    )


def _require_clean_worktree() -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    commit = head.stdout.strip()
    if head.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("unable to resolve exact benchmark Git HEAD")
    if status.returncode != 0:
        raise ValueError("unable to verify clean benchmark worktree")
    if status.stdout.strip():
        raise ValueError("Codex matrix execution requires a clean worktree")
    return commit


def _evaluator_command(
    config: dict[str, str],
    *,
    phase: str,
    run_label: str,
    task_pattern: str,
    results_dir: Path,
    codex_path: Path,
    model_timeout_seconds: int,
    matrix_path: Path,
) -> tuple[list[str], str]:
    run_id = f"codex-{config['id']}-{phase}-{run_label}"
    adapter = ROOT / "scripts" / "codex_baseline_agent.py"
    runner = Path(__file__).resolve()
    agent_command = shlex.join(
        [
            sys.executable,
            str(adapter),
            "--model",
            config["model"],
            "--effort",
            config["effort"],
            "--timeout-seconds",
            str(model_timeout_seconds),
            "--codex-path",
            str(codex_path),
        ]
    )
    command = [
        sys.executable,
        "-m",
        "authzbench.evaluate",
        "--task",
        task_pattern,
        "--agent-cmd",
        agent_command,
        "--agent-source",
        str(adapter),
        "--agent-source",
        str(runner),
        "--agent-source",
        str(matrix_path),
        "--agent-source",
        str(_catalog_path_from_matrix(matrix_path)),
        "--results-dir",
        str(results_dir),
        "--timeout-seconds",
        str(model_timeout_seconds + 30),
        "--benchmark-version",
        "alpha-0.0.1-public-scaffold-local",
        "--agent",
        "codex-cli",
        "--model",
        config["model"],
        "--harness-type",
        "no-tools-model",
        "--run-id",
        run_id,
    ]
    return command, run_id


def _source_binding_reasons(
    summary: dict[str, Any],
    *,
    benchmark_commit_sha: str | None,
    matrix_sha256: str | None,
    matrix_path: Path | None,
) -> list[str]:
    reasons: list[str] = []
    if benchmark_commit_sha is not None and summary.get("benchmark_commit_sha") != benchmark_commit_sha:
        reasons.append("benchmark commit does not match current clean HEAD")
    provenance = summary.get("benchmark_source_provenance")
    if not isinstance(provenance, dict):
        reasons.append("benchmark source provenance is missing")
    elif provenance.get("tracked_worktree_dirty") is not False:
        reasons.append("benchmark source provenance is not clean")
    else:
        expected_commit = benchmark_commit_sha or summary.get("benchmark_commit_sha")
        if provenance.get("git_commit_sha") != expected_commit:
            reasons.append("benchmark source provenance commit does not match")
        if provenance.get("tracked_diff_sha256") != EMPTY_DIFF_SHA256:
            reasons.append("benchmark source provenance tracked diff is not empty")
    protocol = summary.get("evaluation_protocol")
    if not isinstance(protocol, dict):
        reasons.append("evaluation protocol manifest is missing")
        return reasons
    resolved_matrix_path = (matrix_path or DEFAULT_MATRIX).resolve()
    observed_matrix_sha256 = _file_sha256(resolved_matrix_path)
    if matrix_sha256 is not None and matrix_sha256 != observed_matrix_sha256:
        reasons.append("requested matrix digest does not match the current matrix file")
    expected_protocol = _expected_protocol_manifest(resolved_matrix_path)
    observed_source_hashes = protocol.get("source_sha256")
    if not isinstance(observed_source_hashes, dict) or protocol.get(
        "source_set_sha256"
    ) != _stable_json_sha256(observed_source_hashes):
        reasons.append("evaluation protocol source-set hash is internally invalid")
    observed_manifest_payload = dict(protocol)
    observed_manifest_hash = observed_manifest_payload.pop("manifest_sha256", None)
    if observed_manifest_hash != _stable_json_sha256(observed_manifest_payload):
        reasons.append("evaluation protocol manifest hash is internally invalid")
    if protocol.get("schema_version") != expected_protocol["schema_version"]:
        reasons.append("evaluation protocol schema version does not match")
    if protocol.get("protocol_version") != expected_protocol["protocol_version"]:
        reasons.append("evaluation protocol version does not match")
    if protocol.get("source_sha256") != expected_protocol["source_sha256"]:
        reasons.append("evaluation protocol source hashes do not match current sources")
    if protocol.get("source_set_sha256") != expected_protocol["source_set_sha256"]:
        reasons.append("evaluation protocol source-set hash does not match current sources")
    if protocol.get("manifest_sha256") != expected_protocol["manifest_sha256"]:
        reasons.append("evaluation protocol manifest hash does not match current protocol")
    if protocol != expected_protocol:
        reasons.append("evaluation protocol manifest fields do not match the current protocol")
    return reasons


def admission_reasons(
    summary: dict[str, Any],
    config: dict[str, str],
    *,
    benchmark_commit_sha: str | None = None,
    matrix_sha256: str | None = None,
    matrix_path: Path | None = None,
) -> list[str]:
    reasons: list[str] = []
    tasks = summary.get("tasks")
    if summary.get("task_count") != 1 or not isinstance(tasks, list) or len(tasks) != 1:
        return ["admission run did not preserve exactly one task row"]
    task = tasks[0]
    if not isinstance(task, dict):
        return ["admission task row is not an object"]
    for field in ("adapter_failure_count", "infrastructure_failure_count", "invalid_submission_count"):
        if summary.get(field) != 0:
            reasons.append(f"{field} must be zero")
    if summary.get("model_tool_attempt_telemetry_status") != "complete":
        reasons.append("model tool-attempt telemetry must be complete")
    if summary.get("model_tool_attempt_total") != 0:
        reasons.append("model tool-attempt total must be zero")
    if task.get("adapter_requested_model") != config["model"]:
        reasons.append("adapter requested model does not match matrix")
    if task.get("adapter_requested_effort") != config["effort"]:
        reasons.append("adapter requested effort does not match matrix")
    if task.get("adapter_cli_version") != _expected_cli_version(matrix_path or DEFAULT_MATRIX):
        reasons.append("adapter CLI version does not match the matrix")
    if task.get("adapter_output_format") != "structured_json":
        reasons.append("adapter output is not structured_json")
    if task.get("adapter_json_only_compliant") is not True:
        reasons.append("adapter output is not JSON-only compliant")
    if not re.fullmatch(r"[0-9a-f]{64}", str(task.get("adapter_prompt_sha256", ""))):
        reasons.append("adapter prompt hash is missing")
    if task.get("adapter_prompt_hash_scope") != PROMPT_HASH_SCOPE:
        reasons.append("adapter prompt-hash scope does not match")
    if task.get("adapter_profile_skill_loading_status") != PROFILE_SKILL_LOADING_STATUS:
        reasons.append("adapter profile-skill loading status does not match")
    if task.get("adapter_output_schema_sha256") != EXPECTED_OUTPUT_SCHEMA_SHA256:
        reasons.append("adapter output-schema hash does not match the current schema")
    if task.get("adapter_tool_attempt_telemetry_status") != "complete":
        reasons.append("adapter task tool-attempt telemetry must be complete")
    if task.get("adapter_tool_attempt_count") != 0:
        reasons.append("adapter task tool-attempt count must be zero")
    if summary.get("model_identity_status") not in {"verified", "requested_only_unverified"}:
        reasons.append("model identity status is invalid")
    reasons.extend(
        _source_binding_reasons(
            summary,
            benchmark_commit_sha=benchmark_commit_sha,
            matrix_sha256=matrix_sha256,
            matrix_path=matrix_path,
        )
    )
    reasons.extend(_task_binding_reasons(summary, DEFAULT_ADMISSION_TASK))
    return sorted(set(reasons))


def full_completion_reasons(
    summary: dict[str, Any],
    config: dict[str, str],
    *,
    benchmark_commit_sha: str | None = None,
    matrix_sha256: str | None = None,
    matrix_path: Path | None = None,
) -> list[str]:
    reasons: list[str] = []
    tasks = summary.get("tasks")
    if summary.get("task_count") != 63 or not isinstance(tasks, list) or len(tasks) != 63:
        return ["full run did not preserve exactly 63 task rows"]
    if summary.get("infrastructure_failure_count") != 0:
        reasons.append("infrastructure_failure_count must be zero")
    if summary.get("model_tool_attempt_telemetry_status") != "complete":
        reasons.append("model tool-attempt telemetry must be complete")
    if summary.get("model_tool_attempt_total") != 0:
        reasons.append("model tool-attempt total must be zero")
    prompt_hashes: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            reasons.append("full run contains a non-object task row")
            continue
        if task.get("adapter_requested_model") != config["model"]:
            reasons.append("full run adapter requested model mismatch")
        if task.get("adapter_requested_effort") != config["effort"]:
            reasons.append("full run adapter requested effort mismatch")
        if task.get("adapter_cli_version") != _expected_cli_version(matrix_path or DEFAULT_MATRIX):
            reasons.append("full run adapter CLI version does not match the matrix")
        if task.get("adapter_output_schema_sha256") != EXPECTED_OUTPUT_SCHEMA_SHA256:
            reasons.append("full run adapter output-schema hash does not match the current schema")
        if task.get("adapter_tool_attempt_telemetry_status") != "complete":
            reasons.append("full run adapter task tool-attempt telemetry is incomplete")
        if task.get("adapter_tool_attempt_count") != 0:
            reasons.append("full run adapter task tool-attempt count must be zero")
        prompt_hash = str(task.get("adapter_prompt_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", prompt_hash):
            reasons.append("full run adapter prompt hash is missing")
        else:
            prompt_hashes.add(prompt_hash)
        if task.get("adapter_prompt_hash_scope") != PROMPT_HASH_SCOPE:
            reasons.append("full run adapter prompt-hash scope does not match")
        if task.get("adapter_profile_skill_loading_status") != PROFILE_SKILL_LOADING_STATUS:
            reasons.append("full run adapter profile-skill loading status does not match")
    if len(prompt_hashes) != 63:
        reasons.append("full run must preserve 63 unique prompt hashes")
    if summary.get("model_identity_status") not in {"verified", "requested_only_unverified"}:
        reasons.append("full run model identity status is invalid")
    reasons.extend(
        _source_binding_reasons(
            summary,
            benchmark_commit_sha=benchmark_commit_sha,
            matrix_sha256=matrix_sha256,
            matrix_path=matrix_path,
        )
    )
    reasons.extend(_task_binding_reasons(summary, DEFAULT_FULL_TASK_PATTERN))
    return sorted(set(reasons))


def _global_blocker(run_dir: Path) -> str | None:
    sentinel_path = run_dir / "codex-global-blocker.json"
    if sentinel_path.is_file():
        try:
            sentinel = _load_json(sentinel_path)
        except (OSError, json.JSONDecodeError, ValueError):
            sentinel = {}
        if sentinel.get("code") == "codex_workspace_out_of_credits":
            return "codex_workspace_out_of_credits"
    for path in run_dir.glob("case-*/model-output.json"):
        try:
            metadata = _load_json(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if metadata.get("global_blocker") == "codex_workspace_out_of_credits":
            return "codex_workspace_out_of_credits"
    for path in run_dir.glob("case-*/codex-events.jsonl"):
        if path.is_file() and _global_blocker_code(
            path.read_text(encoding="utf-8", errors="replace"), ""
        ):
            return "codex_workspace_out_of_credits"
    return None


def _summary_record(summary: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "task_count",
        "passed_count",
        "mean_score",
        "adapter_failure_count",
        "infrastructure_failure_count",
        "invalid_submission_count",
        "model_identity_status",
        "model_label_verified_task_count",
        "model_tool_attempt_telemetry_status",
        "model_tool_attempt_total",
        "benchmark_commit_sha",
        "evaluation_protocol",
        "benchmark_source_provenance",
    )
    return {field: summary.get(field) for field in fields}


def _safe_summary_path(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("admission row summary_path must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("admission row summary_path must be a safe relative path")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("admission row summary_path escapes repository root") from exc
    return resolved


def _validated_admitted_configurations(
    admission_report: dict[str, Any],
    configurations: list[dict[str, str]],
    *,
    benchmark_commit_sha: str,
    matrix_path: Path,
) -> list[dict[str, str]]:
    matrix_rel = matrix_path.relative_to(ROOT).as_posix()
    matrix_sha256 = _file_sha256(matrix_path)
    if admission_report.get("phase") != "smoke":
        raise ValueError("full phase requires a smoke admission report")
    if admission_report.get("benchmark_commit_sha") != benchmark_commit_sha:
        raise ValueError("admission report benchmark commit must match the clean current HEAD")
    if admission_report.get("matrix_path") != matrix_rel:
        raise ValueError("admission report matrix path must match the requested matrix")
    if admission_report.get("matrix_sha256") != matrix_sha256:
        raise ValueError("admission report matrix digest must match the requested matrix")
    if admission_report.get("codex_cli_version") != _expected_cli_version(matrix_path):
        raise ValueError("admission report Codex CLI version must match the matrix")
    if admission_report.get("global_blocker") is not None:
        raise ValueError("admission report contains a global execution blocker")
    rows = admission_report.get("configurations")
    if not isinstance(rows, list) or len(rows) != len(configurations):
        raise ValueError("admission report must contain every matrix configuration")
    if admission_report.get("requested_configuration_count") != len(configurations):
        raise ValueError("admission report requested_configuration_count must cover the full matrix")
    if admission_report.get("attempted_configuration_count") != len(configurations):
        raise ValueError("admission report must attempt every matrix configuration")
    expected = {item["id"]: item for item in configurations}
    seen: set[str] = set()
    admitted: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("id") not in expected:
            raise ValueError("admission report contains an unknown configuration")
        config = expected[str(row["id"])]
        if row["id"] in seen:
            raise ValueError("admission report contains a duplicate configuration")
        seen.add(str(row["id"]))
        if row.get("model") != config["model"] or row.get("effort") != config["effort"]:
            raise ValueError(f"admission row {row['id']} model/effort does not match the matrix")
        summary_path = _safe_summary_path(row.get("summary_path"))
        if not summary_path.is_file():
            raise ValueError(f"admission row {row['id']} summary does not exist")
        summary = _load_json(summary_path)
        reasons = admission_reasons(
            summary,
            config,
            benchmark_commit_sha=benchmark_commit_sha,
            matrix_sha256=matrix_sha256,
            matrix_path=matrix_path,
        )
        status = row.get("status")
        if status == "admitted":
            if row.get("evaluator_returncode") != 0 or reasons:
                raise ValueError(f"admission row {row['id']} does not satisfy admission controls")
            admitted.append(config)
        elif status == "excluded":
            if not reasons:
                raise ValueError(f"excluded admission row {row['id']} has no reproducible exclusion")
        else:
            raise ValueError(f"admission row {row['id']} has invalid terminal status")
    if seen != set(expected):
        raise ValueError("admission report does not cover the exact matrix configuration set")
    if not admitted:
        raise ValueError("admission report contains no admitted configurations")
    return admitted


def run_matrix(
    configurations: list[dict[str, str]],
    *,
    phase: str,
    run_label: str,
    results_dir: Path,
    codex_path: Path,
    model_timeout_seconds: int,
    matrix_path: Path,
    admission_report: dict[str, Any] | None = None,
    max_configurations: int | None = None,
) -> dict[str, Any]:
    benchmark_commit_sha = _require_clean_worktree()
    if max_configurations is not None and max_configurations < 1:
        raise ValueError("max-configurations must be a positive integer")
    if not codex_path.is_file():
        raise ValueError(f"Codex CLI not found: {codex_path}")
    try:
        matrix_rel = matrix_path.relative_to(ROOT).as_posix()
        results_dir.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(
            "matrix and results directories must remain inside the benchmark repository"
        ) from exc
    matrix_sha256 = _file_sha256(matrix_path)
    matrix_configuration_count = len(configurations)
    report_path = results_dir / f"codex-matrix-{phase}-{run_label}.json"
    if report_path.exists():
        raise ValueError(f"refusing to overwrite existing matrix report: {report_path}")
    if phase == "full":
        if not isinstance(admission_report, dict):
            raise ValueError("full phase requires an admission report")
        configurations = _validated_admitted_configurations(
            admission_report,
            configurations,
            benchmark_commit_sha=benchmark_commit_sha,
            matrix_path=matrix_path,
        )
        if max_configurations is not None:
            raise ValueError("max-configurations is diagnostic-only and cannot limit the full phase")
    codex_cli_version = _require_codex_cli_version(codex_path, matrix_path)
    requested_configuration_count = len(configurations)
    if max_configurations is not None:
        configurations = configurations[:max_configurations]
    selected_configuration_count = len(configurations)

    results_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    global_blocker = None
    task_pattern = DEFAULT_ADMISSION_TASK if phase == "smoke" else "tasks/*/*.json"
    for config in configurations:
        command, run_id = _evaluator_command(
            config,
            phase=phase,
            run_label=run_label,
            task_pattern=task_pattern,
            results_dir=results_dir,
            codex_path=codex_path,
            model_timeout_seconds=model_timeout_seconds,
            matrix_path=matrix_path,
        )
        run_dir = results_dir / run_id
        if run_dir.exists():
            raise ValueError(f"refusing to reuse existing matrix run directory: {run_dir}")
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        summary_path = run_dir / "summary.json"
        summary = _load_json(summary_path) if summary_path.is_file() else {}
        reasons = (
            admission_reasons(
                summary,
                config,
                benchmark_commit_sha=benchmark_commit_sha,
                matrix_sha256=matrix_sha256,
                matrix_path=matrix_path,
            )
            if phase == "smoke"
            else full_completion_reasons(
                summary,
                config,
                benchmark_commit_sha=benchmark_commit_sha,
                matrix_sha256=matrix_sha256,
                matrix_path=matrix_path,
            )
        )
        if completed.returncode != 0:
            reasons.append(f"evaluator command returned {completed.returncode}")
        reasons = sorted(set(reasons))
        blocker = _global_blocker(run_dir) if run_dir.is_dir() else None
        if blocker:
            global_blocker = blocker
        rows.append(
            {
                **config,
                "status": (
                    "blocked_global"
                    if blocker
                    else (
                        "admitted"
                        if phase == "smoke" and not reasons
                        else "excluded"
                        if phase == "smoke"
                        else "completed"
                        if not reasons
                        else "incomplete"
                    )
                ),
                "evaluator_returncode": completed.returncode,
                "run_id": run_id,
                "summary_path": summary_path.relative_to(ROOT).as_posix() if summary_path.is_file() else None,
                "reasons": reasons,
                "summary": _summary_record(summary),
            }
        )
        if blocker:
            break

    expected_terminal_statuses = {"admitted", "excluded"} if phase == "smoke" else {"completed"}
    phase_status = (
        "blocked"
        if global_blocker
        else "diagnostic_partial"
        if selected_configuration_count < requested_configuration_count
        else "completed"
        if len(rows) == len(configurations)
        and all(row["status"] in expected_terminal_statuses for row in rows)
        else "incomplete"
    )
    report = {
        "schema_version": "authzbench-codex-matrix-run-v1",
        "phase": phase,
        "run_label": run_label,
        "benchmark_commit_sha": benchmark_commit_sha,
        "matrix_path": matrix_rel,
        "matrix_sha256": matrix_sha256,
        "codex_cli_version": codex_cli_version,
        "matrix_configuration_count": matrix_configuration_count,
        "requested_configuration_count": requested_configuration_count,
        "selected_configuration_count": selected_configuration_count,
        "attempted_configuration_count": len(rows),
        "global_blocker": global_blocker,
        "phase_status": phase_status,
        "configurations": rows,
        "claim_boundary": (
            "Public-split diagnostic execution only; not registry, leaderboard, private-holdout, "
            "hosted, API, or statistically stable model-ranking evidence."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report | {"report_path": str(report_path)}


def _matrix_exit_code(report: dict[str, Any]) -> int:
    if report.get("global_blocker"):
        return 2
    return 0 if report.get("phase_status") == "completed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AuthZBench-SaaS Codex model/effort matrix serially."
    )
    parser.add_argument("--phase", choices=["smoke", "full"], required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results" / "codex-openai-matrix")
    parser.add_argument("--codex-path", type=Path, default=Path.home() / ".local" / "bin" / "codex")
    parser.add_argument("--model-timeout-seconds", type=int, default=180)
    parser.add_argument("--admission-report", type=Path)
    parser.add_argument("--max-configurations", type=int)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.run_label):
        raise ValueError("run-label must be a safe single path component")
    matrix_path = args.matrix.resolve()
    admission_report = _load_json(args.admission_report) if args.admission_report else None
    report = run_matrix(
        load_matrix(matrix_path),
        phase=args.phase,
        run_label=args.run_label,
        results_dir=args.results_dir.resolve(),
        codex_path=args.codex_path.resolve(),
        model_timeout_seconds=args.model_timeout_seconds,
        matrix_path=matrix_path,
        admission_report=admission_report,
        max_configurations=args.max_configurations,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return _matrix_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
