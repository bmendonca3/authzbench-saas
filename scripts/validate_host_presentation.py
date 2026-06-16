#!/usr/bin/env python3
"""Aggregate validator for the Kaggle-like host presentation readiness."""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path, timeout: int) -> tuple[bool, str, float]:
    start = time.time()
    try:
        res = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start
        return (res.returncode == 0), res.stdout, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return False, f"Command timed out after {timeout} seconds", elapsed
    except Exception as e:
        elapsed = time.time() - start
        return False, str(e), elapsed


def main():
    parser = argparse.ArgumentParser(description="Aggregate host presentation validation.")
    parser.add_argument(
        "--include-container-smoke",
        action="store_true",
        help="Include containerized smoke testing (requires running Docker daemon).",
    )
    parser.add_argument(
        "--skip-public-validation",
        action="store_true",
        help="Skip the public validation step.",
    )
    parser.add_argument(
        "--skip-git-diff-check",
        action="store_true",
        help="Skip git diff check.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Timeout in seconds for each individual command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow dirty git state when building host review bundle.",
    )
    args = parser.parse_args()

    steps = [
        ("Claim boundary check", [sys.executable, "scripts/check_claim_boundary.py", "--json"], "Ensure docs do not overclaim hosted leaderboard features."),
        ("V1 overclaim check", [sys.executable, "scripts/check_v1_overclaim.py", "--json"], "Ensure no v1.0 release claims exist."),
        ("Kaggle sample submission validator", [sys.executable, "scripts/validate_kaggle_sample_submission.py"], "Check headers and format of sample_submission.csv."),
        ("Kaggle dry-run bundle validator", [sys.executable, "scripts/validate_kaggle_dry_run_bundle.py"], "Check integrity of dry-run files and manifest."),
        ("Kaggle toy solution file validator", [sys.executable, "scripts/validate_kaggle_toy_solution_file.py"], "Verify toy solution columns and expected control types."),
        ("Markdown relative links check", [sys.executable, "scripts/check_markdown_links.py"], "Validate relative markdown file links."),
        ("Host review docs validator", [sys.executable, "scripts/validate_host_review_docs.py"], "Validate existence and contents of host-review docs."),
    ]

    if not args.skip_git_diff_check:
        steps.append(("Git diff check", ["git", "diff", "--check"], "Review trailing whitespace or conflicts in git diff."))

    # Validate public command
    if not args.skip_public_validation:
        validate_public_cmd = [sys.executable, "scripts/validate_public.py", "--include-scripted-baseline"]
        if args.include_container_smoke:
            validate_public_cmd.append("--include-container-smoke")
        steps.append(("Public validation", validate_public_cmd, "Validate the baseline evaluations and target applications."))

    failed = False
    json_results = []

    if not args.json:
        print("Running host presentation validation suite...")
        print("=" * 60)

    for name, cmd, hint in steps:
        if not args.json:
            print(f"Running step: {name} ({' '.join(cmd)})...")
        ok, output, elapsed = run_cmd(cmd, ROOT, args.timeout_seconds)

        json_results.append({
            "step": name,
            "command": cmd,
            "passed": ok,
            "elapsed_seconds": round(elapsed, 3),
            "output": output,
            "remediation_hint": hint
        })

        if not ok:
            failed = True
            if not args.json:
                print(f"FAIL: {name}")
                print(output)
                print("-" * 60)
        else:
            if not args.json:
                print(f"PASS: {name}")

    # Build and validate bundle step
    if not args.json:
        print("Running step: Build and validate host review bundle...")

    bundle_step_passed = True
    bundle_output = ""
    bundle_start = time.time()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
        build_cmd = [sys.executable, "scripts/build_host_review_bundle.py", "--output", str(tmp_path)]
        if args.allow_dirty:
            build_cmd.append("--allow-dirty")
        build_ok, build_out, build_elapsed = run_cmd(
            build_cmd,
            ROOT,
            args.timeout_seconds
        )
        bundle_output += f"=== Build Output ===\n{build_out}\n"
        if not build_ok:
            failed = True
            bundle_step_passed = False
        else:
            val_ok, val_out, val_elapsed = run_cmd(
                [sys.executable, "scripts/validate_host_review_bundle.py", "--bundle-dir", str(tmp_path)],
                ROOT,
                args.timeout_seconds
            )
            bundle_output += f"=== Validation Output ===\n{val_out}\n"
            if not val_ok:
                failed = True
                bundle_step_passed = False

    bundle_elapsed = time.time() - bundle_start
    json_results.append({
        "step": "Build and validate host review bundle",
        "command": ["build_host_review_bundle.py", "validate_host_review_bundle.py"],
        "passed": bundle_step_passed,
        "elapsed_seconds": round(bundle_elapsed, 3),
        "output": bundle_output,
        "remediation_hint": "Check bundle filters, allowlists, required files list, or private markers check."
    })

    if not args.json:
        if bundle_step_passed:
            print("PASS: Build and validate host review bundle")
        else:
            print("FAIL: Build and validate host review bundle")
            print(bundle_output)
            print("-" * 60)

    if args.json:
        print(json.dumps({
            "passed": not failed,
            "results": json_results
        }, indent=2))
        sys.exit(1 if failed else 0)

    print("=" * 60)
    if failed:
        print("Host presentation validation FAILED.")
        sys.exit(1)

    print("Host presentation validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
