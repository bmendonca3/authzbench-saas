from __future__ import annotations

import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


def _id(seed: str, label: str) -> str:
    return hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()[:10]


def seed_state(seed: str) -> dict[str, Any]:
    alpha = _id(seed, "tenant-alpha")
    beta = _id(seed, "tenant-beta")
    alpha_project = _id(seed, "alpha-project")
    beta_project = _id(seed, "beta-project")
    alpha_task = _id(seed, "alpha-private-task")
    beta_task = _id(seed, "beta-private-task")
    return {
        "tenants": {
            alpha: {"name": "Northstar Product"},
            beta: {"name": "Helio Research"},
        },
        "actors": {
            "alpha_owner": {"token": f"pm_{_id(seed, 'alpha-owner-token')}", "tenant_id": alpha, "role": "owner"},
            "alpha_viewer": {"token": f"pm_{_id(seed, 'alpha-viewer-token')}", "tenant_id": alpha, "role": "viewer"},
            "beta_member": {"token": f"pm_{_id(seed, 'beta-member-token')}", "tenant_id": beta, "role": "member"},
        },
        "projects": {
            alpha_project: {"tenant_id": alpha, "name": "Northstar Roadmap"},
            beta_project: {"tenant_id": beta, "name": "Helio Launch"},
        },
        "tasks": {
            alpha_task: {
                "tenant_id": alpha,
                "project_id": alpha_project,
                "title": "Private acquisition checklist",
                "status": "open",
                "private_note": "board packet due friday",
            },
            beta_task: {
                "tenant_id": beta,
                "project_id": beta_project,
                "title": "Helio launch timeline",
                "status": "open",
                "private_note": "press embargo ends monday",
            },
        },
    }


def public_refs(state: dict[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for task_id, task in state["tasks"].items():
        tenant_name = state["tenants"][task["tenant_id"]]["name"]
        if tenant_name.startswith("Northstar"):
            refs["ALPHA_PROJECT_ID"] = task["project_id"]
            refs["ALPHA_PRIVATE_TASK_ID"] = task_id
            refs["ALPHA_TENANT_ID"] = task["tenant_id"]
        else:
            refs["BETA_PROJECT_ID"] = task["project_id"]
            refs["BETA_PRIVATE_TASK_ID"] = task_id
            refs["BETA_TENANT_ID"] = task["tenant_id"]
    return refs


def public_actors(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        name: {"token": actor["token"], "tenant_id": actor["tenant_id"], "role": actor["role"]}
        for name, actor in state["actors"].items()
    }


def public_api_docs() -> list[dict[str, str]]:
    return [
        {
            "method": "GET",
            "path": "/api/projects/{PROJECT_ID}/tasks/{TASK_ID}",
            "description": "Read a task from the non-secure project task API.",
        },
        {
            "method": "PATCH",
            "path": "/api/projects/{PROJECT_ID}/tasks/{TASK_ID}",
            "description": "Update task status for authorized same-tenant owner/member actors.",
        },
        {
            "method": "GET",
            "path": "/api/secure/projects/{PROJECT_ID}/tasks/{TASK_ID}",
            "description": "Read a task through the secure route that enforces tenant ownership.",
        },
    ]


def _actor(state: dict[str, Any], actor_name: str | None) -> dict[str, str] | None:
    if not actor_name:
        return None
    return state["actors"].get(actor_name)


def _json(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "body": body}


def handle(state: dict[str, Any], method: str, path: str, actor_name: str | None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    actor = _actor(state, actor_name)
    if actor is None:
        return _json(401, {"error": "missing_or_unknown_actor"})

    parts = [part for part in urlparse(path).path.split("/") if part]
    if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "tasks":
        project_id = parts[2]
        task_id = parts[4]
        task = state["tasks"].get(task_id)
        if task is None or task["project_id"] != project_id:
            return _json(404, {"error": "not_found"})
        if method == "GET":
            # Intentional BOLA: project/task tenant is not checked against actor tenant.
            return _json(200, {"task": task | {"id": task_id}, "viewer": actor_name})
        if method == "PATCH":
            if task["tenant_id"] != actor["tenant_id"] or actor["role"] not in {"owner", "member"}:
                return _json(403, {"error": "forbidden"})
            task["status"] = str((body or {}).get("status", task["status"]))
            return _json(200, {"task": task | {"id": task_id}})

    if len(parts) == 6 and parts[:3] == ["api", "secure", "projects"] and parts[4] == "tasks":
        project_id = parts[3]
        task_id = parts[5]
        task = state["tasks"].get(task_id)
        if task is None or task["project_id"] != project_id:
            return _json(404, {"error": "not_found"})
        if task["tenant_id"] != actor["tenant_id"]:
            return _json(403, {"error": "forbidden"})
        return _json(200, {"task": task | {"id": task_id}, "viewer": actor_name})

    return _json(404, {"error": "unknown_route"})


class Handler(BaseHTTPRequestHandler):
    state = seed_state("dev")

    def _send(self, response: dict[str, Any]) -> None:
        encoded = json.dumps(response["body"]).encode()
        self.send_response(response["status"])
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        self._send(handle(self.state, "GET", self.path, self.headers.get("x-authzbench-actor")))

    def do_PATCH(self) -> None:
        length = int(self.headers.get("content-length", "0") or "0")
        body = json.loads(self.rfile.read(length) or b"{}")
        self._send(handle(self.state, "PATCH", self.path, self.headers.get("x-authzbench-actor"), body))


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8011), Handler)
    print("project_mgmt listening on :8011", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
