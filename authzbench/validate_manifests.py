from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any

from .core import build_context, dump_json, load_json, resolve_templates


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


def _manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _contains_unresolved_template(value: Any) -> bool:
    if isinstance(value, str):
        return "{" in value or "}" in value
    if isinstance(value, list):
        return any(_contains_unresolved_template(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_unresolved_template(item) for item in value.values())
    return False


def _is_public_tasks_path(path: Path) -> bool:
    return len(path.parts) >= 3 and path.parts[-3] == "tasks"


def _is_private_holdout_path(path: Path) -> bool:
    return "tasks_private" in path.parts and "holdout" in path.parts


def validate_manifest(path: Path, seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    data = load_json(path)
    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors
    if data["id"] in seen_ids:
        errors.append(f"{path}: duplicate id: {data['id']}")
    seen_ids.add(data["id"])
    split = data.get("split", "public")
    if split not in VALID_SPLITS:
        errors.append(f"{path}: split must be one of: {', '.join(sorted(VALID_SPLITS))}")
    if split == "private_holdout" and _is_public_tasks_path(path):
        errors.append(f"{path}: private_holdout split must not live under public tasks/")
    if _is_private_holdout_path(path) and split != "private_holdout":
        errors.append(f"{path}: tasks_private/holdout manifests must use split=private_holdout")
    if split == "private_holdout" and str(data["seed"]).startswith("public-"):
        errors.append(f"{path}: private_holdout seed must not use public-* prefix")
    if not isinstance(data["controls"], list) or not data["controls"]:
        errors.append(f"{path}: controls must be a non-empty list")
    if data.get("expected_vulnerable") is True and data["oracle"].get("claim") == "no_vulnerability":
        errors.append(f"{path}: vulnerable task has no_vulnerability oracle")
    if data.get("expected_vulnerable") is True and not isinstance(data.get("expected_boundary"), dict):
        errors.append(f"{path}: vulnerable task must include expected_boundary")
    if data.get("expected_vulnerable") is False and data["oracle"].get("claim") != "no_vulnerability":
        errors.append(f"{path}: secure-control task must use no_vulnerability oracle")
    try:
        context = build_context(data)
    except Exception as exc:  # noqa: BLE001 - validator should report all manifest failures clearly.
        errors.append(f"{path}: failed to render context: {exc}")
        return errors
    if not context["refs"] or not context["actors"]:
        errors.append(f"{path}: rendered context missing refs or actors")
    refs = context["refs"]
    for section_name in ("oracle", "controls"):
        if _contains_unresolved_template(resolve_templates(data.get(section_name), refs)):
            errors.append(f"{path}: unresolved template in {section_name}")
    return errors


def validate_patterns(patterns: list[str]) -> dict[str, Any]:
    paths = _manifest_paths(patterns)
    seen_ids: set[str] = set()
    errors: list[str] = []
    vulnerable = 0
    controls = 0
    private = 0
    for path in paths:
        data = load_json(path)
        if data.get("expected_vulnerable") is True:
            vulnerable += 1
        else:
            controls += 1
        if data.get("split") == "private_holdout":
            private += 1
        errors.extend(validate_manifest(path, seen_ids))
    return {
        "passed": not errors,
        "manifest_count": len(paths),
        "vulnerable_count": vulnerable,
        "control_count": controls,
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
