from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json, runner_integrity_envelope


REQUIRED_FIELDS = {
    "leaderboard_schema_version",
    "eligibility_policy_version",
    "benchmark_fingerprint",
    "benchmark_fingerprint_provenance",
    "comparability_key",
    "repeat_evidence",
    "source_run_summaries",
    "agent",
    "model",
    "harness_type",
    "run_id",
    "benchmark_version",
    "benchmark_commit_sha",
    "split",
    "task_count",
    "public_task_count",
    "private_holdout_task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
    "v0_metric_profile",
    "v0_passed_count",
    "v0_mean_score",
    "invalid_submission_count",
    "invalid_submission_rate",
    "exploit_proven_task_count",
    "exploit_proven_success_rate",
    "vulnerable_full_pass_count",
    "control_false_report_rate",
    "control_execution_pass_rate",
    "authorized_allow_pass_rate",
    "false_positive_rate",
    "boundary_reasoning_pass_rate",
    "target_request_coverage_rate",
    "mean_score",
    "safety_violations",
    "median_duration_seconds",
    "run_count",
    "variance_or_ci",
    "baseline_kind",
    "leaderboard_eligible",
}

STRING_FIELDS = {
    "leaderboard_schema_version",
    "eligibility_policy_version",
    "comparability_key",
    "benchmark_fingerprint_provenance",
    "agent",
    "model",
    "harness_type",
    "run_id",
    "benchmark_version",
    "benchmark_commit_sha",
    "split",
    "v0_metric_profile",
    "variance_or_ci",
    "baseline_kind",
    "source_run_summary",
}

LEADERBOARD_SCHEMA_VERSION = "leaderboard-submission-v1"
ELIGIBILITY_POLICY_VERSION = "leaderboard-eligibility-v1"
FINGERPRINT_SCHEMA_VERSION = "benchmark-fingerprint-v1"
FINGERPRINT_FIELDS = {
    "schema_version",
    "task_set_sha256",
    "task_path_set_sha256",
    "score_policy_version",
    "scorer_contract",
    "evidence_contract_version",
    "task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
}
FINGERPRINT_COUNT_FIELDS = {
    "task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
}
FINGERPRINT_STRING_FIELDS = FINGERPRINT_FIELDS - FINGERPRINT_COUNT_FIELDS
REPEAT_AGGREGATIONS = {"single_run", "primary_run"}
COMPARABILITY_KEY_PATTERN = re.compile(r"^authzbench-cmp-v1:[0-9a-f]{64}$")

INT_FIELDS = {
    "task_count",
    "public_task_count",
    "private_holdout_task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
    "v0_passed_count",
    "invalid_submission_count",
    "exploit_proven_task_count",
    "vulnerable_full_pass_count",
    "safety_violations",
    "run_count",
}

RATE_FIELDS = {
    "v0_mean_score",
    "invalid_submission_rate",
    "exploit_proven_success_rate",
    "control_false_report_rate",
    "control_execution_pass_rate",
    "authorized_allow_pass_rate",
    "false_positive_rate",
    "boundary_reasoning_pass_rate",
    "target_request_coverage_rate",
    "mean_score",
}

VALID_SPLITS = {"public", "private-holdout", "combined"}
VALID_BASELINE_KINDS = {"harness_check", "model_baseline", "tool_agent_baseline"}
VALID_HARNESS_TYPES = {"tool-agent", "no-tools-model", "scripted", "scripted-live-http"}
LIVE_HARNESS_TYPES = {"tool-agent", "scripted-live-http"}
EXPECTED_HARNESS_BY_KIND = {
    "harness_check": {"scripted", "scripted-live-http"},
    "model_baseline": {"no-tools-model"},
    "tool_agent_baseline": {"tool-agent"},
}

ROTATION_METADATA_PATH = ROOT / "tasks_private" / "holdout" / "rotation-metadata.json"

# Pack roles that are eligible to back a private-holdout or combined
# leaderboard submission. Today the only eligible role is "active";
# "shadow" packs are diagnostic only and "retired" packs are
# historical evidence that must not be scored as current.
ELIGIBLE_PACK_ROLES = frozenset({"active"})


def _load_rotation_metadata() -> dict[str, dict[str, str]]:
    """Return a map of pack fingerprint -> pack dict. Returns an
    empty map if the rotation-metadata file is missing or malformed.
    The leaderboard validator then has to fail closed for any
    private-holdout submission because there is no active pack to
    match against.
    """
    if not ROTATION_METADATA_PATH.is_file():
        return {}
    try:
        data = load_json(ROTATION_METADATA_PATH)
    except Exception:  # noqa: BLE001 - rotation metadata may be missing in slim checkouts.
        return {}
    packs = data.get("packs") if isinstance(data, dict) else None
    if not isinstance(packs, list):
        return {}
    out: dict[str, dict[str, str]] = {}
    for pack in packs:
        if not isinstance(pack, dict):
            continue
        fingerprint = str(pack.get("fingerprint_sha256", "")).strip()
        if fingerprint:
            out[fingerprint] = {
                "id": str(pack.get("id", "")),
                "role": str(pack.get("role", "")),
            }
    return out


def _validate_private_pack_role(
    submission: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Goal-external-validation-coverage.md objective-5 CI gate.

    The hard-fail rule applies to leaderboard-eligible private-holdout
    or combined submissions: the fingerprint must match an active
    pack in tasks_private/holdout/rotation-metadata.json. A missing
    fingerprint, an unknown fingerprint, or a non-active role
    (shadow or retired) is a hard error.

    Non-eligible private-holdout submissions (i.e. evidence rows
    kept on disk but explicitly not on the leaderboard) are
    allowed to omit the fingerprint; the validator emits a
    warning so reviewers can spot legacy evidence that pre-dates
    the rotation-metadata convention. Combined splits follow the
    same rule as private-holdout.
    """
    split = submission.get("split")
    if split not in {"private-holdout", "combined"}:
        return
    leaderboard_eligible = submission.get("leaderboard_eligible") is True
    fingerprint = str(submission.get("private_pack_fingerprint_sha256", "")).strip()
    metadata = _load_rotation_metadata()
    if not fingerprint:
        if leaderboard_eligible:
            errors.append(
                f"split={split} submissions must declare private_pack_fingerprint_sha256"
            )
        else:
            warnings.append(
                f"split={split} submission does not declare private_pack_fingerprint_sha256; "
                "this is allowed for non-leaderboard-eligible legacy evidence rows but "
                "becomes a hard error for any row marked leaderboard_eligible=true"
            )
        return
    if not metadata:
        if leaderboard_eligible:
            errors.append(
                "private pack role cannot be verified because tasks_private/holdout/"
                "rotation-metadata.json is missing or malformed"
            )
        else:
            warnings.append(
                "private pack role cannot be verified because tasks_private/holdout/"
                "rotation-metadata.json is missing or malformed; non-eligible legacy row"
            )
        return
    pack = metadata.get(fingerprint)
    if pack is None:
        if leaderboard_eligible:
            errors.append(
                f"private_pack_fingerprint_sha256 {fingerprint!r} does not match any "
                "known pack in tasks_private/holdout/rotation-metadata.json"
            )
        else:
            warnings.append(
                f"private_pack_fingerprint_sha256 {fingerprint!r} does not match any known pack"
            )
        return
    if pack["role"] not in ELIGIBLE_PACK_ROLES:
        if leaderboard_eligible:
            errors.append(
                f"private_pack_fingerprint_sha256 {fingerprint!r} matches pack "
                f"{pack['id']!r} (role={pack['role']!r}); only role=active packs are "
                "eligible to back a private-holdout or combined leaderboard submission"
            )
        else:
            warnings.append(
                f"private_pack_fingerprint_sha256 points at non-active pack "
                f"{pack['id']!r} (role={pack['role']!r}); legacy evidence row only"
            )


SOURCE_SUMMARY_FIELDS = {
    "agent",
    "model",
    "harness_type",
    "benchmark_version",
    "benchmark_commit_sha",
    "task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
    "v0_metric_profile",
    "v0_passed_count",
    "v0_mean_score",
    "invalid_submission_count",
    "invalid_submission_rate",
    "exploit_proven_task_count",
    "exploit_proven_success_rate",
    "vulnerable_full_pass_count",
    "control_false_report_rate",
    "control_execution_pass_rate",
    "authorized_allow_pass_rate",
    "false_positive_rate",
    "boundary_reasoning_pass_rate",
    "target_request_coverage_rate",
    "mean_score",
}


def comparability_key(submission: dict[str, Any]) -> str:
    payload = {
        "benchmark_fingerprint": submission.get("benchmark_fingerprint"),
        "benchmark_commit_sha": submission.get("benchmark_commit_sha"),
        "benchmark_version": submission.get("benchmark_version"),
        "eligibility_policy_version": submission.get("eligibility_policy_version"),
        "leaderboard_schema_version": submission.get("leaderboard_schema_version"),
        "split": submission.get("split"),
        "v0_metric_profile": submission.get("v0_metric_profile"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"authzbench-cmp-v1:{hashlib.sha256(encoded).hexdigest()}"


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)) or value is None


def _rate(value: Any, field: str, errors: list[str]) -> float | None:
    if value is None:
        if field == "target_request_coverage_rate":
            return None
        errors.append(f"{field} must be a number between 0 and 1")
        return None
    if not _is_number(value):
        errors.append(f"{field} must be a number between 0 and 1")
        return None
    numeric = float(value)
    if numeric < 0 or numeric > 1:
        errors.append(f"{field} must be between 0 and 1")
    return numeric


def _close(actual: Any, expected: float) -> bool:
    if not _is_number(actual) or actual is None:
        return False
    return abs(float(actual) - round(expected, 4)) <= 0.0001


def _values_match(left: Any, right: Any) -> bool:
    if _is_number(left) or _is_number(right):
        if left is None or right is None:
            return left is None and right is None
        return _close(left, float(right))
    return left == right


def _has_variance_evidence(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if stripped == "not_repeated":
        return False
    if stripped.startswith(("stddev=", "variance=")):
        try:
            return float(stripped.split("=", 1)[1]) >= 0
        except ValueError:
            return False
    if stripped.startswith("ci95=[") and stripped.endswith("]"):
        raw_bounds = stripped[len("ci95=[") : -1].split(",")
        if len(raw_bounds) != 2:
            return False
        try:
            low, high = (float(item) for item in raw_bounds)
        except ValueError:
            return False
        return 0 <= low <= high <= 1
    return False


def _validate_types(submission: dict[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(submission))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    for field in STRING_FIELDS & set(submission):
        if not isinstance(submission[field], str) or not submission[field].strip():
            errors.append(f"{field} must be a non-empty string")
    for field in INT_FIELDS & set(submission):
        if not _is_int(submission[field]):
            errors.append(f"{field} must be an integer")
        elif int(submission[field]) < 0:
            errors.append(f"{field} must be non-negative")
    for field in RATE_FIELDS & set(submission):
        _rate(submission[field], field, errors)
    if "leaderboard_eligible" in submission and not isinstance(submission["leaderboard_eligible"], bool):
        errors.append("leaderboard_eligible must be boolean")
    if "median_duration_seconds" in submission:
        duration = submission["median_duration_seconds"]
        if duration is not None and (not _is_number(duration) or float(duration) < 0):
            errors.append("median_duration_seconds must be null or a non-negative number")


def _validate_fingerprint(submission: dict[str, Any], errors: list[str]) -> None:
    fingerprint = submission.get("benchmark_fingerprint")
    if not isinstance(fingerprint, dict):
        errors.append("benchmark_fingerprint must be an object")
        return
    missing = sorted(FINGERPRINT_FIELDS - set(fingerprint))
    if missing:
        errors.append(f"benchmark_fingerprint missing required fields: {', '.join(missing)}")
    for field in sorted(FINGERPRINT_STRING_FIELDS & set(fingerprint)):
        if not isinstance(fingerprint[field], str) or not fingerprint[field].strip():
            errors.append(f"benchmark_fingerprint.{field} must be a non-empty string")
    for field in sorted(FINGERPRINT_COUNT_FIELDS & set(fingerprint)):
        if not _is_int(fingerprint[field]) or int(fingerprint[field]) < 0:
            errors.append(f"benchmark_fingerprint.{field} must be a non-negative integer")
    if fingerprint.get("schema_version") != FINGERPRINT_SCHEMA_VERSION:
        errors.append(
            f"benchmark_fingerprint.schema_version must be {FINGERPRINT_SCHEMA_VERSION}"
        )
    for field in ("task_set_sha256", "task_path_set_sha256"):
        value = fingerprint.get(field)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is None:
            errors.append(f"benchmark_fingerprint.{field} must be a lowercase SHA-256 digest")

    for field in FINGERPRINT_COUNT_FIELDS:
        if field in fingerprint and field in submission and fingerprint[field] != submission[field]:
            errors.append(f"benchmark_fingerprint.{field} must match submission {field}")


def _validate_repeat_evidence(submission: dict[str, Any], errors: list[str]) -> None:
    repeat = submission.get("repeat_evidence")
    if not isinstance(repeat, dict):
        errors.append("repeat_evidence must be an object")
        return
    allowed_fields = {"aggregation", "primary_run_id", "source_run_ids", "variance_metric"}
    unexpected = sorted(set(repeat) - allowed_fields)
    if unexpected:
        errors.append(f"repeat_evidence has unsupported fields: {', '.join(unexpected)}")

    aggregation = repeat.get("aggregation")
    if aggregation not in REPEAT_AGGREGATIONS:
        errors.append(f"repeat_evidence.aggregation must be one of {', '.join(sorted(REPEAT_AGGREGATIONS))}")
    source_run_ids = repeat.get("source_run_ids")
    if not isinstance(source_run_ids, list) or not source_run_ids:
        errors.append("repeat_evidence.source_run_ids must be a non-empty list")
        source_run_ids = []
    elif any(not isinstance(item, str) or not item.strip() for item in source_run_ids):
        errors.append("repeat_evidence.source_run_ids entries must be non-empty strings")
    elif len(set(source_run_ids)) != len(source_run_ids):
        errors.append("repeat_evidence.source_run_ids must be unique")

    run_count = submission.get("run_count")
    if _is_int(run_count) and len(source_run_ids) != int(run_count):
        errors.append("repeat_evidence.source_run_ids length must equal run_count")

    primary_run_id = repeat.get("primary_run_id")
    if not isinstance(primary_run_id, str) or not primary_run_id.strip():
        errors.append("repeat_evidence.primary_run_id must be a non-empty string")
    elif source_run_ids and primary_run_id not in source_run_ids:
        errors.append("repeat_evidence.primary_run_id must appear in source_run_ids")
    if submission.get("run_id") != primary_run_id:
        errors.append("run_id must equal repeat_evidence.primary_run_id")

    if aggregation == "single_run":
        if run_count != 1:
            errors.append("single_run repeat evidence requires run_count=1")
        if submission.get("variance_or_ci") != "not_repeated":
            errors.append("single_run repeat evidence requires variance_or_ci=not_repeated")
    elif aggregation == "primary_run":
        if not _is_int(run_count) or int(run_count) < 2:
            errors.append("primary_run repeat evidence requires run_count>=2")
        variance_metric = repeat.get("variance_metric")
        if variance_metric not in RATE_FIELDS:
            errors.append("primary_run repeat evidence requires variance_metric naming a rate field")


def _resolve_source_summaries(
    submission_path: Path,
    submission: dict[str, Any],
    errors: list[str],
) -> list[tuple[Path, dict[str, Any]]]:
    raw_paths = submission.get("source_run_summaries")
    if not isinstance(raw_paths, list) or not raw_paths:
        errors.append("source_run_summaries must be a non-empty list")
        return []
    if any(not isinstance(item, str) or not item.strip() for item in raw_paths):
        errors.append("source_run_summaries entries must be non-empty relative path strings")
        return []
    if len(set(raw_paths)) != len(raw_paths):
        errors.append("source_run_summaries entries must be unique")

    primary_path = submission.get("source_run_summary")
    if isinstance(primary_path, str) and primary_path not in raw_paths:
        errors.append("source_run_summary must also appear in source_run_summaries")

    resolved: list[tuple[Path, dict[str, Any]]] = []
    for raw_path in raw_paths:
        summary_path = _resolve_source_summary(submission_path, raw_path, errors)
        if summary_path is None:
            continue
        summary = load_json(summary_path)
        if not isinstance(summary, dict):
            errors.append(f"source summary must contain a JSON object: {_display_path(summary_path)}")
            continue
        resolved.append((summary_path, summary))
    return resolved


def _validate_repeat_sources(
    submission_path: Path,
    submission: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    sources = _resolve_source_summaries(submission_path, submission, errors)
    repeat = submission.get("repeat_evidence")
    if not isinstance(repeat, dict):
        return
    source_run_ids = repeat.get("source_run_ids")
    if not isinstance(source_run_ids, list):
        return

    resolved_run_ids: list[str] = []
    for summary_path, summary in sources:
        run_id = summary.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            errors.append(f"{_display_path(summary_path)}: run_id is required")
            continue
        resolved_run_ids.append(run_id)
        for field in (
            "agent",
            "model",
            "harness_type",
            "benchmark_version",
            "benchmark_commit_sha",
            "benchmark_fingerprint",
            "v0_metric_profile",
        ):
            if summary.get(field) != submission.get(field):
                message = f"{_display_path(summary_path)}: {field} does not match submission"
                if submission.get("leaderboard_eligible") is True:
                    errors.append(message)
                else:
                    warnings.append(message)
        if submission.get("leaderboard_eligible") is True:
            if summary.get("benchmark_fingerprint_provenance") != "runner-emitted":
                errors.append(f"{_display_path(summary_path)}: eligible source requires runner-emitted fingerprint")
            integrity = summary.get("runner_integrity")
            expected_integrity = runner_integrity_envelope(
                summary,
                generator="scripts/protected_private_eval.py",
            )
            if integrity != expected_integrity:
                errors.append(f"{_display_path(summary_path)}: runner_integrity is missing or invalid")
            protected = summary.get("protected_execution")
            if not isinstance(protected, dict) or protected.get("host_private_paths_denied") is not True:
                errors.append(f"{_display_path(summary_path)}: eligible private source requires host private-path denial")

    if sorted(resolved_run_ids) != sorted(source_run_ids):
        message = "source_run_summaries run_id values must exactly match repeat_evidence.source_run_ids"
        if submission.get("leaderboard_eligible") is True:
            errors.append(message)
        else:
            warnings.append(message)

    if submission.get("leaderboard_eligible") is not True:
        return
    if len(sources) != submission.get("run_count"):
        errors.append("leaderboard_eligible submissions require one source summary per run")
        return
    variance_metric = repeat.get("variance_metric")
    values: list[float] = []
    for summary_path, summary in sources:
        value = summary.get(variance_metric)
        if not _is_number(value) or value is None:
            errors.append(f"{_display_path(summary_path)}: {variance_metric} must be numeric for variance evidence")
            continue
        values.append(float(value))
    if len(values) != len(sources):
        return
    variance = submission.get("variance_or_ci")
    if isinstance(variance, str) and variance.startswith("stddev="):
        expected = round(statistics.pstdev(values), 4)
        try:
            actual = float(variance.split("=", 1)[1])
        except ValueError:
            return
        if abs(actual - expected) > 0.0001:
            errors.append(
                f"variance_or_ci stddev must equal the population standard deviation of "
                f"{variance_metric} across source runs ({expected:.4f})"
            )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _resolve_source_summary(submission_path: Path, raw_path: str, errors: list[str]) -> Path | None:
    if not raw_path.strip():
        errors.append("source_run_summary must be a non-empty relative path when present")
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        errors.append("source_run_summary must be a relative path")
        return None
    search_paths = [submission_path.parent / candidate, ROOT / candidate]
    for search_path in search_paths:
        if search_path.exists():
            return search_path
    errors.append(f"source_run_summary does not exist: {raw_path}")
    return None


def _recompute_from_tasks(summary: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    tasks = summary.get("tasks")
    if tasks is None:
        return {}
    if not isinstance(tasks, list):
        errors.append("source_run_summary tasks must be a list when present")
        return {}
    normalized_tasks = []
    for index, item in enumerate(tasks, start=1):
        if not isinstance(item, dict):
            errors.append(f"source_run_summary tasks[{index}] must be an object")
            continue
        normalized_tasks.append(item)
    tasks = normalized_tasks

    def task_int(item: dict[str, Any], field: str, default: int = 0) -> int:
        value = item.get(field, default)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"source_run_summary task {item.get('task_id', '<unknown>')} field {field} must be an integer")
            return default
        return value

    def task_float(item: dict[str, Any], field: str, default: float = 0.0) -> float:
        value = item.get(field, default)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"source_run_summary task {item.get('task_id', '<unknown>')} field {field} must be a number")
            return default
        return float(value)

    task_count = len(tasks)
    vulnerable = [item for item in tasks if item.get("expected_vulnerable") is True]
    controls = [item for item in tasks if item.get("expected_vulnerable") is False]
    denial_controls = [item for item in controls if item.get("control_type") == "denial"]
    authorized_allow_controls = [item for item in controls if item.get("control_type") == "authorized_allow"]
    target_log_tasks = [item for item in tasks if "target_request_count" in item]
    target_log_correlated = sum(1 for item in target_log_tasks if task_int(item, "target_request_count") > 0)
    v0_passed_count = sum(
        1
        for item in tasks
        if (
            item.get("expected_vulnerable") is True
            and item.get("exploit_proof") == 1
            and item.get("boundary_reasoning") == 1
            and item.get("control_replay_passed") is True
            and item.get("safety") == 1
        )
        or (item.get("expected_vulnerable") is False and item.get("passed") is True)
    )
    return {
        "task_count": task_count,
        "vulnerable_task_count": len(vulnerable),
        "control_task_count": len(controls),
        "denial_control_task_count": len(denial_controls),
        "authorized_allow_control_task_count": len(authorized_allow_controls),
        "v0_passed_count": v0_passed_count,
        "v0_mean_score": round(v0_passed_count / task_count, 4) if task_count else 0,
        "invalid_submission_count": sum(1 for item in tasks if item.get("invalid_submission") is True),
        "invalid_submission_rate": round(
            sum(1 for item in tasks if item.get("invalid_submission") is True) / task_count,
            4,
        )
        if task_count
        else 0,
        "exploit_proven_task_count": sum(1 for item in vulnerable if item.get("exploit_proof") == 1),
        "exploit_proven_success_rate": round(
            sum(1 for item in vulnerable if item.get("exploit_proof") == 1) / len(vulnerable),
            4,
        )
        if vulnerable
        else None,
        "vulnerable_full_pass_count": sum(1 for item in vulnerable if item.get("passed") is True),
        "boundary_reasoning_pass_rate": round(
            sum(1 for item in vulnerable if item.get("boundary_reasoning") == 1) / len(vulnerable),
            4,
        )
        if vulnerable
        else None,
        "control_false_report_rate": round(
            sum(1 for item in controls if task_int(item, "submission_finding_count") > 0) / len(controls),
            4,
        )
        if controls
        else None,
        "control_execution_pass_rate": round(
            sum(1 for item in controls if item.get("control_replay_passed") is True) / len(controls),
            4,
        )
        if controls
        else None,
        "authorized_allow_pass_rate": round(
            sum(1 for item in authorized_allow_controls if item.get("passed") is True)
            / len(authorized_allow_controls),
            4,
        )
        if authorized_allow_controls
        else None,
        "false_positive_rate": round(
            sum(1 for item in controls if task_int(item, "submission_finding_count") > 0) / len(controls), 4
        )
        if controls
        else None,
        "mean_score": round(sum(task_float(item, "score") for item in tasks) / task_count, 4) if task_count else 0,
        "target_request_coverage_rate": round(target_log_correlated / len(target_log_tasks), 4)
        if target_log_tasks
        else None,
    }


def _validate_source_summary(
    submission_path: Path,
    submission: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    require_source_summary: bool,
) -> None:
    raw_path = submission.get("source_run_summary")
    if raw_path is None:
        if require_source_summary or submission.get("leaderboard_eligible") is True:
            errors.append("source_run_summary is required for this validation gate")
        return
    if not isinstance(raw_path, str):
        errors.append("source_run_summary must be a relative path string")
        return
    summary_path = _resolve_source_summary(submission_path, raw_path, errors)
    if summary_path is None:
        return
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        errors.append(f"source_run_summary must contain a JSON object: {_display_path(summary_path)}")
        return

    for field in sorted(SOURCE_SUMMARY_FIELDS):
        if field not in summary:
            errors.append(f"source_run_summary missing field: {field}")
        elif field in submission and not _values_match(submission[field], summary[field]):
            errors.append(
                f"{field} does not match source_run_summary "
                f"({_display_path(summary_path)} has {summary[field]!r}, submission has {submission[field]!r})"
            )

    if "run_id" in summary:
        if submission.get("run_id") != summary.get("run_id"):
            errors.append(
                f"run_id does not match source_run_summary "
                f"({_display_path(summary_path)} has {summary.get('run_id')!r}, submission has {submission.get('run_id')!r})"
            )
    else:
        warnings.append("source_run_summary has no run_id; identity cross-check is limited")

    recomputed = _recompute_from_tasks(summary, errors)
    for field, expected in sorted(recomputed.items()):
        if field in summary and not _values_match(summary[field], expected):
            errors.append(
                f"source_run_summary {field} is inconsistent with its tasks "
                f"({_display_path(summary_path)} has {summary[field]!r}, recomputed {expected!r})"
            )


def validate_submission(
    submission_path: Path,
    *,
    false_positive_threshold: float = 0.05,
    invalid_submission_threshold: float = 0.05,
    min_target_request_coverage: float = 1.0,
    min_private_holdout_count: int = 20,
    require_source_summary: bool = False,
) -> dict[str, Any]:
    submission = load_json(submission_path)
    errors: list[str] = []
    warnings: list[str] = []
    _validate_types(submission, errors)
    _validate_fingerprint(submission, errors)
    _validate_repeat_evidence(submission, errors)

    if submission.get("leaderboard_schema_version") != LEADERBOARD_SCHEMA_VERSION:
        errors.append(f"leaderboard_schema_version must be {LEADERBOARD_SCHEMA_VERSION}")
    if submission.get("eligibility_policy_version") != ELIGIBILITY_POLICY_VERSION:
        errors.append(f"eligibility_policy_version must be {ELIGIBILITY_POLICY_VERSION}")
    supplied_comparability_key = submission.get("comparability_key")
    if isinstance(supplied_comparability_key, str):
        if COMPARABILITY_KEY_PATTERN.fullmatch(supplied_comparability_key) is None:
            errors.append("comparability_key must use authzbench-cmp-v1:<lowercase-sha256>")
        elif supplied_comparability_key != comparability_key(submission):
            errors.append("comparability_key does not match the submission comparability contract")

    split = submission.get("split")
    harness_type = submission.get("harness_type")
    baseline_kind = submission.get("baseline_kind")
    leaderboard_eligible = submission.get("leaderboard_eligible") is True

    _validate_source_summary(submission_path, submission, errors, warnings, require_source_summary)
    _validate_repeat_sources(submission_path, submission, errors, warnings)

    if split not in VALID_SPLITS:
        errors.append(f"split must be one of {', '.join(sorted(VALID_SPLITS))}")
    if harness_type not in VALID_HARNESS_TYPES:
        errors.append(f"harness_type must be one of {', '.join(sorted(VALID_HARNESS_TYPES))}")
    if baseline_kind not in VALID_BASELINE_KINDS:
        errors.append(f"baseline_kind must be one of {', '.join(sorted(VALID_BASELINE_KINDS))}")
    elif harness_type in VALID_HARNESS_TYPES and harness_type not in EXPECTED_HARNESS_BY_KIND[baseline_kind]:
        expected = ", ".join(sorted(EXPECTED_HARNESS_BY_KIND[baseline_kind]))
        errors.append(f"{baseline_kind} submissions must use harness_type: {expected}")

    task_count = int(submission.get("task_count", 0)) if _is_int(submission.get("task_count")) else 0
    public_count = int(submission.get("public_task_count", 0)) if _is_int(submission.get("public_task_count")) else 0
    private_count = (
        int(submission.get("private_holdout_task_count", 0))
        if _is_int(submission.get("private_holdout_task_count"))
        else 0
    )
    vulnerable_count = (
        int(submission.get("vulnerable_task_count", 0)) if _is_int(submission.get("vulnerable_task_count")) else 0
    )
    control_count = int(submission.get("control_task_count", 0)) if _is_int(submission.get("control_task_count")) else 0
    denial_count = (
        int(submission.get("denial_control_task_count", 0))
        if _is_int(submission.get("denial_control_task_count"))
        else 0
    )
    allow_count = (
        int(submission.get("authorized_allow_control_task_count", 0))
        if _is_int(submission.get("authorized_allow_control_task_count"))
        else 0
    )
    run_count = int(submission.get("run_count", 0)) if _is_int(submission.get("run_count")) else 0

    if task_count <= 0:
        errors.append("task_count must be positive")
    if public_count + private_count != task_count:
        errors.append("public_task_count + private_holdout_task_count must equal task_count")
    _validate_private_pack_role(submission, errors, warnings)

    if split == "public" and (public_count != task_count or private_count != 0):
        errors.append("public split submissions must have public_task_count=task_count and private_holdout_task_count=0")
    if split == "private-holdout" and (private_count != task_count or public_count != 0):
        errors.append(
            "private-holdout submissions must have private_holdout_task_count=task_count and public_task_count=0"
        )
    if split == "combined" and (public_count <= 0 or private_count <= 0):
        errors.append("combined submissions must include both public and private holdout task counts")
    if vulnerable_count + control_count != task_count:
        errors.append("vulnerable_task_count + control_task_count must equal task_count")
    if denial_count + allow_count != control_count:
        errors.append("denial_control_task_count + authorized_allow_control_task_count must equal control_task_count")

    bounded_counts = (
        "v0_passed_count",
        "invalid_submission_count",
        "safety_violations",
    )
    for field in bounded_counts:
        value = submission.get(field)
        if _is_int(value) and task_count and int(value) > task_count:
            errors.append(f"{field} cannot exceed task_count")
    if _is_int(submission.get("exploit_proven_task_count")) and int(submission["exploit_proven_task_count"]) > vulnerable_count:
        errors.append("exploit_proven_task_count cannot exceed vulnerable_task_count")
    if _is_int(submission.get("vulnerable_full_pass_count")) and int(submission["vulnerable_full_pass_count"]) > vulnerable_count:
        errors.append("vulnerable_full_pass_count cannot exceed vulnerable_task_count")

    if task_count and _is_int(submission.get("v0_passed_count")):
        if not _close(submission.get("v0_mean_score"), int(submission["v0_passed_count"]) / task_count):
            errors.append("v0_mean_score must equal v0_passed_count / task_count rounded to 4 decimals")
    if task_count and _is_int(submission.get("invalid_submission_count")):
        if not _close(submission.get("invalid_submission_rate"), int(submission["invalid_submission_count"]) / task_count):
            errors.append("invalid_submission_rate must equal invalid_submission_count / task_count rounded to 4 decimals")
    if vulnerable_count and _is_int(submission.get("exploit_proven_task_count")):
        if not _close(
            submission.get("exploit_proven_success_rate"),
            int(submission["exploit_proven_task_count"]) / vulnerable_count,
        ):
            errors.append(
                "exploit_proven_success_rate must equal exploit_proven_task_count / vulnerable_task_count rounded to 4 decimals"
            )

    if not leaderboard_eligible:
        warnings.append("submission is schema-valid evidence but not marked leaderboard_eligible")
    else:
        if submission.get("benchmark_fingerprint_provenance") != "runner-emitted":
            errors.append("leaderboard_eligible submissions require runner-emitted benchmark fingerprints")
        if split != "private-holdout" or private_count <= 0:
            errors.append(
                "leaderboard_eligible submissions must use split=private-holdout until private-only combined metrics exist"
            )
        if private_count < min_private_holdout_count:
            errors.append(
                f"leaderboard_eligible submissions must include at least {min_private_holdout_count} private holdout tasks"
            )
        if baseline_kind == "harness_check" or harness_type in {"scripted", "scripted-live-http"}:
            errors.append("deterministic harness checks are not leaderboard eligible")
        if vulnerable_count <= 0:
            errors.append("leaderboard_eligible submissions must include vulnerable tasks")
        if control_count <= 0:
            errors.append("leaderboard_eligible submissions must include secure controls")
        if run_count < 2:
            errors.append("leaderboard_eligible submissions must include at least two runs")
        if not _has_variance_evidence(submission.get("variance_or_ci")):
            errors.append("leaderboard_eligible submissions must include variance or confidence evidence")
        false_positive_rate = _rate(submission.get("false_positive_rate"), "false_positive_rate", errors)
        control_false_report_rate = _rate(
            submission.get("control_false_report_rate"), "control_false_report_rate", errors
        )
        invalid_rate = _rate(submission.get("invalid_submission_rate"), "invalid_submission_rate", errors)
        if false_positive_rate is not None and false_positive_rate > false_positive_threshold:
            errors.append(
                f"leaderboard_eligible false_positive_rate must be <= {false_positive_threshold:g}"
            )
        if control_false_report_rate is not None and control_false_report_rate > false_positive_threshold:
            errors.append(
                f"leaderboard_eligible control_false_report_rate must be <= {false_positive_threshold:g}"
            )
        if invalid_rate is not None and invalid_rate > invalid_submission_threshold:
            errors.append(
                f"leaderboard_eligible invalid_submission_rate must be <= {invalid_submission_threshold:g}"
            )
        target_coverage = _rate(submission.get("target_request_coverage_rate"), "target_request_coverage_rate", errors)
        if harness_type in LIVE_HARNESS_TYPES and (
            target_coverage is None or target_coverage < min_target_request_coverage
        ):
            errors.append(
                "leaderboard_eligible live/tool submissions must meet target_request_coverage_rate "
                f">= {min_target_request_coverage:g}"
            )

    return {
        "path": str(submission_path),
        "passed": not errors,
        "leaderboard_eligible": leaderboard_eligible and not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _submission_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AuthZBench-SaaS leaderboard submission JSON.")
    parser.add_argument("--submission", action="append", required=True, help="Submission JSON glob. Can be repeated.")
    parser.add_argument("--false-positive-threshold", type=float, default=0.05)
    parser.add_argument("--invalid-submission-threshold", type=float, default=0.05)
    parser.add_argument("--min-target-request-coverage", type=float, default=1.0)
    parser.add_argument("--min-private-holdout-count", type=int, default=20)
    parser.add_argument(
        "--require-source-summary",
        action="store_true",
        help="Require each submission to reference a source_run_summary artifact and cross-check it.",
    )
    args = parser.parse_args()

    paths = _submission_paths(args.submission)
    if not paths:
        result = {"passed": False, "submission_count": 0, "errors": ["no leaderboard submissions matched"]}
        print(dump_json(result))
        return 1
    results = [
        validate_submission(
            path,
            false_positive_threshold=args.false_positive_threshold,
            invalid_submission_threshold=args.invalid_submission_threshold,
            min_target_request_coverage=args.min_target_request_coverage,
            min_private_holdout_count=args.min_private_holdout_count,
            require_source_summary=args.require_source_summary,
        )
        for path in paths
    ]
    result = {
        "passed": all(item["passed"] for item in results),
        "submission_count": len(results),
        "leaderboard_eligible_count": sum(1 for item in results if item["leaderboard_eligible"]),
        "submissions": results,
    }
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
