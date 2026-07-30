"""Validate Harbor adapter metadata artifact.

Checks that the adapter metadata file has the required fields and
does not contain invalid claim wording or private artifacts.

Usage:
    python3 scripts/validate_harbor_adapter_metadata.py
    python3 scripts/validate_harbor_adapter_metadata.py \\
        --metadata artifact/harbor-adapter-metadata.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench_harbor.redaction import scan_for_violations
from authzbench_harbor.schemas import ADAPTER_METADATA_SCHEMA_VERSION

TEMPLATE_SCHEMA_VERSION = "harbor-adapter-metadata-template-v1"
REQUIRED_FIELDS_FOR_REAL_METADATA = [
    "schema_version",
    "evidence_status",
    "public_claim_boundary",
    "adapter_version",
    "adapter_name",
    "package_entrypoint",
    "supported_lanes",
    "planned_unsupported_lanes",
    "artifact_policy",
]
IMPLEMENTED_LANES = {"no_tools"}
PLANNED_UNSUPPORTED_LANES = {"live_http_tool_agent"}
REQUIRED_FALSE_EXTERNAL_CLAIMS = {
    "external_review_complete",
    "harbor_acceptance_claimed",
    "harbor_endorsement_claimed",
    "hosted_execution_verified",
    "hosted_public_leaderboard_claimed",
    "kaggle_acceptance_claimed",
    "platform_acceptance_claimed",
    "saas_provider_validation_complete",
}
FORBIDDEN_CLAIM_PATTERNS = [
    "harbor_accepted",
    "platform_accepted",
    "kaggle_accepted",
    "hosted_leaderboard_ready",
    "externally_reviewed",
    "saas_provider_validated",
]


def validate_adapter_metadata(metadata_path: Path) -> dict:
    errors = []
    warnings = []

    if not metadata_path.is_file():
        return {
            "passed": False,
            "errors": [f"metadata file not found: {metadata_path}"],
            "warnings": [],
            "is_template": False,
        }

    try:
        metadata = load_json(metadata_path)
    except (OSError, ValueError) as exc:
        return {
            "passed": False,
            "errors": [f"metadata file is not valid JSON: {exc}"],
            "warnings": [],
            "is_template": False,
        }
    if not isinstance(metadata, dict):
        return {
            "passed": False,
            "errors": ["metadata JSON must be an object"],
            "warnings": [],
            "is_template": False,
        }

    schema_version = metadata.get("schema_version", "")
    is_template = schema_version == TEMPLATE_SCHEMA_VERSION or metadata.get("template_only") is True

    if is_template:
        return {
            "passed": True,
            "is_template": True,
            "warnings": ["metadata is a template; real adapter metadata has not been generated yet"],
            "errors": [],
        }

    for field in REQUIRED_FIELDS_FOR_REAL_METADATA:
        if field not in metadata:
            errors.append(f"missing required field: {field}")

    if schema_version != ADAPTER_METADATA_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {ADAPTER_METADATA_SCHEMA_VERSION} for real metadata"
        )
    if metadata.get("evidence_status") != "adapter_metadata_complete":
        errors.append("evidence_status must be adapter_metadata_complete")
    boundary = str(metadata.get("public_claim_boundary", ""))
    for phrase in (
        "does not claim Harbor platform acceptance",
        "hosted leaderboard",
        "external review",
    ):
        if phrase not in boundary:
            errors.append(f"public_claim_boundary must include: {phrase}")

    supported_lanes = metadata.get("supported_lanes")
    if not isinstance(supported_lanes, list) or set(supported_lanes) != IMPLEMENTED_LANES:
        errors.append("supported_lanes must contain only the implemented no_tools lane")

    planned_rows = metadata.get("planned_unsupported_lanes")
    if not isinstance(planned_rows, list):
        errors.append("planned_unsupported_lanes must be a list")
        planned_rows = []
    planned_names: set[str] = set()
    for index, row in enumerate(planned_rows):
        if not isinstance(row, dict):
            errors.append(f"planned_unsupported_lanes[{index}] must be an object")
            continue
        name = row.get("name")
        if isinstance(name, str):
            planned_names.add(name)
        if row.get("status") != "planned_unsupported":
            errors.append(
                f"planned_unsupported_lanes[{index}].status must be planned_unsupported"
            )
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"planned_unsupported_lanes[{index}].reason must be a non-empty string"
            )
    if planned_names != PLANNED_UNSUPPORTED_LANES:
        errors.append(
            "planned_unsupported_lanes must contain exactly live_http_tool_agent"
        )

    artifact_policy = metadata.get("artifact_policy")
    if not isinstance(artifact_policy, dict):
        errors.append("artifact_policy must be an object")
    else:
        if artifact_policy.get("public_outputs_redacted") is not True:
            errors.append("artifact_policy.public_outputs_redacted must be true")
        if artifact_policy.get("private_manifests_tracked") is not False:
            errors.append("artifact_policy.private_manifests_tracked must be false")

    for field in sorted(REQUIRED_FALSE_EXTERNAL_CLAIMS):
        if metadata.get(field) is not False:
            errors.append(f"{field} must be explicitly false in local adapter metadata")

    text = json.dumps(metadata).lower()
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        if f'"{pattern}": true' in text or f'"{pattern}":true' in text:
            errors.append(f"forbidden claim found: {pattern} must not be true in public adapter metadata")

    violations = scan_for_violations(metadata, "adapter metadata")
    errors.extend(violations)

    return {
        "passed": len(errors) == 0,
        "is_template": False,
        "schema_version": schema_version,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Harbor adapter metadata")
    parser.add_argument(
        "--metadata",
        default="artifact/harbor-adapter-metadata.json",
        help="Path to Harbor adapter metadata JSON",
    )
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    if not metadata_path.is_file():
        template_path = ROOT / "artifact" / "harbor-adapter-metadata.template.json"
        if template_path.is_file():
            print(f"NOTE: {metadata_path} not found; falling back to template {template_path}", file=sys.stderr)
            metadata_path = template_path
        else:
            print(f"ERROR: {metadata_path} not found", file=sys.stderr)
            return 1

    result = validate_adapter_metadata(metadata_path)
    print(dump_json(result))
    if not result["passed"]:
        print(f"\nValidation FAILED: {len(result['errors'])} error(s)", file=sys.stderr)
        for err in result["errors"]:
            print(f"  ERROR: {err}", file=sys.stderr)
        return 1
    if result.get("is_template"):
        print("Template-only metadata: validation skipped (template present, real metadata not yet generated)", file=sys.stderr)
    else:
        print(f"Validation passed: {metadata_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
