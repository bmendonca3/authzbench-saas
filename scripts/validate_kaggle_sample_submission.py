#!/usr/bin/env python3
"""Validator for platform/kaggle/sample_submission.csv."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "platform/kaggle/sample_submission.csv"
TASKS_DIR = ROOT / "tasks"


def validate_sample_csv(path: Path) -> dict:
    errors = []
    if not path.is_file():
        return {"passed": False, "errors": [f"File does not exist: {path}"]}

    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            if headers != ["Id", "finding_path", "notes"]:
                errors.append(f"Invalid headers: {headers}. Expected: ['Id', 'finding_path', 'notes']")

            ids = []
            vulnerable_count = 0
            denial_count = 0
            authorized_allow_count = 0

            for idx, row in enumerate(reader, start=2):
                task_id = row.get("Id")
                finding_path = row.get("finding_path")
                notes = row.get("notes")

                if not task_id:
                    errors.append(f"Row {idx}: Missing Id")
                    continue

                ids.append(task_id)

                # Check path validity
                if not finding_path:
                    errors.append(f"Row {idx} ({task_id}): Missing finding_path")
                else:
                    if Path(finding_path).is_absolute():
                        errors.append(f"Row {idx} ({task_id}): finding_path must be relative: {finding_path}")
                    if not finding_path.startswith("submissions/"):
                        errors.append(f"Row {idx} ({task_id}): finding_path must start with submissions/: {finding_path}")
                    if not finding_path.endswith("/submission.json"):
                        errors.append(f"Row {idx} ({task_id}): finding_path must end with /submission.json: {finding_path}")

                # Check private strings
                row_str = f"{task_id} {finding_path} {notes}".lower()
                private_patterns = ["tasks_private", "holdout", "/users/", "/home/"]
                for p in private_patterns:
                    if p in row_str:
                        errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

                # Resolve task in public split to check type
                task_paths = list(TASKS_DIR.glob(f"*/{task_id}.json"))
                if not task_paths:
                    errors.append(f"Row {idx} ({task_id}): Id not found in public tasks")
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

            # Unique IDs check
            if len(ids) != len(set(ids)):
                errors.append("Duplicate IDs found in submission CSV")

            if len(ids) < 3:
                errors.append(f"Row count is {len(ids)}, expected at least 3")

            if vulnerable_count == 0:
                errors.append("Sample submission must contain at least one vulnerable task")
            if denial_count == 0:
                errors.append("Sample submission must contain at least one denial control")
            if authorized_allow_count == 0:
                errors.append("Sample submission must contain at least one authorized-allow control")

    except Exception as e:
        errors.append(f"Failed to read CSV file: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    result = validate_sample_csv(CSV_PATH)
    if not result["passed"]:
        print("Kaggle sample submission CSV validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle sample submission CSV validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
