"""Validate one run directory against its deterministic integrity manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.run_bundle import validate_run_bundle_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Run directory containing run-bundle-manifest.json.")
    parser.add_argument("--json", action="store_true", help="Print the complete validation result.")
    args = parser.parse_args()

    bundle = Path(args.bundle)
    if bundle.is_symlink() or not bundle.is_dir():
        print(f"not a non-symlink directory: {bundle}", file=sys.stderr)
        return 2
    result = validate_run_bundle_manifest(bundle)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["passed"]:
        print(f"run bundle manifest ok: {bundle}")
        print(f"bundle_sha256: {result['bundle_sha256']}")
    else:
        print(f"run bundle manifest FAILED: {bundle}", file=sys.stderr)
        for finding in result["findings"]:
            print(f"  ERROR {finding['code']}: {finding}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
