#!/usr/bin/env python3
"""Cross-platform public validation and privacy check wrapper in Python."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_command(args: list[str], label: str) -> bool:
    print(f"=== Running: {label} ({' '.join(args)}) ===")
    try:
        res = subprocess.run(args, cwd=ROOT)
        if res.returncode != 0:
            print(f"FAIL: {label} exited with code {res.returncode}", file=sys.stderr)
            return False
        print(f"PASS: {label}\n")
        return True
    except Exception as e:
        print(f"FAIL: {label} encountered exception: {e}", file=sys.stderr)
        return False


def run_privacy_check() -> bool:
    print("=== Running: Privacy check (git ls-files verification) ===")
    try:
        deny_paths = [
            "tasks_private/holdout",
            "results",
            "captures",
            "docs/reviews/panel-logs",
            "harbor-jobs",
            ".harbor",
            ".handoff"
        ]
        res = subprocess.run(
            ["git", "ls-files"] + deny_paths,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            detail = res.stderr.strip() or "no error output"
            print(f"ERROR: git ls-files failed: {detail}", file=sys.stderr)
            return False

        output = res.stdout.strip()
        if output:
            print("ERROR: private/raw artifact paths are tracked in git:", file=sys.stderr)
            print(output, file=sys.stderr)
            return False
        print("PASS: Privacy check (no private/raw paths tracked)\n")
        return True
    except Exception as e:
        print(f"ERROR: Encountered exception running git ls-files: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run cross-platform public validation suite.")
    parser.add_argument("--include-container-smoke", action="store_true", help="Include containerized smoke test.")
    args = parser.parse_args()

    python_exe = sys.executable

    val_public = [python_exe, "scripts/validate_public.py", "--include-scripted-baseline"]
    if args.include_container_smoke:
        val_public.append("--include-container-smoke")
    if not run_command(val_public, "Public validation"):
        sys.exit(1)

    if not run_command([python_exe, "scripts/validate_baseline_registry.py"], "Baseline registry validator"):
        sys.exit(1)

    if not run_command([
        python_exe, "scripts/validate_leaderboard_submission.py",
        "--submission", "leaderboard_submissions/**/*.json",
        "--require-source-summary"
    ], "Leaderboard submission validator"):
        sys.exit(1)

    if not run_privacy_check():
        sys.exit(1)

    print("All public validations and privacy checks passed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
