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

            # Build public task index
            import json
            task_index = {}
            for t_path in TASKS_DIR.glob("*/*.json"):
                try:
                    t_data = json.loads(t_path.read_text(encoding="utf-8"))
                    t_id = t_data.get("id")
                    if isinstance(t_id, str):
                        task_index[t_id] = t_data
                except Exception:
                    pass

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

                if expected_vulnerable not in ["true", "false"]:
                    errors.append(f"Row {idx} ({task_id}): Invalid expected_vulnerable '{expected_vulnerable}'. Must be true or false")

                if not task_pack_version:
                    errors.append(f"Row {idx} ({task_id}): task_pack_version must be nonempty")

                # Validate Public split tasks exist
                if usage == "Public":
                    task_data = task_index.get(task_id)
                    if not task_data:
                        errors.append(f"Row {idx} ({task_id}): Public task Id not found in tasks/")
                    else:
                        is_vuln_real = task_data.get("expected_vulnerable", False)
                        expected_vuln_bool = (expected_vulnerable == "true")
                        if expected_vuln_bool != is_vuln_real:
                            errors.append(f"Row {idx} ({task_id}): expected_vulnerable mismatch. CSV has {expected_vulnerable}, actual task has {is_vuln_real}")

                        real_control_type = task_data.get("control_type")
                        if is_vuln_real:
                            if control_type:
                                errors.append(f"Row {idx} ({task_id}): Vulnerable public row should have empty control_type, got '{control_type}'")
                        else:
                            if control_type != real_control_type:
                                errors.append(f"Row {idx} ({task_id}): control_type mismatch. CSV has {control_type}, actual task has {real_control_type}")

                    if not oracle_ref.startswith("public-oracle:"):
                        errors.append(f"Row {idx} ({task_id}): Public row oracle_ref must start with 'public-oracle:', got '{oracle_ref}'")
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
