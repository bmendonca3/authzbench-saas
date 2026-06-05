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
from apps.project_mgmt import app as project_mgmt


def _request(
    url: str,
    actor: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    seed: str | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"x-authzbench-actor": actor}
    if seed:
        headers["x-authzbench-seed"] = seed
    if body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _wait_for(url: str, seed: str) -> None:
    deadline = time.time() + 30
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            _request(url, "alpha_owner", seed=seed)
            return
        except Exception as exc:  # noqa: BLE001 - smoke should retry until service is ready.
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"service did not become ready: {url}: {last_error}")


def main() -> int:
    pm_seed = "public-v0-001"
    bill_seed = "public-v0-013"
    pm_refs = project_mgmt.public_refs(project_mgmt.seed_state(pm_seed))
    bill_refs = billing.public_refs(billing.seed_state(bill_seed))

    pm_vuln = f"http://127.0.0.1:8011/api/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    pm_secure = f"http://127.0.0.1:8011/api/secure/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    bill_vuln = f"http://127.0.0.1:8012/api/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"
    bill_secure = f"http://127.0.0.1:8012/api/secure/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"

    _wait_for(pm_vuln, pm_seed)
    _wait_for(bill_secure, bill_seed)

    checks = [
        ("pm_vulnerable_cross_tenant_read", _request(pm_vuln, "beta_member", seed=pm_seed), 200),
        ("pm_secure_cross_tenant_denial", _request(pm_secure, "beta_member", seed=pm_seed), 403),
        ("billing_member_plan_read", _request(bill_vuln, "atlas_member", seed=bill_seed), 200),
        ("billing_member_plan_change", _request(bill_vuln, "atlas_member", "PATCH", {"plan": "enterprise"}, seed=bill_seed), 200),
        ("billing_secure_member_denial", _request(bill_secure, "atlas_member", seed=bill_seed), 403),
    ]
    results = []
    for name, (status, body), expected_status in checks:
        passed = status == expected_status
        results.append({"name": name, "status": status, "expected_status": expected_status, "passed": passed, "body": body})
        if not passed:
            print(json.dumps({"passed": False, "results": results}, indent=2, sort_keys=True))
            return 1

    print(json.dumps({"passed": True, "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
