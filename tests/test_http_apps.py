from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from unittest.mock import patch

from apps.api_tokens import app as api_tokens
from apps.audit_settings import app as audit_settings
from apps.billing import app as billing
from apps.file_sharing import app as file_sharing
from apps.project_mgmt import app as project_mgmt
from apps.support import app as support


def _serve(handler_cls) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def _request(
    url: str,
    actor: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    request_headers = {"x-authzbench-actor": actor}
    request_headers.update(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        request_headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _request_with_headers(
    url: str,
    headers: dict[str, str],
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    request_headers = dict(headers)
    if body is not None:
        data = json.dumps(body).encode()
        request_headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _raw_request(
    url: str,
    actor: str,
    method: str,
    body: bytes | None = None,
) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        data=body,
        headers={"x-authzbench-actor": actor, "content-type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


class HttpAppTests(unittest.TestCase):
    def test_project_mgmt_http_vulnerable_and_secure_paths(self) -> None:
        server, base_url = _serve(project_mgmt.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = project_mgmt.public_refs(project_mgmt.Handler.state)

        vulnerable_status, vulnerable_body = _request(
            f"{base_url}/api/projects/{refs['ALPHA_PROJECT_ID']}/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}",
            "beta_member",
        )
        self.assertEqual(vulnerable_status, 200)
        self.assertEqual(vulnerable_body["viewer"], "beta_member")
        self.assertEqual(vulnerable_body["task"]["tenant_id"], refs["ALPHA_TENANT_ID"])

        secure_status, secure_body = _request(
            f"{base_url}/api/secure/projects/{refs['ALPHA_PROJECT_ID']}/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}",
            "beta_member",
        )
        self.assertEqual(secure_status, 403)
        self.assertEqual(secure_body["error"], "forbidden")

        alias_status, alias_body = _request(
            f"{base_url}/api/workspaces/{refs['ALPHA_PROJECT_ID']}/work-items/{refs['ALPHA_PRIVATE_TASK_ID']}",
            "beta_member",
        )
        self.assertEqual(alias_status, 200)
        self.assertEqual(alias_body["route"], "workspace_work_item_alias")
        self.assertEqual(alias_body["task"]["tenant_id"], refs["ALPHA_TENANT_ID"])

    def test_billing_http_member_plan_change_and_secure_denial(self) -> None:
        server, base_url = _serve(billing.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = billing.public_refs(billing.Handler.state)

        vulnerable_status, vulnerable_body = _request(
            f"{base_url}/api/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
            "atlas_member",
            method="PATCH",
            body={"plan": "enterprise"},
        )
        self.assertEqual(vulnerable_status, 200)
        self.assertEqual(vulnerable_body["viewer"], "atlas_member")
        self.assertEqual(vulnerable_body["org"]["plan"], "enterprise")

        readable_status, readable_body = _request(
            f"{base_url}/api/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
            "atlas_member",
        )
        self.assertEqual(readable_status, 200)
        self.assertEqual(readable_body["viewer"], "atlas_member")
        self.assertEqual(readable_body["org"]["billing_contact"], "cfo@atlas.test")

        secure_status, secure_body = _request(
            f"{base_url}/api/secure/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
            "atlas_member",
        )
        self.assertEqual(secure_status, 403)
        self.assertEqual(secure_body["error"], "forbidden")

        decoy_status, decoy_body = _request(
            f"{base_url}/api/orgs/{refs['ATLAS_ORG_ID']}/settings/admin-export",
            "atlas_member",
        )
        self.assertEqual(decoy_status, 403)
        self.assertEqual(decoy_body["error"], "forbidden")

        admin_decoy_status, admin_decoy_body = _request(
            f"{base_url}/api/orgs/{refs['ATLAS_ORG_ID']}/settings/admin-export",
            "atlas_admin",
        )
        self.assertEqual(admin_decoy_status, 200)
        self.assertEqual(admin_decoy_body["export"]["status"], "queued")

        missing_decoy_status, missing_decoy_body = _request(
            f"{base_url}/api/orgs/missing-org/settings/admin-export",
            "atlas_admin",
        )
        self.assertEqual(missing_decoy_status, 404)
        self.assertEqual(missing_decoy_body["error"], "not_found")

    def test_http_targets_write_request_logs_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"AUTHZBENCH_REQUEST_LOG_DIR": tmp}):
                server, base_url = _serve(project_mgmt.Handler)
                self.addCleanup(server.server_close)
                self.addCleanup(server.shutdown)
                refs = project_mgmt.public_refs(project_mgmt.Handler.state)
                status, _ = _request(
                    f"{base_url}/api/workspaces/{refs['ALPHA_PROJECT_ID']}/work-items/{refs['ALPHA_PRIVATE_TASK_ID']}",
                    "beta_member",
                    headers={
                        "x-authzbench-agent-id": "unit-test-agent",
                        "x-authzbench-run-id": "unit-test-run",
                        "x-authzbench-task-id": "unit-test-task",
                    },
                )
                self.assertEqual(status, 200)

            log_path = Path(tmp) / "project_mgmt.jsonl"
            entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(entries)
            self.assertEqual(entries[-1]["app"], "project_mgmt")
            self.assertEqual(entries[-1]["actor"], "beta_member")
            self.assertEqual(entries[-1]["method"], "GET")
            self.assertEqual(entries[-1]["status"], 200)
            self.assertEqual(entries[-1]["path"].split("/")[-2], "work-items")
            self.assertEqual(entries[-1]["agent_id"], "unit-test-agent")
            self.assertEqual(entries[-1]["run_id"], "unit-test-run")
            self.assertEqual(entries[-1]["task_id"], "unit-test-task")
            self.assertEqual(len(entries[-1]["response_body_sha256"]), 64)

    def test_request_log_io_failure_does_not_break_target_response(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            with patch.dict("os.environ", {"AUTHZBENCH_REQUEST_LOG_DIR": tmp.name}):
                server, base_url = _serve(project_mgmt.Handler)
                self.addCleanup(server.server_close)
                self.addCleanup(server.shutdown)
                refs = project_mgmt.public_refs(project_mgmt.Handler.state)
                status, body = _request(
                    f"{base_url}/api/projects/{refs['ALPHA_PROJECT_ID']}/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}",
                    "beta_member",
                )

        self.assertEqual(status, 200)
        self.assertEqual(body["viewer"], "beta_member")

    def test_support_http_vulnerable_and_secure_paths(self) -> None:
        server, base_url = _serve(support.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = support.public_refs(support.Handler.state)

        cross_org_status, cross_org_body = _request(
            f"{base_url}/api/tickets/{refs['ORBIT_TICKET_ID']}",
            "acme_agent",
        )
        self.assertEqual(cross_org_status, 200)
        self.assertEqual(cross_org_body["viewer"], "acme_agent")
        self.assertEqual(cross_org_body["ticket"]["org_id"], refs["ORBIT_ORG_ID"])

        secure_cross_status, secure_cross_body = _request(
            f"{base_url}/api/secure/tickets/{refs['ORBIT_TICKET_ID']}",
            "acme_agent",
        )
        self.assertEqual(secure_cross_status, 403)
        self.assertEqual(secure_cross_body["error"], "forbidden")

        viewer_write_status, viewer_write_body = _request(
            f"{base_url}/api/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
            "acme_viewer",
            method="PATCH",
            body={"status": "closed"},
        )
        self.assertEqual(viewer_write_status, 200)
        self.assertEqual(viewer_write_body["ticket"]["status"], "closed")

        secure_viewer_write_status, secure_viewer_write_body = _request(
            f"{base_url}/api/secure/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
            "acme_viewer",
            method="PATCH",
            body={"status": "closed"},
        )
        self.assertEqual(secure_viewer_write_status, 403)
        self.assertEqual(secure_viewer_write_body["error"], "forbidden")

        invite_status, invite_body = _request(
            f"{base_url}/api/orgs/{refs['ACME_ORG_ID']}/invites",
            "acme_agent",
            method="POST",
            body={"email": "new-admin@example.test", "role": "admin"},
        )
        self.assertEqual(invite_status, 201)
        self.assertEqual(invite_body["invite"]["role"], "admin")
        self.assertEqual(invite_body["invite"]["created_by"], "acme_agent")

        secure_invite_status, secure_invite_body = _request(
            f"{base_url}/api/secure/orgs/{refs['ACME_ORG_ID']}/invites",
            "acme_agent",
            method="POST",
            body={"email": "new-admin@example.test", "role": "admin"},
        )
        self.assertEqual(secure_invite_status, 403)
        self.assertEqual(secure_invite_body["error"], "forbidden")

    def test_support_secure_routes_reject_wrong_methods_and_invalid_json(self) -> None:
        server, base_url = _serve(support.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = support.public_refs(support.Handler.state)

        wrong_read_status, wrong_read_body = _request(
            f"{base_url}/api/secure/tickets/{refs['ACME_TICKET_ID']}",
            "acme_agent",
            method="POST",
            body={},
        )
        self.assertEqual(wrong_read_status, 405)
        self.assertEqual(wrong_read_body["error"], "method_not_allowed")

        wrong_status_status, wrong_status_body = _request(
            f"{base_url}/api/secure/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
            "acme_agent",
        )
        self.assertEqual(wrong_status_status, 405)
        self.assertEqual(wrong_status_body["error"], "method_not_allowed")

        invalid_status, invalid_body = _raw_request(
            f"{base_url}/api/secure/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
            "acme_agent",
            method="PATCH",
            body=b"{bad json",
        )
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid_body["error"], "invalid_json")

    def test_file_sharing_http_vulnerable_and_secure_paths(self) -> None:
        server, base_url = _serve(file_sharing.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = file_sharing.public_refs(file_sharing.Handler.state)

        cross_workspace_status, cross_workspace_body = _request(
            f"{base_url}/api/files/{refs['APEX_PRIVATE_FILE_ID']}",
            "northstar_viewer",
        )
        self.assertEqual(cross_workspace_status, 200)
        self.assertEqual(cross_workspace_body["viewer"], "northstar_viewer")
        self.assertEqual(cross_workspace_body["file"]["workspace_id"], refs["APEX_WORKSPACE_ID"])

        secure_cross_status, secure_cross_body = _request(
            f"{base_url}/api/secure/files/{refs['APEX_PRIVATE_FILE_ID']}",
            "northstar_viewer",
        )
        self.assertEqual(secure_cross_status, 403)
        self.assertEqual(secure_cross_body["error"], "forbidden")

        expired_status, expired_body = _request(
            f"{base_url}/api/share-links/{refs['EXPIRED_LINK_ID']}",
            "northstar_viewer",
        )
        self.assertEqual(expired_status, 200)
        self.assertEqual(expired_body["link"]["status"], "expired")
        self.assertEqual(expired_body["file"]["id"], refs["NORTHSTAR_SECRET_FILE_ID"])

        secure_expired_status, secure_expired_body = _request(
            f"{base_url}/api/secure/share-links/{refs['EXPIRED_LINK_ID']}",
            "northstar_viewer",
        )
        self.assertEqual(secure_expired_status, 410)
        self.assertEqual(secure_expired_body["error"], "expired")

        viewer_share_status, viewer_share_body = _request(
            f"{base_url}/api/workspaces/{refs['NORTHSTAR_WORKSPACE_ID']}/files/{refs['NORTHSTAR_SECRET_FILE_ID']}/share-links",
            "northstar_viewer",
            method="POST",
            body={"visibility": "public"},
        )
        self.assertEqual(viewer_share_status, 201)
        self.assertEqual(viewer_share_body["link"]["visibility"], "public")
        self.assertEqual(viewer_share_body["link"]["created_by"], "northstar_viewer")
        self.assertEqual(file_sharing.public_refs(file_sharing.Handler.state)["ACTIVE_LINK_ID"], refs["ACTIVE_LINK_ID"])

        secure_viewer_share_status, secure_viewer_share_body = _request(
            f"{base_url}/api/secure/workspaces/{refs['NORTHSTAR_WORKSPACE_ID']}/files/{refs['NORTHSTAR_SECRET_FILE_ID']}/share-links",
            "northstar_viewer",
            method="POST",
            body={"visibility": "public"},
        )
        self.assertEqual(secure_viewer_share_status, 403)
        self.assertEqual(secure_viewer_share_body["error"], "forbidden")

        same_workspace_status, same_workspace_body = _request(
            f"{base_url}/api/secure/files/{refs['NORTHSTAR_SECRET_FILE_ID']}",
            "northstar_viewer",
        )
        self.assertEqual(same_workspace_status, 200)
        self.assertEqual(same_workspace_body["file"]["workspace_id"], refs["NORTHSTAR_WORKSPACE_ID"])

        active_link_status, active_link_body = _request(
            f"{base_url}/api/secure/share-links/{refs['ACTIVE_LINK_ID']}",
            "apex_viewer",
        )
        self.assertEqual(active_link_status, 200)
        self.assertEqual(active_link_body["link"]["status"], "active")
        self.assertEqual(active_link_body["file"]["id"], refs["NORTHSTAR_PUBLIC_FILE_ID"])

        wrong_file_method_status, wrong_file_method_body = _request(
            f"{base_url}/api/files/{refs['APEX_PRIVATE_FILE_ID']}",
            "northstar_viewer",
            method="POST",
            body={},
        )
        self.assertEqual(wrong_file_method_status, 405)
        self.assertEqual(wrong_file_method_body["error"], "method_not_allowed")

        wrong_share_method_status, wrong_share_method_body = _request(
            f"{base_url}/api/share-links/{refs['ACTIVE_LINK_ID']}",
            "northstar_viewer",
            method="POST",
            body={},
        )
        self.assertEqual(wrong_share_method_status, 405)
        self.assertEqual(wrong_share_method_body["error"], "method_not_allowed")

    def test_api_tokens_http_vulnerable_and_secure_paths(self) -> None:
        server, base_url = _serve(api_tokens.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = api_tokens.public_refs(api_tokens.Handler.state)
        actors = api_tokens.public_actors(api_tokens.Handler.state)

        cross_tenant_status, cross_tenant_body = _request(
            f"{base_url}/api/secrets/{refs['HELIO_SECRET_ID']}",
            "meridian_read_token",
        )
        self.assertEqual(cross_tenant_status, 200)
        self.assertEqual(cross_tenant_body["secret"]["tenant_id"], refs["HELIO_TENANT_ID"])
        self.assertEqual(cross_tenant_body["token"]["tenant_id"], refs["MERIDIAN_TENANT_ID"])

        bearer_status, bearer_body = _request_with_headers(
            f"{base_url}/api/secrets/{refs['HELIO_SECRET_ID']}",
            {"Authorization": f"Bearer {actors['meridian_read_token']['token']}"},
        )
        self.assertEqual(bearer_status, 200)
        self.assertEqual(bearer_body["token"]["actor"], "meridian_read_token")

        secure_cross_status, secure_cross_body = _request(
            f"{base_url}/api/secure/secrets/{refs['HELIO_SECRET_ID']}",
            "meridian_read_token",
        )
        self.assertEqual(secure_cross_status, 403)
        self.assertEqual(secure_cross_body["error"], "forbidden")

        read_write_status, read_write_body = _request(
            f"{base_url}/api/secrets/{refs['MERIDIAN_SECRET_ID']}",
            "meridian_read_token",
            method="PATCH",
            body={"value": "rotated by read token"},
        )
        self.assertEqual(read_write_status, 200)
        self.assertEqual(read_write_body["secret"]["updated_by"], "meridian_read_token")
        self.assertEqual(read_write_body["secret"]["value"], "rotated by read token")

        secure_read_write_status, secure_read_write_body = _request(
            f"{base_url}/api/secure/secrets/{refs['MERIDIAN_SECRET_ID']}",
            "meridian_read_token",
            method="PATCH",
            body={"value": "rotated by read token"},
        )
        self.assertEqual(secure_read_write_status, 403)
        self.assertEqual(secure_read_write_body["error"], "forbidden")

        export_status, export_body = _request(
            f"{base_url}/api/exports/{refs['MERIDIAN_EXPORT_ID']}",
            "meridian_read_token",
        )
        self.assertEqual(export_status, 200)
        self.assertEqual(export_body["export"]["classification"], "admin")

        secure_export_status, secure_export_body = _request(
            f"{base_url}/api/secure/exports/{refs['MERIDIAN_EXPORT_ID']}",
            "meridian_read_token",
        )
        self.assertEqual(secure_export_status, 403)
        self.assertEqual(secure_export_body["error"], "forbidden")

        write_token_status, write_token_body = _request(
            f"{base_url}/api/secure/secrets/{refs['MERIDIAN_SECRET_ID']}",
            "meridian_write_token",
            method="PATCH",
            body={"value": "rotated by write token"},
        )
        self.assertEqual(write_token_status, 200)
        self.assertEqual(write_token_body["secret"]["value"], "rotated by write token")
        self.assertEqual(write_token_body["secret"]["updated_by"], "meridian_write_token")

        export_token_status, export_token_body = _request(
            f"{base_url}/api/secure/exports/{refs['MERIDIAN_EXPORT_ID']}",
            "meridian_export_token",
        )
        self.assertEqual(export_token_status, 200)
        self.assertEqual(export_token_body["token"]["actor"], "meridian_export_token")

        wrong_method_status, wrong_method_body = _request(
            f"{base_url}/api/exports/{refs['MERIDIAN_EXPORT_ID']}",
            "meridian_export_token",
            method="PATCH",
            body={},
        )
        self.assertEqual(wrong_method_status, 405)
        self.assertEqual(wrong_method_body["error"], "method_not_allowed")

        invalid_status, invalid_body = _raw_request(
            f"{base_url}/api/secure/secrets/{refs['MERIDIAN_SECRET_ID']}",
            "meridian_write_token",
            method="PATCH",
            body=b"{bad json",
        )
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid_body["error"], "invalid_json")

    def test_audit_settings_http_vulnerable_and_secure_paths(self) -> None:
        server, base_url = _serve(audit_settings.Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        refs = audit_settings.public_refs(audit_settings.Handler.state)
        actors = audit_settings.public_actors(audit_settings.Handler.state)

        cross_org_status, cross_org_body = _request(
            f"{base_url}/api/orgs/{refs['QUASAR_ORG_ID']}/audit-logs/{refs['QUASAR_AUDIT_LOG_ID']}",
            "nimbus_auditor",
        )
        self.assertEqual(cross_org_status, 200)
        self.assertEqual(cross_org_body["audit_log"]["org_id"], refs["QUASAR_ORG_ID"])
        self.assertEqual(cross_org_body["viewer"]["org_id"], refs["NIMBUS_ORG_ID"])

        bearer_status, bearer_body = _request_with_headers(
            f"{base_url}/api/orgs/{refs['QUASAR_ORG_ID']}/audit-logs/{refs['QUASAR_AUDIT_LOG_ID']}",
            {"Authorization": f"Bearer {actors['nimbus_auditor']['token']}"},
        )
        self.assertEqual(bearer_status, 200)
        self.assertEqual(bearer_body["viewer"]["actor"], "nimbus_auditor")

        secure_cross_status, secure_cross_body = _request(
            f"{base_url}/api/secure/orgs/{refs['QUASAR_ORG_ID']}/audit-logs/{refs['QUASAR_AUDIT_LOG_ID']}",
            "nimbus_auditor",
        )
        self.assertEqual(secure_cross_status, 403)
        self.assertEqual(secure_cross_body["error"], "forbidden")

        mismatched_path_status, mismatched_path_body = _request(
            f"{base_url}/api/orgs/{refs['NIMBUS_ORG_ID']}/audit-logs/{refs['QUASAR_AUDIT_LOG_ID']}",
            "nimbus_auditor",
        )
        self.assertEqual(mismatched_path_status, 404)
        self.assertEqual(mismatched_path_body["error"], "not_found")

        member_settings_status, member_settings_body = _request(
            f"{base_url}/api/orgs/{refs['NIMBUS_ORG_ID']}/security/settings",
            "nimbus_member",
            method="PATCH",
            body={"sso_required": False},
        )
        self.assertEqual(member_settings_status, 200)
        self.assertFalse(member_settings_body["settings"]["sso_required"])
        self.assertEqual(member_settings_body["settings"]["updated_by"], "nimbus_member")

        secure_member_settings_status, secure_member_settings_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/security/settings",
            "nimbus_member",
            method="PATCH",
            body={"sso_required": False},
        )
        self.assertEqual(secure_member_settings_status, 403)
        self.assertEqual(secure_member_settings_body["error"], "forbidden")

        member_export_status, member_export_body = _request(
            f"{base_url}/api/orgs/{refs['NIMBUS_ORG_ID']}/audit-exports/{refs['NIMBUS_EXPORT_ID']}",
            "nimbus_member",
        )
        self.assertEqual(member_export_status, 200)
        self.assertEqual(member_export_body["export"]["classification"], "restricted")
        self.assertEqual(member_export_body["viewer"]["role"], "member")

        secure_member_export_status, secure_member_export_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/audit-exports/{refs['NIMBUS_EXPORT_ID']}",
            "nimbus_member",
        )
        self.assertEqual(secure_member_export_status, 403)
        self.assertEqual(secure_member_export_body["error"], "forbidden")

        auditor_own_log_status, auditor_own_log_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/audit-logs/{refs['NIMBUS_AUDIT_LOG_ID']}",
            "nimbus_auditor",
        )
        self.assertEqual(auditor_own_log_status, 200)
        self.assertEqual(auditor_own_log_body["viewer"]["role"], "auditor")

        admin_settings_status, admin_settings_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/security/settings",
            "nimbus_admin",
            method="PATCH",
            body={"session_timeout_minutes": 30},
        )
        self.assertEqual(admin_settings_status, 200)
        self.assertEqual(admin_settings_body["settings"]["session_timeout_minutes"], 30)
        self.assertEqual(admin_settings_body["settings"]["updated_by"], "nimbus_admin")

        auditor_export_status, auditor_export_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/audit-exports/{refs['NIMBUS_EXPORT_ID']}",
            "nimbus_auditor",
        )
        self.assertEqual(auditor_export_status, 200)
        self.assertEqual(auditor_export_body["viewer"]["role"], "auditor")

        wrong_method_status, wrong_method_body = _request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/audit-logs/{refs['NIMBUS_AUDIT_LOG_ID']}",
            "nimbus_auditor",
            method="PATCH",
            body={},
        )
        self.assertEqual(wrong_method_status, 405)
        self.assertEqual(wrong_method_body["error"], "method_not_allowed")

        invalid_status, invalid_body = _raw_request(
            f"{base_url}/api/secure/orgs/{refs['NIMBUS_ORG_ID']}/security/settings",
            "nimbus_admin",
            method="PATCH",
            body=b"{bad json",
        )
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid_body["error"], "invalid_json")


if __name__ == "__main__":
    unittest.main()
