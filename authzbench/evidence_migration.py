from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from authzbench.score import score_submission


MIGRATION_SCHEMA_VERSION = "authzbench-rescore-artifact-v1"
MIGRATION_TOOL_VERSION = "score-policy-v2-migration-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is unreadable or invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def build_rescore_artifact(
    *,
    task_path: Path,
    submission_path: Path,
    source_summary_path: Path,
) -> dict[str, Any]:
    """Build one v2 re-score artifact without modifying any source artifact."""
    for path, label in (
        (task_path, "task"),
        (submission_path, "submission"),
        (source_summary_path, "source summary"),
    ):
        if not path.is_file():
            raise ValueError(f"{label} is missing: {path}")

    task = _load_object(task_path, "task")
    submission = _load_object(submission_path, "submission")
    source_summary = _load_object(source_summary_path, "source summary")
    source_policy = source_summary.get("score_policy_version", "score-policy-v1")
    if source_policy != "score-policy-v1":
        raise ValueError(f"source summary policy must be score-policy-v1, got {source_policy!r}")

    source_task_count = source_summary.get("task_count")
    if not isinstance(source_task_count, int) or source_task_count <= 0:
        raise ValueError("source summary must contain a positive task_count")
    if task.get("id") != submission.get("task_id"):
        raise ValueError("task and submission task_id do not match")

    score = score_submission(task, submission, score_policy_version="score-policy-v2")
    return {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": "rescored_from_policy_v1",
        "source_policy_version": "score-policy-v1",
        "target_policy_version": "score-policy-v2",
        "tool_version": MIGRATION_TOOL_VERSION,
        "task_id": task["id"],
        "source": {
            "task_sha256": sha256_file(task_path),
            "submission_sha256": sha256_file(submission_path),
            "summary_sha256": sha256_file(source_summary_path),
            "summary_task_count": source_task_count,
        },
        "score": score,
    }


def validate_rescore_artifact(artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "status": "rescored_from_policy_v1",
        "source_policy_version": "score-policy-v1",
        "target_policy_version": "score-policy-v2",
        "tool_version": MIGRATION_TOOL_VERSION,
    }
    for field, value in expected.items():
        if artifact.get(field) != value:
            errors.append(f"{field} must be {value!r}")
    if not isinstance(artifact.get("task_id"), str) or not artifact["task_id"]:
        errors.append("task_id must be a non-empty string")
    source = artifact.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        for field in ("task_sha256", "submission_sha256", "summary_sha256"):
            value = source.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                errors.append(f"source.{field} must be a lowercase SHA-256 digest")
        if not isinstance(source.get("summary_task_count"), int) or source["summary_task_count"] <= 0:
            errors.append("source.summary_task_count must be a positive integer")
    score = artifact.get("score")
    if not isinstance(score, dict):
        errors.append("score must be an object")
    else:
        if score.get("score_policy_version") != "score-policy-v2":
            errors.append("score.score_policy_version must be 'score-policy-v2'")
        if score.get("task_id") != artifact.get("task_id"):
            errors.append("score.task_id must match task_id")
    return errors
