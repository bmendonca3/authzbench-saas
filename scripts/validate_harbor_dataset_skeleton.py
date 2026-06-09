from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "harbor-dataset-skeleton-v1"
ALLOWED_ABSOLUTE_PREFIXES = (
    "/api/",
    "/logs/artifacts/",
    "/tasks/",
    "/work-items/",
)
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")
DISALLOWED_TEXT = (
    "calendar." + "google.com",
    "appointments/" + "schedules",
    "accepted" + " by",
    "endorsed" + " by",
)
PRIVATE_MARKERS = (
    "tasks_private/holdout",
    "private route:",
    "private seed:",
    "raw private output",
    "credential:",
    "oracle:",
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _safe_relative(base: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (base / path).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        return None
    return candidate


def _text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(_text_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(_text_values(child))
        return values
    if isinstance(value, str):
        return [value]
    return []


def _public_safety_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    for text in _text_values(value):
        lower = text.lower()
        for marker in DISALLOWED_TEXT:
            if marker in lower:
                errors.append(f"{label}: disallowed private/overclaim marker: {marker}")
        for marker in PRIVATE_MARKERS:
            if marker in lower:
                errors.append(f"{label}: private detail marker is not allowed: {marker}")
        for match in ABSOLUTE_PATH_RE.findall(text):
            if not any(match.startswith(prefix) for prefix in ALLOWED_ABSOLUTE_PREFIXES):
                errors.append(f"{label}: local absolute path is not allowed: {match}")
    return errors


def validate_harbor_dataset_skeleton(dataset_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    dataset_dir = dataset_dir.resolve()
    manifest_path = dataset_dir / "dataset-manifest.json"
    if not manifest_path.exists():
        return {"errors": ["dataset-manifest.json is required"], "passed": False, "task_count": 0}

    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:
        return {"errors": [str(exc)], "passed": False, "task_count": 0}

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("evidence_status") != "generated_public_skeleton":
        errors.append("evidence_status must be generated_public_skeleton")
    if "not Harbor execution evidence" not in str(manifest.get("claim_boundary", "")):
        errors.append("claim_boundary must state the skeleton is not Harbor execution evidence")
    if manifest.get("harbor_execution_verified") is not False:
        errors.append("harbor_execution_verified must be false")
    if manifest.get("private_task_count") != 0:
        errors.append("private_task_count must be 0")
    if manifest.get("harness_lane") not in {"no_tools", "live_http_tool_agent"}:
        errors.append("harness_lane must be no_tools or live_http_tool_agent")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be a list")
        tasks = []
    if manifest.get("task_count") != len(tasks):
        errors.append("task_count must match tasks length")

    seen_task_dirs: set[str] = set()
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            errors.append(f"tasks[{index}] must be an object")
            continue
        task_id = task.get("id")
        task_dir = _safe_relative(dataset_dir, task.get("harbor_task_dir"))
        if task_dir is None:
            errors.append(f"tasks[{index}].harbor_task_dir must be a safe relative path")
            continue
        rel_task_dir = task.get("harbor_task_dir")
        if rel_task_dir in seen_task_dirs:
            errors.append(f"duplicate harbor_task_dir: {rel_task_dir}")
        seen_task_dirs.add(str(rel_task_dir))
        if not task_dir.is_dir():
            errors.append(f"{rel_task_dir}: task directory is missing")
            continue

        required_files = {
            "instruction.md": task_dir / "instruction.md",
            "task.toml": task_dir / "task.toml",
            "environment/context.json": task_dir / "environment" / "context.json",
            "verifier/task_manifest.json": task_dir / "verifier" / "task_manifest.json",
            "tests/test.sh": task_dir / "tests" / "test.sh",
        }
        for name, path in required_files.items():
            if not path.is_file():
                errors.append(f"{rel_task_dir}: missing {name}")

        if required_files["instruction.md"].is_file():
            instruction = required_files["instruction.md"].read_text(encoding="utf-8")
            if "/logs/artifacts/submission.json" not in instruction:
                errors.append(f"{rel_task_dir}: instruction must name /logs/artifacts/submission.json")
            if task.get("expected_vulnerable") is False and "findings: []" not in instruction:
                errors.append(f"{rel_task_dir}: secure-control instruction must preserve findings: [] rule")
            errors.extend(_public_safety_errors(instruction, label=f"{rel_task_dir}/instruction.md"))

        if required_files["task.toml"].is_file():
            task_toml = required_files["task.toml"].read_text(encoding="utf-8")
            required_snippets = (
                f'schema_version = "{SCHEMA_VERSION}"',
                "private_execution = false",
                "harbor_execution_verified = false",
                'command = "tests/test.sh"',
                'scorer_contract = "v0-candidate-authz-evidence"',
            )
            for snippet in required_snippets:
                if snippet not in task_toml:
                    errors.append(f"{rel_task_dir}: task.toml missing {snippet}")
            if manifest.get("harness_lane") == "live_http_tool_agent" and "request correlation" not in task_toml:
                errors.append(f"{rel_task_dir}: live HTTP task.toml must mention request correlation")
            errors.extend(_public_safety_errors(task_toml, label=f"{rel_task_dir}/task.toml"))

        if required_files["tests/test.sh"].is_file():
            script = required_files["tests/test.sh"].read_text(encoding="utf-8")
            if "python3 -m authzbench.score" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must invoke authzbench.score")
            if "/logs/artifacts/score.json" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write score artifact")

        for json_name in ("environment/context.json", "verifier/task_manifest.json"):
            path = required_files[json_name]
            if not path.is_file():
                continue
            try:
                data = _load_json(path)
            except Exception as exc:
                errors.append(str(exc))
                continue
            errors.extend(_public_safety_errors(data, label=f"{rel_task_dir}/{json_name}"))
            if json_name == "environment/context.json" and data.get("task_id") != task_id:
                errors.append(f"{rel_task_dir}: context task_id must match manifest entry")
            if json_name == "verifier/task_manifest.json" and data.get("id") != task_id:
                errors.append(f"{rel_task_dir}: verifier task_manifest id must match manifest entry")
            if json_name == "verifier/task_manifest.json" and data.get("split") == "private_holdout":
                errors.append(f"{rel_task_dir}: private holdout manifests are not allowed")

    errors.extend(_public_safety_errors(manifest, label="dataset-manifest.json"))
    return {
        "errors": sorted(set(errors)),
        "harness_lane": manifest.get("harness_lane"),
        "passed": not errors,
        "task_count": len(tasks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated Harbor dataset skeleton.")
    parser.add_argument("--dataset-dir", type=Path, required=True)
    args = parser.parse_args()
    result = validate_harbor_dataset_skeleton(args.dataset_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
