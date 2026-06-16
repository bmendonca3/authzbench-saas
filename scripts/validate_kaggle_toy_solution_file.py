#!/usr/bin/env python3
"""Validator for platform/kaggle/toy_solution_file.csv."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "platform/kaggle/toy_solution_file.csv"
TASKS_DIR = ROOT / "tasks"


def validate_toy_solution(path: Path) -> dict:
    errors = []
    if not path.is_file():
        return {"passed": False, "errors": [f"File does not exist: {path}"]}

    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            expected_headers = ["Id", "Usage", "expected_vulnerable", "control_type", "oracle_ref", "task_pack_version"]
            if headers != expected_headers:
                errors.append(f"Invalid CSV headers: {headers}. Expected: {expected_headers}")

            for idx, row in enumerate(reader, start=2):
                task_id = row.get("Id")
                usage = row.get("Usage")
                expected_vulnerable = row.get("expected_vulnerable")
                control_type = row.get("control_type")
                oracle_ref = row.get("oracle_ref")
                task_pack_version = row.get("task_pack_version")

                if not task_id:
                    errors.append(f"Row {idx}: Missing Id")
                    continue

                if usage not in ["Public", "Private"]:
                    errors.append(f"Row {idx} ({task_id}): Invalid Usage '{usage}'. Must be Public or Private")

                # Validate Public split tasks exist
                if usage == "Public":
                    task_paths = list(TASKS_DIR.glob(f"*/{task_id}.json"))
                    if not task_paths:
                        errors.append(f"Row {idx} ({task_id}): Public task Id not found in tasks/")
                else:
                    # Private placeholder rows
                    if task_id != "private-row-placeholder":
                        errors.append(f"Row {idx} ({task_id}): Non-placeholder private ID found in toy solutions")
                    if oracle_ref != "host-controlled":
                        errors.append(f"Row {idx} ({task_id}): Private placeholder row oracle_ref must be 'host-controlled'")

                # Leakage / private details checks
                row_str = f"{task_id} {oracle_ref} {task_pack_version}".lower()
                private_patterns = ["tasks_private", "holdout", "private route", "private seed", "/users/", "/home/"]
                for p in private_patterns:
                    if p in row_str:
                        errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

    except Exception as e:
        errors.append(f"Failed to read CSV: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    result = validate_toy_solution(CSV_PATH)
    if not result["passed"]:
        print("Kaggle toy solution file validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle toy solution file validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
