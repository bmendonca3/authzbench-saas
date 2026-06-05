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
    nimbus = _id(seed, "nimbus-org")
    quasar = _id(seed, "quasar-org")
    nimbus_log = _id(seed, "nimbus-audit-log")
    quasar_log = _id(seed, "quasar-audit-log")
    nimbus_export = _id(seed, "nimbus-audit-export")
    return {
        "orgs": {
            nimbus: {"name": "Nimbus Security", "tier": "enterprise"},
            quasar: {"name": "Quasar Security", "tier": "enterprise"},
        },
        "actors": {
            "nimbus_admin": {"token": f"audit_{_id(seed, 'nimbus-admin-token')}", "org_id": nimbus, "role": "admin"},
            "nimbus_auditor": {
                "token": f"audit_{_id(seed, 'nimbus-auditor-token')}",
                "org_id": nimbus,
                "role": "auditor",
            },
            "nimbus_member": {"token": f"audit_{_id(seed, 'nimbus-member-token')}", "org_id": nimbus, "role": "member"},
            "quasar_admin": {"token": f"audit_{_id(seed, 'quasar-admin-token')}", "org_id": quasar, "role": "admin"},
        },
        "audit_logs": {
            nimbus_log: {
                "org_id": nimbus,
                "classification": "security",
                "events": ["sso_required_enabled", "session_timeout_updated", "token_rotation_completed"],
            },
            quasar_log: {
                "org_id": quasar,
                "classification": "security",
                "events": ["admin_export_started", "sso_bypass_blocked", "privileged_role_changed"],
            },
        },
        "settings": {
            nimbus: {
                "sso_required": True,
                "session_timeout_minutes": 45,
                "external_audit_exports": False,
                "updated_by": "system",
            },
            quasar: {
                "sso_required": True,
                "session_timeout_minutes": 30,
                "external_audit_exports": False,
                "updated_by": "system",
            },
        },
        "exports": {
            nimbus_export: {
                "org_id": nimbus,
                "classification": "restricted",
                "format": "jsonl",
                "summary": "security configuration changes and admin audit events",
            },
        },
    }


def public_refs(state: dict[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for org_id, org in state["orgs"].items():
        if org["name"].startswith("Nimbus"):
            refs["NIMBUS_ORG_ID"] = org_id
        else:
            refs["QUASAR_ORG_ID"] = org_id
    for log_id, log in state["audit_logs"].items():
        org_name = state["orgs"][log["org_id"]]["name"]
        if org_name.startswith("Nimbus"):
            refs["NIMBUS_AUDIT_LOG_ID"] = log_id
        else:
            refs["QUASAR_AUDIT_LOG_ID"] = log_id
    for export_id in state["exports"]:
        refs["NIMBUS_EXPORT_ID"] = export_id
    return refs


def public_actors(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        name: {"token": actor["token"], "org_id": actor["org_id"], "role": actor["role"]}
        for name, actor in state["actors"].items()
    }


def public_api_docs() -> list[dict[str, str]]:
    return [
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/audit-logs/{AUDIT_LOG_ID}",
            "description": "Read an audit log by organization and log ID.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/events/{AUDIT_LOG_ID}",
            "description": "Alias for reading audit events by organization and event ID.",
        },
        {
            "method": "GET",
            "path": "/api/secure/orgs/{ORG_ID}/audit-logs/{AUDIT_LOG_ID}",
            "description": "Read an audit log through the alternate audit route.",
        },
        {
            "method": "PATCH",
            "path": "/api/orgs/{ORG_ID}/security/settings",
            "description": "Update organization security settings.",
        },
        {
            "method": "PATCH",
            "path": "/api/secure/orgs/{ORG_ID}/security/settings",
            "description": "Update organization security settings through the alternate settings route.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/audit-exports/{EXPORT_ID}",
            "description": "Read an audit export by organization and export ID.",
        },
        {
            "method": "GET",
            "path": "/api/orgs/{ORG_ID}/compliance/export-preview/{EXPORT_ID}",
            "description": "Preview a compliance export for audit-capable roles.",
        },
        {
            "method": "GET",
            "path": "/api/secure/orgs/{ORG_ID}/audit-exports/{EXPORT_ID}",
            "description": "Read an audit export through the alternate export route.",
        },
    ]


def _actor(state: dict[str, Any], actor_name: str | None) -> dict[str, Any] | None:
    if not actor_name:
        return None
    return state["actors"].get(actor_name)


def _json(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "body": body}


def _actor_body(actor_name: str | None, actor: dict[str, Any]) -> dict[str, Any]:
    return {"actor": actor_name, "org_id": actor["org_id"], "role": actor["role"]}


def _audit_log_body(log_id: str, log: dict[str, Any], actor_name: str | None, actor: dict[str, Any], route: str) -> dict[str, Any]:
    return {"audit_log": log | {"id": log_id}, "viewer": _actor_body(actor_name, actor), "route": route}


def _settings_body(org_id: str, settings: dict[str, Any], actor_name: str | None, actor: dict[str, Any], route: str) -> dict[str, Any]:
    return {"settings": settings | {"org_id": org_id}, "viewer": _actor_body(actor_name, actor), "route": route}


def _export_body(export_id: str, export: dict[str, Any], actor_name: str | None, actor: dict[str, Any], route: str) -> dict[str, Any]:
    return {"export": export | {"id": export_id}, "viewer": _actor_body(actor_name, actor), "route": route}


def _apply_settings(settings: dict[str, Any], actor_name: str | None, body: dict[str, Any] | None) -> None:
    updates = body or {}
    if "sso_required" in updates:
        settings["sso_required"] = bool(updates["sso_required"])
    if "session_timeout_minutes" in updates:
        settings["session_timeout_minutes"] = int(updates["session_timeout_minutes"])
    if "external_audit_exports" in updates:
        settings["external_audit_exports"] = bool(updates["external_audit_exports"])
    settings["updated_by"] = actor_name or "unknown"


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

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3] == "audit-logs":
        org_id = parts[2]
        log_id = parts[4]
        audit_log = state["audit_logs"].get(log_id)
        if org_id not in state["orgs"] or audit_log is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if audit_log["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        # Intentional BOLA: the audit route trusts path ownership but misses actor org binding.
        return _json(200, _audit_log_body(log_id, audit_log, actor_name, actor, "audit_log_api"))

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3] == "events":
        org_id = parts[2]
        log_id = parts[4]
        audit_log = state["audit_logs"].get(log_id)
        if org_id not in state["orgs"] or audit_log is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if audit_log["org_id"] != org_id:
            return _json(404, {"error": "not_found"})
        # Intentional alias of the audit-log BOLA route.
        return _json(200, _audit_log_body(log_id, audit_log, actor_name, actor, "audit_event_alias"))

    if len(parts) == 6 and parts[:3] == ["api", "secure", "orgs"] and parts[4] == "audit-logs":
        org_id = parts[3]
        log_id = parts[5]
        audit_log = state["audit_logs"].get(log_id)
        if org_id not in state["orgs"] or audit_log is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if audit_log["org_id"] != org_id or actor["org_id"] != org_id or actor["role"] not in {"admin", "auditor"}:
            return _json(403, {"error": "forbidden"})
        return _json(200, _audit_log_body(log_id, audit_log, actor_name, actor, "secure_audit_log_api"))

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3:] == ["security", "settings"]:
        org_id = parts[2]
        settings = state["settings"].get(org_id)
        if settings is None:
            return _json(404, {"error": "not_found"})
        if method != "PATCH":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id:
            return _json(403, {"error": "forbidden"})
        # Intentional BFLA: tenant is checked, but admin role is not.
        _apply_settings(settings, actor_name, body)
        return _json(200, _settings_body(org_id, settings, actor_name, actor, "security_settings_api"))

    if len(parts) == 6 and parts[:3] == ["api", "secure", "orgs"] and parts[4:] == ["security", "settings"]:
        org_id = parts[3]
        settings = state["settings"].get(org_id)
        if settings is None:
            return _json(404, {"error": "not_found"})
        if method != "PATCH":
            return _json(405, {"error": "method_not_allowed"})
        if actor["org_id"] != org_id or actor["role"] != "admin":
            return _json(403, {"error": "forbidden"})
        _apply_settings(settings, actor_name, body)
        return _json(200, _settings_body(org_id, settings, actor_name, actor, "secure_security_settings_api"))

    if len(parts) == 5 and parts[:2] == ["api", "orgs"] and parts[3] == "audit-exports":
        org_id = parts[2]
        export_id = parts[4]
        export = state["exports"].get(export_id)
        if org_id not in state["orgs"] or export is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if export["org_id"] != org_id or actor["org_id"] != org_id:
            return _json(403, {"error": "forbidden"})
        # Intentional BFLA: same-org members can retrieve restricted audit exports.
        return _json(200, _export_body(export_id, export, actor_name, actor, "audit_export_api"))

    if len(parts) == 6 and parts[:2] == ["api", "orgs"] and parts[3:5] == ["compliance", "export-preview"]:
        org_id = parts[2]
        export_id = parts[5]
        export = state["exports"].get(export_id)
        if org_id not in state["orgs"] or export is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if export["org_id"] != org_id or actor["org_id"] != org_id or actor["role"] not in {"admin", "auditor"}:
            return _json(403, {"error": "forbidden"})
        return _json(200, _export_body(export_id, export, actor_name, actor, "compliance_export_preview_decoy"))

    if len(parts) == 6 and parts[:3] == ["api", "secure", "orgs"] and parts[4] == "audit-exports":
        org_id = parts[3]
        export_id = parts[5]
        export = state["exports"].get(export_id)
        if org_id not in state["orgs"] or export is None:
            return _json(404, {"error": "not_found"})
        if method != "GET":
            return _json(405, {"error": "method_not_allowed"})
        if export["org_id"] != org_id or actor["org_id"] != org_id or actor["role"] not in {"admin", "auditor"}:
            return _json(403, {"error": "forbidden"})
        return _json(200, _export_body(export_id, export, actor_name, actor, "secure_audit_export_api"))

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

    def _log_and_send(self, method: str, response: dict[str, Any]) -> None:
        seed = self.headers.get("x-authzbench-seed") or "dev"
        actor = self._actor_name(self._state())
        log_request(
            "audit_settings",
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

    def _handle_and_send(self, method: str, body: dict[str, Any] | None = None) -> None:
        state = self._state()
        actor = self._actor_name(state)
        response = handle(state, method, self.path, actor, body)
        self._log_and_send(method, response)

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


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8016), Handler)
    print("audit_settings listening on :8016", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
