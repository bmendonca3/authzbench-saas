"""Per-task oracle audit generator.

The benchmark already gates public task quality via
``scripts/generate_task_quality_matrix.py`` and
``scripts/validate_task_quality_gate.py``, but reviewers need a single audit
table that says, for every task, whether the oracle is objective, the
boundary is specified, the control mix is complete, and what risk flags the
task carries. This script consumes every public task manifest under
``tasks/`` and emits one JSON + one Markdown file.

Manifest parse or validation failures always fail closed so a partial task set
cannot silently become an audit. Normal generation writes the report even when
an audit-specific gate is incomplete; ``--check`` performs no writes and fails
when either owned output is stale or an audit gate is incomplete.

Usage:
    python3 scripts/generate_task_oracle_audit.py
    python3 scripts/generate_task_oracle_audit.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import load_json, stable_json_sha256
from authzbench.validate_manifests import validate_patterns


PUBLIC_TASKS_DIR = ROOT / "tasks"
DEFAULT_JSON_OUTPUT = ROOT / "artifact" / "task-oracle-audit.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "task-oracle-audit.md"
SOURCE_BINDING_PATHS = (
    "authzbench/core.py",
    "authzbench/validate_manifests.py",
    "scripts/generate_task_oracle_audit.py",
)
MAX_INPUT_DIAGNOSTICS = 20


class AuditInputError(ValueError):
    """A bounded set of fatal public-audit input errors."""

    def __init__(self, details: list[str]):
        bounded = details[:MAX_INPUT_DIAGNOSTICS]
        if len(details) > MAX_INPUT_DIAGNOSTICS:
            bounded.append(
                f"{len(details) - MAX_INPUT_DIAGNOSTICS} additional input error(s) omitted"
            )
        super().__init__("; ".join(bounded))
        self.details = bounded


def _control_outcome(status: int) -> str:
    if 200 <= status < 300:
        return "success_2xx"
    if 400 <= status < 500:
        return "denial_4xx"
    return "other_status"


def _task_behavior(task: dict[str, Any]) -> str:
    if task["expected_vulnerable"] is True:
        return "vulnerable"
    return str(task["control_type"])


def _risk_flags(task: dict[str, Any], control_outcomes: Counter[str]) -> list[str]:
    flags: list[str] = []
    if task["expected_vulnerable"] is True and not control_outcomes["denial_4xx"]:
        flags.append("vulnerable_task_missing_denial_control")
    for control in task["controls"]:
        method = str(control["method"]).upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            flags.append("destructive_write")
            break
    return flags


def _audit_task(task: dict[str, Any]) -> dict[str, Any]:
    oracle = task["oracle"]
    boundary = task.get("expected_boundary") or {}
    controls = task["controls"]
    control_outcomes = Counter(_control_outcome(control["status"]) for control in controls)
    risk_flags = _risk_flags(task, control_outcomes)
    return {
        "id": task["id"],
        "app": task["app"],
        "expected_vulnerable": task["expected_vulnerable"],
        "task_behavior": _task_behavior(task),
        "control_type": task.get("control_type"),
        "has_objective": bool(task["objective"]),
        "has_oracle_status": isinstance(oracle.get("status"), int),
        "has_oracle_body_contains": bool(oracle.get("body_contains")),
        "has_oracle_claim": bool(oracle.get("claim")),
        "has_expected_boundary": bool(boundary),
        "boundary_keys": sorted(boundary.keys()) if isinstance(boundary, dict) else [],
        "control_count": len(controls),
        "control_names": [control.get("name") for control in controls],
        "control_outcome_counts": {
            outcome: control_outcomes[outcome]
            for outcome in ("success_2xx", "denial_4xx", "other_status")
        },
        "has_denial_control": bool(control_outcomes["denial_4xx"]),
        "has_successful_control": bool(control_outcomes["success_2xx"]),
        "destructive_write": any(
            str(control["method"]).upper() in {"POST", "PUT", "PATCH", "DELETE"}
            for control in controls
        ),
        "has_boundary_aliases": bool(task.get("boundary_aliases")),
        "risk_flags": risk_flags,
    }


def _cohorts(entries: list[dict[str, Any]]) -> dict[str, int]:
    cohort_counts: Counter[str] = Counter()
    for entry in entries:
        if entry["expected_vulnerable"] is True:
            cohort_counts["vulnerable"] += 1
        else:
            cohort_counts["secure_control"] += 1
            cohort_counts[entry["task_behavior"]] += 1
    cohort_counts["total"] = len(entries)
    return {
        key: cohort_counts[key]
        for key in (
            "total",
            "vulnerable",
            "secure_control",
            "denial",
            "authorized_allow",
        )
    }


def _by_app(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    app_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        app_buckets[entry.get("app") or "unknown"]["total"] += 1
        if entry["expected_vulnerable"] is True:
            app_buckets[entry.get("app") or "unknown"]["vulnerable"] += 1
        else:
            app_buckets[entry.get("app") or "unknown"]["secure_control"] += 1
            app_buckets[entry.get("app") or "unknown"][entry["task_behavior"]] += 1
    return {
        app: {
            key: counts[key]
            for key in (
                "total",
                "vulnerable",
                "secure_control",
                "denial",
                "authorized_allow",
            )
        }
        for app, counts in sorted(app_buckets.items())
    }


def audit_public_tasks(
    tasks_dir: Path = PUBLIC_TASKS_DIR,
    *,
    root: Path = ROOT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    paths = sorted(tasks_dir.glob("*/*.json"))
    if not paths:
        raise AuditInputError([f"{tasks_dir}: no public task manifests found"])
    validation = validate_patterns([str(path) for path in paths])
    if validation["errors"]:
        raise AuditInputError(list(validation["errors"]))

    entries: list[dict[str, Any]] = []
    manifest_items: list[dict[str, Any]] = []
    for path in paths:
        try:
            data = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise AuditInputError(
                [f"{path}: failed to load JSON manifest: {type(exc).__name__}"]
            ) from exc
        manifest_path = path.relative_to(root).as_posix()
        entry = _audit_task(data)
        entry["manifest_path"] = manifest_path
        entries.append(entry)
        manifest_items.append({"manifest_path": manifest_path, "manifest": data})
    return entries, manifest_items


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_manifest_set_sha256(manifest_items: list[dict[str, Any]]) -> str:
    canonical_items = sorted(manifest_items, key=lambda item: item["manifest_path"])
    return stable_json_sha256(canonical_items)


def _source_binding(root: Path) -> dict[str, Any]:
    source_hashes: dict[str, str] = {}
    missing: list[str] = []
    for relative in SOURCE_BINDING_PATHS:
        path = root / relative
        if not path.is_file():
            missing.append(f"{path}: audit source file is missing")
            continue
        source_hashes[relative] = _file_sha256(path)
    if missing:
        raise AuditInputError(missing)
    return {
        "schema_version": "task-oracle-audit-source-binding-v1",
        "source_sha256": source_hashes,
        "current_source_set_sha256": stable_json_sha256(source_hashes),
        "claim_boundary": (
            "The source-set digest binds the exact audit implementation content. "
            "It does not assert a clean Git worktree, release-candidate status, "
            "hosted execution, external validation, or platform acceptance."
        ),
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    tasks_dir = root / PUBLIC_TASKS_DIR.relative_to(ROOT)
    entries, manifest_items = audit_public_tasks(tasks_dir, root=root)
    failures = _check_gates(entries)
    return {
        "schema_version": "task-oracle-audit-v2",
        "tasks_dir": PUBLIC_TASKS_DIR.relative_to(ROOT).as_posix(),
        "source_binding": _source_binding(root),
        "public_manifest_count": len(manifest_items),
        "public_manifest_set_sha256": canonical_manifest_set_sha256(manifest_items),
        "public_manifest_digest_algorithm": (
            "sha256 of canonical JSON over sorted manifest_path + parsed manifest objects"
        ),
        "control_classification": (
            "task behavior uses expected_vulnerable + control_type; per-control outcomes "
            "use validated HTTP status classes only"
        ),
        "summary": _cohorts(entries),
        "per_app": _by_app(entries),
        "entries": entries,
        "schema_gate_failures": failures,
    }


def _check_gates(entries: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        if not entry["has_objective"]:
            failures.append(f"{entry['id']}: missing objective")
        if entry["expected_vulnerable"] is True:
            if not entry["has_oracle_status"]:
                failures.append(f"{entry['id']}: vulnerable task missing oracle.status")
            if not entry["has_oracle_body_contains"]:
                failures.append(f"{entry['id']}: vulnerable task missing oracle.body_contains")
            if not entry["has_expected_boundary"]:
                failures.append(f"{entry['id']}: vulnerable task missing expected_boundary")
        if entry["control_count"] == 0:
            failures.append(f"{entry['id']}: no controls")
        if entry["expected_vulnerable"] is True and not entry["has_denial_control"]:
            failures.append(f"{entry['id']}: vulnerable task missing denial control")
        if "vulnerable_task_missing_denial_control" in entry["risk_flags"]:
            failures.append(f"{entry['id']}: risk_flag vulnerable_task_missing_denial_control")
    return failures


def render_markdown(report: dict[str, Any]) -> str:
    entries = report["entries"]
    failures = report["schema_gate_failures"]
    source_binding = report["source_binding"]
    lines: list[str] = []
    lines.append("# Task Oracle Audit")
    lines.append("")
    cohort_counts = _cohorts(entries)
    total = cohort_counts['total']
    vulnerable = cohort_counts['vulnerable']
    secure_control = cohort_counts['secure_control']
    lines.append(
        "Generated by python3 scripts/generate_task_oracle_audit.py."
        f" This audit covers the current public split with {total} public"
        f" tasks ({vulnerable} vulnerable tasks, {secure_control} secure-control"
        " tasks). One row per public task manifest under `tasks/`. The audit"
        " reports whether the objective, oracle, boundary, and control mix are"
        " complete enough to score the task objectively, and lists any"
        " risk flags it carries. This is a public-task oracle audit and is"
        " not private holdout coverage, external validation, hosted"
        " leaderboard execution, or platform acceptance."
    )
    lines.append("")
    lines.append("## Cohort summary")
    lines.append("")
    app_buckets = _by_app(entries)
    lines.append(f"- Total tasks: {total}")
    lines.append(f"- Vulnerable tasks: {vulnerable}")
    lines.append(f"- Secure control tasks: {secure_control}")
    lines.append(f"- Denial controls: {cohort_counts['denial']}")
    lines.append(f"- Authorized-allow controls: {cohort_counts['authorized_allow']}")
    lines.append(
        f"- Canonical public manifest-set SHA-256: `{report['public_manifest_set_sha256']}`"
    )
    lines.append(
        f"- Current audit source-set SHA-256: `{source_binding['current_source_set_sha256']}`"
    )
    lines.append(
        "- Source claim boundary: exact content binding only; this does not assert a clean Git "
        "worktree or a validated release."
    )
    lines.append("")
    lines.append("## Per-app split")
    lines.append("")
    lines.append("| App | Vulnerable | Denial | Authorized allow | Total |")
    lines.append("| --- | --- | --- | --- | --- |")
    for app, counts in app_buckets.items():
        lines.append(
            f"| `{app}` | {counts['vulnerable']} | {counts['denial']} |"
            f" {counts['authorized_allow']} | {counts['total']} |"
        )
    lines.append("")
    lines.append("## Per-task audit")
    lines.append("")
    lines.append("| Task | App | Behavior | Oracle | Boundary | Controls | Risk flags |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for entry in entries:
        oracle_ok = entry["has_oracle_status"] and entry["has_oracle_body_contains"]
        boundary_ok = entry["has_expected_boundary"]
        outcome_counts = entry["control_outcome_counts"]
        other_summary = (
            f" ({outcome_counts['other_status']} other)"
            if outcome_counts["other_status"]
            else ""
        )
        control_summary = (
            f"{entry['control_count']} controls"
            f" ({outcome_counts['success_2xx']} 2xx)"
            f" ({outcome_counts['denial_4xx']} 4xx)"
            f"{other_summary}"
        )
        risk = ", ".join(entry["risk_flags"]) or "-"
        lines.append(
            f"| `{entry['id']}` | `{entry['app']}` |"
            f" `{entry['task_behavior']}` |"
            f" {'yes' if oracle_ok else 'no'} |"
            f" {'yes' if boundary_ok else 'no'} |"
            f" {control_summary} | {risk} |"
        )
    if failures:
        lines.append("")
        lines.append("## Schema gate failures")
        lines.append("")
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _resolve_output_path(root: Path, configured: Path, canonical_default: Path) -> Path:
    if configured == canonical_default:
        return root / canonical_default.relative_to(ROOT)
    return configured if configured.is_absolute() else root / configured


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; fail on invalid inputs, audit gaps, or stale owned outputs.",
    )
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    json_output = _resolve_output_path(root, args.json_output, DEFAULT_JSON_OUTPUT)
    md_output = _resolve_output_path(root, args.markdown_output, DEFAULT_MARKDOWN_OUTPUT)
    try:
        report = build_report(root)
    except AuditInputError as exc:
        print("task oracle audit: input validation FAILED", file=sys.stderr)
        for detail in exc.details:
            print(f"  - {detail}", file=sys.stderr)
        return 1

    expected_json = json.dumps(report, indent=2, sort_keys=True) + "\n"
    expected_markdown = render_markdown(report)
    failures = report["schema_gate_failures"]

    if args.check:
        stale_outputs: list[str] = []
        for path, expected in (
            (json_output, expected_json),
            (md_output, expected_markdown),
        ):
            try:
                observed = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                stale_outputs.append(
                    f"{_display_path(path, root)}: unreadable output ({type(exc).__name__})"
                )
                continue
            if observed != expected:
                stale_outputs.append(
                    f"{_display_path(path, root)}: stale for the current manifest/source binding"
                )
        if failures:
            print("task oracle audit: schema gate FAILED", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
        if stale_outputs:
            print("task oracle audit: output binding FAILED", file=sys.stderr)
            for failure in stale_outputs:
                print(f"  - {failure}", file=sys.stderr)
        if failures or stale_outputs:
            return 1
        print(
            "task oracle audit: check passed;"
            f" total={report['public_manifest_count']};"
            f" manifest_set_sha256={report['public_manifest_set_sha256']};"
            " source_set_sha256="
            f"{report['source_binding']['current_source_set_sha256']}"
        )
        return 0

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(expected_json, encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(expected_markdown, encoding="utf-8")
    print(
        f"task oracle audit: wrote {_display_path(json_output, root)} and"
        f" {_display_path(md_output, root)};"
        f" total={report['public_manifest_count']};"
        f" manifest_set_sha256={report['public_manifest_set_sha256']}"
    )
    if failures:
        print("schema gate FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
