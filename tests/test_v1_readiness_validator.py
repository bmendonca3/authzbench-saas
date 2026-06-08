from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts.containerized_submission_smoke import REQUIRED_CONTAINER_CONSTRAINTS
from scripts.validate_v1_readiness import (
    EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH,
    HOSTED_EXECUTION_RUNBOOK_PATH,
    HOSTED_EXECUTION_TEMPLATE_PATH,
    PRIVATE_OPERATION_RUNBOOK_PATH,
    PRIVATE_ROTATION_METADATA_TEMPLATE_PATH,
    PAPER_READINESS_RUNBOOK_PATH,
    RELEASE_VALIDATION_PRIVACY_SCAN_COMMAND,
    RELEASE_VALIDATION_CI_WORKFLOW_NAME,
    RELEASE_VALIDATION_RUNBOOK_PATH,
    RELEASE_VALIDATION_TEMPLATE_PATH,
    REQUIRED_RELEASE_VALIDATION_COMMANDS,
    REQUIRED_REVIEW_LANES,
    _benchmark_source_compatibility_errors,
    _private_pack_fingerprint,
    _source_summaries_have_private_denial,
    _validate_external_review_evidence,
    _validate_hosted_execution_evidence,
    _validate_hosted_execution_runbook,
    _validate_paper_readiness_evidence,
    _validate_paper_readiness_runbook,
    _validate_private_operation_blocker,
    _validate_private_operation_runbook,
    _validate_private_rotation_metadata,
    _validate_release_candidate_evidence,
    _validate_release_candidate_runbook,
    _validate_v1_scale_roadmap,
    _working_tree_clean,
    validate_v1_readiness,
)


class V1ReadinessValidatorTests(unittest.TestCase):
    def _seed_git_root(self, root: Path) -> str:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "bmendonca3"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "bmendonca3@example.com"], cwd=root, check=True)
        (root / "README.md").write_text("# seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "seed release evidence root"], cwd=root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def _release_candidate_evidence_payload(self, commit_sha: str) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": "v1-release-candidate-validation-v1",
            "commit_sha": commit_sha,
            "benchmark_source_sha": commit_sha,
            "private_pack_fingerprint_sha256": "b" * 64,
            "exact_head_ci_conclusion": "success",
            "exact_head_ci_run_id": "123456789",
            "exact_head_ci_head_sha": commit_sha,
            "exact_head_ci_workflow_name": RELEASE_VALIDATION_CI_WORKFLOW_NAME,
            "exact_head_ci_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/123456789",
            "pushed_commit": True,
            "commands": {
                command: {
                    "passed": True,
                    "exit_code": 0,
                    "evidence": "checked in release validation log",
                }
                for command in REQUIRED_RELEASE_VALIDATION_COMMANDS
            },
        }
        commands = payload["commands"]
        assert isinstance(commands, dict)
        commands[RELEASE_VALIDATION_PRIVACY_SCAN_COMMAND]["evidence"] = "empty output"
        return payload

    def _write_release_candidate_evidence(
        self,
        root: Path,
        payload: dict[str, object],
    ) -> Path:
        evidence = root / "release-evidence.json"
        evidence.write_text(json.dumps(payload), encoding="utf-8")
        return evidence

    def _paper_readiness_payload(self, benchmark_source_sha: str) -> dict[str, object]:
        return {
            "benchmark_source_sha": benchmark_source_sha,
            "claim_boundary_reviewed": True,
            "generated_paper_tables_clean": True,
            "charts_current_stale_legacy_labeled": True,
            "latexmk_main_tex_passed": True,
            "evidence_scope": "release_candidate",
            "upstream_review_and_infrastructure_complete": True,
            "verification": {
                "paper_tables_command": (
                    "python3 scripts/generate_paper_tables.py && git diff --exit-code -- paper/shared"
                ),
                "charts_command": (
                    "python3 scripts/generate_benchmark_charts.py "
                    "&& git diff --exit-code -- docs/assets/benchmark-charts"
                ),
                "latex_command": "latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex",
                "latex_result": "exit 0; PDF generated without LaTeX errors.",
                "verified_on": date.today().isoformat(),
            },
        }

    def test_current_repo_reports_v1_prep_not_v1_ready(self) -> None:
        result = validate_v1_readiness()
        gates = {gate["id"]: gate for gate in result["gates"]}

        self.assertFalse(result["passed"])
        self.assertFalse(result["v1_ready"])
        self.assertEqual(result["gate_count"], 11)
        self.assertTrue(gates["stable_v1_prep_public_evidence"]["passed"])
        self.assertEqual(gates["stable_v1_prep_public_evidence"]["unmet"], [])
        self.assertTrue(gates["external_review_packet_ready"]["passed"])
        self.assertTrue(gates["submission_governance_spec_defined"]["passed"])
        self.assertFalse(gates["external_review_completed"]["passed"])
        self.assertFalse(gates["hosted_or_containerized_submission_execution"]["passed"])
        self.assertFalse(gates["rotating_private_holdouts_implemented"]["passed"])
        self.assertFalse(gates["repeated_private_tool_agent_evidence"]["passed"])
        self.assertFalse(gates["repeated_private_no_tools_evidence"]["passed"])
        self.assertFalse(gates["paper_and_artifact_readiness"]["passed"])
        self.assertIn(
            PAPER_READINESS_RUNBOOK_PATH,
            gates["paper_and_artifact_readiness"]["evidence"],
        )
        self.assertFalse(gates["final_release_candidate_validation"]["passed"])
        self.assertIn(
            RELEASE_VALIDATION_RUNBOOK_PATH,
            gates["final_release_candidate_validation"]["evidence"],
        )
        self.assertIn(
            "independent external review lanes are not complete",
            gates["external_review_completed"]["unmet"],
        )
        self.assertIn(
            "no repeated eligible private-holdout tool-agent leaderboard row exists",
            gates["repeated_private_tool_agent_evidence"]["unmet"],
        )
        self.assertIn(
            "no repeated eligible private-holdout no-tools model leaderboard row exists",
            gates["repeated_private_no_tools_evidence"]["unmet"],
        )
        self.assertFalse(gates["v1_task_scale"]["passed"])
        self.assertIn("artifact/v1-task-scale-roadmap.json", gates["v1_task_scale"]["evidence"])
        self.assertIn("planned_total_task_count=102", gates["v1_task_scale"]["evidence"])
        self.assertIn(
            "total public plus private holdout tasks is 54, expected at least 100",
            gates["v1_task_scale"]["unmet"],
        )

    def test_strict_cli_fails_until_v1_is_really_ready(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_v1_readiness.py"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertEqual(result.stderr, "")

    def test_allow_incomplete_cli_passes_for_v1_prep_validation(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_v1_readiness.py", "--allow-incomplete"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertEqual(result.stderr, "")

    def test_public_view_ignores_private_checkout_rotation_state(self) -> None:
        with patch(
            "scripts.validate_v1_readiness._validate_private_rotation_metadata"
        ) as rotation_validator:
            result = validate_v1_readiness(public_view=True)

        rotation_validator.assert_not_called()
        gates = {gate["id"]: gate for gate in result["gates"]}
        rotation_gate = gates["rotating_private_holdouts_implemented"]
        self.assertFalse(rotation_gate["passed"])
        self.assertIn(
            "private holdout rotation is intentionally not inspected in public view",
            rotation_gate["unmet"],
        )
        self.assertIn(
            "private holdout operation is blocked until active and shadow/candidate private packs and repeated private rows exist",
            rotation_gate["unmet"],
        )
        self.assertIn("artifact/private-holdout-operation-blocker.json", rotation_gate["evidence"])
        self.assertIn(PRIVATE_OPERATION_RUNBOOK_PATH, rotation_gate["evidence"])
        self.assertIn("validated_private_holdout_task_count=0", rotation_gate["evidence"])

    def test_private_operation_blocker_is_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "private-holdout-operation-blocker-v1",
                        "evidence_status": "blocked",
                        "public_claim_boundary": "Structured blocker evidence only; not v1 private operation.",
                        "blocked_gates": [
                            "rotating_private_holdouts_implemented",
                            "repeated_private_tool_agent_evidence",
                            "repeated_private_no_tools_evidence",
                            "v1_task_scale",
                        ],
                        "blocker": "Needs active and shadow private packs plus repeated private rows.",
                        "next_actions": ["Stage private packs under the maintainer-only holdout root."],
                        "required_private_inputs": ["active private pack", "shadow private pack"],
                        "current_public_view": {
                            "public_task_count": 54,
                            "validated_private_holdout_task_count": 0,
                            "total_task_count": 54,
                            "required_total_task_count": 100,
                        },
                        "last_verified_public_readiness": {
                            "reference_scope": "prior_public_checkpoint",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "ci_run_id": "1",
                            "workflow": RELEASE_VALIDATION_CI_WORKFLOW_NAME,
                            "v1_ready": False,
                            "passed_gate_count": 3,
                            "unmet_gate_count": 8,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["unmet"],
            [
                "private holdout operation is blocked until active and shadow/candidate private packs and repeated private rows exist",
            ],
        )

    def test_private_operation_blocker_requires_concrete_public_safe_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "TBD",
                        "blocked_gates": ["rotating_private_holdouts_implemented"],
                        "blocker": "TBD",
                        "next_actions": ["TBD"],
                        "required_private_inputs": ["TBD"],
                        "current_public_view": {
                            "public_task_count": 49,
                            "validated_private_holdout_task_count": 1,
                            "total_task_count": 50,
                            "required_total_task_count": 99,
                        },
                        "last_verified_public_readiness": {
                            "commit_sha": "not-a-sha",
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/not-a-run",
                            "workflow": "TBD",
                            "v1_ready": True,
                            "passed_gate_count": "3",
                            "unmet_gate_count": "8",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be private-holdout-operation-blocker-v1", result["unmet"])
        self.assertIn("evidence_status must be blocked", result["unmet"])
        self.assertIn(
            "blocked_gates must include: repeated_private_tool_agent_evidence, repeated_private_no_tools_evidence, v1_task_scale",
            result["unmet"],
        )
        self.assertIn("blocker is required", result["unmet"])
        self.assertIn("public_claim_boundary is required", result["unmet"])
        self.assertIn("next_actions must list concrete non-placeholder values", result["unmet"])
        self.assertIn("required_private_inputs must list concrete non-placeholder values", result["unmet"])
        self.assertIn("current_public_view.public_task_count must match current public count 54", result["unmet"])
        self.assertIn("current_public_view.validated_private_holdout_task_count must be 0", result["unmet"])
        self.assertIn("current_public_view.total_task_count must equal public_task_count in public view", result["unmet"])
        self.assertIn("current_public_view.required_total_task_count must be 100", result["unmet"])
        self.assertIn(
            "last_verified_public_readiness.reference_scope must be prior_public_checkpoint",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_readiness.commit_sha must be a 40-character lowercase Git SHA",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_readiness.ci_run_url must reference an AuthZBench-SaaS Actions run",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_readiness.ci_run_id must be a numeric GitHub Actions run id",
            result["unmet"],
        )
        self.assertIn(
            f"last_verified_public_readiness.workflow must be {RELEASE_VALIDATION_CI_WORKFLOW_NAME}",
            result["unmet"],
        )
        self.assertIn("last_verified_public_readiness.v1_ready must be false", result["unmet"])

    def test_private_operation_blocker_requires_matching_ci_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "private-holdout-operation-blocker-v1",
                        "evidence_status": "blocked",
                        "public_claim_boundary": "Structured blocker evidence only; not v1 private operation.",
                        "blocked_gates": [
                            "rotating_private_holdouts_implemented",
                            "repeated_private_tool_agent_evidence",
                            "repeated_private_no_tools_evidence",
                            "v1_task_scale",
                        ],
                        "blocker": "Needs active and shadow private packs plus repeated private rows.",
                        "next_actions": ["Stage private packs under the maintainer-only holdout root."],
                        "required_private_inputs": ["active private pack", "shadow private pack"],
                        "current_public_view": {
                            "public_task_count": 54,
                            "validated_private_holdout_task_count": 0,
                            "total_task_count": 54,
                            "required_total_task_count": 100,
                        },
                        "last_verified_public_readiness": {
                            "reference_scope": "prior_public_checkpoint",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "ci_run_id": "2",
                            "workflow": RELEASE_VALIDATION_CI_WORKFLOW_NAME,
                            "v1_ready": False,
                            "passed_gate_count": 3,
                            "unmet_gate_count": 8,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertIn("last_verified_public_readiness.ci_run_id must match ci_run_url", result["unmet"])

    def test_private_operation_runbook_is_structured_procedure_evidence(self) -> None:
        result = _validate_private_operation_runbook()

        self.assertTrue(result["passed"])
        self.assertEqual(result["path"], PRIVATE_OPERATION_RUNBOOK_PATH)
        self.assertEqual(result["unmet"], [])

    def test_private_operation_runbook_rejects_overclaiming_and_incomplete_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook = root / "artifact" / "private-holdout-operation-runbook.json"
            runbook.parent.mkdir(parents=True)
            runbook.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "private holdout evidence",
                        "required_private_inputs": ["TBD"],
                        "operation_steps": ["stage active pack under ignored maintainer holdout root"],
                        "required_rotation_metadata_fields": ["packs"],
                        "acceptance_checks": ["exactly one active pack"],
                        "publication_rules": ["TBD"],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_runbook(root)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be private-holdout-operation-runbook-v1", result["unmet"])
        self.assertIn("evidence_status must be runbook", result["unmet"])
        self.assertIn(
            "public_claim_boundary must state that the runbook is not private holdout evidence",
            result["unmet"],
        )
        self.assertIn(
            "required_private_inputs missing: active holdout pack, active pack fingerprint, maintainer-only evidence root, repeated private no-tools row, repeated private tool-agent row, rotation metadata, shadow or candidate holdout pack",
            result["unmet"],
        )
        self.assertIn("required_private_inputs cannot contain placeholders", result["unmet"])
        self.assertTrue(any(item.startswith("operation_steps missing:") for item in result["unmet"]))
        self.assertTrue(
            any(item.startswith("required_rotation_metadata_fields missing:") for item in result["unmet"])
        )
        self.assertIn("command_templates must be a list", result["unmet"])
        self.assertTrue(any(item.startswith("command_templates missing snippet:") for item in result["unmet"]))
        self.assertTrue(any(item.startswith("acceptance_checks missing:") for item in result["unmet"]))
        self.assertIn("publication_rules cannot contain placeholders", result["unmet"])

    def test_v1_scale_roadmap_is_structured_planning_evidence(self) -> None:
        result = _validate_v1_scale_roadmap(
            public_task_count=54,
            validated_private_holdout_task_count=0,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["path"], "artifact/v1-task-scale-roadmap.json")
        self.assertEqual(result["planned_additional_task_count"], 48)
        self.assertEqual(result["planned_total_task_count"], 102)
        self.assertEqual(result["unmet"], [])

    def test_v1_scale_roadmap_rejects_overclaiming_and_under_target_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roadmap = root / "artifact" / "v1-task-scale-roadmap.json"
            roadmap.parent.mkdir(parents=True)
            roadmap.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "complete",
                        "public_claim_boundary": "v1 scale complete",
                        "current_public_task_count": 54,
                        "current_validated_private_holdout_task_count": 1,
                        "required_total_task_count": 99,
                        "minimum_additional_tasks_required": 1,
                        "acceptance_criteria": ["manifest validation"],
                        "planned_waves": [
                            {
                                "id": "active-wave",
                                "split": "private-holdout-active",
                                "status": "planned",
                                "planned_task_count": 10,
                                "families": ["billing entitlement misuse"],
                                "control_requirements": {
                                    "denial_controls": True,
                                    "authorized_allow_controls": False,
                                    "scorer_fixtures_or_replay_evidence": True,
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_v1_scale_roadmap(
                root,
                public_task_count=54,
                validated_private_holdout_task_count=0,
            )

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be v1-task-scale-roadmap-v1", result["unmet"])
        self.assertIn("evidence_status must be planning", result["unmet"])
        self.assertIn(
            "public_claim_boundary must state that the roadmap is not task-scale evidence",
            result["unmet"],
        )
        self.assertIn(
            "current_validated_private_holdout_task_count must match validated private holdout task count",
            result["unmet"],
        )
        self.assertIn("required_total_task_count must be 100", result["unmet"])
        self.assertIn(
            "minimum_additional_tasks_required must be 46 for the current task counts",
            result["unmet"],
        )
        self.assertIn(
            "acceptance_criteria missing: authorized-allow controls, chart and table regeneration, "
            "denial controls, scorer fixtures or replay evidence, stale-baseline marking",
            result["unmet"],
        )
        self.assertIn("active-wave: authorized_allow_controls must be true", result["unmet"])
        self.assertIn(
            "planned_waves must include a private-holdout-shadow or private-holdout-candidate wave",
            result["unmet"],
        )
        self.assertIn("planned total task count is 64, expected at least 100", result["unmet"])

    def test_private_operation_blocker_rejects_sensitive_public_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "private-holdout-operation-blocker-v1",
                        "evidence_status": "blocked",
                        "public_claim_boundary": "Structured blocker evidence only; not v1 private operation.",
                        "blocked_gates": [
                            "rotating_private_holdouts_implemented",
                            "repeated_private_tool_agent_evidence",
                            "repeated_private_no_tools_evidence",
                            "v1_task_scale",
                        ],
                        "blocker": "Needs active and shadow private packs plus repeated private rows.",
                        "next_actions": ["Stage private packs without publishing private internals."],
                        "required_private_inputs": ["active private pack", "shadow private pack"],
                        "current_public_view": {
                            "public_task_count": 54,
                            "validated_private_holdout_task_count": 0,
                            "total_task_count": 54,
                            "required_total_task_count": 100,
                        },
                        "last_verified_public_readiness": {
                            "reference_scope": "prior_public_checkpoint",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "v1_ready": False,
                            "passed_gate_count": 3,
                            "unmet_gate_count": 8,
                        },
                        "task_id": "private-task-001",
                        "debug_note": "raw output stored under /Users/example/tasks_private/holdout/active",
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertTrue(any("sensitive key is not allowed" in item for item in result["unmet"]), result)
        self.assertTrue(any("sensitive path marker is not allowed" in item for item in result["unmet"]), result)
        self.assertTrue(any("absolute path is not allowed" in item for item in result["unmet"]), result)

    def test_expected_output_fixture_mismatch_fails_even_when_incomplete_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "expected.json"
            fixture.write_text('{"v1_ready": true}\n', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_v1_readiness.py",
                    "--allow-incomplete",
                    "--public-view",
                    "--expected-output",
                    str(fixture),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertIn("does not match expected fixture", result.stderr)

    def test_hosted_smoke_requires_structured_passed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "failed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "pack-v1",
                        "isolation_model": "container",
                        "command": "smoke failed; private isolation not passed",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("submission-runner smoke result must be passed", result["unmet"])
        self.assertIn("benchmark_source_sha must match release benchmark_source_sha", result["unmet"])
        self.assertIn("active private pack fingerprint is required for hosted smoke evidence", result["unmet"])
        self.assertIn("schema_version must be submission-runner-smoke-v1", result["unmet"])
        self.assertIn("container_constraints are incomplete", result["unmet"])

    def test_hosted_execution_runbook_is_structured_procedure_evidence(self) -> None:
        result = _validate_hosted_execution_runbook()

        self.assertTrue(result["passed"])
        self.assertEqual(result["path"], HOSTED_EXECUTION_RUNBOOK_PATH)
        self.assertEqual(result["execution_modes"], ["fully_containerized", "hosted_runner"])
        self.assertEqual(result["unmet"], [])

    def test_hosted_execution_gate_includes_runbook_but_stays_blocked(self) -> None:
        result = validate_v1_readiness(public_view=True)
        gates = {gate["id"]: gate for gate in result["gates"]}
        hosted_gate = gates["hosted_or_containerized_submission_execution"]

        self.assertFalse(hosted_gate["passed"])
        self.assertIn("artifact/submission-runner-smoke.json", hosted_gate["evidence"])
        self.assertIn(HOSTED_EXECUTION_RUNBOOK_PATH, hosted_gate["evidence"])
        self.assertEqual(
            hosted_gate["unmet"],
            ["hosted/containerized release-candidate smoke is blocked until active private-pack inputs exist"],
        )

    def test_hosted_execution_runbook_rejects_overclaiming_and_incomplete_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook = root / "artifact" / "hosted-submission-execution-runbook.json"
            runbook.parent.mkdir(parents=True)
            runbook.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "release smoke evidence",
                        "required_private_inputs": ["TBD"],
                        "execution_modes": [
                            {
                                "mode": "hosted_runner",
                                "command": "run hosted smoke",
                                "isolation_controls": ["network=none"],
                                "required_smoke_evidence_fields": ["result"],
                            }
                        ],
                        "publication_rules": ["TBD"],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_runbook(root)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be hosted-submission-execution-runbook-v1", result["unmet"])
        self.assertIn("evidence_status must be runbook", result["unmet"])
        self.assertIn(
            "public_claim_boundary must state that the runbook is not release smoke evidence",
            result["unmet"],
        )
        self.assertIn(
            "required_private_inputs missing: active private pack fingerprint, active private pack path, active private pack version, benchmark source sha, maintainer runner image or hosted runner version",
            result["unmet"],
        )
        self.assertIn("required_private_inputs cannot contain placeholders", result["unmet"])
        self.assertIn("hosted_runner: command must use placeholders and release_candidate scope", result["unmet"])
        self.assertIn("execution_modes must include fully_containerized", result["unmet"])
        self.assertIn("publication_rules cannot contain placeholders", result["unmet"])

    def test_paper_readiness_runbook_is_structured_procedure_evidence(self) -> None:
        result = _validate_paper_readiness_runbook()

        self.assertTrue(result["passed"])
        self.assertEqual(result["path"], PAPER_READINESS_RUNBOOK_PATH)
        self.assertEqual(result["unmet"], [])

    def test_paper_readiness_runbook_rejects_overclaiming_and_incomplete_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook = root / PAPER_READINESS_RUNBOOK_PATH
            runbook.parent.mkdir(parents=True)
            runbook.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "paper readiness evidence",
                        "required_inputs": ["TBD"],
                        "refresh_steps": ["regenerate paper tables"],
                        "required_commands": ["python3 scripts/generate_paper_tables.py", "TBD"],
                        "acceptance_checks": ["claim boundary reviewed", "TBD"],
                        "publication_rules": ["TBD"],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_paper_readiness_runbook(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "schema_version must be v1-paper-readiness-runbook-v1",
            result["unmet"],
        )
        self.assertIn("evidence_status must be runbook", result["unmet"])
        self.assertIn(
            "public_claim_boundary must state that the runbook is not paper readiness evidence",
            result["unmet"],
        )
        self.assertIn("required_inputs cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("required_inputs missing:") for item in result["unmet"])
        )
        self.assertTrue(
            any(item.startswith("refresh_steps missing:") for item in result["unmet"])
        )
        self.assertTrue(
            any(item.startswith("required_commands missing:") for item in result["unmet"])
        )
        self.assertIn("required_commands cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("acceptance_checks missing:") for item in result["unmet"])
        )
        self.assertIn("acceptance_checks cannot contain placeholders", result["unmet"])
        self.assertIn("publication_rules cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("publication_rules missing:") for item in result["unmet"])
        )

    def test_hosted_smoke_requires_active_private_pack_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "private-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "run private smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="c" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "private_pack_fingerprint_sha256 must match the active private pack fingerprint",
            result["unmet"],
        )

    def test_hosted_smoke_template_lists_release_candidate_shape(self) -> None:
        template = json.loads(Path(HOSTED_EXECUTION_TEMPLATE_PATH).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        self.assertEqual(template["execution_scope"], "release_candidate")
        self.assertEqual(set(template["container_constraints"]), REQUIRED_CONTAINER_CONSTRAINTS)
        for field in (
            "result",
            "benchmark_source_sha",
            "runner_image_or_hosted_version",
            "private_pack_version",
            "private_pack_fingerprint_sha256",
            "isolation_model",
            "command",
            "submitter_private_manifest_read_denied",
            "scorer_controlled_private_eval",
            "cleanup_completed",
            "privacy_scan_passed",
            "public_output_private_artifacts_included",
        ):
            self.assertIn(field, template)
            self.assertNotEqual(template[field], True)
            self.assertNotEqual(template[field], False)

    def test_hosted_smoke_template_is_not_release_candidate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                Path(HOSTED_EXECUTION_TEMPLATE_PATH).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "submission-runner smoke template is not release-candidate hosted execution evidence",
            result["unmet"],
        )

    def test_hosted_smoke_release_candidate_evidence_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "execution_scope": "release_candidate",
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1@sha256:example",
                        "private_pack_version": "active-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container-rendered-context-only",
                        "command": "containerized submission smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                        "container_constraints": [
                            "network=none",
                            "read_only_rootfs",
                            "cap_drop=ALL",
                            "no_new_privileges",
                            "non_root_user",
                            "resource_limits",
                            "rendered_context_mount_only",
                            "output_file_size_limit",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_hosted_smoke_rejects_template_placeholders_after_schema_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "execution_scope": "release_candidate",
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "<maintainer-runner-image-digest-or-hosted-runner-version>",
                        "private_pack_version": "<active-private-pack-version-from-rotation-metadata>",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "<hosted-or-containerized-private-evaluation-isolation-model>",
                        "command": "<release-candidate smoke command or hosted-runner invocation>",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                        "container_constraints": [
                            "network=none",
                            "read_only_rootfs",
                            "cap_drop=ALL",
                            "no_new_privileges",
                            "non_root_user",
                            "resource_limits",
                            "rendered_context_mount_only",
                            "output_file_size_limit",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("runner_image_or_hosted_version must not be a template placeholder", result["unmet"])
        self.assertIn("private_pack_version must not be a template placeholder", result["unmet"])
        self.assertIn("isolation_model must not be a template placeholder", result["unmet"])
        self.assertIn("command must not be a template placeholder", result["unmet"])

    def test_hosted_smoke_blocked_evidence_is_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-blocker-v1",
                        "evidence_status": "blocked",
                        "blocked_gate": "hosted_or_containerized_submission_execution",
                        "blocker": "Needs the active private pack and maintainer-platform release smoke.",
                        "next_action": "Run the release-candidate smoke on the maintainer platform.",
                        "required_release_inputs": [
                            "active private pack path",
                            "active private pack version",
                            "active private pack fingerprint",
                            "maintainer-platform runner image or hosted version",
                        ],
                        "last_verified_public_rehearsal": {
                            "reference_scope": "prior_public_checkpoint",
                            "execution_scope": "rehearsal",
                            "result": "passed",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "ci_run_id": "1",
                            "workflow": RELEASE_VALIDATION_CI_WORKFLOW_NAME,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["unmet"],
            [
                "hosted/containerized release-candidate smoke is blocked until active private-pack inputs exist",
            ],
        )

    def test_hosted_smoke_blocked_evidence_requires_specific_release_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "evidence_status": "blocked",
                        "blocked_gate": "wrong-gate",
                        "blocker": "TBD",
                        "next_action": "TBD",
                        "required_release_inputs": ["TBD"],
                        "last_verified_public_rehearsal": {
                            "execution_scope": "release_candidate",
                            "result": "failed",
                            "commit_sha": "not-a-sha",
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/not-a-run",
                            "workflow": "TBD",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be submission-runner-smoke-blocker-v1", result["unmet"])
        self.assertIn("blocked_gate must be hosted_or_containerized_submission_execution", result["unmet"])
        self.assertIn("blocker is required", result["unmet"])
        self.assertIn("next_action is required", result["unmet"])
        self.assertIn("required_release_inputs must list concrete missing release inputs", result["unmet"])
        self.assertIn(
            "last_verified_public_rehearsal.reference_scope must be prior_public_checkpoint",
            result["unmet"],
        )
        self.assertIn("last_verified_public_rehearsal.execution_scope must be rehearsal", result["unmet"])
        self.assertIn("last_verified_public_rehearsal.result must be passed", result["unmet"])
        self.assertIn(
            "last_verified_public_rehearsal.commit_sha must be a 40-character lowercase Git SHA",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_rehearsal.ci_run_url must reference an AuthZBench-SaaS Actions run",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_rehearsal.ci_run_id must be a numeric GitHub Actions run id",
            result["unmet"],
        )
        self.assertIn(
            f"last_verified_public_rehearsal.workflow must be {RELEASE_VALIDATION_CI_WORKFLOW_NAME}",
            result["unmet"],
        )

    def test_hosted_smoke_blocked_evidence_requires_matching_ci_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-blocker-v1",
                        "evidence_status": "blocked",
                        "blocked_gate": "hosted_or_containerized_submission_execution",
                        "blocker": "Needs the active private pack and maintainer-platform release smoke.",
                        "next_action": "Run the release-candidate smoke on the maintainer platform.",
                        "required_release_inputs": [
                            "active private pack path",
                            "active private pack version",
                            "active private pack fingerprint",
                            "maintainer-platform runner image or hosted version",
                        ],
                        "last_verified_public_rehearsal": {
                            "reference_scope": "prior_public_checkpoint",
                            "execution_scope": "rehearsal",
                            "result": "passed",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "ci_run_id": "2",
                            "workflow": RELEASE_VALIDATION_CI_WORKFLOW_NAME,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("last_verified_public_rehearsal.ci_run_id must match ci_run_url", result["unmet"])

    def test_hosted_smoke_rejects_rehearsal_execution_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "passed",
                        "execution_scope": "rehearsal",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "ci-rehearsal",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "run private smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "submission-runner smoke execution_scope must be release_candidate",
            result["unmet"],
        )
        self.assertIn(
            "rehearsal smoke evidence is not release-candidate evidence",
            result["unmet"],
        )

    def test_hosted_smoke_rejects_sensitive_public_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "execution_scope": "release_candidate",
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "private-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "read /Users/example/tasks_private/holdout",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                        "container_constraints": [
                            "network=none",
                            "read_only_rootfs",
                            "cap_drop=ALL",
                            "no_new_privileges",
                            "non_root_user",
                            "resource_limits",
                            "rendered_context_mount_only",
                            "output_file_size_limit",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("sensitive path marker" in error for error in result["unmet"]),
            result["unmet"],
        )

    def test_external_review_completion_requires_structured_lane_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "TBD",
                                "reviewer_role_scope": "TBD",
                                "claim_boundary_impact": "TBD",
                                "artifacts_reviewed": ["missing.md"],
                                "disposition": "findings",
                                "decisions": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: review_date must use YYYY-MM-DD", result["unmet"])
        self.assertIn("Application security: reviewer_role_scope is required", result["unmet"])
        self.assertIn("Application security: claim_boundary_impact is required", result["unmet"])
        self.assertIn("Application security: reviewed artifact does not exist: missing.md", result["unmet"])
        self.assertIn("missing structured review lanes: AI-agent/tooling, Benchmark/evals methodology", result["unmet"])

    def test_external_review_pending_lanes_are_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "reviews").mkdir(parents=True)
            (root / "docs" / "reviews" / "external-review-packet.md").write_text("# packet\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are task boundaries realistic?"],
                                "blocker": "Needs an independent AppSec reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are scoring semantics valid?"],
                                "blocker": "Needs an independent evals reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are harness assumptions inspectable?"],
                                "blocker": "Needs an independent tooling reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["lanes"],
            ["AI-agent/tooling", "Application security", "Benchmark/evals methodology"],
        )
        self.assertEqual(
            result["unmet"],
            [
                "Application security: independent review is pending",
                "Benchmark/evals methodology: independent review is pending",
                "AI-agent/tooling: independent review is pending",
            ],
        )

    def test_external_review_pending_lanes_require_real_packet_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "pending",
                                "requested_artifacts": ["missing.md"],
                                "requested_questions": ["Question TBD after reviewer confirms scope."],
                                "blocker": "Reviewer unknown until outreach completes.",
                                "next_action": "TODO recruit reviewer.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: requested artifact does not exist: missing.md", result["unmet"])
        self.assertIn("Application security: pending review requires requested_questions", result["unmet"])
        self.assertIn("Application security: pending review requires blocker", result["unmet"])
        self.assertIn("Application security: pending review requires next_action", result["unmet"])
        self.assertIn("Application security: independent review is pending", result["unmet"])

    def test_external_review_response_template_lists_every_required_lane(self) -> None:
        template = json.loads(Path(EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        self.assertEqual(
            {lane["lane"] for lane in template["review_lanes"]},
            set(REQUIRED_REVIEW_LANES),
        )
        for lane in template["review_lanes"]:
            self.assertEqual(lane["review_status"], "complete")
            self.assertIn("review_date", lane)
            self.assertIn("reviewer_role_scope", lane)
            self.assertIn("claim_boundary_impact", lane)
            self.assertIn("questions_reviewed", lane)
            self.assertIn("artifacts_reviewed", lane)
            self.assertIn("disposition", lane)
            self.assertIn("decisions", lane)

    def test_external_review_response_template_is_not_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = root / "docs" / "reviews" / "external-review-summary.json"
            summary.parent.mkdir(parents=True)
            summary.write_text(
                Path(EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("external review response template is not external review evidence", result["unmet"])

    def test_external_review_public_evidence_rejects_sensitive_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer pending final scope note.",
                                "claim_boundary_impact": "Reviewer confirmed claim boundary.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Reviewer cited raw private output in notes.",
                                        "decision": "rejected",
                                        "claim_boundary_impact": "Private detail must stay out of public evidence.",
                                        "task_id": "private-task-id",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("sensitive key is not allowed in public external review evidence" in error for error in result["unmet"]),
            result["unmet"],
        )
        self.assertTrue(
            any(
                "sensitive path marker is not allowed in public external review evidence" in error
                for error in result["unmet"]
            ),
            result["unmet"],
        )

    def test_external_review_complete_lanes_can_pass_with_real_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reviewed_artifact = root / "docs" / "reviews" / "external-review-packet.md"
            reviewed_artifact.parent.mkdir(parents=True)
            reviewed_artifact.write_text("# packet\n", encoding="utf-8")
            follow_up = root / "docs" / "reviews" / "application-security-review-follow-up.md"
            follow_up.write_text("# follow-up\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "bmendonca3"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "bmendonca3@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "seed review artifacts"], cwd=root, check=True)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent AppSec reviewer for SaaS authorization tasks.",
                                "claim_boundary_impact": "Review accepted one task-language clarification.",
                                "questions_reviewed": ["Are public SaaS authorization boundaries realistic?"],
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "decision": "accepted",
                                        "finding": "Secure-control wording could be clearer.",
                                        "summary": "Clarify secure-control wording.",
                                        "claim_boundary_impact": "No score claim change; documentation wording only.",
                                        "follow_up_artifact": "docs/reviews/application-security-review-follow-up.md",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent benchmark methodology reviewer.",
                                "claim_boundary_impact": "No release-claim changes requested.",
                                "questions_reviewed": ["Does the evidence support the stated claim boundary?"],
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "no_findings",
                                "decisions": [
                                    {
                                        "decision": "rejected",
                                        "finding": "No methodology finding.",
                                        "summary": "No methodology changes needed.",
                                        "claim_boundary_impact": "No release-claim change.",
                                    }
                                ],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent AI-agent tooling reviewer.",
                                "claim_boundary_impact": "No harness-claim changes requested.",
                                "questions_reviewed": ["Are harness assumptions inspectable for agent comparability?"],
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "no_findings",
                                "decisions": [
                                    {
                                        "decision": "rejected",
                                        "finding": "No tooling finding.",
                                        "summary": "No tooling changes needed.",
                                        "claim_boundary_impact": "No harness-claim change.",
                                    }
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add review evidence"], cwd=root, check=True)

            result = _validate_external_review_evidence(root)

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_external_review_complete_lanes_require_questions_and_decision_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "External appsec reviewer pending final scope note.",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "questions_reviewed": ["Does the reviewer still need TBD follow-up?"],
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Clarify one control.",
                                        "decision": "rejected",
                                        "summary": "Decision summary TODO after reviewer callback.",
                                        "claim_boundary_impact": "No claim change.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "questions_reviewed": ["Are stale baselines separated clearly?"],
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "questions_reviewed": ["Is agent comparability inspectable?"],
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: reviewer_role_scope is required", result["unmet"])
        self.assertIn(
            "Application security: questions_reviewed must list concrete bounded questions",
            result["unmet"],
        )
        self.assertIn("Application security: decisions[1].summary is required", result["unmet"])

    def test_external_review_decisions_reject_placeholder_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "TBD",
                                        "decision": "accepted",
                                        "follow_up_artifact": "TBD",
                                        "claim_boundary_impact": "TBD",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: decisions[1].finding is required", result["unmet"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )
        self.assertIn("Application security: decisions[1].claim_boundary_impact is required", result["unmet"])

    def test_external_review_decisions_reject_nonexistent_commit_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": "deadbee",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_external_review_decisions_reject_format_only_github_follow_up_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": "https://github.com/bmendonca3/authzbench-saas/issues/foo",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_external_review_decisions_reject_directory_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": ".",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_rotation_metadata_requires_validated_active_and_candidate_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "tasks_private" / "holdout" / "rotation-metadata.json"
            invalid_pack = root / "tasks_private" / "holdout" / "active-pack" / "billing"
            invalid_pack.mkdir(parents=True)
            (invalid_pack / "not-a-task.json").write_text('{"not": "a task manifest"}', encoding="utf-8")
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn("active-pack: private pack manifests do not validate", result["unmet"])
        self.assertIn("rotation metadata must declare one shadow or candidate private pack", result["unmet"])

    def test_rotation_metadata_template_lists_active_and_shadow_shape(self) -> None:
        template = json.loads(Path(PRIVATE_ROTATION_METADATA_TEMPLATE_PATH).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        roles = {pack["role"] for pack in template["packs"]}
        self.assertIn("active", roles)
        self.assertIn("<shadow-or-candidate>", roles)
        for pack in template["packs"]:
            self.assertIn("id", pack)
            self.assertIn("path", pack)
            self.assertIn("version", pack)
            self.assertIn("fingerprint_sha256", pack)
            self.assertTrue(str(pack["path"]).startswith("tasks_private/holdout/"))
        self.assertIn("compatibility", template)
        self.assertIn("retirement_triggers", template)
        self.assertIn("rerun_policy", template)

    def test_rotation_metadata_template_is_not_private_holdout_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "tasks_private" / "holdout" / "rotation-metadata.json"
            metadata.parent.mkdir(parents=True)
            metadata.write_text(
                Path(PRIVATE_ROTATION_METADATA_TEMPLATE_PATH).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "private holdout rotation metadata template is not private holdout evidence",
            result["unmet"],
        )

    def test_rotation_metadata_requires_declared_fingerprints_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdout = root / "tasks_private" / "holdout"
            for pack_name, task_id in (("active-pack", "private-active"), ("candidate-pack", "private-candidate")):
                pack = holdout / pack_name / "billing"
                pack.mkdir(parents=True)
                (pack / "task.json").write_text(json.dumps({"id": task_id}), encoding="utf-8")
            metadata = holdout / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                                "version": "<active-pack-version>",
                                "fingerprint_sha256": "0" * 64,
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/<candidate-pack>",
                                "version": "candidate-v1",
                                "fingerprint_sha256": "<candidate-fingerprint>",
                            },
                        ],
                        "compatibility": {
                            "compatible_with_active_pack": "<boolean>",
                            "comparison_rule": "<comparison-rule>",
                            "old_rows_policy": "TBD",
                        },
                        "retirement_triggers": ["TBD"],
                        "rerun_policy": {
                            "rerun_no_tools_baselines": False,
                            "rerun_tool_agent_baselines": False,
                            "keep_old_rows_as": "current",
                        },
                    }
                ),
                encoding="utf-8",
            )
            valid_result = {
                "passed": True,
                "leaderboard_suitable": True,
                "manifest_count": 1,
            }

            with patch("scripts.validate_v1_readiness.validate_holdout_pack", return_value=valid_result):
                result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn("active-pack: version must be a concrete non-placeholder string", result["unmet"])
        self.assertIn("active-pack: fingerprint_sha256 must match computed pack fingerprint", result["unmet"])
        self.assertIn("candidate-pack: path must be a non-empty string", result["unmet"])
        self.assertIn("candidate-pack: fingerprint_sha256 must be a lowercase SHA-256 digest", result["unmet"])
        self.assertIn("compatibility.compatible_with_active_pack must be boolean", result["unmet"])
        self.assertIn("compatibility.comparison_rule must be a concrete non-placeholder string", result["unmet"])
        self.assertIn("compatibility.old_rows_policy must be a concrete non-placeholder string", result["unmet"])
        self.assertIn("retirement_triggers must list concrete non-placeholder triggers", result["unmet"])
        self.assertIn("rerun_policy.rerun_no_tools_baselines must be true", result["unmet"])
        self.assertIn("rerun_policy.rerun_tool_agent_baselines must be true", result["unmet"])
        self.assertIn("rerun_policy.keep_old_rows_as must be legacy_snapshot or deprecated", result["unmet"])

    def test_rotation_metadata_can_pass_with_declared_fingerprints_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdout = root / "tasks_private" / "holdout"
            for pack_name, task_id in (("active-pack", "private-active"), ("candidate-pack", "private-candidate")):
                pack = holdout / pack_name / "billing"
                pack.mkdir(parents=True)
                (pack / "task.json").write_text(json.dumps({"id": task_id}), encoding="utf-8")
            active_fingerprint = _private_pack_fingerprint(holdout / "active-pack")
            candidate_fingerprint = _private_pack_fingerprint(holdout / "candidate-pack")
            metadata = holdout / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                                "version": "active-v1",
                                "fingerprint_sha256": active_fingerprint,
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/candidate-pack",
                                "version": "candidate-v1",
                                "fingerprint_sha256": candidate_fingerprint,
                            },
                        ],
                        "compatibility": {
                            "compatible_with_active_pack": False,
                            "comparison_rule": "Do not compare candidate rows with active rows until promoted.",
                            "old_rows_policy": "Mark old rows stale or legacy before new comparisons.",
                        },
                        "retirement_triggers": ["private task leakage suspected"],
                        "rerun_policy": {
                            "rerun_no_tools_baselines": True,
                            "rerun_tool_agent_baselines": True,
                            "keep_old_rows_as": "legacy_snapshot",
                        },
                    }
                ),
                encoding="utf-8",
            )
            valid_result = {
                "passed": True,
                "leaderboard_suitable": True,
                "manifest_count": 1,
            }

            with patch("scripts.validate_v1_readiness.validate_holdout_pack", return_value=valid_result):
                result = _validate_private_rotation_metadata(root)

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])
        self.assertEqual(result["active_pack_fingerprint_sha256"], active_fingerprint)

    def test_rotation_metadata_rejects_duplicate_pack_paths(self) -> None:
        manifest = {
            "id": "private_task_one",
            "app": "billing",
            "seed": "private-seed",
            "expected_vulnerable": True,
            "allowed_hosts": ["localhost"],
            "policy": "private",
            "objective": "Prove private task.",
            "output_schema": {"type": "object"},
            "oracle": {"expected": True},
            "controls": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "tasks_private" / "holdout" / "shared-pack" / "billing"
            pack.mkdir(parents=True)
            (pack / "private_task_one.json").write_text(json.dumps(manifest), encoding="utf-8")
            metadata = root / "tasks_private" / "holdout" / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/shared-pack",
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/shared-pack",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn("candidate-pack: pack path duplicates another declared private pack", result["unmet"])

    def test_rotation_metadata_compares_declared_private_pack_structures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdout = root / "tasks_private" / "holdout"
            for pack_name in ("active-pack", "candidate-pack"):
                pack = holdout / pack_name / "billing"
                pack.mkdir(parents=True)
                (pack / "task.json").write_text("{}\n", encoding="utf-8")
            metadata = holdout / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/candidate-pack",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            invalid_result = {
                "passed": False,
                "leaderboard_suitable": False,
                "manifest_count": 0,
            }

            with patch(
                "scripts.validate_v1_readiness.validate_holdout_pack",
                return_value=invalid_result,
            ) as validator:
                result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertEqual(validator.call_count, 2)
        first_comparison = validator.call_args_list[0].kwargs["comparison_private_patterns"]
        second_comparison = validator.call_args_list[1].kwargs["comparison_private_patterns"]
        self.assertEqual(first_comparison, [])
        self.assertEqual(len(second_comparison), 1)
        self.assertIn("active-pack", second_comparison[0])

    def test_clean_tree_check_rejects_untracked_inputs_except_release_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            evidence = root / "release-evidence.json"
            evidence.write_text("{}\n", encoding="utf-8")
            self.assertTrue(_working_tree_clean(root, {evidence.resolve()}))

            (root / "untracked-task.json").write_text("{}\n", encoding="utf-8")
            self.assertFalse(_working_tree_clean(root, {evidence.resolve()}))

    def test_release_candidate_evidence_rejects_template_placeholders_after_schema_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            commands = payload["commands"]
            assert isinstance(commands, dict)
            payload["benchmark_source_sha"] = "<ancestor-benchmark-source-sha>"
            payload["private_pack_fingerprint_sha256"] = "<active-private-pack-fingerprint-sha256>"
            commands["python3 -m unittest discover -s tests"]["evidence"] = "<log-or-run-id>"
            evidence = self._write_release_candidate_evidence(root, payload)

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("benchmark_source_sha must not be a template placeholder", result["unmet"])
        self.assertIn(
            "private_pack_fingerprint_sha256 must not be a template placeholder",
            result["unmet"],
        )
        self.assertIn(
            "release validation command must record non-placeholder evidence: python3 -m unittest discover -s tests",
            result["unmet"],
        )

    def _source_and_release_with_changed_path(self, changed_path: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            path = root / changed_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            path.write_text("release\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            return _benchmark_source_compatibility_errors(root, source_sha, release_sha)

    def test_benchmark_source_rejects_ancestor_with_task_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("tasks/billing/task.json")

        self.assertIn("release-affecting files changed after benchmark_source_sha: tasks/billing/task.json", errors)

    def test_benchmark_source_rejects_ancestor_with_docker_topology_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("docker-compose.yml")

        self.assertIn("release-affecting files changed after benchmark_source_sha: docker-compose.yml", errors)

    def test_benchmark_source_rejects_ancestor_with_paper_build_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("paper/ieee-sp/main.tex")

        self.assertIn("release-affecting files changed after benchmark_source_sha: paper/ieee-sp/main.tex", errors)

    def test_benchmark_source_allows_narrow_evidence_record_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("artifact/submission-runner-smoke.json")

        self.assertEqual(errors, [])

    def test_paper_readiness_allows_only_narrow_post_source_evidence_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "paper" / "ieee-sp").mkdir(parents=True)
            (root / "paper" / "ieee-sp" / "main.tex").write_text("source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(json.dumps(self._paper_readiness_payload(source_sha)), encoding="utf-8")
            fixture = root / "artifact" / "expected-output" / "v1-readiness-public-view.json"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("{}\n", encoding="utf-8")
            (root / "docs" / "goal.md").write_text("paper evidence\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "evidence",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            result = _validate_paper_readiness_evidence(
                root,
                release_sha=release_sha,
                allowed_post_source_paths={
                    "docs/v1-paper-readiness.json",
                    "artifact/expected-output/v1-readiness-public-view.json",
                    "docs/goal.md",
                },
                upstream_gates_complete=True,
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_paper_readiness_rejects_release_affecting_post_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence.write_text(json.dumps(self._paper_readiness_payload(source_sha)), encoding="utf-8")
            paper = root / "paper" / "ieee-sp" / "main.tex"
            paper.parent.mkdir(parents=True)
            paper.write_text("changed after source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release-affecting change",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            result = _validate_paper_readiness_evidence(
                root,
                release_sha=release_sha,
                allowed_post_source_paths={
                    "docs/v1-paper-readiness.json",
                    "artifact/expected-output/v1-readiness-public-view.json",
                    "docs/goal.md",
                },
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "release-affecting files changed after benchmark_source_sha: paper/ieee-sp/main.tex",
            result["unmet"],
        )

    def test_paper_readiness_rejects_non_sha_benchmark_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            payload = self._paper_readiness_payload("a" * 40)
            payload["benchmark_source_sha"] = "tbd"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("benchmark_source_sha must be a 40-character lowercase Git SHA", result["unmet"])

    def test_paper_readiness_requires_concrete_verification_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            payload = self._paper_readiness_payload("a" * 40)
            payload["verification"] = {
                "paper_tables_command": "TBD",
                "charts_command": "TBD",
                "latex_command": "TBD",
                "latex_result": "<latex-result>",
                "verified_on": "not-a-date",
            }
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "verification.paper_tables_command must be "
            "python3 scripts/generate_paper_tables.py && git diff --exit-code -- paper/shared",
            result["unmet"],
        )
        self.assertIn(
            "verification.charts_command must be "
            "python3 scripts/generate_benchmark_charts.py "
            "&& git diff --exit-code -- docs/assets/benchmark-charts",
            result["unmet"],
        )
        self.assertIn(
            "verification.latex_command must be latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex",
            result["unmet"],
        )
        self.assertIn("verification.latex_result must be a concrete non-placeholder string", result["unmet"])
        self.assertIn("verification.verified_on must use YYYY-MM-DD", result["unmet"])

    def test_paper_readiness_rejects_compact_verified_on_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            payload = self._paper_readiness_payload("a" * 40)
            verification = payload["verification"]
            assert isinstance(verification, dict)
            verification["verified_on"] = "20260608"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("verification.verified_on must use YYYY-MM-DD", result["unmet"])

    def test_paper_readiness_rejects_self_referential_release_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "seed.txt").write_text("seed\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(json.dumps(self._paper_readiness_payload(release_sha)), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root, release_sha=release_sha)

        self.assertFalse(result["passed"])
        self.assertIn(
            "benchmark_source_sha must reference an ancestor commit, not the release commit",
            result["unmet"],
        )

    def test_paper_readiness_rejects_mismatch_with_release_evidence_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(json.dumps(self._paper_readiness_payload("a" * 40)), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root, benchmark_source_sha="b" * 40)

        self.assertFalse(result["passed"])
        self.assertIn("benchmark_source_sha must match release benchmark_source_sha", result["unmet"])

    def test_paper_readiness_rejects_self_attested_upstream_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(json.dumps(self._paper_readiness_payload("a" * 40)), encoding="utf-8")

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("live upstream review and infrastructure gates must pass", result["unmet"])

    def test_release_candidate_template_lists_every_required_command(self) -> None:
        template = json.loads((Path(RELEASE_VALIDATION_TEMPLATE_PATH)).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        self.assertEqual(
            set(template["commands"]),
            set(REQUIRED_RELEASE_VALIDATION_COMMANDS),
        )
        for command in REQUIRED_RELEASE_VALIDATION_COMMANDS:
            self.assertIn("passed", template["commands"][command])
            self.assertNotEqual(template["commands"][command]["passed"], True)

    def test_release_candidate_template_is_not_release_evidence(self) -> None:
        result = _validate_release_candidate_evidence(
            evidence_path=Path(RELEASE_VALIDATION_TEMPLATE_PATH),
            target_sha="a" * 40,
            private_pack_fingerprint_sha256="b" * 64,
        )

        self.assertFalse(result["passed"])
        self.assertIn("release validation template is not release-candidate evidence", result["unmet"])

    def test_release_candidate_evidence_requires_release_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["schema_version"] = "wrong"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be v1-release-candidate-validation-v1", result["unmet"])

    def test_release_candidate_evidence_can_pass_with_exact_ci_url_and_command_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            evidence = root / "release-evidence.json"
            evidence.write_text(
                json.dumps(self._release_candidate_evidence_payload(commit_sha)),
                encoding="utf-8",
            )

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_release_candidate_evidence_requires_exact_head_ci_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["exact_head_ci_url"] = "https://github.com/bmendonca3/authzbench-saas/actions/runs/not-a-run"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("exact_head_ci_url must reference an AuthZBench-SaaS Actions run", result["unmet"])
        self.assertNotIn("exact_head_ci_run_id must match exact_head_ci_url", result["unmet"])

    def test_release_candidate_evidence_requires_matching_exact_head_ci_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["exact_head_ci_run_id"] = "987654321"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("exact_head_ci_run_id must match exact_head_ci_url", result["unmet"])

    def test_release_candidate_evidence_requires_numeric_exact_head_ci_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["exact_head_ci_run_id"] = "run-123456789"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("exact_head_ci_run_id must be a numeric GitHub Actions run id", result["unmet"])

    def test_release_candidate_evidence_requires_exact_head_ci_head_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["exact_head_ci_head_sha"] = "c" * 40
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn("exact_head_ci_head_sha must match release commit_sha", result["unmet"])

    def test_release_candidate_evidence_requires_exact_head_ci_workflow_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["exact_head_ci_workflow_name"] = "Ad hoc validation"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            f"exact_head_ci_workflow_name must be {RELEASE_VALIDATION_CI_WORKFLOW_NAME}",
            result["unmet"],
        )

    def test_release_candidate_evidence_requires_command_exit_code_and_evidence(self) -> None:
        command = REQUIRED_RELEASE_VALIDATION_COMMANDS[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["commands"][command]["exit_code"] = 1
            payload["commands"][command]["evidence"] = "TBD"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(f"release validation command must record exit_code 0: {command}", result["unmet"])
        self.assertIn(
            f"release validation command must record non-placeholder evidence: {command}",
            result["unmet"],
        )

    def test_release_candidate_evidence_requires_empty_privacy_scan_output(self) -> None:
        command = RELEASE_VALIDATION_PRIVACY_SCAN_COMMAND
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["commands"][command]["evidence"] = "printed tracked paths"
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            f"privacy scan command must record evidence exactly 'empty output': {command}",
            result["unmet"],
        )

    def test_release_candidate_evidence_rejects_sensitive_or_local_evidence_strings(self) -> None:
        command = REQUIRED_RELEASE_VALIDATION_COMMANDS[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_sha = self._seed_git_root(root)
            payload = self._release_candidate_evidence_payload(commit_sha)
            payload["commands"][command]["evidence"] = "debug log at /Users/example/private-run.log"
            payload["release_notes"] = ["raw private output was inspected locally"]
            evidence = root / "release-evidence.json"
            evidence.write_text(json.dumps(payload), encoding="utf-8")

            result = _validate_release_candidate_evidence(
                root,
                evidence_path=evidence,
                target_sha=commit_sha,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("absolute path is not allowed in release-candidate evidence" in item for item in result["unmet"]),
            result["unmet"],
        )
        self.assertTrue(
            any("sensitive marker is not allowed in release-candidate evidence" in item for item in result["unmet"]),
            result["unmet"],
        )

    def test_release_candidate_runbook_is_structured_procedure_evidence(self) -> None:
        result = _validate_release_candidate_runbook()

        self.assertTrue(result["passed"])
        self.assertEqual(result["path"], RELEASE_VALIDATION_RUNBOOK_PATH)
        self.assertEqual(result["unmet"], [])

    def test_release_candidate_runbook_rejects_overclaiming_and_incomplete_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook = root / RELEASE_VALIDATION_RUNBOOK_PATH
            runbook.parent.mkdir(parents=True)
            runbook.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "release-candidate validation evidence",
                        "required_inputs": ["TBD"],
                        "required_commands": [
                            "python3 -m unittest discover -s tests",
                            "TBD",
                        ],
                        "required_evidence_fields": ["commit_sha", "TBD"],
                        "acceptance_checks": ["all required commands passed", "TBD"],
                        "publication_rules": ["TBD"],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_release_candidate_runbook(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "schema_version must be v1-release-candidate-validation-runbook-v1",
            result["unmet"],
        )
        self.assertIn("evidence_status must be runbook", result["unmet"])
        self.assertIn(
            "public_claim_boundary must state that the runbook is not release-candidate validation evidence",
            result["unmet"],
        )
        self.assertIn("required_inputs cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("required_inputs missing:") for item in result["unmet"])
        )
        self.assertIn("required_commands cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("required_commands missing:") for item in result["unmet"])
        )
        self.assertIn("required_evidence_fields cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("required_evidence_fields missing:") for item in result["unmet"])
        )
        self.assertIn("acceptance_checks cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("acceptance_checks missing:") for item in result["unmet"])
        )
        self.assertIn("publication_rules cannot contain placeholders", result["unmet"])
        self.assertTrue(
            any(item.startswith("publication_rules missing:") for item in result["unmet"])
        )

    def test_release_candidate_runbook_rejects_local_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook = root / RELEASE_VALIDATION_RUNBOOK_PATH
            runbook.parent.mkdir(parents=True)
            data = json.loads(Path(RELEASE_VALIDATION_RUNBOOK_PATH).read_text(encoding="utf-8"))
            data["release_notes"].append("debug artifact at /Users/example/private-log.json")
            runbook.write_text(json.dumps(data), encoding="utf-8")

            result = _validate_release_candidate_runbook(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "$.release_notes[3]: absolute path is not allowed in public release runbook",
            result["unmet"],
        )

    def test_private_pack_fingerprint_changes_when_manifest_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            app = pack / "billing"
            app.mkdir()
            manifest = app / "task.json"
            manifest.write_text(json.dumps({"id": "private-task", "seed": "one"}), encoding="utf-8")
            first = _private_pack_fingerprint(pack)

            manifest.write_text(json.dumps({"id": "private-task", "seed": "two"}), encoding="utf-8")
            second = _private_pack_fingerprint(pack)

        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertRegex(second, r"^[0-9a-f]{64}$")
        self.assertNotEqual(first, second)

    def test_source_summary_private_denial_rejects_stale_private_pack_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-summary.json"
            submission = root / "submission.json"
            source.write_text(
                json.dumps(
                    {
                        "protected_execution": {"host_private_paths_denied": True},
                        "private_pack_fingerprint_sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            submission_data = {
                "source_run_summaries": [source.name],
                "private_pack_fingerprint_sha256": "0" * 64,
            }
            submission.write_text(json.dumps(submission_data), encoding="utf-8")

            matches = _source_summaries_have_private_denial(
                submission,
                submission_data,
                private_pack_fingerprint_sha256="1" * 64,
            )

        self.assertFalse(matches)


if __name__ == "__main__":
    unittest.main()
