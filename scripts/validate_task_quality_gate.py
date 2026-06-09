from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "artifact" / "task-quality-gate-contract.json"
CONTRACT_SCHEMA_VERSION = "task-quality-gate-contract-v1"

REQUIRED_GATE_IDS = {
    "task_family_design_spec",
    "static_manifest_boundary_validation",
    "app_behavior_tests",
    "scorer_fixtures",
    "scripted_baseline_sanity",
    "matrix_and_chart_regeneration",
    "privacy_and_public_output_scan",
}

REQUIRED_SCORER_FIXTURES = {
    "positive_exploit",
    "wrong_actor",
    "wrong_tenant",
    "wrong_object",
    "missing_boundary",
    "secure_false_positive_failure",
    "secure_empty_findings_pass",
}

AUTHORIZATION_BOUNDARY_KEYS = {
    "victim_tenant",
    "victim_org",
    "victim_workspace",
    "required_role",
    "required_scope",
    "required_link_state",
    "required_boundary",
    "protected_action",
    "entitlement",
    "setting",
    "resource",
    "org",
}

ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")
PRIVATE_MARKERS = (
    "credential:",
    "private route:",
    "private seed:",
    "raw private output",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(item) for item in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(text_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(text_values(child))
        return values
    if isinstance(value, str):
        return [value]
    return []


def validate_contract(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - validators should report compact failures.
        return [f"{display_path(path)}: failed to load contract: {type(exc).__name__}: {exc}"]

    if data.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        errors.append(f"{display_path(path)}: schema_version must be {CONTRACT_SCHEMA_VERSION}")
    boundary = str(data.get("public_claim_boundary", ""))
    for required_phrase in ("not external review evidence", "not v1 readiness evidence"):
        if required_phrase not in boundary:
            errors.append(f"{display_path(path)}: public_claim_boundary must include {required_phrase!r}")
    privacy_boundary = str(data.get("privacy_boundary", ""))
    for required_phrase in ("private manifests", "local absolute paths", "private-source details"):
        if required_phrase not in privacy_boundary:
            errors.append(f"{display_path(path)}: privacy_boundary must cover {required_phrase!r}")

    gates = data.get("required_gates")
    if not isinstance(gates, list):
        return errors + [f"{display_path(path)}: required_gates must be a list"]
    gate_ids = {gate.get("id") for gate in gates if isinstance(gate, dict)}
    missing_gates = sorted(REQUIRED_GATE_IDS - gate_ids)
    if missing_gates:
        errors.append(f"{display_path(path)}: required_gates missing: {', '.join(missing_gates)}")

    scorer_gate = next((gate for gate in gates if isinstance(gate, dict) and gate.get("id") == "scorer_fixtures"), {})
    scorer_evidence = set(scorer_gate.get("evidence") or [])
    missing_fixtures = sorted(REQUIRED_SCORER_FIXTURES - scorer_evidence)
    if missing_fixtures:
        errors.append(f"{display_path(path)}: scorer_fixtures evidence missing: {', '.join(missing_fixtures)}")

    for value in text_values(data):
        lower = value.lower()
        for marker in PRIVATE_MARKERS:
            if marker in lower:
                errors.append(f"{display_path(path)}: private marker is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(value):
            errors.append(f"{display_path(path)}: local absolute path is not allowed: {match}")
    return errors


def has_replay_check(item: dict[str, Any]) -> bool:
    return isinstance(item.get("status"), int) or "body_contains" in item


def validate_control_shape(path: Path, task_id: str, controls: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(controls, list) or not controls:
        return [f"{display_path(path)}: {task_id}: controls must be a non-empty list"]
    for index, control in enumerate(controls):
        if not isinstance(control, dict):
            errors.append(f"{display_path(path)}: {task_id}: controls[{index}] must be an object")
            continue
        for field in ("actor", "method", "path", "status"):
            if field not in control:
                errors.append(f"{display_path(path)}: {task_id}: controls[{index}].{field} is required")
        if not has_replay_check(control):
            errors.append(f"{display_path(path)}: {task_id}: controls[{index}] must include status or body_contains")
    return errors


def validate_task(path: Path) -> tuple[dict[str, int], list[str]]:
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - keep validation output concise.
        return {}, [f"{display_path(path)}: failed to load manifest: {type(exc).__name__}: {exc}"]

    errors: list[str] = []
    task_id = str(data.get("id") or path.stem)
    expected_vulnerable = data.get("expected_vulnerable") is True
    oracle = data.get("oracle") if isinstance(data.get("oracle"), dict) else {}
    controls = data.get("controls")
    control_list = controls if isinstance(controls, list) else []
    stats = {
        "task_count": 1,
        "vulnerable_task_count": 1 if expected_vulnerable else 0,
        "control_task_count": 0 if expected_vulnerable else 1,
        "denial_control_task_count": 1 if data.get("control_type") == "denial" else 0,
        "authorized_allow_control_task_count": 1 if data.get("control_type") == "authorized_allow" else 0,
    }

    if data.get("split", "public") != "public":
        errors.append(f"{display_path(path)}: {task_id}: task-quality gate only counts public manifests")
    if not isinstance(data.get("allowed_hosts"), list) or not data["allowed_hosts"]:
        errors.append(f"{display_path(path)}: {task_id}: allowed_hosts must be a non-empty list")
    errors.extend(validate_control_shape(path, task_id, controls))
    if not has_replay_check(oracle):
        errors.append(f"{display_path(path)}: {task_id}: oracle must include status or body_contains")

    if expected_vulnerable:
        boundary = data.get("expected_boundary")
        if not isinstance(boundary, dict):
            errors.append(f"{display_path(path)}: {task_id}: vulnerable task must include expected_boundary")
            boundary = {}
        if "attacker_actor" not in boundary:
            errors.append(f"{display_path(path)}: {task_id}: expected_boundary must include attacker_actor")
        if not (AUTHORIZATION_BOUNDARY_KEYS & set(boundary)):
            errors.append(
                f"{display_path(path)}: {task_id}: expected_boundary must include a victim or authorization dimension"
            )
        if oracle.get("claim") == "no_vulnerability":
            errors.append(f"{display_path(path)}: {task_id}: vulnerable task must not use no_vulnerability oracle")
        if not any(isinstance(control, dict) and isinstance(control.get("status"), int) and control["status"] >= 400 for control in control_list):
            errors.append(f"{display_path(path)}: {task_id}: vulnerable task must include a secure denial control")
        if "evidence_requirements" in data:
            requirements = data.get("evidence_requirements")
            if not isinstance(requirements, list) or not requirements:
                errors.append(f"{display_path(path)}: {task_id}: evidence_requirements must be a non-empty list when supplied")
            else:
                for index, requirement in enumerate(requirements):
                    request = requirement.get("request") if isinstance(requirement, dict) else None
                    if not isinstance(request, dict):
                        errors.append(f"{display_path(path)}: {task_id}: evidence_requirements[{index}].request is required")
                    elif not all(request.get(field) for field in ("actor", "method", "path")):
                        errors.append(
                            f"{display_path(path)}: {task_id}: evidence_requirements[{index}].request needs actor, method, and path"
                        )
                    if not isinstance(requirement, dict) or not has_replay_check(requirement):
                        errors.append(
                            f"{display_path(path)}: {task_id}: evidence_requirements[{index}] must include status or body_contains"
                        )
    else:
        control_type = data.get("control_type")
        if oracle.get("claim") != "no_vulnerability":
            errors.append(f"{display_path(path)}: {task_id}: secure control must use no_vulnerability oracle")
        if "findings: []" not in str(data.get("output_schema", "")):
            errors.append(f"{display_path(path)}: {task_id}: secure control output_schema must require findings: []")
        if control_type not in {"denial", "authorized_allow"}:
            errors.append(f"{display_path(path)}: {task_id}: secure control_type must be denial or authorized_allow")
        statuses = [control.get("status") for control in control_list if isinstance(control, dict)]
        if control_type == "denial" and not any(isinstance(status, int) and status >= 400 for status in statuses):
            errors.append(f"{display_path(path)}: {task_id}: denial control must include a denial replay check")
        if control_type == "authorized_allow" and not any(isinstance(status, int) and 200 <= status < 300 for status in statuses):
            errors.append(f"{display_path(path)}: {task_id}: authorized_allow control must include a 2xx replay check")

    return stats, errors


def validate_quality_gate(task_patterns: list[str], contract_path: Path) -> dict[str, Any]:
    errors = validate_contract(contract_path)
    totals = {
        "task_count": 0,
        "vulnerable_task_count": 0,
        "control_task_count": 0,
        "denial_control_task_count": 0,
        "authorized_allow_control_task_count": 0,
    }
    paths = manifest_paths(task_patterns)
    if not paths:
        errors.append("no task manifests matched")
    for path in paths:
        stats, task_errors = validate_task(path)
        for key in totals:
            totals[key] += int(stats.get(key, 0))
        errors.extend(task_errors)
    return {
        "schema_version": "task-quality-gate-report-v1",
        "contract": display_path(contract_path),
        "passed": not errors,
        "summary": totals,
        "errors": sorted(set(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe task-quality acceptance gates.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--task", action="append", required=True, help="Public task manifest glob. Can be repeated.")
    args = parser.parse_args()
    result = validate_quality_gate(args.task, args.contract)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
