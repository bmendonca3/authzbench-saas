from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any


_LOCK = threading.Lock()


def _body_hash(body: dict[str, Any]) -> str:
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def log_request(
    app_name: str,
    *,
    seed: str,
    actor: str | None,
    method: str,
    path: str,
    status: int,
    response_body: dict[str, Any],
    run_id: str | None = None,
    agent_id: str | None = None,
    task_id: str | None = None,
) -> None:
    log_dir = os.environ.get("AUTHZBENCH_REQUEST_LOG_DIR")
    if not log_dir:
        return
    entry = {
        "request_id": uuid.uuid4().hex,
        "timestamp_unix": round(time.time(), 6),
        "app": app_name,
        "seed": seed,
        "actor": actor,
        "method": method,
        "path": path,
        "status": status,
        "response_body_sha256": _body_hash(response_body),
        "run_id": run_id,
        "agent_id": agent_id,
        "task_id": task_id,
    }
    path_obj = Path(log_dir) / f"{app_name}.jsonl"
    try:
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK:
            with path_obj.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True) + "\n")
    except Exception as exc:  # noqa: BLE001 - target availability must not depend on log I/O.
        print(f"request log write skipped for {app_name}: {exc}", file=sys.stderr)
