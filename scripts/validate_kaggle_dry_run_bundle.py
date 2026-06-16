#!/usr/bin/env python3
"""Validator for the platform/kaggle/dry-run-bundle/ directory."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "platform/kaggle/dry-run-bundle"
TASKS_DIR = ROOT / "tasks"


def validate_dry_run_bundle(bundle_dir: Path) -> dict:
    errors = []
    if not bundle_dir.is_dir():
        return {"passed": False, "errors": [f"Bundle directory does not exist: {bundle_dir}"]}

    csv_path = bundle_dir / "sample_submission.csv"
    manifest_path = bundle_dir / "manifest.json"

    if not csv_path.is_file():
        errors.append(f"Missing sample_submission.csv in bundle: {csv_path}")
    if not manifest_path.is_file():
        errors.append(f"Missing manifest.json in bundle: {manifest_path}")

    # Validate manifest
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("leaderboard_eligible") is not False:
                errors.append("manifest.json must have leaderboard_eligible: false")
        except Exception as e:
            errors.append(f"Failed to parse manifest.json: {e}")

    # Validate CSV and referenced submissions
    if csv_path.is_file():
        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                if headers != ["Id", "finding_path", "notes"]:
                    errors.append(f"Invalid CSV headers: {headers}")

                vulnerable_count = 0
                denial_count = 0
                authorized_allow_count = 0
                ids = []

                for idx, row in enumerate(reader, start=2):
                    task_id = row.get("Id")
                    finding_path = row.get("finding_path")
                    notes = row.get("notes")

                    if not task_id:
                        errors.append(f"Row {idx}: Missing Id")
                        continue

                    ids.append(task_id)

                    # Check private/leakage patterns
                    row_str = f"{task_id} {finding_path} {notes}".lower()
                    private_patterns = ["tasks_private", "holdout", "private route", "private seed", "raw private", "/users/", "/home/"]
                    for p in private_patterns:
                        if p in row_str:
                            errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

                    # Check submission JSON exists
                    if finding_path:
                        sub_path = bundle_dir / finding_path
                        if not sub_path.is_file():
                            errors.append(f"Referenced finding file does not exist: {finding_path}")
                        else:
                            try:
                                sub_data = json.loads(sub_path.read_text(encoding="utf-8"))
                                if sub_data.get("leaderboard_eligible") is not False:
                                    errors.append(f"{finding_path} must have leaderboard_eligible: false")
                                
                                # Check private markers inside the submission JSON
                                sub_str = json.dumps(sub_data).lower()
                                for p in private_patterns:
                                    if p in sub_str:
                                        errors.append(f"{finding_path}: Contains forbidden private substring '{p}'")
                            except Exception as e:
                                errors.append(f"Failed to parse {finding_path}: {e}")

                    # Check type in public tasks
                    task_paths = list(TASKS_DIR.glob(f"*/{task_id}.json"))
                    if not task_paths:
                        errors.append(f"Row {idx} ({task_id}): Task Id not found in public tasks")
                    else:
                        task_path = task_paths[0]
                        try:
                            task_data = json.loads(task_path.read_text(encoding="utf-8"))
                            is_vulnerable = task_data.get("expected_vulnerable", False)
                            control_type = task_data.get("control_type")
                            if is_vulnerable:
                                vulnerable_count += 1
                            elif control_type == "denial":
                                denial_count += 1
                            elif control_type == "authorized_allow":
                                authorized_allow_count += 1
                        except Exception as e:
                            errors.append(f"Row {idx} ({task_id}): Failed to parse task file: {e}")

                if vulnerable_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one vulnerable task, found {vulnerable_count}")
                if denial_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one denial control, found {denial_count}")
                if authorized_allow_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one authorized-allow control, found {authorized_allow_count}")

        except Exception as e:
            errors.append(f"Failed to read CSV: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    result = validate_dry_run_bundle(BUNDLE_DIR)
    if not result["passed"]:
        print("Kaggle dry-run bundle validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle dry-run bundle validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
