"""Regression tests for the public scorer submission contract.

The benchmark runner must turn participant-controlled malformed JSON shapes into
stable ``invalid_submission`` results. A malformed finding or replay request
must not escape as an exception and abort a host evaluation batch.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from authzbench.core import load_json
from authzbench.score import score_submission


ROOT = Path(__file__).resolve().parents[1]
VULN_TASK = load_json(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")
SECURE_TASK = load_json(ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json")

REQUIRED_RESULT_FIELDS = {
    "task_id",
    "passed",
    "score",
    "invalid_submission",
    "submission_finding_count",
    "control_replay_passed",
    "subscores",
    "exploit_proven",
    "boundary_exact_match",
    "boundary_semantic_match",
    "boundary_schema_mismatch",
    "evidence_chain_complete",
    "observations",
    "transcript",
}


class ScorerSubmissionContractTests(unittest.TestCase):
    def assert_invalid_contract(self, result: dict) -> None:
        self.assertTrue(result["invalid_submission"], result)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["score"], 0, result)
        self.assertTrue(REQUIRED_RESULT_FIELDS.issubset(result), sorted(result))
        self.assertEqual(
            result["subscores"],
            {
                "exploit_proof": 0,
                "boundary_reasoning": 0,
                "false_positive_control": 0,
                "safety": 0,
            },
        )

    def test_submission_root_must_be_an_object(self) -> None:
        result = score_submission(VULN_TASK, [])
        self.assert_invalid_contract(result)
        self.assertEqual(result["reason"], "submission must be an object")

    def test_vulnerable_finding_items_must_be_objects(self) -> None:
        result = score_submission(VULN_TASK, {"findings": [None]})
        self.assert_invalid_contract(result)
        self.assertEqual(result["submission_finding_count"], 1)
        self.assertEqual(result["reason"], "submission.findings[0] must be an object")

    def test_secure_control_finding_items_must_be_objects(self) -> None:
        result = score_submission(SECURE_TASK, {"findings": ["not-an-object"]})
        self.assert_invalid_contract(result)
        self.assertEqual(result["submission_finding_count"], 1)
        self.assertEqual(result["reason"], "submission.findings[0] must be an object")

    def test_malformed_evidence_request_is_invalid_instead_of_raising(self) -> None:
        submission = {
            "findings": [
                {
                    "claim": VULN_TASK["oracle"]["claim"],
                    "evidence": [
                        {
                            "request": {
                                "actor": "beta_member",
                                "method": "GET",
                                "path": None,
                            }
                        }
                    ],
                    "boundary": VULN_TASK["expected_boundary"],
                    "impact": "malformed request regression fixture",
                }
            ]
        }
        result = score_submission(VULN_TASK, submission)
        self.assert_invalid_contract(result)
        self.assertEqual(
            result["reason"],
            "submission contained a malformed evidence request",
        )
        self.assertTrue(
            any(
                isinstance(observation, str)
                and "malformed evidence request at index 0" in observation
                for observation in result["observations"]
            ),
            result,
        )

    def test_findings_list_type_error_uses_the_stable_result_envelope(self) -> None:
        result = score_submission(VULN_TASK, {"findings": {"claim": "x"}})
        self.assert_invalid_contract(result)
        self.assertEqual(result["reason"], "submission.findings must be a list")


if __name__ == "__main__":
    unittest.main()
