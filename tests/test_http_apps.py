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

from apps.billing import app as billing
from apps.project_mgmt import app as project_mgmt


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


if __name__ == "__main__":
    unittest.main()
