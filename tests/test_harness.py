from __future__ import annotations

import glob
import json
import unittest
from pathlib import Path

from authzbench.core import build_context, load_json
from authzbench.score import score_submission


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def task_paths(self) -> list[Path]:
        return [Path(path) for path in glob.glob(str(ROOT / "tasks" / "*" / "*.json"))]

    def test_all_task_manifests_render(self) -> None:
        paths = self.task_paths()
        self.assertEqual(len(paths), 12)
        for path in paths:
            with self.subTest(path=path.name):
                context = build_context(load_json(path))
                self.assertIn("actors", context)
                self.assertIn("refs", context)
                self.assertIn("api_docs", context)
                self.assertTrue(context["api_docs"])
                self.assertFalse(any("{" in value or "}" in value for value in context["refs"].values()))

    def test_valid_project_mgmt_submission_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")
        submission = load_json(ROOT / "examples/submissions/pm_bola_read_alpha_from_beta.valid.json")
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["score"], 1.0)

    def test_valid_billing_submission_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/billing/bill_bfla_member_plan_change.json")
        submission = load_json(ROOT / "examples/submissions/bill_bfla_member_plan_change.valid.json")
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["score"], 1.0)

    def test_secure_controls_accept_empty_findings(self) -> None:
        submission = load_json(ROOT / "examples/submissions/secure_control.no_findings.json")
        for path in self.task_paths():
            task = load_json(path)
            if task["expected_vulnerable"]:
                continue
            with self.subTest(task=task["id"]):
                result = score_submission(task, submission)
                self.assertTrue(result["passed"], result)

    def test_secure_control_rejects_false_positive(self) -> None:
        task = load_json(ROOT / "tasks/billing/bill_secure_member_plan_control.json")
        submission = {
            "findings": [
                {
                    "claim": "member_can_change_billing_plan",
                    "evidence": [
                        {
                            "request": {
                                "actor": "atlas_member",
                                "method": "GET",
                                "path": "/api/secure/orgs/{ATLAS_ORG_ID}/settings/plan"
                            }
                        }
                    ],
                    "out_of_scope_actions": []
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["score"], 0)


if __name__ == "__main__":
    unittest.main()
