"""External submission bundle validator.

The plan section 9.4 requires every external submission bundle to ship
as a single directory containing, at minimum:

  submission.json
  score.json
  summary.json
  transcript.json
  target-requests.jsonl   (only when harness_type == "tool-agent")
  metadata.json
  environment.json

This script enforces that structure plus a small set of cross-file
invariants (run ids agree, fingerprint matches the active private pack,
env hash matches the manifest, tool-agent bundles carry
target-requests, no-tools bundles do not, etc.). It is intentionally a
local gate; it does not phone home, fetch, or compute secrets.

Usage:
    python3 scripts/validate_submission_bundle.py path/to/bundle
    python3 scripts/validate_submission_bundle.py path/to/bundle --require-current-pack
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES: tuple[str, ...] = (
    "submission.json",
    "score.json",
    "summary.json",
    "transcript.json",
    "metadata.json",
    "environment.json",
)

TOOL_AGENT_REQUIRED_FILES: tuple[str, ...] = ("target-requests.jsonl",)


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _stable_hash(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _active_pack_fingerprint() -> str | None:
    p = Path("tasks_private/holdout/rotation-metadata.json")
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for pack in data.get("packs", []):
        if pack.get("role") == "active":
            return pack.get("fingerprint_sha256")
    return None


def validate_bundle(bundle: Path, require_current_pack: bool = False) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    files_present: list[str] = []
    files_missing: list[str] = []
    for name in REQUIRED_FILES:
        path = bundle / name
        if path.is_file():
            files_present.append(name)
        else:
            files_missing.append(name)
            findings.append(
                {"severity": "error", "code": "missing_required_file", "file": name}
            )

    submission = _read_json(bundle / "submission.json") if (bundle / "submission.json").is_file() else None
    score = _read_json(bundle / "score.json") if (bundle / "score.json").is_file() else None
    summary = _read_json(bundle / "summary.json") if (bundle / "summary.json").is_file() else None
    transcript = _read_json(bundle / "transcript.json") if (bundle / "transcript.json").is_file() else None
    metadata = _read_json(bundle / "metadata.json") if (bundle / "metadata.json").is_file() else None
    environment = _read_json(bundle / "environment.json") if (bundle / "environment.json").is_file() else None

    if metadata is None and (bundle / "metadata.json").is_file():
        findings.append({"severity": "error", "code": "metadata_must_be_json_object", "file": "metadata.json"})

    harness_type = None
    if isinstance(metadata, dict):
        harness_type = metadata.get("harness_type")
        for required in ("run_id", "benchmark_commit_sha", "harness_type", "split", "agent", "model"):
            if required not in metadata:
                findings.append(
                    {"severity": "error", "code": "metadata_missing_field", "field": required}
                )
    elif (bundle / "metadata.json").is_file():
        findings.append({"severity": "error", "code": "metadata_must_be_object", "file": "metadata.json"})

    target_requests = bundle / "target-requests.jsonl"
    if harness_type in {"tool-agent", "tool_agent", "live-tool-agent"}:
        if not target_requests.is_file():
            findings.append(
                {"severity": "error", "code": "tool_agent_missing_target_requests", "file": "target-requests.jsonl"}
            )
        else:
            line_count = 0
            for line in target_requests.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    findings.append(
                        {"severity": "error", "code": "target_requests_invalid_jsonl", "line": line_count + 1}
                    )
                line_count += 1
            if line_count == 0:
                findings.append({"severity": "error", "code": "target_requests_empty"})
    else:
        if target_requests.is_file():
            findings.append(
                {"severity": "warning", "code": "no_tools_bundle_has_target_requests", "file": "target-requests.jsonl"}
            )

    if isinstance(submission, dict) and "findings" in submission and not isinstance(submission["findings"], list):
        findings.append({"severity": "error", "code": "submission_findings_must_be_list"})

    run_ids: set[str] = set()
    if isinstance(metadata, dict) and metadata.get("run_id"):
        run_ids.add(metadata["run_id"])
    if isinstance(summary, dict) and summary.get("run_id"):
        run_ids.add(summary["run_id"])
    if isinstance(score, dict) and score.get("run_id"):
        run_ids.add(score["run_id"])
    if isinstance(transcript, dict) and transcript.get("run_id"):
        run_ids.add(transcript["run_id"])
    if isinstance(metadata, dict) and isinstance(metadata.get("run_ids"), list):
        for rid in metadata["run_ids"]:
            if isinstance(rid, str):
                run_ids.add(rid)
    if len(run_ids) > 1:
        findings.append(
            {
                "severity": "error",
                "code": "run_id_mismatch",
                "distinct_run_ids": sorted(run_ids),
            }
        )

    if isinstance(metadata, dict):
        private_fingerprint = metadata.get("private_pack_fingerprint_sha256")
        active = _active_pack_fingerprint()
        if private_fingerprint and active and private_fingerprint != active:
            msg = {
                "severity": "error",
                "code": "private_pack_fingerprint_does_not_match_active",
                "submitted": private_fingerprint,
                "active": active,
            }
            findings.append(msg)
            if require_current_pack:
                findings.append(
                    {
                        "severity": "error",
                        "code": "require_current_pack_failed",
                        "detail": "active private pack fingerprint mismatch is fatal under --require-current-pack",
                    }
                )

    if isinstance(environment, dict):
        env_hash = environment.get("environment_hash")
        if not env_hash:
            findings.append({"severity": "warning", "code": "environment_missing_environment_hash"})
    elif (bundle / "environment.json").is_file():
        findings.append({"severity": "error", "code": "environment_must_be_object", "file": "environment.json"})

    secret_patterns = (
        ("OPENAI" "_API_KEY", r"sk" r"-[A-Za-z0-9]{20,}"),
        ("GITHUB" "_TOKEN", r"ghp" r"_[A-Za-z0-9]{20,}"),
        ("PRIVATE" "_KEY", r"-----BEGIN [A-Z ]*PRIVATE " r"KEY-----"),
    )
    for file in REQUIRED_FILES + TOOL_AGENT_REQUIRED_FILES:
        path = bundle / file
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in secret_patterns:
            if re.search(pattern, text):
                findings.append(
                    {"severity": "error", "code": "secret_pattern_present", "file": file, "pattern": name}
                )

    return {
        "schema_version": "submission-bundle-validation-v1",
        "bundle": str(bundle),
        "required_files_present": files_present,
        "required_files_missing": files_missing,
        "tool_agent_required_files_present": [
            name for name in TOOL_AGENT_REQUIRED_FILES if (bundle / name).is_file()
        ],
        "harness_type": harness_type,
        "run_ids": sorted(run_ids),
        "submission_id": _stable_hash({"files": sorted(files_present), "metadata": metadata}) if metadata else None,
        "findings": findings,
        "passed": not any(f["severity"] == "error" for f in findings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bundle", help="Path to a submission bundle directory.")
    parser.add_argument(
        "--require-current-pack",
        action="store_true",
        help="Fail when the submitted private-pack fingerprint does not match the active pack.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    if not bundle.is_dir():
        print(f"not a directory: {bundle}", file=sys.stderr)
        return 2
    result = validate_bundle(bundle, require_current_pack=args.require_current_pack)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["passed"]:
            print(f"submission bundle ok: {bundle}")
        else:
            print(f"submission bundle FAILED: {bundle}", file=sys.stderr)
            for finding in result["findings"]:
                if finding.get("severity") == "error":
                    print(f"  ERROR {finding.get('code')}: {finding}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
