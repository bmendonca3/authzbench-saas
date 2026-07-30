#!/usr/bin/env python3
"""Validate the public/private AppSec review storage boundary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from authzbench.core import load_json

PUBLIC_SCHEMA = Path("docs/reviews/schemas/appsec-review.schema.json")
PRIVATE_SCHEMA = Path("docs/reviews/schemas/private-appsec-review.schema.json")
AGGREGATE_SCHEMA = Path("docs/reviews/schemas/private-review-aggregate.schema.json")
EXTERNAL_REGISTRY = Path("docs/reviews/external-review-registry.json")
CONTROLLED_PREFIX = "private-review-responses/"
FORBIDDEN_AGGREGATE_PROPERTIES = {
    "pack_id",
    "task_id",
    "task_ids",
    "seed",
    "seeds",
    "route",
    "routes",
    "oracle",
    "oracles",
    "body",
    "bodies",
    "manifest_path",
    "manifest_paths",
    "raw_result",
    "raw_results",
    "diagnostic_detail",
    "diagnostic_details",
    "comments_by_task",
}


def _load_object(root: Path, relative: Path, errors: list[str]) -> dict[str, Any]:
    path = root / relative
    try:
        value = load_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"{relative}: cannot load JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{relative}: root must be a JSON object")
        return {}
    return value


def validate_contract(root: Path = ROOT, *, check_git: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    public_schema = _load_object(root, PUBLIC_SCHEMA, errors)
    private_schema = _load_object(root, PRIVATE_SCHEMA, errors)
    aggregate_schema = _load_object(root, AGGREGATE_SCHEMA, errors)
    registry = _load_object(root, EXTERNAL_REGISTRY, errors)

    public_pack = public_schema.get("properties", {}).get("pack_id", {})
    if public_pack.get("enum") != ["public"]:
        errors.append("public AppSec schema must accept only pack_id='public'")

    private_required = set(private_schema.get("required", []))
    for field in {
        "reviewed_commit_sha",
        "pack_id",
        "task_id",
        "blocking_issue",
        "leakage_concern",
    }:
        if field not in private_required:
            errors.append(f"private AppSec schema must require {field}")
    if private_schema.get("additionalProperties") is not False:
        errors.append("private AppSec schema must set additionalProperties=false")

    aggregate_properties = aggregate_schema.get("properties", {})
    leaked_properties = sorted(FORBIDDEN_AGGREGATE_PROPERTIES & set(aggregate_properties))
    if leaked_properties:
        errors.append(
            "aggregate schema exposes forbidden private properties: "
            + ", ".join(leaked_properties)
        )
    if aggregate_schema.get("additionalProperties") is not False:
        errors.append("private aggregate schema must set additionalProperties=false")
    aggregate_required = set(aggregate_schema.get("required", []))
    for field in {
        "public_safe",
        "reviewed_commit_sha",
        "reviewed_pack_role",
        "reviewed_task_count",
        "rating_distributions",
        "blocking_issue_count",
        "leakage_concern_count",
        "overall_disposition",
        "claim_boundary_impact",
    }:
        if field not in aggregate_required:
            errors.append(f"private aggregate schema must require {field}")

    lanes = registry.get("lanes")
    if not isinstance(lanes, list):
        errors.append("external review registry lanes must be a list")
        lanes = []
    appsec_lanes = [
        lane for lane in lanes if isinstance(lane, dict) and lane.get("lane") == "appsec"
    ]
    if len(appsec_lanes) != 1:
        errors.append("external review registry must contain exactly one appsec lane")
    else:
        lane = appsec_lanes[0]
        if lane.get("schema") != str(PUBLIC_SCHEMA):
            errors.append("public appsec lane must reference only the public AppSec schema")
        records = lane.get("per_task_records")
        if not isinstance(records, list):
            errors.append("public appsec per_task_records must be a list")
        else:
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    errors.append(f"public appsec record {index} must be an object")
                elif record.get("pack_id") != "public":
                    errors.append(
                        f"public appsec record {index} must use pack_id='public'"
                    )

    gitignore_path = root / ".gitignore"
    try:
        gitignore = gitignore_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f".gitignore: cannot read: {exc}")
        gitignore = []
    if CONTROLLED_PREFIX not in {line.strip() for line in gitignore}:
        errors.append(f".gitignore must ignore {CONTROLLED_PREFIX}")

    if check_git:
        try:
            result = subprocess.run(
                ["git", "ls-files", "--", CONTROLLED_PREFIX],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"cannot verify controlled review path with Git: {exc}")
        else:
            if result.returncode != 0:
                errors.append(
                    "git ls-files failed for controlled review path: "
                    + (result.stderr.strip() or "no diagnostic")
                )
            elif result.stdout.strip():
                errors.append(
                    f"controlled private review responses are tracked: {result.stdout.strip()}"
                )

    return {
        "schema_version": "private-review-contract-validation-v1",
        "passed": not errors,
        "errors": errors,
        "public_appsec_schema": str(PUBLIC_SCHEMA),
        "private_controlled_schema": str(PRIVATE_SCHEMA),
        "public_aggregate_schema": str(AGGREGATE_SCHEMA),
        "controlled_response_prefix": CONTROLLED_PREFIX,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_contract(args.root.resolve())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["passed"]:
        print(
            "private review contract: PASS "
            "(public records, controlled private records, aggregate projection separated)"
        )
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
