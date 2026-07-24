"""Deterministic integrity manifests for completed AuthZBench run directories.

The manifest is a local content-consistency checksum. It is not a signature,
timestamp, custody attestation, model-identity proof, or eligibility decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Iterable

from authzbench.core import stable_json_sha256


MANIFEST_FILENAME = "run-bundle-manifest.json"
MANIFEST_SCHEMA_VERSION = "authzbench-run-bundle-manifest-v1"
VALIDATION_SCHEMA_VERSION = "authzbench-run-bundle-validation-v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CLAIM_BOUNDARY = (
    "Local content-consistency checksum only; not a signature, timestamp, "
    "custody attestation, model-identity proof, or eligibility decision."
)
MANIFEST_FIELDS = {
    "schema_version",
    "bundle_root",
    "requirements",
    "files",
    "file_count",
    "total_bytes",
    "claim_boundary",
    "bundle_sha256",
}


class RunBundleError(ValueError):
    """A stable, user-facing run-bundle build error."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _is_safe_relative_path(value: Any) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _is_safe_glob(value: Any) -> bool:
    return _is_safe_relative_path(value)


def _normalize_requirements(
    required_paths: Iterable[str], required_globs: Iterable[str]
) -> dict[str, list[str]]:
    exact_paths = list(required_paths)
    globs = list(required_globs)
    for value in exact_paths:
        if not _is_safe_relative_path(value):
            raise RunBundleError("invalid_required_path", f"unsafe required path: {value!r}")
        if value == MANIFEST_FILENAME:
            raise RunBundleError(
                "invalid_required_path",
                f"the excluded manifest cannot be a required path: {value!r}",
            )
    for value in globs:
        if not _is_safe_glob(value):
            raise RunBundleError("invalid_required_glob", f"unsafe required glob: {value!r}")
    return {
        "exact_paths": sorted(set(exact_paths)),
        "globs": sorted(set(globs)),
    }


def _hash_regular_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    try:
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode):
            raise RunBundleError("symlink_present", f"symlink is not allowed: {path}")
        if not stat.S_ISREG(before.st_mode):
            raise RunBundleError("non_regular_path", f"non-regular path is not allowed: {path}")

        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise RunBundleError("non_regular_path", f"non-regular path is not allowed: {path}")
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    size += len(chunk)
                    digest.update(chunk)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        after = path.lstat()
    except RunBundleError:
        raise
    except OSError as exc:
        raise RunBundleError("bundle_file_unreadable", f"cannot read {path}: {exc}") from exc

    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_opened = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_opened or identity_opened != identity_after or size != after.st_size:
        raise RunBundleError("bundle_file_changed_during_scan", f"file changed while hashing: {path}")
    return size, digest.hexdigest()


def _scan_bundle(root: Path) -> list[dict[str, Any]]:
    if root.is_symlink():
        raise RunBundleError("bundle_root_symlink", f"bundle root cannot be a symlink: {root}")
    if not root.exists():
        raise RunBundleError("bundle_root_missing", f"bundle directory does not exist: {root}")
    if not root.is_dir():
        raise RunBundleError("bundle_root_not_directory", f"bundle root is not a directory: {root}")

    entries: list[dict[str, Any]] = []

    def on_walk_error(exc: OSError) -> None:
        raise RunBundleError("bundle_path_unreadable", str(exc)) from exc

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=on_walk_error):
        current_path = Path(current)
        dirnames.sort()
        filenames.sort()

        for dirname in dirnames:
            directory = current_path / dirname
            if directory.is_symlink():
                relative = directory.relative_to(root).as_posix()
                raise RunBundleError("symlink_present", f"symlink is not allowed: {relative}")

        for filename in filenames:
            path = current_path / filename
            relative = path.relative_to(root).as_posix()
            if relative == MANIFEST_FILENAME:
                continue
            if not _is_safe_relative_path(relative):
                raise RunBundleError("unsafe_bundle_path", f"unsafe bundle path: {relative!r}")
            if path.is_symlink():
                raise RunBundleError("symlink_present", f"symlink is not allowed: {relative}")
            size, digest = _hash_regular_file(path)
            entries.append({"path": relative, "size_bytes": size, "sha256": digest})

    entries.sort(key=lambda entry: entry["path"])
    return entries


def _requirement_findings(
    paths: set[str], requirements: dict[str, list[str]]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for required in requirements["exact_paths"]:
        if required not in paths:
            findings.append(
                {"severity": "error", "code": "required_path_missing", "path": required}
            )
    for pattern in requirements["globs"]:
        if not any(fnmatchcase(path, pattern) for path in paths):
            findings.append(
                {"severity": "error", "code": "required_glob_unmatched", "glob": pattern}
            )
    return findings


def _bundle_digest_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "bundle_sha256"}


def build_run_bundle_manifest(
    bundle_root: str | Path,
    *,
    required_paths: Iterable[str] = ("summary.json",),
    required_globs: Iterable[str] = (),
) -> dict[str, Any]:
    """Create a deterministic manifest without replacing an existing one."""
    root = Path(bundle_root)
    manifest_path = root / MANIFEST_FILENAME
    if manifest_path.exists() or manifest_path.is_symlink():
        raise RunBundleError(
            "manifest_already_exists",
            f"refusing to overwrite existing manifest: {manifest_path}",
        )

    requirements = _normalize_requirements(required_paths, required_globs)
    files = _scan_bundle(root)
    requirement_findings = _requirement_findings(
        {entry["path"] for entry in files}, requirements
    )
    if requirement_findings:
        codes = ", ".join(finding["code"] for finding in requirement_findings)
        raise RunBundleError("required_evidence_missing", codes)

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "bundle_root": ".",
        "requirements": requirements,
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(entry["size_bytes"] for entry in files),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    manifest["bundle_sha256"] = stable_json_sha256(_bundle_digest_payload(manifest))

    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    try:
        with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise RunBundleError(
            "manifest_already_exists",
            f"refusing to overwrite existing manifest: {manifest_path}",
        ) from exc
    except OSError as exc:
        raise RunBundleError("manifest_write_failed", f"cannot write {manifest_path}: {exc}") from exc
    return manifest


def _finding(code: str, **details: Any) -> dict[str, Any]:
    return {"severity": "error", "code": code, **details}


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateKeyError as exc:
        return None, [_finding("manifest_duplicate_key", detail=str(exc))]
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, [_finding("manifest_invalid_json", detail=str(exc))]
    except OSError as exc:
        return None, [_finding("manifest_unreadable", detail=str(exc))]
    if not isinstance(loaded, dict):
        return None, [_finding("manifest_must_be_object")]
    return loaded, []


def _validate_manifest_structure(
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]] | None, list[dict[str, Any]] | None]:
    findings: list[dict[str, Any]] = []
    if set(manifest) != MANIFEST_FIELDS:
        findings.append(_finding("manifest_fields_invalid"))
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        findings.append(_finding("manifest_schema_version_invalid"))
    if manifest.get("bundle_root") != ".":
        findings.append(_finding("manifest_bundle_root_invalid"))

    requirements = manifest.get("requirements")
    normalized_requirements: dict[str, list[str]] | None = None
    if not isinstance(requirements, dict):
        findings.append(_finding("manifest_requirements_invalid"))
    else:
        if set(requirements) != {"exact_paths", "globs"}:
            findings.append(_finding("manifest_requirement_fields_invalid"))
        exact_paths = requirements.get("exact_paths")
        globs = requirements.get("globs")
        if not isinstance(exact_paths, list) or not all(isinstance(item, str) for item in exact_paths):
            findings.append(_finding("manifest_required_paths_invalid"))
        elif any(not _is_safe_relative_path(item) or item == MANIFEST_FILENAME for item in exact_paths):
            findings.append(_finding("manifest_required_path_unsafe"))
        elif exact_paths != sorted(set(exact_paths)):
            findings.append(_finding("manifest_required_paths_not_sorted_unique"))
        elif not isinstance(globs, list) or not all(isinstance(item, str) for item in globs):
            findings.append(_finding("manifest_required_globs_invalid"))
        elif any(not _is_safe_glob(item) for item in globs):
            findings.append(_finding("manifest_required_glob_unsafe"))
        elif globs != sorted(set(globs)):
            findings.append(_finding("manifest_required_globs_not_sorted_unique"))
        else:
            normalized_requirements = {"exact_paths": exact_paths, "globs": globs}

    raw_files = manifest.get("files")
    valid_entries: list[dict[str, Any]] | None = None
    if not isinstance(raw_files, list):
        findings.append(_finding("manifest_files_invalid"))
    else:
        entries: list[dict[str, Any]] = []
        entry_error = False
        for index, entry in enumerate(raw_files):
            if not isinstance(entry, dict):
                findings.append(_finding("manifest_file_entry_invalid", index=index))
                entry_error = True
                continue
            path = entry.get("path")
            size = entry.get("size_bytes")
            digest = entry.get("sha256")
            if set(entry) != {"path", "size_bytes", "sha256"}:
                findings.append(_finding("manifest_file_entry_fields_invalid", index=index))
                entry_error = True
            if not _is_safe_relative_path(path) or path == MANIFEST_FILENAME:
                findings.append(_finding("manifest_file_path_unsafe", index=index))
                entry_error = True
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                findings.append(_finding("manifest_file_size_invalid", index=index))
                entry_error = True
            if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
                findings.append(_finding("manifest_file_sha256_invalid", index=index))
                entry_error = True
            if (
                _is_safe_relative_path(path)
                and path != MANIFEST_FILENAME
                and isinstance(size, int)
                and not isinstance(size, bool)
                and size >= 0
                and isinstance(digest, str)
                and SHA256_PATTERN.fullmatch(digest) is not None
            ):
                entries.append({"path": path, "size_bytes": size, "sha256": digest})

        paths = [entry["path"] for entry in entries]
        if len(entries) == len(raw_files) and paths != sorted(set(paths)):
            findings.append(_finding("manifest_file_paths_not_sorted_unique"))
            entry_error = True
        if not entry_error and len(entries) == len(raw_files):
            valid_entries = entries

        declared_count = manifest.get("file_count")
        if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count < 0:
            findings.append(_finding("manifest_file_count_invalid"))
        elif declared_count != len(raw_files):
            findings.append(_finding("manifest_file_count_mismatch"))

        declared_total = manifest.get("total_bytes")
        if not isinstance(declared_total, int) or isinstance(declared_total, bool) or declared_total < 0:
            findings.append(_finding("manifest_total_bytes_invalid"))
        elif valid_entries is not None and declared_total != sum(entry["size_bytes"] for entry in valid_entries):
            findings.append(_finding("manifest_total_bytes_mismatch"))

    bundle_digest = manifest.get("bundle_sha256")
    if not isinstance(bundle_digest, str) or SHA256_PATTERN.fullmatch(bundle_digest) is None:
        findings.append(_finding("manifest_bundle_sha256_invalid"))
    elif all(key in manifest for key in ("schema_version", "requirements", "files")):
        expected_digest = stable_json_sha256(_bundle_digest_payload(manifest))
        if bundle_digest != expected_digest:
            findings.append(_finding("manifest_bundle_sha256_mismatch"))

    if manifest.get("claim_boundary") != CLAIM_BOUNDARY:
        findings.append(_finding("manifest_claim_boundary_invalid"))
    return findings, normalized_requirements, valid_entries


def validate_run_bundle_manifest(bundle_root: str | Path) -> dict[str, Any]:
    """Validate manifest structure and the complete current directory contents."""
    root = Path(bundle_root)
    manifest_path = root / MANIFEST_FILENAME
    findings: list[dict[str, Any]] = []

    if root.is_symlink():
        findings.append(_finding("bundle_root_symlink"))
    elif not root.exists():
        findings.append(_finding("bundle_root_missing"))
    elif not root.is_dir():
        findings.append(_finding("bundle_root_not_directory"))
    elif manifest_path.is_symlink():
        findings.append(_finding("manifest_symlink"))
    elif not manifest_path.is_file():
        findings.append(_finding("manifest_missing"))

    manifest: dict[str, Any] | None = None
    requirements: dict[str, list[str]] | None = None
    recorded_entries: list[dict[str, Any]] | None = None
    actual_entries: list[dict[str, Any]] | None = None

    if not findings:
        manifest, load_findings = _load_manifest(manifest_path)
        findings.extend(load_findings)
    if manifest is not None:
        structural, requirements, recorded_entries = _validate_manifest_structure(manifest)
        findings.extend(structural)

    if root.exists() and root.is_dir() and not root.is_symlink():
        try:
            actual_entries = _scan_bundle(root)
        except RunBundleError as exc:
            findings.append(_finding(exc.code, detail=exc.detail))

    if actual_entries is not None and recorded_entries is not None:
        actual_by_path = {entry["path"]: entry for entry in actual_entries}
        recorded_by_path = {entry["path"]: entry for entry in recorded_entries}
        for path in sorted(recorded_by_path.keys() - actual_by_path.keys()):
            findings.append(_finding("bundle_file_missing", path=path))
        for path in sorted(actual_by_path.keys() - recorded_by_path.keys()):
            findings.append(_finding("unexpected_bundle_file", path=path))
        for path in sorted(actual_by_path.keys() & recorded_by_path.keys()):
            actual = actual_by_path[path]
            recorded = recorded_by_path[path]
            if actual["size_bytes"] != recorded["size_bytes"]:
                findings.append(_finding("bundle_file_size_mismatch", path=path))
            if actual["sha256"] != recorded["sha256"]:
                findings.append(_finding("bundle_file_sha256_mismatch", path=path))

    if actual_entries is not None and requirements is not None:
        findings.extend(
            _requirement_findings({entry["path"] for entry in actual_entries}, requirements)
        )

    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "bundle": str(root),
        "manifest": MANIFEST_FILENAME,
        "file_count": len(actual_entries) if actual_entries is not None else None,
        "bundle_sha256": manifest.get("bundle_sha256") if manifest is not None else None,
        "findings": findings,
        "passed": not findings,
    }
