from __future__ import annotations

import re
from typing import Any


SCORE_POLICY_V2 = "score-policy-v2"

KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "attacker_actor": ("attacker_actor", "actor", "subject", "principal"),
    "victim_tenant": ("victim_tenant", "target_tenant", "victim_tenant_id", "target_tenant_id"),
    "victim_org": ("victim_org", "target_org", "victim_org_id", "target_org_id"),
    "victim_workspace": ("victim_workspace", "target_workspace", "victim_workspace_id", "target_workspace_id"),
    "required_role": ("required_role", "role", "actor_role", "subject_role"),
    "required_scope": ("required_scope", "scope", "token_scope"),
    "required_membership": ("required_membership", "membership", "workspace_membership"),
    "required_boundary": ("required_boundary", "boundary_type"),
    "required_link_state": ("required_link_state", "link_state"),
}

ENTITY_REFERENCE_SUFFIXES = {
    "victim_tenant": "TENANT_ID",
    "victim_org": "ORG_ID",
    "victim_workspace": "WORKSPACE_ID",
}


def _text(value: Any) -> str | None:
    return value.casefold() if isinstance(value, str) else None


def _reference_prefix(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def _candidate_keys(task: dict[str, Any], canonical_key: str) -> tuple[str, ...]:
    declared = task.get("boundary_v2_key_aliases") or {}
    extra = declared.get(canonical_key, []) if isinstance(declared, dict) else []
    declared_keys = tuple(alias for alias in extra if isinstance(alias, str)) if isinstance(extra, list) else ()
    return tuple(dict.fromkeys((*KEY_ALIASES.get(canonical_key, (canonical_key,)), *declared_keys)))


def boundary_schema_for_task(task: dict[str, Any]) -> dict[str, Any]:
    expected = task.get("expected_boundary") or {}
    if not isinstance(expected, dict):
        return {"required_fields": [], "field_aliases": {}, "value_rule": "public-label-or-approved-id"}
    return {
        "required_fields": list(expected),
        "field_aliases": {key: list(_candidate_keys(task, key)) for key in expected},
        "value_rule": "use the expected public label, an approved seed-resolved ID for victim entities, or a task-declared value alias",
    }


def _matches_expected_value(
    actual: Any,
    expected: Any,
    value_aliases: list[str],
    canonical_key: str,
    refs: dict[str, Any],
) -> str | None:
    if actual == expected:
        return "label"
    actual_text = _text(actual)
    expected_text = _text(expected)
    if actual_text is None or expected_text is None:
        return None
    if actual_text == expected_text:
        return "label"
    if any(actual_text == alias.casefold() for alias in value_aliases):
        return "alias"
    suffix = ENTITY_REFERENCE_SUFFIXES.get(canonical_key)
    if suffix:
        expected_reference = f"{_reference_prefix(expected)}_{suffix}"
        if refs.get(expected_reference) == actual:
            return "id"
    return None


def boundary_matches_v2(
    actual: Any,
    task: dict[str, Any],
    refs: dict[str, Any],
) -> tuple[bool, str, list[dict[str, Any]]]:
    """Strictly match v2 boundary fields without exposing submitted values."""
    expected = task.get("expected_boundary") or {}
    value_aliases = task.get("boundary_aliases") or {}
    if not isinstance(actual, dict) or not isinstance(expected, dict) or not expected:
        return False, "mismatch", [{"status": "invalid_boundary"}]

    diagnostics: list[dict[str, Any]] = []
    semantic = False
    for canonical_key, expected_value in expected.items():
        source_keys = [key for key in _candidate_keys(task, canonical_key) if key in actual]
        detail: dict[str, Any] = {"field": canonical_key, "source_keys": source_keys}
        if not source_keys:
            diagnostics.append(detail | {"status": "missing"})
            continue
        aliases = value_aliases.get(canonical_key) if isinstance(value_aliases, dict) else []
        allowed_values = aliases if isinstance(aliases, list) else []
        match_modes = [
            _matches_expected_value(actual[key], expected_value, allowed_values, canonical_key, refs)
            for key in source_keys
        ]
        if any(mode is None for mode in match_modes):
            diagnostics.append(detail | {"status": "conflict" if len(source_keys) > 1 else "mismatch"})
            continue
        mode = "id" if "id" in match_modes else "alias" if "alias" in match_modes else "label"
        diagnostics.append(detail | {"status": "matched", "match_mode": mode})
        if source_keys != [canonical_key] or mode != "label":
            semantic = True

    if any(item["status"] != "matched" for item in diagnostics):
        return False, "mismatch", diagnostics
    return True, "semantic" if semantic else "exact", diagnostics
