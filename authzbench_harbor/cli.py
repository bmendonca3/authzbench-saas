"""Harbor adapter CLI.

Usage:
    python3 -m authzbench_harbor.cli build \\
        --tasks 'tasks/**/*.json' \\
        --output-dir artifact/harbor-dataset-public-smoke \\
        --harness-lane no_tools \\
        --limit 6 \\
        --overwrite

    python3 -m authzbench_harbor.cli build \\
        --task-id pm_same_tenant_read_control \\
        --output-dir artifact/harbor-dataset-single \\
        --harness-lane no_tools \\
        --overwrite
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench_harbor.adapter import build_dataset  # noqa: E402
from authzbench_harbor.redaction import scan_for_violations  # noqa: E402


def _current_commit_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        sha = result.stdout.strip()
        return sha if len(sha) == 40 else None
    except Exception:
        return None


def cmd_build(args: argparse.Namespace) -> int:
    task_patterns: list[str] = []
    if args.tasks:
        task_patterns.extend(args.tasks)
    if not task_patterns and not args.task_id and not args.task_ids:
        task_patterns = ["tasks/**/*.json"]

    task_ids: list[str] = []
    if args.task_ids:
        for item in args.task_ids:
            task_ids.extend(t.strip() for t in item.split(",") if t.strip())

    benchmark_source_sha = args.benchmark_source_sha or _current_commit_sha()

    output_dir = Path(args.output_dir)
    print(f"Building Harbor dataset -> {output_dir}", file=sys.stderr)

    try:
        manifest = build_dataset(
            task_patterns or ["tasks/**/*.json"],
            output_dir,
            harness_lane=args.harness_lane,
            task_id=args.task_id,
            task_ids=task_ids or None,
            limit=args.limit,
            overwrite=args.overwrite,
            benchmark_source_sha=benchmark_source_sha,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    violations = scan_for_violations(manifest, "dataset manifest")
    if violations:
        print(f"ERROR: public-safety violations in dataset manifest: {violations}", file=sys.stderr)
        return 1

    print(f"Dataset built: {manifest['task_count']} task(s)", file=sys.stderr)
    print(f"  harness_lane: {manifest['harness_lane']}", file=sys.stderr)
    print(f"  output_dir: {output_dir}", file=sys.stderr)
    if args.private_pack:
        print("  NOTE: --private-pack flag noted; private holdout is maintainer-only and NOT written to public tracked output.", file=sys.stderr)
    print(json.dumps({"status": "ok", "task_count": manifest["task_count"], "output_dir": str(output_dir)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m authzbench_harbor.cli",
        description="AuthZBench-SaaS Harbor adapter CLI",
    )
    sub = parser.add_subparsers(dest="command")

    build_parser = sub.add_parser("build", help="Build a Harbor-compatible dataset")
    build_parser.add_argument("--tasks", action="append", help="Task manifest glob pattern (repeatable)")
    build_parser.add_argument("--task-id", default=None, help="Single task ID filter")
    build_parser.add_argument("--task-ids", action="append", help="Comma-separated task ID filter (repeatable)")
    build_parser.add_argument("--limit", type=int, default=None, help="Limit number of tasks")
    build_parser.add_argument("--output-dir", required=True, help="Output directory for dataset")
    build_parser.add_argument(
        "--harness-lane",
        choices=["no_tools", "live_http_tool_agent"],
        default="no_tools",
        help="Harbor harness lane (default: no_tools)",
    )
    build_parser.add_argument("--benchmark-source-sha", default=None, help="Git SHA of benchmark source commit")
    build_parser.add_argument("--private-pack", action="store_true", help="Note that private pack is in use (does not publish private content)")
    build_parser.add_argument("--private-pack-version", default=None, help="Private pack version identifier")
    build_parser.add_argument("--redacted-private", action="store_true", help="Enable private-field redaction in public outputs")
    build_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output directory")

    args = parser.parse_args(argv)
    if args.command == "build":
        return cmd_build(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
