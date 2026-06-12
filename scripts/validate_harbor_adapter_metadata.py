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

from authzbench.core import dump_json
from authzbench_harbor.redaction import scan_for_violations
from authzbench_harbor.schemas import ADAPTER_METADATA_SCHEMA_VERSION

TEMPLATE_SCHEMA_VERSION = "harbor-adapter-metadata-template-v1"
REQUIRED_FIELDS_FOR_REAL_METADATA = [
    "schema_version",
    "evidence_status",
    "public_claim_boundary",
    "adapter_version",
]
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
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "passed": False,
            "errors": [f"metadata file is not valid JSON: {exc}"],
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
