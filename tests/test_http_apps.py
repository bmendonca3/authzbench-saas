from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any

from apps.billing import app as billing
from apps.project_mgmt import app as project_mgmt


def _serve(handler_cls) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def _request(url: str, actor: str, method: str = "GET", body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"x-authzbench-actor": actor}
    if body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
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

        secure_status, secure_body = _request(
            f"{base_url}/api/secure/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
            "atlas_member",
        )
        self.assertEqual(secure_status, 403)
        self.assertEqual(secure_body["error"], "forbidden")


if __name__ == "__main__":
    unittest.main()
