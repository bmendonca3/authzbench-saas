from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path
from typing import Any


APP_MODULES = {
    "project_mgmt": "apps.project_mgmt.app",
    "billing": "apps.billing.app",
    "support": "apps.support.app",
    "file_sharing": "apps.file_sharing.app",
    "api_tokens": "apps.api_tokens.app",
    "audit_settings": "apps.audit_settings.app",
}

APP_TARGETS = {
    "project_mgmt": {"base_url": "http://127.0.0.1:8011", "container_base_url": "http://project_mgmt:8011"},
    "billing": {"base_url": "http://127.0.0.1:8012", "container_base_url": "http://billing:8012"},
    "support": {"base_url": "http://127.0.0.1:8013", "container_base_url": "http://support:8013"},
    "file_sharing": {"base_url": "http://127.0.0.1:8014", "container_base_url": "http://file_sharing:8014"},
    "api_tokens": {"base_url": "http://127.0.0.1:8015", "container_base_url": "http://api_tokens:8015"},
    "audit_settings": {"base_url": "http://127.0.0.1:8016", "container_base_url": "http://audit_settings:8016"},
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def stable_json_sha256(data: Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def benchmark_fingerprint(task_items: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Return a comparable task/scoring fingerprint without exposing task ids."""
    canonical_tasks = [
        {
            "path": path,
            "manifest": task,
        }
        for path, task in sorted(task_items, key=lambda item: item[0])
    ]
    counts = {
        "task_count": len(canonical_tasks),
        "vulnerable_task_count": sum(1 for item in canonical_tasks if item["manifest"].get("expected_vulnerable") is True),
        "control_task_count": sum(1 for item in canonical_tasks if item["manifest"].get("expected_vulnerable") is not True),
        "denial_control_task_count": sum(
            1 for item in canonical_tasks if item["manifest"].get("control_type") == "denial"
        ),
        "authorized_allow_control_task_count": sum(
            1 for item in canonical_tasks if item["manifest"].get("control_type") == "authorized_allow"
        ),
    }
    return {
        "schema_version": "benchmark-fingerprint-v1",
        "task_set_sha256": stable_json_sha256(canonical_tasks),
        "task_path_set_sha256": stable_json_sha256([item["path"] for item in canonical_tasks]),
        "score_policy_version": "score-policy-v1",
        "scorer_contract": "v0-candidate-authz-evidence",
        "evidence_contract_version": "evidence-requirements-v1",
        **counts,
    }


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


def _request_headers(request: dict[str, Any]) -> dict[str, str]:
    raw_headers = request.get("headers") or {}
    if not isinstance(raw_headers, dict):
        raise ValueError("request.headers must be an object when supplied")
    return {str(key).lower(): str(value) for key, value in raw_headers.items()}


def _actor_from_bearer_token(app: Any, state: dict[str, Any], token: str) -> str | None:
    if hasattr(app, "public_actors"):
        for actor_name, actor_data in app.public_actors(state).items():
            if actor_data.get("token") == token:
                return str(actor_name)
    return None


def _request_actor(app: Any, state: dict[str, Any], request: dict[str, Any]) -> str | None:
    actor = request.get("actor")
    actor_name = str(actor) if actor is not None else None
    authorization = _request_headers(request).get("authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return actor_name

    token_actor = _actor_from_bearer_token(app, state, authorization[len(prefix):].strip())
    if token_actor is None:
        return None
    if actor_name is not None and actor_name != token_actor:
        return None
    return token_actor


def replay_request(task: dict[str, Any], request: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    app = load_app(task["app"])
    if state is None:
        state = app.seed_state(task["seed"])
    actor = _request_actor(app, state, request)
    method = str(request.get("method", "GET")).upper()
    path = request.get("path")
    body = request.get("body") or {}
    if not isinstance(path, str):
        raise ValueError("request.path must be a string")
    return app.handle(state, method, path, actor, body)
