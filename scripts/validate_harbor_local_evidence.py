from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_PATH = ROOT / "artifact" / "harbor-local-execution-smoke.json"
SCHEMA_VERSION = "harbor-local-execution-smoke-v1"
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")
ALLOWED_ABSOLUTE_PREFIXES = ("/logs/artifacts/", "/logs/verifier/")
PRIVATE_MARKERS = (
    "tasks_private",
    "private route:",
    "private seed:",
    "raw private output",
    "credential:",
    "oracle:",
)
DISALLOWED_OVERCLAIMS = (
    "accepted by",
    "endorsed by",
    "hosted leaderboard ready",
    "v1 ready",
    "v1-ready",
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(_text_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(_text_values(child))
        return values
    if isinstance(value, str):
        return [value]
    return []


def _public_safety_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for value in _text_values(data):
        lower = value.lower()
        for marker in PRIVATE_MARKERS:
            if marker in lower:
                errors.append(f"private marker is not allowed: {marker}")
        for marker in DISALLOWED_OVERCLAIMS:
            if marker in lower:
                errors.append(f"overclaim is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(value):
            if not any(match.startswith(prefix) for prefix in ALLOWED_ABSOLUTE_PREFIXES):
                errors.append(f"local absolute path is not allowed: {match}")
    return errors


def _checked_in_evidence_path(path: Path) -> bool:
    try:
        return path.resolve() == DEFAULT_EVIDENCE_PATH.resolve()
    except FileNotFoundError:
        return False


def _source_fingerprint_errors(path: Path, benchmark_source_sha: str, benchmark_source_tree_sha: str) -> list[str]:
    if not _checked_in_evidence_path(path):
        return []
    if not re.fullmatch(r"[0-9a-f]{7,40}", benchmark_source_sha):
        return ["benchmark_source_sha must be a git SHA for checked-in smoke evidence"]
    if not re.fullmatch(r"[0-9a-f]{40}", benchmark_source_tree_sha):
        return ["benchmark_source_tree_sha must be a full git tree SHA for checked-in smoke evidence"]
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{benchmark_source_tree_sha}^{{tree}}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["benchmark_source_tree_sha must exist in this repository for checked-in smoke evidence"]
    return []


def validate_harbor_local_evidence(path: Path = DEFAULT_EVIDENCE_PATH) -> dict[str, Any]:
    try:
        data = _load_json(path)
    except Exception as exc:
        return {"errors": [str(exc)], "passed": False}

    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("evidence_status") != "local_harbor_execution_smoke":
        errors.append("evidence_status must be local_harbor_execution_smoke")
    boundary = str(data.get("public_claim_boundary", ""))
    if "not parity evidence" not in boundary or "not v1 readiness" not in boundary:
        errors.append("public_claim_boundary must reject parity and v1 readiness claims")
    if data.get("harbor_execution_verified") is not True:
        errors.append("harbor_execution_verified must be true")
    if data.get("parity_verified") is not False:
        errors.append("parity_verified must be false")
    if data.get("public_outputs_redacted") is not True:
        errors.append("public_outputs_redacted must be true")
    if data.get("private_artifacts_tracked") is not False:
        errors.append("private_artifacts_tracked must be false")
    if data.get("raw_harbor_jobs_tracked") is not False:
        errors.append("raw_harbor_jobs_tracked must be false")
    if not isinstance(data.get("benchmark_source_sha"), str) or len(data["benchmark_source_sha"]) < 7:
        errors.append("benchmark_source_sha is required")
    if not isinstance(data.get("benchmark_source_tree_sha"), str) or not data["benchmark_source_tree_sha"].strip():
        errors.append("benchmark_source_tree_sha is required")
        benchmark_source_tree_sha = ""
    else:
        benchmark_source_tree_sha = data["benchmark_source_tree_sha"]
    if isinstance(data.get("benchmark_source_sha"), str):
        errors.extend(_source_fingerprint_errors(path, data["benchmark_source_sha"], benchmark_source_tree_sha))
    if not isinstance(data.get("harbor_version"), str) or not data["harbor_version"].strip():
        errors.append("harbor_version is required")
    if not isinstance(data.get("docker_server_version"), str) or not data["docker_server_version"].strip():
        errors.append("docker_server_version is required")
    if not isinstance(data.get("harbor_run_id"), str) or not data["harbor_run_id"].strip():
        errors.append("harbor_run_id is required")
    if data.get("task_count") != 1:
        errors.append("task_count must be 1 for the checked-in smoke evidence")
    if data.get("n_total_trials") != 1:
        errors.append("n_total_trials must be 1")
    if data.get("n_completed_trials") != 1:
        errors.append("n_completed_trials must be 1")
    if data.get("n_errored_trials") != 0:
        errors.append("n_errored_trials must be 0")
    if data.get("oracle_solution_mode") != "secure-control-empty-findings":
        errors.append("oracle_solution_mode must be secure-control-empty-findings")
    if data.get("reward_mean") != 1.0:
        errors.append("reward_mean must be 1.0 for the secure-control empty-findings smoke")
    if data.get("scorer_reward_parity_verified") is not True:
        errors.append("scorer_reward_parity_verified must be true for the secure-control smoke")
    native_score = data.get("native_score_summary")
    if not isinstance(native_score, dict):
        errors.append("native_score_summary is required")
    else:
        if native_score.get("submission_shape") != "secure_control_empty_findings":
            errors.append("native_score_summary.submission_shape must be secure_control_empty_findings")
        if native_score.get("score") != 1.0:
            errors.append("native_score_summary.score must be 1.0")
        if native_score.get("passed") is not True:
            errors.append("native_score_summary.passed must be true")
        if native_score.get("control_replay_passed") is not True:
            errors.append("native_score_summary.control_replay_passed must be true")
    if data.get("verifier_reward_files") != ["reward.json", "reward.txt"]:
        errors.append("verifier_reward_files must list reward.json and reward.txt")
    reward_reason = str(data.get("expected_reward_reason", "")).lower()
    if "secure-control" not in reward_reason or "not full adapter parity" not in reward_reason:
        errors.append("expected_reward_reason must explain the secure-control smoke boundary")
    blockers = data.get("blocked_until")
    if not isinstance(blockers, list) or not blockers:
        errors.append("blocked_until must list remaining evidence blockers")
    else:
        joined = " ".join(str(item).lower() for item in blockers)
        if "submission" not in joined or "parity" not in joined:
            errors.append("blocked_until must preserve submission and parity blockers")

    errors.extend(_public_safety_errors(data))
    return {"errors": sorted(set(errors)), "passed": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe local Harbor smoke evidence.")
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE_PATH)
    args = parser.parse_args()
    result = validate_harbor_local_evidence(args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
