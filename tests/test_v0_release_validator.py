from __future__ import annotations

import os
import subprocess
import sys
import unittest

from scripts.validate_v0_release import ROOT, validate_v0_release


class V0ReleaseValidatorTests(unittest.TestCase):
    def test_current_repo_reports_readiness_from_available_evidence(self) -> None:
        result = validate_v0_release()
        gates = {gate["id"]: gate for gate in result["gates"]}
        has_private_holdouts = gates["private_holdout_pack"]["passed"]

        self.assertEqual(result["passed"], has_private_holdouts, result)
        self.assertEqual(result["v0_ready"], has_private_holdouts, result)
        self.assertEqual(result["gate_count"], 8, result)
        self.assertTrue(gates["public_split_scope"]["passed"], result)
        self.assertTrue(gates["documentation_packaging"]["passed"], result)
        if has_private_holdouts:
            self.assertTrue(gates["task_mix"]["passed"], result)
            self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_vulnerable_tasks"], 25, result)
            self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_controls"], 30, result)
        else:
            self.assertFalse(gates["task_mix"]["passed"], result)
            self.assertIn("real private holdout pack is missing", gates["private_holdout_pack"]["unmet"])
            self.assertIn("total vulnerable tasks must be at least 25; got 19", gates["task_mix"]["unmet"])
            self.assertIn("total secure controls must be at least 30; got 27", gates["task_mix"]["unmet"])
        self.assertTrue(gates["baseline_credibility"]["passed"], result)
        self.assertTrue(gates["leaderboard_submissions"]["passed"], result)
        self.assertTrue(gates["sectional_reviews"]["passed"], result)
        self.assertTrue(gates["release_verification_evidence"]["passed"], result)
        self.assertTrue(gates["baseline_credibility"]["evidence"]["v0_baseline_ready"], result)
        self.assertEqual(gates["baseline_credibility"]["unmet"], [], result)
        self.assertEqual(gates["baseline_credibility"]["evidence"]["current_public_model_family_count"], 5, result)
        self.assertEqual(gates["baseline_credibility"]["evidence"]["repeated_model_baseline_count"], 5, result)
        self.assertEqual(gates["leaderboard_submissions"]["evidence"]["release_candidate_submission_count"], 1, result)
        self.assertEqual(
            gates["leaderboard_submissions"]["evidence"]["release_candidate_leaderboard_eligible_count"],
            1,
            result,
        )
        self.assertEqual(gates["sectional_reviews"]["evidence"]["v0_ready_section_count"], 6, result)

    def test_allow_incomplete_cli_returns_success_for_current_evidence_state(self) -> None:
        expected = validate_v0_release()["v0_ready"]
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py", "--allow-incomplete"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f'"v0_ready": {str(expected).lower()}', completed.stdout)

    def test_validator_resolves_leaderboard_paths_from_repo_root(self) -> None:
        original_cwd = os.getcwd()
        try:
            os.chdir(ROOT.parent)
            result = validate_v0_release()
        finally:
            os.chdir(original_cwd)

        gates = {gate["id"]: gate for gate in result["gates"]}
        self.assertEqual(gates["leaderboard_submissions"]["evidence"]["example_submission_count"], 1, result)
        self.assertEqual(
            gates["leaderboard_submissions"]["evidence"]["release_candidate_submission_count"],
            1,
            result,
        )
        self.assertEqual(
            gates["leaderboard_submissions"]["evidence"]["release_candidate_leaderboard_eligible_count"],
            1,
            result,
        )

    def test_strict_cli_return_code_matches_current_evidence_state(self) -> None:
        expected = validate_v0_release()["passed"]
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0 if expected else 1, completed.stderr)
        self.assertIn(f'"v0_ready": {str(expected).lower()}', completed.stdout)


if __name__ == "__main__":
    unittest.main()
