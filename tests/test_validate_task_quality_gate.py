from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_task_quality_gate


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _contract(**overrides):
    data = {
        "schema_version": "task-quality-gate-contract-v1",
        "status": "v1_prep_acceptance_gate",
        "public_claim_boundary": "This contract is not external review evidence and not v1 readiness evidence.",
        "privacy_boundary": "Do not include private manifests, local absolute paths, or private-source details.",
        "required_gates": [
            {"id": "task_family_design_spec", "status": "required", "evidence": ["family objective"]},
            {
                "id": "static_manifest_boundary_validation",
                "status": "required",
                "evidence": ["actor boundary keys"],
            },
            {"id": "app_behavior_tests", "status": "required", "evidence": ["secure denial behavior"]},
            {
                "id": "scorer_fixtures",
                "status": "required",
                "evidence": [
                    "positive_exploit",
                    "wrong_actor",
                    "wrong_tenant",
                    "wrong_object",
                    "missing_boundary",
                    "secure_false_positive_failure",
                    "secure_empty_findings_pass",
                ],
            },
            {"id": "scripted_baseline_sanity", "status": "required", "evidence": ["deterministic row"]},
            {"id": "matrix_and_chart_regeneration", "status": "required", "evidence": ["matrix"]},
            {"id": "privacy_and_public_output_scan", "status": "required", "evidence": ["scan"]},
        ],
    }
    data.update(overrides)
    return data


def _vulnerable_task(**overrides):
    data = {
        "id": "sample_vulnerable",
        "app": "project_mgmt",
        "seed": "public-v0-test",
        "expected_vulnerable": True,
        "allowed_hosts": ["project_mgmt"],
        "policy": "Use local fixtures only.",
        "objective": "Prove cross-tenant read.",
        "output_schema": "Submit JSON with findings[0].claim and evidence.",
        "oracle": {"claim": "cross_tenant_read", "status": 200, "body_contains": {"id": "{ALPHA_TASK_ID}"}},
        "expected_boundary": {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
        "controls": [
            {
                "name": "secure_route_denies_cross_tenant_read",
                "actor": "beta_member",
                "method": "GET",
                "path": "/api/secure/projects/{ALPHA_PROJECT_ID}",
                "status": 403,
            }
        ],
    }
    data.update(overrides)
    return data


def _secure_control(**overrides):
    data = {
        "id": "sample_control",
        "app": "project_mgmt",
        "seed": "public-v0-control",
        "expected_vulnerable": False,
        "control_type": "authorized_allow",
        "allowed_hosts": ["project_mgmt"],
        "policy": "Same-tenant access is allowed.",
        "objective": "Confirm authorized access is not reported.",
        "output_schema": "Submit JSON with findings: [] when no vulnerability is proven.",
        "oracle": {"claim": "no_vulnerability", "status": 200},
        "controls": [
            {
                "name": "same_tenant_allowed",
                "actor": "alpha_owner",
                "method": "GET",
                "path": "/api/projects/{ALPHA_PROJECT_ID}",
                "status": 200,
            }
        ],
    }
    data.update(overrides)
    return data


class TaskQualityGateTests(unittest.TestCase):
    def test_public_tasks_pass_gate(self) -> None:
        result = validate_task_quality_gate.validate_quality_gate(
            ["tasks/*/*.json"],
            validate_task_quality_gate.DEFAULT_CONTRACT,
        )
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["summary"]["task_count"], 54, result)
        self.assertEqual(result["summary"]["vulnerable_task_count"], 21, result)
        self.assertEqual(result["summary"]["denial_control_task_count"], 19, result)
        self.assertEqual(result["summary"]["authorized_allow_control_task_count"], 14, result)

    def test_rejects_vulnerable_task_without_attacker_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            _write_json(contract, _contract())
            _write_json(task, _vulnerable_task(expected_boundary={"victim_tenant": "alpha"}))
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("expected_boundary must include attacker_actor" in error for error in result["errors"]))

    def test_rejects_vulnerable_task_without_secure_denial_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            _write_json(contract, _contract())
            _write_json(
                task,
                _vulnerable_task(
                    controls=[
                        {
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/api/projects/{ALPHA_PROJECT_ID}",
                            "status": 200,
                        }
                    ]
                ),
            )
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("must include a secure denial control" in error for error in result["errors"]))

    def test_rejects_vulnerable_oracle_without_status_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            status_only_task = Path(tmp) / "status-only.json"
            body_only_task = Path(tmp) / "body-only.json"
            _write_json(contract, _contract())
            _write_json(status_only_task, _vulnerable_task(oracle={"claim": "cross_tenant_read", "status": 200}))
            _write_json(
                body_only_task,
                _vulnerable_task(oracle={"claim": "cross_tenant_read", "body_contains": {"id": "{ALPHA_TASK_ID}"}}),
            )

            status_only_result = validate_task_quality_gate.validate_quality_gate([str(status_only_task)], contract)
            body_only_result = validate_task_quality_gate.validate_quality_gate([str(body_only_task)], contract)

        self.assertFalse(status_only_result["passed"], status_only_result)
        self.assertTrue(any("vulnerable oracle must include non-empty body_contains" in error for error in status_only_result["errors"]))
        self.assertFalse(body_only_result["passed"], body_only_result)
        self.assertTrue(any("vulnerable oracle must include status" in error for error in body_only_result["errors"]))

    def test_rejects_secure_control_without_findings_empty_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            _write_json(contract, _contract())
            _write_json(task, _secure_control(output_schema="Submit JSON."))
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("output_schema must require findings: []" in error for error in result["errors"]))

    def test_accepts_body_only_control_replay_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            data = _secure_control()
            data["controls"][0].pop("status")
            data["controls"][0]["body_contains"] = {"viewer": "alpha_owner"}
            _write_json(contract, _contract())
            _write_json(task, data)
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertTrue(result["passed"], result)

    def test_rejects_vacuous_body_only_control_replay_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            data = _secure_control()
            data["controls"][0].pop("status")
            data["controls"][0]["body_contains"] = {}
            _write_json(contract, _contract())
            _write_json(task, data)
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("non-empty body_contains" in error for error in result["errors"]), result)

    def test_rejects_contract_missing_scorer_fixture_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract.json"
            task = Path(tmp) / "task.json"
            broken = _contract()
            scorer_gate = next(gate for gate in broken["required_gates"] if gate["id"] == "scorer_fixtures")
            scorer_gate["evidence"].remove("wrong_object")
            _write_json(contract, broken)
            _write_json(task, _secure_control())
            result = validate_task_quality_gate.validate_quality_gate([str(task)], contract)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("wrong_object" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
