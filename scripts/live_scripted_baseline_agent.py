from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from scripted_baseline_agent import solve


def _request(base_url: str, seed_header: str, seed: str, request_data: dict[str, Any]) -> dict[str, Any]:
    body = request_data.get("body")
    data = None
    headers = {
        "content-type": "application/json",
        "x-authzbench-actor": str(request_data["actor"]),
        seed_header: seed,
    }
    if body is not None:
        data = json.dumps(body).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + str(request_data["path"]),
        data=data,
        headers=headers,
        method=str(request_data.get("method", "GET")).upper(),
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return {"status": response.status, "body": json.loads(response.read())}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "body": json.loads(exc.read())}


def _exercise_live_target(context: dict[str, Any], submission: dict[str, Any]) -> None:
    target = context["target"]
    base_url = target["base_url"]
    seed_header = target["seed_header"]
    seed = target["seed"]
    for finding in submission.get("findings", []):
        for evidence in finding.get("evidence", []):
            response = _request(base_url, seed_header, seed, evidence["request"])
            evidence["live_response"] = response
            if response["status"] >= 400:
                raise RuntimeError(f"live proof request failed: {response}")


def main() -> int:
    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission = solve(context)
    _exercise_live_target(context, submission)
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
