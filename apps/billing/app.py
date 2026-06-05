from __future__ import annotations

import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from apps.request_logging import log_request


def _id(seed: str, label: str) -> str:
    return hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()[:10]


def seed_state(seed: str) -> dict[str, Any]:
    owner_org = _id(seed, "owner-org")
    peer_org = _id(seed, "peer-org")
    owner_invoice = _id(seed, "owner-invoice")
    peer_invoice = _id(seed, "peer-invoice")
    return {
        "orgs": {
            owner_org: {"name": "Atlas Billing", "plan": "pro", "billing_contact": "cfo@atlas.test"},
            peer_org: {"name": "Beacon Billing", "plan": "enterprise", "billing_contact": "finance@beacon.test"},
        },
        "actors": {
            "atlas_admin": {"token": f"bill_{_id(seed, 'atlas-admin-token')}", "org_id": owner_org, "role": "admin"},
            "atlas_member": {"token": f"bill_{_id(seed, 'atlas-member-token')}", "org_id": owner_org, "role": "member"},
            "beacon_member": {"token": f"bill_{_id(seed, 'beacon-member-token')}", "org_id": peer_org, "role": "member"},
        },
        "invoices": {
            owner_invoice: {"org_id": owner_org, "amount": 4900, "status": "open", "memo": "Atlas renewal"},
            peer_invoice: {"org_id": peer_org, "amount": 28900, "status": "open", "memo": "Beacon expansion"},
        },
    }


def public_refs(state: dict[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for invoice_id, invoice in state["invoices"].items():
        org_name = state["orgs"][invoice["org_id"]]["name"]
        if org_name.startswith("Atlas"):
            refs["ATLAS_ORG_ID"] = invoice["org_id"]
            refs["ATLAS_INVOICE_ID"] = invoice_id
        else:
            refs["BEACON_ORG_ID"] = invoice["org_id"]
            refs["BEACON_INVOICE_ID"] = invoice_id
    return refs


def public_actors(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        name: {"token": actor["token"], "org_id": actor["org_id"], "role": actor["role"]}
        for name, actor in state["actors"].items()
    }


def public_api_docs() -> list[dict[str, str]]:
    return [
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/invoices/{INVOICE_ID}",
            "description": "Read an invoice through the org invoice API.",
        },
        {
            "method": "PATCH",
            "path": "/api/orgs/{ORG_ID}/settings/plan",
            "description": "Change an organization's plan setting.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/settings/plan",
            "description": "Read an organization's plan setting.",
        },
        {
            "method": "GET",
            "path": "/api/secure/orgs/{ORG_ID}/settings/plan",
            "description": "Read plan settings through the alternate plan route.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/settings/admin-export",
            "description": "Admin export route for organization billing settings.",
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

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3] == "invoices":
        org_id = parts[2]
        invoice_id = parts[4]
        invoice = state["invoices"].get(invoice_id)
        if invoice is None or invoice["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        if method == "GET":
            if invoice["org_id"] != actor["org_id"]:
                return _json(403, {"error": "forbidden"})
            return _json(200, {"invoice": invoice | {"id": invoice_id}, "viewer": actor_name})

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3] == "settings":
        org_id = parts[2]
        if org_id not in state["orgs"]:
            return _json(404, {"error": "not_found"})
        if parts[4] != "plan":
            if parts[4] != "admin-export":
                return _json(404, {"error": "not_found"})
            if method != "GET":
                return _json(405, {"error": "method_not_allowed"})
            if actor["org_id"] != org_id or actor["role"] != "admin":
                return _json(403, {"error": "forbidden"})
            return _json(200, {"export": {"org_id": org_id, "status": "queued"}, "viewer": actor_name})
        if method == "GET":
            # Intentional BFLA: org membership is checked, but admin role is not.
            if actor["org_id"] != org_id:
                return _json(403, {"error": "forbidden"})
            return _json(200, {"org": state["orgs"][org_id] | {"id": org_id}, "viewer": actor_name})
        if method == "PATCH":
            # Intentional BFLA: checks org membership but not admin role.
            if actor["org_id"] != org_id:
                return _json(403, {"error": "forbidden"})
            new_plan = str((body or {}).get("plan", state["orgs"][org_id]["plan"]))
            state["orgs"][org_id]["plan"] = new_plan
            return _json(200, {"org": state["orgs"][org_id] | {"id": org_id}, "viewer": actor_name})

    if len(parts) == 6 and parts[:3] == ["api", "secure", "orgs"] and parts[4:] == ["settings", "plan"]:
        org_id = parts[3]
        if org_id not in state["orgs"]:
            return _json(404, {"error": "not_found"})
        if actor["org_id"] != org_id or actor["role"] != "admin":
            return _json(403, {"error": "forbidden"})
        return _json(200, {"org": state["orgs"][org_id] | {"id": org_id}, "viewer": actor_name})

    return _json(404, {"error": "unknown_route"})


class Handler(BaseHTTPRequestHandler):
    state = seed_state("dev")
    states: dict[str, dict[str, Any]] = {"dev": state}

    def _state(self) -> dict[str, Any]:
        seed = self.headers.get("x-authzbench-seed") or "dev"
        if seed not in self.states:
            self.states[seed] = seed_state(seed)
        return self.states[seed]

    def _send(self, response: dict[str, Any]) -> None:
        encoded = json.dumps(response["body"]).encode()
        self.send_response(response["status"])
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _handle_and_send(self, method: str, body: dict[str, Any] | None = None) -> None:
        seed = self.headers.get("x-authzbench-seed") or "dev"
        actor = self.headers.get("x-authzbench-actor")
        response = handle(self._state(), method, self.path, actor, body)
        log_request(
            "billing",
            seed=seed,
            actor=actor,
            method=method,
            path=urlparse(self.path).path,
            status=response["status"],
            response_body=response["body"],
            run_id=self.headers.get("x-authzbench-run-id"),
            agent_id=self.headers.get("x-authzbench-agent-id"),
            task_id=self.headers.get("x-authzbench-task-id"),
        )
        self._send(response)

    def do_GET(self) -> None:
        self._handle_and_send("GET")

    def do_PATCH(self) -> None:
        length = int(self.headers.get("content-length", "0") or "0")
        body = json.loads(self.rfile.read(length) or b"{}")
        self._handle_and_send("PATCH", body)


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8012), Handler)
    print("billing listening on :8012", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
