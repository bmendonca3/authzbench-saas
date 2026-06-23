"""Task taxonomy matrix generator.

The benchmark claims diversity across apps, vulnerability types, control
types, boundary types, route patterns, and difficulty. The taxonomy should
be visible and machine-generated, not asserted. This script walks the
public task manifests under ``tasks/`` and produces:

  * one JSON summary table
  * one Markdown matrix grouped by app and vulnerability class
  * a per-class count summary that reviewers can scan in 30 seconds

The classification is heuristic. It uses the task id, objective, oracle
claim, expected boundary, and control mix to bucket the task into the
class labels listed in the AuthZBench-SaaS fix plan. Tasks that don't
match any class land in ``unclassified_or_other`` so the gap is visible.

Usage:
    python3 scripts/generate_task_taxonomy.py
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TASKS_DIR = ROOT / "tasks"
DEFAULT_JSON_OUTPUT = ROOT / "artifact" / "task-taxonomy.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "task-taxonomy.md"


VULN_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "BOLA": ("bola", "object_id", "object-level"),
    "BFLA": ("bfla", "role", "function-level"),
    "cross_tenant_read": ("cross_tenant", "cross_workspace", "tenant_isolation", "cross_org", "cross_project"),
    "cross_tenant_write": ("cross_tenant_write", "cross_workspace_write"),
    "role_bypass": ("role_bypass", "required_role", "viewer", "guest", "member"),
    "token_scope_bypass": ("scope", "token", "export", "admin scope"),
    "entitlement_bypass": ("entitlement", "plan", "billing", "premium"),
    "stale_share_link": ("stale", "expired", "revoked", "share_link"),
    "reassignment_abuse": ("reassign", "transfer", "ownership"),
    "audit_admin_exposure": ("audit", "retention", "admin_export"),
}


BOUNDARY_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "tenant": ("tenant",),
    "org": ("org", "organization"),
    "project": ("project",),
    "team": ("team",),
    "user": ("user",),
    "object": ("object",),
    "role": ("role",),
    "token": ("token", "scope"),
    "plan_entitlement": ("plan", "entitlement", "billing"),
    "share_link": ("share_link", "link_state"),
}


CONTROL_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "vulnerable_proof": ("vulnerable", "exploit", "bypass"),
    "denial_control": ("denial", "denies", "forbidden", "secure"),
    "authorized_allow_control": ("authorized_allow", "allow", "permitted"),
    "alias_route": ("alias",),
    "decoy_endpoint": ("decoy",),
}


ROUTE_PATTERN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "direct_object_id": (),
    "nested_project_object": ("project", "object"),
    "alias_route": ("alias",),
    "admin_route": ("admin", "audit"),
    "export_route": ("export", "download"),
    "mutation_route": ("mutation", "share", "reassign", "transfer"),
    "token_auth_route": ("token", "scope"),
}


DIFFICULTY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "single_step_obvious": (),
    "single_step_with_decoy": ("decoy",),
    "multi_step_discovery": ("multistep", "multi_step", "multi-step", "discover"),
    "state_changing": ("mutation", "share", "reassign", "transfer", "destroy"),
    "token_scope_reasoning": ("scope", "token", "entitlement"),
    "false_positive_trap_heavy": ("decoy", "trap", "false_positive", "positive_alias"),
}


def _scan_keywords(haystack: str, table: dict[str, tuple[str, ...]]) -> list[str]:
    lowered = haystack.lower()
    hits: list[str] = []
    for label, keywords in table.items():
        if any(keyword in lowered for keyword in keywords):
            hits.append(label)
    return hits


def _taxonomy_for_task(task: dict[str, Any]) -> dict[str, Any]:
    blob = " ".join(
        str(value)
        for value in (
            task.get("id"),
            task.get("objective"),
            task.get("oracle", {}).get("claim") if isinstance(task.get("oracle"), dict) else None,
            task.get("expected_boundary"),
            " ".join(str(control.get("name", "")) for control in task.get("controls", [])),
            " ".join(str(control.get("path", "")) for control in task.get("controls", [])),
        )
        if value is not None
    )
    blob_lower = blob.lower()

    vuln_classes = _scan_keywords(blob_lower, VULN_CLASS_KEYWORDS)
    boundary_types = _scan_keywords(blob_lower, BOUNDARY_TYPE_KEYWORDS)
    control_types: list[str] = []
    for control in task.get("controls", []):
        control_blob = " ".join(
            str(value) for value in control.values() if value is not None
        ).lower()
        control_types.extend(_scan_keywords(control_blob, CONTROL_TYPE_KEYWORDS))
    control_types = sorted(set(control_types)) or ["vulnerable_proof"]
    route_patterns = _scan_keywords(blob_lower, ROUTE_PATTERN_KEYWORDS) or ["direct_object_id"]
    difficulty = _scan_keywords(blob_lower, DIFFICULTY_KEYWORDS) or ["single_step_obvious"]

    if not vuln_classes:
        vuln_classes = ["unclassified_or_other"]

    return {
        "id": task.get("id"),
        "app": task.get("app"),
        "expected_vulnerable": task.get("expected_vulnerable"),
        "vulnerability_classes": vuln_classes,
        "boundary_types": boundary_types,
        "control_types": control_types,
        "route_patterns": route_patterns,
        "difficulty": difficulty,
    }


def build_taxonomy(tasks_dir: Path = PUBLIC_TASKS_DIR) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(tasks_dir.glob("*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        row = _taxonomy_for_task(data)
        row["manifest_path"] = str(path.relative_to(ROOT))
        rows.append(row)
    return rows


def _cohort_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for label in row.get(key, []):
            counts[label] += 1
    return dict(counts)


def _cohort_matrix(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    app_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for label in row.get(key, []):
            app_buckets[row.get("app") or "unknown"][label] += 1
    return {app: dict(counts) for app, counts in sorted(app_buckets.items())}


def render_markdown(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# Task taxonomy matrix")
    lines.append("")
    task_count = len(rows)
    lines.append(
        "Generated by python3 scripts/generate_task_taxonomy.py."
        f" This matrix covers the current public split with {task_count} public"
        " tasks. Each public task is classified by vulnerability class, boundary"
        " type, control type, route pattern, and difficulty. The classifier is"
        " keyword-based and intentionally simple, so the matrix is a starting"
        " point for reviewer audits, not a final taxonomy."
    )
    lines.append("")
    lines.append("## Cohort counts")
    lines.append("")
    for key, title in (
        ("vulnerability_classes", "Vulnerability class"),
        ("boundary_types", "Boundary type"),
        ("control_types", "Control type"),
        ("route_patterns", "Route pattern"),
        ("difficulty", "Difficulty"),
    ):
        lines.append(f"### {title}")
        lines.append("")
        counts = _cohort_counts(rows, key)
        if counts:
            for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
                lines.append(f"- `{label}`: {count}")
        else:
            lines.append("- _(no matches)_")
        lines.append("")

    lines.append("## Per-app x vulnerability class matrix")
    lines.append("")
    matrix = _cohort_matrix(rows, "vulnerability_classes")
    all_labels = sorted({label for counts in matrix.values() for label in counts})
    lines.append("| App | " + " | ".join(f"`{label}`" for label in all_labels) + " |")
    lines.append("| --- | " + " | ".join("---" for _ in all_labels) + " |")
    for app, counts in matrix.items():
        cells = [str(counts.get(label, 0)) for label in all_labels]
        lines.append(f"| `{app}` | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Per-task classification")
    lines.append("")
    lines.append("| Task | App | Expected | Vulnerability | Boundary | Control | Route | Difficulty |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append(
            f"| `{row['id']}` | `{row['app']}` | {row['expected_vulnerable']} |"
            f" {', '.join(row['vulnerability_classes'])} |"
            f" {', '.join(row['boundary_types']) or '-'} |"
            f" {', '.join(row['control_types'])} |"
            f" {', '.join(row['route_patterns'])} |"
            f" {', '.join(row['difficulty'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tasks_dir = root / PUBLIC_TASKS_DIR.relative_to(ROOT)
    json_output = root / args.json_output.relative_to(ROOT) if not args.json_output.is_absolute() else args.json_output
    md_output = root / args.markdown_output.relative_to(ROOT) if not args.markdown_output.is_absolute() else args.markdown_output

    rows = build_taxonomy(tasks_dir)
    report = {
        "schema_version": "task-taxonomy-v1",
        "tasks_dir": str(PUBLIC_TASKS_DIR.relative_to(ROOT)),
        "summary": {
            "task_count": len(rows),
            "vulnerability_class_counts": _cohort_counts(rows, "vulnerability_classes"),
            "boundary_type_counts": _cohort_counts(rows, "boundary_types"),
            "control_type_counts": _cohort_counts(rows, "control_types"),
            "route_pattern_counts": _cohort_counts(rows, "route_patterns"),
            "difficulty_counts": _cohort_counts(rows, "difficulty"),
        },
        "per_app_vulnerability_class_matrix": _cohort_matrix(rows, "vulnerability_classes"),
        "entries": rows,
    }

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(rows), encoding="utf-8")

    print(
        f"task taxonomy: wrote {json_output.relative_to(root)} and"
        f" {md_output.relative_to(root)}; total={len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
