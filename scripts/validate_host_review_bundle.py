#!/usr/bin/env python3
"""Validate the built host review bundle."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Add project root to python path to allow importing scripts
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.build_host_review_bundle import check_private_markers, DENY_PREFIXES
from scripts.check_claim_boundary import _scan_text_file

REQUIRED_FILES = [
    "docs/host-review-package.md",
    "platform/kaggle/sample_submission.csv",
    "platform/kaggle/sample_submission.json",
    "docs/host-facing-one-page-summary.md",
    "platform/kaggle/README.md",
    "platform/kaggle/rules-template.md",
    "platform/kaggle/competition-page-draft.md",
    "platform/kaggle/faq.md",
    "platform/kaggle/dry-run-bundle/manifest.json",
    "platform/kaggle/dry-run-bundle/sample_submission.csv",
    "platform/kaggle/toy_solution_file.csv",
]


def validate_bundle(bundle_dir: Path) -> dict:
    errors = []

    # 1. manifest.json existence and parsing
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.is_file():
        errors.append(f"manifest.json is missing in bundle directory: {bundle_dir}")
        return {"passed": False, "errors": errors}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Failed to parse manifest.json: {e}")
        return {"passed": False, "errors": errors}

    # Check manifest format
    if manifest.get("schema_version") != "host-review-bundle-manifest-v1":
        errors.append(f"Unexpected manifest schema version: {manifest.get('schema_version')}")

    # Check commit SHA format
    source_commit = manifest.get("source_commit")
    if not source_commit:
        errors.append("manifest.json is missing source_commit")
    elif not re.match(r"^[0-9a-fA-F]{40}$", source_commit) and source_commit != "unknown":
        errors.append(f"source_commit must be a 40-character hex SHA, got '{source_commit}'")

    # Check timestamp format
    created_at = manifest.get("created_at_utc")
    if not created_at:
        errors.append("manifest.json is missing created_at_utc")
    elif not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$", created_at):
        errors.append(f"created_at_utc must be ISO-8601 UTC format (e.g. YYYY-MM-DDTHH:MM:SSZ), got '{created_at}'")

    # Check claim boundary matches approved wording
    claim_boundary = manifest.get("claim_boundary")
    expected_claim_boundary = "host-review only; no platform acceptance, hosted leaderboard operation, or external validation."
    if claim_boundary != expected_claim_boundary:
        errors.append(f"claim_boundary mismatch. Expected '{expected_claim_boundary}', got '{claim_boundary}'")

    files = manifest.get("files", [])
    if not files:
        errors.append("manifest.json contains no files list")
        return {"passed": False, "errors": errors}

    manifest_paths = set()

    # 2. Check each file listed in the manifest
    for f_info in files:
        rel_path = f_info.get("path")
        expected_sha = f_info.get("sha256")
        expected_bytes = f_info.get("bytes")

        if not rel_path:
            errors.append("File entry in manifest missing 'path'")
            continue

        manifest_paths.add(rel_path)

        # - a manifest path is absolute
        if rel_path.startswith("/") or rel_path.startswith("\\") or (len(rel_path) > 1 and rel_path[1] == ":"):
            errors.append(f"Manifest path is absolute: {rel_path}")
            continue

        # - any path starts with/contains denied prefixes
        norm_path = Path(rel_path).as_posix()
        parts = norm_path.split("/")
        for deny in DENY_PREFIXES:
            if "/" in deny:
                if norm_path == deny or norm_path.startswith(deny + "/") or f"/{deny}/" in f"/{norm_path}/":
                    errors.append(f"File path contains denied prefix '{deny}': {rel_path}")
            else:
                if deny in parts:
                    errors.append(f"File path contains denied component '{deny}': {rel_path}")

        # - file exists on disk
        actual_file_path = bundle_dir / rel_path
        if not actual_file_path.is_file():
            errors.append(f"File in manifest does not exist in bundle: {rel_path}")
            continue

        # - file size and hash match
        actual_bytes = actual_file_path.stat().st_size
        if actual_bytes != expected_bytes:
            errors.append(f"File size mismatch for {rel_path}: expected {expected_bytes}, got {actual_bytes}")

        h = hashlib.sha256()
        h.update(actual_file_path.read_bytes())
        actual_sha = h.hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"File hash mismatch for {rel_path}: expected {expected_sha}, got {actual_sha}")

        # - check private markers
        if not rel_path.startswith("tests/"):
            marker_errors = check_private_markers(actual_file_path)
            if marker_errors:
                for err in marker_errors:
                    errors.append(f"{rel_path}: {err}")

        # - check forbidden claim boundary text
        if actual_file_path.suffix.lower() in [".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml"]:
            if not rel_path.startswith("tests/") and not rel_path.startswith("docs/reviews/"):
                hits = _scan_text_file(actual_file_path)
                for line_number, line, phrase in hits:
                    errors.append(
                        f"{rel_path}:L{line_number}: Forbidden claim boundary phrase '{phrase}' "
                        f"outside allowed context: '{line.strip()}'"
                    )

    # Check for prohibited symlinks in the bundle directory
    for path in bundle_dir.rglob("*"):
        if path.is_symlink():
            errors.append(f"Symlinks are prohibited inside the review bundle: {path.relative_to(bundle_dir)}")

    # Check for unmanifested extra files in the bundle directory
    actual_paths = {
        str(path.relative_to(bundle_dir).as_posix())
        for path in bundle_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json" and path.name != "HOST_PACKET_CHECKSUMS.sha256"
    }

    missing_from_manifest = sorted(actual_paths - manifest_paths)
    if missing_from_manifest:
        errors.append(
            "Bundle contains files not listed in manifest: "
            + ", ".join(missing_from_manifest[:20])
        )

    # 3. Check for required host docs
    for req in REQUIRED_FILES:
        if req not in manifest_paths:
            errors.append(f"Required file is missing from the bundle: {req}")

    # 4. Run embedded Kaggle validators inside the bundle directory
    if len(errors) == 0:
        # Validate sample submission in bundle
        sub_script = bundle_dir / "scripts/validate_kaggle_sample_submission.py"
        sub_csv = bundle_dir / "platform/kaggle/sample_submission.csv"
        sub_tasks = bundle_dir / "tasks"
        if sub_script.is_file() and sub_csv.is_file():
            res = subprocess.run(
                [sys.executable, str(sub_script), "--csv", str(sub_csv), "--tasks-dir", str(sub_tasks), "--require-existing-findings"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if res.returncode != 0:
                errors.append(f"Kaggle sample submission validator failed inside bundle:\n{res.stdout}")

        # Validate dry run bundle in bundle
        dry_script = bundle_dir / "scripts/validate_kaggle_dry_run_bundle.py"
        dry_dir = bundle_dir / "platform/kaggle/dry-run-bundle"
        if dry_script.is_file() and dry_dir.is_dir():
            res = subprocess.run(
                [sys.executable, str(dry_script), "--bundle-dir", str(dry_dir), "--tasks-dir", str(sub_tasks)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if res.returncode != 0:
                errors.append(f"Kaggle dry-run bundle validator failed inside bundle:\n{res.stdout}")

        # Validate toy solution file in bundle
        toy_script = bundle_dir / "scripts/validate_kaggle_toy_solution_file.py"
        toy_csv = bundle_dir / "platform/kaggle/toy_solution_file.csv"
        if toy_script.is_file() and toy_csv.is_file():
            res = subprocess.run(
                [sys.executable, str(toy_script), "--csv", str(toy_csv), "--tasks-dir", str(sub_tasks)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if res.returncode != 0:
                errors.append(f"Kaggle toy solution validator failed inside bundle:\n{res.stdout}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Validate the built host review bundle.")
    parser.add_argument("--bundle-dir", default="dist/authzbench-saas-host-review", help="Path to bundle directory.")
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir)
    result = validate_bundle(bundle_dir)
    if not result["passed"]:
        print("Host review bundle validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Host review bundle validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
