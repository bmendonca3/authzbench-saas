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
        self.assertEqual(len(paths), 37)
        for path in paths:
            with self.subTest(path=path.name):
                context = build_context(load_json(path))
                self.assertIn("actors", context)
                self.assertIn("refs", context)
                self.assertIn("api_docs", context)
                self.assertIn("target", context)
                self.assertTrue(context["api_docs"])
                self.assertEqual(context["target"]["seed_header"], "x-authzbench-seed")
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

    def test_valid_billing_plan_read_submission_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/billing/bill_bfla_member_reads_plan_settings.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "member_can_read_billing_plan_settings",
                    "boundary": {"attacker_actor": "atlas_member", "required_role": "admin"},
                    "impact": "A non-admin organization member can read billing-plan settings.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "atlas_member",
                                "method": "GET",
                                "path": f"/api/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["score"], 1.0)

    def test_boundary_mismatch_loses_boundary_reasoning_credit(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "cross_tenant_task_read",
                    "boundary": {"attacker_actor": "beta_member", "victim_tenant": "beta"},
                    "impact": "A member from one tenant can read another tenant's private task.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "beta_member",
                                "method": "GET",
                                "path": f"/api/projects/{refs['ALPHA_PROJECT_ID']}/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}",
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 1)
        self.assertEqual(result["subscores"]["boundary_reasoning"], 0)

    def test_all_vulnerable_controls_must_pass_for_control_credit(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")
        task = task | {
            "controls": [
                *task["controls"],
                {
                    "name": "intentionally_wrong_expected_status",
                    "actor": "beta_member",
                    "method": "GET",
                    "path": "/api/secure/projects/{ALPHA_PROJECT_ID}/tasks/{ALPHA_PRIVATE_TASK_ID}",
                    "status": 200,
                },
            ]
        }
        submission = load_json(ROOT / "examples/submissions/pm_bola_read_alpha_from_beta.valid.json")
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["false_positive_control"], 0)

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

    def test_control_request_bodies_are_replayed(self) -> None:
        task = load_json(ROOT / "tasks/support/sup_bfla_viewer_closes_ticket.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "viewer_can_close_ticket",
                    "boundary": {"attacker_actor": "acme_viewer", "required_role": "agent"},
                    "impact": "A read-only support viewer can close a support ticket.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "acme_viewer",
                                "method": "PATCH",
                                "path": f"/api/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
                                "body": {"status": "closed"},
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        secure_control = [entry for entry in result["transcript"] if entry["name"] == "secure_status_route_denies_viewer_write"][0]
        self.assertEqual(secure_control["request"]["body"], {"status": "closed"})

    def test_secure_control_oracle_body_must_match(self) -> None:
        task = load_json(ROOT / "tasks/support/sup_secure_viewer_status_control.json")
        task["oracle"]["body_contains"] = {"error": "not_the_expected_error"}
        submission = load_json(ROOT / "examples/submissions/secure_control.no_findings.json")
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["score"], 0)


if __name__ == "__main__":
    unittest.main()
