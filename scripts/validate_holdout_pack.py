from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json
from authzbench.validate_manifests import validate_patterns


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a private AuthZBench-SaaS holdout pack.")
    parser.add_argument(
        "--task",
        action="append",
        help="Private holdout manifest glob. Can be repeated.",
    )
    parser.add_argument("--min-count", type=int, default=20)
    parser.add_argument("--preferred-count", type=int, default=24)
    parser.add_argument("--max-count", type=int, default=30)
    parser.add_argument("--min-vulnerable", type=int, default=12)
    parser.add_argument("--min-controls", type=int, default=8)
    args = parser.parse_args()

    patterns = args.task or ["tasks_private/holdout/**/*.json"]
    result = validate_patterns(patterns)
    errors = list(result["errors"])
    count = result["manifest_count"]
    private_count = result["private_holdout_count"]
    vulnerable_count = result["vulnerable_count"]
    control_count = result["control_count"]

    if count == 0:
        errors.append("no private holdout manifests matched the supplied glob")
    if private_count != count:
        errors.append("every holdout manifest must set split=private_holdout")
    if count < args.min_count:
        errors.append(f"holdout pack has {count} tasks; minimum is {args.min_count}")
    if count > args.max_count:
        errors.append(f"holdout pack has {count} tasks; maximum is {args.max_count}")
    if vulnerable_count < args.min_vulnerable:
        errors.append(f"holdout pack has {vulnerable_count} vulnerable tasks; minimum is {args.min_vulnerable}")
    if control_count < args.min_controls:
        errors.append(f"holdout pack has {control_count} controls; minimum is {args.min_controls}")

    result.update(
        {
            "preferred_count": args.preferred_count,
            "min_count": args.min_count,
            "max_count": args.max_count,
            "min_vulnerable": args.min_vulnerable,
            "min_controls": args.min_controls,
            "passed": not errors,
            "errors": errors,
        }
    )
    print(dump_json(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
