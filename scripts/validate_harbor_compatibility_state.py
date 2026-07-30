"""Validate the checked-in three-task Harbor compatibility evidence.

The validator separates two questions:

* whether the evidence is internally well formed and honestly classified; and
* whether the generated pilot still matches the current canonical source tree.

A historical/stale artifact can therefore validate as an honest record while
``active_compatibility_verified`` remains false. It cannot become current by
editing status fields: the generated dataset must pass the canonical skeleton
validator first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench_harbor.public_pilot import PUBLIC_PILOT_TASKS
from authzbench_harbor.redaction import scan_for_violations
from authzbench.core import load_json
from scripts.validate_harbor_dataset_skeleton import (
    validate_harbor_dataset_skeleton,
)


PILOT_DIR = ROOT / "artifact" / "harbor-kaggle-public-pilot"
EVIDENCE_PATH = PILOT_DIR / "local-harbor-evidence.json"
SCHEMA_VERSION = "authzbench-harbor-local-evidence-v2"
CURRENT_STATUS = "current_source_compatible"
STALE_STATUS = "historical_stale_requires_rebuild"


def _load_object(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def _exact_task_map(
    rows: object,
    *,
    id_field: str,
    label: str,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        task_id = row.get(id_field)
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"{label}[{index}].{id_field} must be a non-empty string")
            continue
        if task_id in result:
            errors.append(f"{label} contains duplicate task id: {task_id}")
            continue
        result[task_id] = row
    expected = set(PUBLIC_PILOT_TASKS)
    if set(result) != expected:
        errors.append(
            f"{label} task ids must exactly match the three-task public pilot; "
            f"missing={sorted(expected - set(result))}, "
            f"unexpected={sorted(set(result) - expected)}"
        )
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_binding_errors(
    dataset_dir: Path,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
) -> list[str]:
    """Return missing/tampered bindings required for a current run claim."""

    errors: list[str] = []
    source_sha = evidence.get("benchmark_source_sha")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        errors.append(
            "current compatibility evidence requires a full benchmark_source_sha"
        )
    elif manifest.get("benchmark_source_sha") != source_sha:
        errors.append(
            "dataset manifest benchmark_source_sha must match compatibility evidence"
        )
    else:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{source_sha}^{{commit}}"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            errors.append(
                "benchmark_source_sha must resolve to a commit in this repository"
            )

    bound_files = {
        "dataset_manifest_sha256": dataset_dir / "dataset-manifest.json",
        "run_config_sha256": dataset_dir / "run_authzbench_saas.yaml",
    }
    for field, path in bound_files.items():
        value = evidence.get(field)
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"[0-9a-f]{64}", value)
            or value != _sha256(path)
        ):
            errors.append(f"{field} must match the checked-in pilot file")

    run_ids = evidence.get("harbor_run_ids")
    if (
        not isinstance(run_ids, list)
        or len(run_ids) != 6
        or len(set(run_ids)) != 6
        or not all(isinstance(run_id, str) and run_id.strip() for run_id in run_ids)
    ):
        errors.append(
            "current compatibility evidence requires six unique Harbor run ids"
        )
    verified_at = evidence.get("execution_verified_at")
    if not isinstance(verified_at, str) or not verified_at.strip():
        errors.append("current compatibility evidence requires execution_verified_at")
    return errors


def validate_harbor_compatibility_state(
    dataset_dir: Path = PILOT_DIR,
    evidence_path: Path = EVIDENCE_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        evidence = _load_object(evidence_path)
    except Exception as exc:
        return {
            "active_compatibility_verified": False,
            "current_validation_errors": [],
            "errors": [str(exc)],
            "passed": False,
        }
    try:
        manifest = _load_object(dataset_dir / "dataset-manifest.json")
    except Exception as exc:
        return {
            "active_compatibility_verified": False,
            "current_validation_errors": [str(exc)],
            "errors": [],
            "passed": False,
        }

    if evidence.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    boundary = str(evidence.get("claim_boundary", ""))
    for phrase in (
        "not Kaggle-hosted execution",
        "platform acceptance",
        "independent review",
        "launch evidence",
    ):
        if phrase not in boundary:
            errors.append(f"claim_boundary must include: {phrase}")

    manifest_rows = _exact_task_map(
        manifest.get("tasks"),
        id_field="id",
        label="dataset manifest tasks",
        errors=errors,
    )
    evidence_rows = _exact_task_map(
        evidence.get("tasks"),
        id_field="task_id",
        label="compatibility evidence tasks",
        errors=errors,
    )
    if manifest.get("task_count") != len(PUBLIC_PILOT_TASKS):
        errors.append("dataset manifest task_count must be 3")
    if manifest.get("oracle_solution_mode") != "public-pilot-reference":
        errors.append(
            "dataset manifest oracle_solution_mode must be public-pilot-reference"
        )

    manifest_contract = evidence.get("manifest_contract")
    if not isinstance(manifest_contract, dict):
        errors.append("manifest_contract must be an object")
        manifest_contract = {}
    if manifest_contract.get("task_count") != len(PUBLIC_PILOT_TASKS):
        errors.append("manifest_contract.task_count must be 3")
    if manifest_contract.get("digest_match_count") != len(PUBLIC_PILOT_TASKS):
        errors.append("manifest_contract.digest_match_count must be 3")
    if manifest_contract.get("all_digests_match") is not True:
        errors.append("manifest_contract.all_digests_match must be true")
    if manifest_contract.get("publish_attempted") is not False:
        errors.append("manifest_contract.publish_attempted must be false")

    runtime = evidence.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
        runtime = {}
    if runtime.get("raw_jobs_retained_outside_repository") is not True:
        errors.append("runtime.raw_jobs_retained_outside_repository must be true")
    if runtime.get("job_roots_redacted") is not True:
        errors.append("runtime.job_roots_redacted must be true")
    for forbidden_field in ("fresh_job_root", "prior_repeat_job_root"):
        if forbidden_field in runtime:
            errors.append(f"runtime.{forbidden_field} must not be tracked")
    if runtime.get("verifier_source_set_sha256") != manifest.get(
        "verifier_source_set_sha256"
    ):
        errors.append(
            "runtime.verifier_source_set_sha256 must match the dataset manifest"
        )

    fresh = evidence.get("fresh_current_starter_validation")
    if not isinstance(fresh, dict):
        errors.append("fresh_current_starter_validation must be an object")
        fresh = {}
    expected_fresh_counts = {
        "total_runs": 6,
        "completed_runs": 6,
        "errored_runs": 0,
        "nop_zero_count": 3,
        "oracle_one_count": 3,
        "trial_log_count": 6,
        "ctrf_count": 6,
    }
    for field, expected in expected_fresh_counts.items():
        if fresh.get(field) != expected:
            errors.append(
                f"fresh_current_starter_validation.{field} must be {expected}"
            )

    for task_id in sorted(set(manifest_rows) & set(evidence_rows)):
        manifest_row = manifest_rows[task_id]
        evidence_row = evidence_rows[task_id]
        if manifest_row.get("pilot_behavior") != PUBLIC_PILOT_TASKS[task_id]:
            errors.append(f"{task_id}: manifest pilot_behavior is incorrect")
        if evidence_row.get("pilot_behavior") != PUBLIC_PILOT_TASKS[task_id]:
            errors.append(f"{task_id}: evidence pilot_behavior is incorrect")
        if evidence_row.get("harbor_content_digest") != manifest_row.get(
            "harbor_content_digest"
        ):
            errors.append(
                f"{task_id}: evidence harbor_content_digest must match the manifest"
            )
        if evidence_row.get("fresh_nop_reward") != 0.0:
            errors.append(f"{task_id}: fresh_nop_reward must be 0.0")
        if evidence_row.get("fresh_oracle_reward") != 1.0:
            errors.append(f"{task_id}: fresh_oracle_reward must be 1.0")
        if evidence_row.get("prior_nop_rewards") != [0.0, 0.0]:
            errors.append(f"{task_id}: prior_nop_rewards must contain two zeroes")
        if evidence_row.get("prior_oracle_rewards") != [1.0, 1.0]:
            errors.append(f"{task_id}: prior_oracle_rewards must contain two ones")

    dataset_result = validate_harbor_dataset_skeleton(dataset_dir)
    current_validation_errors = [
        *(dataset_result.get("errors") or []),
        *_current_binding_errors(dataset_dir, manifest, evidence),
    ]
    active_compatibility_verified = (
        dataset_result.get("passed") is True
        and not current_validation_errors
        and not errors
    )
    expected_status = CURRENT_STATUS if active_compatibility_verified else STALE_STATUS
    if evidence.get("evidence_status") != expected_status:
        errors.append(
            f"evidence_status must be {expected_status} for the validated dataset state"
        )
    if active_compatibility_verified:
        if evidence.get("current_claim_eligible") is not True:
            errors.append("current compatible evidence must be current_claim_eligible")
        if evidence.get("requires_rebuild_before_current_claim") is not False:
            errors.append(
                "current compatible evidence must not require a rebuild"
            )
    else:
        if evidence.get("current_claim_eligible") is not False:
            errors.append("stale evidence must set current_claim_eligible=false")
        if evidence.get("requires_rebuild_before_current_claim") is not True:
            errors.append(
                "stale evidence must require a rebuild before a current claim"
            )
        stale_reason = evidence.get("stale_reason")
        if not isinstance(stale_reason, str) or not stale_reason.strip():
            errors.append("stale evidence must include stale_reason")

    errors.extend(scan_for_violations(evidence, "Harbor compatibility evidence"))
    return {
        "active_compatibility_verified": active_compatibility_verified,
        "current_validation_errors": current_validation_errors,
        "declared_status": evidence.get("evidence_status"),
        "errors": sorted(set(errors)),
        "passed": not errors,
        "task_count": len(evidence_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the three-task Harbor compatibility evidence state."
    )
    parser.add_argument("--dataset-dir", type=Path, default=PILOT_DIR)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
    args = parser.parse_args()
    result = validate_harbor_compatibility_state(args.dataset_dir, args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
