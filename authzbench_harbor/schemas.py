"""Public-safe schema constants and validation helpers for the Harbor adapter."""

from __future__ import annotations

ADAPTER_SCHEMA_VERSION = "harbor-adapter-v1"
SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION = "harbor-scorer-bridge-output-v1"
PARITY_EXPERIMENT_SCHEMA_VERSION = "harbor-parity-experiment-v1"
ADAPTER_SMOKE_SCHEMA_VERSION = "harbor-adapter-smoke-v1"
ADAPTER_METADATA_SCHEMA_VERSION = "harbor-adapter-metadata-v1"

SUBMISSION_FINDING_REQUIRED_KEYS = {"task_id", "route", "method", "evidence", "boundary", "expected_status"}

PRIVATE_PATTERNS = [
    "tasks_private/holdout",
    "tasks_private",
    "/var/folders",
    "harbor-jobs",
    ".harbor",
    "private_seed",
    "private_route",
    "oracle_body",
    "raw_private",
]

# Patterns that must appear as JSON keys (not inside string values / IDs).
PRIVATE_KEY_PATTERNS = [
    "credential",
    "secret",
]


def check_public_safety(text: str) -> list[str]:
    """Return list of privacy violations found in *text*."""
    import re
    violations = []
    for pattern in PRIVATE_PATTERNS:
        if pattern.lower() in text.lower():
            violations.append(f"public-safety violation: '{pattern}' found in output")
    # Only flag credential/secret when they appear as a JSON key (not inside a task ID or string value).
    for key in PRIVATE_KEY_PATTERNS:
        # Match `"credential":` or `"secret":` as a JSON key
        if re.search(rf'"{re.escape(key)}"\s*:', text, re.IGNORECASE):
            violations.append(f"public-safety violation: JSON key '{key}' found in output")
    if re.search(r"/Users/[A-Za-z]", text):
        violations.append("public-safety violation: local absolute path (/Users/...) found in output")
    if re.search(r"/home/[A-Za-z]", text):
        violations.append("public-safety violation: local absolute path (/home/...) found in output")
    return violations


def validate_submission(submission: object) -> list[str]:
    """Return list of validation errors for an agent submission dict."""
    errors = []
    if not isinstance(submission, dict):
        errors.append("submission must be a JSON object")
        return errors
    if "findings" not in submission:
        errors.append("submission must have a 'findings' key")
        return errors
    findings = submission["findings"]
    if not isinstance(findings, list):
        errors.append("submission.findings must be a list")
        return errors
    return errors


def validate_submission_against_task(submission: dict, task: dict) -> list[str]:
    """Cross-check submission task_id fields against the task manifest."""
    errors = []
    task_id = task.get("id")
    findings = submission.get("findings", [])
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"findings[{i}] must be a JSON object")
            continue
        finding_task_id = finding.get("task_id")
        if finding_task_id and finding_task_id != task_id:
            errors.append(
                f"findings[{i}].task_id '{finding_task_id}' does not match task id '{task_id}'"
            )
    return errors
