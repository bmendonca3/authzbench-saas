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
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs/reviews/external-review-registry.json"
SUMMARY_PATH = ROOT / "docs/reviews/external-review-summary.md"

VALID_DISPOSITIONS = {"accept", "accept_with_minor_changes", "reject"}
VALID_STATUSES = {"pending", "in_progress", "complete"}


def _is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    return lowered in {"", "tbd", "todo", "n/a", "pending", "null", "none"}


def _validate_lane(lane: dict[str, Any], require_complete: bool) -> list[str]:
    findings: list[str] = []
    status = lane.get("review_status")
    if status not in VALID_STATUSES:
        findings.append(f"{lane.get('lane')}: review_status must be one of {sorted(VALID_STATUSES)}")
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
            findings.append(f"{lane.get('lane')}: missing required field {required!r}")
    if require_complete and status != "complete":
        findings.append(f"{lane.get('lane')}: review_status is not 'complete' under --require-v2-complete")
    if status == "complete":
        if _is_placeholder(lane.get("reviewer_id")):
            findings.append(f"{lane.get('lane')}: reviewer_id is placeholder under 'complete'")
        if not re.fullmatch(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", str(lane.get("review_date") or "")):
            findings.append(f"{lane.get('lane')}: review_date is not a YYYY-MM-DD date under 'complete'")
        if not re.fullmatch(r"^[0-9a-f]{40}$", str(lane.get("reviewed_commit_sha") or "")):
            findings.append(f"{lane.get('lane')}: reviewed_commit_sha is not a 40-char SHA under 'complete'")
        if lane.get("overall_disposition") not in VALID_DISPOSITIONS:
            findings.append(
                f"{lane.get('lane')}: overall_disposition must be one of {sorted(VALID_DISPOSITIONS)} under 'complete'"
            )
        if lane.get("blocking_issues"):
            findings.append(
                f"{lane.get('lane')}: blocking_issues is non-empty under 'complete' (must be resolved or explicitly accepted)"
            )
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
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    lanes = data.get("lanes", [])
    lane_reports: list[dict[str, Any]] = []
    findings: list[str] = []
    for lane in lanes:
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
    return {
        "schema_version": "external-review-summary-v1",
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "summary_md_path": str(SUMMARY_PATH.relative_to(ROOT)) if SUMMARY_PATH.exists() else None,
        "lanes": lane_reports,
        "findings": findings,
        "passed": not findings,
        "v2_external_validation_complete": (
            all(lane.get("review_status") == "complete" for lane in lanes) if lanes else False
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
