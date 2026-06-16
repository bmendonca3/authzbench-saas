#!/usr/bin/env python3
"""Validator for platform/kaggle/toy_solution_file.csv."""

import argparse
import csv
import sys
from pathlib import Path

# Add scripts/ to sys.path so we can import helpers when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_public_task_index import load_public_task_index

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "platform/kaggle/toy_solution_file.csv"
TASKS_DIR = ROOT / "tasks"


def validate_toy_solution(csv_path: Path, tasks_dir: Path) -> dict:
    errors = []
    if not csv_path.is_file():
        return {"passed": False, "errors": [f"CSV file does not exist: {csv_path}"]}
    if not tasks_dir.is_dir():
        return {"passed": False, "errors": [f"Tasks directory does not exist: {tasks_dir}"]}

    try:
        task_index = load_public_task_index(tasks_dir)
    except Exception as e:
        return {"passed": False, "errors": [f"Failed to load task index: {e}"]}

    try:
        with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            expected_headers = ["Id", "Usage", "expected_vulnerable", "control_type", "oracle_ref", "task_pack_version"]
            if headers != expected_headers:
                errors.append(f"Invalid CSV headers: {headers}. Expected: {expected_headers}")

            vulnerable_public_count = 0
            denial_public_count = 0
            authorized_allow_public_count = 0
            private_placeholder_count = 0
            ids = []

            for idx, row in enumerate(reader, start=2):
                if not row or all(not val for val in row.values()):
                    errors.append(f"Row {idx}: Blank row detected")
                    continue

                if None in row or any(k is None for k in row.keys()):
                    errors.append(f"Row {idx}: Contains extra unnamed columns")
                    continue

                task_id = row.get("Id")
                usage = row.get("Usage")
                expected_vulnerable = row.get("expected_vulnerable")
                control_type = row.get("control_type")
                oracle_ref = row.get("oracle_ref")
                task_pack_version = row.get("task_pack_version")

                if task_id is None or usage is None or expected_vulnerable is None or control_type is None or oracle_ref is None or task_pack_version is None:
                    errors.append(f"Row {idx}: Missing one or more columns")
                    continue

                task_id = task_id.strip()
                usage = usage.strip()
                expected_vulnerable = expected_vulnerable.strip()
                control_type = control_type.strip()
                oracle_ref = oracle_ref.strip()
                task_pack_version = task_pack_version.strip()

                if not task_id:
                    errors.append(f"Row {idx}: Missing Id")
                    continue

                if task_id in ids:
                    errors.append(f"Row {idx}: Duplicate task Id '{task_id}' in solution file")
                ids.append(task_id)

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
                        is_vuln_real = task_data.get("expected_vulnerable")
                        expected_vuln_bool = (expected_vulnerable == "true")
                        if expected_vuln_bool != is_vuln_real:
                            errors.append(f"Row {idx} ({task_id}): expected_vulnerable mismatch. CSV has {expected_vulnerable}, actual task has {is_vuln_real}")

                        real_control_type = task_data.get("control_type")
                        if is_vuln_real:
                            if control_type:
                                errors.append(f"Row {idx} ({task_id}): Vulnerable public row should have empty control_type, got '{control_type}'")
                            vulnerable_public_count += 1
                        else:
                            if control_type != real_control_type:
                                errors.append(f"Row {idx} ({task_id}): control_type mismatch. CSV has '{control_type}', actual task has '{real_control_type}'")
                            if control_type == "denial":
                                denial_public_count += 1
                            elif control_type == "authorized_allow":
                                authorized_allow_public_count += 1

                    if not oracle_ref.startswith("public-oracle:"):
                        errors.append(f"Row {idx} ({task_id}): Public row oracle_ref must start with 'public-oracle:', got '{oracle_ref}'")
                else:
                    # Private placeholder rows
                    if task_id != "private-row-placeholder":
                        errors.append(f"Row {idx} ({task_id}): Non-placeholder private ID found in toy solutions")
                    if oracle_ref != "host-controlled":
                        errors.append(f"Row {idx} ({task_id}): Private placeholder row oracle_ref must be 'host-controlled'")
                    if expected_vulnerable != "false":
                        errors.append(f"Row {idx} ({task_id}): Private placeholder row expected_vulnerable must be false")
                    if control_type != "denial":
                        errors.append(f"Row {idx} ({task_id}): Private placeholder row control_type must be denial")
                    private_placeholder_count += 1

                # Leakage / private details checks
                row_str = f"{task_id} {oracle_ref} {task_pack_version}".lower()
                private_patterns = ["tasks_private", "holdout", "private route", "private seed", "/users/", "/home/"]
                for p in private_patterns:
                    if p in row_str:
                        errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

            if vulnerable_public_count < 1:
                errors.append(f"Toy solution file must contain at least one vulnerable public row, found {vulnerable_public_count}")
            if denial_public_count < 1:
                errors.append(f"Toy solution file must contain at least one denial public control row, found {denial_public_count}")
            if authorized_allow_public_count < 1:
                errors.append(f"Toy solution file must contain at least one authorized-allow public control row, found {authorized_allow_public_count}")
            if private_placeholder_count != 1:
                errors.append(f"Toy solution file must contain exactly one private placeholder row, found {private_placeholder_count}")

    except Exception as e:
        errors.append(f"Failed to read CSV: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Validate Kaggle toy solution file.")
    parser.add_argument("--csv", type=str, default=str(CSV_PATH), help="Path to solution CSV file")
    parser.add_argument("--tasks-dir", type=str, default=str(TASKS_DIR), help="Path to tasks directory")
    args = parser.parse_args()

    result = validate_toy_solution(Path(args.csv), Path(args.tasks_dir))
    if not result["passed"]:
        print("Kaggle toy solution file validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle toy solution file validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
