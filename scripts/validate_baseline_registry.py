from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import benchmark_fingerprint, dump_json, load_json, stable_json_sha256
from authzbench.run import summarize_task_results
from authzbench.validate_manifests import validate_patterns


REQUIRED_ENTRY_FIELDS = {
    "id",
    "summary_path",
    "kind",
    "release_suitability",
    "leaderboard_eligible",
    "run_count",
    "expected_harness_type",
    "expected_task_count",
    "requires_rerun_before_current_comparison",
}

REQUIRED_SUMMARY_FIELDS = {
    "agent",
    "benchmark_commit_sha",
    "benchmark_version",
    "control_task_count",
    "exploit_proven_success_rate",
    "false_positive_rate",
    "harness_type",
    "mean_score",
    "model",
    "passed_count",
    "task_count",
    "vulnerable_task_count",
}

REQUIRED_TOOL_AGENT_SUMMARY_FIELDS = {
    "model_tool_plan_artifact_count",
    "per_task_tool_probe_artifact_count",
    "planner_failure_count",
    "planner_parse_error_count",
    "target_request_correlated_task_count",
    "target_request_coverage_rate",
}

REQUIRED_RELEASE_SNAPSHOT_FIELDS = {
    "id",
    "public_split",
    "baseline_ids",
    "min_real_model_families",
    "min_runs_per_serious_baseline",
    "requires_tool_agent_baseline",
}

PUBLIC_COUNT_FIELDS = (
    "task_count",
    "vulnerable_task_count",
    "control_task_count",
    "denial_control_task_count",
    "authorized_allow_control_task_count",
)

VALID_KINDS = {"harness_check", "model_baseline", "tool_agent_baseline"}
VALID_SUITABILITY = {
    "current_public_split",
    "current_public_harness_check",
    "current_public_stale",
    "legacy_snapshot",
}

RESCORE_SCHEMA_VERSION = "public-run-rescore-v1"
RESCORE_DERIVATION = "offline_rescore_from_saved_public_submissions"
VALID_CURRENT_RESULT_DERIVATIONS = {
    "runner_emitted",
    RESCORE_DERIVATION,
    "promoted_cohort_delta_merge",
}
RESCORE_HASH_FIELDS = {
    "source_summary_sha256",
    "source_submission_set_sha256",
    "source_score_set_sha256",
    "source_model_output_set_sha256",
    "rescored_score_set_sha256",
    "rescored_task_rows_sha256",
    "runner_source_sha256",
    "scorer_source_sha256",
    "rescore_tool_sha256",
}
TOOL_TELEMETRY_COVERAGE_FIELDS = {
    "tool_probe_telemetry_complete_task_count",
    "tool_probe_telemetry_coverage_rate",
    "tool_probe_telemetry_status",
}
TOOL_TELEMETRY_TOTAL_FIELDS = {
    "executed_tool_probe_total",
    "fallback_probe_total",
    "submitted_finding_total",
}
VALID_ADAPTER_FAILURE_TYPES = {
    "adapter_metadata_failure",
    "command_failure",
    "model_label_failure",
    "output_parse_failure",
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


_TARGET_SOURCE_HASH_CACHE: dict[str, dict[str, str | None]] = {}


def _target_source_hashes(target_commit: str) -> dict[str, str | None]:
    cached = _TARGET_SOURCE_HASH_CACHE.get(target_commit)
    if cached is not None:
        return cached
    source_paths = {
        "scorer_source_sha256": "authzbench/score.py",
        "runner_source_sha256": "authzbench/run.py",
        "rescore_tool_sha256": "scripts/rescore_public_run.py",
    }
    hashes: dict[str, str | None] = {}
    for field, relative_path in source_paths.items():
        completed = subprocess.run(
            ["git", "show", f"{target_commit}:{relative_path}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        hashes[field] = (
            hashlib.sha256(completed.stdout).hexdigest() if completed.returncode == 0 else None
        )
    _TARGET_SOURCE_HASH_CACHE[target_commit] = hashes
    return hashes

# Required provenance fields on every "current" entry. These were
# introduced after the v1.0-internal release per
# docs/goal-external-validation-coverage.md objective 1, and are
# enforced as a hard CI gate for entries that claim current
# public-split or current public harness-check suitability. Stale
# and legacy-snapshot entries are explicitly allowed to use the
# legacy field set (model_family, run_artifacts, etc.) and are
# warned, not failed, when these fields are missing.
REQUIRED_CURRENT_ENTRY_PROVENANCE_FIELDS = {
    "model_name",
    "model_version",
    "scaffold_name",
    "run_date",
    "evidence_status",
}

PROMOTED_COMPOSITE_CONSTRUCTION = "promoted_cohort_delta_merge"

REQUIRED_PROMOTED_COMPOSITE_ENTRY_FIELDS = {
    "baseline_construction",
    "base_public_task_count",
    "delta_public_task_count",
    "merged_public_task_count",
    "base_summary_path",
    "delta_summary_paths",
    "promotion_annotation",
    "not_full_rerun",
}

REQUIRED_PROMOTED_COMPOSITE_SUMMARY_FIELDS = {
    "baseline_construction",
    "base_public_task_count",
    "delta_public_task_count",
    "merged_public_task_count",
    "delta_task_ids",
    "not_full_rerun",
    "promotion_annotation",
    "promotion_sources",
    "public_split_freshness",
    "rerun_scope",
}

# harness_check entries do not have a model or scaffold; the
# provenance gate still requires run_date and evidence_status.
HARNESS_CHECK_REQUIRED_PROVENANCE_FIELDS = {
    "run_date",
    "evidence_status",
}


def _validate_rescore_provenance(
    summary: dict[str, Any],
    raw_entry: dict[str, Any],
    entry_id: str,
    location: str,
    current_fingerprint: dict[str, Any],
    errors: list[str],
) -> None:
    provenance = summary.get("rescore_provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{entry_id}: {location} missing rescore_provenance")
        return
    expected_values = {
        "schema_version": RESCORE_SCHEMA_VERSION,
        "derivation": RESCORE_DERIVATION,
        "source_score_policy_version": "score-policy-v1",
        "target_score_policy_version": current_fingerprint["score_policy_version"],
        "adapter_failure_policy": "fail_closed_from_model_output_and_agent_returncode",
        "claim_exact_match_scored": False,
        "partial_boundary_credit_scored": False,
        "model_execution_repeated": False,
    }
    for field, expected in expected_values.items():
        if provenance.get(field) != expected:
            errors.append(
                f"{entry_id}: {location} rescore_provenance.{field} "
                f"{provenance.get(field)!r} does not match {expected!r}"
            )
    if provenance.get("source_run_id") != summary.get("run_id"):
        errors.append(f"{entry_id}: {location} rescore source_run_id must match summary run_id")
    target_commit = provenance.get("target_benchmark_commit_sha")
    if target_commit != summary.get("benchmark_commit_sha") or not re.fullmatch(
        r"[0-9a-f]{40}", str(target_commit or "")
    ):
        errors.append(
            f"{entry_id}: {location} rescore target benchmark commit must be a 40-character SHA matching the summary"
        )
    for field in sorted(RESCORE_HASH_FIELDS):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(field, ""))):
            errors.append(f"{entry_id}: {location} rescore_provenance.{field} must be a SHA-256 digest")
    if isinstance(target_commit, str) and re.fullmatch(r"[0-9a-f]{40}", target_commit):
        for field, expected in _target_source_hashes(target_commit).items():
            if expected is None:
                errors.append(
                    f"{entry_id}: {location} cannot read rescore source at target benchmark commit"
                )
            elif provenance.get(field) != expected:
                errors.append(
                    f"{entry_id}: {location} rescore_provenance.{field} does not match target commit source"
                )

    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        errors.append(f"{entry_id}: {location} tasks must be a list for fail-closed validation")
        return
    adapter_rows = [row for row in tasks if isinstance(row, dict) and row.get("adapter_failure_type")]
    infrastructure_rows = [row for row in tasks if isinstance(row, dict) and row.get("infrastructure_failure")]
    runner_failure_rows = [row for row in tasks if isinstance(row, dict) and row.get("runner_agent_failure")]
    if provenance.get("rescored_task_rows_sha256") != stable_json_sha256(tasks):
        errors.append(f"{entry_id}: {location} rescored task-row digest does not match tasks")
    for row in adapter_rows:
        failure_type = row.get("adapter_failure_type")
        task_id = row.get("task_id", "<unknown>")
        if failure_type not in VALID_ADAPTER_FAILURE_TYPES:
            errors.append(f"{entry_id}: {location} {task_id} has invalid adapter_failure_type {failure_type!r}")
        if row.get("score") != 0 or row.get("passed") is not False or row.get("invalid_submission") is not True:
            errors.append(f"{entry_id}: {location} {task_id} adapter failure must fail closed")
        expected_infrastructure = failure_type != "output_parse_failure"
        if row.get("infrastructure_failure") is not expected_infrastructure:
            errors.append(
                f"{entry_id}: {location} {task_id} infrastructure_failure must be "
                f"{expected_infrastructure} for {failure_type}"
            )
    count_expectations = {
        "adapter_failure_count": len(adapter_rows),
        "adapter_output_parse_failure_count": sum(
            1 for row in adapter_rows if row.get("adapter_failure_type") == "output_parse_failure"
        ),
        "adapter_metadata_failure_count": sum(
            1 for row in adapter_rows if row.get("adapter_failure_type") == "adapter_metadata_failure"
        ),
        "infrastructure_failure_count": len(infrastructure_rows),
        "runner_agent_failure_count": len(runner_failure_rows),
    }
    for field, expected in count_expectations.items():
        if summary.get(field) != expected:
            errors.append(
                f"{entry_id}: {location} {field} {summary.get(field)!r} does not match task rows {expected}"
            )

    try:
        recomputed = summarize_task_results(tasks)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(
            f"{entry_id}: {location} cannot recompute rescore aggregates: {type(exc).__name__}"
        )
        return
    for field, expected in recomputed.items():
        if field == "tasks":
            continue
        if field in TOOL_TELEMETRY_COVERAGE_FIELDS and field not in summary:
            continue
        if (
            field in TOOL_TELEMETRY_TOTAL_FIELDS
            and "tool_probe_telemetry_status" not in summary
            and recomputed["tool_probe_telemetry_status"] != "complete"
        ):
            continue
        if summary.get(field) != expected:
            errors.append(
                f"{entry_id}: {location} {field} {summary.get(field)!r} "
                f"does not match recomputed value {expected!r}"
            )


def _current_public_task_items() -> list[tuple[str, dict[str, Any]]]:
    task_root = ROOT / "tasks"
    return [
        (path.relative_to(ROOT).as_posix(), load_json(path))
        for path in sorted(task_root.glob("*/*.json"))
        if path.is_file()
    ]


def _task_counts() -> dict[str, int]:
    result = validate_patterns([str(ROOT / "tasks" / "*" / "*.json")])
    if result["errors"]:
        raise SystemExit("public manifests must validate before baseline registry validation")
    return {
        "task_count": int(result["manifest_count"]),
        "vulnerable_task_count": int(result["vulnerable_count"]),
        "control_task_count": int(result["control_count"]),
        "denial_control_task_count": int(result["denial_control_count"]),
        "authorized_allow_control_task_count": int(result["authorized_allow_control_count"]),
    }


def _summary_path(registry_path: Path, summary_path: str) -> Path:
    candidate = Path(summary_path)
    if candidate.is_absolute():
        return candidate
    return registry_path.parent / candidate


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _validate_current_fingerprint(
    summary: dict[str, Any],
    expected_fingerprint: dict[str, Any],
    entry_id: str,
    location: str,
    errors: list[str],
) -> None:
    fingerprint = summary.get("benchmark_fingerprint")
    if not isinstance(fingerprint, dict):
        errors.append(f"{entry_id}: {location} missing benchmark_fingerprint")
        return
    for field in (
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
    ):
        if fingerprint.get(field) != expected_fingerprint.get(field):
            errors.append(
                f"{entry_id}: {location} benchmark_fingerprint.{field} "
                f"{fingerprint.get(field)!r} does not match current public split "
                f"{expected_fingerprint.get(field)!r}"
            )


def _validate_fingerprint_counts(
    summary: dict[str, Any],
    expected_counts: dict[str, int],
    entry_id: str,
    location: str,
    errors: list[str],
) -> None:
    fingerprint = summary.get("benchmark_fingerprint")
    if not isinstance(fingerprint, dict):
        errors.append(f"{entry_id}: {location} missing benchmark_fingerprint")
        return
    for field in PUBLIC_COUNT_FIELDS:
        if fingerprint.get(field) != expected_counts.get(field):
            errors.append(
                f"{entry_id}: {location} benchmark_fingerprint.{field} "
                f"{fingerprint.get(field)!r} does not match snapshot {expected_counts.get(field)!r}"
            )


def _validate_summary_counts(
    summary: dict[str, Any],
    expected_counts: dict[str, int],
    entry_id: str,
    location: str,
    errors: list[str],
    *,
    prefix: str,
) -> None:
    for count_field in PUBLIC_COUNT_FIELDS:
        if count_field in summary and summary[count_field] != expected_counts[count_field]:
            errors.append(
                f"{entry_id}: {location} {prefix} {count_field} "
                f"{summary[count_field]!r} does not match {expected_counts[count_field]}"
            )


def _validate_promoted_composite_provenance(
    registry_path: Path,
    raw_entry: dict[str, Any],
    summary: dict[str, Any],
    entry_id: str,
    expected_task_count: int,
    errors: list[str],
) -> None:
    construction = str(raw_entry.get("baseline_construction", "")).strip()
    summary_construction = str(summary.get("baseline_construction", "")).strip()
    has_promoted_markers = any(
        field in raw_entry
        for field in REQUIRED_PROMOTED_COMPOSITE_ENTRY_FIELDS
    ) or any(field in summary for field in REQUIRED_PROMOTED_COMPOSITE_SUMMARY_FIELDS)
    if not has_promoted_markers:
        return
    if construction != PROMOTED_COMPOSITE_CONSTRUCTION:
        errors.append(
            f"{entry_id}: promoted composite current rows must set "
            f"baseline_construction={PROMOTED_COMPOSITE_CONSTRUCTION!r}"
        )
        return
    if summary_construction != PROMOTED_COMPOSITE_CONSTRUCTION:
        errors.append(
            f"{entry_id}: promoted composite summary must set "
            f"baseline_construction={PROMOTED_COMPOSITE_CONSTRUCTION!r}"
        )

    missing_entry_fields = sorted(
        field for field in REQUIRED_PROMOTED_COMPOSITE_ENTRY_FIELDS if field not in raw_entry
    )
    if missing_entry_fields:
        errors.append(
            f"{entry_id}: promoted composite entry missing fields: "
            f"{', '.join(missing_entry_fields)}"
        )
    missing_summary_fields = sorted(
        field for field in REQUIRED_PROMOTED_COMPOSITE_SUMMARY_FIELDS if field not in summary
    )
    if missing_summary_fields:
        errors.append(
            f"{entry_id}: promoted composite summary missing fields: "
            f"{', '.join(missing_summary_fields)}"
        )

    if raw_entry.get("not_full_rerun") is not True:
        errors.append(f"{entry_id}: promoted composite entry must set not_full_rerun=true")
    if summary.get("not_full_rerun") is not True:
        errors.append(f"{entry_id}: promoted composite summary must set not_full_rerun=true")

    base_count = raw_entry.get("base_public_task_count")
    delta_count = raw_entry.get("delta_public_task_count")
    merged_count = raw_entry.get("merged_public_task_count")
    if not isinstance(base_count, int):
        errors.append(f"{entry_id}: base_public_task_count must be an integer")
    if not isinstance(delta_count, int):
        errors.append(f"{entry_id}: delta_public_task_count must be an integer")
    if not isinstance(merged_count, int):
        errors.append(f"{entry_id}: merged_public_task_count must be an integer")
    if isinstance(base_count, int) and isinstance(delta_count, int) and isinstance(merged_count, int):
        if base_count + delta_count != merged_count:
            errors.append(
                f"{entry_id}: base_public_task_count + delta_public_task_count must equal "
                "merged_public_task_count"
            )
        if merged_count != expected_task_count:
            errors.append(
                f"{entry_id}: merged_public_task_count {merged_count!r} does not match "
                f"expected_task_count {expected_task_count}"
            )
    for field in ("base_public_task_count", "delta_public_task_count", "merged_public_task_count"):
        if field in summary and raw_entry.get(field) != summary.get(field):
            errors.append(
                f"{entry_id}: promoted composite {field} {summary.get(field)!r} "
                f"does not match registry {raw_entry.get(field)!r}"
            )

    delta_paths = raw_entry.get("delta_summary_paths")
    if not isinstance(delta_paths, list) or not delta_paths:
        errors.append(f"{entry_id}: delta_summary_paths must be a non-empty list")
    else:
        for index, delta_path in enumerate(delta_paths, start=1):
            if not isinstance(delta_path, str) or not delta_path.strip():
                errors.append(f"{entry_id}: delta_summary_paths[{index}] must be a non-empty path")
                continue
            if not _summary_path(registry_path, delta_path).exists():
                errors.append(f"{entry_id}: missing delta summary {_display_path(_summary_path(registry_path, delta_path))}")

    base_summary_path = raw_entry.get("base_summary_path")
    if not isinstance(base_summary_path, str) or not base_summary_path.strip():
        errors.append(f"{entry_id}: base_summary_path must be a non-empty path")
    elif not _summary_path(registry_path, base_summary_path).exists():
        errors.append(f"{entry_id}: missing base summary {_display_path(_summary_path(registry_path, base_summary_path))}")

    promotion_sources = summary.get("promotion_sources")
    if not isinstance(promotion_sources, dict):
        errors.append(f"{entry_id}: promoted composite summary promotion_sources must be an object")
    else:
        for field in ("base_summary", "delta_summary", "base_task_count", "delta_task_count"):
            if field not in promotion_sources:
                errors.append(f"{entry_id}: promoted composite summary promotion_sources missing {field}")


def _require_int(value: Any, field: str, entry_id: str, errors: list[str]) -> int:
    if not isinstance(value, int):
        errors.append(f"{entry_id}: {field} must be an integer")
        return 0
    return value


def _validate_summary_file(
    registry_path: Path,
    raw_entry: dict[str, Any],
    entry_id: str,
    summary_path: str,
    expected_task_count: int,
    public_counts: dict[str, int],
    current_fingerprint: dict[str, Any],
    errors: list[str],
    label: str = "summary",
    enforce_current_public: bool = True,
) -> dict[str, Any] | None:
    summary_file = _summary_path(registry_path, summary_path)
    location = label if label == "summary" else f"{label} {_display_path(summary_file)}"
    if not summary_file.exists():
        errors.append(f"{entry_id}: missing {location}")
        return None

    summary = load_json(summary_file)
    if not isinstance(summary, dict):
        errors.append(f"{entry_id}: {location} must be a JSON object")
        return None

    missing_summary = sorted(REQUIRED_SUMMARY_FIELDS - set(summary))
    if missing_summary:
        errors.append(f"{entry_id}: {location} missing fields: {', '.join(missing_summary)}")

    if summary.get("harness_type") != raw_entry.get("expected_harness_type"):
        errors.append(
            f"{entry_id}: {location} harness_type {summary.get('harness_type')!r} "
            f"does not match registry {raw_entry.get('expected_harness_type')!r}"
        )
    if summary.get("task_count") != expected_task_count:
        errors.append(
            f"{entry_id}: {location} task_count {summary.get('task_count')!r} "
            f"does not match registry {expected_task_count}"
        )
    for optional_field in ("expected_agent", "expected_model"):
        summary_field = optional_field.removeprefix("expected_")
        if optional_field in raw_entry and summary.get(summary_field) != raw_entry[optional_field]:
            errors.append(
                f"{entry_id}: {location} {summary_field} {summary.get(summary_field)!r} "
                f"does not match registry {raw_entry[optional_field]!r}"
            )

    suitability = str(raw_entry.get("release_suitability"))
    if enforce_current_public and suitability in {"current_public_split", "current_public_harness_check"}:
        if expected_task_count != public_counts["task_count"]:
            errors.append(
                f"{entry_id}: {suitability} must use current public task count "
                f"{public_counts['task_count']}"
            )
        for count_field in (
            "vulnerable_task_count",
            "control_task_count",
            "denial_control_task_count",
            "authorized_allow_control_task_count",
        ):
            if count_field in summary and summary[count_field] != public_counts[count_field]:
                errors.append(
                    f"{entry_id}: {location} current public {count_field} "
                    f"{summary[count_field]!r} does not match {public_counts[count_field]}"
                )
        _validate_current_fingerprint(summary, current_fingerprint, entry_id, location, errors)
        if raw_entry.get("kind") in {"model_baseline", "tool_agent_baseline"}:
            evaluation_protocol = summary.get("evaluation_protocol")
            if (
                isinstance(evaluation_protocol, dict)
                and evaluation_protocol.get("version") == "blinded-control-evidence-v1"
                and summary.get("model_identity_status") != "verified"
            ):
                errors.append(
                    f"{entry_id}: {location} blinded protocol rows require verified effective "
                    "model identity for current registry use"
                )
            if (
                isinstance(evaluation_protocol, dict)
                and evaluation_protocol.get("version") == "blinded-control-evidence-v1"
                and summary.get("model_label_verified_task_count") != summary.get("task_count")
            ):
                errors.append(
                    f"{entry_id}: {location} blinded protocol verified-model task count must "
                    "equal task_count for current registry use"
                )
            result_derivation = raw_entry.get("result_derivation")
            if result_derivation not in VALID_CURRENT_RESULT_DERIVATIONS:
                errors.append(
                    f"{entry_id}: current model/tool entry result_derivation must be one of "
                    f"{', '.join(sorted(VALID_CURRENT_RESULT_DERIVATIONS))}"
                )
            elif result_derivation == RESCORE_DERIVATION:
                _validate_rescore_provenance(
                    summary,
                    raw_entry,
                    entry_id,
                    location,
                    current_fingerprint,
                    errors,
                )

    return summary


def _has_repeated_run_evidence(
    registry_path: Path,
    raw_entry: dict[str, Any],
    entry_id: str,
    run_count: int,
    expected_task_count: int,
    public_counts: dict[str, int],
    current_fingerprint: dict[str, Any],
    errors: list[str],
    enforce_current_public: bool = True,
    snapshot_counts: dict[str, int] | None = None,
) -> bool:
    run_artifacts = raw_entry.get("run_artifacts")
    if not isinstance(run_artifacts, list):
        errors.append(f"{entry_id}: repeated or leaderboard baselines must include a run_artifacts list")
        return False
    if len(run_artifacts) != run_count:
        errors.append(f"{entry_id}: run_artifacts length must match run_count")
        return False

    ok = True
    seen_paths: set[Path] = set()
    seen_run_ids: set[str] = set()
    for index, artifact_path in enumerate(run_artifacts, start=1):
        if not isinstance(artifact_path, str) or not artifact_path.strip():
            errors.append(f"{entry_id}: run_artifacts[{index}] must be a non-empty path")
            ok = False
            continue
        candidate = _summary_path(registry_path, artifact_path)
        resolved = candidate.resolve(strict=False)
        if resolved in seen_paths:
            errors.append(f"{entry_id}: run_artifacts must point to unique files")
            ok = False
        seen_paths.add(resolved)
        if not candidate.exists():
            errors.append(f"{entry_id}: missing run artifact {_display_path(candidate)}")
            ok = False
            continue
        artifact = _validate_summary_file(
            registry_path,
            raw_entry,
            entry_id,
            artifact_path,
            expected_task_count,
            public_counts,
            current_fingerprint,
            errors,
            label="run artifact",
            enforce_current_public=enforce_current_public,
        )
        run_id = str(artifact.get("run_id", "")).strip() if isinstance(artifact, dict) else ""
        if isinstance(artifact, dict) and snapshot_counts is not None:
            artifact_location = f"run artifact {_display_path(candidate)}"
            _validate_summary_counts(artifact, snapshot_counts, entry_id, artifact_location, errors, prefix="snapshot")
            _validate_fingerprint_counts(artifact, snapshot_counts, entry_id, artifact_location, errors)
        if not run_id:
            errors.append(f"{entry_id}: run artifact {_display_path(candidate)} must include a run_id")
            ok = False
        elif run_id in seen_run_ids:
            errors.append(f"{entry_id}: run_artifacts must contain distinct run_id values")
            ok = False
        else:
            seen_run_ids.add(run_id)
    return ok


def _snapshot_counts(raw_snapshot: dict[str, Any], snapshot_id: str, errors: list[str]) -> dict[str, int]:
    raw_counts = raw_snapshot.get("public_split")
    if not isinstance(raw_counts, dict):
        errors.append(f"{snapshot_id}: public_split must be an object")
        raw_counts = {}
    counts: dict[str, int] = {}
    for field in PUBLIC_COUNT_FIELDS:
        counts[field] = _require_int(raw_counts.get(field), f"public_split.{field}", snapshot_id, errors)
    return counts


def _validate_release_snapshot(
    raw_snapshot: dict[str, Any],
    entries_by_id: dict[str, dict[str, Any]],
    summaries_by_id: dict[str, dict[str, Any]],
    registry_path: Path,
    errors: list[str],
) -> dict[str, Any]:
    snapshot_id = str(raw_snapshot.get("id", "<missing-id>"))
    missing = sorted(REQUIRED_RELEASE_SNAPSHOT_FIELDS - set(raw_snapshot))
    if missing:
        errors.append(f"{snapshot_id}: missing release snapshot fields: {', '.join(missing)}")
    counts = _snapshot_counts(raw_snapshot, snapshot_id, errors)
    baseline_ids = raw_snapshot.get("baseline_ids")
    if not isinstance(baseline_ids, list) or not baseline_ids:
        errors.append(f"{snapshot_id}: baseline_ids must be a non-empty list")
        baseline_ids = []

    min_model_families = _require_int(
        raw_snapshot.get("min_real_model_families"),
        "min_real_model_families",
        snapshot_id,
        errors,
    )
    min_runs = _require_int(
        raw_snapshot.get("min_runs_per_serious_baseline"),
        "min_runs_per_serious_baseline",
        snapshot_id,
        errors,
    )
    requires_tool_agent = bool(raw_snapshot.get("requires_tool_agent_baseline"))
    model_families: set[str] = set()
    repeated_model_baselines = 0
    has_tool_agent_baseline = False
    snapshot_unmet: list[str] = []
    seen_ids: set[str] = set()

    for raw_baseline_id in baseline_ids:
        baseline_id = str(raw_baseline_id)
        if baseline_id in seen_ids:
            errors.append(f"{snapshot_id}: duplicate baseline id {baseline_id}")
            continue
        seen_ids.add(baseline_id)
        entry = entries_by_id.get(baseline_id)
        if entry is None:
            errors.append(f"{snapshot_id}: missing baseline id {baseline_id}")
            continue
        summary = summaries_by_id.get(baseline_id)
        if summary is None:
            continue

        expected_task_count = _require_int(
            entry.get("expected_task_count"),
            f"{baseline_id}.expected_task_count",
            snapshot_id,
            errors,
        )
        if expected_task_count != counts["task_count"]:
            errors.append(
                f"{snapshot_id}: {baseline_id} expected_task_count {expected_task_count} "
                f"does not match snapshot task_count {counts['task_count']}"
            )
        _validate_summary_counts(summary, counts, baseline_id, "release snapshot summary", errors, prefix=snapshot_id)
        _validate_fingerprint_counts(summary, counts, baseline_id, "release snapshot summary", errors)

        kind = str(entry.get("kind"))
        if kind not in {"model_baseline", "tool_agent_baseline"}:
            continue
        model_family = str(entry.get("model_family", "")).strip()
        if model_family:
            model_families.add(model_family)
        run_count = _require_int(entry.get("run_count"), f"{baseline_id}.run_count", snapshot_id, errors)
        if kind == "tool_agent_baseline":
            has_tool_agent_baseline = True
        if run_count >= min_runs:
            has_repeated_evidence = _has_repeated_run_evidence(
                registry_path,
                entry,
                baseline_id,
                run_count,
                expected_task_count,
                counts,
                {},
                errors,
                enforce_current_public=False,
                snapshot_counts=counts,
            )
            if has_repeated_evidence:
                repeated_model_baselines += 1

    if len(model_families) < min_model_families:
        snapshot_unmet.append(f"model families: {len(model_families)} of {min_model_families}")
    if repeated_model_baselines < min_model_families:
        snapshot_unmet.append(f"repeated model baselines: {repeated_model_baselines} of {min_model_families}")
    if requires_tool_agent and not has_tool_agent_baseline:
        snapshot_unmet.append("missing tool-agent baseline")
    if min_runs < 2:
        snapshot_unmet.append("min_runs_per_serious_baseline should be at least 2")

    return {
        "id": snapshot_id,
        "ready": not snapshot_unmet,
        "baseline_count": len(seen_ids),
        "model_family_count": len(model_families),
        "repeated_model_baseline_count": repeated_model_baselines,
        "has_tool_agent_baseline": has_tool_agent_baseline,
        "public_split": counts,
        "unmet": snapshot_unmet,
    }


def validate_registry(registry_path: Path = ROOT / "baselines" / "baseline-registry.json") -> dict[str, Any]:
    registry = load_json(registry_path)
    errors: list[str] = []
    warnings: list[str] = []
    public_counts = _task_counts()
    current_fingerprint = benchmark_fingerprint(_current_public_task_items())
    v0_requirements = registry.get("v0_requirements", {})
    min_model_families = int(v0_requirements.get("min_real_model_families", 5))
    min_runs = int(v0_requirements.get("min_runs_per_serious_baseline", 2))
    requires_tool_agent = bool(v0_requirements.get("requires_tool_agent_baseline", True))

    if registry.get("schema_version") != "baseline-registry-v1":
        errors.append("registry schema_version must be baseline-registry-v1")

    declared_public_split = registry.get("public_split", {})
    if not isinstance(declared_public_split, dict):
        errors.append("public_split must be an object")
        declared_public_split = {}
    for field, expected in public_counts.items():
        if declared_public_split.get(field) != expected:
            errors.append(f"public_split.{field} is {declared_public_split.get(field)!r}; expected {expected}")

    entries = registry.get("baselines")
    if not isinstance(entries, list) or not entries:
        errors.append("baselines must be a non-empty list")
        entries = []

    model_families: set[str] = set()
    current_model_families: set[str] = set()
    has_tool_agent_baseline = False
    has_current_scripted_sanity_baseline = False
    has_current_model_or_tool_agent_baseline = False
    repeated_model_baselines = 0
    seen_entry_ids: set[str] = set()
    entries_by_id: dict[str, dict[str, Any]] = {}
    summaries_by_id: dict[str, dict[str, Any]] = {}

    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            errors.append("every baseline entry must be an object")
            continue
        entry_id = str(raw_entry.get("id", "<missing-id>"))
        if entry_id in seen_entry_ids:
            errors.append(f"{entry_id}: duplicate baseline id")
        seen_entry_ids.add(entry_id)
        entries_by_id[entry_id] = raw_entry
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(raw_entry))
        if missing:
            errors.append(f"{entry_id}: missing registry fields: {', '.join(missing)}")
            continue

        kind = str(raw_entry.get("kind"))
        suitability = str(raw_entry.get("release_suitability"))
        run_count = _require_int(raw_entry.get("run_count"), "run_count", entry_id, errors)
        expected_task_count = _require_int(raw_entry.get("expected_task_count"), "expected_task_count", entry_id, errors)
        leaderboard_eligible = raw_entry.get("leaderboard_eligible")
        requires_rerun_before_current = bool(raw_entry.get("requires_rerun_before_current_comparison"))

        if kind not in VALID_KINDS:
            errors.append(f"{entry_id}: kind must be one of {', '.join(sorted(VALID_KINDS))}")
        if suitability not in VALID_SUITABILITY:
            errors.append(f"{entry_id}: release_suitability must be one of {', '.join(sorted(VALID_SUITABILITY))}")
        if not isinstance(leaderboard_eligible, bool):
            errors.append(f"{entry_id}: leaderboard_eligible must be boolean")
        if suitability == "current_public_harness_check" and kind != "harness_check":
            errors.append(f"{entry_id}: current_public_harness_check is only valid for harness_check entries")
        if kind == "harness_check" and suitability == "current_public_harness_check":
            has_current_scripted_sanity_baseline = True
        if kind == "harness_check" and suitability == "current_public_split":
            errors.append(f"{entry_id}: harness checks must use current_public_harness_check, not current_public_split")

        summary = _validate_summary_file(
            registry_path,
            raw_entry,
            entry_id,
            str(raw_entry.get("summary_path")),
            expected_task_count,
            public_counts,
            current_fingerprint,
            errors,
        )
        if summary is None:
            continue
        summaries_by_id[entry_id] = summary

        if suitability == "legacy_snapshot":
            if not requires_rerun_before_current:
                errors.append(
                    f"{entry_id}: legacy_snapshot must set requires_rerun_before_current_comparison=true"
                )
        if suitability == "current_public_stale":
            if not requires_rerun_before_current:
                errors.append(
                    f"{entry_id}: current_public_stale must set requires_rerun_before_current_comparison=true"
                )
            if leaderboard_eligible:
                errors.append(f"{entry_id}: current_public_stale entries cannot be leaderboard_eligible")

        if kind in {"model_baseline", "tool_agent_baseline"}:
            model_family = str(raw_entry.get("model_family", "")).strip()
            if not model_family:
                errors.append(f"{entry_id}: model baselines must declare model_family")
            else:
                pass
        if suitability in {"current_public_split", "current_public_harness_check"}:
            required = (
                HARNESS_CHECK_REQUIRED_PROVENANCE_FIELDS
                if kind == "harness_check"
                else REQUIRED_CURRENT_ENTRY_PROVENANCE_FIELDS
            )
            missing_provenance = sorted(
                field for field in required if not str(raw_entry.get(field, "")).strip()
            )
            if missing_provenance:
                errors.append(
                    f"{entry_id}: current {suitability} entry missing required provenance "
                    f"fields: {', '.join(missing_provenance)}"
                )
            if kind in {"model_baseline", "tool_agent_baseline"} and suitability == "current_public_split":
                _validate_promoted_composite_provenance(
                    registry_path,
                    raw_entry,
                    summary,
                    entry_id,
                    expected_task_count,
                    errors,
                )
        elif kind in {"model_baseline", "tool_agent_baseline"}:
            # Stale or legacy-snapshot entries: warn on missing
            # provenance but do not fail. The warning surfaces in
            # the validator's JSON output.
            missing_provenance = sorted(
                field
                for field in REQUIRED_CURRENT_ENTRY_PROVENANCE_FIELDS
                if not str(raw_entry.get(field, "")).strip()
            )
            if missing_provenance:
                warnings.append(
                    f"{entry_id}: historical entry missing provenance fields "
                    f"(allowed for stale/legacy only): {', '.join(missing_provenance)}"
                )
        if kind in {"model_baseline", "tool_agent_baseline"}:
            model_family = str(raw_entry.get("model_family", "")).strip()
            if not model_family:
                errors.append(f"{entry_id}: model baselines must declare model_family")
            else:
                model_families.add(model_family)
                if suitability == "current_public_split":
                    current_model_families.add(model_family)
                    has_current_model_or_tool_agent_baseline = True
            if kind == "tool_agent_baseline" and suitability == "current_public_split":
                has_tool_agent_baseline = True
                has_current_model_or_tool_agent_baseline = True
                missing_tool_fields = sorted(REQUIRED_TOOL_AGENT_SUMMARY_FIELDS - set(summary))
                if missing_tool_fields:
                    errors.append(
                        f"{entry_id}: current public tool-agent summary missing fields: "
                        f"{', '.join(missing_tool_fields)}"
                    )
                if summary.get("target_request_correlated_task_count") != expected_task_count:
                    errors.append(
                        f"{entry_id}: current public tool-agent must correlate target requests for "
                        f"all {expected_task_count} tasks"
                    )
                if summary.get("target_request_coverage_rate") != 1.0:
                    errors.append(f"{entry_id}: current public tool-agent target_request_coverage_rate must be 1.0")
                if summary.get("model_tool_plan_artifact_count") != expected_task_count:
                    errors.append(
                        f"{entry_id}: current public tool-agent must include one model-tool plan artifact per task"
                    )
                if summary.get("per_task_tool_probe_artifact_count") != expected_task_count:
                    errors.append(
                        f"{entry_id}: current public tool-agent must include one tool-probe artifact per task"
                    )
            has_repeated_evidence = True
            if run_count >= min_runs:
                has_repeated_evidence = _has_repeated_run_evidence(
                    registry_path,
                    raw_entry,
                    entry_id,
                    run_count,
                    expected_task_count,
                    public_counts,
                    current_fingerprint,
                    errors,
                )
            if suitability == "current_public_split" and run_count >= min_runs and has_repeated_evidence:
                repeated_model_baselines += 1
            if leaderboard_eligible and (suitability != "current_public_split" or run_count < min_runs):
                errors.append(
                    f"{entry_id}: leaderboard_eligible model baselines must use the current public split "
                    f"and include at least {min_runs} runs"
                )
            if leaderboard_eligible and run_count >= min_runs and not has_repeated_evidence:
                errors.append(f"{entry_id}: leaderboard_eligible model baselines must include validated run_artifacts")
        elif leaderboard_eligible:
            errors.append(f"{entry_id}: harness checks are not leaderboard eligible")

        if run_count <= 0:
            errors.append(f"{entry_id}: run_count must be positive")

    release_snapshot_results: list[dict[str, Any]] = []
    raw_release_snapshots = registry.get("release_snapshots", [])
    if raw_release_snapshots:
        if not isinstance(raw_release_snapshots, list):
            errors.append("release_snapshots must be a list")
        else:
            seen_snapshot_ids: set[str] = set()
            for raw_snapshot in raw_release_snapshots:
                if not isinstance(raw_snapshot, dict):
                    errors.append("every release snapshot must be an object")
                    continue
                snapshot_id = str(raw_snapshot.get("id", "<missing-id>"))
                if snapshot_id in seen_snapshot_ids:
                    errors.append(f"{snapshot_id}: duplicate release snapshot id")
                    continue
                seen_snapshot_ids.add(snapshot_id)
                release_snapshot_results.append(
                    _validate_release_snapshot(raw_snapshot, entries_by_id, summaries_by_id, registry_path, errors)
                )

    unmet_v0_requirements: list[str] = []
    if len(current_model_families) < min_model_families:
        unmet_v0_requirements.append(
            f"current public model families: {len(current_model_families)} of {min_model_families}"
        )
    if repeated_model_baselines < min_model_families:
        unmet_v0_requirements.append(
            f"repeated model baselines: {repeated_model_baselines} of {min_model_families}"
        )
    if requires_tool_agent and not has_tool_agent_baseline:
        unmet_v0_requirements.append("missing current public tool-agent baseline")
    if min_runs < 2:
        warnings.append("v0 min_runs_per_serious_baseline should be at least 2")
    v0_release_snapshot_ready = any(
        item["id"] == "v0.0" and item["ready"] for item in release_snapshot_results
    )

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "public_split": public_counts,
        "baseline_count": len(entries),
        "model_family_count": len(model_families),
        "current_public_model_family_count": len(current_model_families),
        "repeated_model_baseline_count": repeated_model_baselines,
        "has_current_public_tool_agent_baseline": has_tool_agent_baseline,  # legacy alias of has_current_public_model_or_tool_agent_baseline
        "has_current_public_scripted_sanity_baseline": has_current_scripted_sanity_baseline,
        "has_current_public_model_or_tool_agent_baseline": has_current_model_or_tool_agent_baseline,
        "v0_baseline_ready": not unmet_v0_requirements,
        "unmet_v0_requirements": unmet_v0_requirements,
        "release_snapshots": release_snapshot_results,
        "v0_release_snapshot_ready": v0_release_snapshot_ready,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AuthZBench-SaaS baseline registry honesty.")
    parser.add_argument("--registry", default=str(ROOT / "baselines" / "baseline-registry.json"))
    args = parser.parse_args()
    result = validate_registry(Path(args.registry))
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
