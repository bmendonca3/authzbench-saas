"""One-command clean-room wrapper for the dependency-free public gate.

The wrapper delegates to ``scripts/validate_public.py`` instead of maintaining
a second validation list. Container smoke is included by default; callers
without Docker can explicitly omit it with ``--skip-container-smoke``. The
summary is printed without writing a file unless ``--output`` is supplied.

Usage:
    python3 scripts/reproduce_public_artifact.py
    python3 scripts/reproduce_public_artifact.py --skip-container-smoke
    python3 scripts/reproduce_public_artifact.py --json
    python3 scripts/reproduce_public_artifact.py --output /tmp/public-summary.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _public_validation_step(skip_container_smoke: bool) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/validate_public.py",
        "--include-scripted-baseline",
    ]
    if not skip_container_smoke:
        command.append("--include-container-smoke")
    return {
        "id": "public_validation",
        "description": "Dependency-free public validation gate",
        "command": command,
    }


def _run_step(step: dict[str, Any], cwd: Path) -> dict[str, Any]:
    started = time.time()
    try:
        result = subprocess.run(
            step["command"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return {
            "id": step["id"],
            "description": step["description"],
            "command": step["command"],
            "passed": False,
            "returncode": None,
            "elapsed_seconds": round(time.time() - started, 3),
            "stdout_tail": "",
            "stderr_tail": f"executable not found: {exc}",
        }
    return {
        "id": step["id"],
        "description": step["description"],
        "command": step["command"],
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON summary path. No file is written by default.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full summary as JSON.")
    parser.add_argument(
        "--skip-container-smoke",
        action="store_true",
        help="Omit Docker-backed container smoke from the public validation gate.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "scripts" / "validate_public.py").is_file():
        print(f"not an AuthZBench-SaaS repo: {root}", file=sys.stderr)
        return 2

    if shutil.which("docker") is None and not args.skip_container_smoke:
        print(
            "docker is required for the default reproduction; "
            "use --skip-container-smoke to run the dependency-free Python gate only",
            file=sys.stderr,
        )
        return 2

    step = _public_validation_step(args.skip_container_smoke)
    step_results = [_run_step(step, root)]
    overall_passed = all(s["passed"] for s in step_results)
    summary = {
        "schema_version": "public-reproduction-v1",
        "root": ".",
        "container_smoke_included": not args.skip_container_smoke,
        "overall_passed": overall_passed,
        "step_count": len(step_results),
        "passed_step_count": sum(1 for s in step_results if s["passed"]),
        "steps": step_results,
    }

    output_path: Path | None = None
    if args.output is not None:
        output_path = args.output.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        output_note = (
            f"; summary at {output_path}"
            if output_path is not None
            else "; no summary file written"
        )
        if overall_passed:
            print(
                f"reproduction ok: {summary['passed_step_count']}/{summary['step_count']} "
                f"steps passed{output_note}"
            )
        else:
            print(
                f"reproduction FAILED: {summary['passed_step_count']}/{summary['step_count']} "
                f"steps passed{output_note}",
                file=sys.stderr,
            )
            for step in step_results:
                if not step["passed"]:
                    print(f"  - {step['id']} (rc={step['returncode']})", file=sys.stderr)
    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
