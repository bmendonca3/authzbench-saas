#!/usr/bin/env python3
"""Build and validate the public-safe host review bundle."""

from __future__ import annotations

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


def _git_error(label: str, stderr: str) -> RuntimeError:
    detail = stderr.strip() or "no error output"
    return RuntimeError(f"{label}: {detail}")


def resolve_git_commit(ref_commit: str = "", root: Path = ROOT) -> str:
    requested_ref = ref_commit or "HEAD"
    res = subprocess.run(
        ["git", "rev-parse", "--verify", f"{requested_ref}^{{commit}}"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        raise _git_error(f"Failed to resolve Git ref '{requested_ref}'", res.stderr)
    commit_sha = res.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise RuntimeError(
            f"Resolved Git ref '{requested_ref}' to invalid commit SHA '{commit_sha}'"
        )
    return commit_sha


def get_git_commit(root: Path = ROOT) -> str:
    return resolve_git_commit(root=root)


def get_git_tree_sha(commit_sha: str, root: Path = ROOT) -> str:
    res = subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit_sha}^{{tree}}"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        raise _git_error(
            f"Failed to resolve source tree for commit '{commit_sha}'",
            res.stderr,
        )
    tree_sha = res.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
        raise RuntimeError(f"Resolved invalid source tree SHA '{tree_sha}'")
    return tree_sha


def list_git_tree_entries(commit_sha: str, root: Path = ROOT) -> list[dict[str, str]]:
    res = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", commit_sha],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        raise _git_error(
            f"Failed to list files for commit '{commit_sha}'",
            res.stderr.decode("utf-8", errors="replace"),
        )

    entries: list[dict[str, str]] = []
    for raw_entry in res.stdout.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split()
            rel_path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise RuntimeError(f"Failed to parse Git tree entry: {exc}") from exc
        entries.append(
            {
                "path": rel_path,
                "mode": mode,
                "object_type": object_type,
                "object_sha": object_sha,
            }
        )
    return entries


def read_git_blob(blob_sha: str, root: Path = ROOT) -> bytes:
    res = subprocess.run(
        ["git", "cat-file", "blob", blob_sha],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        raise _git_error(
            f"Failed to read Git blob '{blob_sha}'",
            res.stderr.decode("utf-8", errors="replace"),
        )
    return res.stdout


def is_git_dirty(root: Path = ROOT) -> bool:
    res = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        raise _git_error("Failed to inspect Git working tree", res.stderr)
    return bool(res.stdout.strip())


def get_self_hash() -> str:
    try:
        h = hashlib.sha256()
        h.update(Path(__file__).resolve().read_bytes())
        return h.hexdigest()
    except Exception:
        return "unknown"


def build_bundle(
    output_dir: Path,
    ref_commit: str = "",
    allow_dirty: bool = False,
    created_at_utc: str = "",
    *,
    root: Path = ROOT,
) -> dict:
    files_list = []
    errors = []

    try:
        dirty = is_git_dirty(root)
    except Exception as exc:
        errors.append(str(exc))
        return {"passed": False, "errors": errors, "manifest": {}}
    if dirty and not allow_dirty:
        errors.append(
            "Git repository contains uncommitted changes. "
            "Use --allow-dirty only for an explicit development check; "
            "working-tree changes are never included in the bundle."
        )
        return {"passed": False, "errors": errors, "manifest": {}}

    try:
        requested_ref = ref_commit or "HEAD"
        commit_sha = resolve_git_commit(ref_commit, root)
        tree_sha = get_git_tree_sha(commit_sha, root)
        tree_entries = list_git_tree_entries(commit_sha, root)
    except Exception as exc:
        errors.append(str(exc))
        return {"passed": False, "errors": errors, "manifest": {}}

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    for entry in tree_entries:
        rel_path = entry["path"]

        if not is_allowed_file(rel_path):
            continue

        path_parts = Path(rel_path).parts
        if rel_path.startswith("/") or ".." in path_parts:
            errors.append(f"Git tree contains unsafe bundle path: {rel_path}")
            continue
        if entry["object_type"] != "blob":
            errors.append(
                f"Allowed bundle path is not a Git blob: {rel_path} "
                f"({entry['object_type']})"
            )
            continue
        if entry["mode"] == "120000":
            errors.append(f"Symlinks are prohibited in the host review bundle: {rel_path}")
            continue

        try:
            content = read_git_blob(entry["object_sha"], root)
        except Exception as exc:
            errors.append(f"{rel_path}: {exc}")
            continue

        dest_path = output_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(content)
        dest_path.chmod(0o755 if entry["mode"] == "100755" else 0o644)

        if not rel_path.startswith("tests/"):
            marker_errors = check_private_markers(dest_path)
            if marker_errors:
                errors.extend(f"{rel_path}: {error}" for error in marker_errors)

        file_hash = hashlib.sha256(content).hexdigest()

        files_list.append({
            "path": rel_path,
            "sha256": file_hash,
            "bytes": len(content),
            "git_blob_sha": entry["object_sha"],
            "git_mode": entry["mode"],
        })

    files_list.sort(key=lambda x: x["path"])

    timestamp = (
        created_at_utc
        if created_at_utc
        else datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    manifest = {
        "schema_version": "host-review-bundle-manifest-v1",
        "source_commit": commit_sha,
        "source_ref": requested_ref,
        "source_tree": tree_sha,
        "source_materialization": "git_object_database",
        "working_tree_changes_included": False,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="dist/authzbench-saas-host-review")
    parser.add_argument("--ref", type=str, default="")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Allow an explicit development check from a dirty checkout. "
            "The bundle still materializes only the exact --ref/HEAD commit."
        ),
    )
    parser.add_argument("--created-at-utc", type=str, default="", help="Forced created_at_utc timestamp")
    args = parser.parse_args(argv)

    if args.check:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
            result = build_bundle(
                tmp_path,
                args.ref,
                allow_dirty=args.allow_dirty,
                created_at_utc="2026-06-16T00:00:00Z",
            )
            if not result["passed"]:
                print("Host review bundle validation FAILED:", file=sys.stderr)
                for err in result["errors"]:
                    print(f"- {err}", file=sys.stderr)
                return 1
            print("Host review bundle check PASSED (temp build succeeded).")
            return 0

    out_path = Path(args.output)
    result = build_bundle(
        out_path,
        args.ref,
        allow_dirty=args.allow_dirty,
        created_at_utc=args.created_at_utc,
    )
    if not result["passed"]:
        print("Host review bundle build FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        return 1
    print(f"Host review bundle successfully built at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
