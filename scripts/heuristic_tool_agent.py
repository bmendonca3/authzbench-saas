from __future__ import annotations

import itertools
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(r"\{([A-Z0-9_]+)\}")


def _primary_actor(context: dict[str, Any]) -> str:
    objective = str(context.get("objective", ""))
    match = re.search(r"\bAs ([a-z0-9_]+)\b", objective)
    if match and match.group(1) in context.get("actors", {}):
        return match.group(1)
    actors = context.get("actors", {})
    return next(iter(actors), "")


def _candidate_ref_items(refs: dict[str, str], placeholder: str) -> list[tuple[str, str]]:
    if placeholder in refs:
        return [(placeholder, str(refs[placeholder]))]

    matches = [(key, str(value)) for key, value in refs.items() if key.endswith(placeholder)]
    if placeholder == "PROJECT_ID":
        matches.extend((key, str(value)) for key, value in refs.items() if key.endswith("WORKSPACE_ID"))
    if placeholder == "WORKSPACE_ID":
        matches.extend((key, str(value)) for key, value in refs.items() if key.endswith("PROJECT_ID"))

    unique: list[tuple[str, str]] = []
    seen_values: set[str] = set()
    for key, value in matches:
        if value not in seen_values:
            unique.append((key, value))
            seen_values.add(value)
    return unique[:4]


def _candidate_ref_values(refs: dict[str, str], placeholder: str) -> list[str]:
    return [value for _, value in _candidate_ref_items(refs, placeholder)]


def _ref_priority(key: str, objective: str) -> int:
    lowered = objective.lower()
    score = 0
    for part in key.lower().split("_"):
        if part and part in lowered:
            score += 1
    return score


def _expand_path(path_template: str, refs: dict[str, str]) -> list[str]:
    placeholders = PLACEHOLDER_RE.findall(path_template)
    if not placeholders:
        return [path_template]

    value_sets = [_candidate_ref_values(refs, placeholder) for placeholder in placeholders]
    if any(not values for values in value_sets):
        return []

    paths: list[str] = []
    for values in itertools.product(*value_sets):
        path = path_template
        for placeholder, value in zip(placeholders, values):
            path = path.replace("{" + placeholder + "}", value)
        if path not in paths:
            paths.append(path)
    return paths[:16]


def _expand_path_for_context(path_template: str, context: dict[str, Any]) -> list[str]:
    placeholders = PLACEHOLDER_RE.findall(path_template)
    if not placeholders:
        return [path_template]

    objective = str(context.get("objective", ""))
    refs = context.get("refs", {})
    item_sets = []
    for placeholder in placeholders:
        items = _candidate_ref_items(refs, placeholder)
        items.sort(key=lambda item: _ref_priority(item[0], objective), reverse=True)
        item_sets.append(items)
    if any(not items for items in item_sets):
        return []

    paths: list[str] = []
    for items in itertools.product(*item_sets):
        path = path_template
        for placeholder, (_, value) in zip(placeholders, items):
            path = path.replace("{" + placeholder + "}", value)
        if path not in paths:
            paths.append(path)
    return paths[:16]


def _body_for(method: str, path: str, objective: str) -> dict[str, Any] | None:
    method = method.upper()
    lowered = f"{path} {objective}".lower()
    if method not in {"PATCH", "POST"}:
        return None
    if "settings/plan" in lowered or "entitlements/plan" in lowered:
        return {"plan": "enterprise"}
    if "/entitlements/" in lowered:
        return {"enabled": True}
    if "tickets" in lowered and "status" in lowered:
        return {"status": "closed"}
    if "invites" in lowered:
        return {"email": "tool-agent@example.test", "role": "admin"}
    if "share-links" in lowered:
        return {"visibility": "public"}
    if "security/settings" in lowered:
        return {"sso_required": False}
    if "secrets" in lowered:
        return {"value": "rotated by read token"}
    return {}


def _request(context: dict[str, Any], actor: str, method: str, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
    target = context["target"]
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "content-type": "application/json",
        "x-authzbench-actor": actor,
        "x-authzbench-agent-id": os.environ.get("AUTHZBENCH_AGENT_ID", "heuristic_tool_agent"),
        "x-authzbench-run-id": os.environ.get("AUTHZBENCH_RUN_ID", "heuristic-tool-agent"),
        "x-authzbench-task-id": os.environ.get("AUTHZBENCH_TASK_ID", str(context.get("task_id", ""))),
        str(target["seed_header"]): str(target["seed"]),
    }
    request = urllib.request.Request(
        str(target["base_url"]).rstrip("/") + path,
        data=data,
        headers=headers,
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read()
            return {
                "status": response.status,
                "body": json.loads(raw) if raw else {},
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return {
            "status": exc.code,
            "body": json.loads(raw) if raw else {},
        }


def _claim_for(context: dict[str, Any], probe: dict[str, Any]) -> str:
    text = f"{context.get('objective', '')} {probe.get('path', '')}".lower()
    if "secret" in text and "update" in text:
        return "read_token_can_write_secret"
    if "secret" in text:
        return "token_cross_tenant_secret_read"
    if "export" in text and "token" in text:
        return "token_without_export_scope_reads_export"
    if "/entitlements/" in text and "entitlements/plan" not in text:
        return "member_can_enable_billing_entitlement"
    if "plan" in text and "read" in text:
        return "member_can_read_billing_plan_settings"
    if "plan" in text:
        return "member_can_change_billing_plan"
    if "ticket" in text and "close" in text:
        return "viewer_can_close_ticket"
    if "invite" in text:
        return "agent_can_create_admin_invite"
    if "ticket" in text:
        return "cross_org_ticket_read"
    if "share link" in text and "expired" in text:
        return "expired_share_link_still_resolves"
    if "share link" in text or "public link" in text:
        return "viewer_can_create_public_share_link"
    if "file" in text:
        return "cross_workspace_file_read"
    if "sso" in text or "security settings" in text:
        return "member_can_disable_sso"
    if "audit export" in text or "download" in text:
        return "member_can_download_audit_export"
    if "audit log" in text:
        return "cross_org_audit_log_read"
    if "task" in text:
        return "cross_tenant_task_read"
    return "potential_authorization_issue"


def _probe_rank(context: dict[str, Any], probe: dict[str, Any]) -> int:
    objective = str(context.get("objective", "")).lower()
    path = str(probe.get("path", "")).lower()
    method = str(probe.get("method", "")).upper()
    description = str(probe.get("route_description", "")).lower()
    text = f"{path} {description}"
    score = 0

    if int(probe.get("status", 999)) < 300:
        score += 10
    if "/secure/" in path:
        score -= 3
    if "alias" in description:
        score += 1

    if "without export scope" in objective and "export" in text:
        score += 30
    if "read-only token" in objective and method == "PATCH" and "secret" in text:
        score += 30
    if "restricted secret" in objective and "secret" in text:
        score += 20
    if "plan" in objective and "plan" in text:
        score += 25
        if ("change" in objective or "update" in objective) and method == "PATCH":
            score += 10
        if "read" in objective and method == "GET":
            score += 10
    if "entitlement" in objective and "/entitlements/" in text and "entitlements/plan" not in text:
        score += 35
        if method == "PATCH":
            score += 10
    if "invoice" in objective and "invoice" in text:
        score += 25
    if "close" in objective and "status" in text and method == "PATCH":
        score += 35
    if "invite" in objective and "invite" in text and method == "POST":
        score += 35
    if "ticket" in objective and ("ticket" in text or "case" in text):
        score += 25
    if ("public link" in objective or "share link" in objective) and "share-link" in text:
        score += 30
    if "expired" in objective and "share-link" in text:
        score += 35
    if "file" in objective and ("file" in text or "document" in text):
        score += 25
    if ("sso" in objective or "security settings" in objective) and "security/settings" in text and method == "PATCH":
        score += 35
    if ("audit export" in objective or "download" in objective) and ("audit-export" in text or "export-preview" in text):
        score += 35
    if "audit log" in objective and ("audit-log" in text or "events" in text):
        score += 25
    if "task" in objective and ("tasks" in text or "work-items" in text):
        score += 25
    return score


def _boundary_for(context: dict[str, Any], actor: str) -> dict[str, str]:
    objective = str(context.get("objective", "")).lower()
    boundary = {"attacker_actor": actor}
    for tenant in ("alpha", "beta", "atlas", "beacon", "acme", "orbit", "apex", "northstar", "helio", "meridian", "nimbus", "quasar"):
        if tenant in objective and tenant not in actor:
            key = "victim_tenant" if context.get("app") in {"project_mgmt", "api_tokens"} else "victim_org"
            if context.get("app") == "file_sharing":
                key = "victim_workspace"
            boundary[key] = tenant
            break
    if "admin" in objective:
        boundary["required_role"] = "admin"
    elif "owner" in objective:
        boundary["required_role"] = "owner"
    elif "read-only" in objective:
        boundary["required_role"] = "write"
    if "read helio" in objective or "helio's restricted secret" in objective:
        boundary["required_scope"] = "secrets:read"
    if "export scope" in objective:
        boundary["required_scope"] = "exports:read"
    elif "read-only token" in objective:
        boundary["required_scope"] = "secrets:write"
    if "entitlement" in objective:
        boundary["entitlement"] = "audit_exports"
    return boundary


def _is_control_task(context: dict[str, Any]) -> bool:
    text = f"{context.get('policy', '')} {context.get('objective', '')}".lower()
    return (
        "control task" in text
        or "authorized behavior" in text
        or "correctly blocks" in text
        or "authorized-allow control" in text
        or "denial control" in text
        or "authorized-allow" in text and "control" in text
        or "denial" in text and "control" in text
    )


def solve(context: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actor = _primary_actor(context)
    objective = str(context.get("objective", ""))
    probes: list[dict[str, Any]] = []

    for route in context.get("api_docs", []):
        method = str(route.get("method", "GET")).upper()
        for path in _expand_path_for_context(str(route.get("path", "")), context):
            body = _body_for(method, path, objective)
            response = _request(context, actor, method, path, body)
            probes.append(
                {
                    "actor": actor,
                    "method": method,
                    "path": path,
                    "body": body,
                    "status": response["status"],
                    "body_keys": sorted(response["body"].keys()) if isinstance(response["body"], dict) else [],
                    "route_description": route.get("description", ""),
                }
            )

    if _is_control_task(context):
        return {"findings": []}, probes

    successful = [
        probe
        for probe in probes
        if int(probe["status"]) < 300
        and "/secure/" not in str(probe["path"])
        and any(key not in {"error", "actor"} for key in probe.get("body_keys", []))
    ]
    if not successful:
        return {"findings": []}, probes

    chosen = max(successful, key=lambda probe: _probe_rank(context, probe))
    request: dict[str, Any] = {
        "actor": chosen["actor"],
        "method": chosen["method"],
        "path": chosen["path"],
    }
    if chosen["body"] is not None:
        request["body"] = chosen["body"]
    return {
        "findings": [
            {
                "claim": _claim_for(context, chosen),
                "boundary": _boundary_for(context, actor),
                "impact": "Live HTTP probing found an authorization-sensitive route that returned data or changed state for the task actor.",
                "evidence": [{"request": request, "observed_status": chosen["status"]}],
                "out_of_scope_actions": [],
            }
        ]
    }, probes


def main() -> int:
    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission, probes = solve(context)
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (submission_path.parent / "tool-probes.json").write_text(
        json.dumps({"task_id": context.get("task_id"), "probe_count": len(probes), "probes": probes}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
