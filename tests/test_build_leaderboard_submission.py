from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_leaderboard_submission import build_submission
from scripts.protected_private_eval import ROOT, redacted_summary
from scripts.validate_leaderboard_submission import validate_submission


def _active_private_pack_fingerprint() -> str:
    """Return the role=active private pack fingerprint from the
    rotation metadata. The leaderboard submission validator
    (objective-5) requires every leaderboard-eligible
    private-holdout or combined submission to point at this
    fingerprint.
    """
    from authzbench.core import load_json as _load

    rotation = _load(ROOT / "tasks_private" / "holdout" / "rotation-metadata.json")
    for pack in rotation.get("packs", []):
        if pack.get("role") == "active":
            return str(pack["fingerprint_sha256"])
    raise RuntimeError("no active private pack in rotation-metadata.json")


def _runner_summary(run_id: str) -> dict:
    return {
        "agent": "unit-agent",
        "authorized_allow_control_task_count": 6,
        "authorized_allow_pass_rate": 1.0,
        "benchmark_commit_sha": "a" * 40,
        "benchmark_fingerprint": {
            "authorized_allow_control_task_count": 6,
            "control_task_count": 12,
            "denial_control_task_count": 6,
            "evidence_contract_version": "evidence-requirements-v1",
            "schema_version": "benchmark-fingerprint-v1",
            "score_policy_version": "score-policy-v1",
            "scorer_contract": "v0-candidate-authz-evidence",
            "task_count": 24,
            "task_path_set_sha256": "b" * 64,
            "task_set_sha256": "c" * 64,
            "vulnerable_task_count": 12,
        },
        "benchmark_version": "unit-version",
        "boundary_reasoning_pass_rate": 0.25,
        "control_execution_pass_rate": 1.0,
        "control_false_report_count": 0,
        "control_false_report_rate": 0.0,
        "control_task_count": 12,
        "denial_control_task_count": 6,
        "exploit_proven_success_rate": 0.25,
        "exploit_proven_task_count": 3,
        "false_positive_rate": 0.0,
        "harness_type": "no-tools-model",
        "invalid_submission_count": 0,
        "invalid_submission_rate": 0.0,
        "mean_score": 0.625,
        "model": "unit-model",
        "private_pack_fingerprint_sha256": _active_private_pack_fingerprint(),
        "protected_execution": {
            "agent_cwd": "temporary-empty-workspace",
            "agent_received": "rendered-context-only",
            "host_private_paths_denied": True,
            "isolation_backend": "unit-test",
            "private_manifests_readable_in_agent_workspace": False,
            "raw_result_bundle_tracked": False,
            "tracked_private_manifest_count": 0,
        },
        "run_id": run_id,
        "target_request_coverage_rate": None,
        "task_count": 24,
        "v0_mean_score": 0.625,
        "v0_metric_profile": "v0-candidate-authz-evidence",
        "v0_passed_count": 15,
        "vulnerable_full_pass_count": 3,
        "vulnerable_task_count": 12,
    }


class BuildLeaderboardSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        # Skip when the gitignored private-rotation-metadata file is
        # missing. The 4 (a5e5b01-era) tests that follow assert on
        # gate state derived from the active private pack and the
        # repeated private leaderboard rows; in public-CI checkouts
        # the file is intentionally absent and the assertions would
        # otherwise error or fail on environment-specific unmet
        # items. Local runs (where the file is present) are
        # unaffected. See round 2 amendment in
        # docs/release-evidence-tracking.md for the matching
        # validator fix.
        from pathlib import Path
        rotation_metadata = Path("tasks_private") / "holdout" / "rotation-metadata.json"
        if not rotation_metadata.is_file():
            self.skipTest(
                "tasks_private/holdout/rotation-metadata.json not present; "
                "this test depends on the gitignored private holdout rotation metadata"
            )
    def test_runner_redacted_summaries_build_an_eligible_validated_row(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            paths = []
            for run_id in ("unit-run-1", "unit-run-2"):
                path = root / f"{run_id}.json"
                path.write_text(
                    json.dumps(redacted_summary(_runner_summary(run_id)), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
            row = build_submission(
                paths,
                primary_run_id="unit-run-2-redacted",
                baseline_kind="model_baseline",
                leaderboard_eligible=True,
            )
            submission_path = root / "submission.json"
            submission_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_submission(submission_path, require_source_summary=True)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["leaderboard_eligible"], result)
        self.assertEqual(row["run_count"], 2)
        self.assertEqual(row["variance_or_ci"], "stddev=0.0000")

    def test_cross_commit_repeat_cannot_be_eligible(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            first = redacted_summary(_runner_summary("unit-run-1"))
            second_summary = _runner_summary("unit-run-2")
            second_summary["benchmark_commit_sha"] = "d" * 40
            second = redacted_summary(second_summary)
            paths = []
            for name, summary in (("one.json", first), ("two.json", second)):
                path = root / name
                path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                paths.append(path)
            row = build_submission(
                paths,
                primary_run_id="unit-run-2-redacted",
                baseline_kind="model_baseline",
                leaderboard_eligible=True,
            )
            submission_path = root / "submission.json"
            submission_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_submission(submission_path, require_source_summary=True)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("benchmark_commit_sha does not match" in error for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
