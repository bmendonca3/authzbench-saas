from __future__ import annotations

import os
import subprocess
import sys
import unittest

from scripts.validate_v0_release import ROOT, validate_v0_release


class V0ReleaseValidatorTests(unittest.TestCase):
    def test_current_repo_is_v0_release_candidate_ready(self) -> None:
        result = validate_v0_release()
        gates = {gate["id"]: gate for gate in result["gates"]}

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["v0_ready"], result)
        self.assertEqual(result["gate_count"], 8, result)
        self.assertTrue(gates["public_split_scope"]["passed"], result)
        self.assertTrue(gates["documentation_packaging"]["passed"], result)
        self.assertTrue(gates["private_holdout_pack"]["passed"], result)
        self.assertTrue(gates["task_mix"]["passed"], result)
        self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_vulnerable_tasks"], 25, result)
        self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_controls"], 30, result)
        self.assertTrue(gates["baseline_credibility"]["passed"], result)
        self.assertTrue(gates["leaderboard_submissions"]["passed"], result)
        self.assertTrue(gates["sectional_reviews"]["passed"], result)
        self.assertTrue(gates["release_verification_evidence"]["passed"], result)
        self.assertTrue(gates["baseline_credibility"]["evidence"]["v0_baseline_ready"], result)
        self.assertEqual(gates["leaderboard_submissions"]["evidence"]["release_candidate_submission_count"], 1, result)
        self.assertEqual(
            gates["leaderboard_submissions"]["evidence"]["release_candidate_leaderboard_eligible_count"],
            1,
            result,
        )
        self.assertEqual(gates["sectional_reviews"]["evidence"]["v0_ready_section_count"], 6, result)

    def test_allow_incomplete_cli_still_returns_success_for_release_candidate(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py", "--allow-incomplete"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"v0_ready": true', completed.stdout)

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

    def test_strict_cli_passes_when_v0_gates_pass(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"v0_ready": true', completed.stdout)


if __name__ == "__main__":
    unittest.main()
