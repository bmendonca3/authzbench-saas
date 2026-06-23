from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = ROOT / "docs" / "task-quality-matrix.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "task-quality-matrix.md"


REQUIRED_PUBLIC_FIELDS = [
    "id",
    "app",
    "expected_vulnerable",
    "allowed_hosts",
    "policy",
    "objective",
    "output_schema",
    "oracle",
    "controls",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def public_task_paths(root: Path) -> list[Path]:
    return sorted((root / "tasks").glob("*/*.json"))


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


def _safe_requirement_summary(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for requirement in sorted(requirements, key=lambda item: item.get("index", 0)):
        request = requirement.get("request") if isinstance(requirement.get("request"), dict) else {}
        summary.append(
            {
                "index": requirement.get("index"),
                "actor_present": _present(request.get("actor")),
                "method": request.get("method"),
                "request_path_template_present": _present(request.get("path")),
                "request_body_required": "body" in request,
                "status_check_present": isinstance(requirement.get("status"), int),
                "body_check_present": "body_contains" in requirement,
            }
        )
    return summary


def summarize_task(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    expected_vulnerable = data.get("expected_vulnerable") is True
    controls = data.get("controls") if isinstance(data.get("controls"), list) else []
    oracle = data.get("oracle") if isinstance(data.get("oracle"), dict) else {}
    evidence_requirements = data.get("evidence_requirements")
    if not isinstance(evidence_requirements, list):
        evidence_requirements = []
    missing_public_fields = [field for field in REQUIRED_PUBLIC_FIELDS if not _present(data.get(field))]
    boundary = data.get("expected_boundary") if isinstance(data.get("expected_boundary"), dict) else {}
    control_type = data.get("control_type")
    control_status_check_count = sum(
        1 for control in controls if isinstance(control, dict) and isinstance(control.get("status"), int)
    )
    control_success_check_count = sum(
        1
        for control in controls
        if isinstance(control, dict) and isinstance(control.get("status"), int) and 200 <= control["status"] < 300
    )
    control_denial_check_count = sum(
        1
        for control in controls
        if isinstance(control, dict) and isinstance(control.get("status"), int) and control["status"] >= 400
    )
    task = {
        "id": data.get("id"),
        "manifest_path": str(path.relative_to(ROOT)),
        "app": data.get("app"),
        "split": data.get("split", "public"),
        "expected_vulnerable": expected_vulnerable,
        "control_type": None if expected_vulnerable else control_type,
        "expected_boundary_keys": sorted(boundary),
        "expected_boundary_present": bool(boundary),
        "control_count": len(controls),
        "control_status_check_count": control_status_check_count,
        "control_success_check_count": control_success_check_count,
        "control_denial_check_count": control_denial_check_count,
        "oracle_status_present": isinstance(oracle.get("status"), int),
        "oracle_body_check_present": "body_contains" in oracle,
        "scorer_oracle_present": bool(oracle),
        "allowed_host_count": len(data.get("allowed_hosts", [])) if isinstance(data.get("allowed_hosts"), list) else 0,
        "evidence_requirements_count": len(evidence_requirements),
        "evidence_requirement_steps": _safe_requirement_summary(evidence_requirements),
        "replay_proof_status": (
            "multi_step_evidence_requirements"
            if evidence_requirements
            else "direct_oracle_and_controls"
            if expected_vulnerable
            else "secure_control_oracle"
        ),
        "quality_flags": {
            "required_public_fields_present": not missing_public_fields,
            "missing_public_fields": missing_public_fields,
            "vulnerable_boundary_requirement_satisfied": (not expected_vulnerable) or bool(boundary),
            "secure_control_type_requirement_satisfied": expected_vulnerable
            or control_type in {"denial", "authorized_allow"},
            "has_controls": bool(controls),
            "has_scorer_oracle": bool(oracle),
            "has_replayable_check": isinstance(oracle.get("status"), int) or "body_contains" in oracle,
            "workflow_evidence_ready": (not evidence_requirements)
            or all(
                isinstance(requirement, dict)
                and isinstance(requirement.get("request"), dict)
                and ("status" in requirement or "body_contains" in requirement)
                for requirement in evidence_requirements
            ),
        },
    }
    return task


def build_matrix(root: Path = ROOT) -> dict[str, Any]:
    tasks = [summarize_task(path, load_json(path)) for path in public_task_paths(root)]
    app_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for task in tasks:
        app = str(task["app"])
        app_counts[app]["tasks"] += 1
        if task["expected_vulnerable"]:
            app_counts[app]["vulnerable"] += 1
        else:
            app_counts[app]["controls"] += 1
            app_counts[app][str(task["control_type"])] += 1
        if task["evidence_requirements_count"]:
            app_counts[app]["workflow_evidence_tasks"] += 1
    vulnerable_count = sum(1 for task in tasks if task["expected_vulnerable"])
    control_count = len(tasks) - vulnerable_count
    denial_count = sum(1 for task in tasks if task["control_type"] == "denial")
    authorized_allow_count = sum(1 for task in tasks if task["control_type"] == "authorized_allow")
    workflow_evidence_count = sum(1 for task in tasks if task["evidence_requirements_count"])
    flagged_tasks = [
        task["id"]
        for task in tasks
        if not all(value for key, value in task["quality_flags"].items() if key != "missing_public_fields")
    ]
    return {
        "schema_version": "task-quality-matrix-schema-1",
        "source": {
            "task_glob": "tasks/*/*.json",
            "public_safe": True,
            "privacy_boundary": "Public task ids and task-derived structural review signals only. Oracle bodies, seeds, refs, request paths, and private holdout manifests are not included.",
        },
        "summary": {
            "task_count": len(tasks),
            "app_count": len(app_counts),
            "vulnerable_task_count": vulnerable_count,
            "control_task_count": control_count,
            "denial_control_task_count": denial_count,
            "authorized_allow_control_task_count": authorized_allow_count,
            "workflow_evidence_task_count": workflow_evidence_count,
            "vulnerable_workflow_evidence_task_count": sum(
                1 for task in tasks if task["expected_vulnerable"] and task["evidence_requirements_count"]
            ),
            "tasks_with_quality_flags": flagged_tasks,
        },
        "apps": {
            app: {
                "task_count": counts["tasks"],
                "vulnerable_task_count": counts["vulnerable"],
                "control_task_count": counts["controls"],
                "denial_control_task_count": counts["denial"],
                "authorized_allow_control_task_count": counts["authorized_allow"],
                "workflow_evidence_task_count": counts["workflow_evidence_tasks"],
            }
            for app, counts in sorted(app_counts.items())
        },
        "tasks": tasks,
    }


def markdown(matrix: dict[str, Any]) -> str:
    summary = matrix["summary"]
    lines = [
        "# Task Quality Matrix",
        "",
        "Generated public-safe task audit matrix for AuthZBench-SaaS.",
        "",
        "This file summarizes public task structure, replay evidence readiness,",
        "and vulnerable/control mix. It intentionally does not include oracle",
        "body values, seeds, private holdout manifests, raw run logs, or private",
        "leaderboard artifacts.",
        "",
        "Regenerate with:",
        "",
        "```bash",
        "python3 scripts/generate_task_quality_matrix.py",
        "```",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Public tasks | {summary['task_count']} |",
        f"| App families | {summary['app_count']} |",
        f"| Vulnerable tasks | {summary['vulnerable_task_count']} |",
        f"| Secure controls | {summary['control_task_count']} |",
        f"| Denial controls | {summary['denial_control_task_count']} |",
        f"| Authorized-allow controls | {summary['authorized_allow_control_task_count']} |",
        f"| Tasks with explicit workflow evidence requirements | {summary['workflow_evidence_task_count']} |",
        f"| Vulnerable workflow tasks with evidence requirements | {summary['vulnerable_workflow_evidence_task_count']} |",
        "",
        "## App Mix",
        "",
        "| App | Tasks | Vulnerable | Controls | Denial | Authorized Allow | Workflow Evidence |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for app, counts in matrix["apps"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    app,
                    str(counts["task_count"]),
                    str(counts["vulnerable_task_count"]),
                    str(counts["control_task_count"]),
                    str(counts["denial_control_task_count"]),
                    str(counts["authorized_allow_control_task_count"]),
                    str(counts["workflow_evidence_task_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Task Review Matrix",
            "",
            "| Task | App | Type | Replay Proof | Controls | Boundary Keys | Evidence Steps |",
            "| --- | --- | --- | --- | ---: | --- | ---: |",
        ]
    )
    for task in matrix["tasks"]:
        task_type = "vulnerable" if task["expected_vulnerable"] else f"control:{task['control_type']}"
        boundary = ", ".join(task["expected_boundary_keys"]) if task["expected_boundary_keys"] else "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(task["id"]),
                    str(task["app"]),
                    task_type,
                    str(task["replay_proof_status"]),
                    str(task["control_count"]),
                    boundary,
                    str(task["evidence_requirements_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Current Interpretation",
            "",
            "The matrix supports the claim that the public scaffold is reviewable and",
            "structured across multiple SaaS authorization families. It supports the",
            "v1.0-internal internal/public-view packaging and is not external validation.",
            "Current repeated baseline breadth and more workflow-real",
            "task expansion remain a roadmap gap, not a blocker to the v1.0-internal label.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(matrix: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_output.write_text(markdown(matrix), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate public-safe task quality matrix artifacts.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    args = parser.parse_args()
    matrix = build_matrix(ROOT)
    write_outputs(matrix, args.json_output, args.markdown_output)
    print(f"wrote {_display_path(args.json_output)} and {_display_path(args.markdown_output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
