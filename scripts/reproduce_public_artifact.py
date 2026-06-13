"""One-command clean-room public validation runner.

The plan section 5.1 wants a single command a reviewer can run on
a fresh clone to reproduce the public artifact. This script wraps
the per-step validation surface and emits a single
``public-reproduction-summary.json`` artifact with the
per-step pass / fail record.

It is intentionally a thin orchestration layer over the existing
``scripts/validate_public.py``,
``scripts/check_claim_boundary.py``,
``scripts/generate_task_oracle_audit.py``,
``scripts/generate_task_taxonomy.py``, and
``scripts/analyze_baseline_variance.py`` entry points. The goal
is "one command, one summary", not a re-implementation of those
scripts.

Usage:
    python3 scripts/reproduce_public_artifact.py
    python3 scripts/reproduce_public_artifact.py --skip-container-smoke
    python3 scripts/reproduce_public_artifact.py --json
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
DEFAULT_OUTPUT = ROOT / "artifact" / "reproduction" / "public-reproduction-summary.json"

STEPS: tuple[dict[str, Any], ...] = (
    {
        "id": "v1_readiness",
        "description": "Public-view v1 readiness fixture match",
        "command": ["python3", "scripts/validate_v1_readiness.py", "--public-view", "--expected-output", "artifact/expected-output/v1-readiness-public-view.json"],
    },
    {
        "id": "claim_boundary",
        "description": "Claim-boundary forbidden-phrase CI check",
        "command": ["python3", "scripts/check_claim_boundary.py"],
    },
    {
        "id": "task_oracle_audit",
        "description": "Task oracle audit (schema gate)",
        "command": ["python3", "scripts/generate_task_oracle_audit.py", "--check"],
    },
    {
        "id": "task_taxonomy",
        "description": "Task taxonomy report",
        "command": ["python3", "scripts/generate_task_taxonomy.py"],
    },
    {
        "id": "baseline_variance",
        "description": "Baseline variance and confidence",
        "command": ["python3", "scripts/analyze_baseline_variance.py", "--require-current-public"],
    },
    {
        "id": "harbor_claim_boundary",
        "description": "Harbor non-claim test",
        "command": ["python3", "-m", "pytest", "tests/test_harbor_claim_boundary.py", "-q"],
    },
)


def _run_step(step: dict[str, Any], cwd: Path, skip_container_smoke: bool) -> dict[str, Any]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true", help="Print the full summary as JSON.")
    parser.add_argument(
        "--skip-container-smoke",
        action="store_true",
        help="Reserved for callers that don't have Docker available. The default step set already skips the per-app container smoke.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "scripts" / "validate_v1_readiness.py").is_file():
        print(f"not an AuthZBench-SaaS repo: {root}", file=sys.stderr)
        return 2

    if shutil.which("docker") is None and not args.skip_container_smoke:
        # The default step set already avoids docker; this is a hint to
        # the operator, not a hard gate.
        pass

    step_results = [_run_step(step, root, args.skip_container_smoke) for step in STEPS]
    overall_passed = all(s["passed"] for s in step_results)
    summary = {
        "schema_version": "public-reproduction-v1",
        "root": str(root),
        "overall_passed": overall_passed,
        "step_count": len(step_results),
        "passed_step_count": sum(1 for s in step_results if s["passed"]),
        "steps": step_results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        if overall_passed:
            print(
                f"reproduction ok: {summary['passed_step_count']}/{summary['step_count']} steps passed; summary at {args.output.relative_to(root)}"
            )
        else:
            print(
                f"reproduction FAILED: {summary['passed_step_count']}/{summary['step_count']} steps passed; summary at {args.output.relative_to(root)}",
                file=sys.stderr,
            )
            for step in step_results:
                if not step["passed"]:
                    print(f"  - {step['id']} (rc={step['returncode']})", file=sys.stderr)
    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
