from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench.validate_manifests import validate_patterns


REQUIRED_HOLDOUT_VARIANT_FIELDS = {"route_variant", "decoy_variant"}


def _manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _load_manifest_metadata(patterns: list[str]) -> list[dict[str, Any]]:
    return [load_json(path) for path in _manifest_paths(patterns)]


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _oracle_shape(manifest: dict[str, Any]) -> dict[str, Any]:
    oracle = manifest.get("oracle")
    if not isinstance(oracle, dict):
        return {}
    return {
        "claim": oracle.get("claim"),
        "status": oracle.get("status"),
        "body_contains": oracle.get("body_contains"),
    }


def _control_shape(control: Any) -> dict[str, Any]:
    if not isinstance(control, dict):
        return {}
    return {
        "actor": control.get("actor"),
        "method": str(control.get("method", "")).upper(),
        "path": control.get("path"),
        "status": control.get("status"),
        "body": control.get("body"),
        "body_contains": control.get("body_contains"),
    }


def _public_structure_signature(manifest: dict[str, Any]) -> str:
    controls = manifest.get("controls") if isinstance(manifest.get("controls"), list) else []
    control_shapes = sorted((_control_shape(control) for control in controls), key=_json_key)
    relevant = {
        "app": manifest.get("app"),
        "expected_vulnerable": manifest.get("expected_vulnerable"),
        "control_type": manifest.get("control_type"),
        "expected_boundary": manifest.get("expected_boundary"),
        "output_schema": manifest.get("output_schema"),
        "oracle": _oracle_shape(manifest),
        "controls": control_shapes,
    }
    return _json_key(relevant)


def _holdout_variant(manifest: dict[str, Any]) -> dict[str, Any]:
    value = manifest.get("holdout_variant")
    return value if isinstance(value, dict) else {}


def _variant_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _is_rehearsal_manifest(manifest: dict[str, Any]) -> bool:
    return (
        "rehearsal_note" in manifest
        and str(manifest.get("id", "")).startswith("holdout_rehearsal_")
        and str(manifest.get("seed", "")).startswith("private-v0-rehearsal-")
    )


def validate_holdout_pack(
    patterns: list[str],
    *,
    public_patterns: list[str],
    comparison_private_patterns: list[str] | None = None,
    min_count: int,
    preferred_count: int,
    max_count: int,
    min_vulnerable: int,
    min_controls: int,
    min_apps: int,
    max_per_app: int,
    min_denial_controls: int,
    min_authorized_allow_controls: int,
    min_route_variants: int,
    min_decoy_variants: int,
) -> dict[str, Any]:
    result = validate_patterns(patterns)
    errors = list(result["errors"])
    count = result["manifest_count"]
    private_count = result["private_holdout_count"]
    vulnerable_count = result["vulnerable_count"]
    control_count = result["control_count"]
    denial_count = result["denial_control_count"]
    authorized_allow_count = result["authorized_allow_control_count"]

    holdout_manifests = _load_manifest_metadata(patterns)
    public_manifests = _load_manifest_metadata(public_patterns)
    comparison_private_manifests = _load_manifest_metadata(comparison_private_patterns or [])
    app_counts = Counter(str(item.get("app")) for item in holdout_manifests)
    public_ids = {str(item.get("id")) for item in public_manifests}
    public_seeds = {str(item.get("seed")) for item in public_manifests}
    public_signatures = {_public_structure_signature(item) for item in public_manifests}
    comparison_private_signatures = {
        _public_structure_signature(item) for item in comparison_private_manifests
    }
    holdout_ids = {str(item.get("id")) for item in holdout_manifests}
    holdout_seeds = {str(item.get("seed")) for item in holdout_manifests}
    rehearsal_count = sum(1 for item in holdout_manifests if _is_rehearsal_manifest(item))
    structure_overlap_count = sum(
        1 for item in holdout_manifests if _public_structure_signature(item) in public_signatures
    )
    private_structure_overlaps = {
        _public_structure_signature(item)
        for item in holdout_manifests
        if _public_structure_signature(item) in comparison_private_signatures
    }
    private_structure_overlap_count = len(private_structure_overlaps)
    non_rehearsal_structure_overlaps = [
        str(item.get("id"))
        for item in holdout_manifests
        if _public_structure_signature(item) in public_signatures and not _is_rehearsal_manifest(item)
    ]
    missing_variant_ids: list[str] = []
    route_variants: set[str] = set()
    decoy_variants: set[str] = set()
    for item in holdout_manifests:
        variant = _holdout_variant(item)
        missing_fields = REQUIRED_HOLDOUT_VARIANT_FIELDS - set(variant)
        route_variant = _variant_value(variant.get("route_variant"))
        decoy_variant = _variant_value(variant.get("decoy_variant"))
        if missing_fields or route_variant is None or decoy_variant is None:
            missing_variant_ids.append(str(item.get("id")))
            continue
        route_variants.add(route_variant)
        decoy_variants.add(decoy_variant)
    warnings: list[str] = []

    if count == 0:
        errors.append("no private holdout manifests matched the supplied glob")
    if private_count != count:
        errors.append("every holdout manifest must set split=private_holdout")
    if count < min_count:
        errors.append(f"holdout pack has {count} tasks; minimum is {min_count}")
    if count > max_count:
        errors.append(f"holdout pack has {count} tasks; maximum is {max_count}")
    if vulnerable_count < min_vulnerable:
        errors.append(f"holdout pack has {vulnerable_count} vulnerable tasks; minimum is {min_vulnerable}")
    if control_count < min_controls:
        errors.append(f"holdout pack has {control_count} controls; minimum is {min_controls}")
    if denial_count < min_denial_controls:
        errors.append(f"holdout pack has {denial_count} denial controls; minimum is {min_denial_controls}")
    if authorized_allow_count < min_authorized_allow_controls:
        errors.append(
            f"holdout pack has {authorized_allow_count} authorized-allow controls; "
            f"minimum is {min_authorized_allow_controls}"
        )
    if len(app_counts) < min_apps:
        errors.append(f"holdout pack covers {len(app_counts)} apps; minimum is {min_apps}")
    overloaded_apps = sorted(app for app, app_count in app_counts.items() if app_count > max_per_app)
    if overloaded_apps:
        errors.append(f"holdout pack has more than {max_per_app} tasks for app(s): {', '.join(overloaded_apps)}")
    overlapping_ids = sorted(holdout_ids & public_ids)
    if overlapping_ids:
        errors.append(f"holdout pack reuses public task id(s): {', '.join(overlapping_ids[:5])}")
    overlapping_seeds = sorted(holdout_seeds & public_seeds)
    if overlapping_seeds:
        errors.append(f"holdout pack reuses public task seed(s): {', '.join(overlapping_seeds[:5])}")
    if missing_variant_ids:
        errors.append(
            "holdout manifest(s) missing holdout_variant route_variant/decoy_variant: "
            f"{', '.join(missing_variant_ids[:5])}"
        )
    if len(route_variants) < min_route_variants:
        errors.append(f"holdout pack has {len(route_variants)} route variants; minimum is {min_route_variants}")
    if len(decoy_variants) < min_decoy_variants:
        errors.append(f"holdout pack has {len(decoy_variants)} decoy variants; minimum is {min_decoy_variants}")
    if non_rehearsal_structure_overlaps:
        errors.append(
            "non-rehearsal holdout manifest(s) reuse public task structure: "
            f"{', '.join(non_rehearsal_structure_overlaps[:5])}"
        )
    if private_structure_overlap_count:
        errors.append(
            "holdout pack reuses "
            f"{private_structure_overlap_count} structural fingerprint(s) from comparison private pack"
        )
    if rehearsal_count:
        warnings.append(
            "holdout pack contains rehearsal manifests generated from public task structure; "
            "do not use it for private leaderboard scoring"
        )
    if structure_overlap_count:
        warnings.append(
            "holdout pack contains manifest(s) with public task structural fingerprints; "
            "only explicitly marked rehearsal packs may use this for workflow testing"
        )

    leaderboard_suitable = not errors and not rehearsal_count and not structure_overlap_count

    result.update(
        {
            "preferred_count": preferred_count,
            "min_count": min_count,
            "max_count": max_count,
            "min_vulnerable": min_vulnerable,
            "min_controls": min_controls,
            "min_apps": min_apps,
            "max_per_app": max_per_app,
            "min_denial_controls": min_denial_controls,
            "min_authorized_allow_controls": min_authorized_allow_controls,
            "min_route_variants": min_route_variants,
            "min_decoy_variants": min_decoy_variants,
            "app_counts": dict(sorted(app_counts.items())),
            "route_variant_count": len(route_variants),
            "decoy_variant_count": len(decoy_variants),
            "rehearsal_manifest_count": rehearsal_count,
            "public_structure_overlap_count": structure_overlap_count,
            "private_structure_overlap_count": private_structure_overlap_count,
            "leaderboard_suitable": leaderboard_suitable,
            "warnings": warnings,
            "passed": not errors,
            "errors": errors,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a private AuthZBench-SaaS holdout pack.")
    parser.add_argument("--task", action="append", help="Private holdout manifest glob. Can be repeated.")
    parser.add_argument(
        "--public-task",
        action="append",
        help="Public manifest glob used to reject reused task IDs and seeds. Can be repeated.",
    )
    parser.add_argument(
        "--comparison-private-task",
        action="append",
        help="Existing private-pack glob used to reject structural overlap. Can be repeated.",
    )
    parser.add_argument("--min-count", type=int, default=20)
    parser.add_argument("--preferred-count", type=int, default=24)
    parser.add_argument("--max-count", type=int, default=30)
    parser.add_argument("--min-vulnerable", type=int, default=12)
    parser.add_argument("--min-controls", type=int, default=8)
    parser.add_argument("--min-apps", type=int, default=6)
    parser.add_argument("--max-per-app", type=int, default=8)
    parser.add_argument("--min-denial-controls", type=int, default=4)
    parser.add_argument("--min-authorized-allow-controls", type=int, default=4)
    parser.add_argument("--min-route-variants", type=int, default=6)
    parser.add_argument("--min-decoy-variants", type=int, default=6)
    args = parser.parse_args()

    patterns = args.task or ["tasks_private/holdout/**/*.json"]
    public_patterns = args.public_task or ["tasks/*/*.json"]
    result = validate_holdout_pack(
        patterns,
        public_patterns=public_patterns,
        comparison_private_patterns=args.comparison_private_task,
        min_count=args.min_count,
        preferred_count=args.preferred_count,
        max_count=args.max_count,
        min_vulnerable=args.min_vulnerable,
        min_controls=args.min_controls,
        min_apps=args.min_apps,
        max_per_app=args.max_per_app,
        min_denial_controls=args.min_denial_controls,
        min_authorized_allow_controls=args.min_authorized_allow_controls,
        min_route_variants=args.min_route_variants,
        min_decoy_variants=args.min_decoy_variants,
    )
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
