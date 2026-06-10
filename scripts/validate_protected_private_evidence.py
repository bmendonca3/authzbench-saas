from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import runner_integrity_envelope


SENSITIVE_KEYS = {
    "controls",
    "oracle",
    "run_dir",
    "target_log_dir",
    "task_id",
    "task_path",
    "tasks",
    "transcript",
}

SENSITIVE_STRING_MARKERS = (
    "/Users/",
    "captures/",
    "docs/reviews/panel-logs",
    "results/",
    "tasks_private/holdout",
)
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")

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


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: summary must be a JSON object")
    return data


def _find_sensitive_items(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in SENSITIVE_KEYS:
                findings.append(f"{child_path}: sensitive key is not allowed in redacted evidence")
            findings.extend(_find_sensitive_items(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_sensitive_items(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for marker in SENSITIVE_STRING_MARKERS:
            if marker in value:
                findings.append(f"{path}: sensitive path marker {marker!r} is not allowed")
        if ABSOLUTE_PATH_RE.search(value):
            findings.append(f"{path}: absolute path is not allowed in redacted evidence")
    return findings


def _summary_errors(path: Path, summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    protected = summary.get("protected_execution") if isinstance(summary.get("protected_execution"), dict) else {}
    private_count = int(summary.get("private_holdout_task_count") or summary.get("task_count") or 0)
    vulnerable_count = int(summary.get("vulnerable_task_count") or 0)
    control_count = int(summary.get("control_task_count") or 0)
    authorized_allow_count = int(summary.get("authorized_allow_control_task_count") or 0)
    fingerprint = summary.get("benchmark_fingerprint")

    if summary.get("redacted_private_holdout_source") is not True:
        errors.append(f"{path}: redacted_private_holdout_source must be true")
    if summary.get("split") != "private-holdout":
        errors.append(f"{path}: split must be private-holdout")
    if int(summary.get("public_task_count") or 0) != 0:
        errors.append(f"{path}: public_task_count must be 0")
    if not (20 <= private_count <= 30):
        errors.append(f"{path}: private holdout task count must be 20-30; got {private_count}")
    if int(summary.get("task_count") or 0) != private_count:
        errors.append(f"{path}: task_count must match private_holdout_task_count")
    if vulnerable_count < 12:
        errors.append(f"{path}: vulnerable_task_count minimum is 12; got {vulnerable_count}")
    if control_count < 8:
        errors.append(f"{path}: control_task_count must be at least 8; got {control_count}")
    if authorized_allow_count < 4:
        errors.append(
            f"{path}: authorized_allow_control_task_count must be at least 4; got {authorized_allow_count}"
        )
    if summary.get("raw_private_artifacts_tracked") is not False:
        errors.append(f"{path}: raw_private_artifacts_tracked must be false")
    if summary.get("full_result_bundle_tracked") is not False:
        errors.append(f"{path}: full_result_bundle_tracked must be false")
    if int(summary.get("tracked_private_manifest_count") or 0) != 0:
        errors.append(f"{path}: tracked_private_manifest_count must be 0")
    if protected.get("private_manifests_readable_in_agent_workspace") is not False:
        errors.append(f"{path}: private manifests must not be readable in the agent workspace")
    if protected.get("agent_received") != "rendered-context-only":
        errors.append(f"{path}: protected execution must provide rendered context only")
    if int(protected.get("tracked_private_manifest_count") or 0) != 0:
        errors.append(f"{path}: protected_execution.tracked_private_manifest_count must be 0")
    if not str(summary.get("run_id") or "").strip():
        errors.append(f"{path}: run_id is required")
    if int(summary.get("invalid_submission_count") or 0) != 0:
        errors.append(f"{path}: invalid_submission_count must be 0")
    if int(summary.get("control_false_report_count") or 0) != 0:
        errors.append(f"{path}: control_false_report_count must be 0")
    if not isinstance(fingerprint, dict):
        errors.append(f"{path}: benchmark_fingerprint must be an object")
    else:
        missing = sorted(FINGERPRINT_FIELDS - set(fingerprint))
        if missing:
            errors.append(f"{path}: benchmark_fingerprint missing fields: {', '.join(missing)}")
        if fingerprint.get("schema_version") != "benchmark-fingerprint-v1":
            errors.append(f"{path}: benchmark_fingerprint schema_version must be benchmark-fingerprint-v1")
        for field, expected in (
            ("task_count", private_count),
            ("vulnerable_task_count", vulnerable_count),
            ("control_task_count", control_count),
            ("denial_control_task_count", int(summary.get("denial_control_task_count") or 0)),
            ("authorized_allow_control_task_count", authorized_allow_count),
        ):
            if fingerprint.get(field) != expected:
                errors.append(f"{path}: benchmark_fingerprint.{field} must match summary {field}")
        for field in ("task_set_sha256", "task_path_set_sha256"):
            value = fingerprint.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                errors.append(f"{path}: benchmark_fingerprint.{field} must be a lowercase SHA-256 digest")
    provenance = summary.get("benchmark_fingerprint_provenance")
    if provenance not in {"runner-emitted", "recomputed-from-maintained-private-pack"}:
        errors.append(f"{path}: benchmark_fingerprint_provenance is invalid")
    if provenance == "runner-emitted":
        expected_integrity = runner_integrity_envelope(
            summary,
            generator="scripts/protected_private_eval.py",
        )
        if summary.get("runner_integrity") != expected_integrity:
            errors.append(f"{path}: runner_integrity is missing or invalid")
    errors.extend(f"{path}: {finding}" for finding in _find_sensitive_items(summary))
    return errors


def validate_protected_private_evidence(
    paths: list[Path],
    *,
    min_run_count: int = 2,
    require_tool_agent: bool = True,
    min_target_request_coverage: float | None = 1.0,
    require_host_isolation: bool = False,
) -> dict[str, Any]:
    summaries = [_load_json(path) for path in paths]
    errors: list[str] = []
    for path, summary in zip(paths, summaries):
        errors.extend(_summary_errors(path, summary))

    run_ids = [str(summary.get("run_id") or "") for summary in summaries]
    unique_run_ids = {run_id for run_id in run_ids if run_id}
    if len(summaries) < min_run_count:
        errors.append(f"protected private evidence requires at least {min_run_count} runs; got {len(summaries)}")
    if len(unique_run_ids) != len(run_ids):
        errors.append("protected private evidence run_id values must be unique")

    task_counts = {int(summary.get("private_holdout_task_count") or summary.get("task_count") or 0) for summary in summaries}
    if len(task_counts) > 1:
        errors.append("protected private evidence summaries must use the same private holdout task count")
    fingerprints = {
        json.dumps(summary.get("benchmark_fingerprint"), sort_keys=True, separators=(",", ":"))
        for summary in summaries
        if isinstance(summary.get("benchmark_fingerprint"), dict)
    }
    if len(fingerprints) > 1:
        errors.append("protected private evidence summaries must use the same benchmark_fingerprint")

    tool_agent_summaries = [summary for summary in summaries if summary.get("harness_type") == "tool-agent"]
    host_isolated_summaries = [
        summary
        for summary in summaries
        if isinstance(summary.get("protected_execution"), dict)
        and summary["protected_execution"].get("host_private_paths_denied") is True
    ]
    if require_host_isolation and len(host_isolated_summaries) != len(summaries):
        errors.append("all protected private evidence summaries must enforce host private-path denial")
    if require_tool_agent and not tool_agent_summaries:
        errors.append("at least one protected private tool-agent summary is required")
    if min_target_request_coverage is not None:
        covered = [
            summary
            for summary in tool_agent_summaries
            if isinstance(summary.get("target_request_coverage_rate"), (int, float))
            and float(summary["target_request_coverage_rate"]) >= min_target_request_coverage
        ]
        if require_tool_agent and not covered:
            errors.append(
                "at least one protected private tool-agent summary must meet target request coverage "
                f"{min_target_request_coverage}"
            )

    return {
        "errors": errors,
        "harness_types": sorted({str(summary.get("harness_type")) for summary in summaries}),
        "host_isolated_summary_count": len(host_isolated_summaries),
        "max_target_request_coverage_rate": max(
            (
                float(summary["target_request_coverage_rate"])
                for summary in summaries
                if isinstance(summary.get("target_request_coverage_rate"), (int, float))
            ),
            default=None,
        ),
        "model_count": len({str(summary.get("model")) for summary in summaries}),
        "passed": not errors,
        "private_holdout_task_count": next(iter(task_counts), 0) if task_counts else 0,
        "protected_private_run_count": len(summaries),
        "raw_private_artifacts_tracked": any(bool(summary.get("raw_private_artifacts_tracked")) for summary in summaries),
        "redacted_summary_count": len(summaries),
        "tool_agent_summary_count": len(tool_agent_summaries),
        "tracked_private_manifest_count": sum(int(summary.get("tracked_private_manifest_count") or 0) for summary in summaries),
        "unique_run_count": len(unique_run_ids),
    }


def _expand_patterns(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern))
    return sorted({path for path in paths if path.is_file()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate redacted protected-private evidence summaries.")
    parser.add_argument("--summary", action="append", required=True, help="Redacted summary path or glob. Repeatable.")
    parser.add_argument("--min-run-count", type=int, default=2)
    parser.add_argument("--no-require-tool-agent", action="store_true")
    parser.add_argument("--min-target-request-coverage", type=float, default=1.0)
    parser.add_argument("--require-host-isolation", action="store_true")
    args = parser.parse_args()

    paths = _expand_patterns(args.summary)
    result = validate_protected_private_evidence(
        paths,
        min_run_count=args.min_run_count,
        require_tool_agent=not args.no_require_tool_agent,
        min_target_request_coverage=args.min_target_request_coverage,
        require_host_isolation=args.require_host_isolation,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
