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
        self.assertEqual(len(paths), 54)
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

    def test_multistep_project_mgmt_evidence_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_multistep_beta_update_then_alpha_alias_read.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "cross_tenant_task_read_after_same_tenant_workflow",
                    "boundary": {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                    "impact": "A Beta member can first establish normal same-tenant task access, then read Alpha task data through a workspace alias.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "beta_member",
                                "method": "PATCH",
                                "path": f"/api/projects/{refs['BETA_PROJECT_ID']}/tasks/{refs['BETA_PRIVATE_TASK_ID']}",
                                "body": {"status": "triaged"},
                            }
                        },
                        {
                            "request": {
                                "actor": "beta_member",
                                "method": "GET",
                                "path": f"/api/workspaces/{refs['ALPHA_PROJECT_ID']}/work-items/{refs['ALPHA_PRIVATE_TASK_ID']}",
                            }
                        },
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 1, result)

    def test_multistep_project_mgmt_evidence_requires_each_step(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_multistep_beta_update_then_alpha_alias_read.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "cross_tenant_task_read_after_same_tenant_workflow",
                    "boundary": {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                    "impact": "A Beta member can read Alpha task data.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "beta_member",
                                "method": "GET",
                                "path": f"/api/workspaces/{refs['ALPHA_PROJECT_ID']}/work-items/{refs['ALPHA_PRIVATE_TASK_ID']}",
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
        self.assertTrue(any("missing evidence step" in str(item) for item in result["observations"]), result)

    def test_multistep_project_mgmt_rejects_duplicate_final_step(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_multistep_beta_update_then_alpha_alias_read.json")
        refs = build_context(task)["refs"]
        duplicate_final_request = {
            "actor": "beta_member",
            "method": "GET",
            "path": f"/api/workspaces/{refs['ALPHA_PROJECT_ID']}/work-items/{refs['ALPHA_PRIVATE_TASK_ID']}",
        }
        submission = {
            "findings": [
                {
                    "claim": "cross_tenant_task_read_after_same_tenant_workflow",
                    "boundary": {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                    "impact": "A Beta member can read Alpha task data.",
                    "evidence": [{"request": duplicate_final_request}, {"request": duplicate_final_request}],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
        self.assertTrue(any("evidence request shape failed" in str(item) for item in result["observations"]), result)

    def _support_reassignment_submission(self) -> tuple[dict, dict]:
        task = load_json(
            ROOT / "tasks/support/sup_multistep_agent_status_then_admin_reassignment.json"
        )
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "agent_can_reassign_ticket_after_status_workflow",
                    "boundary": {
                        "attacker_actor": "acme_agent",
                        "required_role": "admin",
                        "org": "acme",
                        "protected_action": "ticket_reassignment",
                    },
                    "impact": "A non-admin support agent can reassign a ticket after a normal status update.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "acme_agent",
                                "method": "PATCH",
                                "path": (
                                    f"/api/secure/orgs/{refs['ACME_ORG_ID']}"
                                    f"/tickets/{refs['ACME_TICKET_ID']}/status"
                                ),
                                "body": {"status": "pending"},
                            }
                        },
                        {
                            "request": {
                                "actor": "acme_agent",
                                "method": "PATCH",
                                "path": (
                                    f"/api/orgs/{refs['ACME_ORG_ID']}"
                                    f"/cases/{refs['ACME_TICKET_ID']}/owner"
                                ),
                                "body": {"assigned_to": "acme_viewer"},
                            }
                        },
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        return task, submission

    def test_multistep_support_reassignment_scores_full_credit(self) -> None:
        task, submission = self._support_reassignment_submission()
        result = score_submission(task, submission)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 1, result)
        proof_steps = [
            entry for entry in result["transcript"] if entry["name"].startswith("proof_")
        ]
        self.assertEqual(proof_steps[0]["response"]["body"]["ticket"]["assigned_to"], "acme_agent")
        self.assertEqual(proof_steps[1]["response"]["body"]["ticket"]["assigned_to"], "acme_viewer")

    def test_multistep_support_reassignment_rejects_missing_step(self) -> None:
        task, submission = self._support_reassignment_submission()
        submission["findings"][0]["evidence"] = submission["findings"][0]["evidence"][1:]
        result = score_submission(task, submission)

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
        self.assertTrue(any("missing evidence step" in str(item) for item in result["observations"]), result)

    def test_multistep_support_reassignment_rejects_reordered_or_duplicate_steps(self) -> None:
        task, submission = self._support_reassignment_submission()
        original = submission["findings"][0]["evidence"]
        for evidence in ([original[1], original[0]], [original[1], original[1]]):
            with self.subTest(evidence=evidence):
                candidate = json.loads(json.dumps(submission))
                candidate["findings"][0]["evidence"] = evidence
                result = score_submission(task, candidate)
                self.assertFalse(result["passed"], result)
                self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
                self.assertTrue(
                    any("evidence request shape failed" in str(item) for item in result["observations"]),
                    result,
                )

    def test_multistep_support_reassignment_rejects_malformed_evidence(self) -> None:
        task, submission = self._support_reassignment_submission()
        submission["findings"][0]["evidence"] = {"request": {"actor": "acme_agent"}}
        result = score_submission(task, submission)

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
        self.assertTrue(
            any("finding evidence must be a list" in str(item) for item in result["observations"]),
            result,
        )

    def test_malformed_evidence_fails_without_crashing(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")
        submission = {
            "findings": [
                {
                    "claim": "cross_tenant_task_read",
                    "boundary": {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                    "impact": "Malformed evidence should not crash scoring.",
                    "evidence": {"request": {"actor": "beta_member"}},
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
        self.assertTrue(any("finding evidence must be a list" in str(item) for item in result["observations"]), result)

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

    def test_valid_billing_entitlement_submission_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/billing/bill_bfla_member_enables_export_entitlement.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "member_can_enable_billing_entitlement",
                    "boundary": {
                        "attacker_actor": "atlas_member",
                        "required_role": "admin",
                        "org": "atlas",
                        "entitlement": "audit_exports",
                    },
                    "impact": "A non-admin organization member can enable an admin-only billing feature entitlement.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "atlas_member",
                                "method": "PATCH",
                                "path": f"/api/orgs/{refs['ATLAS_ORG_ID']}/entitlements/{refs['ATLAS_ENTITLEMENT_KEY']}",
                                "body": {"enabled": True},
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

    def test_audit_bola_requires_matching_path_org(self) -> None:
        task = load_json(ROOT / "tasks/audit_settings/aud_bola_nimbus_reads_quasar_audit_log.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "cross_org_audit_log_read",
                    "boundary": {
                        "attacker_actor": "nimbus_auditor",
                        "victim_org": "quasar",
                        "required_boundary": "same_org",
                    },
                    "impact": "A Nimbus auditor can read Quasar audit data.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "nimbus_auditor",
                                "method": "GET",
                                "path": f"/api/orgs/{refs['NIMBUS_ORG_ID']}/audit-logs/{refs['QUASAR_AUDIT_LOG_ID']}",
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)

    def test_api_token_bearer_evidence_scores_full_credit(self) -> None:
        task = load_json(ROOT / "tasks/api_tokens/tok_cross_tenant_secret_read.json")
        context = build_context(task)
        refs = context["refs"]
        token = context["actors"]["meridian_read_token"]["token"]
        submission = {
            "findings": [
                {
                    "claim": "token_cross_tenant_secret_read",
                    "boundary": {
                        "attacker_actor": "meridian_read_token",
                        "victim_tenant": "helio",
                        "required_scope": "secrets:read",
                    },
                    "impact": "A Meridian read token can read Helio tenant secret material.",
                    "evidence": [
                        {
                            "request": {
                                "method": "GET",
                                "path": f"/api/secrets/{refs['HELIO_SECRET_ID']}",
                                "headers": {"Authorization": f"Bearer {token}"},
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertTrue(result["passed"], result)
        proof = [entry for entry in result["transcript"] if entry["name"] == "proof"][0]
        self.assertEqual(proof["request"]["headers"]["Authorization"], f"Bearer {token}")

    def test_api_token_unknown_bearer_evidence_fails_closed(self) -> None:
        task = load_json(ROOT / "tasks/api_tokens/tok_cross_tenant_secret_read.json")
        refs = build_context(task)["refs"]
        submission = {
            "findings": [
                {
                    "claim": "token_cross_tenant_secret_read",
                    "boundary": {
                        "attacker_actor": "meridian_read_token",
                        "victim_tenant": "helio",
                        "required_scope": "secrets:read",
                    },
                    "impact": "A Meridian read token can read Helio tenant secret material.",
                    "evidence": [
                        {
                            "request": {
                                "method": "GET",
                                "path": f"/api/secrets/{refs['HELIO_SECRET_ID']}",
                                "headers": {"Authorization": "Bearer not-a-seeded-token"},
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)

    def test_api_token_actor_and_bearer_must_match(self) -> None:
        task = load_json(ROOT / "tasks/api_tokens/tok_cross_tenant_secret_read.json")
        context = build_context(task)
        refs = context["refs"]
        token = context["actors"]["helio_read_token"]["token"]
        submission = {
            "findings": [
                {
                    "claim": "token_cross_tenant_secret_read",
                    "boundary": {
                        "attacker_actor": "meridian_read_token",
                        "victim_tenant": "helio",
                        "required_scope": "secrets:read",
                    },
                    "impact": "A Meridian read token can read Helio tenant secret material.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "meridian_read_token",
                                "method": "GET",
                                "path": f"/api/secrets/{refs['HELIO_SECRET_ID']}",
                                "headers": {"Authorization": f"Bearer {token}"},
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["subscores"]["exploit_proof"], 0, result)

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

    def test_body_only_secure_control_replay_scores_without_status(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_same_tenant_read_control.json")
        task["id"] = "pm_same_tenant_read_control_body_only_unit"
        task["controls"][0].pop("status")
        task["controls"][0]["body_contains"] = {"viewer": "alpha_owner"}
        submission = load_json(ROOT / "examples/submissions/secure_control.no_findings.json")

        result = score_submission(task, submission)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["control_replay_passed"], result)

    def test_vacuous_body_only_secure_control_replay_fails_without_status(self) -> None:
        task = load_json(ROOT / "tasks/project_mgmt/pm_same_tenant_read_control.json")
        task["id"] = "pm_same_tenant_read_control_empty_body_only_unit"
        task["controls"][0].pop("status")
        task["controls"][0]["body_contains"] = {}
        submission = load_json(ROOT / "examples/submissions/secure_control.no_findings.json")

        result = score_submission(task, submission)

        self.assertFalse(result["passed"], result)
        self.assertFalse(result["control_replay_passed"], result)

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
