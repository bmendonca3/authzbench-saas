"""Redaction helpers for the Harbor adapter.

Ensures private task content, routes, seeds, oracle bodies, credentials,
and local paths are never written to tracked public artifacts.
"""

from __future__ import annotations

import re
from typing import Any

from authzbench_harbor.schemas import PRIVATE_PATTERNS, check_public_safety


REDACTED_PLACEHOLDER = "<REDACTED>"


def redact_private_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *data* with private fields replaced by REDACTED_PLACEHOLDER."""
    PRIVATE_KEYS = {
        "seed", "oracle", "controls", "expected_boundary", "private_route",
        "private_seed", "oracle_body", "credential", "secret",
    }
    result = {}
    for key, value in data.items():
        if key in PRIVATE_KEYS:
            result[key] = REDACTED_PLACEHOLDER
        elif isinstance(value, dict):
            result[key] = redact_private_fields(value)
        elif isinstance(value, list):
            result[key] = [
                redact_private_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def redact_absolute_paths(text: str) -> str:
    """Replace local absolute paths with REDACTED_PLACEHOLDER."""
    text = re.sub(r"/Users/[^\s\"']+", REDACTED_PLACEHOLDER, text)
    text = re.sub(r"/home/[^\s\"']+", REDACTED_PLACEHOLDER, text)
    text = re.sub(r"/var/folders/[^\s\"']+", REDACTED_PLACEHOLDER, text)
    text = re.sub(r"/tmp/[^\s\"']+", REDACTED_PLACEHOLDER, text)
    return text


def public_safe_task(task: dict[str, Any]) -> dict[str, Any]:
    """Return a public-safe copy of a task manifest suitable for adapter metadata."""
    PUBLIC_KEYS = {"id", "app", "expected_vulnerable", "allowed_hosts", "policy", "objective", "output_schema"}
    return {k: v for k, v in task.items() if k in PUBLIC_KEYS}


def scan_for_violations(artifact: Any, source_label: str = "output") -> list[str]:
    """Scan a serialisable artifact for privacy violations. Returns list of errors."""
    import json
    try:
        text = json.dumps(artifact)
    except (TypeError, ValueError) as exc:
        return [f"could not serialize {source_label} for privacy scan: {exc}"]
    return check_public_safety(text)
