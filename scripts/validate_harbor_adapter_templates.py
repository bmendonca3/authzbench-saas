from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_METADATA_TEMPLATE_PATH = ROOT / "artifact" / "harbor-adapter-metadata.template.json"
PARITY_EXPERIMENT_TEMPLATE_PATH = ROOT / "artifact" / "harbor-parity-experiment.template.json"
ADAPTER_METADATA_SCHEMA_VERSION = "harbor-adapter-metadata-template-v1"
PARITY_EXPERIMENT_SCHEMA_VERSION = "harbor-parity-experiment-template-v1"
REQUIRED_CLI_FLAGS = {"--output-dir", "--limit", "--overwrite", "--task-ids"}
REQUIRED_DATASET_ROOT_FILES = {"dataset.toml", "dataset-manifest.json", "run_authzbench_saas.yaml"}
REQUIRED_TASK_DIRECTORY_FILES = {
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "verifier/task_manifest.json",
    "solution/solve.sh",
    "tests/test.sh",
}
REQUIRED_LANES = {"no_tools", "live_http_tool_agent"}
REQUIRED_PARITY_INPUTS = {
    "real Harbor runs from the packaged adapter",
    "matching original AuthZBench-SaaS runs",
    "matching benchmark_source_sha",
    "matching comparability_key",
    "matching task ids or redacted private-pack fingerprint",
    "matching agent/model/timeouts",
    "public-safe redaction and privacy scan status",
}
REQUIRED_PARITY_RESULT_FIELDS = {
    "harbor_run_ids",
    "authzbench_run_ids",
    "task_count",
    "metric_name",
    "harbor_mean",
    "authzbench_mean",
    "absolute_delta",
    "standard_error",
    "parity_acceptance_rule",
    "privacy_scan_status",
}
DISALLOWED_TEXT = (
    "calendar." + "google.com",
    "appointments/" + "schedules",
    "accepted" + " by",
    "endorsed" + " by",
)
PRIVATE_MARKERS = (
    "tasks_private/holdout",
    "private route:",
    "private seed:",
    "raw private output",
    "credential:",
    "oracle:",
)
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")
ALLOWED_ABSOLUTE_PREFIXES = ("/logs/artifacts/",)


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


def _public_safety_errors(data: dict[str, Any], *, label: str) -> list[str]:
    errors: list[str] = []
    for value in _text_values(data):
        lower = value.lower()
        for marker in DISALLOWED_TEXT:
            if marker in lower:
                errors.append(f"{label}: disallowed overclaim/private marker: {marker}")
        for marker in PRIVATE_MARKERS:
            if marker in lower:
                errors.append(f"{label}: private detail marker is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(value):
            if not any(match.startswith(prefix) for prefix in ALLOWED_ABSOLUTE_PREFIXES):
                errors.append(f"{label}: local absolute path is not allowed: {match}")
    return errors


def _missing(required: set[str], actual: Any) -> list[str]:
    return sorted(required - {str(item) for item in actual or [] if isinstance(item, str)})


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def validate_harbor_adapter_templates(
    adapter_metadata_template_path: Path = ADAPTER_METADATA_TEMPLATE_PATH,
    parity_experiment_template_path: Path = PARITY_EXPERIMENT_TEMPLATE_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        metadata = _load_json(adapter_metadata_template_path)
    except Exception as exc:
        return {"errors": [str(exc)], "passed": False}
    try:
        parity = _load_json(parity_experiment_template_path)
    except Exception as exc:
        return {"errors": [str(exc)], "passed": False}

    if metadata.get("schema_version") != ADAPTER_METADATA_SCHEMA_VERSION:
        errors.append(f"adapter metadata template schema_version must be {ADAPTER_METADATA_SCHEMA_VERSION}")
    if metadata.get("template_only") is not True:
        errors.append("adapter metadata template must set template_only true")
    if metadata.get("evidence_status") != "implementation_template":
        errors.append("adapter metadata template evidence_status must be implementation_template")
    metadata_boundary = str(metadata.get("public_claim_boundary", ""))
    if "not Harbor adapter metadata evidence" not in metadata_boundary or "not Harbor execution evidence" not in metadata_boundary:
        errors.append("adapter metadata template claim boundary must reject metadata and execution evidence claims")
    if metadata.get("adapter_name") != "authzbench-saas-harbor":
        errors.append("adapter metadata template adapter_name must be authzbench-saas-harbor")
    if "uv run python -m authzbench_saas_harbor.main" not in str(metadata.get("package_entrypoint", "")):
        errors.append("adapter metadata template package_entrypoint must name the future module entrypoint")
    missing_flags = _missing(REQUIRED_CLI_FLAGS, metadata.get("required_cli_flags"))
    if missing_flags:
        errors.append("adapter metadata template required_cli_flags missing: " + ", ".join(missing_flags))
    missing_root = _missing(REQUIRED_DATASET_ROOT_FILES, metadata.get("dataset_root_files"))
    if missing_root:
        errors.append("adapter metadata template dataset_root_files missing: " + ", ".join(missing_root))
    missing_task_files = _missing(REQUIRED_TASK_DIRECTORY_FILES, metadata.get("task_directory_files"))
    if missing_task_files:
        errors.append("adapter metadata template task_directory_files missing: " + ", ".join(missing_task_files))
    missing_lanes = _missing(REQUIRED_LANES, metadata.get("supported_lanes"))
    if missing_lanes:
        errors.append("adapter metadata template supported_lanes missing: " + ", ".join(missing_lanes))
    artifact_policy = metadata.get("artifact_policy")
    if not isinstance(artifact_policy, dict):
        errors.append("adapter metadata template artifact_policy must be an object")
        artifact_policy = {}
    if artifact_policy.get("public_outputs_redacted") is not True:
        errors.append("adapter metadata template artifact_policy.public_outputs_redacted must be true")
    if artifact_policy.get("private_manifests_tracked") is not False:
        errors.append("adapter metadata template artifact_policy.private_manifests_tracked must be false")
    if artifact_policy.get("raw_private_artifacts_tracked") is not False:
        errors.append("adapter metadata template artifact_policy.raw_private_artifacts_tracked must be false")
    if not isinstance(metadata.get("required_before_real_metadata"), list) or len(metadata["required_before_real_metadata"]) < 4:
        errors.append("adapter metadata template required_before_real_metadata must list concrete blockers")

    if parity.get("schema_version") != PARITY_EXPERIMENT_SCHEMA_VERSION:
        errors.append(f"parity experiment template schema_version must be {PARITY_EXPERIMENT_SCHEMA_VERSION}")
    if parity.get("template_only") is not True:
        errors.append("parity experiment template must set template_only true")
    if parity.get("evidence_status") != "implementation_template":
        errors.append("parity experiment template evidence_status must be implementation_template")
    parity_boundary = str(parity.get("public_claim_boundary", ""))
    if "not Harbor parity evidence" not in parity_boundary or "not Harbor execution evidence" not in parity_boundary:
        errors.append("parity experiment template claim boundary must reject parity and execution evidence claims")
    if parity.get("parity_verified") is not False:
        errors.append("parity experiment template parity_verified must be false")
    if parity.get("harbor_execution_verified") is not False:
        errors.append("parity experiment template harbor_execution_verified must be false")
    if parity.get("comparison_scope") != "future_verified_runs_only":
        errors.append("parity experiment template comparison_scope must be future_verified_runs_only")
    missing_inputs = _missing(REQUIRED_PARITY_INPUTS, parity.get("required_inputs"))
    if missing_inputs:
        errors.append("parity experiment template required_inputs missing: " + ", ".join(missing_inputs))
    missing_result_fields = _missing(REQUIRED_PARITY_RESULT_FIELDS, parity.get("result_fields_required_before_parity_claim"))
    if missing_result_fields:
        errors.append("parity experiment template result_fields_required_before_parity_claim missing: " + ", ".join(missing_result_fields))
    if parity.get("result_rows") != []:
        errors.append("parity experiment template result_rows must be empty")
    if not isinstance(parity.get("blocked_until"), list) or len(parity["blocked_until"]) < 4:
        errors.append("parity experiment template blocked_until must list concrete blockers")

    errors.extend(_public_safety_errors(metadata, label=adapter_metadata_template_path.name))
    errors.extend(_public_safety_errors(parity, label=parity_experiment_template_path.name))
    return {
        "adapter_metadata_template": _display_path(adapter_metadata_template_path),
        "errors": sorted(set(errors)),
        "parity_experiment_template": _display_path(parity_experiment_template_path),
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe Harbor adapter metadata/parity templates.")
    parser.add_argument("--adapter-metadata-template", type=Path, default=ADAPTER_METADATA_TEMPLATE_PATH)
    parser.add_argument("--parity-experiment-template", type=Path, default=PARITY_EXPERIMENT_TEMPLATE_PATH)
    args = parser.parse_args()
    result = validate_harbor_adapter_templates(args.adapter_metadata_template, args.parity_experiment_template)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
