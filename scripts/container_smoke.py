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


def _wait_for(url: str, seed: str) -> None:
    deadline = time.time() + 30
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            _request(url, "alpha_owner", seed=seed, task_id="readiness_probe")
            return
        except Exception as exc:  # noqa: BLE001 - smoke should retry until service is ready.
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"service did not become ready: {url}: {last_error}")


def main() -> int:
    log_dir = Path("captures/request-logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    for log_name in ("project_mgmt.jsonl", "billing.jsonl", "support.jsonl"):
        (log_dir / log_name).unlink(missing_ok=True)

    pm_seed = "public-v0-001"
    bill_seed = "public-v0-013"
    support_seed = "public-v0-016"
    pm_refs = project_mgmt.public_refs(project_mgmt.seed_state(pm_seed))
    bill_refs = billing.public_refs(billing.seed_state(bill_seed))
    support_refs = support.public_refs(support.seed_state(support_seed))

    pm_vuln = f"http://127.0.0.1:8011/api/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    pm_secure = f"http://127.0.0.1:8011/api/secure/projects/{pm_refs['ALPHA_PROJECT_ID']}/tasks/{pm_refs['ALPHA_PRIVATE_TASK_ID']}"
    bill_vuln = f"http://127.0.0.1:8012/api/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"
    bill_secure = f"http://127.0.0.1:8012/api/secure/orgs/{bill_refs['ATLAS_ORG_ID']}/settings/plan"
    support_vuln = f"http://127.0.0.1:8013/api/tickets/{support_refs['ORBIT_TICKET_ID']}"
    support_secure = f"http://127.0.0.1:8013/api/secure/tickets/{support_refs['ORBIT_TICKET_ID']}"

    _wait_for(pm_vuln, pm_seed)
    _wait_for(bill_secure, bill_seed)
    _wait_for(support_vuln, support_seed)

    checks = [
        ("pm_vulnerable_cross_tenant_read", _request(pm_vuln, "beta_member", seed=pm_seed, task_id="pm_vulnerable_cross_tenant_read"), 200),
        ("pm_secure_cross_tenant_denial", _request(pm_secure, "beta_member", seed=pm_seed, task_id="pm_secure_cross_tenant_denial"), 403),
        ("billing_member_plan_read", _request(bill_vuln, "atlas_member", seed=bill_seed, task_id="billing_member_plan_read"), 200),
        ("billing_member_plan_change", _request(bill_vuln, "atlas_member", "PATCH", {"plan": "enterprise"}, seed=bill_seed, task_id="billing_member_plan_change"), 200),
        ("billing_secure_member_denial", _request(bill_secure, "atlas_member", seed=bill_seed, task_id="billing_secure_member_denial"), 403),
        ("support_cross_org_ticket_read", _request(support_vuln, "acme_agent", seed=support_seed, task_id="support_cross_org_ticket_read"), 200),
        ("support_secure_cross_org_denial", _request(support_secure, "acme_agent", seed=support_seed, task_id="support_secure_cross_org_denial"), 403),
    ]
    results = []
    for name, (status, body), expected_status in checks:
        passed = status == expected_status
        results.append({"name": name, "status": status, "expected_status": expected_status, "passed": passed, "body": body})
        if not passed:
            print(json.dumps({"passed": False, "results": results}, indent=2, sort_keys=True))
            return 1

    logs = {}
    for app_name in ("project_mgmt", "billing", "support"):
        log_path = log_dir / f"{app_name}.jsonl"
        if not log_path.exists():
            print(json.dumps({"passed": False, "reason": f"missing request log: {log_path}", "results": results}, indent=2, sort_keys=True))
            return 1
        entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not entries:
            print(json.dumps({"passed": False, "reason": f"empty request log: {log_path}", "results": results}, indent=2, sort_keys=True))
            return 1
        expected_prefix = {"project_mgmt": "pm_", "billing": "billing_", "support": "support_"}[app_name]
        expected_seed = {"project_mgmt": pm_seed, "billing": bill_seed, "support": support_seed}[app_name]
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
