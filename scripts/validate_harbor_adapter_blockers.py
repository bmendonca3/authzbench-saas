from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_harbor_adapter_metadata import validate_adapter_metadata
from scripts.validate_harbor_compatibility_state import (
    validate_harbor_compatibility_state,
)
from scripts.validate_harbor_local_evidence import validate_harbor_local_evidence
from scripts.validate_harbor_parity_experiment import validate_parity_experiment
from authzbench.core import load_json as load_strict_json


BLOCKERS_PATH = ROOT / "artifact" / "harbor-adapter-readiness-blockers.json"
SCHEMA_VERSION = "harbor-adapter-readiness-blockers-v1"
EVIDENCE_STATUS = "current_readiness_blockers"
METADATA_PATH = ROOT / "artifact" / "harbor-adapter-metadata.json"
PARITY_PATH = ROOT / "artifact" / "harbor-parity-experiment.json"
LOCAL_SMOKE_PATH = ROOT / "artifact" / "harbor-local-execution-smoke.json"
RUNBOOK_PATH = ROOT / "docs" / "harbor-integration-runbook.md"
PACKAGE_PATHS = (
    ROOT / "authzbench_harbor" / "__init__.py",
    ROOT / "authzbench_harbor" / "adapter.py",
    ROOT / "authzbench_harbor" / "cli.py",
    ROOT / "authzbench_harbor" / "dataset_builder.py",
    ROOT / "authzbench_harbor" / "redaction.py",
    ROOT / "authzbench_harbor" / "schemas.py",
    ROOT / "authzbench_harbor" / "scorer_bridge.py",
)
REQUIRED_FALSE_EXTERNAL_CLAIMS = {
    "external_review_complete",
    "harbor_acceptance_claimed",
    "harbor_endorsement_claimed",
    "hosted_execution_verified",
    "hosted_public_leaderboard_claimed",
    "kaggle_acceptance_claimed",
    "platform_acceptance_claimed",
    "ready_for_harbor_platform_review",
    "saas_provider_validation_complete",
}
REQUIRED_PUBLIC_SOURCES = {
    "https://www.harborframework.com/docs/datasets/adapters",
    "https://www.harborframework.com/docs/datasets/publishing",
    "https://www.harborframework.com/docs/datasets",
    "https://www.harborframework.com/docs/run-jobs/run-evals",
}
REQUIRED_BLOCKERS = {
    "harbor_adapter_package",
    "adapter_metadata_json",
    "parity_experiment_json",
    "adapter_readme_parity_table",
    "local_harbor_run",
    "harbor_review_or_publish_path",
}
REQUIRED_HELPERS = {
    "public_skeleton_builder",
    "public_skeleton_validator",
    "adapter_contract_validator",
    "adapter_metadata_parity_templates",
    "local_execution_preflight",
}
DISALLOWED_TEXT = (
    "calendar." + "google.com",
    "appointments/" + "schedules",
    "accepted" + " by",
    "endorsed" + " by",
)
PRIVATE_MARKERS = (
    "private route:",
    "private seed:",
    "raw private output",
    "credential:",
    "oracle:",
)
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")
ALLOWED_ABSOLUTE_PREFIXES = ("/logs/artifacts/", "/logs/verifier/")
ALLOWED_ABSOLUTE_PATHS = {"/logs/artifacts", "/logs/verifier"}


def _load_json(path: Path) -> dict[str, Any]:
    data = load_strict_json(path)
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
        for marker in DISALLOWED_TEXT:
            if marker in lower:
                errors.append(f"disallowed overclaim/private marker: {marker}")
        for marker in PRIVATE_MARKERS:
            if marker in lower:
                errors.append(f"sensitive private detail marker is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(value):
            if match not in ALLOWED_ABSOLUTE_PATHS and not any(match.startswith(prefix) for prefix in ALLOWED_ABSOLUTE_PREFIXES):
                errors.append(f"local absolute path is not allowed: {match}")
    return errors


def _derive_readiness_statuses() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Derive readiness rows from current files instead of trusting row prose."""

    evidence_errors: dict[str, list[str]] = {}
    package_missing = [
        path.relative_to(ROOT).as_posix()
        for path in PACKAGE_PATHS
        if not path.is_file()
    ]
    package_status = "complete" if not package_missing else "blocked"
    if package_missing:
        evidence_errors["harbor_adapter_package"] = [
            "missing package paths: " + ", ".join(package_missing)
        ]

    metadata_result = validate_adapter_metadata(METADATA_PATH)
    metadata_status = "complete" if metadata_result["passed"] else "blocked"
    if not metadata_result["passed"]:
        evidence_errors["adapter_metadata_json"] = list(
            metadata_result.get("errors") or []
        )

    parity_result = validate_parity_experiment(PARITY_PATH)
    parity_status = "blocked"
    if parity_result["passed"]:
        if parity_result.get("evidence_status") == "current":
            try:
                parity_data = _load_json(PARITY_PATH)
            except Exception as exc:
                evidence_errors["parity_experiment_json"] = [str(exc)]
            else:
                source_sha = parity_data.get("benchmark_source_sha")
                if (
                    isinstance(source_sha, str)
                    and re.fullmatch(r"[0-9a-f]{40}", source_sha)
                    and parity_data.get("current_claim_eligible") is True
                ):
                    parity_status = "complete"
                else:
                    parity_status = "blocked"
                    evidence_errors["parity_experiment_json"] = [
                        "current parity evidence requires an exact 40-character "
                        "benchmark_source_sha and current_claim_eligible=true"
                    ]
        elif parity_result.get("evidence_status") in {
            "historical_backcompat",
            "historical_stale",
        }:
            parity_status = "historical_stale"
    else:
        evidence_errors["parity_experiment_json"] = list(
            parity_result.get("errors") or []
        )

    runbook_status = "blocked"
    if RUNBOOK_PATH.is_file():
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
        if (
            "historical six-task" in runbook.lower()
            and "planned_unsupported" in runbook
        ):
            runbook_status = (
                "historical_stale"
                if parity_status == "historical_stale"
                else "complete"
                if parity_status == "complete"
                else "blocked"
            )
        else:
            evidence_errors["adapter_readme_parity_table"] = [
                "runbook must label the six-task table historical and the live "
                "HTTP lane planned_unsupported"
            ]
    else:
        evidence_errors["adapter_readme_parity_table"] = ["runbook is missing"]

    compatibility_result = validate_harbor_compatibility_state()
    local_smoke_result = validate_harbor_local_evidence(LOCAL_SMOKE_PATH)
    if (
        compatibility_result["passed"]
        and compatibility_result["active_compatibility_verified"]
    ):
        local_run_status = "complete"
    elif compatibility_result["passed"] and local_smoke_result["passed"]:
        local_run_status = "historical_stale"
    else:
        local_run_status = "blocked"
        combined_errors = [
            *compatibility_result.get("errors", []),
            *local_smoke_result.get("errors", []),
        ]
        evidence_errors["local_harbor_run"] = combined_errors or [
            "local Harbor evidence did not validate"
        ]

    statuses = {
        "harbor_adapter_package": package_status,
        "adapter_metadata_json": metadata_status,
        "parity_experiment_json": parity_status,
        "adapter_readme_parity_table": runbook_status,
        "local_harbor_run": local_run_status,
        "harbor_review_or_publish_path": "blocked_external",
    }
    return statuses, evidence_errors


def validate_harbor_adapter_blockers(path: Path = BLOCKERS_PATH) -> dict[str, Any]:
    errors: list[str] = []
    try:
        data = _load_json(path)
    except Exception as exc:
        return {"blocked_item_count": 0, "errors": [str(exc)], "passed": False, "repo_side_helper_count": 0}

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("evidence_status") != EVIDENCE_STATUS:
        errors.append(f"evidence_status must be {EVIDENCE_STATUS}")
    boundary = str(data.get("public_claim_boundary", ""))
    if (
        "not Harbor platform acceptance" not in boundary
        or "not hosted public leaderboard operation" not in boundary
        or "not external review completion" not in boundary
    ):
        errors.append(
            "public_claim_boundary must reject platform acceptance, hosted "
            "operation, and external review claims"
        )
    if data.get("no_tools_adapter_status") != "implemented_local":
        errors.append("no_tools_adapter_status must be implemented_local")
    if data.get("live_http_tool_agent_status") != "planned_unsupported":
        errors.append(
            "live_http_tool_agent_status must be planned_unsupported"
        )
    for field in sorted(REQUIRED_FALSE_EXTERNAL_CLAIMS):
        if data.get(field) is not False:
            errors.append(f"{field} must be explicitly false")

    sources = set(data.get("public_sources") or [])
    missing_sources = sorted(REQUIRED_PUBLIC_SOURCES - sources)
    if missing_sources:
        errors.append("public_sources missing: " + ", ".join(missing_sources))

    helpers = data.get("repo_side_progress")
    if not isinstance(helpers, list):
        errors.append("repo_side_progress must be a list")
        helpers = []
    helper_items = {item.get("item") for item in helpers if isinstance(item, dict)}
    missing_helpers = sorted(REQUIRED_HELPERS - helper_items)
    if missing_helpers:
        errors.append("repo_side_progress missing: " + ", ".join(missing_helpers))
    for helper in helpers:
        if not isinstance(helper, dict):
            errors.append("repo_side_progress entries must be objects")
            continue
        if helper.get("status") not in {
            "partial_repo_side_helper",
            "partial_repo_side_smoke",
            "historical_repo_side_smoke",
        }:
            errors.append(
                f"{helper.get('item')}: status must be partial_repo_side_helper, "
                "partial_repo_side_smoke, or historical_repo_side_smoke"
            )
        if "does not" not in str(helper.get("claim_boundary", "")):
            errors.append(f"{helper.get('item')}: claim_boundary must state what the helper does not prove")

    blockers = data.get("required_before_adapter_ready")
    if not isinstance(blockers, list):
        errors.append("required_before_adapter_ready must be a list")
        blockers = []
    blocker_items = {item.get("item") for item in blockers if isinstance(item, dict)}
    missing_blockers = sorted(REQUIRED_BLOCKERS - blocker_items)
    if missing_blockers:
        errors.append("required_before_adapter_ready missing: " + ", ".join(missing_blockers))
    declared_statuses: dict[str, str] = {}
    for blocker in blockers:
        if not isinstance(blocker, dict):
            errors.append("required_before_adapter_ready entries must be objects")
            continue
        item = blocker.get("item")
        VALID_BLOCKER_STATUSES = {
            "blocked",
            "blocked_external",
            "historical_stale",
            "partial_repo_side_smoke",
            "complete",
        }
        if blocker.get("status") not in VALID_BLOCKER_STATUSES:
            errors.append(f"{item}: status must be one of: {', '.join(sorted(VALID_BLOCKER_STATUSES))}")
        if isinstance(item, str) and isinstance(blocker.get("status"), str):
            declared_statuses[item] = blocker["status"]
        if not isinstance(blocker.get("required_evidence"), list) or not blocker["required_evidence"]:
            errors.append(f"{item}: required_evidence must be a non-empty list")
        # missing_input is required for non-complete blockers
        if blocker.get("status") != "complete":
            if not isinstance(blocker.get("missing_input"), str) or not blocker["missing_input"].strip():
                errors.append(f"{item}: missing_input is required")

    derived_statuses, evidence_errors = _derive_readiness_statuses()
    for item, derived_status in derived_statuses.items():
        declared_status = declared_statuses.get(item)
        if declared_status != derived_status:
            errors.append(
                f"{item}: declared status {declared_status!r} does not match "
                f"derived status {derived_status!r}"
            )

    boundaries = data.get("hard_public_boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 4:
        errors.append("hard_public_boundaries must list concrete public claim boundaries")

    errors.extend(_public_safety_errors(data))
    return {
        "blocked_item_count": len(blocker_items),
        "errors": sorted(set(errors)),
        "derived_statuses": derived_statuses,
        "evidence_errors": evidence_errors,
        "passed": not errors,
        "repo_side_helper_count": len(helper_items),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-safe Harbor adapter readiness blocker artifact.")
    parser.add_argument("--path", type=Path, default=BLOCKERS_PATH)
    args = parser.parse_args()
    result = validate_harbor_adapter_blockers(args.path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
