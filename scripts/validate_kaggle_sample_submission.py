#!/usr/bin/env python3
"""Validator for platform/kaggle/sample_submission.csv."""

import argparse
import csv
import json
import sys
from pathlib import Path

# Add scripts/ to sys.path so we can import helpers when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from path_validation import resolve_relative_inside
from load_public_task_index import load_public_task_index

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "platform/kaggle/sample_submission.csv"
TASKS_DIR = ROOT / "tasks"


def validate_sample_csv(csv_path: Path, tasks_dir: Path, require_existing_findings: bool = False) -> dict:
    errors = []
    if not csv_path.is_file():
        return {"passed": False, "errors": [f"CSV file does not exist: {csv_path}"]}
    if not tasks_dir.is_dir():
        return {"passed": False, "errors": [f"Tasks directory does not exist: {tasks_dir}"]}

    try:
        task_index = load_public_task_index(tasks_dir)
    except Exception as e:
        return {"passed": False, "errors": [f"Failed to load task index: {e}"]}

    csv_dir = csv_path.parent

    try:
        ids = []
        finding_paths = []
        vulnerable_count = 0
        denial_count = 0
        authorized_allow_count = 0

        with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
            if not lines:
                return {"passed": False, "errors": ["CSV file is empty"]}

            f.seek(0)

            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            if headers != ["Id", "finding_path", "notes"]:
                errors.append(f"Invalid headers: {headers}. Expected: ['Id', 'finding_path', 'notes']")

            for idx, row in enumerate(reader, start=2):
                if not row or all(not val for val in row.values()):
                    errors.append(f"Row {idx}: Blank row detected")
                    continue

                if None in row or any(k is None for k in row.keys()):
                    errors.append(f"Row {idx}: Contains extra unnamed columns")
                    continue

                task_id = row.get("Id")
                finding_path = row.get("finding_path")
                notes = row.get("notes")

                if task_id is None or finding_path is None or notes is None:
                    errors.append(f"Row {idx}: Missing one or more required columns (Id, finding_path, notes)")
                    continue

                if task_id != task_id.strip():
                    errors.append(f"Row {idx}: Id has leading/trailing whitespace: '{task_id}'")
                if finding_path != finding_path.strip():
                    errors.append(f"Row {idx}: finding_path has leading/trailing whitespace: '{finding_path}'")
                if notes != notes.strip():
                    errors.append(f"Row {idx}: notes has leading/trailing whitespace: '{notes}'")

                task_id = task_id.strip()
                finding_path = finding_path.strip()
                notes = notes.strip()

                if not task_id:
                    errors.append(f"Row {idx}: Missing Id")
                    continue

                if task_id in ids:
                    errors.append(f"Row {idx}: Duplicate task Id '{task_id}'")
                ids.append(task_id)

                if not finding_path:
                    errors.append(f"Row {idx} ({task_id}): Missing finding_path")
                else:
                    if finding_path in finding_paths:
                        errors.append(f"Row {idx} ({task_id}): Duplicate finding_path '{finding_path}'")
                    finding_paths.append(finding_path)

                    expected_normalized_path = f"submissions/{task_id}/submission.json"
                    if finding_path != expected_normalized_path:
                        errors.append(
                            f"Row {idx} ({task_id}): finding_path is not normalized. "
                            f"Expected '{expected_normalized_path}', got '{finding_path}'"
                        )

                    try:
                        resolved_path = resolve_relative_inside(csv_dir, finding_path, label="finding_path")
                        if require_existing_findings:
                            if not resolved_path.is_file():
                                errors.append(f"Row {idx} ({task_id}): Finding file does not exist: {finding_path}")
                            else:
                                try:
                                    json.loads(resolved_path.read_text(encoding="utf-8"))
                                except json.JSONDecodeError as exc:
                                    errors.append(f"Row {idx} ({task_id}): Finding file is not valid JSON: {finding_path} ({exc})")
                    except ValueError as ve:
                        errors.append(f"Row {idx} ({task_id}): {ve}")

                # Check private strings
                row_str = f"{task_id} {finding_path} {notes}".lower()
                private_patterns = ["tasks_private", "holdout", "/users/", "/home/"]
                for p in private_patterns:
                    if p in row_str:
                        errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

                # Resolve task in public split to check type
                task_data = task_index.get(task_id)
                if not task_data:
                    errors.append(f"Row {idx} ({task_id}): Id not found in public tasks")
                else:
                    is_vulnerable = task_data.get("expected_vulnerable")
                    control_type = task_data.get("control_type")
                    if is_vulnerable:
                        vulnerable_count += 1
                    elif control_type == "denial":
                        denial_count += 1
                    elif control_type == "authorized_allow":
                        authorized_allow_count += 1

            if len(ids) < 3:
                errors.append(f"Task count is {len(ids)}, expected at least 3")

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
    parser = argparse.ArgumentParser(description="Validate Kaggle sample submission CSV.")
    parser.add_argument("--csv", type=str, default=str(CSV_PATH), help="Path to sample CSV file")
    parser.add_argument("--tasks-dir", type=str, default=str(TASKS_DIR), help="Path to tasks directory")
    parser.add_argument("--require-existing-findings", action="store_true", help="Require referenced finding files to exist")
    args = parser.parse_args()

    result = validate_sample_csv(Path(args.csv), Path(args.tasks_dir), args.require_existing_findings)
    if not result["passed"]:
        print("Kaggle sample submission CSV validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle sample submission CSV validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
