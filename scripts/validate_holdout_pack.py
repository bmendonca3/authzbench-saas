from __future__ import annotations

import argparse
import glob
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench.validate_manifests import validate_patterns


def _manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _load_manifest_metadata(patterns: list[str]) -> list[dict[str, Any]]:
    return [load_json(path) for path in _manifest_paths(patterns)]


def validate_holdout_pack(
    patterns: list[str],
    *,
    public_patterns: list[str],
    min_count: int,
    preferred_count: int,
    max_count: int,
    min_vulnerable: int,
    min_controls: int,
    min_apps: int,
    max_per_app: int,
    min_denial_controls: int,
    min_authorized_allow_controls: int,
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
    app_counts = Counter(str(item.get("app")) for item in holdout_manifests)
    public_ids = {str(item.get("id")) for item in public_manifests}
    public_seeds = {str(item.get("seed")) for item in public_manifests}
    holdout_ids = {str(item.get("id")) for item in holdout_manifests}
    holdout_seeds = {str(item.get("seed")) for item in holdout_manifests}

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
            "app_counts": dict(sorted(app_counts.items())),
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
    parser.add_argument("--min-count", type=int, default=20)
    parser.add_argument("--preferred-count", type=int, default=24)
    parser.add_argument("--max-count", type=int, default=30)
    parser.add_argument("--min-vulnerable", type=int, default=12)
    parser.add_argument("--min-controls", type=int, default=8)
    parser.add_argument("--min-apps", type=int, default=6)
    parser.add_argument("--max-per-app", type=int, default=8)
    parser.add_argument("--min-denial-controls", type=int, default=4)
    parser.add_argument("--min-authorized-allow-controls", type=int, default=4)
    args = parser.parse_args()

    patterns = args.task or ["tasks_private/holdout/**/*.json"]
    public_patterns = args.public_task or ["tasks/*/*.json"]
    result = validate_holdout_pack(
        patterns,
        public_patterns=public_patterns,
        min_count=args.min_count,
        preferred_count=args.preferred_count,
        max_count=args.max_count,
        min_vulnerable=args.min_vulnerable,
        min_controls=args.min_controls,
        min_apps=args.min_apps,
        max_per_app=args.max_per_app,
        min_denial_controls=args.min_denial_controls,
        min_authorized_allow_controls=args.min_authorized_allow_controls,
    )
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
