from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


APP_MODULES = {
    "project_mgmt": "apps.project_mgmt.app",
    "billing": "apps.billing.app",
    "support": "apps.support.app",
    "file_sharing": "apps.file_sharing.app",
}

APP_TARGETS = {
    "project_mgmt": {"base_url": "http://127.0.0.1:8011", "container_base_url": "http://project_mgmt:8011"},
    "billing": {"base_url": "http://127.0.0.1:8012", "container_base_url": "http://billing:8012"},
    "support": {"base_url": "http://127.0.0.1:8013", "container_base_url": "http://support:8013"},
    "file_sharing": {"base_url": "http://127.0.0.1:8014", "container_base_url": "http://file_sharing:8014"},
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def load_app(app_name: str):
    try:
        return importlib.import_module(APP_MODULES[app_name])
    except KeyError as exc:
        raise ValueError(f"unknown app: {app_name}") from exc


def build_context(task: dict[str, Any]) -> dict[str, Any]:
    app = load_app(task["app"])
    state = app.seed_state(task["seed"])
    refs = app.public_refs(state)
    actors = app.public_actors(state)
    api_docs = app.public_api_docs() if hasattr(app, "public_api_docs") else []
    return {
        "task_id": task["id"],
        "app": task["app"],
        "seed": task["seed"],
        "policy": task["policy"],
        "objective": task["objective"],
        "allowed_hosts": task["allowed_hosts"],
        "target": APP_TARGETS[task["app"]] | {"seed_header": "x-authzbench-seed", "seed": task["seed"]},
        "actors": actors,
        "refs": refs,
        "api_docs": api_docs,
        "output_schema": task["output_schema"],
    }


def resolve_path(path_template: str, refs: dict[str, str]) -> str:
    path = path_template
    for name, value in refs.items():
        path = path.replace("{" + name + "}", str(value))
    return path


def resolve_templates(value: Any, refs: dict[str, str]) -> Any:
    if isinstance(value, str):
        return resolve_path(value, refs)
    if isinstance(value, list):
        return [resolve_templates(item, refs) for item in value]
    if isinstance(value, dict):
        return {key: resolve_templates(item, refs) for key, item in value.items()}
    return value


def replay_request(task: dict[str, Any], request: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    app = load_app(task["app"])
    if state is None:
        state = app.seed_state(task["seed"])
    actor = request.get("actor")
    method = str(request.get("method", "GET")).upper()
    path = request.get("path")
    body = request.get("body") or {}
    if not isinstance(path, str):
        raise ValueError("request.path must be a string")
    return app.handle(state, method, path, actor, body)
