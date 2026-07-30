"""Regenerate or verify the current deterministic public harness summary.

This artifact is a scorer/harness sanity check, not a model baseline. It is
generated without target-side request logs, so score-policy-v3 can establish
the core authorization result but must leave safety unobserved and promotion
eligibility false.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import SCORE_POLICY_VERSION, dump_json
from authzbench.run import run_benchmark


OUTPUT = ROOT / "baselines" / "scripted-baseline-public-63-summary.json"
RUN_ID = "scripted-sanity-score-policy-v3-public-63"
ARTIFACT_DATE = "2026-07-29"


def build_summary() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="authzbench-scripted-summary.") as tmp:
        summary = run_benchmark(
            ["tasks/*/*.json"],
            "python3 scripts/scripted_baseline_agent.py",
            Path(tmp),
            10,
            benchmark_version="alpha-0.0.1-public-scaffold-local",
            score_policy_version=SCORE_POLICY_VERSION,
            benchmark_commit_sha=None,
            agent="scripted_baseline_agent",
            model="deterministic-script",
            harness_type="scripted",
            target_log_dir=None,
            run_id=RUN_ID,
        )

    summary.pop("run_dir", None)
    summary.update(
        {
            "artifact_schema_version": "scripted-harness-summary-v1",
            "artifact_date": ARTIFACT_DATE,
            "artifact_generated_by": "scripts/generate_scripted_baseline_summary.py",
            # The runner truthfully stamps the observed HEAD SHA whenever every
            # executable benchmark source matches HEAD; this development artifact
            # deliberately keeps the claim null even on an exact-commit-clean tree.
            "benchmark_commit_sha": None,
            "benchmark_source_state": "development-uncommitted-not-release-frozen",
            "source_claim_scope": (
                "The benchmark fingerprint binds the current source tree and public "
                "manifests. benchmark_commit_sha is null because this development "
                "artifact does not claim an exact committed or released source ref."
            ),
        }
    )

    expected = {
        "task_count": 63,
        "passed_count": 63,
        "core_passed_count": 63,
        "promotion_eligible_count": 0,
        "evidence_chain_complete_count": 27,
        "vulnerable_safety_pass_rate": None,
        "vulnerable_safety_observation_coverage_rate": 0.0,
        "target_request_correlated_task_count": None,
        "target_request_coverage_rate": None,
    }
    mismatches = {
        field: {"actual": summary.get(field), "expected": value}
        for field, value in expected.items()
        if summary.get(field) != value
    }
    if mismatches:
        raise ValueError(f"scripted harness invariants failed: {mismatches}")
    if summary.get("benchmark_commit_sha") is not None:
        raise ValueError("development scripted harness summary must not claim a commit SHA")
    if summary.get("benchmark_fingerprint", {}).get("score_policy_version") != SCORE_POLICY_VERSION:
        raise ValueError("scripted harness fingerprint does not use the current score policy")
    return summary


def rendered_summary() -> str:
    return dump_json(build_summary()) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate or verify the deterministic public harness summary."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the generated summary. Without this flag, verify the checked-in artifact.",
    )
    args = parser.parse_args()

    rendered = rendered_summary()
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0
    if not OUTPUT.is_file():
        print(f"missing generated artifact: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != rendered:
        print(
            "scripted harness summary is stale; run "
            "python3 scripts/generate_scripted_baseline_summary.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"verified {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
