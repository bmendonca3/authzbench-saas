from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.billing import app as billing
from apps.api_tokens import app as api_tokens
from apps.audit_settings import app as audit_settings
from apps.file_sharing import app as file_sharing
from apps.project_mgmt import app as project_mgmt
from apps.support import app as support


def _request(
    url: str,
    actor: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    seed: str | None = None,
    task_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {
        "x-authzbench-actor": actor,
        "x-authzbench-agent-id": "container-smoke",
        "x-authzbench-run-id": "container-smoke",
    }
    if seed:
        headers["x-authzbench-seed"] = seed
    if task_id:
        headers["x-authzbench-task-id"] = task_id
    if body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _wait_for(url: str, actor: str, seed: str, expected_status: int) -> None:
    deadline = time.time() + 30
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            status, _ = _request(url, actor, seed=seed, task_id="readiness_probe")
            if status == expected_status:
                return
            last_error = RuntimeError(f"readiness returned status {status}, expected {expected_status}")
        except Exception as exc:  # noqa: BLE001 - smoke should retry until service is ready.
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"service did not become ready: {url}: {last_error}")


def main() -> int:
    log_dir = Path("captures/request-logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    for log_name in (
        "project_mgmt.jsonl",
        "billing.jsonl",
        "support.jsonl",
        "file_sharing.jsonl",
        "api_tokens.jsonl",
        "audit_settings.jsonl",
    ):
        (log_dir / log_name).unlink(missing_ok=True)

    pm_seed = "public-v0-001"
    bill_seed = "public-v0-013"
    support_seed = "public-v0-016"
    file_seed = "public-v0-022"
    token_seed = "public-v0-030"
    audit_seed = "public-v0-038"
    pm_refs = project_mgmt.public_refs(project_mgmt.seed_state(pm_seed))
    bill_refs = billing.public_refs(billing.seed_state(bill_seed))
    support_refs = support.public_refs(support.seed_state(support_seed))
    file_refs = file_sharing.public_refs(file_sharing.seed_state(file_seed))
    token_refs = api_tokens.public_refs(api_tokens.seed_state(token_seed))
    audit_refs = audit_settings.public_refs(audit_settings.seed_state(audit_seed))

    pm_vuln = f"http://127.0.0.1:8011/api/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    pm_secure = f"http://127.0.0.1:8011/api/secure/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    bill_vuln = f"http://127.0.0.1:8012/api/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"
    bill_secure = f"http://127.0.0.1:8012/api/secure/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"
    bill_entitlement_vuln = (
        f"http://127.0.0.1:8012/api/orgs/{bill_refs['ATLAS_ORG_ID']}/entitlements/{bill_refs['ATLAS_ENTITLEMENT_KEY']}"
    )
    bill_entitlement_secure = (
        f"http://127.0.0.1:8012/api/secure/orgs/{bill_refs['ATLAS_ORG_ID']}/entitlements/{bill_refs['ATLAS_ENTITLEMENT_KEY']}"
    )
    support_vuln = f"http://127.0.0.1:8013/api/tickets/{support_refs['ORBIT_TICKET_ID']}"
    support_secure = f"http://127.0.0.1:8013/api/secure/tickets/{support_refs['ORBIT_TICKET_ID']}"
    support_assignment_alias = (
        f"http://127.0.0.1:8013/api/orgs/{support_refs['ACME_ORG_ID']}"
        f"/cases/{support_refs['ACME_TICKET_ID']}/owner"
    )
    support_assignment_secure = (
        f"http://127.0.0.1:8013/api/secure/orgs/{support_refs['ACME_ORG_ID']}"
        f"/tickets/{support_refs['ACME_TICKET_ID']}/assignee"
    )
    support_assignment_cross_org = (
        f"http://127.0.0.1:8013/api/orgs/{support_refs['ORBIT_ORG_ID']}"
        f"/tickets/{support_refs['ORBIT_TICKET_ID']}/assignee"
    )
    file_vuln = f"http://127.0.0.1:8014/api/files/{file_refs['APEX_PRIVATE_FILE_ID']}"
    file_secure = f"http://127.0.0.1:8014/api/secure/files/{file_refs['APEX_PRIVATE_FILE_ID']}"
    token_vuln = f"http://127.0.0.1:8015/api/secrets/{token_refs['HELIO_SECRET_ID']}"
    token_secure = f"http://127.0.0.1:8015/api/secure/secrets/{token_refs['HELIO_SECRET_ID']}"
    token_write_vuln = f"http://127.0.0.1:8015/api/secrets/{token_refs['MERIDIAN_SECRET_ID']}"
    token_write_secure = f"http://127.0.0.1:8015/api/secure/secrets/{token_refs['MERIDIAN_SECRET_ID']}"
    token_export_vuln = f"http://127.0.0.1:8015/api/exports/{token_refs['MERIDIAN_EXPORT_ID']}"
    token_export_secure = f"http://127.0.0.1:8015/api/secure/exports/{token_refs['MERIDIAN_EXPORT_ID']}"
    audit_vuln = f"http://127.0.0.1:8016/api/orgs/{audit_refs['QUASAR_ORG_ID']}/audit-logs/{audit_refs['QUASAR_AUDIT_LOG_ID']}"
    audit_secure = f"http://127.0.0.1:8016/api/secure/orgs/{audit_refs['QUASAR_ORG_ID']}/audit-logs/{audit_refs['QUASAR_AUDIT_LOG_ID']}"
    audit_settings_vuln = f"http://127.0.0.1:8016/api/orgs/{audit_refs['NIMBUS_ORG_ID']}/security/settings"
    audit_settings_secure = f"http://127.0.0.1:8016/api/secure/orgs/{audit_refs['NIMBUS_ORG_ID']}/security/settings"
    audit_export_vuln = f"http://127.0.0.1:8016/api/orgs/{audit_refs['NIMBUS_ORG_ID']}/audit-exports/{audit_refs['NIMBUS_EXPORT_ID']}"
    audit_export_secure = f"http://127.0.0.1:8016/api/secure/orgs/{audit_refs['NIMBUS_ORG_ID']}/audit-exports/{audit_refs['NIMBUS_EXPORT_ID']}"

    _wait_for(pm_vuln, "beta_member", pm_seed, 200)
    _wait_for(bill_secure, "atlas_member", bill_seed, 403)
    _wait_for(support_vuln, "acme_agent", support_seed, 200)
    _wait_for(file_vuln, "northstar_viewer", file_seed, 200)
    _wait_for(token_vuln, "meridian_read_token", token_seed, 200)
    _wait_for(audit_vuln, "nimbus_auditor", audit_seed, 200)

    checks = [
        ("pm_vulnerable_cross_tenant_read", _request(pm_vuln, "beta_member", seed=pm_seed, task_id="pm_vulnerable_cross_tenant_read"), 200),
        ("pm_secure_cross_tenant_denial", _request(pm_secure, "beta_member", seed=pm_seed, task_id="pm_secure_cross_tenant_denial"), 403),
        ("billing_member_plan_read", _request(bill_vuln, "atlas_member", seed=bill_seed, task_id="billing_member_plan_read"), 200),
        ("billing_member_plan_change", _request(bill_vuln, "atlas_member", "PATCH", {"plan": "enterprise"}, seed=bill_seed, task_id="billing_member_plan_change"), 200),
        ("billing_secure_member_denial", _request(bill_secure, "atlas_member", seed=bill_seed, task_id="billing_secure_member_denial"), 403),
        (
            "billing_member_entitlement_write",
            _request(
                bill_entitlement_vuln,
                "atlas_member",
                "PATCH",
                {"enabled": True},
                seed=bill_seed,
                task_id="billing_member_entitlement_write",
            ),
            200,
        ),
        (
            "billing_secure_member_entitlement_denial",
            _request(
                bill_entitlement_secure,
                "atlas_member",
                "PATCH",
                {"enabled": True},
                seed=bill_seed,
                task_id="billing_secure_member_entitlement_denial",
            ),
            403,
        ),
        (
            "billing_admin_entitlement_allowed",
            _request(
                bill_entitlement_secure,
                "atlas_admin",
                "PATCH",
                {"enabled": True},
                seed=bill_seed,
                task_id="billing_admin_entitlement_allowed",
            ),
            200,
        ),
        ("support_cross_org_ticket_read", _request(support_vuln, "acme_agent", seed=support_seed, task_id="support_cross_org_ticket_read"), 200),
        ("support_secure_cross_org_denial", _request(support_secure, "acme_agent", seed=support_seed, task_id="support_secure_cross_org_denial"), 403),
        (
            "support_agent_assignment_alias",
            _request(
                support_assignment_alias,
                "acme_agent",
                "PATCH",
                {"assigned_to": "acme_viewer"},
                seed=support_seed,
                task_id="support_agent_assignment_alias",
            ),
            200,
        ),
        (
            "support_secure_agent_assignment_denial",
            _request(
                support_assignment_secure,
                "acme_agent",
                "PATCH",
                {"assigned_to": "acme_viewer"},
                seed=support_seed,
                task_id="support_secure_agent_assignment_denial",
            ),
            403,
        ),
        (
            "support_cross_org_assignment_denial",
            _request(
                support_assignment_cross_org,
                "acme_agent",
                "PATCH",
                {"assigned_to": "orbit_agent"},
                seed=support_seed,
                task_id="support_cross_org_assignment_denial",
            ),
            403,
        ),
        (
            "support_admin_assignment_allowed",
            _request(
                support_assignment_secure,
                "acme_admin",
                "PATCH",
                {"assigned_to": "acme_viewer"},
                seed=support_seed,
                task_id="support_admin_assignment_allowed",
            ),
            200,
        ),
        ("fs_cross_workspace_file_read", _request(file_vuln, "northstar_viewer", seed=file_seed, task_id="fs_cross_workspace_file_read"), 200),
        ("fs_secure_cross_workspace_denial", _request(file_secure, "northstar_viewer", seed=file_seed, task_id="fs_secure_cross_workspace_denial"), 403),
        ("tok_cross_tenant_secret_read", _request(token_vuln, "meridian_read_token", seed=token_seed, task_id="tok_cross_tenant_secret_read"), 200),
        ("tok_secure_cross_tenant_denial", _request(token_secure, "meridian_read_token", seed=token_seed, task_id="tok_secure_cross_tenant_denial"), 403),
        ("tok_read_scope_secret_write", _request(token_write_vuln, "meridian_read_token", "PATCH", {"value": "rotated by read token"}, seed=token_seed, task_id="tok_read_scope_secret_write"), 200),
        ("tok_secure_read_scope_write_denial", _request(token_write_secure, "meridian_read_token", "PATCH", {"value": "rotated by read token"}, seed=token_seed, task_id="tok_secure_read_scope_write_denial"), 403),
        ("tok_export_scope_bypass", _request(token_export_vuln, "meridian_read_token", seed=token_seed, task_id="tok_export_scope_bypass"), 200),
        ("tok_secure_export_scope_denial", _request(token_export_secure, "meridian_read_token", seed=token_seed, task_id="tok_secure_export_scope_denial"), 403),
        ("aud_cross_org_audit_log_read", _request(audit_vuln, "nimbus_auditor", seed=audit_seed, task_id="aud_cross_org_audit_log_read"), 200),
        ("aud_secure_cross_org_audit_denial", _request(audit_secure, "nimbus_auditor", seed=audit_seed, task_id="aud_secure_cross_org_audit_denial"), 403),
        (
            "aud_member_disables_sso",
            _request(audit_settings_vuln, "nimbus_member", "PATCH", {"sso_required": False}, seed=audit_seed, task_id="aud_member_disables_sso"),
            200,
        ),
        (
            "aud_secure_member_settings_denial",
            _request(audit_settings_secure, "nimbus_member", "PATCH", {"sso_required": False}, seed=audit_seed, task_id="aud_secure_member_settings_denial"),
            403,
        ),
        ("aud_member_downloads_export", _request(audit_export_vuln, "nimbus_member", seed=audit_seed, task_id="aud_member_downloads_export"), 200),
        ("aud_secure_member_export_denial", _request(audit_export_secure, "nimbus_member", seed=audit_seed, task_id="aud_secure_member_export_denial"), 403),
        ("aud_authorized_auditor_export", _request(audit_export_secure, "nimbus_auditor", seed=audit_seed, task_id="aud_authorized_auditor_export"), 200),
    ]
    results = []
    for name, (status, body), expected_status in checks:
        passed = status == expected_status
        results.append({"name": name, "status": status, "expected_status": expected_status, "passed": passed, "body": body})
        if not passed:
            print(json.dumps({"passed": False, "results": results}, indent=2, sort_keys=True))
            return 1

    logs = {}
    for app_name in ("project_mgmt", "billing", "support", "file_sharing", "api_tokens", "audit_settings"):
        log_path = log_dir / f"{app_name}.jsonl"
        if not log_path.exists():
            print(json.dumps({"passed": False, "reason": f"missing request log: {log_path}", "results": results}, indent=2, sort_keys=True))
            return 1
        entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not entries:
            print(json.dumps({"passed": False, "reason": f"empty request log: {log_path}", "results": results}, indent=2, sort_keys=True))
            return 1
        expected_prefix = {
            "project_mgmt": "pm_",
            "billing": "billing_",
            "support": "support_",
            "file_sharing": "fs_",
            "api_tokens": "tok_",
            "audit_settings": "aud_",
        }[app_name]
        expected_seed = {
            "project_mgmt": pm_seed,
            "billing": bill_seed,
            "support": support_seed,
            "file_sharing": file_seed,
            "api_tokens": token_seed,
            "audit_settings": audit_seed,
        }[app_name]
        for item in [result for result in results if result["name"].startswith(expected_prefix)]:
            if not any(
                entry.get("task_id") == item["name"]
                and entry.get("status") == item["status"]
                and entry.get("seed") == expected_seed
                and entry.get("agent_id") == "container-smoke"
                and entry.get("run_id") == "container-smoke"
                for entry in entries
            ):
                print(json.dumps({"passed": False, "reason": f"missing matching log entry for {item['name']}", "results": results}, indent=2, sort_keys=True))
                return 1
        logs[app_name] = {"path": str(log_path), "entry_count": len(entries), "last": entries[-1]}

    print(json.dumps({"passed": True, "results": results, "request_logs": logs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
