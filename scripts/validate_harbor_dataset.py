"""Validate a generated Harbor dataset directory.

Checks that required files exist for each task, that no private manifests
are included, and that the dataset manifest is well-formed.

Usage:
    python3 scripts/validate_harbor_dataset.py \\
        --dataset-dir artifact/harbor-dataset-public-smoke
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json
from authzbench_harbor.redaction import scan_for_violations

REQUIRED_ROOT_FILES = ["dataset.toml", "run_authzbench_saas.yaml", "dataset-manifest.json"]
REQUIRED_TASK_FILES = [
    "task.toml",
    "instruction.md",
    "solution/solve.sh",
    "tests/test.sh",
    "environment/Dockerfile",
    "tests/Dockerfile",
    "verifier/task_manifest.json",
    "tests/task_manifest.json",
]
PRIVATE_INDICATORS = ["tasks_private/holdout", "private_holdout", "split: private"]


def validate_dataset(dataset_dir: Path) -> dict:
    errors = []
    warnings = []

    if not dataset_dir.is_dir():
        return {"passed": False, "errors": [f"dataset directory not found: {dataset_dir}"], "warnings": []}

    for fname in REQUIRED_ROOT_FILES:
        fpath = dataset_dir / fname
        if not fpath.is_file():
            errors.append(f"missing required root file: {fname}")

    manifest_path = dataset_dir / "dataset-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"dataset-manifest.json is not valid JSON: {exc}")
            manifest = {}

        if not manifest.get("schema_version"):
            errors.append("dataset-manifest.json missing schema_version")
        if not isinstance(manifest.get("task_count"), int) or manifest["task_count"] < 1:
            errors.append("dataset-manifest.json task_count must be a positive integer")
        if manifest.get("private_task_count", 0) != 0:
            errors.append("dataset-manifest.json private_task_count must be 0 for public datasets")

        tasks = manifest.get("tasks", [])
        if not tasks:
            errors.append("dataset-manifest.json tasks list is empty")

        task_ids = set()
        for task_entry in tasks:
            task_id = task_entry.get("id")
            if not task_id:
                errors.append("task entry missing id")
                continue
            if task_id in task_ids:
                errors.append(f"duplicate task id: {task_id}")
            task_ids.add(task_id)

            task_subdir = dataset_dir / task_entry.get("harbor_task_dir", "")
            if not task_subdir.is_dir():
                errors.append(f"task directory not found: {task_entry.get('harbor_task_dir')}")
                continue

            for rel in REQUIRED_TASK_FILES:
                fpath = task_subdir / rel
                if not fpath.is_file():
                    errors.append(f"task {task_id}: missing required file: {rel}")

            verifier_manifest_path = task_subdir / "verifier" / "task_manifest.json"
            if verifier_manifest_path.is_file():
                try:
                    task_manifest = json.loads(verifier_manifest_path.read_text(encoding="utf-8"))
                    if task_manifest.get("id") != task_id:
                        errors.append(
                            f"task {task_id}: verifier/task_manifest.json id mismatch: "
                            f"'{task_manifest.get('id')}'"
                        )
                    for indicator in PRIVATE_INDICATORS:
                        if indicator in verifier_manifest_path.read_text(encoding="utf-8"):
                            errors.append(f"task {task_id}: verifier manifest contains private indicator: {indicator}")
                except json.JSONDecodeError:
                    errors.append(f"task {task_id}: verifier/task_manifest.json is not valid JSON")

        violations = scan_for_violations(manifest, "dataset manifest")
        for v in violations:
            warnings.append(v)

    result = {
        "passed": len(errors) == 0,
        "dataset_dir": str(dataset_dir),
        "errors": errors,
        "warnings": warnings,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated Harbor dataset directory")
    parser.add_argument("--dataset-dir", required=True, help="Path to generated Harbor dataset directory")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    result = validate_dataset(dataset_dir)
    print(dump_json(result))
    if not result["passed"]:
        print(f"\nValidation FAILED: {len(result['errors'])} error(s)", file=sys.stderr)
        for err in result["errors"]:
            print(f"  ERROR: {err}", file=sys.stderr)
        return 1
    print(f"Validation passed: {dataset_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
