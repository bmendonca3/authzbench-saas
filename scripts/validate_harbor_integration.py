from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.validate_harbor_adapter_blockers import validate_harbor_adapter_blockers
except ModuleNotFoundError:  # direct execution as python3 scripts/validate_harbor_integration.py
    from validate_harbor_adapter_blockers import validate_harbor_adapter_blockers


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "artifact" / "harbor-adapter-contract.json"
RUNBOOK_PATH = ROOT / "docs" / "harbor-integration-runbook.md"
BLOCKERS_PATH = ROOT / "artifact" / "harbor-adapter-readiness-blockers.json"
SCHEMA_VERSION = "harbor-adapter-contract-v1"
REQUIRED_COMPONENTS = {
    "dataset_builder",
    "task_context_renderer",
    "runner_bridge",
    "output_collector",
    "verifier_scorer_bridge",
    "metadata_normalizer",
    "artifact_redaction_policy",
    "dataset_skeleton_builder",
    "reference_run_config",
}
REQUIRED_LANES = {"no_tools", "live_http_tool_agent"}
REQUIRED_METADATA = {
    "benchmark_source_sha",
    "benchmark_fingerprint",
    "comparability_key",
    "harness_type",
    "model",
    "agent",
    "tool_access",
    "timeout_seconds",
    "source_summary_hashes",
    "target_request_coverage_rate",
    "private_pack_version",
    "private_pack_fingerprint_sha256",
    "redaction_status",
    "privacy_scan_status",
}
REQUIRED_PUBLIC_SOURCES = {
    "https://github.com/harbor-framework/harbor",
    "https://www.harborframework.com/docs/run-jobs/run-evals",
    "https://www.harborframework.com/docs/tasks",
    "https://www.harborframework.com/docs/run-jobs/results-and-artifacts",
}
REQUIRED_PACKAGE_LAYOUT = {
    "pyproject.toml",
    "README.md",
    "adapter_metadata.json",
    "parity_experiment.json",
    "run_authzbench_saas.yaml",
    "src/authzbench_saas_harbor/__init__.py",
    "src/authzbench_saas_harbor/adapter.py",
    "src/authzbench_saas_harbor/main.py",
    "src/authzbench_saas_harbor/task-template/task.toml",
    "src/authzbench_saas_harbor/task-template/instruction.md",
    "src/authzbench_saas_harbor/task-template/environment/Dockerfile",
    "src/authzbench_saas_harbor/task-template/solution/solve.sh",
    "src/authzbench_saas_harbor/task-template/tests/test.sh",
}
REQUIRED_ADAPTER_CLI_FLAGS = {"--output-dir", "--limit", "--overwrite", "--task-ids"}
DISALLOWED_TEXT = (
    "accepted",
    "endorsed",
    "private meeting",
    "calendar." + "google.com",
    "appointments/" + "schedules",
)
SENSITIVE_TEXT = (
    "private route:",
    "private seed:",
    "raw private output at",
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


def _string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(_string_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(_string_values(child))
        return values
    if isinstance(value, str):
        return [value]
    return []


def _public_safety_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for value in _string_values(data):
        lower = value.lower()
        for marker in DISALLOWED_TEXT:
            if marker in lower:
                errors.append(f"disallowed overclaim/private marker: {marker}")
        for marker in SENSITIVE_TEXT:
            if marker in lower:
                errors.append(f"sensitive private detail marker is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(value):
            if not any(match.startswith(prefix) for prefix in ALLOWED_ABSOLUTE_PREFIXES):
                errors.append(f"local absolute path is not allowed: {match}")
    return errors


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_harbor_integration(
    contract_path: Path = CONTRACT_PATH,
    runbook_path: Path = RUNBOOK_PATH,
    blockers_path: Path = BLOCKERS_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        data = _load_json(contract_path)
    except Exception as exc:
        return {"passed": False, "errors": [str(exc)]}

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("evidence_status") != "implementation_target":
        errors.append("evidence_status must be implementation_target")
    boundary = data.get("public_claim_boundary")
    if not _nonempty_string(boundary) or "not" not in str(boundary).lower():
        errors.append("public_claim_boundary must state the contract is not execution/readiness evidence")
    if "harbor run -p" not in str(data.get("local_run_template", "")):
        errors.append("local_run_template must include harbor run -p")
    dataset_shape = data.get("dataset_shape")
    if not isinstance(dataset_shape, dict):
        errors.append("dataset_shape must be an object")
        dataset_shape = {}
    if dataset_shape.get("task_toml_schema_version") != "1.3":
        errors.append("dataset_shape.task_toml_schema_version must be 1.3")
    task_directory_files = set(dataset_shape.get("task_directory_files") or [])
    for required_file in (
        "instruction.md",
        "task.toml",
        "environment/Dockerfile",
        "verifier/task_manifest.json",
        "solution/solve.sh",
        "tests/test.sh",
        "run_authzbench_saas.yaml",
    ):
        if required_file not in task_directory_files:
            errors.append(f"dataset_shape.task_directory_files missing: {required_file}")

    public_sources = set(data.get("public_sources") or [])
    missing_sources = sorted(REQUIRED_PUBLIC_SOURCES - public_sources)
    if missing_sources:
        errors.append("public_sources missing: " + ", ".join(missing_sources))

    components = data.get("adapter_components")
    if not isinstance(components, list):
        errors.append("adapter_components must be a list")
        components = []
    component_names = {item.get("name") for item in components if isinstance(item, dict)}
    missing_components = sorted(REQUIRED_COMPONENTS - component_names)
    if missing_components:
        errors.append("adapter_components missing: " + ", ".join(missing_components))
    for component in components:
        if not isinstance(component, dict):
            errors.append("adapter_components entries must be objects")
            continue
        if component.get("required") is not True:
            errors.append(f"{component.get('name')}: required must be true")
        if not _nonempty_string(component.get("responsibility")):
            errors.append(f"{component.get('name')}: responsibility is required")

    lanes = data.get("lanes")
    if not isinstance(lanes, list):
        errors.append("lanes must be a list")
        lanes = []
    lane_names = {item.get("name") for item in lanes if isinstance(item, dict)}
    missing_lanes = sorted(REQUIRED_LANES - lane_names)
    if missing_lanes:
        errors.append("lanes missing: " + ", ".join(missing_lanes))
    for lane in lanes:
        if not isinstance(lane, dict):
            errors.append("lanes entries must be objects")
            continue
        if lane.get("required") is not True:
            errors.append(f"{lane.get('name')}: required must be true")
        for field in ("agent_input", "agent_output", "scoring_rule"):
            if not _nonempty_string(lane.get(field)):
                errors.append(f"{lane.get('name')}: {field} is required")
    lane_text = json.dumps(lanes, sort_keys=True)
    if "findings: []" not in lane_text:
        errors.append("lanes must preserve secure-control findings: [] rule")
    if "target-request coverage" not in lane_text:
        errors.append("live HTTP lane must require target-request coverage")

    artifact_mapping = data.get("artifact_mapping")
    if not isinstance(artifact_mapping, list) or len(artifact_mapping) < 5:
        errors.append("artifact_mapping must include at least five Harbor/AuthZBench mappings")

    metadata = set(data.get("required_run_metadata") or [])
    missing_metadata = sorted(REQUIRED_METADATA - metadata)
    if missing_metadata:
        errors.append("required_run_metadata missing: " + ", ".join(missing_metadata))

    protected = data.get("protected_private_requirements")
    if not isinstance(protected, list) or len(protected) < 5:
        errors.append("protected_private_requirements must list concrete private-execution safeguards")
    blocked = data.get("blocked_until")
    if not isinstance(blocked, list) or len(blocked) < 5:
        errors.append("blocked_until must list concrete blockers")

    expected_package = data.get("expected_adapter_package")
    if not isinstance(expected_package, dict):
        errors.append("expected_adapter_package must be an object")
        expected_package = {}
    else:
        if expected_package.get("evidence_status") != "implementation_target":
            errors.append("expected_adapter_package.evidence_status must be implementation_target")
        package_boundary = str(expected_package.get("claim_boundary", ""))
        if "not implemented Harbor SDK integration" not in package_boundary:
            errors.append("expected_adapter_package.claim_boundary must reject implemented-SDK evidence claims")
        package_layout = set(expected_package.get("package_layout") or [])
        missing_package_layout = sorted(REQUIRED_PACKAGE_LAYOUT - package_layout)
        if missing_package_layout:
            errors.append("expected_adapter_package.package_layout missing: " + ", ".join(missing_package_layout))
        module_entrypoint = str(expected_package.get("module_entrypoint", ""))
        if "uv run python -m authzbench_saas_harbor.main" not in module_entrypoint:
            errors.append("expected_adapter_package.module_entrypoint must name the future module entrypoint")
        if "--output-dir" not in module_entrypoint:
            errors.append("expected_adapter_package.module_entrypoint must include --output-dir")
        cli_flags = set(expected_package.get("required_cli_flags") or [])
        missing_cli_flags = sorted(REQUIRED_ADAPTER_CLI_FLAGS - cli_flags)
        if missing_cli_flags:
            errors.append("expected_adapter_package.required_cli_flags missing: " + ", ".join(missing_cli_flags))
        helper = str(expected_package.get("repo_side_compatibility_helper", ""))
        for flag in sorted(REQUIRED_ADAPTER_CLI_FLAGS):
            if flag not in helper:
                errors.append(f"expected_adapter_package.repo_side_compatibility_helper missing {flag}")
        package_blockers = expected_package.get("blocked_until")
        if not isinstance(package_blockers, list) or len(package_blockers) < 3:
            errors.append("expected_adapter_package.blocked_until must list concrete blockers")

    if not runbook_path.exists():
        errors.append(f"missing runbook: {runbook_path.relative_to(ROOT)}")
    else:
        runbook = runbook_path.read_text(encoding="utf-8")
        for term in (
            "Harbor-compatible execution target",
            "SDK Adapter Expectations",
            "Live HTTP Tool-Agent Lane",
            "scripts/build_harbor_dataset_skeleton.py",
            "scripts/validate_harbor_dataset_skeleton.py",
            "scripts/validate_harbor_adapter_blockers.py",
            "scripts/check_harbor_local_execution.py",
        ):
            if term not in runbook:
                errors.append(f"runbook missing required term: {term}")

    blocker_result = validate_harbor_adapter_blockers(blockers_path)
    if not blocker_result["passed"]:
        for error in blocker_result["errors"]:
            errors.append(f"adapter_readiness_blockers: {error}")

    errors.extend(_public_safety_errors(data))
    return {
        "adapter_component_count": len(component_names),
        "errors": sorted(set(errors)),
        "lane_count": len(lane_names),
        "passed": not errors,
        "required_metadata_count": len(metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe Harbor adapter planning contract.")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--runbook", type=Path, default=RUNBOOK_PATH)
    parser.add_argument("--blockers", type=Path, default=BLOCKERS_PATH)
    args = parser.parse_args()
    result = validate_harbor_integration(args.contract, args.runbook, args.blockers)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
