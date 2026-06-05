from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts.validate_leaderboard_submission import ROOT, validate_submission


EXAMPLE = ROOT / "examples" / "leaderboard" / "scripted-sanity-public.leaderboard.json"


def _write_submission(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "submission.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class LeaderboardSubmissionTests(unittest.TestCase):
    def test_public_scripted_example_is_valid_but_not_eligible(self) -> None:
        result = validate_submission(EXAMPLE)

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

    def test_rejects_public_split_marked_leaderboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = load_json(EXAMPLE)
            data["baseline_kind"] = "model_baseline"
            data["harness_type"] = "no-tools-model"
            data["leaderboard_eligible"] = True
            data["run_count"] = 2
            data["variance_or_ci"] = "stddev=0.0000"
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

    def test_valid_private_repeated_model_submission_can_be_eligible(self) -> None:
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
            path = _write_submission(Path(tmp), data)

            result = validate_submission(path)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["leaderboard_eligible"], result)


if __name__ == "__main__":
    unittest.main()
