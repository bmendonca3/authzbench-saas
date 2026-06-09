from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import build_context, dump_json, load_json


SCHEMA_VERSION = "harbor-dataset-skeleton-v1"


def _task_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "task"


def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _reference_run_config() -> str:
    return "\n".join(
        [
            "# Public-safe Harbor run target for generated skeleton datasets.",
            "# This file is not evidence that Harbor execution has been verified.",
            "datasets:",
            "  - path: .",
            "",
            "# Default oracle-style verifier lane for structure checks.",
            "agents:",
            "  - name: oracle",
            "",
            "# Uncomment and verify concrete agents/models in a real Harbor run.",
            "# agents:",
            "#   - name: codex",
            "#     model_name: openai/gpt-5-mini",
            "",
            "environment:",
            "  type: docker",
            "  delete: true",
            "",
            "orchestrator:",
            "  type: local",
            "  n_concurrent_trials: 1",
            "",
            "artifacts:",
            "  - /logs/artifacts",
            "",
        ]
    )


def _environment_dockerfile() -> str:
    return "\n".join(
        [
            "# Public-safe placeholder environment for the Harbor dataset skeleton.",
            "# This file is not Harbor execution evidence.",
            "FROM python:3.11-slim",
            "WORKDIR /workspace",
            "ENV PYTHONUNBUFFERED=1",
            "",
            "# A verified Harbor adapter must replace this placeholder with a",
            "# pinned image/package path that provides authzbench scoring code.",
            "",
        ]
    )


def _solution_script() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "echo 'AuthZBench-SaaS Harbor skeleton does not include a public oracle solution.' >&2",
            "echo 'Run the scorer-controlled verifier against an agent submission instead.' >&2",
            "exit 64",
            "",
        ]
    )


def _instruction(task: dict[str, Any], context_relpath: str) -> str:
    control_rule = (
        "This is a secure-control task. Return an AuthZBench-SaaS submission with `findings: []` "
        "unless you have explicit evidence that the control failed."
        if task.get("expected_vulnerable") is False
        else "This is a vulnerable-task candidate. Submit exactly one replayable finding only if backend evidence proves it."
    )
    return "\n".join(
        [
            "# AuthZBench-SaaS Harbor Task",
            "",
            "Read the rendered context JSON for actors, targets, API docs, and output schema:",
            "",
            f"- `{context_relpath}`",
            "",
            "Write the agent submission to:",
            "",
            "- `/logs/artifacts/submission.json`",
            "",
            control_rule,
            "",
            "The verifier runs the AuthZBench-SaaS scorer. Do not rely on prose-only claims.",
            "",
        ]
    )


def _task_toml(task: dict[str, Any], *, task_path: Path, harness_lane: str) -> str:
    service_notes = [
        "no_tools lane uses rendered context only",
        "live_http_tool_agent lane requires target services and request correlation",
        "verifier/scorer owns replay and oracle access",
    ]
    if harness_lane == "live_http_tool_agent":
        service_notes.extend(
            [
                "start target services before agent phase",
                "preserve AUTHZBENCH_AGENT_ID-equivalent request correlation",
            ]
        )
    agent_network_mode = "no-network" if harness_lane == "no_tools" else "allowlist"
    agent_allowed_hosts = [] if harness_lane == "no_tools" else ["localhost", "127.0.0.1"]
    lines = [
        'schema_version = "1.3"',
        "",
        "[task]",
        f"name = {_toml_string('authzbench-saas/' + _safe_name(str(task['id'])))}",
        f"description = {_toml_string('AuthZBench-SaaS public Harbor skeleton task for ' + str(task['app']))}",
        'authors = [{ name = "bmendonca3" }]',
        'keywords = ["authzbench-saas", "authorization", "harbor-compatible"]',
        "",
        "[metadata.authzbench]",
        f"skeleton_schema_version = {_toml_string(SCHEMA_VERSION)}",
        f"id = {_toml_string(str(task['id']))}",
        f"app = {_toml_string(str(task['app']))}",
        f"source_task_path = {_toml_string(_relative_to_root(task_path))}",
        f"harness_lane = {_toml_string(harness_lane)}",
        "private_execution = false",
        "harbor_execution_verified = false",
        f"claim_boundary = {_toml_string('Generated public dataset skeleton only; not Harbor execution evidence or v1 readiness.')}",
        f"required_artifacts = {_toml_list(['/logs/artifacts/submission.json', '/logs/artifacts/score.json'])}",
        f"service_notes = {_toml_list(service_notes)}",
        "",
        "[verifier]",
        "timeout_sec = 120.0",
        'environment_mode = "separate"',
        'network_mode = "no-network"',
        "",
        "[agent]",
        "timeout_sec = 120.0",
        f"network_mode = {_toml_string(agent_network_mode)}",
        f"allowed_hosts = {_toml_list(agent_allowed_hosts)}",
        "",
        "[environment]",
        'network_mode = "no-network"',
        'os = "linux"',
        "cpus = 1",
        "memory_mb = 2048",
        "",
        "[metadata.authzbench.verifier]",
        'test_script = "tests/test.sh"',
        'scorer_contract = "v0-candidate-authz-evidence"',
        'submission_path = "/logs/artifacts/submission.json"',
        'score_output_path = "/logs/artifacts/score.json"',
        "",
    ]
    return "\n".join(lines)


def build_harbor_dataset_skeleton(
    task_patterns: list[str],
    output_dir: Path,
    *,
    harness_lane: str = "no_tools",
    task_ids: list[str] | None = None,
    limit: int | None = None,
    clean: bool = False,
) -> dict[str, Any]:
    if harness_lane not in {"no_tools", "live_http_tool_agent"}:
        raise ValueError("harness_lane must be no_tools or live_http_tool_agent")
    requested_task_ids = set(task_ids or [])
    task_paths = _task_paths(task_patterns)
    if requested_task_ids:
        filtered_paths: list[Path] = []
        for task_path in task_paths:
            task = load_json(task_path)
            if task.get("id") in requested_task_ids:
                filtered_paths.append(task_path)
        task_paths = filtered_paths
    if limit is not None:
        task_paths = task_paths[:limit]
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks: list[dict[str, Any]] = []
    for task_path in task_paths:
        task = load_json(task_path)
        if requested_task_ids and task.get("id") not in requested_task_ids:
            continue
        if task.get("split") == "private_holdout":
            raise ValueError("private holdout manifests must not be exported with the public Harbor skeleton builder")
        task_dir = output_dir / "tasks" / _safe_name(str(task["id"]))
        environment_dir = task_dir / "environment"
        solution_dir = task_dir / "solution"
        verifier_dir = task_dir / "verifier"
        tests_dir = task_dir / "tests"
        environment_dir.mkdir(parents=True, exist_ok=True)
        solution_dir.mkdir(parents=True, exist_ok=True)
        verifier_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        context = build_context(task)
        (environment_dir / "context.json").write_text(dump_json(context) + "\n", encoding="utf-8")
        (environment_dir / "Dockerfile").write_text(_environment_dockerfile(), encoding="utf-8")
        (verifier_dir / "task_manifest.json").write_text(dump_json(task) + "\n", encoding="utf-8")
        (task_dir / "instruction.md").write_text(_instruction(task, "environment/context.json"), encoding="utf-8")
        (task_dir / "task.toml").write_text(_task_toml(task, task_path=task_path, harness_lane=harness_lane), encoding="utf-8")
        solution_path = solution_dir / "solve.sh"
        solution_path.write_text(_solution_script(), encoding="utf-8")
        solution_path.chmod(0o755)
        test_script = "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "mkdir -p /logs/artifacts",
                'python3 -m authzbench.score verifier/task_manifest.json /logs/artifacts/submission.json > /logs/artifacts/score.json',
                'python3 - <<\'PY\'',
                "import json",
                "from pathlib import Path",
                "score = json.loads(Path('/logs/artifacts/score.json').read_text())",
                "raise SystemExit(0 if score.get('passed') is True else 1)",
                "PY",
                "",
            ]
        )
        script_path = tests_dir / "test.sh"
        script_path.write_text(test_script, encoding="utf-8")
        script_path.chmod(0o755)
        tasks.append(
            {
                "id": task["id"],
                "app": task["app"],
                "expected_vulnerable": bool(task.get("expected_vulnerable")),
                "harbor_task_dir": task_dir.relative_to(output_dir).as_posix(),
                "source_task_path": _relative_to_root(task_path),
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "evidence_status": "generated_public_skeleton",
        "claim_boundary": "This generated dataset skeleton is not Harbor execution evidence, not Harbor acceptance, and not v1 readiness.",
        "harness_lane": harness_lane,
        "task_count": len(tasks),
        "private_task_count": 0,
        "harbor_execution_verified": False,
        "reference_run_config": "run_authzbench_saas.yaml",
        "tasks": tasks,
    }
    (output_dir / "run_authzbench_saas.yaml").write_text(_reference_run_config(), encoding="utf-8")
    (output_dir / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public-safe Harbor dataset skeleton from AuthZBench-SaaS tasks.")
    parser.add_argument("--task", action="append", required=True, help="Public task manifest glob. Repeatable.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--harness-lane", choices=["no_tools", "live_http_tool_agent"], default="no_tools")
    parser.add_argument("--task-id", action="append", help="Optional task id filter. Repeatable.")
    parser.add_argument(
        "--task-ids",
        action="append",
        help="Comma-separated task id filter, matching Harbor adapter CLI expectations. Repeatable.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Alias for --clean, matching Harbor adapter CLI expectations.")
    args = parser.parse_args()
    task_ids = list(args.task_id or [])
    for value in args.task_ids or []:
        task_ids.extend(task_id.strip() for task_id in value.split(",") if task_id.strip())
    manifest = build_harbor_dataset_skeleton(
        args.task,
        args.output_dir,
        harness_lane=args.harness_lane,
        task_ids=task_ids,
        limit=args.limit,
        clean=args.clean or args.overwrite,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
