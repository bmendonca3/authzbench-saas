from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any

from .core import build_context, dump_json, is_safe_identifier, load_json, resolve_templates


REQUIRED_FIELDS = {
    "id",
    "app",
    "seed",
    "expected_vulnerable",
    "allowed_hosts",
    "policy",
    "objective",
    "output_schema",
    "oracle",
    "controls",
}

VALID_SPLITS = {"public", "private_holdout"}
VALID_CONTROL_TYPES = {"denial", "authorized_allow"}
MAX_TEMPLATE_NESTING = 100



def _manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})



def _contains_unresolved_template(value: Any) -> bool:
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str) and ("{" in item or "}" in item):
            return True
        if isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, dict):
            pending.extend(item.values())
    return False


def _template_nesting_exceeds_limit(value: Any, max_depth: int = MAX_TEMPLATE_NESTING) -> bool:
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > max_depth:
            return True
        if isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
    return False



def _is_public_tasks_path(path: Path) -> bool:
    return len(path.parts) >= 3 and path.parts[-3] == "tasks"



def _is_private_holdout_path(path: Path) -> bool:
    return "tasks_private" in path.parts and "holdout" in path.parts



def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_meaningful_json_match(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list, str)):
        return bool(value)
    return True



def _validate_foundational_shapes(path: Path, data: dict[str, Any]) -> tuple[list[str], bool]:
    """Validate types used by later semantic checks.

    The validator is intentionally callable on untrusted host/contributor input.
    Return field-specific errors before operations such as set membership,
    ``str.startswith``, or ``dict.get`` can raise on malformed JSON shapes.
    """

    errors: list[str] = []
    invalid = False

    for field in ("id", "app", "seed", "policy", "objective", "output_schema"):
        if not _is_non_empty_string(data.get(field)):
            errors.append(f"{path}: {field} must be a non-empty string")
            invalid = True

    if _is_non_empty_string(data.get("id")) and not is_safe_identifier(data["id"]):
        errors.append(f"{path}: id must be a safe single path component")
        invalid = True

    expected_vulnerable = data.get("expected_vulnerable")
    if not isinstance(expected_vulnerable, bool):
        errors.append(f"{path}: expected_vulnerable must be a boolean")
        invalid = True

    split = data.get("split", "public")
    if not isinstance(split, str):
        errors.append(f"{path}: split must be a string")
        invalid = True

    allowed_hosts = data.get("allowed_hosts")
    if not isinstance(allowed_hosts, list) or not allowed_hosts or not all(
        _is_non_empty_string(host) for host in allowed_hosts
    ):
        errors.append(f"{path}: allowed_hosts must be a non-empty list of strings")
        invalid = True

    oracle = data.get("oracle")
    if not isinstance(oracle, dict):
        errors.append(f"{path}: oracle must be an object")
        invalid = True
    else:
        if not _is_non_empty_string(oracle.get("claim")):
            errors.append(f"{path}: oracle.claim must be a non-empty string")
            invalid = True
        status = oracle.get("status")
        if isinstance(status, bool) or not isinstance(status, int):
            errors.append(f"{path}: oracle.status must be an integer")
            invalid = True
        if not _is_meaningful_json_match(oracle.get("body_contains")):
            errors.append(f"{path}: oracle.body_contains must be non-empty")
            invalid = True

    controls = data.get("controls")
    if not isinstance(controls, list) or not controls:
        errors.append(f"{path}: controls must be a non-empty list")
        invalid = True
    elif any(not isinstance(control, dict) for control in controls):
        errors.append(f"{path}: every controls item must be an object")
        invalid = True
    else:
        for index, control in enumerate(controls):
            for field in ("name", "actor", "method", "path"):
                if not _is_non_empty_string(control.get(field)):
                    errors.append(
                        f"{path}: controls[{index}].{field} must be a non-empty string"
                    )
                    invalid = True
            status = control.get("status")
            if isinstance(status, bool) or not isinstance(status, int):
                errors.append(f"{path}: controls[{index}].status must be an integer")
                invalid = True
            if "body" in control and not isinstance(control["body"], dict):
                errors.append(f"{path}: controls[{index}].body must be an object when supplied")
                invalid = True
            if "body_contains" in control and not _is_meaningful_json_match(
                control["body_contains"]
            ):
                errors.append(
                    f"{path}: controls[{index}].body_contains must be non-empty when supplied"
                )
                invalid = True

    return errors, invalid



def validate_manifest(path: Path, seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - validators should report file failures without raw tracebacks.
        return [f"{path}: failed to load JSON manifest: {type(exc).__name__}"]
    if not isinstance(data, dict):
        return [f"{path}: manifest root must be an object"]

    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors

    shape_errors, foundational_shapes_invalid = _validate_foundational_shapes(path, data)
    errors.extend(shape_errors)
    if foundational_shapes_invalid:
        return errors

    task_id = data["id"]
    if task_id in seen_ids:
        errors.append(f"{path}: duplicate id: {task_id}")
    seen_ids.add(task_id)

    split = data.get("split", "public")
    if split not in VALID_SPLITS:
        errors.append(f"{path}: split must be one of: {', '.join(sorted(VALID_SPLITS))}")
    if split == "private_holdout" and _is_public_tasks_path(path):
        errors.append(f"{path}: private_holdout split must not live under public tasks/")
    if _is_private_holdout_path(path) and split != "private_holdout":
        errors.append(f"{path}: tasks_private/holdout manifests must use split=private_holdout")
    if split == "private_holdout" and data["seed"].startswith("public-"):
        errors.append(f"{path}: private_holdout seed must not use public-* prefix")

    oracle = data["oracle"]
    if data["expected_vulnerable"] is True and oracle.get("claim") == "no_vulnerability":
        errors.append(f"{path}: vulnerable task has no_vulnerability oracle")
    if data["expected_vulnerable"] is True:
        expected_boundary = data.get("expected_boundary")
        if not isinstance(expected_boundary, dict) or not expected_boundary:
            errors.append(f"{path}: vulnerable task must include a non-empty expected_boundary object")
        elif any(
            not _is_non_empty_string(key) or not _is_non_empty_string(value)
            for key, value in expected_boundary.items()
        ):
            errors.append(f"{path}: expected_boundary keys and values must be non-empty strings")
        boundary_aliases = data.get("boundary_aliases")
        if boundary_aliases is not None and not isinstance(boundary_aliases, dict):
            errors.append(f"{path}: boundary_aliases must be an object when supplied")
        elif isinstance(boundary_aliases, dict) and isinstance(expected_boundary, dict):
            for key, aliases in boundary_aliases.items():
                if key not in expected_boundary:
                    errors.append(f"{path}: boundary_aliases contains unknown expected boundary key: {key}")
                if not isinstance(aliases, list) or not aliases or not all(
                    _is_non_empty_string(alias) for alias in aliases
                ):
                    errors.append(
                        f"{path}: boundary_aliases.{key} must be a non-empty list of strings"
                    )
    if data["expected_vulnerable"] is False and oracle.get("claim") != "no_vulnerability":
        errors.append(f"{path}: secure-control task must use no_vulnerability oracle")
    if data["expected_vulnerable"] is False:
        control_type = data.get("control_type")
        if not isinstance(control_type, str) or control_type not in VALID_CONTROL_TYPES:
            errors.append(f"{path}: secure-control task must set control_type to denial or authorized_allow")
        else:
            status = oracle.get("status")
            if isinstance(status, int):
                if control_type == "authorized_allow" and not (200 <= status < 300):
                    errors.append(f"{path}: authorized_allow control must have a 2xx oracle status")
                if control_type == "denial" and 200 <= status < 300:
                    errors.append(f"{path}: denial control must not have a 2xx oracle status")
    try:
        context = build_context(data)
    except Exception as exc:  # noqa: BLE001 - validator should report all manifest failures clearly.
        errors.append(f"{path}: failed to render context: {exc}")
        return errors
    if not context["refs"] or not context["actors"]:
        errors.append(f"{path}: rendered context missing refs or actors")
    refs = context["refs"]
    for section_name in ("oracle", "controls", "evidence_requirements"):
        if section_name not in data:
            continue
        section = data.get(section_name)
        if _template_nesting_exceeds_limit(section):
            errors.append(
                f"{path}: {section_name} nesting exceeds validation limit {MAX_TEMPLATE_NESTING}"
            )
            continue
        try:
            resolved_section = resolve_templates(section, refs)
        except RecursionError:
            errors.append(f"{path}: {section_name} nesting exceeds safe template resolution depth")
            continue
        if _contains_unresolved_template(resolved_section):
            errors.append(f"{path}: unresolved template in {section_name}")
    evidence_requirements = data.get("evidence_requirements")
    if evidence_requirements is not None:
        if data["expected_vulnerable"] is not True:
            errors.append(f"{path}: evidence_requirements are only supported for vulnerable tasks")
        elif not isinstance(evidence_requirements, list) or not evidence_requirements:
            errors.append(f"{path}: evidence_requirements must be a non-empty list when supplied")
        else:
            seen_requirement_indexes: set[int] = set()
            for index, requirement in enumerate(evidence_requirements):
                if not isinstance(requirement, dict):
                    errors.append(f"{path}: evidence_requirements[{index}] must be an object")
                    continue
                requirement_index = requirement.get("index")
                if not isinstance(requirement_index, int) or requirement_index < 0:
                    errors.append(f"{path}: evidence_requirements[{index}].index must be a non-negative integer")
                elif requirement_index in seen_requirement_indexes:
                    errors.append(f"{path}: duplicate evidence_requirements index: {requirement_index}")
                else:
                    seen_requirement_indexes.add(requirement_index)
                if "request" not in requirement:
                    errors.append(f"{path}: evidence_requirements[{index}].request is required")
                elif not isinstance(requirement["request"], dict):
                    errors.append(f"{path}: evidence_requirements[{index}].request must be an object")
                if "status" in requirement and not isinstance(requirement["status"], int):
                    errors.append(f"{path}: evidence_requirements[{index}].status must be an integer when supplied")
                if "body_contains" not in requirement and "status" not in requirement:
                    errors.append(f"{path}: evidence_requirements[{index}] must include status or body_contains")
            if seen_requirement_indexes and seen_requirement_indexes != set(range(len(seen_requirement_indexes))):
                errors.append(f"{path}: evidence_requirements indexes must be contiguous starting at 0")
    return errors



def validate_patterns(patterns: list[str]) -> dict[str, Any]:
    paths = _manifest_paths(patterns)
    seen_ids: set[str] = set()
    errors: list[str] = []
    vulnerable = 0
    controls = 0
    denial_controls = 0
    authorized_allow_controls = 0
    private = 0
    for path in paths:
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001 - keep malformed private packs from dumping stack traces.
            errors.append(f"{path}: failed to load JSON manifest: {type(exc).__name__}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path}: manifest root must be an object")
            continue
        if data.get("expected_vulnerable") is True:
            vulnerable += 1
        elif data.get("expected_vulnerable") is False:
            controls += 1
            if data.get("control_type") == "denial":
                denial_controls += 1
            if data.get("control_type") == "authorized_allow":
                authorized_allow_controls += 1
        if data.get("split") == "private_holdout":
            private += 1
        errors.extend(validate_manifest(path, seen_ids))
    return {
        "passed": not errors,
        "manifest_count": len(paths),
        "vulnerable_count": vulnerable,
        "control_count": controls,
        "denial_control_count": denial_controls,
        "authorized_allow_control_count": authorized_allow_controls,
        "private_holdout_count": private,
        "errors": errors,
    }



def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AuthZBench-SaaS task manifests.")
    parser.add_argument("--task", action="append", required=True, help="Task manifest glob. Can be repeated.")
    args = parser.parse_args()
    result = validate_patterns(args.task)
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
