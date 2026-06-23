"""Per-task oracle audit generator.

The benchmark already gates public task quality via
``scripts/generate_task_quality_matrix.py`` and
``scripts/validate_task_quality_gate.py``, but reviewers need a single audit
table that says, for every task, whether the oracle is objective, the
boundary is specified, the control mix is complete, and what risk flags the
task carries. This script consumes every public task manifest under
``tasks/`` and emits one JSON + one Markdown file.

It is intentionally a *report* you can regenerate, not a gate that fails
hard. The companion gate lives in ``--check`` mode and only fails on
schema-level gaps (no objective, no oracle, no controls, missing denial
control on a vulnerable task, etc).

Usage:
    python3 scripts/generate_task_oracle_audit.py
    python3 scripts/generate_task_oracle_audit.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TASKS_DIR = ROOT / "tasks"
DEFAULT_JSON_OUTPUT = ROOT / "artifact" / "task-oracle-audit.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "task-oracle-audit.md"

DENIAL_KEYWORDS = ("denies", "denial", "forbidden", "secure")
ALLOW_KEYWORDS = ("authorized", "allow", "permits", "allows")
ALIAS_KEYWORDS = ("alias",)
DECOY_KEYWORDS = ("decoy",)


def _classify_control(control: dict[str, Any]) -> set[str]:
    name = (control.get("name") or "").lower()
    flags: set[str] = set()
    if any(keyword in name for keyword in DENIAL_KEYWORDS):
        flags.add("denial")
    if any(keyword in name for keyword in ALLOW_KEYWORDS):
        flags.add("authorized_allow")
    if any(keyword in name for keyword in ALIAS_KEYWORDS):
        flags.add("alias")
    if any(keyword in name for keyword in DECOY_KEYWORDS):
        flags.add("decoy")
    return flags


def _risk_flags(task: dict[str, Any], control_flags: set[str]) -> list[str]:
    flags: list[str] = []
    if task.get("expected_vulnerable") is True and "denial" not in control_flags:
        flags.append("vulnerable_task_missing_denial_control")
    method = ""
    for control in task.get("controls", []):
        method = str(control.get("method", "")).upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            flags.append("destructive_write")
            break
    if "decoy" not in control_flags and task.get("expected_vulnerable") is True:
        flags.append("vulnerable_task_no_decoy_control")
    return flags


def _audit_task(task: dict[str, Any]) -> dict[str, Any]:
    oracle = task.get("oracle") or {}
    boundary = task.get("expected_boundary") or {}
    controls = task.get("controls") or []
    control_flags: set[str] = set()
    for control in controls:
        control_flags |= _classify_control(control)
    risk_flags = _risk_flags(task, control_flags)
    return {
        "id": task.get("id"),
        "app": task.get("app"),
        "expected_vulnerable": task.get("expected_vulnerable"),
        "has_objective": bool(task.get("objective")),
        "has_oracle_status": isinstance(oracle.get("status"), int),
        "has_oracle_body_contains": bool(oracle.get("body_contains")),
        "has_oracle_claim": bool(oracle.get("claim")),
        "has_expected_boundary": bool(boundary),
        "boundary_keys": sorted(boundary.keys()) if isinstance(boundary, dict) else [],
        "control_count": len(controls),
        "control_names": [control.get("name") for control in controls],
        "has_denial_control": "denial" in control_flags,
        "has_authorized_allow_control": "authorized_allow" in control_flags,
        "has_alias_control": "alias" in control_flags,
        "has_decoy_control": "decoy" in control_flags,
        "destructive_write": any(str(c.get("method", "")).upper() in {"POST", "PUT", "PATCH", "DELETE"} for c in controls),
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
    cohort_counts["total"] = len(entries)
    return dict(cohort_counts)


def _by_app(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    app_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        app_buckets[entry.get("app") or "unknown"]["total"] += 1
        if entry["expected_vulnerable"] is True:
            app_buckets[entry.get("app") or "unknown"]["vulnerable"] += 1
        else:
            app_buckets[entry.get("app") or "unknown"]["secure_control"] += 1
    return {app: dict(counts) for app, counts in sorted(app_buckets.items())}


def audit_public_tasks(tasks_dir: Path = PUBLIC_TASKS_DIR) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(tasks_dir.glob("*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entry = _audit_task(data)
        entry["manifest_path"] = str(path.relative_to(ROOT))
        entries.append(entry)
    return entries


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


def render_markdown(entries: list[dict[str, Any]], failures: list[str]) -> str:
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
    lines.append("")
    lines.append("## Per-app split")
    lines.append("")
    lines.append("| App | Vulnerable | Secure control | Total |")
    lines.append("| --- | --- | --- | --- |")
    for app, counts in app_buckets.items():
        lines.append(
            f"| `{app}` | {counts['vulnerable']} | {counts['secure_control']} | {counts['total']} |"
        )
    lines.append("")
    lines.append("## Per-task audit")
    lines.append("")
    lines.append("| Task | App | Expected | Oracle | Boundary | Controls | Risk flags |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for entry in entries:
        oracle_ok = entry["has_oracle_status"] and entry["has_oracle_body_contains"]
        boundary_ok = entry["has_expected_boundary"]
        control_summary = (
            f"{entry['control_count']} controls"
            f"{' (denial)' if entry['has_denial_control'] else ''}"
            f"{' (allow)' if entry['has_authorized_allow_control'] else ''}"
            f"{' (alias)' if entry['has_alias_control'] else ''}"
            f"{' (decoy)' if entry['has_decoy_control'] else ''}"
        )
        risk = ", ".join(entry["risk_flags"]) or "-"
        lines.append(
            f"| `{entry['id']}` | `{entry['app']}` |"
            f" {entry['expected_vulnerable']} |"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when any schema-level oracle gap is found.",
    )
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tasks_dir = root / PUBLIC_TASKS_DIR.relative_to(ROOT)
    json_output = root / args.json_output.relative_to(ROOT) if not args.json_output.is_absolute() else args.json_output
    md_output = root / args.markdown_output.relative_to(ROOT) if not args.markdown_output.is_absolute() else args.markdown_output

    entries = audit_public_tasks(tasks_dir)
    failures = _check_gates(entries)
    report = {
        "schema_version": "task-oracle-audit-v1",
        "tasks_dir": str(PUBLIC_TASKS_DIR.relative_to(ROOT)),
        "summary": _cohorts(entries),
        "per_app": _by_app(entries),
        "entries": entries,
        "schema_gate_failures": failures,
    }

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(entries, failures), encoding="utf-8")

    print(
        f"task oracle audit: wrote {json_output.relative_to(root)} and"
        f" {md_output.relative_to(root)}; total={report['summary']['total']}"
    )
    if args.check and failures:
        print("schema gate FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
