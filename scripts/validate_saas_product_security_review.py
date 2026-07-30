"""Validate the separate SaaS product-security realism review registry.

The default mode accepts a well-formed pending registry without claiming that
the review is complete. ``--require-complete`` is the strict external-evidence
gate and fails until real, source-bound review records cover every benchmark app
and every declared vulnerability family with no unresolved blocking issue.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from authzbench.core import load_json

try:
    from scripts.validate_external_review_summary import (
        _is_placeholder,
        _validate_json_schema_record,
        _value_has_private_marker,
    )
except ModuleNotFoundError:
    from validate_external_review_summary import (
        _is_placeholder,
        _validate_json_schema_record,
        _value_has_private_marker,
    )


REGISTRY_PATH = ROOT / "docs/reviews/saas-product-security-review-registry.json"
PACKET_PATH = "docs/reviews/saas-provider-review-packet.md"
SCHEMA_PATH = "docs/reviews/schemas/saas-product-security-review.schema.json"
VALID_STATUSES = {"pending", "in_progress", "complete"}
VALID_DISPOSITIONS = {"accept", "accept_with_minor_changes", "reject"}
ACCEPTED_DISPOSITIONS = {"accept", "accept_with_minor_changes"}
REGISTRY_ALLOWED_FIELDS = {
    "schema_version",
    "claim_boundary",
    "packet",
    "schema",
    "review_status",
    "reviewer_id",
    "review_date",
    "reviewed_commit_sha",
    "overall_disposition",
    "blocking_issues",
    "nonblocking_issues",
    "records",
    "blocker",
    "next_action",
}
REQUIRED_APPS = {
    "project_mgmt",
    "billing",
    "support",
    "file_sharing",
    "api_tokens",
    "audit_settings",
}
REQUIRED_FAMILIES = {
    "bola",
    "bfla",
    "cross-tenant",
    "role-bypass",
    "token-scope",
    "entitlement",
    "share-link",
    "reassignment",
    "admin-exposure",
}


def _git_commit_exists(commit_sha: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _concrete_text(value: Any) -> bool:
    return isinstance(value, str) and not _is_placeholder(value)


def _load_object(path: Path, label: str, findings: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        findings.append(f"missing {label}: {path.relative_to(ROOT)}")
        return None
    try:
        payload = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(f"{label} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        findings.append(f"{label} root must be an object")
        return None
    return payload


def validate(require_complete: bool = False) -> dict[str, Any]:
    findings: list[str] = []
    registry = _load_object(REGISTRY_PATH, "SaaS product-security registry", findings)
    schema = _load_object(ROOT / SCHEMA_PATH, "SaaS product-security schema", findings)
    if registry is None or schema is None:
        return {
            "schema_version": "saas-product-security-review-validation-v1",
            "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
            "findings": findings,
            "passed": False,
            "saas_product_security_validation_complete": False,
        }

    if registry.get("schema_version") != "saas-product-security-review-registry-v1":
        findings.append(
            "registry schema_version must be 'saas-product-security-review-registry-v1'"
        )
    extra_fields = sorted(set(registry) - REGISTRY_ALLOWED_FIELDS)
    if extra_fields:
        findings.append(f"unexpected registry fields: {', '.join(extra_fields)}")
    if _value_has_private_marker(registry):
        findings.append("registry contains a private-detail marker")
    if registry.get("packet") != PACKET_PATH:
        findings.append(f"packet must be {PACKET_PATH!r}")
    if registry.get("schema") != SCHEMA_PATH:
        findings.append(f"schema must be {SCHEMA_PATH!r}")
    if not (ROOT / PACKET_PATH).is_file():
        findings.append("referenced SaaS product-security review packet does not exist")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        findings.append("review schema must be a closed object schema")
    if not _concrete_text(registry.get("claim_boundary")):
        findings.append("claim_boundary must be concrete public-safe text")
    elif _value_has_private_marker(registry["claim_boundary"]):
        findings.append("claim_boundary contains a private-detail marker")

    status = registry.get("review_status")
    if status not in VALID_STATUSES:
        findings.append(f"review_status must be one of {sorted(VALID_STATUSES)}")
    if require_complete and status != "complete":
        findings.append("review_status is not 'complete' under --require-complete")

    for field in ("blocking_issues", "nonblocking_issues", "records"):
        if not isinstance(registry.get(field), list):
            findings.append(f"{field} must be a list")
    for field in ("blocking_issues", "nonblocking_issues"):
        issues = registry.get(field)
        if isinstance(issues, list) and any(
            not _concrete_text(item) or _value_has_private_marker(item)
            for item in issues
        ):
            findings.append(f"{field} must contain concrete public-safe strings")
    records = registry.get("records")
    if not isinstance(records, list):
        records = []

    seen_pairs: set[tuple[str, str]] = set()
    observed_apps: set[str] = set()
    observed_families: set[str] = set()
    for index, record in enumerate(records):
        label = f"records[{index}]"
        findings.extend(_validate_json_schema_record(record, schema, label))
        if not isinstance(record, dict):
            continue
        app_id = record.get("app_id")
        family = record.get("vulnerability_family")
        if isinstance(app_id, str):
            observed_apps.add(app_id)
        if isinstance(family, str):
            observed_families.add(family)
        if isinstance(app_id, str) and isinstance(family, str):
            pair = (app_id, family)
            if pair in seen_pairs:
                findings.append(f"{label}: duplicate app/family review record")
            seen_pairs.add(pair)
        for field in ("reviewer_role", "review_date", "reviewed_commit_sha"):
            lane_field = "reviewer_role" if field == "reviewer_role" else field
            expected = (
                "SaaS product-security reviewer"
                if field == "reviewer_role"
                else registry.get(lane_field)
            )
            if record.get(field) != expected:
                findings.append(f"{label}.{field}: must match the registry-level value")
        if status == "complete" and record.get("blocking_issue") is True:
            findings.append(f"{label}: unresolved blocking issue is incompatible with complete status")

    if status == "pending":
        if records:
            findings.append("pending registry must not contain review records")
        if not _concrete_text(registry.get("blocker")):
            findings.append("pending registry requires a concrete blocker")
        if not _concrete_text(registry.get("next_action")):
            findings.append("pending registry requires a concrete next_action")

    if status == "complete":
        if _is_placeholder(registry.get("reviewer_id")):
            findings.append("reviewer_id is required under complete status")
        review_date = registry.get("review_date")
        if not isinstance(review_date, str) or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
            review_date,
        ) is None:
            findings.append("review_date must be YYYY-MM-DD under complete status")
        else:
            try:
                if date.fromisoformat(review_date) > date.today():
                    findings.append("review_date cannot be in the future")
            except ValueError:
                findings.append("review_date is not a real calendar date")
        reviewed_commit_sha = registry.get("reviewed_commit_sha")
        if not isinstance(reviewed_commit_sha, str) or re.fullmatch(
            r"[0-9a-f]{40}",
            reviewed_commit_sha,
        ) is None:
            findings.append("reviewed_commit_sha must be a 40-character lowercase Git SHA")
        elif not _git_commit_exists(reviewed_commit_sha):
            findings.append("reviewed_commit_sha must reference an existing commit")
        if registry.get("overall_disposition") not in VALID_DISPOSITIONS:
            findings.append(
                f"overall_disposition must be one of {sorted(VALID_DISPOSITIONS)} under complete status"
            )
        elif require_complete and registry.get("overall_disposition") not in ACCEPTED_DISPOSITIONS:
            findings.append("overall_disposition must be accepted under --require-complete")
        if registry.get("blocking_issues"):
            findings.append("blocking_issues must be empty under complete status")
        if not records:
            findings.append("complete review requires non-empty records")
        missing_apps = sorted(REQUIRED_APPS - observed_apps)
        missing_families = sorted(REQUIRED_FAMILIES - observed_families)
        if missing_apps:
            findings.append(f"complete review is missing app coverage: {', '.join(missing_apps)}")
        if missing_families:
            findings.append(
                "complete review is missing vulnerability-family coverage: "
                + ", ".join(missing_families)
            )

    complete = (
        status == "complete"
        and registry.get("overall_disposition") in ACCEPTED_DISPOSITIONS
        and not findings
    )
    return {
        "schema_version": "saas-product-security-review-validation-v1",
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "record_count": len(records),
        "observed_apps": sorted(observed_apps),
        "observed_vulnerability_families": sorted(observed_families),
        "findings": findings,
        "passed": not findings,
        "saas_product_security_validation_complete": complete,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail until real source-bound review records cover every required app and family.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full JSON result.")
    args = parser.parse_args()

    result = validate(require_complete=args.require_complete)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["passed"]:
        print(
            "SaaS product-security review registry: ok; "
            f"validation_complete={result['saas_product_security_validation_complete']}"
        )
    else:
        print(
            f"SaaS product-security review registry: FAILED ({len(result['findings'])} findings)",
            file=sys.stderr,
        )
        for finding in result["findings"]:
            print(f"  - {finding}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
