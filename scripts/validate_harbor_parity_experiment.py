"""Validate a Harbor parity experiment artifact.

Checks that the parity experiment file has the required schema and does not
claim parity_verified without real Harbor execution evidence.

Usage:
    python3 scripts/validate_harbor_parity_experiment.py
    python3 scripts/validate_harbor_parity_experiment.py \\
        --parity-file artifact/harbor-parity-experiment.json
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
from authzbench_harbor.schemas import PARITY_EXPERIMENT_SCHEMA_VERSION

TEMPLATE_SCHEMA_VERSION = "harbor-parity-experiment-template-v1"
REQUIRED_FIELDS = [
    "schema_version",
    "evidence_status",
    "public_claim_boundary",
    "parity_verified",
]


def validate_parity_experiment(parity_path: Path) -> dict:
    errors = []
    warnings = []

    if not parity_path.is_file():
        return {
            "passed": False,
            "errors": [f"parity experiment file not found: {parity_path}"],
            "warnings": [],
            "is_template": False,
        }

    try:
        data = json.loads(parity_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "passed": False,
            "errors": [f"parity experiment file is not valid JSON: {exc}"],
            "warnings": [],
            "is_template": False,
        }

    schema_version = data.get("schema_version", "")
    is_template = schema_version == TEMPLATE_SCHEMA_VERSION or data.get("template_only") is True

    if is_template:
        return {
            "passed": True,
            "is_template": True,
            "warnings": ["parity experiment is a template; real experiment evidence not yet generated"],
            "errors": [],
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")

    if data.get("parity_verified") is True:
        harbor_results = data.get("harbor_results")
        if not isinstance(harbor_results, dict):
            errors.append(
                "parity_verified is true but harbor_results is missing or not a dict; "
                "cannot claim parity without real Harbor run evidence"
            )
        elif not harbor_results.get("harbor_run_id"):
            errors.append(
                "parity_verified is true but harbor_results.harbor_run_id is missing; "
                "cannot claim parity without a real Harbor run id"
            )
        native_results = data.get("native_authzbench_results")
        if not isinstance(native_results, dict) or not native_results:
            errors.append(
                "parity_verified is true but native_authzbench_results is missing or empty"
            )

    if data.get("raw_harbor_jobs_tracked") is True:
        errors.append("raw_harbor_jobs_tracked must be false; raw Harbor job directories must not be tracked")
    if data.get("private_artifacts_tracked") is True:
        errors.append("private_artifacts_tracked must be false")

    violations = scan_for_violations(data, "parity experiment")
    errors.extend(violations)

    return {
        "passed": len(errors) == 0,
        "is_template": False,
        "schema_version": schema_version,
        "parity_verified": data.get("parity_verified"),
        "evidence_status": data.get("evidence_status"),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Harbor parity experiment artifact")
    parser.add_argument(
        "--parity-file",
        default="artifact/harbor-parity-experiment.json",
        help="Path to parity experiment JSON",
    )
    args = parser.parse_args()

    parity_path = Path(args.parity_file)
    if not parity_path.is_file():
        template_path = ROOT / "artifact" / "harbor-parity-experiment.template.json"
        if template_path.is_file():
            print(f"NOTE: {parity_path} not found; falling back to template {template_path}", file=sys.stderr)
            parity_path = template_path
        else:
            print(f"ERROR: {parity_path} not found", file=sys.stderr)
            return 1

    result = validate_parity_experiment(parity_path)
    print(dump_json(result))
    if not result["passed"]:
        print(f"\nValidation FAILED: {len(result['errors'])} error(s)", file=sys.stderr)
        for err in result["errors"]:
            print(f"  ERROR: {err}", file=sys.stderr)
        return 1
    if result.get("is_template"):
        print("Template-only parity experiment: validation skipped", file=sys.stderr)
    else:
        print(f"Validation passed: {parity_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
