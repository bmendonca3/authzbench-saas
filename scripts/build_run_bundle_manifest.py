"""Build a deterministic integrity manifest for one completed run directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.run_bundle import RunBundleError, build_run_bundle_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Completed run directory to freeze.")
    parser.add_argument(
        "--require",
        action="append",
        dest="required_paths",
        help="Required exact relative path. Repeatable; defaults to summary.json.",
    )
    parser.add_argument(
        "--require-glob",
        action="append",
        default=[],
        help="Required relative glob with at least one match. Repeatable.",
    )
    parser.add_argument("--json", action="store_true", help="Print the complete manifest.")
    args = parser.parse_args()

    bundle = Path(args.bundle)
    if bundle.is_symlink() or not bundle.is_dir():
        print(f"not a non-symlink directory: {bundle}", file=sys.stderr)
        return 2
    try:
        manifest = build_run_bundle_manifest(
            bundle,
            required_paths=args.required_paths if args.required_paths is not None else ["summary.json"],
            required_globs=args.require_glob,
        )
    except RunBundleError as exc:
        print(f"run bundle manifest FAILED [{exc.code}]: {exc.detail}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"run bundle manifest created: {bundle / 'run-bundle-manifest.json'}")
        print(f"bundle_sha256: {manifest['bundle_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
