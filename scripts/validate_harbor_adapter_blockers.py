from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BLOCKERS_PATH = ROOT / "artifact" / "harbor-adapter-readiness-blockers.json"
SCHEMA_VERSION = "harbor-adapter-readiness-blockers-v1"
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
ALLOWED_ABSOLUTE_PREFIXES = ("/logs/artifacts/",)
ALLOWED_ABSOLUTE_PATHS = {"/logs/artifacts"}


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


def validate_harbor_adapter_blockers(path: Path = BLOCKERS_PATH) -> dict[str, Any]:
    errors: list[str] = []
    try:
        data = _load_json(path)
    except Exception as exc:
        return {"blocked_item_count": 0, "errors": [str(exc)], "passed": False, "repo_side_helper_count": 0}

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("evidence_status") != "implementation_blockers":
        errors.append("evidence_status must be implementation_blockers")
    boundary = str(data.get("public_claim_boundary", ""))
    if "not Harbor adapter readiness evidence" not in boundary or "not parity evidence" not in boundary:
        errors.append("public_claim_boundary must reject adapter readiness and parity evidence claims")

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
        if helper.get("status") != "partial_repo_side_helper":
            errors.append(f"{helper.get('item')}: status must be partial_repo_side_helper")
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
    for blocker in blockers:
        if not isinstance(blocker, dict):
            errors.append("required_before_adapter_ready entries must be objects")
            continue
        if blocker.get("status") != "blocked":
            errors.append(f"{blocker.get('item')}: status must be blocked")
        if not isinstance(blocker.get("required_evidence"), list) or not blocker["required_evidence"]:
            errors.append(f"{blocker.get('item')}: required_evidence must be a non-empty list")
        if not isinstance(blocker.get("missing_input"), str) or not blocker["missing_input"].strip():
            errors.append(f"{blocker.get('item')}: missing_input is required")

    boundaries = data.get("hard_public_boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 4:
        errors.append("hard_public_boundaries must list concrete public claim boundaries")

    errors.extend(_public_safety_errors(data))
    return {
        "blocked_item_count": len(blocker_items),
        "errors": sorted(set(errors)),
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
