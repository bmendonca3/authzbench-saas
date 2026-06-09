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
    "/logs/verifier/",
    "/tests/",
    "/tasks/",
    "/work-items/",
)
ALLOWED_ABSOLUTE_PATHS = {"/logs/artifacts", "/logs/verifier", "/usr/bin/env"}
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


def _load_toml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current: dict[str, Any] = root
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = root
            for part in line[1:-1].split("."):
                if not part:
                    raise ValueError(f"{path}:{line_number}: empty TOML table component")
                child = current.setdefault(part, {})
                if not isinstance(child, dict):
                    raise ValueError(f"{path}:{line_number}: table conflicts with scalar value")
                current = child
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected key = value")
        key, value = (part.strip() for part in line.split("=", 1))
        if not key:
            raise ValueError(f"{path}:{line_number}: empty TOML key")
        if value in {"true", "false"}:
            current[key] = value == "true"
        elif value.startswith('"') and value.endswith('"'):
            current[key] = json.loads(value)
        else:
            try:
                current[key] = json.loads(value)
            except json.JSONDecodeError:
                current[key] = value
    return root


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


def _public_safety_errors(value: Any, *, label: str, allowed_absolute_prefixes: tuple[str, ...] = ()) -> list[str]:
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
            allowed_prefixes = ALLOWED_ABSOLUTE_PREFIXES + allowed_absolute_prefixes
            if match not in ALLOWED_ABSOLUTE_PATHS and not any(match.startswith(prefix) for prefix in allowed_prefixes):
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
    dataset_toml_path = _safe_relative(dataset_dir, manifest.get("dataset_toml"))
    if dataset_toml_path is None:
        errors.append("dataset_toml must be a safe relative path")
    elif not dataset_toml_path.is_file():
        errors.append("dataset_toml file is missing")
    else:
        dataset_toml_rel = dataset_toml_path.relative_to(dataset_dir).as_posix()
        dataset_toml = dataset_toml_path.read_text(encoding="utf-8")
        for snippet in (
            'name = "authzbench-saas-public-skeleton"',
            'version = "public-skeleton"',
            'evidence_status = "generated_public_skeleton"',
            "harbor_execution_verified = false",
            "harbor_publish_verified = false",
            "not Harbor publish evidence",
            "not Harbor execution evidence",
        ):
            if snippet not in dataset_toml:
                errors.append(f"{dataset_toml_rel} missing {snippet}")
        errors.extend(_public_safety_errors(dataset_toml, label=dataset_toml_rel))
        try:
            dataset_config = _load_toml(dataset_toml_path)
        except Exception as exc:
            errors.append(str(exc))
        else:
            authzbench = dataset_config.get("metadata", {}).get("authzbench")
            if dataset_config.get("name") != "authzbench-saas-public-skeleton":
                errors.append(f"{dataset_toml_rel}: name must be authzbench-saas-public-skeleton")
            if dataset_config.get("version") != "public-skeleton":
                errors.append(f"{dataset_toml_rel}: version must be public-skeleton")
            task_refs = dataset_config.get("tasks")
            if not isinstance(task_refs, list):
                errors.append(f"{dataset_toml_rel}: tasks must be a list")
                task_refs = []
            manifest_task_refs = [task.get("harbor_task_dir") for task in manifest.get("tasks", []) if isinstance(task, dict)]
            if task_refs != manifest_task_refs:
                errors.append(f"{dataset_toml_rel}: tasks must match dataset-manifest harbor_task_dir order")
            if not isinstance(authzbench, dict):
                errors.append(f"{dataset_toml_rel}: [metadata.authzbench] table is required")
                authzbench = {}
            if authzbench.get("skeleton_schema_version") != SCHEMA_VERSION:
                errors.append(f"{dataset_toml_rel}: metadata.authzbench.skeleton_schema_version must be {SCHEMA_VERSION}")
            if authzbench.get("private_task_count") != 0:
                errors.append(f"{dataset_toml_rel}: metadata.authzbench.private_task_count must be 0")
            if authzbench.get("harbor_execution_verified") is not False:
                errors.append(f"{dataset_toml_rel}: metadata.authzbench.harbor_execution_verified must be false")
            if authzbench.get("harbor_publish_verified") is not False:
                errors.append(f"{dataset_toml_rel}: metadata.authzbench.harbor_publish_verified must be false")
    run_config_path = _safe_relative(dataset_dir, manifest.get("reference_run_config"))
    if run_config_path is None:
        errors.append("reference_run_config must be a safe relative path")
    elif not run_config_path.is_file():
        errors.append("reference_run_config file is missing")
    else:
        run_config_rel = run_config_path.relative_to(dataset_dir).as_posix()
        run_config = run_config_path.read_text(encoding="utf-8")
        for snippet in (
            "job_name: authzbench-public-skeleton-smoke",
            "tasks:",
            "agents:",
            "  - name: oracle",
            "environment:",
            "  type: docker",
            "/logs/artifacts",
            "not evidence that Harbor execution has been verified",
        ):
            if snippet not in run_config:
                errors.append(f"{run_config_rel} missing {snippet}")
        errors.extend(
            _public_safety_errors(
                run_config,
                label=run_config_rel,
                allowed_absolute_prefixes=(dataset_dir.as_posix() + "/",),
            )
        )

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be a list")
        tasks = []
    if not tasks:
        errors.append("tasks must contain at least one public task")
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
            "environment/Dockerfile": task_dir / "environment" / "Dockerfile",
            "environment/context.json": task_dir / "environment" / "context.json",
            "solution/solve.sh": task_dir / "solution" / "solve.sh",
            "verifier/task_manifest.json": task_dir / "verifier" / "task_manifest.json",
            "tests/Dockerfile": task_dir / "tests" / "Dockerfile",
            "tests/task_manifest.json": task_dir / "tests" / "task_manifest.json",
            "tests/test.sh": task_dir / "tests" / "test.sh",
            "tests/authzbench/score.py": task_dir / "tests" / "authzbench" / "score.py",
            "tests/authzbench/core.py": task_dir / "tests" / "authzbench" / "core.py",
            "tests/apps/project_mgmt/app.py": task_dir / "tests" / "apps" / "project_mgmt" / "app.py",
            "tests/environment/Dockerfile": task_dir / "tests" / "environment" / "Dockerfile",
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
                'schema_version = "1.3"',
                "[task]",
                "[metadata.authzbench]",
                f'skeleton_schema_version = "{SCHEMA_VERSION}"',
                "private_execution = false",
                "harbor_execution_verified = false",
                "[verifier]",
                'environment_mode = "separate"',
                "[agent]",
                "[environment]",
                "[metadata.authzbench.verifier]",
                'test_script = "tests/test.sh"',
                'scorer_contract = "v0-candidate-authz-evidence"',
            )
            for snippet in required_snippets:
                if snippet not in task_toml:
                    errors.append(f"{rel_task_dir}: task.toml missing {snippet}")
            if manifest.get("harness_lane") == "live_http_tool_agent" and "request correlation" not in task_toml:
                errors.append(f"{rel_task_dir}: live HTTP task.toml must mention request correlation")
            errors.extend(_public_safety_errors(task_toml, label=f"{rel_task_dir}/task.toml"))
            try:
                task_config = _load_toml(required_files["task.toml"])
            except Exception as exc:
                errors.append(str(exc))
            else:
                task_table = task_config.get("task")
                metadata = task_config.get("metadata")
                authzbench = metadata.get("authzbench") if isinstance(metadata, dict) else None
                verifier = task_config.get("verifier")
                agent = task_config.get("agent")
                environment = task_config.get("environment")
                if not isinstance(task_table, dict):
                    errors.append(f"{rel_task_dir}: task.toml [task] table is required")
                    task_table = {}
                if not isinstance(authzbench, dict):
                    errors.append(f"{rel_task_dir}: task.toml [metadata.authzbench] table is required")
                    authzbench = {}
                if not isinstance(verifier, dict):
                    errors.append(f"{rel_task_dir}: task.toml [verifier] table is required")
                    verifier = {}
                if not isinstance(agent, dict):
                    errors.append(f"{rel_task_dir}: task.toml [agent] table is required")
                    agent = {}
                if not isinstance(environment, dict):
                    errors.append(f"{rel_task_dir}: task.toml [environment] table is required")
                    environment = {}

                if task_config.get("schema_version") != "1.3":
                    errors.append(f"{rel_task_dir}: task.toml schema_version must be 1.3")
                if authzbench.get("skeleton_schema_version") != SCHEMA_VERSION:
                    errors.append(f"{rel_task_dir}: metadata.authzbench.skeleton_schema_version must be {SCHEMA_VERSION}")
                if authzbench.get("id") != task_id:
                    errors.append(f"{rel_task_dir}: metadata.authzbench.id must match manifest entry")
                if authzbench.get("private_execution") is not False:
                    errors.append(f"{rel_task_dir}: metadata.authzbench.private_execution must be false")
                if authzbench.get("harbor_execution_verified") is not False:
                    errors.append(f"{rel_task_dir}: metadata.authzbench.harbor_execution_verified must be false")
                if verifier.get("environment_mode") != "separate":
                    errors.append(f"{rel_task_dir}: verifier.environment_mode must be separate")
                if verifier.get("network_mode") != "no-network":
                    errors.append(f"{rel_task_dir}: verifier.network_mode must be no-network")
                expected_agent_network = "allowlist" if manifest.get("harness_lane") == "live_http_tool_agent" else "no-network"
                if agent.get("network_mode") != expected_agent_network:
                    errors.append(f"{rel_task_dir}: agent.network_mode must be {expected_agent_network}")
                if environment.get("network_mode") != "no-network":
                    errors.append(f"{rel_task_dir}: environment.network_mode must be no-network")

        if required_files["environment/Dockerfile"].is_file():
            dockerfile = required_files["environment/Dockerfile"].read_text(encoding="utf-8")
            if "not Harbor execution evidence" not in dockerfile:
                errors.append(f"{rel_task_dir}: environment/Dockerfile must preserve non-evidence claim boundary")
            if "FROM python:" not in dockerfile:
                errors.append(f"{rel_task_dir}: environment/Dockerfile must define a base image")
            errors.extend(_public_safety_errors(dockerfile, label=f"{rel_task_dir}/environment/Dockerfile"))

        if required_files["tests/environment/Dockerfile"].is_file():
            verifier_dockerfile = required_files["tests/environment/Dockerfile"].read_text(encoding="utf-8")
            if "not Harbor verifier/scorer parity evidence" not in verifier_dockerfile:
                errors.append(
                    f"{rel_task_dir}: tests/environment/Dockerfile must preserve non-evidence claim boundary"
                )
            if "FROM python:" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/environment/Dockerfile must define a base image")
            errors.extend(
                _public_safety_errors(
                    verifier_dockerfile,
                    label=f"{rel_task_dir}/tests/environment/Dockerfile",
                )
            )

        if required_files["tests/Dockerfile"].is_file():
            verifier_dockerfile = required_files["tests/Dockerfile"].read_text(encoding="utf-8")
            if "not Harbor verifier/scorer parity evidence" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/Dockerfile must preserve non-evidence claim boundary")
            if "FROM python:" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/Dockerfile must define a base image")
            if "ENV PYTHONPATH=/tests" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/Dockerfile must expose copied public scorer code")
            if "COPY authzbench /tests/authzbench" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/Dockerfile must copy public authzbench scorer code")
            if "COPY apps /tests/apps" not in verifier_dockerfile:
                errors.append(f"{rel_task_dir}: tests/Dockerfile must copy public app replay code")
            errors.extend(_public_safety_errors(verifier_dockerfile, label=f"{rel_task_dir}/tests/Dockerfile"))

        if required_files["solution/solve.sh"].is_file():
            solution = required_files["solution/solve.sh"].read_text(encoding="utf-8")
            if "does not include a public oracle solution" not in solution:
                errors.append(f"{rel_task_dir}: solution/solve.sh must preserve placeholder oracle boundary")
            if "exit 64" not in solution:
                errors.append(f"{rel_task_dir}: solution/solve.sh must fail closed until a verified oracle exists")
            errors.extend(_public_safety_errors(solution, label=f"{rel_task_dir}/solution/solve.sh"))

        if required_files["tests/test.sh"].is_file():
            script = required_files["tests/test.sh"].read_text(encoding="utf-8")
            if "python3 -m authzbench.score" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must invoke authzbench.score")
            if "missing agent submission" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must handle missing agent submissions explicitly")
            if "/tests/task_manifest.json" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must use the verifier task manifest copy")
            if "/logs/artifacts/score.json" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write score artifact")
            if "/logs/artifacts/reward.json" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write reward.json artifact")
            if "/logs/artifacts/reward.txt" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write reward.txt artifact")
            if "/logs/verifier/reward.json" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write Harbor verifier reward.json")
            if "/logs/verifier/reward.txt" not in script:
                errors.append(f"{rel_task_dir}: tests/test.sh must write Harbor verifier reward.txt")
            errors.extend(_public_safety_errors(script, label=f"{rel_task_dir}/tests/test.sh"))

        for json_name in ("environment/context.json", "verifier/task_manifest.json", "tests/task_manifest.json"):
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
            if json_name == "tests/task_manifest.json" and data.get("id") != task_id:
                errors.append(f"{rel_task_dir}: tests task_manifest id must match manifest entry")
            if json_name == "tests/task_manifest.json" and data.get("split") == "private_holdout":
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
