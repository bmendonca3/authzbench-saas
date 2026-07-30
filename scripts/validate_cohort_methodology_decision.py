#!/usr/bin/env python3
"""Validate the scored-cohort methodology decision and its source bindings."""

from __future__ import annotations

import argparse
import hashlib
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

DECISION_PATH = Path("docs/reviews/cohort-methodology-decision.json")
SCHEMA_PATH = Path("docs/reviews/schemas/cohort-methodology-decision.schema.json")
CONTRACT_PATH = Path("artifact/scored-cohort-contract.v1.json")
SUMMARY_PATHS = [
    "artifact/private-holdout-active-public-summary.json",
    "artifact/private-holdout-shadow-public-summary.json",
]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PRIVATE_KEY_MARKERS = (
    "task_id",
    "task_ids",
    "seed",
    "route",
    "oracle",
    "body",
    "manifest_path",
    "raw_result",
    "diagnostic_detail",
)


def _load_object(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot load JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: root must be a JSON object")
        return {}
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit_exists(root: Path, sha: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def _git_blob(root: Path, sha: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{sha}:{relative_path}"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout if result.returncode == 0 else None


def _safe_file(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _private_key_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key).lower().replace("-", "_")
            child_path = f"{path}.{raw_key}"
            if any(marker in key for marker in PRIVATE_KEY_MARKERS):
                errors.append(f"{child_path}: private-detail key is not allowed")
            errors.extend(_private_key_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_private_key_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if "tasks_private/" in lowered or re.search(r"(^|\\s)/(users|private|tmp)/", lowered):
            errors.append(f"{path}: private or absolute path marker is not allowed")
    return errors


def _validate_private_summary_refresh(
    root: Path,
    public_manifest_digest: str,
    errors: list[str],
) -> None:
    for relative in SUMMARY_PATHS:
        summary = _load_object(root / relative, errors, relative)
        bindings = summary.get("source_bindings")
        if not isinstance(bindings, dict):
            errors.append(f"{relative}: source_bindings are required for accepted methodology")
            continue
        if bindings.get("public_manifest_set_sha256") != public_manifest_digest:
            errors.append(f"{relative}: public manifest digest is stale or missing")
        private_fingerprint = bindings.get("private_pack_fingerprint_sha256")
        if not isinstance(private_fingerprint, str) or HEX64.fullmatch(
            private_fingerprint
        ) is None:
            errors.append(f"{relative}: private pack fingerprint is required")
        source_sha = bindings.get("overlap_check_source_commit_sha")
        if (
            not isinstance(source_sha, str)
            or HEX40.fullmatch(source_sha) is None
            or not _git_commit_exists(root, source_sha)
        ):
            errors.append(f"{relative}: overlap-check source commit is invalid")
        for field in ("summary_generated_at", "overlap_checked_at"):
            value = bindings.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{relative}: {field} is required")


def validate(
    root: Path = ROOT,
    *,
    require_complete: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    decision = _load_object(root / DECISION_PATH, errors, str(DECISION_PATH))
    schema = _load_object(root / SCHEMA_PATH, errors, str(SCHEMA_PATH))
    contract = _load_object(root / CONTRACT_PATH, errors, str(CONTRACT_PATH))
    errors.extend(_private_key_errors(decision))

    if schema.get("additionalProperties") is not False:
        errors.append("cohort methodology schema must set additionalProperties=false")
    allowed_fields = set(schema.get("properties", {}))
    unexpected = sorted(set(decision) - allowed_fields)
    if unexpected:
        errors.append("unexpected decision fields: " + ", ".join(unexpected))
    required_fields = set(schema.get("required", []))
    missing = sorted(required_fields - set(decision))
    if missing:
        errors.append("missing decision fields: " + ", ".join(missing))

    if decision.get("schema_version") != "cohort-methodology-decision-v1":
        errors.append("schema_version must be cohort-methodology-decision-v1")
    status = decision.get("status")
    if status not in {"pending", "accepted", "rejected"}:
        errors.append("status must be pending, accepted, or rejected")
    claim = decision.get("public_claim_boundary")
    if not isinstance(claim, str) or not claim.strip():
        errors.append("public_claim_boundary must be concrete text")

    bindings = decision.get("source_bindings")
    if not isinstance(bindings, dict):
        errors.append("source_bindings must be an object")
        bindings = {}
    if bindings.get("cohort_contract_path") != str(CONTRACT_PATH):
        errors.append("cohort_contract_path must reference the canonical contract")
    contract_path = root / CONTRACT_PATH
    if contract_path.is_file():
        expected_contract_digest = _sha256(contract_path)
        if bindings.get("cohort_contract_sha256") != expected_contract_digest:
            errors.append("cohort contract digest is stale")
    public_digest = contract.get("source_bindings", {}).get(
        "public_manifest_set_sha256"
    )
    if not isinstance(public_digest, str) or HEX64.fullmatch(public_digest) is None:
        errors.append("cohort contract public manifest digest is invalid")
        public_digest = ""
    if bindings.get("public_manifest_set_sha256") != public_digest:
        errors.append("decision public manifest digest does not match cohort contract")
    if bindings.get("private_summary_paths") != SUMMARY_PATHS:
        errors.append("private_summary_paths must equal the canonical active/shadow summaries")
    refresh_status = bindings.get("private_summary_refresh_status")
    if refresh_status not in {"required", "current"}:
        errors.append("private_summary_refresh_status must be required or current")

    private_cohort = decision.get("private_cohort")
    if not isinstance(private_cohort, dict):
        errors.append("private_cohort must be an object")
        private_cohort = {}
    if private_cohort.get("observed_private_task_count") != 48:
        errors.append("observed_private_task_count must be 48")
    minimums = private_cohort.get("minimum_analysis")
    if not isinstance(minimums, dict):
        errors.append("minimum_analysis must be an object")
        minimums = {}

    if decision.get("launch_ready") is not False:
        errors.append("cohort methodology decision cannot set launch_ready=true")

    if status == "pending":
        if decision.get("reviewer_role_scope") is not None:
            errors.append("pending decision reviewer_role_scope must be null")
        if decision.get("review_date") is not None:
            errors.append("pending decision review_date must be null")
        if decision.get("reviewed_commit_sha") is not None:
            errors.append("pending decision reviewed_commit_sha must be null")
        if private_cohort.get("cluster_assignment_status") != "pending":
            errors.append("pending decision cluster assignment must be pending")
        if private_cohort.get("cluster_disjointness_status") != "pending":
            errors.append("pending decision cluster disjointness must be pending")
        if minimums.get("status") != "pending":
            errors.append("pending decision minimum analysis must be pending")
        for field in (
            "analysis_artifact",
            "minimum_scored_task_count",
            "minimum_semantic_cluster_count",
        ):
            if minimums.get(field) is not None:
                errors.append(f"pending decision {field} must be null")
        if decision.get("methodology_decision") is not None:
            errors.append("pending methodology_decision must be null")
        if decision.get("cohort_admitted") is not False:
            errors.append("pending decision cohort_admitted must be false")
        if decision.get("admitted_scored_task_count") != 0:
            errors.append("pending decision admitted_scored_task_count must be zero")
        for field in ("blocker", "next_action"):
            value = decision.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"pending decision requires concrete {field}")
        if refresh_status != "required":
            errors.append("pending decision must keep private summary refresh required")
        if require_complete:
            errors.append("cohort methodology decision is pending")

    elif status == "accepted":
        reviewer = decision.get("reviewer_role_scope")
        if not isinstance(reviewer, str) or not reviewer.strip():
            errors.append("accepted decision requires reviewer_role_scope")
        review_date = decision.get("review_date")
        try:
            parsed_date = date.fromisoformat(str(review_date))
        except ValueError:
            errors.append("accepted decision review_date must be YYYY-MM-DD")
        else:
            if parsed_date > date.today():
                errors.append("accepted decision review_date cannot be in the future")
        reviewed_sha = decision.get("reviewed_commit_sha")
        if (
            not isinstance(reviewed_sha, str)
            or HEX40.fullmatch(reviewed_sha) is None
            or not _git_commit_exists(root, reviewed_sha)
        ):
            errors.append("accepted decision requires an existing reviewed commit")
            reviewed_sha = ""
        if refresh_status != "current":
            errors.append("accepted decision requires current private summary bindings")
        elif public_digest:
            _validate_private_summary_refresh(root, public_digest, errors)
        if private_cohort.get("cluster_assignment_status") != "complete":
            errors.append("accepted decision requires complete private cluster assignment")
        if private_cohort.get("cluster_disjointness_status") != "verified":
            errors.append("accepted decision requires verified cluster disjointness")
        if minimums.get("status") != "complete":
            errors.append("accepted decision requires complete numeric minimum analysis")
        analysis_path = _safe_file(root, minimums.get("analysis_artifact"))
        if analysis_path is None:
            errors.append("accepted decision requires a safe existing analysis_artifact")
        elif reviewed_sha:
            relative = analysis_path.relative_to(root).as_posix()
            reviewed_blob = _git_blob(root, reviewed_sha, relative)
            if reviewed_blob is None or reviewed_blob != analysis_path.read_bytes():
                errors.append("minimum analysis artifact must match the reviewed commit")
        minimum_task_count = minimums.get("minimum_scored_task_count")
        minimum_cluster_count = minimums.get("minimum_semantic_cluster_count")
        if not isinstance(minimum_task_count, int) or isinstance(
            minimum_task_count, bool
        ) or minimum_task_count <= 0:
            errors.append("minimum_scored_task_count must be a positive integer")
        if not isinstance(minimum_cluster_count, int) or isinstance(
            minimum_cluster_count, bool
        ) or minimum_cluster_count <= 0:
            errors.append("minimum_semantic_cluster_count must be a positive integer")
        if decision.get("methodology_decision") not in {
            "accept",
            "accept_with_minor_changes",
        }:
            errors.append("accepted status requires an accepting methodology_decision")
        if decision.get("cohort_admitted") is not True:
            errors.append("accepted decision requires cohort_admitted=true")
        admitted = decision.get("admitted_scored_task_count")
        if not isinstance(admitted, int) or isinstance(admitted, bool) or admitted <= 0:
            errors.append("accepted decision requires a positive admitted task count")
        elif isinstance(minimum_task_count, int) and admitted < minimum_task_count:
            errors.append("admitted task count is below the reviewed numeric minimum")
        if decision.get("blocker") is not None or decision.get("next_action") is not None:
            errors.append("accepted decision blocker and next_action must be null")

    elif status == "rejected" and require_complete:
        errors.append("rejected cohort methodology cannot satisfy completion")

    complete = status == "accepted" and not errors
    return {
        "schema_version": "cohort-methodology-decision-validation-v1",
        "passed": not errors,
        "methodology_complete": complete,
        "status": status,
        "errors": errors,
        "decision_path": str(DECISION_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.root.resolve(), require_complete=args.require_complete)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["passed"]:
        print(
            "cohort methodology decision: ok; "
            f"methodology_complete={result['methodology_complete']}"
        )
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
