from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json, runner_integrity_envelope
from scripts.validate_leaderboard_submission import ROOT, comparability_key, validate_submission


EXAMPLE = ROOT / "examples" / "leaderboard" / "scripted-sanity-public.leaderboard.json"
RELEASE_CANDIDATE = ROOT / "leaderboard_submissions" / "2026-06-05" / "haiku-private-holdout.leaderboard.json"


def _write_submission(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class LeaderboardSubmissionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
