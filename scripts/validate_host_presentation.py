#!/usr/bin/env python3
"""Aggregate validator for the Kaggle-like host presentation readiness."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        res = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return (res.returncode == 0), res.stdout
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Aggregate host presentation validation.")
    parser.add_argument(
        "--include-container-smoke",
        action="store_true",
        help="Include containerized smoke testing (requires running Docker daemon).",
    )
    args = parser.parse_args()

    steps = [
        ("Claim boundary check", ["python3", "scripts/check_claim_boundary.py", "--json"]),
        ("V1 overclaim check", ["python3", "scripts/check_v1_overclaim.py", "--json"]),
        ("Kaggle sample submission validator", ["python3", "scripts/validate_kaggle_sample_submission.py"]),
        ("Kaggle dry-run bundle validator", ["python3", "scripts/validate_kaggle_dry_run_bundle.py"]),
        ("Kaggle toy solution file validator", ["python3", "scripts/validate_kaggle_toy_solution_file.py"]),
        ("Markdown relative links check", ["python3", "scripts/check_markdown_links.py"]),
        ("Host review docs validator", ["python3", "scripts/validate_host_review_docs.py"]),
        ("Git diff check", ["git", "diff", "--check"]),
    ]

    # Validate public command
    validate_public_cmd = ["python3", "scripts/validate_public.py", "--include-scripted-baseline"]
    if args.include_container_smoke:
        validate_public_cmd.append("--include-container-smoke")
    steps.append(("Public validation", validate_public_cmd))

    failed = False
    print("Running host presentation validation suite...")
    print("=" * 60)

    for name, cmd in steps:
        print(f"Running step: {name} ({' '.join(cmd)})...")
        ok, output = run_cmd(cmd, ROOT)
        if not ok:
            print(f"FAIL: {name}")
            print(output)
            print("-" * 60)
            failed = True
        else:
            print(f"PASS: {name}")

    # Build and validate bundle
    print("Running step: Build and validate host review bundle...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
        build_ok, build_out = run_cmd(
            ["python3", "scripts/build_host_review_bundle.py", "--output", str(tmp_path)],
            ROOT,
        )
        if not build_ok:
            print("FAIL: Build host review bundle")
            print(build_out)
            failed = True
        else:
            val_ok, val_out = run_cmd(
                ["python3", "scripts/validate_host_review_bundle.py", "--bundle-dir", str(tmp_path)],
                ROOT,
            )
            if not val_ok:
                print("FAIL: Validate host review bundle")
                print(val_out)
                failed = True
            else:
                print("PASS: Build and validate host review bundle")

    print("=" * 60)
    if failed:
        print("Host presentation validation FAILED.")
        sys.exit(1)

    print("Host presentation validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
