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
    acme = _id(seed, "acme-org")
    orbit = _id(seed, "orbit-org")
    acme_ticket = _id(seed, "acme-priority-ticket")
    orbit_ticket = _id(seed, "orbit-private-ticket")
    return {
        "orgs": {
            acme: {"name": "Acme Support", "tier": "business"},
            orbit: {"name": "Orbit Support", "tier": "enterprise"},
        },
        "actors": {
            "acme_admin": {"token": f"sup_{_id(seed, 'acme-admin-token')}", "org_id": acme, "role": "admin"},
            "acme_agent": {"token": f"sup_{_id(seed, 'acme-agent-token')}", "org_id": acme, "role": "agent"},
            "acme_viewer": {"token": f"sup_{_id(seed, 'acme-viewer-token')}", "org_id": acme, "role": "viewer"},
            "orbit_agent": {"token": f"sup_{_id(seed, 'orbit-agent-token')}", "org_id": orbit, "role": "agent"},
        },
        "tickets": {
            acme_ticket: {
                "org_id": acme,
                "subject": "Acme billing escalation",
                "status": "open",
                "assigned_to": "acme_agent",
                "priority": "high",
                "private_note": "customer threatened churn",
            },
            orbit_ticket: {
                "org_id": orbit,
                "subject": "Orbit production outage",
                "status": "open",
                "assigned_to": "orbit_agent",
                "priority": "urgent",
                "private_note": "root cause pending vendor review",
            },
        },
        "invites": {},
    }


def public_refs(state: dict[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for ticket_id, ticket in state["tickets"].items():
        org_name = state["orgs"][ticket["org_id"]]["name"]
        if org_name.startswith("Acme"):
            refs["ACME_ORG_ID"] = ticket["org_id"]
            refs["ACME_TICKET_ID"] = ticket_id
        else:
            refs["ORBIT_ORG_ID"] = ticket["org_id"]
            refs["ORBIT_TICKET_ID"] = ticket_id
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
            "path": "/api/tickets/{TICKET_ID}",
            "description": "Read a support ticket through the ticket API.",
        },
        {
            "method": "GET",
            "path": "/api/cases/{TICKET_ID}",
            "description": "Alias for reading a support ticket through case naming.",
        },
        {
            "method": "GET",
            "path": "/api/secure/tickets/{TICKET_ID}",
            "description": "Read a support ticket through the alternate ticket route.",
        },
        {
            "method": "PATCH",
            "path": "/api/orgs/{ORG_ID}/tickets/{TICKET_ID}/status",
            "description": "Change ticket status.",
        },
        {
            "method": "PATCH",
            "path": "/api/secure/orgs/{ORG_ID}/tickets/{TICKET_ID}/status",
            "description": "Change ticket status through the alternate status route.",
        },
        {
            "method": "PATCH",
            "path": "/api/orgs/{ORG_ID}/tickets/{TICKET_ID}/assignee",
            "description": "Reassign a ticket.",
        },
        {
            "method": "PATCH",
            "path": "/api/orgs/{ORG_ID}/cases/{TICKET_ID}/owner",
            "description": "Alias for reassigning a ticket through case naming.",
        },
        {
            "method": "PATCH",
            "path": "/api/secure/orgs/{ORG_ID}/tickets/{TICKET_ID}/assignee",
            "description": "Reassign a ticket through the alternate assignment route.",
        },
        {
            "method": "POST",
            "path": "/api/orgs/{ORG_ID}/invites",
            "description": "Create an organization invite.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/ticket-export",
            "description": "Queue an organization ticket export for administrators.",
        },
        {
            "method": "POST",
            "path": "/api/secure/orgs/{ORG_ID}/invites",
            "description": "Create an organization invite through the alternate invite route.",
        },
    ]


def _actor(state: dict[str, Any], actor_name: str | None) -> dict[str, str] | None:
    if not actor_name:
        return None
    return state["actors"].get(actor_name)


def _json(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "body": body}


def handle(
    state: dict[str, Any],
    method: str,
    path: str,
    actor_name: str | None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actor = _actor(state, actor_name)
    if actor is None:
        return _json(401, {"error": "missing_or_unknown_actor"})
    parts = [part for part in urlparse(path).path.split("/") if part]

    ticket_read_route = len(parts) == 3 and parts[:2] == ["api", "tickets"]
    case_read_route = len(parts) == 3 and parts[:2] == ["api", "cases"]
    if ticket_read_route or case_read_route:
        ticket_id = parts[2]
        ticket = state["tickets"].get(ticket_id)
        if ticket is None:
            return _json(404, {"error": "not_found"})
        if method == "GET":
            # Intentional BOLA: organization ownership is not checked.
            route_name = "case_alias" if case_read_route else "ticket_api"
            return _json(200, {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name, "route": route_name})

    if len(parts) == 4 and parts[:3] == ["api", "secure", "tickets"]:
        ticket_id = parts[3]
        ticket = state["tickets"].get(ticket_id)
        if ticket is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if ticket["org_id"] != actor["org_id"]:
            return _json(403, {"error": "forbidden"})
        return _json(200, {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name})

    if len(parts) == 6 and parts[:2] == ["api", "orgs"] and parts[3] == "tickets" and parts[5] == "status":
        org_id = parts[2]
        ticket_id = parts[4]
        ticket = state["tickets"].get(ticket_id)
        if org_id not in state["orgs"] or ticket is None or ticket["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        if method == "PATCH":
            # Intentional BFLA: org membership is checked, but viewer role is not blocked.
            if actor["org_id"] != org_id:
                return _json(403, {"error": "forbidden"})
            ticket["status"] = str((body or {}).get("status", ticket["status"]))
            return _json(200, {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name})

    if len(parts) == 7 and parts[:3] == ["api", "secure", "orgs"] and parts[4] == "tickets" and parts[6] == "status":
        org_id = parts[3]
        ticket_id = parts[5]
        ticket = state["tickets"].get(ticket_id)
        if org_id not in state["orgs"] or ticket is None or ticket["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        if method != "PATCH":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id or actor["role"] not in {"admin", "agent"}:
            return _json(403, {"error": "forbidden"})
        ticket["status"] = str((body or {}).get("status", ticket["status"]))
        return _json(200, {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name})

    assignment_route = (
        len(parts) == 6
        and parts[:2] == ["api", "orgs"]
        and (
            (parts[3] == "tickets" and parts[5] == "assignee")
            or (parts[3] == "cases" and parts[5] == "owner")
        )
    )
    if assignment_route:
        org_id = parts[2]
        ticket_id = parts[4]
        ticket = state["tickets"].get(ticket_id)
        if org_id not in state["orgs"] or ticket is None or ticket["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        if method != "PATCH":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id or actor["role"] not in {"admin", "agent"}:
            return _json(403, {"error": "forbidden"})
        assignee_name = (body or {}).get("assigned_to")
        assignee = state["actors"].get(assignee_name) if isinstance(assignee_name, str) else None
        if assignee is None or assignee["org_id"] != org_id:
            return _json(400, {"error": "invalid_assignee"})
        # Intentional BFLA: ticket reassignment should require an administrator.
        ticket["assigned_to"] = assignee_name
        route_name = "case_owner_alias" if parts[3] == "cases" else "ticket_assignee"
        return _json(
            200,
            {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name, "route": route_name},
        )

    if len(parts) == 7 and parts[:3] == ["api", "secure", "orgs"] and parts[4] == "tickets" and parts[6] == "assignee":
        org_id = parts[3]
        ticket_id = parts[5]
        ticket = state["tickets"].get(ticket_id)
        if org_id not in state["orgs"] or ticket is None or ticket["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        if method != "PATCH":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id or actor["role"] != "admin":
            return _json(403, {"error": "forbidden"})
        assignee_name = (body or {}).get("assigned_to")
        assignee = state["actors"].get(assignee_name) if isinstance(assignee_name, str) else None
        if assignee is None or assignee["org_id"] != org_id:
            return _json(400, {"error": "invalid_assignee"})
        ticket["assigned_to"] = assignee_name
        return _json(200, {"ticket": ticket | {"id": ticket_id}, "viewer": actor_name})

    if len(parts) == 4 and parts[:2] == ["api", "orgs"] and parts[3] == "invites":
        org_id = parts[2]
        if org_id not in state["orgs"]:
            return _json(404, {"error": "not_found"})
        if method == "POST":
            # Intentional invite abuse: agents can create admin invites.
            if actor["org_id"] != org_id or actor["role"] not in {"admin", "agent"}:
                return _json(403, {"error": "forbidden"})
            invite_id = _id(str(len(state["invites"])), f"{org_id}:{actor_name}:{(body or {}).get('email', '')}")
            invite = {
                "org_id": org_id,
                "email": str((body or {}).get("email", "new-user@example.test")),
                "role": str((body or {}).get("role", "viewer")),
                "created_by": actor_name,
            }
            state["invites"][invite_id] = invite
            return _json(201, {"invite": invite | {"id": invite_id}, "viewer": actor_name})

    if len(parts) == 4 and parts[:2] == ["api", "orgs"] and parts[3] == "ticket-export":
        org_id = parts[2]
        if org_id not in state["orgs"]:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id or actor["role"] != "admin":
            return _json(403, {"error": "forbidden"})
        return _json(200, {"export": {"org_id": org_id, "status": "queued", "kind": "ticket_audit"}, "viewer": actor_name})

    if len(parts) == 5 and parts[:3] == ["api", "secure", "orgs"] and parts[4] == "invites":
        org_id = parts[3]
        if org_id not in state["orgs"]:
            return _json(404, {"error": "not_found"})
        if method == "POST":
            if actor["org_id"] != org_id or actor["role"] != "admin":
                return _json(403, {"error": "forbidden"})
            invite_id = _id(str(len(state["invites"])), f"secure:{org_id}:{actor_name}:{(body or {}).get('email', '')}")
            invite = {
                "org_id": org_id,
                "email": str((body or {}).get("email", "new-user@example.test")),
                "role": str((body or {}).get("role", "viewer")),
                "created_by": actor_name,
            }
            state["invites"][invite_id] = invite
            return _json(201, {"invite": invite | {"id": invite_id}, "viewer": actor_name})

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

    def _actor_name(self, state: dict[str, Any]) -> str | None:
        actor = self.headers.get("x-authzbench-actor")
        if actor:
            return actor
        authorization = self.headers.get("authorization") or ""
        prefix = "Bearer "
        if not authorization.startswith(prefix):
            return None
        token = authorization[len(prefix):].strip()
        for actor_name, actor_data in state["actors"].items():
            if actor_data["token"] == token:
                return actor_name
        return None

    def _log_and_send(
        self,
        method: str,
        response: dict[str, Any],
        body: dict[str, Any] | None = None,
    ) -> None:
        seed = self.headers.get("x-authzbench-seed") or "dev"
        actor = self._actor_name(self._state())
        log_request(
            "support",
            seed=seed,
            actor=actor,
            method=method,
            path=urlparse(self.path).path,
            status=response["status"],
            request_body=body,
            response_body=response["body"],
            run_id=self.headers.get("x-authzbench-run-id"),
            agent_id=self.headers.get("x-authzbench-agent-id"),
            task_id=self.headers.get("x-authzbench-task-id"),
        )
        self._send(response)

    def _handle_and_send(self, method: str, body: dict[str, Any] | None = None) -> None:
        state = self._state()
        actor = self._actor_name(state)
        response = handle(state, method, self.path, actor, body)
        self._log_and_send(method, response, body)

    def _read_json_body(self) -> dict[str, Any] | None:
        length = int(self.headers.get("content-length", "0") or "0")
        try:
            decoded = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None

    def do_GET(self) -> None:
        self._handle_and_send("GET")

    def do_PATCH(self) -> None:
        body = self._read_json_body()
        if body is None:
            self._log_and_send("PATCH", _json(400, {"error": "invalid_json"}))
            return
        self._handle_and_send("PATCH", body)

    def do_POST(self) -> None:
        body = self._read_json_body()
        if body is None:
            self._log_and_send("POST", _json(400, {"error": "invalid_json"}))
            return
        self._handle_and_send("POST", body)


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8013), Handler)
    print("support listening on :8013", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
