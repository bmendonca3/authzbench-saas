from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json, runner_integrity_envelope
from scripts.validate_leaderboard_submission import (
    ROOT,
    _load_rotation_metadata,
    comparability_key,
    validate_submission,
)


def _active_private_pack_fingerprint() -> str:
    """Return the role=active private pack fingerprint from the
    rotation metadata. The leaderboard submission validator
    (objective-5) requires every leaderboard-eligible
    private-holdout or combined submission to point at this
    fingerprint.
    """
    for fingerprint, pack in _load_rotation_metadata().items():
        if pack.get("role") == "active":
            return fingerprint
    raise RuntimeError("no active private pack in rotation-metadata.json")


EXAMPLE = ROOT / "examples" / "leaderboard" / "scripted-sanity-public.leaderboard.json"
RELEASE_CANDIDATE = ROOT / "leaderboard_submissions" / "2026-06-05" / "haiku-private-holdout.leaderboard.json"


def _write_submission(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class LeaderboardSubmissionTests(unittest.TestCase):
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
    def test_public_scripted_example_is_valid_but_not_eligible(self) -> None:
        result = validate_submission(EXAMPLE, require_source_summary=True)

        self.assertTrue(result["passed"], result)
        self.assertFalse(result["leaderboard_eligible"], result)
        self.assertTrue(any("not marked leaderboard_eligible" in item for item in result["warnings"]), result)
        self.assertFalse(any("identity cross-check is limited" in item for item in result["warnings"]), result)

    def test_historical_private_holdout_row_is_valid_but_not_eligible_without_runner_fingerprint(self) -> None:
        result = validate_submission(RELEASE_CANDIDATE, require_source_summary=True)

        self.assertTrue(result["passed"], result)
        self.assertFalse(result["leaderboard_eligible"], result)
        self.assertTrue(any("not marked leaderboard_eligible" in item for item in result["warnings"]), result)

    def test_rejects_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data.pop("benchmark_commit_sha")
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("missing required fields" in error for error in result["errors"]), result)

    def test_require_source_summary_rejects_unbacked_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data.pop("source_run_summary")
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path, require_source_summary=True)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("source_run_summary is required" in error for error in result["errors"]), result)

    def test_rejects_submission_that_disagrees_with_source_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["task_count"] = 43
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path, require_source_summary=True)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("task_count does not match source_run_summary" in error for error in result["errors"]), result)

    def test_rejects_source_summary_that_disagrees_with_task_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = {
                "agent": "unit-agent",
                "model": "unit-model",
                "harness_type": "no-tools-model",
                "benchmark_version": "unit-version",
                "benchmark_commit_sha": "abc123",
                "run_id": "unit-run",
                "task_count": 1,
                "vulnerable_task_count": 1,
                "control_task_count": 0,
                "denial_control_task_count": 0,
                "authorized_allow_control_task_count": 0,
                "v0_metric_profile": "v0-candidate-authz-evidence",
                "v0_passed_count": 1,
                "v0_mean_score": 1.0,
                "invalid_submission_count": 0,
                "invalid_submission_rate": 0.0,
                "exploit_proven_task_count": 1,
                "exploit_proven_success_rate": 1.0,
                "vulnerable_full_pass_count": 1,
                "control_false_report_rate": 0.0,
                "control_execution_pass_rate": 0,
                "authorized_allow_pass_rate": 0,
                "false_positive_rate": 0,
                "boundary_reasoning_pass_rate": 1.0,
                "target_request_coverage_rate": None,
                "mean_score": 1.0,
                "tasks": [
                    {
                        "task_id": "unit-task",
                        "expected_vulnerable": True,
                        "score": 0,
                        "passed": False,
                        "invalid_submission": False,
                        "submission_finding_count": 0,
                        "control_replay_passed": True,
                        "exploit_proof": 0,
                        "boundary_reasoning": 0,
                        "safety": 1,
                    }
                ],
            }
            source_path = tmp_path / "summary.json"
            source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            data = load_json(EXAMPLE)
            data.update(
                {
                    "agent": "unit-agent",
                    "model": "unit-model",
                    "harness_type": "no-tools-model",
                    "benchmark_version": "unit-version",
                    "benchmark_commit_sha": "abc123",
                    "run_id": "unit-run",
                    "task_count": 1,
                    "public_task_count": 1,
                    "private_holdout_task_count": 0,
                    "vulnerable_task_count": 1,
                    "control_task_count": 0,
                    "denial_control_task_count": 0,
                    "authorized_allow_control_task_count": 0,
                    "v0_passed_count": 1,
                    "v0_mean_score": 1.0,
                    "exploit_proven_task_count": 1,
                    "exploit_proven_success_rate": 1.0,
                    "vulnerable_full_pass_count": 1,
                    "control_execution_pass_rate": 0,
                    "authorized_allow_pass_rate": 0,
                    "mean_score": 1.0,
                    "source_run_summary": "summary.json",
                }
            )
            path = _write_submission(tmp_path, data)

            result = validate_submission(path, require_source_summary=True)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("inconsistent with its tasks" in error for error in result["errors"]), result)

    def test_rejects_malformed_task_row_numbers_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = {
                "agent": "unit-agent",
                "model": "unit-model",
                "harness_type": "no-tools-model",
                "benchmark_version": "unit-version",
                "benchmark_commit_sha": "abc123",
                "run_id": "unit-run",
                "task_count": 1,
                "vulnerable_task_count": 0,
                "control_task_count": 1,
                "denial_control_task_count": 1,
                "authorized_allow_control_task_count": 0,
                "v0_metric_profile": "v0-candidate-authz-evidence",
                "v0_passed_count": 1,
                "v0_mean_score": 1.0,
                "invalid_submission_count": 0,
                "invalid_submission_rate": 0.0,
                "exploit_proven_task_count": 0,
                "exploit_proven_success_rate": 0,
                "vulnerable_full_pass_count": 0,
                "control_false_report_rate": 0.0,
                "control_execution_pass_rate": 1.0,
                "authorized_allow_pass_rate": 0,
                "false_positive_rate": 0.0,
                "boundary_reasoning_pass_rate": 0,
                "target_request_coverage_rate": 1.0,
                "mean_score": 1.0,
                "tasks": [
                    {
                        "task_id": "unit-control",
                        "expected_vulnerable": False,
                        "control_type": "denial",
                        "score": "bad",
                        "passed": True,
                        "invalid_submission": False,
                        "submission_finding_count": "bad",
                        "control_replay_passed": True,
                        "target_request_count": "bad",
                    }
                ],
            }
            source_path = tmp_path / "summary.json"
            source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            data = load_json(EXAMPLE)
            data.update(
                {
                    "agent": "unit-agent",
                    "model": "unit-model",
                    "harness_type": "no-tools-model",
                    "benchmark_version": "unit-version",
                    "benchmark_commit_sha": "abc123",
                    "run_id": "unit-run",
                    "task_count": 1,
                    "public_task_count": 1,
                    "private_holdout_task_count": 0,
                    "vulnerable_task_count": 0,
                    "control_task_count": 1,
                    "denial_control_task_count": 1,
                    "authorized_allow_control_task_count": 0,
                    "v0_passed_count": 1,
                    "v0_mean_score": 1.0,
                    "exploit_proven_task_count": 0,
                    "exploit_proven_success_rate": 0,
                    "vulnerable_full_pass_count": 0,
                    "control_execution_pass_rate": 1.0,
                    "authorized_allow_pass_rate": 0,
                    "target_request_coverage_rate": 1.0,
                    "mean_score": 1.0,
                    "source_run_summary": "summary.json",
                }
            )
            path = _write_submission(tmp_path, data)

            result = validate_submission(path, require_source_summary=True)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("target_request_count must be an integer" in error for error in result["errors"]), result)
        self.assertTrue(any("submission_finding_count must be an integer" in error for error in result["errors"]), result)
        self.assertTrue(any("score must be a number" in error for error in result["errors"]), result)

    def test_rejects_public_split_marked_leaderboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data.pop("source_run_summary")
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("split=private-holdout" in error for error in result["errors"]), result)

    def test_rejects_combined_split_until_private_only_metrics_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "combined"
            data["public_task_count"] = 24
            data["private_holdout_task_count"] = 20
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data.pop("source_run_summary")
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("private-only combined metrics" in error for error in result["errors"]), result)

    def test_rejects_harness_check_marked_leaderboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("harness checks" in error for error in result["errors"]), result)

    def test_rejects_one_off_eligible_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("at least two runs" in error for error in result["errors"]), result)
        self.assertTrue(any("variance or confidence" in error for error in result["errors"]), result)

    def test_rejects_placeholder_variance_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "TBD"
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("variance or confidence" in error for error in result["errors"]), result)

    def test_rejects_inconsistent_counts_and_rates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["public_task_count"] = 43
            data["v0_mean_score"] = 0.5
            data["exploit_proven_success_rate"] = 0.5
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("public_task_count + private_holdout_task_count" in error for error in result["errors"]), result)
        self.assertTrue(any("v0_mean_score" in error for error in result["errors"]), result)
        self.assertTrue(any("exploit_proven_success_rate" in error for error in result["errors"]), result)

    def test_rejects_fingerprint_count_or_comparability_key_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["benchmark_fingerprint"]["task_count"] = 45
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("benchmark_fingerprint.task_count" in error for error in result["errors"]), result)
        self.assertTrue(any("comparability_key" in error for error in result["errors"]), result)

    def test_comparability_key_binds_benchmark_commit_and_version(self) -> None:
        data = load_json(EXAMPLE)
        original = comparability_key(data)

        data["benchmark_commit_sha"] = "0" * 40
        self.assertNotEqual(comparability_key(data), original)

        data = load_json(EXAMPLE)
        data["benchmark_version"] = "different-version"
        self.assertNotEqual(comparability_key(data), original)

    def test_eligible_row_requires_runner_emitted_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(RELEASE_CANDIDATE)
            data["leaderboard_eligible"] = True
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("runner-emitted benchmark fingerprints" in error for error in result["errors"]), result)

    def test_eligible_repeat_requires_one_matching_source_summary_per_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["leaderboard_eligible"] = True
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = data["task_count"]
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data["repeat_evidence"] = {
                "aggregation": "primary_run",
                "primary_run_id": data["run_id"],
                "source_run_ids": ["missing-repeat", data["run_id"]],
                "variance_metric": "v0_mean_score",
            }
            data["comparability_key"] = comparability_key(data)
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("one source summary per run" in error for error in result["errors"]), result)

    def test_tool_agent_leaderboard_entry_requires_target_request_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "tool_agent_baseline"
            data["harness_type"] = "tool-agent"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data["target_request_coverage_rate"] = None
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("target_request_coverage_rate" in error for error in result["errors"]), result)

    def test_rejects_tool_agent_kind_with_no_tools_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "tool_agent_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tool_agent_baseline submissions" in error for error in result["errors"]), result)

    def test_rejects_tiny_private_holdout_for_eligible_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["task_count"] = 8
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 8
            data["vulnerable_task_count"] = 4
            data["control_task_count"] = 4
            data["denial_control_task_count"] = 2
            data["authorized_allow_control_task_count"] = 2
            data["v0_passed_count"] = 8
            data["exploit_proven_task_count"] = 4
            data["vulnerable_full_pass_count"] = 4
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("at least 20 private holdout tasks" in error for error in result["errors"]), result)

    def test_rejects_leaderboard_eligible_submission_without_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["vulnerable_task_count"] = 44
            data["control_task_count"] = 0
            data["denial_control_task_count"] = 0
            data["authorized_allow_control_task_count"] = 0
            data["exploit_proven_task_count"] = 44
            data["vulnerable_full_pass_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data["run_id"] = "private-no-controls-run"
            data["source_run_summary"] = "summary.json"
            source = {
                field: data[field]
                for field in (
                    "agent",
                    "model",
                    "harness_type",
                    "benchmark_version",
                    "benchmark_commit_sha",
                    "task_count",
                    "vulnerable_task_count",
                    "control_task_count",
                    "denial_control_task_count",
                    "authorized_allow_control_task_count",
                    "v0_metric_profile",
                    "v0_passed_count",
                    "v0_mean_score",
                    "invalid_submission_count",
                    "invalid_submission_rate",
                    "exploit_proven_task_count",
                    "exploit_proven_success_rate",
                    "vulnerable_full_pass_count",
                    "control_false_report_rate",
                    "control_execution_pass_rate",
                    "authorized_allow_pass_rate",
                    "false_positive_rate",
                    "boundary_reasoning_pass_rate",
                    "target_request_coverage_rate",
                    "mean_score",
                )
            }
            source["run_id"] = data["run_id"]
            (tmp_path / "summary.json").write_text(
                json.dumps(source, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            path = _write_submission(tmp_path, data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("must include secure controls" in error for error in result["errors"]), result)

    def test_valid_private_repeated_model_submission_can_be_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 46
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data["run_id"] = "private-model-run"
            data["repeat_evidence"] = {
                "aggregation": "primary_run",
                "primary_run_id": "private-model-run",
                "source_run_ids": ["private-model-repeat", "private-model-run"],
                "variance_metric": "v0_mean_score",
            }
            data["split"] = "private-holdout"
            data["private_pack_fingerprint_sha256"] = _active_private_pack_fingerprint()
            data["comparability_key"] = comparability_key(data)
            data["source_run_summary"] = "summary.json"
            data["source_run_summaries"] = ["repeat-summary.json", "summary.json"]
            source = {
                field: data[field]
                for field in (
                    "agent",
                    "model",
                    "harness_type",
                    "benchmark_version",
                    "benchmark_commit_sha",
                    "task_count",
                    "vulnerable_task_count",
                    "control_task_count",
                    "denial_control_task_count",
                    "authorized_allow_control_task_count",
                    "v0_metric_profile",
                    "v0_passed_count",
                    "v0_mean_score",
                    "invalid_submission_count",
                    "invalid_submission_rate",
                    "exploit_proven_task_count",
                    "exploit_proven_success_rate",
                    "vulnerable_full_pass_count",
                    "control_false_report_rate",
                    "control_execution_pass_rate",
                    "authorized_allow_pass_rate",
                    "false_positive_rate",
                    "boundary_reasoning_pass_rate",
                    "target_request_coverage_rate",
                    "mean_score",
                )
            }
            source["run_id"] = data["run_id"]
            for field in (
                "leaderboard_schema_version",
                "eligibility_policy_version",
                "benchmark_fingerprint",
                "benchmark_fingerprint_provenance",
                "comparability_key",
                "repeat_evidence",
            ):
                source[field] = data[field]
            source["runner_integrity"] = runner_integrity_envelope(
                source,
                generator="scripts/protected_private_eval.py",
            )
            source["protected_execution"] = {
                "host_private_paths_denied": True,
                "isolation_backend": "unit-test",
            }
            (tmp_path / "summary.json").write_text(
                json.dumps(source, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            repeat_source = copy.deepcopy(source)
            repeat_source["run_id"] = "private-model-repeat"
            repeat_source["runner_integrity"] = runner_integrity_envelope(
                repeat_source,
                generator="scripts/protected_private_eval.py",
            )
            (tmp_path / "repeat-summary.json").write_text(
                json.dumps(repeat_source, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            path = _write_submission(tmp_path, data)

            result = validate_submission(path)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["leaderboard_eligible"], result)

    def test_rejects_leaderboard_eligible_submission_without_source_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 44
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
            data.pop("source_run_summary")
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertFalse(result["passed"], result)
        self.assertFalse(result["leaderboard_eligible"], result)
        self.assertTrue(any("source_run_summary is required" in error for error in result["errors"]), result)

    def _make_dummy_submission(self, findings: int) -> tuple[dict, dict]:
        data = copy.deepcopy(load_json(EXAMPLE))
        tasks = [
            {
                "task_id": "vulnerable",
                "expected_vulnerable": True,
                "score": 1,
                "passed": True,
                "invalid_submission": False,
                "submission_finding_count": 0,
                "control_replay_passed": True,
                "exploit_proof": 1,
                "boundary_reasoning": 1,
                "safety": 1,
            },
            {
                "task_id": "denial",
                "expected_vulnerable": False,
                "control_type": "denial",
                "score": 0,
                "passed": False,
                "invalid_submission": False,
                "submission_finding_count": findings,
                "control_replay_passed": True if findings else False,
                "safety": 1,
            },
            {
                "task_id": "allow",
                "expected_vulnerable": False,
                "control_type": "authorized_allow",
                "score": 1,
                "passed": True,
                "invalid_submission": False,
                "submission_finding_count": 0,
                "control_replay_passed": True,
                "safety": 1,
            }
        ]

        data.update({
            "agent": "unit-agent",
            "model": "unit-model",
            "baseline_kind": "model_baseline",
            "harness_type": "no-tools-model",
            "benchmark_version": "unit-version",
            "benchmark_commit_sha": "abc123",
            "run_id": "unit-run",
            "task_count": 3,
            "public_task_count": 3,
            "private_holdout_task_count": 0,
            "vulnerable_task_count": 1,
            "control_task_count": 2,
            "denial_control_task_count": 1,
            "authorized_allow_control_task_count": 1,
            "v0_passed_count": 2,
            "v0_mean_score": round(2/3, 4),
            "invalid_submission_count": 0,
            "invalid_submission_rate": 0.0,
            "exploit_proven_task_count": 1,
            "exploit_proven_success_rate": 1.0,
            "vulnerable_full_pass_count": 1,
            "control_execution_pass_rate": 1.0 if findings else 0.5,
            "control_false_report_rate": 0.5 if findings else 0.0,
            "false_positive_rate": 0.5 if findings else 0.0,
            "authorized_allow_pass_rate": 1.0,
            "boundary_reasoning_pass_rate": 1.0,
            "target_request_coverage_rate": None,
            "mean_score": round(2/3, 4),
            "source_run_summary": "summary.json",
            "source_run_summaries": ["summary.json"],
        })

        data["benchmark_fingerprint"].update({
            "task_count": 3,
            "vulnerable_task_count": 1,
            "control_task_count": 2,
            "denial_control_task_count": 1,
            "authorized_allow_control_task_count": 1,
        })
        data["repeat_evidence"]["primary_run_id"] = "unit-run"
        data["repeat_evidence"]["source_run_ids"] = ["unit-run"]
        data["comparability_key"] = comparability_key(data)

        source = {
            field: data[field]
            for field in (
                "agent", "model", "harness_type", "benchmark_version", "benchmark_commit_sha",
                "task_count", "vulnerable_task_count", "control_task_count", "denial_control_task_count",
                "authorized_allow_control_task_count", "v0_metric_profile", "v0_passed_count", "v0_mean_score",
                "invalid_submission_count", "invalid_submission_rate", "exploit_proven_task_count", "exploit_proven_success_rate",
                "vulnerable_full_pass_count", "control_false_report_rate", "control_execution_pass_rate", "authorized_allow_pass_rate",
                "false_positive_rate", "boundary_reasoning_pass_rate", "target_request_coverage_rate", "mean_score"
            )
        }
        source["benchmark_fingerprint"] = data["benchmark_fingerprint"]
        source["run_id"] = data["run_id"]
        source["tasks"] = tasks
        return data, source

    def test_recomputed_false_positive_rate_ignores_execution_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data, source = self._make_dummy_submission(findings=0)

            source_path = tmp_path / "summary.json"
            source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            path = _write_submission(tmp_path, data)

            result = validate_submission(path, require_source_summary=True)

        self.assertTrue(result["passed"], result)

    def test_recomputed_false_positive_rate_counts_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data, source = self._make_dummy_submission(findings=1)

            source_path = tmp_path / "summary.json"
            source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            path = _write_submission(tmp_path, data)

            result = validate_submission(path, require_source_summary=True)

        self.assertTrue(result["passed"], result)


    def test_leaderboard_eligible_private_holdout_requires_active_pack_fingerprint(self) -> None:
        """Goal-external-validation-coverage.md objective-5 hard CI
        gate. A leaderboard-eligible private-holdout submission must
        carry a private_pack_fingerprint_sha256 that matches the
        role=active pack in
        tasks_private/holdout/rotation-metadata.json.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 24
            data["leaderboard_eligible"] = True
            data["private_pack_fingerprint_sha256"] = (
                "9" * 64  # deliberately not a real fingerprint
            )
            data["comparability_key"] = comparability_key(data)
            path = _write_submission(tmp_path, data)
            result = validate_submission(path)
        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any(
                "private_pack_fingerprint_sha256" in error
                and "does not match any known pack" in error
                for error in result["errors"]
            ),
            result,
        )

    def test_leaderboard_eligible_private_holdout_rejects_shadow_pack(self) -> None:
        """Pointing a leaderboard-eligible private-holdout submission
        at a shadow pack (role != active) is a hard error, even if
        the fingerprint is otherwise valid.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rotation = _load_rotation_metadata()
            shadow_fp = next(
                fingerprint
                for fingerprint, pack in rotation.items()
                if pack.get("role") == "shadow"
            )
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 24
            data["leaderboard_eligible"] = True
            data["private_pack_fingerprint_sha256"] = shadow_fp
            data["comparability_key"] = comparability_key(data)
            path = _write_submission(tmp_path, data)
            result = validate_submission(path)
        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any(
                "only role=active packs are eligible" in error
                for error in result["errors"]
            ),
            result,
        )

    def test_non_eligible_private_holdout_without_fingerprint_warns_only(self) -> None:
        """A non-leaderboard-eligible private-holdout submission
        (i.e. legacy evidence row) is allowed to omit the
        fingerprint; the validator emits a warning, not a hard
        error.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = copy.deepcopy(load_json(EXAMPLE))
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["split"] = "private-holdout"
            data["public_task_count"] = 0
            data["private_holdout_task_count"] = 24
            data["leaderboard_eligible"] = False
            data.pop("private_pack_fingerprint_sha256", None)
            data["comparability_key"] = comparability_key(data)
            path = _write_submission(tmp_path, data)
            result = validate_submission(path)
        self.assertTrue(
            any(
                "private_pack_fingerprint_sha256" in warning
                and "non-leaderboard-eligible legacy evidence" in warning
                for warning in result["warnings"]
            ),
            result,
        )
        self.assertFalse(
            any(
                "must declare private_pack_fingerprint_sha256" in error
                for error in result["errors"]
            ),
            result,
        )


if __name__ == "__main__":
    unittest.main()
