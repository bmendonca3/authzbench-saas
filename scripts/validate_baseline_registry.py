from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
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

VALID_KINDS = {"harness_check", "model_baseline", "tool_agent_baseline"}
VALID_SUITABILITY = {"current_public_split", "current_public_harness_check", "legacy_snapshot"}


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
    errors: list[str],
    label: str = "summary",
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
    if suitability in {"current_public_split", "current_public_harness_check"}:
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

    return summary


def _has_repeated_run_evidence(
    registry_path: Path,
    raw_entry: dict[str, Any],
    entry_id: str,
    run_count: int,
    expected_task_count: int,
    public_counts: dict[str, int],
    errors: list[str],
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
            errors,
            label="run artifact",
        )
        run_id = str(artifact.get("run_id", "")).strip() if isinstance(artifact, dict) else ""
        if not run_id:
            errors.append(f"{entry_id}: run artifact {_display_path(candidate)} must include a run_id")
            ok = False
        elif run_id in seen_run_ids:
            errors.append(f"{entry_id}: run_artifacts must contain distinct run_id values")
            ok = False
        else:
            seen_run_ids.add(run_id)
    return ok


def validate_registry(registry_path: Path = ROOT / "baselines" / "baseline-registry.json") -> dict[str, Any]:
    registry = load_json(registry_path)
    errors: list[str] = []
    warnings: list[str] = []
    public_counts = _task_counts()
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
    repeated_model_baselines = 0

    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            errors.append("every baseline entry must be an object")
            continue
        entry_id = str(raw_entry.get("id", "<missing-id>"))
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(raw_entry))
        if missing:
            errors.append(f"{entry_id}: missing registry fields: {', '.join(missing)}")
            continue

        kind = str(raw_entry.get("kind"))
        suitability = str(raw_entry.get("release_suitability"))
        run_count = _require_int(raw_entry.get("run_count"), "run_count", entry_id, errors)
        expected_task_count = _require_int(raw_entry.get("expected_task_count"), "expected_task_count", entry_id, errors)
        leaderboard_eligible = raw_entry.get("leaderboard_eligible")
        requires_rerun = bool(raw_entry.get("requires_rerun_before_v0"))

        if kind not in VALID_KINDS:
            errors.append(f"{entry_id}: kind must be one of {', '.join(sorted(VALID_KINDS))}")
        if suitability not in VALID_SUITABILITY:
            errors.append(f"{entry_id}: release_suitability must be one of {', '.join(sorted(VALID_SUITABILITY))}")
        if not isinstance(leaderboard_eligible, bool):
            errors.append(f"{entry_id}: leaderboard_eligible must be boolean")
        if suitability == "current_public_harness_check" and kind != "harness_check":
            errors.append(f"{entry_id}: current_public_harness_check is only valid for harness_check entries")
        if kind == "harness_check" and suitability == "current_public_split":
            errors.append(f"{entry_id}: harness checks must use current_public_harness_check, not current_public_split")

        summary = _validate_summary_file(
            registry_path,
            raw_entry,
            entry_id,
            str(raw_entry.get("summary_path")),
            expected_task_count,
            public_counts,
            errors,
        )
        if summary is None:
            continue

        if suitability == "legacy_snapshot":
            if not requires_rerun:
                errors.append(f"{entry_id}: legacy_snapshot must set requires_rerun_before_v0=true")

        if kind in {"model_baseline", "tool_agent_baseline"}:
            model_family = str(raw_entry.get("model_family", "")).strip()
            if not model_family:
                errors.append(f"{entry_id}: model baselines must declare model_family")
            else:
                model_families.add(model_family)
                if suitability == "current_public_split":
                    current_model_families.add(model_family)
            if kind == "tool_agent_baseline" and suitability == "current_public_split":
                has_tool_agent_baseline = True
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
                    errors,
                )
            if run_count >= min_runs and has_repeated_evidence:
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

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "public_split": public_counts,
        "baseline_count": len(entries),
        "model_family_count": len(model_families),
        "current_public_model_family_count": len(current_model_families),
        "repeated_model_baseline_count": repeated_model_baselines,
        "has_current_public_tool_agent_baseline": has_tool_agent_baseline,
        "v0_baseline_ready": not unmet_v0_requirements,
        "unmet_v0_requirements": unmet_v0_requirements,
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
