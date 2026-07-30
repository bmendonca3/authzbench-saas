"""External review summary gate.

The plan section 8.3 requires a CI-failable gate that asserts:

  * v2 external validation requires all three review lanes complete.
  * Each lane must include real reviewer metadata (no placeholder
    reviews).
  * Blocking issues must be resolved or explicitly accepted.
  * Public summary must not reveal private task internals.

This script consumes ``docs/reviews/external-review-registry.json`` and
emits a per-lane pass / fail + the project-level disposition. It is
the gate the readiness fixture points at; it is intentionally a
report (not a CI gate) so a pending external review does not break
the v1.0-internal cut.

Usage:
    python3 scripts/validate_external_review_summary.py
    python3 scripts/validate_external_review_summary.py --require-v2-complete
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

REGISTRY_PATH = ROOT / "docs/reviews/external-review-registry.json"
SUMMARY_PATH = ROOT / "docs/reviews/external-review-summary.md"

VALID_DISPOSITIONS = {"accept", "accept_with_minor_changes", "reject"}
ACCEPTED_DISPOSITIONS = {"accept", "accept_with_minor_changes"}
VALID_STATUSES = {"pending", "in_progress", "complete"}
REQUIRED_LANE_IDS = ("appsec", "benchmark_evals", "agent_tooling")
EXPECTED_PUBLIC_TASK_COUNT = 63
REGISTRY_ALLOWED_FIELDS = {"schema_version", "description", "lanes"}
LANE_ALLOWED_FIELDS = {
    "lane",
    "reviewer_role",
    "packet",
    "schema",
    "review_status",
    "reviewer_id",
    "review_date",
    "reviewed_commit_sha",
    "overall_disposition",
    "blocking_issues",
    "nonblocking_issues",
    "per_task_records",
}
LANE_CONTRACTS = {
    "appsec": {
        "reviewer_role": "AppSec reviewer",
        "packet": "docs/reviews/appsec-review-packet.md",
        "schema": "docs/reviews/schemas/appsec-review.schema.json",
    },
    "benchmark_evals": {
        "reviewer_role": "Benchmark / evals reviewer",
        "packet": "docs/reviews/benchmark-methodology-review-packet.md",
        "schema": "docs/reviews/schemas/evals-review.schema.json",
    },
    "agent_tooling": {
        "reviewer_role": "AI-agent / tooling reviewer",
        "packet": "docs/reviews/agent-tooling-review-packet.md",
        "schema": "docs/reviews/schemas/agent-tooling-review.schema.json",
    },
}
PRIVATE_TEXT_MARKERS = (
    "tasks_private/",
    "results_private/",
    "private task id",
    "private route",
    "private seed",
    "oracle body",
    "/users/",
)


def _is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    lowered = value.strip().lower()
    return (
        lowered in {"", "tbd", "todo", "n/a", "pending", "null", "none", "unknown"}
        or re.search(r"<[^<>]+>", value) is not None
    )


def _value_has_private_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_value_has_private_marker(child) for child in value.values())
    if isinstance(value, list):
        return any(_value_has_private_marker(child) for child in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in PRIVATE_TEXT_MARKERS)


def _validate_json_schema_record(
    record: Any,
    schema: dict[str, Any],
    label: str,
) -> list[str]:
    findings: list[str] = []
    if not isinstance(record, dict):
        return [f"{label}: record must be an object"]

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(required, list) or not isinstance(properties, dict):
        return [f"{label}: review schema has an invalid required/properties contract"]

    for field in required:
        if field not in record:
            findings.append(f"{label}: missing schema-required field {field!r}")
    if schema.get("additionalProperties") is False:
        extras = sorted(set(record) - set(properties))
        if extras:
            findings.append(f"{label}: unexpected fields: {', '.join(extras)}")

    for field, value in record.items():
        contract = properties.get(field)
        if not isinstance(contract, dict):
            continue
        expected_type = contract.get("type")
        type_ok = {
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "array": isinstance(value, list),
            "object": isinstance(value, dict),
        }.get(expected_type, True)
        if not type_ok:
            findings.append(f"{label}.{field}: expected {expected_type}")
            continue
        if "enum" in contract and value not in contract["enum"]:
            findings.append(f"{label}.{field}: value is outside the allowed enum")
        if isinstance(value, str):
            if isinstance(contract.get("minLength"), int) and len(value) < contract["minLength"]:
                findings.append(f"{label}.{field}: string is shorter than minLength")
            if isinstance(contract.get("pattern"), str) and re.search(contract["pattern"], value) is None:
                findings.append(f"{label}.{field}: string does not match required pattern")
            if _is_placeholder(value):
                findings.append(f"{label}.{field}: placeholder value is not allowed")
        if isinstance(value, int) and not isinstance(value, bool):
            if isinstance(contract.get("minimum"), int) and value < contract["minimum"]:
                findings.append(f"{label}.{field}: value is below minimum")
            if isinstance(contract.get("maximum"), int) and value > contract["maximum"]:
                findings.append(f"{label}.{field}: value is above maximum")
        if isinstance(value, list) and isinstance(contract.get("items"), dict):
            item_type = contract["items"].get("type")
            if item_type == "string" and any(not isinstance(item, str) for item in value):
                findings.append(f"{label}.{field}: every array item must be a string")
    if _value_has_private_marker(record):
        findings.append(f"{label}: public review record contains a private-detail marker")
    return findings


def _load_lane_schema(lane_id: str, findings: list[str]) -> dict[str, Any] | None:
    expected = LANE_CONTRACTS[lane_id]
    schema_path = ROOT / expected["schema"]
    if not schema_path.is_file():
        findings.append(f"{lane_id}: schema file does not exist: {expected['schema']}")
        return None
    try:
        schema = load_json(schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(f"{lane_id}: schema file is not valid JSON: {exc}")
        return None
    if not isinstance(schema, dict) or schema.get("type") != "object":
        findings.append(f"{lane_id}: schema must define an object")
        return None
    return schema


def _public_task_ids(findings: list[str]) -> set[str]:
    task_ids: set[str] = set()
    paths = sorted((ROOT / "tasks").glob("*/*.json"))
    if not paths:
        findings.append("appsec: public task inventory is missing or empty")
        return task_ids
    for path in paths:
        try:
            payload = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(
                f"appsec: public task manifest is unreadable: {path.relative_to(ROOT)}: {exc}"
            )
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not payload["id"]:
            findings.append(
                f"appsec: public task manifest has no concrete id: {path.relative_to(ROOT)}"
            )
            continue
        if payload["id"] in task_ids:
            findings.append(f"appsec: duplicate public task id in manifest inventory: {payload['id']}")
        task_ids.add(payload["id"])
    if len(paths) != EXPECTED_PUBLIC_TASK_COUNT or len(task_ids) != EXPECTED_PUBLIC_TASK_COUNT:
        findings.append(
            "appsec: public task inventory must contain exactly "
            f"{EXPECTED_PUBLIC_TASK_COUNT} unique manifests"
        )
    return task_ids


def _git_commit_exists(commit_sha: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _validate_records(
    lane: dict[str, Any],
    findings: list[str],
    *,
    require_full_coverage: bool,
) -> None:
    lane_id = str(lane.get("lane"))
    records = lane.get("per_task_records")
    if not isinstance(records, list) or not records:
        if require_full_coverage:
            findings.append(f"{lane_id}: complete review requires non-empty per_task_records")
        return
    schema = _load_lane_schema(lane_id, findings)
    if schema is None:
        return

    for index, record in enumerate(records):
        label = f"{lane_id}.per_task_records[{index}]"
        findings.extend(_validate_json_schema_record(record, schema, label))
        if not isinstance(record, dict):
            continue
        for field in ("reviewer_role", "review_date", "reviewed_commit_sha"):
            lane_field = "reviewer_role" if field == "reviewer_role" else field
            if record.get(field) != lane.get(lane_field):
                findings.append(f"{label}.{field}: must match the lane-level value")
        if record.get("blocking_issue") is True or record.get("blocking_issues"):
            findings.append(f"{label}: unresolved blocking issue is incompatible with complete status")

    if lane_id == "appsec":
        record_task_ids = [
            record.get("task_id")
            for record in records
            if isinstance(record, dict) and isinstance(record.get("task_id"), str)
        ]
        duplicates = sorted({task_id for task_id in record_task_ids if record_task_ids.count(task_id) > 1})
        if duplicates:
            findings.append(f"appsec: duplicate public task review records: {', '.join(duplicates)}")
        expected_task_ids = _public_task_ids(findings)
        missing = sorted(expected_task_ids - set(record_task_ids))
        unexpected = sorted(set(record_task_ids) - expected_task_ids)
        if require_full_coverage and missing:
            findings.append(f"appsec: missing public task review records ({len(missing)})")
        if unexpected:
            findings.append(f"appsec: unexpected public task review ids: {', '.join(unexpected)}")
    elif require_full_coverage and len(records) != 1:
        findings.append(f"{lane_id}: complete lane requires exactly one lane-level review record")
    elif not require_full_coverage and len(records) > 1:
        findings.append(f"{lane_id}: in-progress lane allows at most one lane-level review record")


def _validate_lane(lane: dict[str, Any], require_complete: bool) -> list[str]:
    findings: list[str] = []
    lane_id = lane.get("lane")
    extra_fields = sorted(set(lane) - LANE_ALLOWED_FIELDS)
    if extra_fields:
        findings.append(f"{lane_id}: unexpected lane fields: {', '.join(extra_fields)}")
    status = lane.get("review_status")
    if status not in VALID_STATUSES:
        findings.append(f"{lane_id}: review_status must be one of {sorted(VALID_STATUSES)}")
    for required in (
        "lane",
        "reviewer_role",
        "packet",
        "schema",
        "review_status",
        "reviewer_id",
        "review_date",
        "reviewed_commit_sha",
        "overall_disposition",
        "blocking_issues",
        "nonblocking_issues",
        "per_task_records",
    ):
        if required not in lane:
            findings.append(f"{lane_id}: missing required field {required!r}")
    if lane_id not in LANE_CONTRACTS:
        return findings
    expected = LANE_CONTRACTS[lane_id]
    for field in ("reviewer_role", "packet", "schema"):
        if lane.get(field) != expected[field]:
            findings.append(f"{lane_id}: {field} must be {expected[field]!r}")
    for field in ("packet", "schema"):
        if not (ROOT / expected[field]).is_file():
            findings.append(f"{lane_id}: referenced {field} file does not exist")
    for field in ("blocking_issues", "nonblocking_issues", "per_task_records"):
        if not isinstance(lane.get(field), list):
            findings.append(f"{lane_id}: {field} must be a list")
    for field in ("blocking_issues", "nonblocking_issues"):
        issues = lane.get(field)
        if isinstance(issues, list) and any(
            not isinstance(item, str)
            or _is_placeholder(item)
            or _value_has_private_marker(item)
            for item in issues
        ):
            findings.append(f"{lane_id}: {field} must contain concrete public-safe strings")
    if require_complete and status != "complete":
        findings.append(f"{lane_id}: review_status is not 'complete' under --require-v2-complete")
    if status == "complete":
        if _is_placeholder(lane.get("reviewer_id")):
            findings.append(f"{lane_id}: reviewer_id is placeholder under 'complete'")
        if not re.fullmatch(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", str(lane.get("review_date") or "")):
            findings.append(f"{lane_id}: review_date is not a YYYY-MM-DD date under 'complete'")
        else:
            try:
                if date.fromisoformat(str(lane["review_date"])) > date.today():
                    findings.append(f"{lane_id}: review_date cannot be in the future")
            except ValueError:
                findings.append(f"{lane_id}: review_date is not a real calendar date")
        if not re.fullmatch(r"^[0-9a-f]{40}$", str(lane.get("reviewed_commit_sha") or "")):
            findings.append(f"{lane_id}: reviewed_commit_sha is not a 40-char SHA under 'complete'")
        elif not _git_commit_exists(str(lane["reviewed_commit_sha"])):
            findings.append(f"{lane_id}: reviewed_commit_sha must reference an existing commit")
        if lane.get("overall_disposition") not in VALID_DISPOSITIONS:
            findings.append(
                f"{lane_id}: overall_disposition must be one of {sorted(VALID_DISPOSITIONS)} under 'complete'"
            )
        elif require_complete and lane.get("overall_disposition") not in ACCEPTED_DISPOSITIONS:
            findings.append(
                f"{lane_id}: overall_disposition must be accepted under --require-v2-complete"
            )
        if lane.get("blocking_issues"):
            findings.append(
                f"{lane_id}: blocking_issues is non-empty under 'complete' (must be resolved or explicitly accepted)"
            )
        _validate_records(lane, findings, require_full_coverage=True)
    elif status == "in_progress" and lane.get("per_task_records"):
        _validate_records(lane, findings, require_full_coverage=False)
    elif status == "pending" and lane.get("per_task_records"):
        findings.append(f"{lane_id}: pending lane must not contain review records")
    return findings


def validate(require_v2_complete: bool = False) -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {
            "schema_version": "external-review-summary-v1",
            "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
            "lanes": [],
            "findings": [f"missing registry: {REGISTRY_PATH.relative_to(ROOT)}"],
            "passed": False,
        }
    try:
        data = load_json(REGISTRY_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "external-review-summary-v1",
            "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
            "lanes": [],
            "findings": [f"registry is not valid JSON: {exc}"],
            "passed": False,
            "v2_external_validation_complete": False,
        }
    if not isinstance(data, dict):
        return {
            "schema_version": "external-review-summary-v1",
            "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
            "lanes": [],
            "findings": ["registry root must be an object"],
            "passed": False,
            "v2_external_validation_complete": False,
        }
    lanes = data.get("lanes", [])
    lane_reports: list[dict[str, Any]] = []
    findings: list[str] = []
    if data.get("schema_version") != "external-review-registry-v1":
        findings.append("registry schema_version must be 'external-review-registry-v1'")
    extra_registry_fields = sorted(set(data) - REGISTRY_ALLOWED_FIELDS)
    if extra_registry_fields:
        findings.append(f"unexpected registry fields: {', '.join(extra_registry_fields)}")
    if _value_has_private_marker(data):
        findings.append("registry contains a private-detail marker")
    if not isinstance(data.get("description"), str) or _is_placeholder(data.get("description")):
        findings.append("registry description must be concrete text")
    if not isinstance(lanes, list):
        findings.append("registry lanes must be a list")
        lanes = []

    lane_ids: list[str] = []
    for index, lane in enumerate(lanes):
        if not isinstance(lane, dict):
            findings.append(f"lane entry {index} must be an object")
            continue
        lane_id = lane.get("lane")
        if isinstance(lane_id, str):
            lane_ids.append(lane_id)
        lane_findings = _validate_lane(lane, require_v2_complete)
        lane_reports.append(
            {
                "lane": lane.get("lane"),
                "review_status": lane.get("review_status"),
                "reviewer_id": lane.get("reviewer_id"),
                "review_date": lane.get("review_date"),
                "overall_disposition": lane.get("overall_disposition"),
                "findings": lane_findings,
                "passed": not lane_findings,
            }
        )
        findings.extend(lane_findings)

    duplicate_lane_ids = sorted({lane_id for lane_id in lane_ids if lane_ids.count(lane_id) > 1})
    missing_lane_ids = sorted(set(REQUIRED_LANE_IDS) - set(lane_ids))
    unexpected_lane_ids = sorted(set(lane_ids) - set(REQUIRED_LANE_IDS))
    if duplicate_lane_ids:
        findings.append(f"duplicate review lanes: {', '.join(duplicate_lane_ids)}")
    if missing_lane_ids:
        findings.append(f"missing required review lanes: {', '.join(missing_lane_ids)}")
    if unexpected_lane_ids:
        findings.append(f"unexpected review lanes: {', '.join(unexpected_lane_ids)}")

    canonical_lane_set = (
        len(lanes) == len(REQUIRED_LANE_IDS)
        and len(lane_ids) == len(REQUIRED_LANE_IDS)
        and set(lane_ids) == set(REQUIRED_LANE_IDS)
        and not duplicate_lane_ids
    )
    return {
        "schema_version": "external-review-summary-v1",
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "summary_md_path": str(SUMMARY_PATH.relative_to(ROOT)) if SUMMARY_PATH.exists() else None,
        "lanes": lane_reports,
        "findings": findings,
        "passed": not findings,
        "v2_external_validation_complete": (
            not findings
            and canonical_lane_set
            and all(
                lane.get("review_status") == "complete"
                and lane.get("overall_disposition") in ACCEPTED_DISPOSITIONS
                for lane in lanes
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--require-v2-complete",
        action="store_true",
        help="Fail unless every review lane is in 'complete' status with a real reviewer record.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full JSON result.")
    args = parser.parse_args()

    result = validate(require_v2_complete=args.require_v2_complete)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["passed"]:
            print(
                f"external review summary: ok; v2_external_validation_complete={result['v2_external_validation_complete']}"
            )
        else:
            print(f"external review summary: FAILED ({len(result['findings'])} findings)", file=sys.stderr)
            for finding in result["findings"]:
                print(f"  - {finding}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
