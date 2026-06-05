from __future__ import annotations

import os
import subprocess
import sys
import unittest

from scripts.validate_v0_release import ROOT, validate_v0_release


class V0ReleaseValidatorTests(unittest.TestCase):
    def test_current_repo_is_honest_but_not_v0_ready(self) -> None:
        result = validate_v0_release()
        gates = {gate["id"]: gate for gate in result["gates"]}

        self.assertFalse(result["passed"], result)
        self.assertFalse(result["v0_ready"], result)
        self.assertEqual(result["gate_count"], 8, result)
        self.assertTrue(gates["public_split_scope"]["passed"], result)
        self.assertTrue(gates["documentation_packaging"]["passed"], result)
        if gates["private_holdout_pack"]["passed"]:
            self.assertTrue(gates["task_mix"]["passed"], result)
            self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_vulnerable_tasks"], 25, result)
            self.assertGreaterEqual(gates["task_mix"]["evidence"]["total_controls"], 30, result)
        else:
            self.assertFalse(gates["task_mix"]["passed"], result)
            self.assertTrue(
                any("total vulnerable tasks" in item for item in gates["task_mix"]["unmet"]),
                result,
            )
        self.assertTrue(gates["baseline_credibility"]["passed"], result)
        self.assertFalse(gates["leaderboard_submissions"]["passed"], result)
        self.assertFalse(gates["sectional_reviews"]["passed"], result)
        self.assertFalse(gates["release_verification_evidence"]["passed"], result)
        self.assertTrue(gates["baseline_credibility"]["evidence"]["v0_baseline_ready"], result)
        self.assertTrue(
            any("no release-candidate leaderboard submissions" in item for item in gates["leaderboard_submissions"]["unmet"]),
            result,
        )
        self.assertTrue(
            any("fresh_clone_validation_passed" in item for item in gates["release_verification_evidence"]["unmet"]),
            result,
        )

    def test_allow_incomplete_cli_returns_success_for_alpha_audit(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py", "--allow-incomplete"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"v0_ready": false', completed.stdout)

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
            0,
            result,
        )

    def test_strict_cli_fails_until_v0_gates_pass(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_v0_release.py"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('"v0_ready": false', completed.stdout)


if __name__ == "__main__":
    unittest.main()
