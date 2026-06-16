#!/usr/bin/env python3
"""Build and validate the public-safe host review bundle."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWLIST = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    ".python-version",
    "requirements.lock",
    "Dockerfile",
    "docker-compose.yml",
    "authzbench",
    "apps",
    "tasks",
    "examples",
    "scripts",
    "tests",
    "baselines",
    "artifact",
    "docs",
    "platform/kaggle",
]

DENY_PREFIXES = [
    "tasks_private",
    "results",
    "captures",
    "docs/reviews",
    "harbor-jobs",
    ".harbor",
    ".handoff",
    ".git",
]

DENY_EXTENSIONS = [
    ".pem",
    ".key",
    ".p12",
    ".pfx",
]


def is_allowed_file(rel_path: str) -> bool:
    # Must start with one of the allowlist prefixes
    if not any(rel_path.startswith(p) for p in ALLOWLIST):
        return False
    # Must not contain any deny prefixes as components or sub-paths
    norm_path = Path(rel_path).as_posix()
    parts = norm_path.split("/")
    for deny in DENY_PREFIXES:
        if "/" in deny:
            if norm_path == deny or norm_path.startswith(deny + "/") or f"/{deny}/" in f"/{norm_path}/":
                return False
        else:
            if deny in parts:
                return False
    # Must not end with denied extensions
    if any(rel_path.endswith(ext) for ext in DENY_EXTENSIONS):
        return False
    # Exclude env files
    basename = os.path.basename(rel_path)
    if basename == ".env" or basename.startswith(".env.") or basename.endswith(".env"):
        return False
    return True


def check_private_markers(path: Path) -> list:
    errors = []
    # Only scan text files
    if path.suffix.lower() not in [".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml", ".sh", ".csv"]:
        return []

    try:
        content = path.read_text(encoding="utf-8")
        # Check sk-... api keys
        if re.search(r"sk-[a-zA-Z0-9]{32,}", content):
            errors.append(f"Contains OpenAI API key marker: {path.name}")
        # Check ghp_... github tokens
        if re.search(r"ghp_[a-zA-Z0-9]{36,}", content):
            errors.append(f"Contains GitHub token marker: {path.name}")
        # Check user absolute local paths (e.g. /Users/username)
        user_home = str(Path.home())
        target_user_path = "/Users/" + "brianmendonca"
        if user_home in content or target_user_path in content:
            errors.append(f"Contains absolute local path: {path.name}")
    except UnicodeDecodeError:
        pass
    return errors


def build_bundle(output_dir: Path, ref_commit: str = "") -> dict:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    files_list = []
    errors = []

    # Gather tracked files
    for root_dir, dirs, files in os.walk(ROOT):
        # Skip hidden directories like .git
        if ".git" in dirs:
            dirs.remove(".git")

        for file in files:
            file_path = Path(root_dir) / file
            rel_path = str(file_path.relative_to(ROOT))

            if not is_allowed_file(rel_path):
                continue

            # Verify private markers
            marker_errors = check_private_markers(file_path)
            if marker_errors:
                errors.extend(marker_errors)

            # Copy file
            dest_path = output_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)

            # Hash file
            h = hashlib.sha256()
            h.update(file_path.read_bytes())
            file_hash = h.hexdigest()

            files_list.append({
                "path": rel_path,
                "sha256": file_hash,
                "bytes": file_path.stat().st_size
            })

    # Sort files_list for determinism
    files_list.sort(key=lambda x: x["path"])

    manifest = {
        "schema_version": "host-review-bundle-manifest-v1",
        "source_commit": ref_commit,
        "created_at_utc": "2026-06-16T00:00:00Z",
        "claim_boundary": "host-review only; no platform acceptance, hosted leaderboard operation, or external validation.",
        "files": files_list,
        "denied_prefixes_checked": DENY_PREFIXES,
        "privacy_scan_passed": len(errors) == 0
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {"passed": len(errors) == 0, "errors": errors, "manifest": manifest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="dist/authzbench-saas-host-review")
    parser.add_argument("--ref", type=str, default="")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
            result = build_bundle(tmp_path, args.ref)
            if not result["passed"]:
                print("Host review bundle validation FAILED:", file=sys.stderr)
                for err in result["errors"]:
                    print(f"- {err}", file=sys.stderr)
                sys.exit(1)
            print("Host review bundle check PASSED (temp build succeeded).")
            sys.exit(0)
    else:
        out_path = Path(args.output)
        result = build_bundle(out_path, args.ref)
        if not result["passed"]:
            print("Host review bundle build FAILED:", file=sys.stderr)
            for err in result["errors"]:
                print(f"- {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Host review bundle successfully built at {args.output}")
        sys.exit(0)


if __name__ == "__main__":
    main()
