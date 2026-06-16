#!/usr/bin/env python3
"""Build and validate the public-safe host review bundle."""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
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
    "authzbench_harbor",
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
    path_obj = Path(rel_path)
    parts = path_obj.parts

    # Check if the first parts match any ALLOWLIST prefix
    allowed = False
    for allowed_prefix in ALLOWLIST:
        prefix_parts = Path(allowed_prefix).parts
        if len(parts) >= len(prefix_parts) and parts[:len(prefix_parts)] == prefix_parts:
            allowed = True
            break
    if not allowed:
        return False

    # Must not contain any deny prefixes as components
    for deny in DENY_PREFIXES:
        deny_parts = Path(deny).parts
        for i in range(len(parts) - len(deny_parts) + 1):
            if parts[i:i+len(deny_parts)] == deny_parts:
                return False

    # Must not end with denied extensions
    if any(rel_path.endswith(ext) for ext in DENY_EXTENSIONS):
        return False

    # Exclude env files
    basename = path_obj.name
    if basename == ".env" or basename.startswith(".env.") or basename.endswith(".env"):
        return False
    return True


def check_private_markers(path: Path) -> list:
    errors = []
    if path.suffix.lower() not in [".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml", ".sh", ".csv"]:
        return []

    local_path_patterns = (
        re.compile(r"/Users/[A-Za-z0-9._-]+/"),
        re.compile(r"/home/[A-Za-z0-9._-]+/"),
        re.compile(r"C:\\Users\\[A-Za-z0-9._-]+\\", re.IGNORECASE),
    )

    try:
        content = path.read_text(encoding="utf-8")
        if re.search(r"sk-[a-zA-Z0-9]{32,}", content):
            errors.append(f"Contains OpenAI API key marker: {path.name}")
        if re.search(r"ghp_[a-zA-Z0-9]{36,}", content):
            errors.append(f"Contains GitHub token marker: {path.name}")
        user_home = str(Path.home())
        if user_home in content:
            errors.append(f"Contains absolute local path: {path.name}")
        else:
            for pattern in local_path_patterns:
                if pattern.search(content):
                    errors.append(f"Contains absolute local path: {path.name}")
                    break
    except UnicodeDecodeError:
        pass
    return errors


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def is_git_dirty() -> bool:
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return len(res.stdout.strip()) > 0
    except Exception:
        return False


def get_self_hash() -> str:
    try:
        h = hashlib.sha256()
        h.update(Path(__file__).resolve().read_bytes())
        return h.hexdigest()
    except Exception:
        return "unknown"


def build_bundle(output_dir: Path, ref_commit: str = "", allow_dirty: bool = False, created_at_utc: str = "") -> dict:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    files_list = []
    errors = []

    dirty = is_git_dirty()
    if dirty and not allow_dirty:
        errors.append("Git repository contains uncommitted changes. Commit or stash them, or use --allow-dirty.")
        return {"passed": False, "errors": errors, "manifest": {}}

    commit_sha = ref_commit if ref_commit else get_git_commit()

    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        tracked = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception as e:
        errors.append(f"Failed to list git tracked files: {e}")
        return {"passed": False, "errors": errors, "manifest": {}}

    for rel_path in tracked:
        file_path = ROOT / rel_path

        if not is_allowed_file(rel_path):
            continue

        if not rel_path.startswith("tests/"):
            marker_errors = check_private_markers(file_path)
            if marker_errors:
                errors.extend(marker_errors)

        dest_path = output_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)

        h = hashlib.sha256()
        h.update(file_path.read_bytes())
        file_hash = h.hexdigest()

        files_list.append({
            "path": rel_path,
            "sha256": file_hash,
            "bytes": file_path.stat().st_size
        })

    files_list.sort(key=lambda x: x["path"])

    timestamp = created_at_utc if created_at_utc else datetime.datetime.utcnow().isoformat() + "Z"

    manifest = {
        "schema_version": "host-review-bundle-manifest-v1",
        "source_commit": commit_sha,
        "git_dirty": dirty,
        "created_at_utc": timestamp,
        "claim_boundary": "host-review only; no platform acceptance, hosted leaderboard operation, or external validation.",
        "builder_metadata": {
            "python_version": sys.version,
            "platform": sys.platform,
            "builder_script_sha256": get_self_hash(),
        },
        "files": files_list,
        "denied_prefixes_checked": DENY_PREFIXES,
        "privacy_scan_passed": len(errors) == 0
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Generate HOST_PACKET_CHECKSUMS.sha256
    checksums_lines = []
    h_m = hashlib.sha256()
    h_m.update(manifest_path.read_bytes())
    checksums_lines.append(f"{h_m.hexdigest()}  manifest.json")

    for f in files_list:
        checksums_lines.append(f"{f['sha256']}  {f['path']}")

    checksums_path = output_dir / "HOST_PACKET_CHECKSUMS.sha256"
    checksums_path.write_text("\n".join(checksums_lines) + "\n", encoding="utf-8")

    return {"passed": len(errors) == 0, "errors": errors, "manifest": manifest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="dist/authzbench-saas-host-review")
    parser.add_argument("--ref", type=str, default="")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow building bundle with dirty git state")
    parser.add_argument("--created-at-utc", type=str, default="", help="Forced created_at_utc timestamp")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
            result = build_bundle(tmp_path, args.ref, allow_dirty=True, created_at_utc="2026-06-16T00:00:00Z")
            if not result["passed"]:
                print("Host review bundle validation FAILED:", file=sys.stderr)
                for err in result["errors"]:
                    print(f"- {err}", file=sys.stderr)
                sys.exit(1)
            print("Host review bundle check PASSED (temp build succeeded).")
            sys.exit(0)
    else:
        out_path = Path(args.output)
        result = build_bundle(out_path, args.ref, allow_dirty=args.allow_dirty, created_at_utc=args.created_at_utc)
        if not result["passed"]:
            print("Host review bundle build FAILED:", file=sys.stderr)
            for err in result["errors"]:
                print(f"- {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Host review bundle successfully built at {args.output}")
        sys.exit(0)


if __name__ == "__main__":
    main()
