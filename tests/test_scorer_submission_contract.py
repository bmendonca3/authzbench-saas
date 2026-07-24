"""Regression tests for the public scorer submission contract.

The benchmark runner must turn participant-controlled malformed JSON shapes into
stable ``invalid_submission`` results. A malformed finding or replay request
must not escape as an exception and abort a host evaluation batch.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from authzbench.core import build_context, load_json
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
    "claim_present",
    "claim_exact_match",
    "boundary_exact_match",
    "boundary_semantic_match",
    "boundary_partial_match",
    "boundary_schema_mismatch",
    "boundary_match_mode",
    "boundary_field_match_rate",
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
                    "out_of_scope_actions": [],
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

    def test_vulnerable_finding_required_fields_are_enforced(self) -> None:
        valid = {
            "claim": "natural claim",
            "evidence": [{"request": {"path": "/unused"}}],
            "boundary": {},
            "impact": "authorization impact",
            "out_of_scope_actions": [],
        }
        invalid_values = {
            "claim": "",
            "evidence": [],
            "boundary": None,
            "impact": None,
            "out_of_scope_actions": None,
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                result = score_submission(
                    VULN_TASK,
                    {"findings": [valid | {field: value}]},
                )
                self.assert_invalid_contract(result)
                self.assertIn(f"finding.{field}", result["reason"])

    def test_null_or_non_object_optional_request_fields_are_invalid(self) -> None:
        for field, value in (("headers", None), ("headers", []), ("body", None), ("body", "text")):
            with self.subTest(field=field, value=value):
                request = {
                    "actor": "beta_member",
                    "method": "GET",
                    "path": "/api/projects/example/tasks/example",
                    field: value,
                }
                result = score_submission(
                    VULN_TASK,
                    {
                        "findings": [
                            {
                                "claim": "natural claim",
                                "evidence": [{"request": request}],
                                "boundary": {},
                                "impact": "malformed request regression fixture",
                                "out_of_scope_actions": [],
                            }
                        ]
                    },
                )
                self.assert_invalid_contract(result)

    def test_null_evidence_request_is_invalid(self) -> None:
        result = score_submission(
            VULN_TASK,
            {
                "findings": [
                    {
                        "claim": "natural claim",
                        "evidence": [{"request": None}],
                        "boundary": {},
                        "impact": "malformed request regression fixture",
                        "out_of_scope_actions": [],
                    }
                ]
            },
        )
        self.assert_invalid_contract(result)

    def test_participant_request_parser_exception_is_invalid(self) -> None:
        result = score_submission(
            VULN_TASK,
            {
                "findings": [
                    {
                        "claim": "natural claim",
                        "evidence": [
                            {
                                "request": {
                                    "actor": "beta_member",
                                    "method": "GET",
                                    "path": "http://[",
                                }
                            }
                        ],
                        "boundary": {},
                        "impact": "malformed request regression fixture",
                        "out_of_scope_actions": [],
                    }
                ]
            },
        )
        self.assert_invalid_contract(result)
        self.assertTrue(
            any("evidence request replay failed" in str(item) for item in result["observations"]),
            result,
        )

    def test_app_value_conversion_exception_is_invalid(self) -> None:
        task = load_json(ROOT / "tasks/audit_settings/aud_bfla_member_disables_sso.json")
        refs = build_context(task)["refs"]
        result = score_submission(
            task,
            {
                "findings": [
                    {
                        "claim": "natural claim",
                        "evidence": [
                            {
                                "request": {
                                    "actor": "nimbus_member",
                                    "method": "PATCH",
                                    "path": f"/api/orgs/{refs['NIMBUS_ORG_ID']}/security/settings",
                                    "body": {"session_timeout_minutes": "not-an-integer"},
                                }
                            }
                        ],
                        "boundary": {},
                        "impact": "malformed request regression fixture",
                        "out_of_scope_actions": [],
                    }
                ]
            },
        )
        self.assert_invalid_contract(result)

    def test_natural_claim_and_dimension_aware_boundary_ids_can_pass(self) -> None:
        refs = build_context(VULN_TASK)["refs"]
        result = score_submission(
            VULN_TASK,
            {
                "findings": [
                    {
                        "claim": "Beta member can read an Alpha private task across tenants",
                        "evidence": [
                            {
                                "request": {
                                    "actor": "beta_member",
                                    "method": "GET",
                                    "path": (
                                        f"/api/projects/{refs['ALPHA_PROJECT_ID']}"
                                        f"/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}"
                                    ),
                                }
                            }
                        ],
                        "boundary": {
                            "actor": "beta_member",
                            "target_tenant": refs["ALPHA_TENANT_ID"],
                        },
                        "impact": "Cross-tenant private task disclosure",
                        "out_of_scope_actions": [],
                    }
                ]
            },
        )
        self.assertTrue(result["passed"], result)
        self.assertFalse(result["claim_exact_match"], result)
        self.assertTrue(result["boundary_semantic_match"], result)
        self.assertEqual(result["boundary_match_mode"], "semantic", result)
        self.assertEqual(result["boundary_field_match_rate"], 1, result)

    def test_attacker_side_id_cannot_satisfy_victim_dimension(self) -> None:
        submission = {
            "findings": [
                {
                    **{
                        "claim": VULN_TASK["oracle"]["claim"],
                        "evidence": [
                            {
                                "request": {
                                    "actor": "beta_member",
                                    "method": "GET",
                                    "path": "/api/projects/{ALPHA_PROJECT_ID}/tasks/{ALPHA_PRIVATE_TASK_ID}".format(
                                        **build_context(VULN_TASK)["refs"]
                                    ),
                                }
                            }
                        ],
                    },
                    "boundary": {
                        "actor": "beta_member",
                        "actor_tenant": build_context(VULN_TASK)["refs"]["ALPHA_TENANT_ID"],
                    },
                    "impact": "Cross-tenant private task disclosure",
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(VULN_TASK, submission)
        self.assertFalse(result["passed"], result)
        self.assertTrue(result["boundary_partial_match"], result)
        self.assertEqual(result["boundary_field_match_rate"], 0.5, result)
        self.assertEqual(result["subscores"]["boundary_reasoning"], 0, result)

    def test_fabricated_label_with_hex_suffix_is_not_a_runtime_id_match(self) -> None:
        refs = build_context(VULN_TASK)["refs"]
        result = score_submission(
            VULN_TASK,
            {
                "findings": [
                    {
                        "claim": "Cross-tenant task disclosure",
                        "evidence": [
                            {
                                "request": {
                                    "actor": "beta_member",
                                    "method": "GET",
                                    "path": (
                                        f"/api/projects/{refs['ALPHA_PROJECT_ID']}"
                                        f"/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}"
                                    ),
                                }
                            }
                        ],
                        "boundary": {
                            "actor": "beta_member",
                            "target_tenant": "alpha_deadbeef",
                        },
                        "impact": "Cross-tenant private task disclosure",
                        "out_of_scope_actions": [],
                    }
                ]
            },
        )

        self.assertFalse(result["passed"], result)
        self.assertTrue(result["boundary_partial_match"], result)
        self.assertEqual(result["boundary_missing_fields"], ["victim_tenant"], result)


if __name__ == "__main__":
    unittest.main()
