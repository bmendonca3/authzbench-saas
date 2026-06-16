#!/usr/bin/env python3
"""Validator for the platform/kaggle/dry-run-bundle/ directory."""

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
BUNDLE_DIR = ROOT / "platform/kaggle/dry-run-bundle"
TASKS_DIR = ROOT / "tasks"


def validate_dry_run_bundle(bundle_dir: Path, tasks_dir: Path) -> dict:
    errors = []
    if not bundle_dir.is_dir():
        return {"passed": False, "errors": [f"Bundle directory does not exist: {bundle_dir}"]}
    if not tasks_dir.is_dir():
        return {"passed": False, "errors": [f"Tasks directory does not exist: {tasks_dir}"]}

    try:
        task_index = load_public_task_index(tasks_dir)
    except Exception as e:
        return {"passed": False, "errors": [f"Failed to load task index: {e}"]}

    csv_path = bundle_dir / "sample_submission.csv"
    manifest_path = bundle_dir / "manifest.json"

    if not csv_path.is_file():
        errors.append(f"Missing sample_submission.csv in bundle: {csv_path}")
    if not manifest_path.is_file():
        errors.append(f"Missing manifest.json in bundle: {manifest_path}")

    manifest_tasks = {}
    expected_shapes = []

    # Validate manifest
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("leaderboard_eligible") is not False:
                errors.append("manifest.json must have leaderboard_eligible: false")
            if manifest.get("split") != "public":
                errors.append(f"manifest.json split must be 'public', got {manifest.get('split')}")
            if manifest.get("csv") != "sample_submission.csv":
                errors.append(f"manifest.json csv file must be 'sample_submission.csv', got {manifest.get('csv')}")

            manifest_tasks_list = manifest.get("tasks", [])
            if not isinstance(manifest_tasks_list, list):
                errors.append("manifest.json tasks must be a list")
            else:
                for mt in manifest_tasks_list:
                    m_id = mt.get("Id")
                    if not m_id:
                        errors.append("manifest.json task missing Id")
                        continue
                    manifest_tasks[m_id] = mt

            expected_shapes = manifest.get("expected_shape_files", [])
            if not isinstance(expected_shapes, list):
                errors.append("manifest.json expected_shape_files must be a list")
            else:
                for shape_file in expected_shapes:
                    try:
                        resolved_shape = resolve_relative_inside(bundle_dir, shape_file, label="expected_shape_file")
                        if not resolved_shape.is_file():
                            errors.append(f"Expected shape file does not exist in bundle: {shape_file}")
                    except ValueError as ve:
                        errors.append(f"manifest.json expected_shape_file error: {ve}")

        except Exception as e:
            errors.append(f"Failed to parse manifest.json: {e}")

    # Validate CSV and referenced submissions
    if csv_path.is_file():
        try:
            csv_tasks = {}
            with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                if headers != ["Id", "finding_path", "notes"]:
                    errors.append(f"Invalid CSV headers: {headers}")

                vulnerable_count = 0
                denial_count = 0
                authorized_allow_count = 0

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
                        errors.append(f"Row {idx}: Missing required fields")
                        continue

                    task_id = task_id.strip()
                    finding_path = finding_path.strip()
                    notes = notes.strip()

                    if not task_id:
                        errors.append(f"Row {idx}: Missing Id")
                        continue

                    if task_id in csv_tasks:
                        errors.append(f"Row {idx}: Duplicate task Id '{task_id}' in CSV")
                    csv_tasks[task_id] = finding_path

                    # Check private/leakage patterns
                    row_str = f"{task_id} {finding_path} {notes}".lower()
                    private_patterns = ["tasks_private", "holdout", "private route", "private seed", "raw private", "/users/", "/home/"]
                    for p in private_patterns:
                        if p in row_str:
                            errors.append(f"Row {idx} ({task_id}): Contains forbidden private substring '{p}'")

                    # Check submission JSON exists
                    if finding_path:
                        expected_normalized_path = f"submissions/{task_id}/submission.json"
                        if finding_path != expected_normalized_path:
                            errors.append(
                                f"Row {idx} ({task_id}): finding_path is not normalized. "
                                f"Expected '{expected_normalized_path}', got '{finding_path}'"
                            )

                        try:
                            sub_path = resolve_relative_inside(bundle_dir, finding_path, label="finding_path")
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
                        except ValueError as ve:
                            errors.append(f"Row {idx} ({task_id}): {ve}")

                    # Check type in public tasks
                    task_data = task_index.get(task_id)
                    if not task_data:
                        errors.append(f"Row {idx} ({task_id}): Task Id not found in public tasks")
                    else:
                        is_vulnerable = task_data.get("expected_vulnerable")
                        control_type = task_data.get("control_type")
                        if is_vulnerable:
                            vulnerable_count += 1
                        elif control_type == "denial":
                            denial_count += 1
                        elif control_type == "authorized_allow":
                            authorized_allow_count += 1

                if vulnerable_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one vulnerable task, found {vulnerable_count}")
                if denial_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one denial control, found {denial_count}")
                if authorized_allow_count != 1:
                    errors.append(f"Dry-run bundle must contain exactly one authorized-allow control, found {authorized_allow_count}")

                # Parity checks between manifest and CSV
                csv_ids = set(csv_tasks.keys())
                manifest_ids = set(manifest_tasks.keys())

                missing_in_manifest = csv_ids - manifest_ids
                if missing_in_manifest:
                    errors.append(f"Tasks in CSV missing from manifest.json: {missing_in_manifest}")

                missing_in_csv = manifest_ids - csv_ids
                if missing_in_csv:
                    errors.append(f"Tasks in manifest.json missing from CSV: {missing_in_csv}")

                for t_id, mt in manifest_tasks.items():
                    if t_id in csv_tasks:
                        if mt.get("finding_path") != csv_tasks[t_id]:
                            errors.append(
                                f"Task '{t_id}' finding_path mismatch: manifest has '{mt.get('finding_path')}', CSV has '{csv_tasks[t_id]}'"
                            )

                        task_data = task_index.get(t_id)
                        if task_data:
                            if mt.get("expected_vulnerable") != task_data.get("expected_vulnerable"):
                                errors.append(
                                    f"Task '{t_id}' expected_vulnerable mismatch: manifest has {mt.get('expected_vulnerable')}, task has {task_data.get('expected_vulnerable')}"
                                )
                            m_ct = mt.get("control_type")
                            if m_ct == "":
                                m_ct = None
                            t_ct = task_data.get("control_type")
                            if t_ct == "":
                                t_ct = None
                            if m_ct != t_ct:
                                errors.append(
                                    f"Task '{t_id}' control_type mismatch: manifest has '{mt.get('control_type')}', task has '{task_data.get('control_type')}'"
                                )

        except Exception as e:
            errors.append(f"Failed to read CSV: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Validate Kaggle dry-run bundle.")
    parser.add_argument("--bundle-dir", type=str, default=str(BUNDLE_DIR), help="Path to bundle directory")
    parser.add_argument("--tasks-dir", type=str, default=str(TASKS_DIR), help="Path to tasks directory")
    args = parser.parse_args()

    result = validate_dry_run_bundle(Path(args.bundle_dir), Path(args.tasks_dir))
    if not result["passed"]:
        print("Kaggle dry-run bundle validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Kaggle dry-run bundle validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
